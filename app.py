import os
import re
import requests
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ArchiTek | Market Intel", page_icon="🎄", layout="wide")

# --- 2. THE BRAND-SAFE STEALTH CSS ---
st.markdown("""
<style>
    /* 1. NUKE STREAMLIT DEFAULT BRANDING ONLY */
    header, footer, .stAppDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
        visibility: hidden !important; display: none !important;
    }
    
    /* 2. PROTECT THE SIDEBAR & BRANDING */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #30363D !important;
        visibility: visible !important;
    }
    
    /* 3. BRAND LINK BUTTONS (Custom Styling) */
    .brand-btn {
        display: block;
        width: 100%;
        padding: 12px;
        margin: 10px 0;
        text-align: center;
        text-decoration: none;
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        cursor: pointer;
    }
    .linkedin { background-color: #0077B5; }
    .youtube { background-color: #FF0000; }
    .gurukul { background-color: #238636; border: 1px solid #30363D; }

    /* 4. THEME & INPUTS */
    .stApp {background-color: #0E1117; color: #E6E6E6;}
    .stTextInput > div > div > input { background-color: #161B22; color: #FAFAFA; border: 1px solid #30363D; }
    
    /* 5. MAIN ACTION BUTTON */
    div.stButton > button {
        background-color: #238636 !important;
        color: white !important;
        height: 3.5em;
        width: 100%;
        font-weight: bold;
        border: none !important;
    }
    
    .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. THE BRANDED SIDEBAR ---
try:
    sponsor_key = st.secrets["GOOGLE_API_KEY"]
except:
    sponsor_key = None

with st.sidebar:
    st.title("🏛️ ArchiTek // V8")
    st.caption("Strategic Intelligence Engine")
    st.markdown("---")
    
    # MISSION BRIEF
    st.subheader("🎯 Mission Brief")
    user_role = st.selectbox(
        "Your Role",
        ("Venture Capital Partner", "Chief Technology Officer", "Staff Software Engineer", "Brand & Content Lead")
    )
    industry = st.text_input("Target Sector", value="General")
    
    st.markdown("---")
    auth_key = sponsor_key or st.text_input("Enter API Key", type="password")

    # --- BRAND LINKS (Hard-coded HTML to prevent hiding) ---
    st.subheader("🔗 Founder Links")
    st.markdown(f"""
        <a class="brand-btn linkedin" href="https://www.linkedin.com/in/prashantbhardwaj30/" target="_blank">LinkedIn Profile</a>
        <a class="brand-btn youtube" href="https://www.youtube.com/@DesiAILabs" target="_blank">YouTube: Desi AI Labs</a>
        <div style="margin-top: 20px; padding: 15px; background: #161b22; border-radius: 10px; border: 1px solid #30363d;">
            <p style="font-size: 13px; color: #FAFAFA; margin-bottom: 10px; font-weight: bold;">🎓 AI Gurukul Training</p>
            <a class="brand-btn gurukul" href="https://aigurukul.lovable.app" target="_blank">Join Program</a>
        </div>
    """, unsafe_allow_html=True)

# --- 4. ENGINE LOGIC ---
def get_strategic_prompt(role, ind, txt):
    # Enforced CRISP/CLEAR output via direct instruction
    base = f"Analyze research for {ind}. Be concise. Use Markdown tables/bullets only."
    
    if role == "Venture Capital Partner":
        return f"{base} Context: {txt[:80000]}. 1. Market Heatmap, 2. Decision Door Table, 3. ROI Wedge."
    elif role == "Chief Technology Officer":
        return f"{base} Context: {txt[:80000]}. 1. Friction Score, 2. Technical Moat, 3. Architecture (Graphviz DOT in ```dot tags)."
    elif role == "Staff Software Engineer":
        return f"{base} Context: {txt[:80000]}. 1. MVP Hack, 2. .cursorrules code block, 3. Logic Flow (Graphviz DOT in ```dot tags)."
    elif role == "Brand & Content Lead":
        return f"{base} Context: {txt[:80000]}. 1. ROI Value Hook, 2. LinkedIn Post Draft, 3. YouTube Short Script."
    return base

# --- 5. INTERFACE & EXECUTION ---
st.title("ArchiTek // Market Intelligence")
st.markdown("Turning Academic Research into Market Dominance.")

c1, c2 = st.columns(2)
with c1: url = st.text_input("arXiv URL", placeholder="https://arxiv.org/abs/...")
with c2: up_file = st.file_uploader("Or Upload PDF", type=["pdf"])

if st.button("Execute Strategic Audit") and auth_key:
    stream = None
    if url:
        try:
            id_match = re.search(r'(\d{4}\.\d{4,5})', url)
            res = requests.get(f"https://arxiv.org/pdf/{id_match.group(1)}.pdf", timeout=20)
            stream = BytesIO(res.content)
        except: st.error("Invalid arXiv URL format.")
    else: stream = up_file

    if stream:
        with st.spinner("Auditing Intelligence..."):
            try:
                genai.configure(api_key=auth_key)
                reader = PdfReader(stream)
                data = "".join([p.extract_text() for p in reader.pages])
                
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in models if 'flash' in m), models[0]).split('/')[-1]
                
                resp = genai.GenerativeModel(m_name).generate_content(get_strategic_prompt(user_role, industry, data))
                
                st.markdown("---")
                st.markdown(resp.text)
                
                dot_match = re.search(r'```dot\n(.*?)\n```', resp.text, re.DOTALL)
                if dot_match:
                    st.graphviz_chart(dot_match.group(1))
            except Exception as e:
                st.error(f"Execution Error: {e}")
