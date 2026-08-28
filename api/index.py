import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from groq import Groq

app = FastAPI(title="AURELIA AI Travel Planner")

SYSTEM_PROMPT = """You are AURELIA, a luxury AI travel planner.
Build realistic, useful and elegant travel plans. Personalize answers to budget, dates,
interests and trip style. Use Indian Rupees (₹) unless another currency is requested.
When relevant include destination overview, best time/weather considerations, hotel area
suggestions, food, transport, budget, itinerary, packing, safety and hidden gems.
Keep the luxury tone polished but practical. Do not claim live availability unless you
actually have live data."""

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)

class ItineraryRequest(BaseModel):
    destination: str
    days: int
    travelers: int
    budget: int
    start_date: str
    pace: str
    hotel: str
    interests: list[str] = Field(default_factory=list)

def get_client():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured in Vercel."
        )
    return Groq(api_key=key)

def complete(messages):
    try:
        response = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=3000,
        )
        return response.choices[0].message.content.strip()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Groq API error: {exc}")

@app.get("/api")
def health():
    return {"status": "ok", "app": "AURELIA AI Travel Planner"}

@app.post("/api/chat")
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in request.history[-10:]:
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({"role": role, "content": content[:6000]})

    messages.append({"role": "user", "content": request.message[:8000]})
    return {"reply": complete(messages)}

@app.post("/api/itinerary")
def itinerary(request: ItineraryRequest):
    if not request.destination.strip():
        raise HTTPException(status_code=400, detail="Destination is required.")

    interests = ", ".join(request.interests) if request.interests else "general travel"
    prompt = f"""Create a complete {request.days}-day travel itinerary for {request.destination}.

Trip details:
- Travelers: {request.travelers}
- Budget: ₹{request.budget:,}
- Hotel style: {request.hotel}
- Interests: {interests}
- Start date: {request.start_date}
- Trip pace: {request.pace}

Return these sections:
1. Trip overview
2. Estimated budget breakdown in ₹
3. Day-by-day itinerary with Morning, Afternoon and Evening
4. Suggested food and cafés
5. Hotel area suggestions
6. Transport tips
7. Hidden gems
8. Packing checklist
9. Safety tips
10. Final luxury travel tip

Make it practical, realistic and elegant. Clearly label estimates as estimates."""

    return {"itinerary": complete([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])}
