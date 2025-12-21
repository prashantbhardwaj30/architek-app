import os
import re
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. CONFIGURATION ---
# Festive Christmas Update 🎄
st.set_page_config(page_title="ArchiTek | Intel Engine", page_icon="🎄", layout="wide")

# --- CSS: BLACK OPS & STEALTH MODE ---
st.markdown("""
<style>
    /* 1. HIDE ALL DEFAULT STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 2. NUCLEAR OPTION FOR THE TOOLBAR & DEPLOY BUTTON */
    [data-testid="stToolbar"] {
        visibility: hidden !important;
        display: none !important;
    }
    .stAppDeployButton {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 3. HIDE THE COLORED LINE AT THE TOP */
    [data-testid="stDecoration"] {
        visibility: hidden !important;
        display: none !important;
    }

    /* 4. BLACK OPS THEME */
    .stApp {background-color: #0E1117; color: #E6E6E6;}
    
    /* 5. INPUT FIELDS (Dark Mode) */
    .stTextInput > div > div > input {
        background-color: #161B22; 
        color: #FAFAFA; 
        border: 1px solid #30363D;
    }
    
    /* 6. GREEN ACTION BUTTON */
    .stButton > button {
        background-color: #238636 !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
    }
    
    /* 7. SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363D;
    }
    
    /* 8. REMOVE TOP PADDING */
    .block-container {
        padding-top: 1rem !important; 
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# --- 3. AUTH & SIDEBAR SETUP ---
try:
    sponsor_key = st.secrets["GOOGLE_API_KEY"]
except:
    sponsor_key = None

active_key = None

with st.sidebar:
    st.title("🏛️ ArchiTek // V4")
    st.caption("Adaptive Intelligence Engine")
    st.markdown("---")
    
    # --- MISSION BRIEF ---
    st.subheader("🎯 Mission Brief")
    
    user_persona = st.selectbox(
        "Your Role",
        ("Startup Founder", "Enterprise CTO", "Lead Engineer", "Content Creator (YouTube/LinkedIn)"),
        help="The AI will adapt its analysis to match your expertise."
    )
    
    target_industry = st.text_input(
        "Target Sector", 
        value="General",
        placeholder="e.g., Fintech, BioTech, Legal..."
    )
    
    st.markdown("---")
    
    # --- AUTH ---
    if sponsor_key:
        st.success("✅ **System Online**")
        active_key = sponsor_key
        with st.expander("Override Access Key"):
            active_key = st.text_input("API Key", type="password") or sponsor_key
    else:
        st.warning("⚠️ Manual Auth Required")
        active_key = st.text_input("Enter API Key", type="password")

    # --- ECOSYSTEM UPSELL ---
    st.markdown("---")
    st.caption("🚀 Built by [DesiAILabs](https://www.youtube.com/@DesiAILabs)")
    
    st.markdown("""
    <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-top: 10px;">
        <h4 style="margin: 0; color: #FAFAFA; font-size: 16px;">🎓 Learn to Build This</h4>
        <p style="font-size: 12px; color: #8b949e; margin: 5px 0 10px 0;">Master AI Agents & LLMs with Prashant Bhardwaj.</p>
        <a href="https://aigurukul.lovable.app" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; background-color: #238636; color: white; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer; transition: background-color 0.3s;">
                Join AI Gurukul
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- 4. PROMPT LOGIC: THE V5 BOARDROOM ---
def get_persona_prompt(role, industry, text):
    base_prompt = f"Analyze this research paper for the {industry} sector. Context: {text[:100000]}."
    
    if role == "Startup Founder":
        return f"""
        {base_prompt}
        ACT AS: A Board consisting of Jeff Bezos and Sam Altman.
        
        ## 1. The Opportunity (Altman's Wedge)
        * **The Wedge:** What is the smallest, most aggressive entry point into {industry}?
        * **Viral Coefficient:** How does this product grow naturally?
        * **The SaaS Concept:** A specific micro-SaaS title and value prop.

        ## 2. The Bezos Friction Scorecard
        * **Decision Type:** Is this a 'One-Way Door' (Complex/Hard to pivot) or 'Two-Way Door' (Easy to test)?
        * **Two-Pizza Team Requirement:** How many people are needed to build the MVP?
        * **Frugality Check:** What is the cheapest way to prove this works today?

        ## 3. Market Validation (Smoke Test)
        * **The "Zero-Dollar" Test:** Exactly how to validate demand without writing code.
        * **Target Metric:** What specific number (signups/clicks) proves this is a business?
        """
        
    elif role == "Enterprise CTO":
        return f"""
        {base_prompt}
        ACT AS: A Senior Principal Architect and Jeff Bezos.
        
        ## 1. Executive Risk Audit
        * **Implementation Friction:** On a scale of 1-10, how hard is this to integrate?
        * **Legacy Compatibility:** How does this disrupt existing {industry} stacks?
        * **One-Way Doors:** Identify the irreversible technical decisions in this paper.

        ## 2. Technical Architecture (Karpathy Style)
        * **The "Autonomy Slider":** How much of this can be handled by AI Agents vs. Human code?
        * **Architecture Diagram (Graphviz):** ```dot
        graph TD
        A[Input Data] --> B[Paper Logic]
        B --> C[API Layer]
        C --> D[User Value]
        ```
        """

    elif role == "Lead Engineer":
        return f"""
        {base_prompt}
        ACT AS: Andrej Karpathy (Software 3.0 approach).
        
        ## 1. The Logic Breakdown
        * **Neural Architecture:** How would a machine describe this logic?
        * **System Flow (Graphviz):** Provide a DOT code block showing the data pipeline.
        
        ## 2. The Agent Protocol (.cursorrules)
        * Create a system-level instruction for an AI Agent (Cursor/Windsurf).
        * Define the "Source of Truth" from the paper.
        * Structure: Folder hierarchy, tech stack, and safety constraints.
        
        ## 3. The Execution Hack
        * The 'Weekend Build' path: Which APIs to use to simulate the paper's results.
        """
    return base_prompt

# --- 5. EXECUTION ---
if active_key:
    genai.configure(api_key=active_key)
    
    st.title("ArchiTek // Intel Engine")
    st.markdown(f"**Mission:** Analyze Research for **{user_persona}** in **{target_industry}**.")

    uploaded_file = st.file_uploader("Upload Target Dossier (PDF)", type=["pdf"])

    if uploaded_file and st.button("Execute Analysis"):
        with st.spinner("Extracting Intel..."):
            try:
                # 1. READ PDF
                pdf = PdfReader(uploaded_file)
                text = "".join([p.extract_text() for p in pdf.pages])
                
                # 2. SMART MODEL SELECTOR
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                if not available_models:
                    st.error("❌ No models found. Check your API Key permissions.")
                    st.stop()
                
                # Prioritize Flash -> Pro
                model_name = next((m for m in available_models if 'flash' in m), None)
                if not model_name:
                    model_name = next((m for m in available_models if 'pro' in m), available_models[0])
                
                final_model_name = model_name.split('/')[-1]
                model = genai.GenerativeModel(final_model_name)
                
                # 3. GENERATE
                final_prompt = get_persona_prompt(user_persona, target_industry, text)
                response = model.generate_content(final_prompt)
                st.session_state.analysis_result = response.text
                
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    st.error("⚠️ **Quota Exceeded.** The sponsor key is overloaded. Use your own key in the sidebar.")
                else:
                    st.error(f"❌ Mission Failed: {str(e)}")

# --- 6. OUTPUT & DOWNLOAD ---
if st.session_state.analysis_result:
    st.markdown("---")
    st.markdown(st.session_state.analysis_result)
    
    # --- DIAGRAM RENDERER ---
    diagram_match = re.search(r'```dot\n(.*?)\n```', st.session_state.analysis_result, re.DOTALL)
    if diagram_match:
        st.subheader("🏗️ Architecture Diagram")
        try:
            st.graphviz_chart(diagram_match.group(1))
            st.caption("Visualized by ArchiTek Engine")
        except Exception as e:
            st.warning("Diagram could not be rendered automatically.")

    st.download_button(
        label="📥 Download Intel Report",
        data=st.session_state.analysis_result.encode('utf-8'),
        file_name=f"ArchiTek_{user_persona.replace(' ', '_')}_Report.md",
        mime="text/markdown"
    )

