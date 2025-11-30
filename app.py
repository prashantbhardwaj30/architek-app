import os
import tempfile
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

st.set_page_config(page_title="ArchiTek | Blueprint Engine", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {background-color: #0E1117; color: #FAFAFA;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🏛️ ArchiTek")
    st.markdown("**Whitepaper to Wallet.**")
    st.markdown("---")
    
    api_key = st.text_input(
        "Enter Gemini API Key",
        type="password",
        help="Get it from ai.google.dev/aistudio",
    )
    st.markdown("---")

if api_key:
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        st.sidebar.success(f"✅ API Key Valid")
        st.sidebar.info(f"📋 Available models:\n\n" + "\n".join([f"• {m.split('/')[-1]}" for m in available_models[:5]]))
        
        # Try to use the best available model
        model_to_use = None
        preferred_models = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        for preferred in preferred_models:
            for available in available_models:
                if preferred in available:
                    model_to_use = available.split('/')[-1]  # Remove 'models/' prefix
                    break
            if model_to_use:
                break
        
        if not model_to_use and available_models:
            # Use first available model
            model_to_use = available_models[0].split('/')[-1]
        
        if model_to_use:
            model = genai.GenerativeModel(model_to_use)
            models_ready = True
            st.sidebar.info(f"🤖 Using: **{model_to_use}**")
        else:
            st.error("❌ No compatible models found")
            models_ready = False
            
    except Exception as e:
        st.error(f"❌ API Key Error: {str(e)}")
        models_ready = False
else:
    st.warning("⚠️ Enter your Gemini API Key")
    models_ready = False

st.header("Build Your AI SaaS Blueprint")
st.markdown("Upload a research paper to generate the **Implementation Blueprint**.")

uploaded_file = st.file_uploader("Upload ArXiv PDF", type=["pdf"])

if uploaded_file and models_ready:
    with st.spinner("Analyzing... (10-20s)"):
        try:
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            text = text[:100000]
            
            prompt = f"""
You are a Senior AI Solutions Architect. Analyze this research paper for a Solopreneur who wants to build a SaaS.

RESEARCH PAPER:
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
            st.success("✅ Blueprint Generated. Start building.")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
