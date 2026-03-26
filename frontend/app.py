import streamlit as st
import os
from pathlib import Path

st.set_page_config(
    page_title="ExamPrep AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main background */
.main { background-color: #f8f9fb; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
}
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #a0aec0 !important; }

/* Cards */
.ep-card {
    background: white;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    margin-bottom: 1rem;
    border-left: 4px solid #667eea;
}
.ep-card-green  { border-left-color: #48bb78; }
.ep-card-orange { border-left-color: #ed8936; }
.ep-card-red    { border-left-color: #fc8181; }
.ep-card-purple { border-left-color: #9f7aea; }

/* Metric tiles */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.metric-tile {
    flex: 1;
    background: white;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.metric-tile .val { font-size: 2rem; font-weight: 700; color: #667eea; }
.metric-tile .lbl { font-size: 0.78rem; color: #718096; margin-top: 2px; }

/* Chat bubbles */
.chat-user {
    background: #667eea;
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0 0.5rem 3rem;
    font-size: 0.93rem;
}
.chat-bot {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 0.9rem 1.1rem;
    margin: 0.5rem 3rem 0.5rem 0;
    font-size: 0.93rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.source-pill {
    display: inline-block;
    background: #ebf4ff;
    color: #3182ce;
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 99px;
    margin: 3px 2px 0 0;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-left: 6px;
}
.badge-blue   { background: #ebf4ff; color: #3182ce; }
.badge-green  { background: #f0fff4; color: #276749; }
.badge-orange { background: #fffaf0; color: #c05621; }
.badge-red    { background: #fff5f5; color: #c53030; }

/* Upload zone */
.upload-zone {
    border: 2px dashed #c3dafe;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    background: #ebf8ff;
    margin-bottom: 1rem;
}

/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #2d3748;
    margin: 1.2rem 0 0.6rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.divider { border: none; border-top: 1px solid #e2e8f0; margin: 1rem 0; }

/* Tabs override */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    background: #edf2f7;
    color: #4a5568;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #667eea !important;
    border-bottom: 2px solid #667eea;
}

/* Progress bar */
.prog-bar-outer {
    background: #e2e8f0;
    border-radius: 99px;
    height: 8px;
    width: 100%;
    margin: 4px 0 10px;
}
.prog-bar-inner {
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 99px;
    height: 8px;
}

button[kind="primary"] { background: #667eea !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ───────────────────────────────────────────────────
defaults = {
    "chat_history": [],
    "current_subject": "General",
    "uploaded_docs": [],
    "vector_store": None,
    "subjects": ["General"],
    "topic_scores": {},
    "total_questions_solved": 0,
    "gemini_api_key": "",
    "doc_metadata": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 ExamPrep AI")
    st.markdown("*Your intelligent study companion*")
    st.markdown("---")

    # API Key
    api_key = st.text_input(
        "🔑 Gemini API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Get a free key at aistudio.google.com",
        placeholder="AIza...",
    )
    if api_key:
        st.session_state.gemini_api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key

    st.markdown("---")

    # Subject selector
    st.markdown("**📚 Active Subject**")
    subject = st.selectbox(
        "Subject",
        st.session_state.subjects,
        index=st.session_state.subjects.index(st.session_state.current_subject)
        if st.session_state.current_subject in st.session_state.subjects else 0,
        label_visibility="collapsed",
    )
    st.session_state.current_subject = subject

    new_subject = st.text_input("➕ Add subject", placeholder="e.g. DBMS, OS, CN")
    if st.button("Add", use_container_width=True) and new_subject.strip():
        if new_subject.strip() not in st.session_state.subjects:
            st.session_state.subjects.append(new_subject.strip())
            st.session_state.current_subject = new_subject.strip()
            st.rerun()

    st.markdown("---")

    # Stats
    n_docs = len(st.session_state.uploaded_docs)
    n_q    = st.session_state.total_questions_solved
    st.markdown(f"📄 **{n_docs}** document{'s' if n_docs != 1 else ''} loaded")
    st.markdown(f"✅ **{n_q}** questions solved")

    st.markdown("---")
    st.markdown("**Quick prompts**")
    quick = [
        "Explain this topic with examples",
        "What are likely exam questions?",
        "Create a 10-question quiz",
        "Summarise my weak areas",
        "Give me a study plan",
    ]
    for q in quick:
        if st.button(q, use_container_width=True, key=f"qp_{q}"):
            st.session_state._quick_prompt = q

    st.markdown("---")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ── Main layout ──────────────────────────────────────────────────────────────
st.markdown(f"# 🎓 ExamPrep AI &nbsp;<span class='badge badge-blue'>{st.session_state.current_subject}</span>", unsafe_allow_html=True)

tab_chat, tab_upload, tab_progress, tab_exam = st.tabs(
    ["💬 Study Chat", "📂 Upload Materials", "📊 My Progress", "📝 Exam Mode"]
)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — STUDY CHAT
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    from src.chat import render_chat
    render_chat()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — UPLOAD MATERIALS
# ─────────────────────────────────────────────────────────────────────────────
with tab_upload:
    from src.upload import render_upload
    render_upload()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PROGRESS
# ─────────────────────────────────────────────────────────────────────────────
with tab_progress:
    from src.progress import render_progress
    render_progress()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — EXAM MODE
# ─────────────────────────────────────────────────────────────────────────────
with tab_exam:
    from src.exam_mode import render_exam_mode
    render_exam_mode()
