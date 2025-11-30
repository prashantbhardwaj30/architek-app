import os
import tempfile

import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding


st.set_page_config(
    page_title="ArchiTek | Blueprint Engine",
    page_icon="🏛️",
    layout="wide",
)

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

with st.sidebar:
    st.title("🏛️ ArchiTek")
    st.markdown("**Whitepaper to Wallet.**")
    st.markdown("---")

    api_key = st.text_input(
        "Enter OpenAI API Key",
        type="password",
        help="Get it from platform.openai.com",
    )

    st.markdown("---")
    st.info("💡 **Pro Tip:** This uses GPT-4 for deep analysis.")

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
    
    try:
        Settings.llm = OpenAI(
            model="gpt-4o-mini",  # Fast and cheap
            api_key=api_key,
            temperature=0.2,
        )

        Settings.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=api_key,
        )
        
        models_initialized = True
        
    except Exception as e:
        st.error(f"❌ Failed to initialize models: {str(e)}")
        models_initialized = False
else:
    st.warning("⚠️ Please enter your OpenAI API Key to initialize the Architect.")
    models_initialized = False

st.header("Build Your AI SaaS Blueprint")
st.markdown("Upload a research paper to generate the **Implementation Blueprint**.")

uploaded_file = st.file_uploader("Upload ArXiv PDF", type=["pdf"])

if uploaded_file and api_key and models_initialized:
    with st.spinner("Analyzing Architecture... (This may take 10–20s)"):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                documents = SimpleDirectoryReader(temp_dir).load_data()
                index = VectorStoreIndex.from_documents(documents)
                query_engine = index.as_query_engine()

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
                st.markdown("---")
                st.markdown(response.response)
                st.success("✅ Blueprint Generated. Start building.")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            
elif uploaded_file and not models_initialized:
    st.error("⚠️ Models not initialized. Check your API key.")
