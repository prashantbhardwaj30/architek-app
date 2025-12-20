import os
import re
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ArchiTek | Intel Engine", page_icon="🏛️", layout="wide")

# Black Ops Style CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;} 
    
    .stApp {background-color: #0E1117; color: #E6E6E6;}
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #161B22; 
        color: #FAFAFA; 
        border: 1px solid #30363D;
    }
    
    /* Green Action Button */
    .stButton > button {
        background-color: #238636 !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# --- 3. AUTH & SETUP ---
try:
    sponsor_key = st.secrets["GOOGLE_API_KEY"]
except:
    sponsor_key = None

active_key = None

with st.sidebar:
    st.title("🏛️ ArchiTek // V3")
    st.caption("Adaptive Intelligence Engine")
    st.markdown("---")
    
    # --- MISSION BRIEF ---
    st.subheader("🎯 Mission Brief")
    
    user_persona = st.selectbox(
        "Your Role",
        ("Startup Founder", "Enterprise CTO", "Strategy Consultant", "Lead Engineer"),
        help="The AI will adapt its analysis to match your expertise."
    )
    
    target_industry = st.text_input(
        "Target Sector", 
        value="General",
        placeholder="e.g., Fintech, BioTech, Legal..."
    )
    
    st.markdown("---")
    
    if sponsor_key:
        st.success("✅ **System Online**")
        active_key = sponsor_key
        with st.expander("Override Access Key"):
            active_key = st.text_input("API Key", type="password") or sponsor_key
    else:
        st.warning("⚠️ Manual Auth Required")
        active_key = st.text_input("Enter API Key", type="password")

# --- 4. PROMPT LOGIC ---
def get_persona_prompt(role, industry, text):
    base_prompt = f"Analyze this research paper. Context: {text[:100000]}."
    
    if role == "Startup Founder":
        return f"""
        {base_prompt}
        ACT AS: A ruthless VC & Product Architect.
        GOAL: Extract a money-making SaaS idea for the {industry} sector.
        
        OUTPUT FORMAT:
        ## 1. The Opportunity (Money)
        * **The Pain Point:** What expensive problem does this solve?
        * **The Solution:** A micro-SaaS concept for {industry}.
        * **Unfair Advantage:** Why this tech beats standard GPT-4 wrappers.
        
        ## 2. The Mechanics (Logic)
        * **Secret Sauce:** The one logic/equation that matters (Explain simply).
        * **Executive Pseudo-Code:** IF/THEN logic of the core algorithm.
        
        ## 3. Go-To-Market
        * **First 10 Customers:** Exactly who to email.
        * **Pricing Model:** How to charge (Sub vs Usage).
        """
        
    elif role == "Enterprise CTO":
        return f"""
        {base_prompt}
        ACT AS: A Senior Principal Architect at a Fortune 500 company.
        GOAL: Assess technical feasibility and risk for {industry} adoption.
        
        OUTPUT FORMAT:
        ## 1. Executive Summary
        * **Strategic Value:** Does this move the needle for {industry}?
        * **Build vs. Buy:** Should we build this internally or wait for a vendor?
        
        ## 2. Technical Architecture
        * **Core Components:** Required infrastructure (Vector DBs, GPU specs).
        * **Latency & Cost Analysis:** Is this computationally expensive?
        * **Integration Risks:** Security/Compliance red flags for {industry}.
        
        ## 3. Implementation Roadmap
        * **Phase 1 (POC):** Success metrics.
        * **Phase 2 (Scale):** Infrastructure requirements.

        ## 4. Architecture Diagram (Graphviz)
        * Create a VALID Graphviz DOT code block representing the system architecture.
        * Wrap it in ```dot ... ``` tags.
        * Use rectangular nodes for components and labeled edges for data flow.
        """

    elif role == "Strategy Consultant":
        return f"""
        {base_prompt}
        ACT AS: A Partner at McKinsey/Deloitte.
        GOAL: Create a briefing for a C-Level client in {industry}.
        
        OUTPUT FORMAT:
        ## 1. The "So What?"
        * **Market Impact:** How this disrupts the current {industry} value chain.
        * **Competitive Threat:** What happens if competitors adopt this first?
        
        ## 2. Strategic Use Cases
        * **Efficiency Play:** How to cut costs.
        * **Innovation Play:** New revenue streams enabled by this research.
        
        ## 3. The Pitch (Slide Content)
        * **Slide 1 Headline:** The "Hook".
        * **Key Statistic/Insight:** The strongest data point from the paper.
        * **Recommendation:** Immediate next steps.
        """

    elif role == "Lead Engineer":
        return f"""
        {base_prompt}
        ACT AS: A Staff Engineer / Hacker.
        GOAL: How do I build this this weekend?
        
        OUTPUT FORMAT:
        ## 1. The Hack
        * **Core Logic:** The breakdown of the algorithm (No math jargon).
        * **The "Trick":** What makes this work? (e.g., specific prompting, graph traversal).
        
        ## 2. Implementation Guide
        * **Stack Recommendation:** Python + [Libraries].
        * **Pseudo-Code:** Clean, readable logic flow.
        * **Gotchas:** What will break? (e.g., Context window limits, hallucinations).
        
        ## 3. MVP Spec
        * **Minimal Feature Set:** The smallest version of this code that works.

        ## 4. System Flow (Graphviz)
        * Create a VALID Graphviz DOT code block showing the data pipeline.
        * Wrap it in ```dot ... ``` tags.
        * Keep it simple: Input -> Process -> Output.
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
                
                # 2. SMART MODEL SELECTOR (THE FIX)
                # Instead of hardcoding, we ask Google what models are available
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                if not available_models:
                    st.error("❌ No models found. Check your API Key permissions.")
                    st.stop()
                
                # Prioritize Flash for speed, then Pro, then others
                model_name = next((m for m in available_models if 'flash' in m), None)
                if not model_name:
                    model_name = next((m for m in available_models if 'pro' in m), available_models[0])
                
                # Clean the model name (remove 'models/' prefix if needed for instantiation)
                final_model_name = model_name.split('/')[-1]
                model = genai.GenerativeModel(final_model_name)
                
                # 3. GENERATE
                final_prompt = get_persona_prompt(user_persona, target_industry, text)
                response = model.generate_content(final_prompt)
                st.session_state.analysis_result = response.text
                
            except Exception as e:
                # Better Error Messages
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    st.error("⚠️ **Quota Exceeded.** The sponsor key is overloaded. Use your own key in the sidebar.")
                else:
                    st.error(f"❌ Mission Failed: {str(e)}")

# --- 6. OUTPUT & DOWNLOAD ---
if st.session_state.analysis_result:
    st.markdown("---")
    st.markdown(st.session_state.analysis_result)
    
    # --- DIAGRAM RENDERER ---
    # Looks for ```dot code blocks and renders them
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
