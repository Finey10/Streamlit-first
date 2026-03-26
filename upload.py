"""Upload Materials tab"""
import streamlit as st
from src.document_processor import ingest_document, CONTENT_TYPE_LABELS


def render_upload():
    subject = st.session_state.current_subject
    api_key = st.session_state.gemini_api_key

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 📂 Upload Study Materials")
        st.markdown(
            "Upload your **lecture notes, textbooks, lab manuals, and previous year question papers**. "
            "The AI will automatically detect the content type and index everything for smart retrieval."
        )

        st.markdown("""
<div class='upload-zone'>
    <div style='font-size:2rem'>📄</div>
    <div style='font-weight:600; margin:0.4rem 0'>Drag & drop your files here</div>
    <div style='font-size:0.82rem; color:#4a5568'>PDF · DOCX · PPTX · TXT</div>
</div>
""", unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Choose files",
            type=["pdf", "docx", "pptx", "ppt", "doc", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if not api_key:
            st.warning("⚠️ Add your Gemini API key in the sidebar before uploading.")

        if uploaded and api_key:
            if st.button("📥 Process & Index Files", type="primary", use_container_width=True):
                progress_bar = st.progress(0, text="Starting...")
                results      = []

                for i, file in enumerate(uploaded):
                    progress_bar.progress(
                        (i + 1) / len(uploaded),
                        text=f"Processing {file.name}...",
                    )

                    # Check duplicates
                    existing_names = [d["filename"] for d in st.session_state.doc_metadata]
                    if file.name in existing_names:
                        results.append(("⚠️", f"{file.name} already uploaded — skipped."))
                        continue

                    result = ingest_document(
                        file,
                        subject,
                        api_key,
                        existing_store=st.session_state.vector_store,
                    )

                    if len(result) == 4:
                        success, msg, meta, store = result
                        if success:
                            st.session_state.vector_store  = store
                            st.session_state.uploaded_docs.append(file.name)
                            st.session_state.doc_metadata.append(meta)
                            results.append(("✅", msg))
                        else:
                            results.append(("❌", msg))
                    else:
                        success, msg, meta = result
                        results.append(("❌", msg))

                progress_bar.empty()

                for icon, msg in results:
                    if icon == "✅":
                        st.success(msg)
                    elif icon == "⚠️":
                        st.warning(msg)
                    else:
                        st.error(msg)

                if any(r[0] == "✅" for r in results):
                    st.balloons()
                    st.rerun()

    with col_right:
        st.markdown("### 📚 Indexed Materials")

        docs = st.session_state.doc_metadata
        if not docs:
            st.markdown("""
<div style='text-align:center; padding:2rem; color:#718096; 
     border:1px dashed #e2e8f0; border-radius:10px;'>
    <div style='font-size:2rem'>📭</div>
    <div>No materials uploaded yet</div>
</div>
""", unsafe_allow_html=True)
        else:
            # Group by content type
            by_type = {}
            for doc in docs:
                ct = doc.get("content_type", "lecture_notes")
                by_type.setdefault(ct, []).append(doc)

            for ctype, cdocs in by_type.items():
                label = CONTENT_TYPE_LABELS.get(ctype, ctype)
                st.markdown(f"**{label}**")
                for doc in cdocs:
                    chunks = doc.get("chunks", 0)
                    chars  = doc.get("chars", 0)
                    subj   = doc.get("subject", "General")
                    st.markdown(
                        f"""<div class='ep-card' style='padding:0.7rem 1rem; margin-bottom:0.5rem;'>
    <div style='font-weight:600; font-size:0.9rem;'>{doc['filename']}</div>
    <div style='font-size:0.78rem; color:#718096; margin-top:2px;'>
        📦 {chunks} chunks &nbsp;·&nbsp; 
        📝 {chars:,} chars &nbsp;·&nbsp; 
        <span class='badge badge-blue'>{subj}</span>
    </div>
</div>""",
                        unsafe_allow_html=True,
                    )
                st.markdown("")

        st.markdown("---")
        st.markdown("### 💡 Tips for best results")
        tips = [
            ("📝", "Upload previous year question papers for exact solution matching"),
            ("📖", "Add your textbook chapters for comprehensive theory"),
            ("📋", "Include lecture notes for your professor's specific approach"),
            ("🔬", "Lab manuals help with practical-type questions"),
            ("📁", "Upload materials per subject using the subject selector"),
        ]
        for icon, tip in tips:
            st.markdown(f"- {icon} {tip}")
