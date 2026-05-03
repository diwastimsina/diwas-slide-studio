# 🎯 Diwas Slide Studio

An AI-powered, fully local presentation generator. Upload a PDF or Word document, chat with the AI to shape your slides, and export a world-class deck — all for free, running entirely on your machine.

---

## Features

- **Chat-driven editing** — describe changes in plain English and slides update live
- **Document support** — PDF, DOCX, DOC, and TXT
- **Auto-generated visuals** — bar charts, pie charts, two-column layouts, quote slides, and more
- **4 visual themes** — Professional, Modern, Minimal, Bold
- **Dual export** — download as `.pptx` (editable) or `.pdf` (shareable)
- **Multi-LLM routing** — uses Groq → Gemini → Ollama in priority order
- **100% local & free** — your documents never leave your machine

---

## Demo

| Chat Interface | Live Preview |
|---|---|
| Type natural language commands | Thumbnails update after every change |
| *"Add a market trends slide"* | Slide deck rebuilds instantly |
| *"Change theme to bold"* | Download PPTX or PDF anytime |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/diwastimsina/diwas-slide-studio.git
cd diwas-slide-studio
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install & start Ollama (free local LLM)

Download from [ollama.ai](https://ollama.ai), then:

```bash
ollama pull deepseek-r1:latest
ollama serve
```

### 4. Run the app

```bash
bash run.sh
```

Then open **http://localhost:8501** in your browser.

---

## Optional: Free API Keys for Faster Generation

Ollama works great but can be slow on older machines. Paste a free API key in the sidebar to speed things up dramatically.

| Provider | Speed | Free Tier | Link |
|---|---|---|---|
| **Groq** | ~5 sec | Generous daily limit | [console.groq.com](https://console.groq.com) |
| **Gemini Flash** | ~10 sec | 15 req/min | [aistudio.google.com](https://aistudio.google.com) |
| **Ollama** | ~60–90 sec | Unlimited, fully local | [ollama.ai](https://ollama.ai) |

The app automatically falls back to Ollama if no API keys are provided.

---

## How It Works

```
Upload PDF/DOCX
      ↓
Extract text (pypdf / python-docx)
      ↓
LLM analyzes content → structured JSON slide plan
      ↓
python-pptx renders slides + matplotlib draws charts
      ↓
Live preview thumbnails generated
      ↓
Chat to refine → LLM updates JSON → slides re-render
      ↓
Export PPTX or PDF
```

---

## Project Structure

```
diwas-slide-studio/
├── app.py                  # Streamlit chat UI
├── chat_engine.py          # Intent detection + slide modification prompts
├── llm_router.py           # Groq → Gemini → Ollama fallback router
├── document_processor.py   # PDF + DOCX text extraction
├── presentation_builder.py # PPTX slide renderer with charts
├── preview_renderer.py     # Live thumbnail generator
├── pdf_exporter.py         # PDF export via reportlab
├── requirements.txt
└── run.sh                  # One-click launcher
```

---

## Example Chat Commands

Once your slides are generated, try:

- *"Make the title slide more impactful"*
- *"Add a competitor analysis slide"*
- *"Change theme to modern"*
- *"Make all bullet points shorter"*
- *"Add speaker notes to every slide"*
- *"Add a bar chart comparing Q1 and Q2"*
- *"Remove slide 5"*
- *"What is the main finding of this document?"*

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) (for local LLM)
- 8 GB RAM recommended for `deepseek-r1:latest`
- Use `deepseek-r1:1.5b` for lower-memory machines

---

## Built With

- [Streamlit](https://streamlit.io) — UI framework
- [Ollama](https://ollama.ai) — local LLM runtime
- [python-pptx](https://python-pptx.readthedocs.io) — PowerPoint generation
- [matplotlib](https://matplotlib.org) — chart rendering
- [pypdf](https://pypdf.readthedocs.io) + [python-docx](https://python-docx.readthedocs.io) — document parsing
- [reportlab](https://www.reportlab.com) — PDF export

---

## License

MIT — free to use, modify, and share.

---

*Built by [Diwas Timsina](https://github.com/diwastimsina)*
