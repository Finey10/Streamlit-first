"""
LangChain agent powered by Gemini
Handles: topic explanations, question solving, study plans, quiz generation
"""
import os
import re
from typing import List, Dict, Optional, Tuple

# ── Prompt templates ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are ExamPrep AI, an expert academic tutor specialising in helping students 
understand subjects deeply and excel in exams. You have access to the student's uploaded study 
materials (lecture notes, textbooks, lab manuals, and previous year question papers).

Your personality:
- Clear, encouraging, and thorough
- Use examples and analogies liberally
- Structure answers with headers when explaining concepts
- For exam questions, give step-by-step solutions
- Always mention which source material you're drawing from

When answering:
1. Draw primarily from the retrieved context (student's own materials)
2. Supplement with your knowledge when context is insufficient
3. For 2-mark questions: give concise definitions + one example
4. For 5-mark questions: definition + explanation + example + diagram description
5. For 10-mark questions: comprehensive coverage with all sub-topics
6. Always end topic explanations with "Likely exam angle:" hinting at how this is typically tested
"""

TOPIC_EXPLAIN_PROMPT = """Using the student's study materials below, explain the topic: **{topic}**

RETRIEVED CONTEXT:
{context}

Subject: {subject}

Provide:
1. **Clear definition** (2-3 sentences)
2. **Core concepts** with bullet points
3. **Worked example** 
4. **Common exam questions** on this topic
5. **Likely exam angle:** how this is typically tested

Format your answer with markdown headers. Be thorough but exam-focused."""


QUESTION_SOLVE_PROMPT = """The student is asking about this exam question: **{question}**

RETRIEVED CONTEXT (from their study materials):
{context}

Subject: {subject}

Provide:
1. **Question type & marks** (estimate if not stated)
2. **Step-by-step solution**
3. **Key concepts tested**
4. **Model answer** (concise version suitable for exam)
5. **Common mistakes** students make on this question

Use the student's own study material as the primary source."""


QUIZ_PROMPT = """Generate a {num_questions}-question quiz on: **{topic}**

CONTEXT FROM STUDY MATERIALS:
{context}

Subject: {subject}

Format EXACTLY as:
Q1. [Question text]
a) [Option]  b) [Option]  c) [Option]  d) [Option]
Answer: [letter] — [brief explanation]

---
(repeat for each question)

Mix difficulty: 40% easy, 40% medium, 20% hard."""


STUDY_PLAN_PROMPT = """Create a personalised study plan for the student.

Subject: {subject}
Weak topics identified: {weak_topics}
Available study materials: {doc_list}
Days until exam: {days}

Create a day-by-day study plan that:
1. Prioritises weak areas
2. Includes revision cycles
3. Allocates time for practice questions
4. Suggests which document to study each day

Format as a clear table or day-wise breakdown."""


WEAK_AREA_PROMPT = """Analyse the student's learning session and identify weak areas.

Questions attempted: {questions}
Topics covered: {topics}
Errors or confusion noted: {errors}

Provide:
1. **Topics needing more attention** (ranked)
2. **Specific gaps** identified
3. **Recommended next steps**
4. **Suggested practice questions** for each weak area"""


GENERAL_PROMPT = """Student query: {query}

RETRIEVED CONTEXT (from their study materials):
{context}

Subject: {subject}

Answer the query thoroughly, drawing from the student's materials. 
If the context doesn't cover the topic well, say so and answer from general knowledge."""


# ── Intent classifier ────────────────────────────────────────────────────────
def classify_intent(query: str) -> str:
    q = query.lower()

    question_triggers = [
        "solve", "answer", "explain q", "q1", "q2", "q3", "q4", "q5",
        "question no", "question number", "from 20", "paper", "marks question",
        "how to solve", "solution for",
    ]
    quiz_triggers = ["quiz", "test me", "generate questions", "practice questions", "mcq"]
    plan_triggers = ["study plan", "schedule", "timetable", "how many days", "plan for exam"]
    weak_triggers = ["weak", "struggling", "don't understand", "confused about", "difficult"]
    explain_triggers = [
        "explain", "what is", "define", "describe", "elaborate",
        "tell me about", "how does", "concept of",
    ]

    if any(t in q for t in quiz_triggers):   return "quiz"
    if any(t in q for t in plan_triggers):   return "study_plan"
    if any(t in q for t in weak_triggers):   return "weak_area"
    if any(t in q for t in question_triggers): return "question_solve"
    if any(t in q for t in explain_triggers): return "topic_explain"
    return "general"


# ── Retrieval ─────────────────────────────────────────────────────────────────
def retrieve_context(
    query: str,
    vector_store,
    k: int = 6,
    filter_subject: Optional[str] = None,
    content_type_filter: Optional[str] = None,
) -> Tuple[str, List[Dict]]:
    """Retrieve relevant chunks from the vector store."""
    if vector_store is None:
        return "", []

    try:
        search_filter = {}
        if filter_subject and filter_subject != "General":
            search_filter["subject"] = filter_subject
        if content_type_filter:
            search_filter["content_type"] = content_type_filter

        docs = vector_store.similarity_search(
            query, k=k,
            filter=search_filter if search_filter else None,
        )

        if not docs:  # retry without filter
            docs = vector_store.similarity_search(query, k=k)

        context_parts = []
        sources       = []
        seen_sources  = set()

        for doc in docs:
            meta    = doc.metadata
            src     = meta.get("source", "unknown")
            ctype   = meta.get("content_type", "notes")
            label   = {"question_paper": "📝", "lab_manual": "🔬",
                       "textbook": "📖", "lecture_notes": "📋"}.get(ctype, "📄")

            header  = f"[{label} {src}]"
            context_parts.append(f"{header}\n{doc.page_content}")

            if src not in seen_sources:
                sources.append({"source": src, "content_type": ctype})
                seen_sources.add(src)

        return "\n\n---\n\n".join(context_parts), sources

    except Exception as e:
        return f"[Retrieval error: {e}]", []


# ── LLM call ─────────────────────────────────────────────────────────────────
def call_gemini(prompt: str, api_key: str, temperature: float = 0.3) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model    = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            SYSTEM_PROMPT + "\n\n" + prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048,
            ),
        )
        return response.text
    except Exception as e:
        return f"❌ Gemini error: {e}\n\nPlease check your API key and try again."


# ── Main agent function ───────────────────────────────────────────────────────
def run_agent(
    query: str,
    subject: str,
    vector_store,
    api_key: str,
    chat_history: List[Dict] = None,
    extra_params: Dict = None,
) -> Tuple[str, List[Dict], str]:
    """
    Main entry point.
    Returns: (answer, sources, intent)
    """
    if not api_key:
        return (
            "⚠️ Please enter your **Gemini API key** in the sidebar to get started.",
            [],
            "error",
        )

    extra_params = extra_params or {}
    intent       = classify_intent(query)

    # ── Retrieve context ──────────────────────────────────────────────────
    # For question papers, bias retrieval toward question_paper chunks
    ctype_filter = "question_paper" if intent == "question_solve" else None
    context, sources = retrieve_context(
        query, vector_store, k=6,
        filter_subject=subject,
        content_type_filter=ctype_filter,
    )

    if not context:
        context = "No uploaded study materials found for this subject yet."

    # ── Build prompt by intent ────────────────────────────────────────────
    if intent == "topic_explain":
        prompt = TOPIC_EXPLAIN_PROMPT.format(
            topic=query, context=context, subject=subject
        )

    elif intent == "question_solve":
        prompt = QUESTION_SOLVE_PROMPT.format(
            question=query, context=context, subject=subject
        )

    elif intent == "quiz":
        num = extra_params.get("num_questions", 5)
        topic = extra_params.get("topic", query)
        prompt = QUIZ_PROMPT.format(
            num_questions=num, topic=topic, context=context, subject=subject
        )

    elif intent == "study_plan":
        weak   = extra_params.get("weak_topics", "Not yet identified")
        docs   = extra_params.get("doc_list", "Uploaded materials")
        days   = extra_params.get("days", 7)
        prompt = STUDY_PLAN_PROMPT.format(
            subject=subject, weak_topics=weak,
            doc_list=docs, days=days,
        )

    elif intent == "weak_area":
        prompt = WEAK_AREA_PROMPT.format(
            questions=extra_params.get("questions", query),
            topics=extra_params.get("topics", subject),
            errors=extra_params.get("errors", "General confusion"),
        )

    else:
        prompt = GENERAL_PROMPT.format(
            query=query, context=context, subject=subject
        )

    # Add chat history for continuity
    if chat_history and len(chat_history) > 1:
        history_text = "\n".join(
            f"{'Student' if m['role']=='user' else 'Tutor'}: {m['content'][:200]}"
            for m in chat_history[-4:]  # last 2 exchanges
        )
        prompt = f"Previous conversation:\n{history_text}\n\n---\n\n{prompt}"

    answer = call_gemini(prompt, api_key)
    return answer, sources, intent


# ── Utility: extract topics from answer ──────────────────────────────────────
def extract_topics_from_answer(answer: str) -> List[str]:
    """Pull topic names from headers in a markdown answer."""
    headers = re.findall(r"#+\s+(.+)", answer)
    return [h.strip("* ").strip() for h in headers[:5]]
