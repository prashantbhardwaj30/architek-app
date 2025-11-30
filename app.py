import os
import tempfile
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings

# --- NEW V2 IMPORTS (Crucial for your requirements.txt) ---
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="ArchiTek | Blueprint Engine",
    page_icon="🏛️",
    layout="wide",
)

# Hide Streamlit default branding for a pro look
st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp {background-color: #0E1117; color: #FAFAFA;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 2. SIDEBAR: CREDENTIALS & BRANDING ---
with st.sidebar:
    st.title("🏛️ ArchiTek")
    st.markdown("**Whitepaper to Wallet.**")
    st.markdown("---")

    # Secure API Key Entry
    api_key = st.text_input(
        "Enter Gemini API Key",
        type="password",
        help="Get it free from Google AI Studio",
    )

    st.markdown("---")
    st.info("💡 **Status:** V2 Stack (Google GenAI) Active")

# --- 3. THE "BRAIN" SETUP ---
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

    # LLM: Using the specific version ID to prevent alias errors
    Settings.llm = GoogleGenAI(
        model="models/gemini-1.5-flash-001", 
        temperature=0.2,
        api_key=api_key,
    )

    # Embeddings: Updated to the latest stable text-embedding-004
    Settings.embed_model = GoogleGenAIEmbedding(
        model_name="models/text-embedding-004", 
        api_key=api_key,
    )
else:
    st.warning("⚠️ Please enter your Gemini API Key to initialize the Architect.")

# --- 4. MAIN INTERFACE ---
st.header("Build Your AI SaaS Blueprint")
st.markdown("Upload a research paper to generate the **Implementation Blueprint**.")

uploaded_file = st.file_uploader("Upload ArXiv PDF", type=["pdf"])

if uploaded_file and api_key:
    with st.spinner("Analyzing Architecture... (This may take 10-20s)"):
        # Save uploaded file temporarily for LlamaIndex processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # --- THE RAG PIPELINE ---
            documents = SimpleDirectoryReader(temp_dir).load_data()
            
            # Create Index (In-memory for MVP speed)
            index = VectorStoreIndex.from_documents(documents)
            query_engine = index.as_query_engine()

            # --- THE "STREET SMART" PROMPT (Kept Original) ---
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

            try:
                response = query_engine.query(prompt)

                # --- DISPLAY RESULTS ---
                st.markdown("---")
                st.markdown(response.response)
                st.success("✅ Blueprint Generated. Start building.")
                
            except Exception as e:
                st.error(f"❌ Something went wrong: {e}")

elif not api_key:
    st.info("🔑 Enter your Gemini API key in the sidebar to start.")
