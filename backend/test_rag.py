
from rag import load_pdf, split_docs, create_vectorstore, ask_question

# 📄 Load your file (put a sample.pdf in your project)
file_path = "sample.pdf"

docs = load_pdf(file_path)
chunks = split_docs(docs)
db = create_vectorstore(chunks)

query = input("Ask a question: ")
answer = ask_question(db, query)

print("\nAnswer:\n", answer)