import os
import re
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. CONFIGURATION ---
# Festive Christmas Update 🎄
st.set_page_config(page_title="ArchiTek | Intel Engine", page_icon="🎄", layout="wide")

# --- CSS: ULTIMATE STEALTH MODE ---
st.markdown("""
<style>
    /* HIDE ALL DEFAULT STREAMLIT BRANDING & DEPLOY BUTTONS */
    #MainMenu, footer, header, .stAppDeployButton, [data-testid="stStatusWidget"], [data-testid="stDecoration"] {
        visibility: hidden !important; display: none !important;
    }
    [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    
    /* BLACK OPS THEME */
    .stApp {background-color: #0E1117; color: #E6E6E6;}
    
    /* INPUT FIELDS (Dark Mode) */
    .stTextInput > div > div > input { background-color: #161B22; color: #FAFAFA; border: 1px solid #30363D; }
    
    /* GREEN ACTION BUTTON */
    .stButton > button { background-color: #238636 !important; color: white !important; border: none !important; font-weight: bold; }
    
    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363D; }
    
    /* REMOVE TOP PADDING */
    .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# --- 3. AUTH & BRANDED SIDEBAR ---
try:
    sponsor_key = st.secrets["GOOGLE_API_KEY"]
except:
    sponsor_key = None

active_key = None

with st.sidebar:
    st.title("🏛️ ArchiTek // V5")
    st.caption("Strategic Intelligence Engine")
    st.markdown("---")
    
    # --- MISSION BRIEF ---
    st.subheader("🎯 Mission Brief")
    user_persona = st.selectbox(
        "Your Role",
        ("Venture Capital Partner", "Chief Technology Officer", "Staff Software Engineer", "Brand & Content Lead")
    )
    target_industry = st.text_input("Target Sector", value="General")
    
    st.markdown("---")
    active_key = sponsor_key or st.text_input("Enter API Key", type="password")

    # --- BRAND LINKS (YouTube & LinkedIn) ---
    st.subheader("🔗 Connect with me")
    st.markdown(f"""
        <a href="https://www.linkedin.com/in/prashantbhardwaj30/" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; background-color: #0077B5; color: white; border: none; padding: 8px; border-radius: 5px; margin-bottom: 5px; font-weight: bold; cursor: pointer;">LinkedIn Profile</button>
        </a>
        <a href="https://www.youtube.com/@DesiAILabs" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; background-color: #FF0000; color: white; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer;">Desi AI Labs (YouTube)</button>
        </a>
    """, unsafe_allow_html=True)

    # --- ECOSYSTEM UPSELL ---
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d;">
        <h4 style="margin: 0; color: #FAFAFA; font-size: 14px;">🎓 Master AI Build</h4>
        <p style="font-size: 11px; color: #8b949e; margin: 5px 0 10px 0;">Build AI Agents with Prashant Bhardwaj.</p>
        <a href="https://aigurukul.lovable.app" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; background-color: #238636; color: white; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer;">Join AI Gurukul</button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- 4. V5 STRATEGIC PROMPT LOGIC ---
def get_persona_prompt(role, industry, text):
    base = f"Analyze this research for {industry}. Context: {text[:80000]}."
    
    if role == "Venture Capital Partner":
        return f"{base} Focus: ROI. 1. Market Wedge (Entry point), 2. Scaling Factor, 3. 'Decision Door' (Table: Reversible vs Irreversible risks)."
    
    elif role == "Chief Technology Officer":
        return f"{base} Focus: Implementation. 1. Friction Score (1-10), 2. Integration Risks, 3. System Architecture (Graphviz DOT code in ```dot tags)."
    
    elif role == "Staff Software Engineer":
        return f"{base} Focus: Automation. 1. Shortest MVP Path, 2. The Agent Protocol (.cursorrules for AI code editors), 3. Logic Flow (Graphviz DOT code in ```dot tags)."
    
    elif role == "Brand & Content Lead":
        return f"{base} Focus: Viral Growth. 1. The ROI Value Hook, 2. LinkedIn & YouTube Content Blueprint, 3. 'OneUsefulThing' Insight."
    
    return base

# --- 5. EXECUTION ---
if active_key:
    genai.configure(api_key=active_key)
    st.title("ArchiTek // Strategic Engine")
    uploaded_file = st.file_uploader("Upload Dossier (PDF)", type=["pdf"])

    if uploaded_file and st.button("Execute Intelligence Analysis"):
        with st.spinner("Extracting Strategic Value..."):
            try:
                pdf = PdfReader(uploaded_file)
                text = "".join([p.extract_text() for p in pdf.pages])
                
                # Smart Model Selection
                available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model_name = next((m for m in available if 'flash' in m), available[0]).split('/')[-1]
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content(get_persona_prompt(user_persona, target_industry, text))
                st.session_state.analysis_result = response.text
                
            except Exception as e:
                st.error(f"Mission Failed: {str(e)}")

# --- 6. OUTPUT & DIAGRAMS ---
if st.session_state.analysis_result:
    st.markdown("---")
    st.markdown(st.session_state.analysis_result)
    
    match = re.search(r'```dot\n(.*?)\n```', st.session_state.analysis_result, re.DOTALL)
    if match:
        st.subheader("🏗️ Architecture Visual")
        st.graphviz_chart(match.group(1))

    st.download_button("📥 Download Intel", st.session_state.analysis_result.encode('utf-8'), f"ArchiTek_{user_persona}.md")
