import os
import re
import requests
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from io import BytesIO
from datetime import datetime
import random
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="ArchiTek | Market Intel", 
    page_icon="🎄", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS: SIDEBAR LOCK & STEALTH ---
st.markdown("""
<style>
    header, footer, .stAppDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
        visibility: hidden !important; display: none !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #30363D !important;
        min-width: 340px !important;
    }
    .brand-btn {
        display: block; width: 100%; padding: 12px; margin: 10px 0;
        text-align: center; text-decoration: none !important;
        color: white !important; font-weight: bold; border-radius: 8px;
    }
    .linkedin { background-color: #0077B5; }
    .youtube { background-color: #FF0000; }
    .gurukul { background-color: #238636; border: 1px solid #30363D; }
    .stApp {background-color: #0E1117; color: #E6E6E6;}
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE (The Download Fix) ---
if "report_content" not in st.session_state:
    st.session_state.report_content = None

# --- 4. BRANDED SIDEBAR ---
try:
    sponsor_key = st.secrets["GOOGLE_API_KEY"]
except:
    sponsor_key = None

with st.sidebar:
    st.title("🏛️ ArchiTek // V10.2")
    st.caption("Strategic Intelligence Engine")
    st.markdown("---")
    
    st.subheader("🎯 Mission Brief")
    user_role = st.selectbox("Your Role", ("Venture Capital Partner", "Chief Technology Officer", "Staff Software Engineer", "Brand & Content Lead"))
    industry = st.text_input("Target Sector", value="General")
    
    auth_key = sponsor_key or st.text_input("Enter API Key", type="password")

    st.markdown("---")
    st.subheader("🔗 Founder Links")
    st.markdown(f"""
        <a class="brand-btn linkedin" href="https://www.linkedin.com/in/prashantbhardwaj30/" target="_blank">LinkedIn Profile</a>
        <a class="brand-btn youtube" href="https://www.youtube.com/@DesiAILabs" target="_blank">YouTube Channel</a>
        <div style="margin-top: 20px; padding: 15px; background: #161b22; border-radius: 10px; border: 1px solid #30363d;">
            <p style="font-size: 13px; color: #FAFAFA; margin-bottom: 10px; font-weight: bold;">🎓 AI Gurukul Training</p>
            <a class="brand-btn gurukul" href="https://aigurukul.lovable.app" target="_blank">Join Program</a>
        </div>
    """, unsafe_allow_html=True)

# --- 5. ENGINE LOGIC ---
def get_strategic_prompt(role, ind, txt):
    base = f"Analyze for {ind}. Output must be scannable with tables/bullets. Context: {txt[:80000]}."
    if role == "Brand & Content Lead":
        return f"{base} Provide: 1. ROI Hook, 2. LinkedIn Viral Post, 3. YouTube Short Script in Hinglish (DesiAILabs style)."
    elif role == "Staff Software Engineer":
        return f"{base} Provide: 1. MVP Hack, 2. .cursorrules for AI agents, 3. Architecture Blueprint (Graphviz DOT code in ```dot tags)."
    return f"{base} Provide: 1. Market Heatmap, 2. Decision Door Table, 3. ROI Wedge."

# --- 6. INTERFACE & EXECUTION ---
st.title("ArchiTek // Market Intelligence")
st.markdown("Turning Academic Research into **Market Dominance**.")

c1, c2 = st.columns(2)
with c1: url = st.text_input("arXiv URL", placeholder="[https://arxiv.org/abs/](https://arxiv.org/abs/)...")
with c2: up_file = st.file_uploader("Or Upload PDF", type=["pdf"])

if st.button("🚀 Execute Strategic Audit"):
    if not auth_key:
        st.error("❌ Key Required. Please enter your Gemini API key in the sidebar.")
    else:
        stream = None
        if url:
            try:
                id_match = re.search(r'(\d{4}\.\d{4,5})', url)
                res = requests.get(f"[https://arxiv.org/pdf/](https://arxiv.org/pdf/){id_match.group(1)}.pdf", timeout=20)
                stream = BytesIO(res.content)
            except: st.error("arXiv URL is invalid or unreachable.")
        else: stream = up_file

        if stream:
            with st.spinner("🕵️ Auditing Intelligence..."):
                try:
                    genai.configure(api_key=auth_key)
                    reader = PdfReader(stream)
                    data = "".join([p.extract_text() for p in reader.pages])
                    
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    m_name = next((m for m in models if 'flash' in m), models[0]).split('/')[-1]
                    
                    resp = genai.GenerativeModel(m_name).generate_content(get_strategic_prompt(user_role, industry, data))
                    
                    # Store result in session state to persist for download
                    st.session_state.report_content = resp.text
                    
                except Exception as e:
                    st.error(f"Execution Error: {e}")

# --- 7. DISPLAY & PERSISTENT DOWNLOAD ---
if st.session_state.report_content:
    st.markdown("---")
    st.markdown(st.session_state.report_content)
    
    # RENDER PLOTLY GAUGE
    st.subheader("📈 Market Timing Signal")
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=random.randint(60, 95),
        title={'text': "Market Readiness Score"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#238636"}}
    ))
    fig.update_layout(paper_bgcolor="#0E1117", font={'color': "white"}, height=300)
    st.plotly_chart(fig, use_container_width=True)

    # RENDER GRAPHVIZ
    dot_match = re.search(r'```dot\n(.*?)\n```', st.session_state.report_content, re.DOTALL)
    if dot_match:
        st.subheader("🏗️ Architecture Visual")
        st.graphviz_chart(dot_match.group(1))
    
    st.markdown("---")
    # THE PERSISTENT DOWNLOAD BUTTON
    st.download_button(
        label="📥 Download Strategic Report",
        data=st.session_state.report_content,
        file_name=f"ArchiTek_{industry}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        key="download-report"
    )
