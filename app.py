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
    st.title("🏛️ ArchiTek // V5.1")
    st.caption("Strategic Intelligence Engine")
    st.markdown("---")
    
    st.subheader("🎯 Mission Brief")
    user_persona = st.selectbox(
        "Your Role",
        ("Venture Capital Partner", "Chief Technology Officer", "Staff Software Engineer", "Brand & Content Lead")
    )
    target_industry = st.text_input("Target Sector", value="General")
    
    st.markdown("---")
    active_key = sponsor_key or st.text_input("Enter API Key", type="password")

    st.subheader("🔗 Connect with me")
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

# --- 4. HELPER FUNCTIONS (The "Black Ops" Downloader) ---
def download_arxiv_pdf(url):
    # Regex to catch arXiv ID from links like /abs/2302.06544 or /pdf/2302.06544
    arxiv_id_match = re.search(r'(\d{4}\.\d{4,5})', url)
    if not arxiv_id_match:
        return None
    
    arxiv_id = arxiv_id_match.group(1)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    response = requests.get(pdf_url, timeout=30)
    if response.status_code == 200:
        return BytesIO(response.content)
    return None

def get_persona_prompt(role, industry, text):
    base = f"Analyze this research for {industry}. Context: {text[:80000]}."
    if role == "Venture Capital Partner":
        return f"{base} Focus: ROI. Output: 1. Market Wedge (Entry point), 2. Scaling Factor, 3. 'Decision Door' (Table: Reversible vs Irreversible risks). Use bold bullet points."
    elif role == "Chief Technology Officer":
        return f"{base} Focus: Implementation. Output: 1. Friction Score (1-10), 2. Integration Risks, 3. System Architecture (Graphviz DOT code in ```dot tags)."
    elif role == "Staff Software Engineer":
        return f"{base} Focus: Automation. Output: 1. Shortest MVP Path, 2. The Agent Protocol (.cursorrules for AI code editors), 3. Logic Flow (Graphviz DOT code in ```dot tags)."
    elif role == "Brand & Content Lead":
        return f"{base} Focus: Viral Growth. Output: 1. The ROI Value Hook, 2. LinkedIn & YouTube Content Blueprint, 3. 'OneUsefulThing' Insight."
    return base

# --- 5. EXECUTION LOOP ---
st.title("ArchiTek // Strategic Engine")
st.markdown("Paste an **arXiv URL** or upload a **PDF Dossier** to begin.")

col1, col2 = st.columns(2)
with col1:
    url_input = st.text_input("Enter arXiv URL", placeholder="https://arxiv.org/abs/2302.06544")
with col2:
    uploaded_file = st.file_uploader("Or Upload PDF", type=["pdf"])

if st.button("Execute Strategic Analysis") and active_key:
    pdf_stream = None
    
    # Logic: Prioritize URL if both are provided, or handle one
    if url_input:
        with st.spinner("Downloading from arXiv..."):
            pdf_stream = download_arxiv_pdf(url_input)
            if not pdf_stream:
                st.error("❌ Failed to download. Check the arXiv URL.")
    elif uploaded_file:
        pdf_stream = uploaded_file

    if pdf_stream:
        with st.spinner("Extracting Strategic Value..."):
            try:
                genai.configure(api_key=active_key)
                pdf = PdfReader(pdf_stream)
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
