import os
import re
import requests
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ArchiTek | Market Intel", page_icon="🎄", layout="wide")

# --- 2. THE ULTIMATE VISIBILITY CSS ---
st.markdown("""
<style>
    /* 1. Nuke Default Branding */
    header, footer, .stAppDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
        visibility: hidden !important; display: none !important;
    }
    
    /* 2. FORCE SIDEBAR VISIBILITY */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #30363D !important;
        visibility: visible !important;
        display: block !important;
    }
    
    /* 3. THEME & COLORS */
    .stApp {background-color: #0E1117; color: #E6E6E6;}
    .stTextInput > div > div > input { background-color: #161B22; color: #FAFAFA; border: 1px solid #30363D; }
    
    /* 4. SIDEBAR BUTTONS */
    .stSidebar .stButton > button { 
        background-color: #238636 !important; 
        color: white !important; 
        font-weight: bold; 
        border: none !important; 
        width: 100% !important;
        padding: 10px !important;
        margin-top: 10px;
    }

    /* 5. MAIN EXECUTE BUTTON */
    div.stButton > button:first-child {
        background-color: #238636 !important;
        color: white !important;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
    
    .block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. BRANDED SIDEBAR ---
try:
    sponsor_key = st.secrets["GOOGLE_API_KEY"]
except:
    sponsor_key = None

with st.sidebar:
    st.title("🏛️ ArchiTek // V7")
    st.caption("Strategic Intelligence Engine")
    st.markdown("---")
    
    st.subheader("🎯 Mission Brief")
    user_role = st.selectbox(
        "Your Role",
        ("Venture Capital Partner", "Chief Technology Officer", "Staff Software Engineer", "Brand & Content Lead")
    )
    industry = st.text_input("Target Sector", value="General")
    
    st.markdown("---")
    auth_key = sponsor_key or st.text_input("Enter API Key", type="password")

    # --- PERSONAL BRAND ASSETS ---
    st.subheader("🔗 Connect")
    st.markdown("""
        <a href="https://www.linkedin.com/in/prashantbhardwaj30/" target="_blank">
            <button style="width: 100%; background-color: #0077B5; color: white; border: none; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; cursor: pointer;">LinkedIn Profile</button>
        </a>
        <a href="https://www.youtube.com/@DesiAILabs" target="_blank">
            <button style="width: 100%; background-color: #FF0000; color: white; border: none; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; cursor: pointer;">YouTube: Desi AI Labs</button>
        </a>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d;">
        <h4 style="margin: 0; color: #FAFAFA; font-size: 14px;">🎓 AI Gurukul</h4>
        <p style="font-size: 11px; color: #8b949e; margin: 5px 0 10px 0;">Build AI Agents with Prashant Bhardwaj.</p>
        <a href="https://aigurukul.lovable.app" target="_blank">
            <button style="width: 100%; background-color: #238636; color: white; border: none; padding: 10px; border-radius: 5px; font-weight: bold; cursor: pointer;">Join Training</button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- 4. ENGINE LOGIC ---
def get_strategic_prompt(role, ind, txt):
    # Optimized for CRISP and CLEAR output
    base = f"Analyze this research for {ind}. Be extremely concise. Use tables and bullet points only."
    
    if role == "Venture Capital Partner":
        return f"{base} Context: {txt[:80000]}. Provide: 1. Market Heatmap, 2. Decision Door Table (Reversible vs Not), 3. ROI Wedge."
    elif role == "Chief Technology Officer":
        return f"{base} Context: {txt[:80000]}. Provide: 1. Friction Score (1-10), 2. Implementation Risks, 3. Architecture (Graphviz DOT in ```dot tags)."
    elif role == "Staff Software Engineer":
        return f"{base} Context: {txt[:80000]}. Provide: 1. MVP Path, 2. .cursorrules code block, 3. Flow Diagram (Graphviz DOT in ```dot tags)."
    elif role == "Brand & Content Lead":
        return f"{base} Context: {txt[:80000]}. Provide: 1. The ROI Hook, 2. LinkedIn Post Draft, 3. YouTube Short Script."
    return base

# --- 5. INTERFACE & EXECUTION ---
st.title("ArchiTek // Market Intelligence")
st.caption("Turning Academic Research into Market Dominance.")

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
        except: st.error("arXiv URL Error")
    else: stream = up_file

    if stream:
        with st.spinner("Auditing..."):
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
                st.error(f"Error: {e}")
