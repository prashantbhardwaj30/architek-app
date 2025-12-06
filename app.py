import os
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ArchiTek | Blueprint Engine", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {background-color: #0E1117; color: #FAFAFA;}
</style>
""", unsafe_allow_html=True)

# --- 2. SMART AUTH LOGIC ---
# Try to load the sponsor key from Streamlit Secrets
try:
    sponsor_key = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    sponsor_key = None

active_key = None

with st.sidebar:
    st.title("🏛️ ArchiTek")
    st.markdown("**Whitepaper to Wallet.**")
    st.markdown("---")
    
    # Logic: If sponsor key exists, use it by default. Allow override.
    if sponsor_key:
        st.success("✅ **Free Access Active**")
        st.caption("Sponsored by BehindTheBlackBox")
        
        # Default to sponsor key
        active_key = sponsor_key
        
        # Optional Override for Power Users
        with st.expander("🔑 Use Your Own Key (Optional)"):
            user_key = st.text_input("Enter Gemini API Key", type="password")
            if user_key:
                active_key = user_key
                st.info("Using your personal key.")
    else:
        # Fallback if no secrets are set
        st.warning("⚠️ Free Quota Paused.")
        active_key = st.text_input("Enter Gemini API Key", type="password")

    st.markdown("---")

# --- 3. MODEL SETUP & VALIDATION ---
model = None
models_ready = False

if active_key:
    genai.configure(api_key=active_key)
    
    try:
        # List available models to ensure key works
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if available_models:
            # Smart Model Selection (Prioritize Flash for speed/cost)
            model_to_use = None
            preferred_models = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro']
            
            for preferred in preferred_models:
                for available in available_models:
                    if preferred in available:
                        model_to_use = available.split('/')[-1]
                        break
                if model_to_use: break
            
            # Fallback
            if not model_to_use:
                model_to_use = available_models[0].split('/')[-1]

            model = genai.GenerativeModel(model_to_use)
            models_ready = True
            st.sidebar.info(f"🤖 Brain: **{model_to_use}**")
        else:
            st.sidebar.error("❌ Key valid, but no models found.")
            
    except Exception as e:
        # Catch Rate Limit or Auth errors immediately
        if "429" in str(e) or "403" in str(e):
            st.sidebar.error("⚠️ **Sponsor Quota Exceeded.**")
            st.sidebar.warning("Please enter your own API Key in the expander above.")
            models_ready = False
        else:
            st.sidebar.error(f"❌ Key Error: {str(e)}")
            models_ready = False
else:
    st.info("👈 Waiting for credentials...")

# --- 4. MAIN INTERFACE ---
st.header("Build Your AI SaaS Blueprint")
st.markdown("Upload a research paper to generate the **Implementation Blueprint**.")

uploaded_file = st.file_uploader("Upload ArXiv PDF", type=["pdf"])

if uploaded_file and models_ready:
    if st.button("Generate Blueprint 🚀"):
        with st.spinner("Analyzing Architecture... (This takes 10-20s)"):
            try:
                # PDF Processing
                pdf_reader = PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # Truncate to safety limit (Flash has 1M context, but let's be safe)
                text = text[:100000]
                
                prompt = f"""
                You are a Senior AI Solutions Architect. Analyze this research paper for a Solopreneur who wants to build a SaaS.

                RESEARCH PAPER TEXT:
                {text}

                OUTPUT FORMAT (Strictly follow this structure):

                ## 1. Core Mechanism (The Code Logic)
                * **Key Concept:** One sentence explaining the breakthrough.
                * **Critical Equation:** Extract the most important formula (in LaTeX).
                * **Plain English:** Explain what that formula DOES.
                * **Pseudo-Code:** Write a Python function (def) representing this core logic.

                ## 2. Product-Market Translation (The Money)
                * **The "Unfair Advantage":** What does this tech do better/cheaper than current tools?
                * **Under-Tapped Niche:** Identify ONE specific, boring, high-margin industry (e.g., Legal, Oil, Medical) that needs this.
                * **SaaS Idea:** Name and describe a micro-SaaS product for that niche.

                ## 3. The MVP Checklist (The 7-Day Plan)
                * List 5 steps to build a Minimum Viable Product using existing APIs (Gemini/OpenAI) + LangChain.
                * Identify the "Small Scale" parameters (e.g., "Don't train, use RAG with top_k=5").
                """
                
                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(response.text)
                st.balloons()
                st.success("✅ Blueprint Generated. Start building.")
                
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ **Too Many Requests.** The sponsored key is currently overloaded. Please use your own key in the sidebar.")
                else:
                    st.error(f"❌ Analysis Failed: {str(e)}")
