"""Chat tab — study assistant conversation interface"""
import streamlit as st
from src.agent import run_agent, extract_topics_from_answer
from src.progress_tracker import update_topic_score, log_interaction


INTENT_LABELS = {
    "topic_explain":   ("📖", "Topic explanation"),
    "question_solve":  ("📝", "Exam question solved"),
    "quiz":            ("🎯", "Quiz generated"),
    "study_plan":      ("📅", "Study plan"),
    "weak_area":       ("🔍", "Weak area analysis"),
    "general":         ("💬", "General answer"),
    "error":           ("⚠️", ""),
}


def render_chat():
    subject     = st.session_state.current_subject
    api_key     = st.session_state.gemini_api_key
    vector_store = st.session_state.vector_store

    # ── Chat history display ───────────────────────────────────────────────
    chat_container = st.container()

    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
<div style='text-align:center; padding: 3rem 1rem; color: #718096;'>
    <div style='font-size:3.5rem; margin-bottom:1rem;'>🎓</div>
    <div style='font-size:1.1rem; font-weight:600; color:#4a5568;'>Welcome to ExamPrep AI</div>
    <div style='font-size:0.9rem; margin-top:0.5rem;'>
        Upload your study materials, then ask anything:<br>
        <em>"Explain Database Normalization with examples"</em><br>
        <em>"Solve Q3 from 2022 DBMS paper"</em><br>
        <em>"Create a 5-question quiz on OS scheduling"</em>
    </div>
</div>
""", unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-user">👤 {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    # Bot message
                    icon, label = INTENT_LABELS.get(msg.get("intent", "general"), ("💬", ""))
                    badge = f'<span class="badge badge-blue">{icon} {label}</span>' if label else ""

                    st.markdown(
                        f'<div class="chat-bot">{badge}',
                        unsafe_allow_html=True,
                    )
                    st.markdown(msg["content"])

                    # Source pills
                    if msg.get("sources"):
                        pills = "".join(
                            f'<span class="source-pill">📄 {s["source"]}</span>'
                            for s in msg["sources"]
                        )
                        st.markdown(
                            f'<div style="margin-top:6px">{pills}</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Input row ──────────────────────────────────────────────────────────
    col_input, col_btn = st.columns([5, 1])

    # Handle quick prompts from sidebar
    default_val = ""
    if hasattr(st.session_state, "_quick_prompt"):
        default_val = st.session_state._quick_prompt
        del st.session_state._quick_prompt

    with col_input:
        user_input = st.text_area(
            "Ask anything about your subject...",
            value=default_val,
            height=80,
            key="chat_input",
            label_visibility="collapsed",
            placeholder=f"Ask about {subject} — topics, exam questions, quizzes, study plans...",
        )

    with col_btn:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        send = st.button("Send 🚀", use_container_width=True, type="primary")

    # ── Contextual options ─────────────────────────────────────────────────
    with st.expander("⚙️ Advanced options", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            num_q = st.slider("Quiz questions", 3, 15, 5)
        with col_b:
            days  = st.number_input("Days to exam", min_value=1, max_value=90, value=7)

    # ── Send handler ───────────────────────────────────────────────────────
    if send and user_input.strip():
        query = user_input.strip()

        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": query})

        with st.spinner("🤔 Thinking..."):
            answer, sources, intent = run_agent(
                query=query,
                subject=subject,
                vector_store=vector_store,
                api_key=api_key,
                chat_history=st.session_state.chat_history,
                extra_params={"num_questions": num_q, "days": days},
            )

        # Track progress
        topics = extract_topics_from_answer(answer)
        for topic in topics:
            update_topic_score(subject, topic, intent)

        if intent in ("question_solve", "quiz"):
            st.session_state.total_questions_solved += 1

        log_interaction(subject, query, intent)

        # Add bot message
        st.session_state.chat_history.append({
            "role":    "assistant",
            "content": answer,
            "sources": sources,
            "intent":  intent,
        })

        st.rerun()
