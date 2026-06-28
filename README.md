# Grid Decarbonisation Planning RAG

A production-ready Retrieval Augmented Generation (RAG) system for electrical
distribution utilities and  STRUXURE Grid deployments.
Enables grid planners and engineers to query regulatory documents, decarbonisation
roadmaps, load forecasts, and STRUXURE documentation in natural language —
and generate structured planning reports and feeder-level recommendations.

Everything runs 100% locally. No cloud API. No data leaves the system.

---

## Problem Statement

Grid planners working on decarbonisation projects deal with hundreds of documents
spanning CEA regulations, DISCOM policies, IEC standards, OEM manuals, and load
forecasting reports. Finding the right information across these sources manually
is slow and error-prone — especially when making time-sensitive decisions about
feeder upgrades, renewable integration, and regulatory compliance.

This system ingests all relevant documents into a local vector database and
provides three intelligent output modes:

- Natural language QnA grounded in the knowledge base
- Structured planning reports for specific feeders and renewable projects
- Feeder-level upgrade and compliance recommendations

---

## Tech Stack

| Layer             | Tool                              |
|-------------------|-----------------------------------|
| LLM               | Llama 3.2 via Ollama (local)      |
| Embeddings        | nomic-embed-text via Ollama       |
| Vector Database   | ChromaDB (local persistent)       |
| RAG Framework     | LangChain                         |
| Backend API       | FastAPI                           |
| Frontend          | Streamlit                         |
| Document Loaders  | LangChain Community               |
| Package Manager   | uv                                |
| Language          | Python 3.12                       |

---

## Architecture

```
INPUT DOCUMENTS
PDF / TXT / DOCX / XLSX / CSV
(Regulations, Roadmaps, Forecasts, STRUXURE Docs, Policies)
          |
          v
   FASTAPI INGESTION API
   POST /api/ingest
          |
          v
   DOCUMENT LOADERS (LangChain)
   PyPDF / TextLoader / Docx2txt / UnstructuredExcel / CSVLoader
          |
          v
   CHUNKING LAYER
   RecursiveCharacterTextSplitter
   chunk_size=600, overlap=100
   metadata: category, source, page
          |
          v
   EMBEDDING LAYER
   nomic-embed-text via Ollama
          |
          v
   CHROMADB VECTOR STORE
   Collection: grid_decarb_kb
   Category filter on retrieval:
   regulations | roadmaps | forecasts | ecostuxure | policies
          |
          v
   FASTAPI RAG ENDPOINTS
   POST /api/query   -> QnA answer
   POST /api/report  -> Planning report
   POST /api/feeder  -> Feeder recommendations
          |
          v
   LLM LAYER
   Llama 3.2 via Ollama
   3 specialised prompt templates
          |
          v
   STREAMLIT FRONTEND
   3 tabs: QnA | Planning Report | Feeder Recommendations
   + Upload panel + Category filter sidebar
```

---

## Project Structure

```
grid-decarb-rag/
|
|-- config.py                        # Centralised configuration
|-- ingest.py                        # Document ingestion pipeline
|-- rag_chain.py                     # LangChain RAG logic + 3 prompt templates
|-- api.py                           # FastAPI backend
|-- app.py                           # Streamlit frontend
|-- setup.sh                         # One command full setup script
|-- requirements.txt                 # Python dependencies
|-- README.md
|
|-- data/
|   |-- regulations/                 # CEA regulations, IEC standards, DISCOM rules
|   |-- roadmaps/                    # Grid decarbonisation roadmaps
|   |-- forecasts/                   # Solar and EV load forecast reports and CSVs
|   |-- ecostuxure/                  # Company STRUXURE Grid documentation
|   |-- policies/                    # RDSS scheme, RPO targets, tariff orders
|
|-- chroma_db/                       # ChromaDB persistent vector store (auto created)
```

---

## Setup and Installation

### Prerequisites

- Ubuntu OS
- Python 3.9 or higher
- uv package manager
- Ollama installed and running

### Option 1 - Automated Setup (Recommended)

```bash
chmod +x setup.sh
./setup.sh
```

### Option 2 - Manual Setup

**Step 1 - Install uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

**Step 2 - Install Ollama and pull models**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
ollama pull nomic-embed-text
```

**Step 3 - Create virtual environment and install dependencies**
```bash
uv venv
source .venv/bin/activate
uv add langchain langchain-community langchain-chroma langchain-ollama \
       chromadb fastapi uvicorn streamlit \
       pypdf python-docx docx2txt openpyxl \
       unstructured python-multipart requests
```

**Step 4 - Create folder structure**
```bash
mkdir -p data/regulations data/roadmaps data/forecasts data/ecostuxure data/policies chroma_db
```

**Step 5 - Add documents to data folders and run ingestion**
```bash
uv run python ingest.py
```

**Step 6 - Launch backend and frontend**
```bash
# Terminal 1
uv run python api.py

# Terminal 2
uv run streamlit run app.py
```

Open browser:
- Streamlit UI  : http://localhost:8501
- FastAPI docs  : http://localhost:8000/docs

---

## Configuration

All configuration is centralised in `config.py` using frozen Python dataclasses.
No `.env` file required. Change anything in one place and it reflects everywhere.

```python
class OllamaConfig:
    base_url   : str   = "http://localhost:11434"
    model      : str   = "llama3.2"
    embedding  : str   = "nomic-embed-text"
    temperature: float = 0.1

class ChromaConfig:
    db_path        : str = "./chroma_db"
    collection_name: str = "grid_decarb_kb"

class RetrieverConfig:
    search_type: str = "similarity"
    top_k      : int = 5

class DataConfig:
    chunk_size    : int = 600
    chunk_overlap : int = 100

class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
```

---

## Knowledge Base Categories

| Category     | Contents                                                              |
|--------------|-----------------------------------------------------------------------|
| regulations  | CEA connectivity standards, IEC 61850, protection requirements        |
| roadmaps     | India grid decarbonisation roadmap 2030, state level plans            |
| forecasts    | Solar capacity forecasts, EV load projections, feeder level data      |
| ecostuxure   | STRUXURE Grid ADMS, PME, Asset Advisor, Microgrid Advisor docs     |
| policies     | RDSS scheme guidelines, RPO targets, net metering policies, DISCOM    |

---

## API Endpoints

| Method | Endpoint          | Purpose                                     |
|--------|-------------------|---------------------------------------------|
| GET    | /api/health       | System health check — Ollama + ChromaDB     |
| GET    | /api/categories   | List available document categories          |
| GET    | /api/documents    | Chunk count per category                    |
| POST   | /api/ingest       | Upload and ingest a document                |
| POST   | /api/ingest/all   | Ingest all documents in data/ folders       |
| POST   | /api/query        | Natural language QnA                        |
| POST   | /api/report       | Generate structured planning report         |
| POST   | /api/feeder       | Get feeder-level recommendations            |

Full interactive API documentation available at http://localhost:8000/docs

---

## Output Modes

### Mode 1 — QnA
Ask natural language questions grounded in the knowledge base.

Sample questions:
- What are the CEA regulations for rooftop solar interconnection at 11kV feeder level?
- What is the maximum DG penetration allowed on a single 11kV feeder?
- What does STRUXURE ADMS DERM module do for renewable integration?
- What is the BESCOM net metering compensation rate for FY 2023-24?

### Mode 2 — Planning Report
Generate a comprehensive 10-section planning report for a specific feeder
and renewable integration project. Includes executive summary, voltage impact
analysis, regulatory compliance checklist, upgrade recommendations, STRUXURE
integration opportunities, and estimated timeline.

Sample input:
- Feeder: F-7 Indiranagar Commercial
- Addition: 500 kW rooftop solar
- Voltage level: 11kV

### Mode 3 — Feeder Recommendations
Get structured recommendations per feeder covering upgrade priority, voltage
violation risk, protection relay changes, reactive power compensation, smart
metering upgrades, STRUXURE integration, regulatory compliance, timeline,
and estimated cost range.

---

## Prompt Engineering

Three specialised prompt templates are used depending on the output mode:

**QnA Prompt** — instructs LLM to answer factually from context, cite regulatory
references and source documents, and respond with structured fields.

**Planning Report Prompt** — instructs LLM to generate a 10-section engineering
report with executive summary, feasibility assessment, regulatory compliance,
upgrade roadmap, STRUXURE integration, and risk assessment.

**Feeder Recommendation Prompt** — instructs LLM to output structured feeder
recommendations across 9 dimensions: upgrade priority, voltage risk, protection,
reactive power, smart metering, STRUXURE modules, regulations, timeline, cost.

All prompts include a hallucination guardrail — if the answer is not in the
retrieved context, the LLM responds with a specific not-found message rather
than fabricating an answer.

---

## Adding New Documents

To extend the knowledge base:

1. Add the file to the appropriate folder under data/
2. Upload via Streamlit sidebar or call the API directly:

```bash
curl -X POST http://localhost:8000/api/ingest \
     -F "file=@your_document.pdf" \
     -F "category=regulations"
```

3. The document is automatically chunked, embedded, and stored in ChromaDB.
   No restart required.

Supported file formats: PDF, TXT, DOCX, XLSX, XLS, CSV

---

## Key Learning Outcomes

- Production-grade RAG system with FastAPI + Streamlit separation of concerns
- Multiple specialised prompt templates for different output modes
- Category-based metadata filtering in ChromaDB for targeted retrieval
- File upload and dynamic ingestion via REST API without system restart
- Domain-specific prompt engineering for electrical distribution use cases
- Frozen Python dataclasses for type-safe centralised configuration
- Hallucination guardrails in prompt design for high-stakes planning use cases

---

## Domain Context

This project is specifically designed for  electrical
distribution and STRUXURE Grid domain. It covers:

- Indian regulatory framework: CEA, KERC, DISCOM, RDSS scheme
- Renewable integration: Rooftop solar, EV charging, BESS
- Grid standards: IEC 61850, IEC 61968, IEEE 519, EN 50160
- Company products: STRUXURE ADMS, PME, Asset Advisor, Easergy relays
- Planning concepts: Feeder penetration limits, VVO, DERM, duck curve management

---

## Author

Kumar Gaurav
Senior Software Engineer | Python | GenAI | RAG | ETL Pipelines | IoT Data
Capgemini Engineering | Bengaluru, India
GitHub: https://github.com/kumarg160491