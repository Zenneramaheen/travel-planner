import os
from datetime import date
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="AURELIA | AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# ----------------------------
# CUSTOM UI
# ----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(201,168,106,0.14), transparent 25%),
            radial-gradient(circle at 90% 20%, rgba(70,100,140,0.14), transparent 25%),
            linear-gradient(135deg, #070808, #101213 55%, #0b0c0c);
        color: #f4f0e8;
    }

    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif !important;
        letter-spacing: 0.3px;
    }

    .hero {
        padding: 18px 0 8px 0;
    }

    .hero h1 {
        font-size: 52px;
        margin: 0;
        color: #f6f1e7;
    }

    .hero .gold { color: #c9a86a; }

    .subtitle {
        color: #aaa;
        font-size: 16px;
        margin-top: 8px;
    }

    .card {
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(201,168,106,0.22);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 10px 35px rgba(0,0,0,0.2);
        margin-bottom: 12px;
    }

    .chip {
        display: inline-block;
        padding: 6px 10px;
        margin: 4px 6px 0 0;
        border-radius: 999px;
        background: rgba(201,168,106,0.12);
        border: 1px solid rgba(201,168,106,0.25);
        color: #e3c690;
        font-size: 13px;
    }

    .metric {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(201,168,106,0.2);
        border-radius: 16px;
        padding: 16px;
        text-align: center;
    }

    .metric-value { font-size: 24px; font-weight: 700; color: #d6b477; }
    .metric-label { font-size: 13px; color: #a7a7a7; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111313, #080909);
        border-right: 1px solid #302a20;
    }

    .stButton > button {
        background: linear-gradient(135deg, #c8a66a, #8d6b38);
        color: #111;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.65rem 1rem;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #e0c58d, #b38a4b);
        color: #000;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox div, .stNumberInput input {
        background-color: #171919 !important;
        color: #f4f0e8 !important;
        border-radius: 10px !important;
    }

    hr { border-color: #302a20; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# GROQ CLIENT
# ----------------------------
client = None
if api_key:
    client = Groq(api_key=api_key)

MODEL = "llama-3.3-70b-versatile"

# ----------------------------
# SESSION STATE
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "itinerary" not in st.session_state:
    st.session_state.itinerary = ""
if "prefs" not in st.session_state:
    st.session_state.prefs = {}

# ----------------------------
# HELPERS
# ----------------------------
def build_system_prompt():
    return """
You are AURELIA, a luxury AI travel planner.

Goals:
- Build realistic, beautiful, and useful travel plans
- Keep answers structured and easy to scan
- Be personalized to budget, dates, interests, and trip style
- Use Indian Rupees (₹) unless another currency is requested

Always include when relevant:
- destination overview
- best time / weather considerations
- hotel area suggestions
- food recommendations
- transport advice
- budget estimate
- day-by-day itinerary
- packing checklist
- safety tips
- hidden gems
- a polished luxury tone without being overly verbose
"""

def ask_ai(user_text: str) -> str:
    if not client:
        return "GROQ_API_KEY is missing. Add it to your .env file and restart the app."

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_text},
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error while contacting Groq API:\n\n{e}"

def build_itinerary_prompt(p):
    interests = ", ".join(p["interests"]) if p["interests"] else "general travel"
    return f"""
Create a complete {p['days']}-day travel itinerary for {p['destination']}.

Trip details:
- Travelers: {p['travelers']}
- Budget: ₹{p['budget']}
- Hotel style: {p['hotel']}
- Interests: {interests}
- Start date: {p['start_date']}
- Trip pace: {p['pace']}

Return a well-organized plan with these sections:

1. Trip overview
2. Estimated budget breakdown in ₹
3. Day-by-day itinerary
   - Morning
   - Afternoon
   - Evening
4. Suggested food and cafés
5. Hotel area suggestions
6. Transport tips
7. Hidden gems
8. Packing checklist
9. Safety tips
10. Final luxury travel tip

Make it practical, realistic, and elegant.
"""

def make_summary_card(title, value, label):
    return f"""
    <div class="metric">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.markdown("## ✈️ AURELIA")
    st.caption("Luxury AI travel planner")

    st.markdown("---")
    st.markdown("### Trip details")

    destination = st.text_input("Destination", placeholder="e.g. Bali, Dubai, Paris")
    days = st.slider("Number of days", 1, 30, 5)
    travelers = st.number_input("Travelers", min_value=1, max_value=20, value=2)
    budget = st.number_input("Budget (₹)", min_value=5000, max_value=10000000, value=100000, step=5000)
    start_date = st.date_input("Start date", value=date.today())

    pace = st.selectbox("Trip pace", ["Relaxed", "Balanced", "Packed"])
    hotel = st.selectbox("Hotel style", ["Luxury 5-star", "Boutique hotel", "Mid-range hotel", "Budget-friendly", "Resort"])
    interests = st.multiselect(
        "Interests",
        ["Luxury", "Adventure", "Beaches", "Culture", "Shopping", "Food", "Nature", "Nightlife", "Photography", "Relaxation"],
        default=["Culture", "Food"],
    )

    st.markdown("---")

    gen_btn = st.button("🗺️ Generate itinerary", use_container_width=True)
    clear_btn = st.button("🧹 Clear chat", use_container_width=True)

    st.markdown("---")
    st.caption("Tip: ask things like “Plan a 6-day luxury trip to Tokyo for 2 people.”")

# ----------------------------
# CLEAR CHAT
# ----------------------------
if clear_btn:
    st.session_state.messages = []
    st.session_state.itinerary = ""
    st.rerun()

# ----------------------------
# GENERATE ITINERARY
# ----------------------------
prefs = {
    "destination": destination.strip(),
    "days": days,
    "travelers": travelers,
    "budget": budget,
    "start_date": start_date.strftime("%d %b %Y"),
    "pace": pace,
    "hotel": hotel,
    "interests": interests,
}
st.session_state.prefs = prefs

if gen_btn:
    if not destination.strip():
        st.warning("Please enter a destination first.")
    else:
        with st.spinner("Designing your journey..."):
            prompt = build_itinerary_prompt(prefs)
            st.session_state.itinerary = ask_ai(prompt)
        st.success("Itinerary generated successfully.")

# ----------------------------
# HEADER
# ----------------------------
st.markdown(
    """
    <div class="hero">
        <h1>Travel, <span class="gold">beautifully.</span></h1>
        <p class="subtitle">A luxury AI travel planner with chat, itinerary generation, and practical travel guidance.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# METRICS
# ----------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(make_summary_card("AI", "Smart", "Planning"), unsafe_allow_html=True)
with c2:
    st.markdown(make_summary_card("24/7", "Always", "Available"), unsafe_allow_html=True)
with c3:
    st.markdown(make_summary_card("₹", "Budget", "Aware"), unsafe_allow_html=True)
with c4:
    st.markdown(make_summary_card("∞", "Luxury", "Ideas"), unsafe_allow_html=True)

st.markdown("")

# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3 = st.tabs(["💬 Travel Chat", "🗺️ Itinerary", "✨ Inspiration"])

with tab1:
    st.markdown(
        """
        <div class="card">
            <h3>Ask AURELIA anything about travel</h3>
            <p>Destinations, hotels, budgets, food, sightseeing, packing, safety, and full trip plans.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Example: Plan a luxury 5-day trip to Bali for 2 people")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Planning your trip..."):
                reply = ask_ai(prompt)
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

with tab2:
    st.markdown("## Your personalized itinerary")

    if st.session_state.itinerary:
        st.markdown(st.session_state.itinerary)
        st.download_button(
            "📥 Download itinerary",
            st.session_state.itinerary,
            file_name="travel_itinerary.txt",
            mime="text/plain",
        )
    else:
        st.info("Use the sidebar to choose your trip details, then click Generate itinerary.")

with tab3:
    st.markdown("## Travel inspiration")

    ideas = [
        ("🏝️ Bali", "Beaches, temples, wellness, and luxury villas."),
        ("🌆 Dubai", "Shopping, skyline views, desert experiences."),
        ("🏔️ Switzerland", "Alpine scenery, scenic trains, premium stays."),
        ("🕌 Istanbul", "History, food, architecture, and culture."),
        ("🌊 Maldives", "Private overwater villas and pure relaxation."),
        ("🌸 Japan", "Food, culture, technology, and beautiful seasons."),
    ]

    left, right = st.columns(2)
    for i, (title, desc) in enumerate(ideas):
        target = left if i % 2 == 0 else right
        with target:
            st.markdown(
                f"""
                <div class="card">
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.caption("AURELIA AI Travel Planner • Python • Streamlit • Groq")