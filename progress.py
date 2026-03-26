"""Progress tab — topic mastery dashboard"""
import streamlit as st
from src.progress_tracker import (
    get_topic_scores, get_weak_topics,
    get_interaction_counts, get_recent_interactions, get_quiz_stats,
)

INTENT_ICON = {
    "topic_explain":  "📖",
    "question_solve": "📝",
    "quiz":           "🎯",
    "study_plan":     "📅",
    "weak_area":      "🔍",
    "general":        "💬",
}


def score_color(score: float) -> str:
    if score >= 70: return "#48bb78"
    if score >= 40: return "#ed8936"
    return "#fc8181"


def render_progress():
    subject = st.session_state.current_subject

    st.markdown(f"### 📊 Learning Progress — {subject}")

    # ── Top metrics ──────────────────────────────────────────────────────────
    counts    = get_interaction_counts(subject)
    quiz_stats = get_quiz_stats(subject)
    total_int = sum(counts.values())
    topics    = get_topic_scores(subject)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Topics Studied",    len(topics))
    col2.metric("Total Interactions", total_int)
    col3.metric("Questions Solved",  counts.get("question_solve", 0))
    col4.metric("Quiz Accuracy",     f"{quiz_stats['pct']}%" if quiz_stats["attempted"] else "—")

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        # ── Topic mastery bars ───────────────────────────────────────────────
        st.markdown("#### 🎯 Topic Mastery")

        if not topics:
            st.info("Start chatting about topics to track your progress!")
        else:
            for t in topics[:15]:
                score = min(t["score"], 100)
                color = score_color(score)
                label = t["topic"][:40]
                st.markdown(
                    f"""<div style='margin-bottom:10px;'>
  <div style='display:flex; justify-content:space-between; font-size:0.87rem;'>
    <span style='color:#2d3748; font-weight:500;'>{label}</span>
    <span style='color:{color}; font-weight:700;'>{score:.0f}%</span>
  </div>
  <div class='prog-bar-outer'>
    <div class='prog-bar-inner' style='width:{score}%; background:{color};'></div>
  </div>
  <div style='font-size:0.74rem; color:#a0aec0;'>
    {t['interactions']} interactions · last seen {(t['last_seen'] or '')[:10]}
  </div>
</div>""",
                    unsafe_allow_html=True,
                )

        # ── Interaction breakdown ───────────────────────────────────────────
        if counts:
            st.markdown("#### 📈 Session Breakdown")
            for intent, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                icon = INTENT_ICON.get(intent, "💬")
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:6px 0;border-bottom:1px solid #f0f0f0;font-size:0.88rem;'>"
                    f"<span>{icon} {intent.replace('_',' ').title()}</span>"
                    f"<span style='font-weight:700;color:#667eea;'>{cnt}</span></div>",
                    unsafe_allow_html=True,
                )

    with col_right:
        # ── Weak areas ──────────────────────────────────────────────────────
        st.markdown("#### ⚠️ Needs Attention")
        weak = get_weak_topics(subject)

        if not weak:
            st.markdown("""
<div style='text-align:center; padding:1.5rem; color:#48bb78; 
     border:1px solid #c6f6d5; border-radius:10px; background:#f0fff4;'>
    <div style='font-size:1.8rem'>🌟</div>
    <div style='font-weight:600; margin-top:0.4rem;'>All topics looking strong!</div>
</div>
""", unsafe_allow_html=True)
        else:
            for t in weak:
                score = t["score"]
                color = score_color(score)
                st.markdown(
                    f"""<div class='ep-card ep-card-red' style='padding:0.7rem 1rem;'>
  <div style='font-weight:600;font-size:0.9rem;'>{t['topic']}</div>
  <div style='font-size:0.78rem;margin-top:3px;'>
    Score: <span style='color:{color};font-weight:700;'>{score:.0f}/100</span>
  </div>
</div>""",
                    unsafe_allow_html=True,
                )
            if st.button("📚 Get study recommendations", use_container_width=True):
                weak_names = ", ".join(t["topic"] for t in weak)
                st.session_state.chat_history.append(
                    {"role": "user", "content": f"I'm struggling with: {weak_names}. Give me a focused study plan."}
                )
                st.switch_page("app.py") if hasattr(st, "switch_page") else None

        st.markdown("---")

        # ── Recent activity ─────────────────────────────────────────────────
        st.markdown("#### 🕐 Recent Activity")
        recent = get_recent_interactions(subject, limit=8)
        if not recent:
            st.caption("No activity yet.")
        else:
            for r in recent:
                icon  = INTENT_ICON.get(r["intent"], "💬")
                ts    = (r["timestamp"] or "")[:16].replace("T", " ")
                query = r["query"][:55] + ("…" if len(r["query"]) > 55 else "")
                st.markdown(
                    f"<div style='font-size:0.8rem;padding:5px 0;"
                    f"border-bottom:1px solid #f0f0f0;'>"
                    f"{icon} <span style='color:#2d3748;'>{query}</span><br>"
                    f"<span style='color:#a0aec0;font-size:0.73rem;'>{ts}</span></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── Export study guide ───────────────────────────────────────────────────
    st.markdown("#### 📤 Export")
    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("📋 Export progress report", use_container_width=True):
            lines = [f"# ExamPrep AI — Progress Report\n**Subject:** {subject}\n"]
            lines.append(f"**Topics studied:** {len(topics)}")
            lines.append(f"**Total interactions:** {total_int}")
            if topics:
                lines.append("\n## Topic Scores")
                for t in topics:
                    lines.append(f"- {t['topic']}: {t['score']:.0f}/100")
            if weak:
                lines.append("\n## Weak Areas")
                for t in weak:
                    lines.append(f"- {t['topic']}: {t['score']:.0f}/100")
            report = "\n".join(lines)
            st.download_button(
                "⬇️ Download report.md",
                report.encode(),
                file_name=f"{subject}_progress.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with col_b:
        if st.button("🗑️ Reset progress for this subject", use_container_width=True):
            st.warning("This will clear all progress data for this subject. Are you sure?")
