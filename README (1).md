# 🎓 ExamPrep AI — Academic Assistant

> An AI-powered exam preparation assistant built with LangChain, Google Gemini, and Streamlit.  
> Upload your lecture notes, textbooks, and previous year question papers — then ask anything.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 Multi-format upload | PDF, DOCX, PPTX, TXT — auto content-type detection |
| 🔍 Multi-source RAG | Combines notes + textbook + question papers for answers |
| 📖 Topic explanations | Comprehensive theory with examples, exam angles |
| 📝 Exam Q solver | Solves previous year questions step-by-step |
| 🎯 Exam Mode | Timed MCQ quiz generated from your own materials |
| 📊 Progress tracker | Topic mastery scores, weak area detection |
| 📅 Study planner | Personalised day-wise study plans |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/examprep-ai.git
cd examprep-ai
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get your free Gemini API key
1. Go to [https://aistudio.google.com](https://aistudio.google.com)
2. Click **"Get API key"** → **"Create API key"**
3. Copy the key (starts with `AIza...`)

### 5. Run the app
```bash
streamlit run app.py
```

### 6. Open in browser
Visit [http://localhost:8501](http://localhost:8501)

---

## 📁 Project Structure

```
examprep-ai/
├── app.py                      # Main Streamlit entry point
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── agent.py                # LangChain + Gemini agent (core RAG)
│   ├── document_processor.py  # PDF/DOCX/PPTX extraction + FAISS indexing
│   ├── chat.py                 # Study chat UI component
│   ├── upload.py               # Upload materials UI component
│   ├── progress.py             # Progress dashboard UI component
│   ├── progress_tracker.py    # SQLite-backed progress tracking
│   └── exam_mode.py            # Timed quiz generator + scorer
└── data/
    ├── uploads/                # Saved uploaded files
    ├── faiss_index/            # FAISS vector indexes (per subject)
    └── db/                     # SQLite progress database
```

---

## 🧠 Architecture

```
Student → Streamlit UI
            ↓
       LangChain Agent  (intent classification → prompt selection)
            ↓
     [RAG Retrieval via FAISS]  →  Google Gemini API
            ↓
     Structured Answer + Sources
            ↓
     SQLite Progress Tracking
```

### Multi-Source RAG Pipeline
1. **Upload** → PyPDF2 / python-docx / python-pptx extract raw text
2. **Chunk** → 800-char overlapping chunks with paragraph-aware splitting
3. **Content type detection** → question_paper / textbook / lecture_notes / lab_manual
4. **Embed** → Google `embedding-001` model via LangChain
5. **Store** → FAISS index saved per subject
6. **Retrieve** → Top-6 similarity search with optional content-type filter
7. **Generate** → Gemini 1.5 Flash with subject-aware system prompt

---

## 💬 Example Queries

```
"Explain Database Normalization with examples"
"Solve Q3 from 2022 DBMS paper — Boyce-Codd Normal Form"
"Create a 10-question quiz on OS scheduling algorithms"
"I'm struggling with process synchronization — help me understand"
"Give me a 7-day study plan for my DBMS exam"
"What are the most likely exam questions on SQL joins?"
```

---

## 🌐 Deploy to Streamlit Cloud (Free)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → set `app.py` as entry point
4. Add `GOOGLE_API_KEY` in **Secrets** (or enter it in the UI)
5. Deploy!

---

## 🗺️ Roadmap

| Week | Milestone |
|---|---|
| 1–2 | ✅ Document upload + FAISS pipeline + basic Streamlit UI |
| 3–4 | ✅ LangChain agent + topic explanations + question solving |
| 5–6 | ✅ Exam Mode + progress tracker + weak area detection |
| 7–8 | 🔜 Study plan generator + export + final polish + deploy |

### Planned improvements
- [ ] OCR support for scanned PDFs (Tesseract)
- [ ] Diagram/image extraction from slides
- [ ] Equation rendering for Math subjects
- [ ] Export study guide as PDF
- [ ] Multi-user support with login

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | Google Gemini 1.5 Flash (free tier) |
| Agent | LangChain |
| Embeddings | Google `embedding-001` |
| Vector DB | FAISS (local) |
| Document parsing | PyPDF2, pdfplumber, python-docx, python-pptx |
| Progress DB | SQLite |
| Deployment | Streamlit Cloud |

---

## 👥 Team

Built for the Agentic AI Program — Track A (Exam Preparation Assistant)

---

## 📄 License
MIT
