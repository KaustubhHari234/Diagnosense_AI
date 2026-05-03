<div align="center">

# Diagnosense AI

### An AI-powered Medical Report Diagnosis Platform

*Upload your medical reports. Ask questions. Receive grounded, source-cited insights powered by Retrieval-Augmented Generation.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-VectorDB-blueviolet)](https://www.pinecone.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Google Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

</div>

---

## Overview

**Diagnosense AI** is an end-to-end clinical assistant that turns unstructured medical PDFs into searchable, queryable knowledge. Patients upload their lab reports, scans, or discharge summaries; the system chunks and embeds the text into a Pinecone vector index, then uses Google's **Gemini 2.5 Flash** through a LangChain RAG pipeline to generate a probable diagnosis, key findings, and recommended next steps — every response anchored to the original source.

A **role-based access control (RBAC)** layer keeps the workflow safe and auditable:

| Role | Capabilities |
|------|--------------|
| **Patient** | Upload reports, request diagnosis from their own documents |
| **Doctor** | Review the diagnosis history of any patient by username |
| **Admin** | Reserved role (no diagnosis generation by design) |

---

## Key Features

- **Multi-PDF ingestion** — upload one or many medical reports in a single request
- **Domain-tuned embeddings** — `sentence-transformers/embeddinggemma-300m-medical` for semantically rich medical text
- **RAG-grounded answers** — Gemini 2.5 Flash responds *only* from retrieved report context, with cited source filenames
- **Structured clinical output** — every diagnosis returns: probable diagnosis, key findings, suggested next steps
- **Persistent diagnosis history** — every Q&A is timestamped and stored in MongoDB for longitudinal review
- **Secure auth** — HTTP Basic Auth backed by bcrypt-hashed passwords
- **Polished Streamlit UI** — separate dashboards for patients and doctors

---

## System Architecture

```
┌────────────────────┐         ┌───────────────────────────────┐
│   Streamlit UI     │         │         FastAPI Server         │
│   (client/app.py)  │ ──────► │           server/main.py       │
│                    │  HTTP   │                                │
│  • Login / Signup  │  Basic  │  /auth     →  signup, login    │
│  • Patient Upload  │  Auth   │  /reports  →  upload + index   │
│  • Diagnosis Form  │         │  /diagnosis→  RAG query        │
│  • Doctor Review   │         └───────────────────────────────┘
└────────────────────┘                       │
                                             ▼
                          ┌──────────────────────────────────┐
                          │            Data Plane            │
                          │                                  │
                          │  MongoDB   →  users / reports /  │
                          │              diagnosis_history   │
                          │                                  │
                          │  Pinecone  →  chunk embeddings   │
                          │              (dotproduct, AWS)   │
                          │                                  │
                          │  Gemini    →  diagnosis LLM      │
                          │  HF Embed  →  medical embeddings │
                          └──────────────────────────────────┘
```

### Request flow — generating a diagnosis

1. Patient uploads PDFs → `POST /reports/upload`
2. Server saves files, splits via `RecursiveCharacterTextSplitter` (500 chars, 100 overlap)
3. Chunks are embedded and upserted into Pinecone with `doc_id`, `uploader`, and `source` metadata
4. Patient asks a question → `POST /diagnosis/from_report`
5. Question is embedded; Pinecone returns the top-5 semantically similar chunks for that `doc_id`
6. LangChain `PromptTemplate | LLM` chain produces a structured diagnosis
7. The result is persisted to `diagnosis_history` and returned with cited sources

---

## Project Structure

```
Diagnosense_AI/
│
├── server/                       FastAPI backend
│   ├── main.py                   App factory + CORS + routers
│   ├── auth/
│   │   ├── route.py              /auth/signup, /auth/login, authenticate dep
│   │   ├── models.py             SignupRequest schema
│   │   └── hash_utils.py         bcrypt hash + verify
│   ├── reports/
│   │   ├── route.py              /reports/upload (patient-only)
│   │   └── vectorstore.py        PDF → chunks → embeddings → Pinecone
│   ├── diagnosis/
│   │   ├── route.py              /diagnosis/from_report, /by_patient_name
│   │   └── query.py              RAG chain (Pinecone retrieve → Gemini)
│   ├── config/
│   │   └── db.py                 Mongo client + collections
│   └── models/
│       └── db_models.py          UserOut, ReportMeta, DiagnosisRecord
│
├── client/                       Streamlit frontend
│   ├── app.py                    Patient & Doctor dashboards
│   └── requirements.txt
│
├── uploaded_dir/                 Local PDF cache
├── main.py                       Health-check entrypoint
├── requirements.txt              Backend dependencies
├── pyproject.toml
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | Streamlit, Requests |
| **LLM** | Google Gemini 2.5 Flash (`langchain-google-genai`) |
| **Embeddings** | `sentence-transformers/embeddinggemma-300m-medical` |
| **Vector Store** | Pinecone (Serverless, AWS, dotproduct metric) |
| **Database** | MongoDB (`pymongo`) |
| **PDF Parsing** | `langchain-community` PyPDFLoader |
| **Auth** | HTTP Basic Auth + `passlib[bcrypt]` |
| **Orchestration** | LangChain (Core + Community) |

---

## Getting Started

### 1. Prerequisites

- Python **3.11+**
- A **MongoDB** connection string (Atlas or self-hosted)
- A **Pinecone** account + API key
- A **Google AI Studio** API key for Gemini

### 2. Clone & install

```bash
git clone https://github.com/<your-username>/Diagnosense_AI.git
cd Diagnosense_AI

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file at the project root:

```env
# MongoDB
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net
DB_NAME=rbac-diagnosis

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=us-east-1
PINECONE_INDEX_NAME=rbac-diagnosis-index

# Google Gemini
GOOGLE_API_KEY=your_google_api_key

# Embeddings (optional override)
EMBED_MODEL_NAME=sentence-transformers/embeddinggemma-300m-medical

# Local upload cache
UPLOAD_DIR=./uploaded_dir

# Frontend
API_URL=http://localhost:8000
```

### 4. Run the backend

```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs are available at **http://localhost:8000/docs**.

### 5. Run the Streamlit client

```bash
streamlit run client/app.py
```

Open **http://localhost:8501** and sign up as either a `patient` or a `doctor`.

---

## API Reference

### Auth

| Method | Endpoint | Body / Auth | Description |
|--------|----------|-------------|-------------|
| `POST` | `/auth/signup` | `{username, password, role}` | Create a new account |
| `GET`  | `/auth/login`  | HTTP Basic | Verify credentials, return profile |

### Reports *(patient only)*

| Method | Endpoint | Body / Auth | Description |
|--------|----------|-------------|-------------|
| `POST` | `/reports/upload` | `multipart files[]` + Basic | Index PDFs and return a `doc_id` |

### Diagnosis

| Method | Endpoint | Body / Auth | Description |
|--------|----------|-------------|-------------|
| `POST` | `/diagnosis/from_report` | `doc_id`, `question` (form) + Basic | Generate a RAG diagnosis (patient only) |
| `GET`  | `/diagnosis/by_patient_name` | `patient_name` (query) + Basic | Fetch a patient's diagnosis history (doctor only) |

### Sample diagnosis response

```json
{
  "diagnosis": "1) Probable diagnosis: ...\n2) Key findings: ...\n3) Recommended next steps: ...",
  "sources": ["cbc_2026_03.pdf", "lipid_panel.pdf"]
}
```

---

## How RAG Is Wired

The retrieval pipeline lives in `server/diagnosis/query.py`:

```python
prompt = PromptTemplate.from_template("""
You are a medical assistant. Using only the provided context, produce:
1) A concise probable diagnosis (4-5 lines)
2) Key major findings from the report (bullet points)
3) Recommended next steps — labeled as suggestions, not medical advice.

Context: {context_text}
User question: {question}
""")

rag_chain = prompt | llm    # LangChain LCEL composition
```

Pinecone matches are **filtered by `doc_id`**, so a patient's question can never retrieve another patient's chunks — RBAC is enforced at both the API layer *and* the retrieval layer.

---

## Security Notes

- Passwords are stored as **bcrypt hashes** (`passlib[bcrypt]`); plaintext never touches the database
- HTTP Basic Auth is used for simplicity — for production, terminate over **HTTPS** and consider migrating to OAuth2 / JWT
- CORS is currently `*` for development; **lock this down** before deploying
- Generated diagnoses are explicitly framed as **suggestions, not medical advice** in the prompt template

---

## Roadmap

- [ ] JWT-based authentication and refresh tokens
- [ ] DICOM and image-based report support (radiology)
- [ ] Doctor-side annotation and override workflow
- [ ] Streaming token responses in the Streamlit UI
- [ ] Audit log for every diagnosis access (HIPAA-friendly)
- [ ] Dockerfile + docker-compose for one-command deployment

---

## Disclaimer

> Diagnosense AI is a **research and educational prototype**. It is **not** a regulated medical device and must **not** be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified clinician.

---

## License

This project is released under the **MIT License**. See `LICENSE` for details.

---

<div align="center">

**Built with FastAPI, LangChain, Pinecone, and Gemini.**

*If this project helped you, consider leaving a star.*

</div>
