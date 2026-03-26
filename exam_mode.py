"""Exam Mode tab — timed quiz generation and scoring"""
import re
import streamlit as st
from src.agent import run_agent
from src.progress_tracker import log_quiz_result


def parse_quiz(raw: str):
    """Parse LLM-generated quiz into structured format."""
    questions = []
    blocks = re.split(r"\n(?=Q\d+\.)", raw.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Question text
        q_match = re.match(r"Q\d+\.\s*(.+?)(?=\n[a-d]\))", block, re.DOTALL)
        if not q_match:
            continue
        q_text = q_match.group(1).strip()

        # Options
        opts = re.findall(r"([a-d])\)\s*(.+?)(?=\n[a-d]\)|\nAnswer:|$)", block, re.DOTALL)
        options = {o[0]: o[1].strip() for o in opts}

        if len(options) < 2:
            continue

        # Answer
        ans_match = re.search(r"Answer:\s*([a-d])", block, re.IGNORECASE)
        answer = ans_match.group(1).lower() if ans_match else list(options.keys())[0]

        # Explanation
        exp_match = re.search(r"Answer:\s*[a-d]\s*[—–-]\s*(.+)$", block, re.DOTALL)
        explanation = exp_match.group(1).strip() if exp_match else ""

        questions.append({
            "question":    q_text,
            "options":     options,
            "answer":      answer,
            "explanation": explanation,
        })

    return questions


def render_exam_mode():
    subject     = st.session_state.current_subject
    api_key     = st.session_state.gemini_api_key
    vector_store = st.session_state.vector_store

    st.markdown("### 📝 Exam Mode")
    st.markdown("Generate a timed quiz from your uploaded materials and test your knowledge.")

    # ── Init exam state ──────────────────────────────────────────────────────
    if "exam_state" not in st.session_state:
        st.session_state.exam_state = "setup"  # setup | active | results

    # ══════════════════════════════════════════════════════════════════════════
    # SETUP SCREEN
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.exam_state == "setup":
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("#### Configure your quiz")
            topic    = st.text_input("Topic / chapter", placeholder="e.g. Database Normalization, OS Scheduling")
            num_q    = st.slider("Number of questions", 3, 15, 5)
            col1, col2 = st.columns(2)
            with col1:
                difficulty = st.selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard"])
            with col2:
                timer_min = st.number_input("Time limit (min)", min_value=1, max_value=60, value=10)

        with col_r:
            st.markdown("#### About Exam Mode")
            st.markdown("""
<div class='ep-card ep-card-purple' style='margin-top:0;'>
    <b>📋 How it works</b><br><br>
    1. Enter a topic from your uploaded materials<br>
    2. AI generates an MCQ quiz based on <em>your own notes</em><br>
    3. Answer all questions within the time limit<br>
    4. Get detailed feedback + explanations<br>
    5. Weak areas are automatically flagged for revision
</div>
""", unsafe_allow_html=True)

        if not api_key:
            st.warning("⚠️ Add your Gemini API key to start.")
        elif not vector_store and not topic:
            st.info("💡 Upload materials first for topic-specific questions, or enter any topic for general questions.")

        start = st.button("🚀 Start Quiz", type="primary", use_container_width=False)

        if start and topic.strip():
            query = f"Generate {num_q} {difficulty.lower()} MCQ questions about {topic}"
            with st.spinner("Generating your quiz..."):
                raw_quiz, _, _ = run_agent(
                    query=query,
                    subject=subject,
                    vector_store=vector_store,
                    api_key=api_key,
                    extra_params={"num_questions": num_q, "topic": topic},
                )

            questions = parse_quiz(raw_quiz)

            if len(questions) < 2:
                st.error("❌ Couldn't parse quiz questions. Try a different topic or rephrase.")
                st.markdown("**Raw output:**")
                st.text(raw_quiz[:800])
            else:
                st.session_state.exam_questions  = questions
                st.session_state.exam_answers    = {}
                st.session_state.exam_topic      = topic
                st.session_state.exam_timer_sec  = timer_min * 60
                st.session_state.exam_start_time = __import__("time").time()
                st.session_state.exam_state      = "active"
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIVE EXAM
    # ══════════════════════════════════════════════════════════════════════════
    elif st.session_state.exam_state == "active":
        import time
        questions = st.session_state.exam_questions
        topic     = st.session_state.exam_topic
        elapsed   = time.time() - st.session_state.exam_start_time
        remaining = max(0, st.session_state.exam_timer_sec - elapsed)
        mins, secs = divmod(int(remaining), 60)

        # Timer display
        timer_color = "#fc8181" if remaining < 60 else "#48bb78" if remaining > 120 else "#ed8936"
        st.markdown(
            f"<div style='display:flex; justify-content:space-between; "
            f"align-items:center; margin-bottom:1rem;'>"
            f"<span style='font-size:1.1rem; font-weight:700;'>📝 {topic}</span>"
            f"<span style='font-size:1.3rem; font-weight:700; color:{timer_color};'>"
            f"⏱️ {mins:02d}:{secs:02d}</span></div>",
            unsafe_allow_html=True,
        )

        if remaining == 0:
            st.session_state.exam_state = "results"
            st.rerun()

        progress = len(st.session_state.exam_answers) / len(questions)
        st.progress(progress, text=f"{len(st.session_state.exam_answers)}/{len(questions)} answered")

        # Questions
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            opts = q["options"]
            choice = st.radio(
                f"q{i+1}",
                options=list(opts.keys()),
                format_func=lambda k, o=opts: f"{k}) {o[k]}",
                key=f"exam_q{i}",
                label_visibility="collapsed",
                horizontal=True,
            )
            st.session_state.exam_answers[i] = choice
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        col_submit, col_cancel = st.columns([2, 1])
        with col_submit:
            if st.button("✅ Submit Quiz", type="primary", use_container_width=True):
                st.session_state.exam_state = "results"
                st.rerun()
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.exam_state = "setup"
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # RESULTS
    # ══════════════════════════════════════════════════════════════════════════
    elif st.session_state.exam_state == "results":
        questions = st.session_state.exam_questions
        answers   = st.session_state.exam_answers
        topic     = st.session_state.exam_topic
        subject   = st.session_state.current_subject

        correct = sum(
            1 for i, q in enumerate(questions)
            if answers.get(i) == q["answer"]
        )
        total   = len(questions)
        pct     = correct / total * 100

        # Score banner
        if pct >= 80:
            color, emoji, msg = "#48bb78", "🌟", "Excellent!"
        elif pct >= 60:
            color, emoji, msg = "#ed8936", "👍", "Good effort!"
        else:
            color, emoji, msg = "#fc8181", "📚", "Needs more practice"

        st.markdown(
            f"<div style='background:{color}22; border:2px solid {color}; "
            f"border-radius:12px; padding:1.5rem; text-align:center; margin-bottom:1.5rem;'>"
            f"<div style='font-size:2.5rem;'>{emoji}</div>"
            f"<div style='font-size:1.8rem; font-weight:700; color:{color};'>"
            f"{correct}/{total} &nbsp;({pct:.0f}%)</div>"
            f"<div style='font-size:1rem; color:#4a5568; margin-top:0.3rem;'>{msg}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        log_quiz_result(subject, topic, correct, total)

        # Detailed review
        st.markdown("#### 📋 Answer Review")
        for i, q in enumerate(questions):
            user_ans    = answers.get(i, "—")
            correct_ans = q["answer"]
            is_correct  = user_ans == correct_ans
            icon        = "✅" if is_correct else "❌"
            bg          = "#f0fff4" if is_correct else "#fff5f5"
            border      = "#c6f6d5" if is_correct else "#fed7d7"

            opts = q["options"]
            st.markdown(
                f"<div style='background:{bg}; border:1px solid {border}; "
                f"border-radius:8px; padding:0.9rem; margin-bottom:0.7rem;'>"
                f"<b>{icon} Q{i+1}. {q['question']}</b><br>"
                f"<span style='font-size:0.88rem;'>Your answer: "
                f"<b>{user_ans}) {opts.get(user_ans,'—')}</b></span><br>"
                + (f"<span style='font-size:0.88rem; color:#e53e3e;'>Correct: "
                   f"<b>{correct_ans}) {opts.get(correct_ans,'')}</b></span><br>"
                   if not is_correct else "")
                + (f"<span style='font-size:0.82rem; color:#718096; margin-top:4px; display:block;'>"
                   f"💡 {q['explanation']}</span>" if q["explanation"] else "")
                + "</div>",
                unsafe_allow_html=True,
            )

        col_retry, col_chat, col_new = st.columns(3)
        with col_retry:
            if st.button("🔄 Retry same topic", use_container_width=True):
                st.session_state.exam_state = "setup"
                st.rerun()
        with col_chat:
            if st.button("💬 Discuss weak areas", use_container_width=True):
                wrong_topics = [
                    q["question"][:60]
                    for i, q in enumerate(questions)
                    if answers.get(i) != q["answer"]
                ]
                if wrong_topics:
                    q_text = "I got these wrong in my quiz:\n" + "\n".join(f"- {t}" for t in wrong_topics)
                    q_text += "\nPlease explain these concepts."
                    st.session_state.chat_history.append({"role": "user", "content": q_text})
                st.session_state.exam_state = "setup"
                st.rerun()
        with col_new:
            if st.button("📝 New quiz", use_container_width=True, type="primary"):
                st.session_state.exam_state = "setup"
                st.rerun()
