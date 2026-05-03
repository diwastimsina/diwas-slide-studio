import streamlit as st
import time
import json
from document_processor import extract_text, chunk_text
from chat_engine import analyze_document, modify_presentation, answer_question, detect_intent
from presentation_builder import build_presentation
from preview_renderer import render_all_thumbnails
from pdf_exporter import build_pdf

st.set_page_config(
    page_title="Diwas Slide Studio",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0A0F1E; color: #E8EAF0; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1428 0%, #0A0F1E 100%);
    border-right: 1px solid #1E2D45;
}
header[data-testid="stHeader"] { background: transparent; }
.app-header {
    background: linear-gradient(135deg, #0D1B2A 0%, #0A0F1E 100%);
    border-bottom: 1px solid #1E2D45;
    padding: 0.8rem 1.5rem; margin: -1rem -1rem 1rem -1rem;
}
.app-title {
    font-size: 1.4rem; font-weight: 800;
    background: linear-gradient(135deg, #1E90FF, #00D4AA);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.app-subtitle { font-size: 0.8rem; color: #6B7A99; }
.msg-user {
    background: linear-gradient(135deg, #1E3A5F, #1A3050);
    border: 1px solid #2A5080; border-radius: 18px 18px 4px 18px;
    padding: 0.65rem 1rem; margin-left: 10%;
    color: #E8EAF0; font-size: 0.92rem; margin-bottom: 0.5rem;
}
.msg-assistant {
    background: linear-gradient(135deg, #0F1E35, #0D1B2A);
    border: 1px solid #1E2D45; border-radius: 18px 18px 18px 4px;
    padding: 0.65rem 1rem; margin-right: 10%;
    color: #E8EAF0; font-size: 0.92rem; margin-bottom: 0.5rem;
}
.msg-role { font-size: 0.72rem; font-weight: 600; margin-bottom: 0.3rem; }
.msg-user .msg-role { color: #1E90FF; text-align: right; }
.msg-assistant .msg-role { color: #00D4AA; }
.msg-system {
    background: rgba(0,212,170,0.07); border: 1px solid rgba(0,212,170,0.2);
    border-radius: 10px; padding: 0.4rem 0.8rem;
    color: #00D4AA; font-size: 0.82rem; text-align: center; margin-bottom: 0.4rem;
}
.msg-error {
    background: rgba(255,80,80,0.07); border: 1px solid rgba(255,80,80,0.25);
    border-radius: 10px; padding: 0.4rem 0.8rem;
    color: #FF6B6B; font-size: 0.82rem; margin-bottom: 0.4rem;
}
.preview-header {
    font-size: 0.78rem; font-weight: 600; color: #6B7A99;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;
}
.slide-count-badge {
    background: linear-gradient(135deg, #1E90FF22, #00D4AA22);
    border: 1px solid #1E90FF44; border-radius: 20px;
    padding: 0.2rem 0.7rem; font-size: 0.78rem; color: #1E90FF;
    display: inline-block; margin-bottom: 0.6rem;
}
.slide-label {
    font-size: 0.68rem; color: #6B7A99; text-align: center; margin-top: 0.1rem;
}
.stButton > button {
    background: linear-gradient(135deg, #1E90FF, #0070DD) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.status-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; margin-right: 6px; vertical-align: middle;
}
.status-online { background: #00D4AA; box-shadow: 0 0 6px #00D4AA; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
for key, default in [
    ("messages", []),
    ("analysis", None),
    ("doc_text", ""),
    ("thumbnails", []),
    ("pptx_bytes", None),
    ("pdf_bytes", None),
    ("doc_name", ""),
    ("processing", False),
    ("pending_message", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Diwas Slide Studio")
    st.markdown("---")

    st.markdown("### 🔑 Free API Keys *(optional)*")
    st.markdown('<span style="font-size:0.78rem;color:#6B7A99">Leave blank to use local Ollama</span>',
                unsafe_allow_html=True)

    groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", key="groq_key")
    gemini_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...", key="gemini_key")

    if groq_key:
        st.markdown('<span class="status-dot status-online"></span>'
                    '<span style="font-size:0.8rem;color:#00D4AA">Groq active (fastest)</span>',
                    unsafe_allow_html=True)
    elif gemini_key:
        st.markdown('<span class="status-dot status-online"></span>'
                    '<span style="font-size:0.8rem;color:#00D4AA">Gemini active</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-dot status-online"></span>'
                    '<span style="font-size:0.8rem;color:#B0C4DE">Ollama (local)</span>',
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ Settings")

    ollama_model = st.selectbox("Ollama Model",
        ["deepseek-r1:latest", "deepseek-r1:1.5b", "llama3.2", "mistral", "gemma2"], index=0)
    default_theme = st.selectbox("Default Theme",
        ["professional", "modern", "minimal", "bold"], index=0)

    st.markdown("---")
    st.markdown("### 📁 Upload Document")
    uploaded_file = st.file_uploader("PDF or Word file",
        type=["pdf", "docx", "doc", "txt"], label_visibility="collapsed")

    if uploaded_file:
        st.markdown(f'<div style="font-size:0.8rem;color:#00D4AA">📄 {uploaded_file.name}</div>',
                    unsafe_allow_html=True)
        if st.button("🚀 Generate Slides", use_container_width=True):
            st.session_state.processing = True

    st.markdown("---")
    if st.session_state.analysis:
        if st.button("🗑️ Start Over", use_container_width=True):
            for k in ["analysis", "pptx_bytes", "pdf_bytes"]:
                st.session_state[k] = None
            for k in ["doc_text", "doc_name"]:
                st.session_state[k] = ""
            st.session_state.messages = []
            st.session_state.thumbnails = []
            st.rerun()

    st.markdown("---")
    st.markdown("""
<div style="font-size:0.75rem;color:#3D4F6B;line-height:1.8">
<strong style="color:#6B7A99">Get free API keys:</strong><br>
🟣 <a href="https://console.groq.com" target="_blank" style="color:#7AB3F0">console.groq.com</a> — fastest<br>
🔵 <a href="https://aistudio.google.com" target="_blank" style="color:#7AB3F0">aistudio.google.com</a> — Gemini<br>
🟡 Ollama already installed ✓
</div>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────
def get_keys():
    return {"groq": st.session_state.get("groq_key", ""),
            "gemini": st.session_state.get("gemini_key", "")}

def add_msg(role, content, kind="text"):
    st.session_state.messages.append({"role": role, "content": content, "kind": kind})

def rebuild_all():
    if st.session_state.analysis:
        st.session_state.pptx_bytes = build_presentation(st.session_state.analysis)
        st.session_state.pdf_bytes = build_pdf(st.session_state.analysis)
        st.session_state.thumbnails = render_all_thumbnails(st.session_state.analysis)


# ── Process document upload ────────────────────────────────────────────────
if st.session_state.processing and uploaded_file:
    st.session_state.processing = False
    try:
        add_msg("system", f"📄 Processing **{uploaded_file.name}**...", "system")
        raw_text = extract_text(uploaded_file.getvalue(), uploaded_file.name)
        if not raw_text.strip():
            add_msg("system", "❌ Could not extract text from this file.", "error")
        else:
            st.session_state.doc_text = raw_text
            st.session_state.doc_name = uploaded_file.name
            add_msg("system", f"🤖 Analyzing {len(raw_text):,} characters — building slides...", "system")
            analysis = analyze_document(chunk_text(raw_text), get_keys(), ollama_model)
            analysis["theme"] = default_theme
            st.session_state.analysis = analysis
            rebuild_all()
            n = len(analysis.get("slides", []))
            title = analysis.get("title", "Your Presentation")
            add_msg("assistant",
                f"✅ Done! Created **{n} slides** for **\"{title}\"**.\n\n"
                "Your preview is live on the right. Tell me what to change and I'll update instantly.\n\n"
                "**Try asking:** *\"Make the title more impactful\"*, *\"Add a market trends slide\"*, "
                "*\"Change theme to bold\"*, *\"Make bullets more concise\"*")
    except Exception as e:
        err = str(e)
        msg = "❌ Cannot reach Ollama — run `ollama serve` in Terminal." \
              if "connection" in err.lower() or "refused" in err.lower() else f"❌ {err}"
        add_msg("system", msg, "error")
    st.rerun()


# ── App header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">🎯 Diwas Slide Studio</div>
    <div class="app-subtitle">Chat to create and refine world-class presentations</div>
</div>
""", unsafe_allow_html=True)

chat_col, preview_col = st.columns([5, 6], gap="large")


# ── LEFT: Chat ─────────────────────────────────────────────────────────────
with chat_col:

    if not st.session_state.messages:
        st.markdown("""
<div style="text-align:center;padding:4rem 1rem;color:#3D4F6B">
    <div style="font-size:3.5rem;margin-bottom:1rem">🎯</div>
    <div style="font-size:1.05rem;font-weight:600;color:#5A6A8A;margin-bottom:0.5rem">
        Upload a document to get started
    </div>
    <div style="font-size:0.85rem;color:#3D4F6B;line-height:1.7">
        PDF or Word → AI builds your slides<br>Then chat to refine anything
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            role, content, kind = msg["role"], msg["content"], msg.get("kind", "text")
            if kind == "system":
                st.markdown(f'<div class="msg-system">{content}</div>', unsafe_allow_html=True)
            elif kind == "error":
                st.markdown(f'<div class="msg-error">{content}</div>', unsafe_allow_html=True)
            elif role == "user":
                st.markdown(f'<div class="msg-user"><div class="msg-role">You</div>{content}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-assistant"><div class="msg-role">✦ Studio AI</div>{content}</div>',
                            unsafe_allow_html=True)

    st.markdown("---")

    # Quick-edit chips
    if st.session_state.analysis:
        st.markdown('<span style="font-size:0.8rem;color:#6B7A99;font-weight:600">QUICK EDITS</span>',
                    unsafe_allow_html=True)
        chips = [
            "Change theme to modern", "Make bullets shorter",
            "Add a timeline slide", "Change theme to bold",
            "Add speaker notes", "Make title more impactful",
        ]
        c1, c2, c3 = st.columns(3)
        for i, chip in enumerate(chips):
            with [c1, c2, c3][i % 3]:
                if st.button(chip, key=f"chip_{i}", use_container_width=True):
                    st.session_state.pending_message = chip
                    st.rerun()

    # Chat input
    if st.session_state.analysis:
        user_input = st.chat_input("Ask me to change anything about the slides...")

        if st.session_state.pending_message:
            user_input = st.session_state.pending_message
            st.session_state.pending_message = None

        if user_input:
            add_msg("user", user_input)
            try:
                keys = get_keys()
                intent = detect_intent(user_input, keys, ollama_model)

                if intent == "modify":
                    add_msg("system", "🔄 Updating slides...", "system")
                    new_analysis = modify_presentation(
                        st.session_state.analysis, user_input,
                        st.session_state.doc_text, keys, ollama_model)
                    st.session_state.analysis = new_analysis
                    rebuild_all()
                    n = len(new_analysis.get("slides", []))
                    add_msg("assistant",
                        f"✅ Updated! Your deck now has **{n} slides**. What else would you like to change?")

                elif intent == "question":
                    answer = answer_question(
                        st.session_state.analysis, user_input,
                        st.session_state.doc_text, keys, ollama_model)
                    add_msg("assistant", answer)

                else:
                    add_msg("assistant",
                        "I'm here to help with your presentation! Tell me what to adjust — "
                        "add slides, change charts, switch themes, or anything else.")

            except Exception as e:
                add_msg("system", f"❌ {str(e)}", "error")
            st.rerun()
    else:
        st.markdown('<div style="color:#3D4F6B;font-size:0.82rem;text-align:center;padding:0.5rem">'
                    'Upload a document in the sidebar to start chatting</div>', unsafe_allow_html=True)


# ── RIGHT: Live preview ────────────────────────────────────────────────────
with preview_col:
    if st.session_state.analysis:
        analysis = st.session_state.analysis
        slides = analysis.get("slides", [])
        theme = analysis.get("theme", "professional")

        hc1, hc2, hc3 = st.columns([3, 2, 2])
        with hc1:
            st.markdown(f'<div class="slide-count-badge">📊 {len(slides)} slides · {theme}</div>',
                        unsafe_allow_html=True)
        base_name = (st.session_state.doc_name or "presentation").rsplit(".", 1)[0]
        with hc2:
            if st.session_state.pptx_bytes:
                st.download_button(
                    "⬇️ PPTX",
                    data=st.session_state.pptx_bytes,
                    file_name=f"{base_name}_slides.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                )
        with hc3:
            if st.session_state.pdf_bytes:
                st.download_button(
                    "⬇️ PDF",
                    data=st.session_state.pdf_bytes,
                    file_name=f"{base_name}_slides.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        st.markdown('<div class="preview-header">Live Slide Preview</div>', unsafe_allow_html=True)

        thumbs = st.session_state.thumbnails
        if thumbs:
            for row in range(0, len(slides), 2):
                row_slides = slides[row:row+2]
                row_thumbs = thumbs[row:row+2]
                cols = st.columns(len(row_thumbs), gap="small")
                for col, slide, thumb in zip(cols, row_slides, row_thumbs):
                    with col:
                        num = row + row_slides.index(slide) + 1
                        st.image(thumb, use_container_width=True)
                        st.markdown(
                            f'<div class="slide-label">#{num} · {slide.get("type","")}</div>',
                            unsafe_allow_html=True)
        else:
            with st.spinner("Rendering previews..."):
                rebuild_all()
                st.rerun()

    else:
        st.markdown("""
<div style="
    height:68vh; display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    border:2px dashed #1E2D45; border-radius:16px;
    text-align:center; padding:2rem;
">
    <div style="font-size:4rem;opacity:0.3;margin-bottom:1rem">🖼️</div>
    <div style="font-size:1rem;font-weight:600;color:#4A5A7A;margin-bottom:0.5rem">
        Live preview appears here
    </div>
    <div style="font-size:0.82rem;color:#2D3A55">
        Upload a document in the sidebar<br>to generate your slide deck
    </div>
</div>
""", unsafe_allow_html=True)
