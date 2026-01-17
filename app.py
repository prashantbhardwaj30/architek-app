import os
import re
import requests
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from io import BytesIO

# --- 1. CONFIGURATION & STEALTH CSS ---
st.set_page_config(page_title="ArchiTek | Intel Engine", page_icon="🎄", layout="wide")

st.markdown("""
<style>
    #MainMenu, footer, header, .stAppDeployButton, [data-testid="stStatusWidget"], [data-testid="stDecoration"] {
        visibility: hidden !important; display: none !important;
    }
    [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    .stApp {background-color: #0E1117; color: #E6E6E6;}
    .stTextInput > div > div > input { background-color: #161B22; color: #FAFAFA; border: 1px solid #30363D; }
    .stButton > button { background-color: #238636 !important; color: white !important; font-weight: bold; border: none !important; }
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363D; }
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

with st.sidebar:
    st.title("🏛️ ArchiTek // V5.2")
    st.caption("Market Intelligence Engine")
    st.markdown("---")
    
    st.subheader("🎯 Mission Brief")
    user_persona = st.selectbox(
        "Your Role",
        ("Venture Capital Partner", "Chief Technology Officer", "Staff Software Engineer", "Brand & Content Lead")
    )
    target_industry = st.text_input("Target Sector", value="General", help="e.g., Fintech, HealthTech, Supply Chain")
    
    st.markdown("---")
    active_key = sponsor_key or st.text_input("Enter API Key", type="password")

    st.subheader("🔗 Connect")
    st.markdown(f"""
        <a href="https://www.linkedin.com/in/prashantbhardwaj30/" target="_blank"><button style="width: 100%; background-color: #0077B5; color: white; border: none; padding: 8px; border-radius: 5px; margin-bottom: 5px; font-weight: bold; cursor: pointer;">LinkedIn Profile</button></a>
        <a href="https://www.youtube.com/@DesiAILabs" target="_blank"><button style="width: 100%; background-color: #FF0000; color: white; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer;">YouTube Channel</button></a>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-top: 10px;">
        <h4 style="margin: 0; color: #FAFAFA; font-size: 14px;">🎓 Master AI Build</h4>
        <a href="https://aigurukul.lovable.app" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; background-color: #238636; color: white; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer;">Join AI Gurukul</button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- 4. STRATEGIC LOGIC ---
def get_persona_prompt(role, industry, text):
    # Added the Market Heatmap & Saturation Audit to the base logic
    base = f"Analyze this research for the {industry} sector in 2026. Context: {text[:80000]}."
    
    if role == "Venture Capital Partner":
        return f"""{base} 
        1. **Market Heatmap:** Rate the current 'Hotness' vs 'Saturation' of this idea in {industry}. 
        2. **The Wedge:** Smallest entry point. 
        3. **Decision Door:** (Table: Reversible vs Irreversible risks). 
        4. **ROI Forecast:** Why this is a 10x play or a waste of capital."""
    
    elif role == "Chief Technology Officer":
        return f"""{base} 
        1. **Friction Score (1-10):** Implementation difficulty. 
        2. **Technical Moat:** Can someone clone this with a basic prompt? 
        3. **Architecture (Graphviz DOT):** System logic flow in ```dot tags."""
    
    elif role == "Staff Software Engineer":
        return f"""{base} 
        1. **The Hack:** Shortest path to MVP. 
        2. **Agent Protocol:** Full .cursorrules instructions for AI code editors. 
        3. **Logic Map (Graphviz DOT):** Data pipeline in ```dot tags."""
    
    elif role == "Brand & Content Lead":
        return f"""{base} 
        1. **The ROI Hook:** Why this matters for business. 
        2. **Viral Blueprint:** LinkedIn/YouTube script. 
        3. **Industry 'Counter-Intuitive' Insight:** The one thing competitors are getting wrong."""
    return base

def download_arxiv_pdf(url):
    arxiv_id_match = re.search(r'(\d{4}\.\d{4,5})', url)
    if not arxiv_id_match: return None
    response = requests.get(f"https://arxiv.org/pdf/{arxiv_id_match.group(1)}.pdf", timeout=30)
    return BytesIO(response.content) if response.status_code == 200 else None

# --- 5. EXECUTION ---
st.title("ArchiTek // Market Intelligence")
st.markdown("Automating the path from **Academic Research** to **Market Dominance**.")

c1, c2 = st.columns(2)
with c1: url_in = st.text_input("arXiv URL", placeholder="https://arxiv.org/abs/...")
with c2: file_in = st.file_uploader("Upload PDF", type=["pdf"])

if st.button("Execute Strategic Audit") and active_key:
    stream = download_arxiv_pdf(url_in) if url_in else file_in
    if stream:
        with st.spinner("Auditing Market & Tech..."):
            try:
                genai.configure(api_key=active_key)
                pdf = PdfReader(stream)
                raw_text = "".join([p.extract_text() for p in pdf.pages])
                
                # Model selection
                available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model_name = next((m for m in available if 'flash' in m), available[0]).split('/')[-1]
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content(get_persona_prompt(user_persona, target_industry, raw_text))
                st.session_state.analysis_result = response.text
            except Exception as e:
                st.error(f"Audit Failed: {str(e)}")

# --- 6. OUTPUT ---
if st.session_state.analysis_result:
    st.markdown("---")
    st.markdown(st.session_state.analysis_result)
    
    match = re.search(r'```dot\n(.*?)\n```', st.session_state.analysis_result, re.DOTALL)
    if match:
        st.subheader("🏗️ System Flow")
        st.graphviz_chart(match.group(1))

    st.download_button("📥 Download Intelligence Report", st.session_state.analysis_result.encode('utf-8'), f"ArchiTek_Audit.md")
