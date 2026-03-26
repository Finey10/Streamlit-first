
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq

import os

# 🔑 Load API keys from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# 📄 Step 1: Load PDF
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return documents


# ✂️ Step 2: Split into chunks
def split_docs(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return splitter.split_documents(documents)


# 🧠 Step 3: Create vector store
def create_vectorstore(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )

    db = FAISS.from_documents(chunks, embeddings)
    return db


# 🤖 Step 4: Ask question
def ask_question(db, query):
    docs = db.similarity_search(query)

    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=GROQ_API_KEY
    )

    context = "\n".join([doc.page_content for doc in docs])

    prompt = f"""
    Answer the question based on the context below.

    Context:
    {context}

    Question:
    {query}
    """

    response = llm.invoke(prompt)
    return response.content