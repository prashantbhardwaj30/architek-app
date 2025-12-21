Here is the **Complete, "Creator-Ready" `app.py**`.

It includes everything we discussed:

* **🎄 Christmas Icon**: Set in the page config.
* **🕵️‍♂️ Stealth Mode (Updated)**: Aggressively hides the "Manage App" button and Streamlit badges.
* **🎥 Creator Persona**: New mode to generate scripts for **DesiAILabs** and **LinkedIn**.
* **🎓 Ecosystem Upsell**: The sidebar card linking to your **AI Gurukul**.
* **🤖 Agent Handoff**: The `.cursorrules` generator for engineers.

### 📋 Instructions

1. **Copy** the code below.
2. **Paste** it into your `app.py` (overwrite everything).
3. **Commit** to GitHub.

```python
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

    # --- ECOSYSTEM UPSELL (Step 3 Integration) ---
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

    elif role == "Lead Engineer":
        return f"""
        {base_prompt}
        ACT AS: A Staff Engineer & AI Agent Architect.
        GOAL: Create the "Spec File" to feed into an AI Code Editor (Cursor/Windsurf).
        
        OUTPUT FORMAT:
        ## 1. The Hack
        * **Core Logic:** The breakdown of the algorithm (No math jargon).
        * **The "Trick":** What makes this work? (e.g., specific prompting, graph traversal).
        
        ## 2. Implementation Guide
        * **Stack Recommendation:** Python + [Libraries].
        * **Gotchas:** What will break? (e.g., Context window limits, hallucinations).
        
        ## 3. System Flow (Graphviz)
        * Create a VALID Graphviz DOT code block showing the data pipeline.
        * Wrap it in ```dot ... ``` tags.
        
        ## 4. The Agent Protocol (.cursorrules)
        * Write a comprehensive system prompt that I can paste into a `.cursorrules` file.
        * **Context:** Tell the AI Agent exactly what this project is.
        * **File Structure:** Define the folder structure (app.py, requirements.txt, /src).
        * **Coding Standards:** "Use Python 3.9+, Type Hinting, no spaghetti code."
        * **Goal:** "Build the MVP described in the Analysis above."
        """

    elif role == "Content Creator (YouTube/LinkedIn)":
        return f"""
        {base_prompt}
        ACT AS: A Viral Tech Influencer & Educator (like 'DesiAILabs').
        GOAL: Turn this complex research paper into engaging content for a mass audience.
        
        OUTPUT FORMAT:
        ## 1. The YouTube Short (60s Script)
        * **Hook (0-5s):** A shocking fact/statement from the paper.
        * **The "What" (5-30s):** Explain the core breakthrough in simple Hindi/English (Hinglish).
        * **The "Wow" (30-50s):** Show a specific capability or result.
        * **CTA (50-60s):** "Check the link in bio for the full blueprint."
        
        ## 2. The LinkedIn Carousel (5 Slides)
        * **Slide 1:** The "Clickbait" Title (e.g., "RAG is Dead?").
        * **Slide 2:** The Problem (The "Before").
        * **Slide 3:** The Solution (The Paper's Logic).
        * **Slide 4:** The Architecture Diagram (Describe it).
        * **Slide 5:** "Steal this Workflow" (Link to ArchiTek).
        
        ## 3. The "OneUsefulThing" Insight (Blog)
        * **The Big Shift:** How this changes the AI landscape in 2026.
        * **Analogy:** Explain the tech using a real-world analogy (e.g., "Like a Librarian with a photographic memory").
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
                
                # 2. SMART MODEL SELECTOR (Resolves 404 Error)
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

```
