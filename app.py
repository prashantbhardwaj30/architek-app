import streamlit as st
import os
import tempfile
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="ArchiTek | Blueprint Engine", page_icon="🏛️", layout="wide")

# Hide Streamlit default branding for a pro look
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {background-color: #0E1117; color: #FAFAFA;}
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: CREDENTIALS & BRANDING ---
with st.sidebar:
    st.title("🏛️ ArchiTek")
    st.markdown("**Whitepaper to Wallet.**")
    st.markdown("---")
    
    # Secure API Key Entry (Street Smart: Don't hardcode keys!)
    api_key = st.text_input("Enter Gemini API Key", type="password", help="Get it free at aistudio.google.com")
    
    st.markdown("---")
    st.info("💡 **Pro Tip:** Use 'Flash' model for speed, 'Pro' for deep logic.")

# --- 3. THE "BRAIN" SETUP ---
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    # Configure Gemini 1.5 Flash for Speed & Context
    Settings.llm = Gemini(model="models/gemini-1.5-flash", temperature=0.2)
    Settings.embed_model = GeminiEmbedding(model="models/text-embedding-004")
else:
    st.warning("⚠️ Please enter your Gemini API Key to initialize the Architect.")

# --- 4. MAIN INTERFACE ---
st.header("Build Your AI SaaS Blueprint")
st.markdown("Upload a research paper to generate the **Implementation Blueprint**.")

uploaded_file = st.file_uploader("Upload ArXiv PDF", type=['pdf'])

if uploaded_file and api_key:
    with st.spinner("Analyzing Architecture... (This may take 10-20s)"):
        
        # Save uploaded file temporarily for LlamaIndex processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # --- THE RAG PIPELINE ---
            documents = SimpleDirectoryReader(temp_dir).load_data()
            index = VectorStoreIndex.from_documents(documents)
            query_engine = index.as_query_engine()

            # --- THE "STREET SMART" PROMPT ---
            # This is where the magic happens. We force specific, actionable outputs.
            prompt = """
            You are a Senior AI Solutions Architect. Analyze this research paper for a Solopreneur who wants to build a SaaS.
            
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

            response = query_engine.query(prompt)
            
            # --- DISPLAY RESULTS ---
            st.markdown("---")
            st.markdown(response.response)
            
            st.success("✅ Blueprint Generated. Start building.")
