# Document Portal

LangChain-based document analysis, comparison, and conversational RAG over PDFs, DOCX, and text files. Models are loaded from `config/config.yaml` (Google Gemini embeddings/chat, Groq, or InferX).

## Environment (micromamba + Homebrew)

This project uses Homebrew `micromamba` with a user-level prefix (not the Cellar prefix):

```
/opt/homebrew/bin/micromamba
        │
        │  MAMBA_ROOT_PREFIX
        ↓
~/.local/share/mamba
        │
        ├── pkgs/
        └── envs/
              └── doc_portal/
```

### One-time setup

```bash
export MAMBA_ROOT_PREFIX="$HOME/.local/share/mamba"

# Create the env if it does not exist (Python 3.12)
/opt/homebrew/bin/micromamba create -n doc_portal python=3.12 -y

eval "$(/opt/homebrew/bin/micromamba shell hook -s zsh)"
micromamba activate doc_portal

cd Document_portal
pip install -r requirements.txt
pip install -e .
```

Always set `MAMBA_ROOT_PREFIX` before `micromamba` commands so the env lives under `~/.local/share/mamba/envs/doc_portal`, not Homebrew’s Cellar.

### Activate later

```bash
export MAMBA_ROOT_PREFIX="$HOME/.local/share/mamba"
eval "$(/opt/homebrew/bin/micromamba shell hook -s zsh)"
micromamba activate doc_portal
```

Or run a command without activating:

```bash
export MAMBA_ROOT_PREFIX="$HOME/.local/share/mamba"
/opt/homebrew/bin/micromamba run -n doc_portal python test.py
```

## Configuration

Copy or create a `.env` in `Document_portal/` with:

```
GOOGLE_API_KEY=...
GROQ_API_KEY=...
INFERX_API_KEY=...
LLM_PROVIDER=google   # or groq or inferx
```

Model names and temperatures are in `config/config.yaml`.

## Layout

- `src/document_analyzer` — ingest PDFs and run structured analysis
- `src/document_compare` — compare two documents
- `src/document_chat` — FAISS-backed conversational RAG
- `utils/model_loader.py` — embeddings and LLM factory
- `prompt/prompt_library.py` — prompt registry
