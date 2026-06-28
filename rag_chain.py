# rag_chain.py
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA
from config import cfg


# -- Prompt Templates ---------------------------------------------------------

QNA_PROMPT = """
You are an expert grid decarbonisation planning assistant for electrical
distribution utilities and Company STRUXURE Grid deployments.

Use ONLY the context below to answer the question.
If the answer is not in the context, say:
"I don't have enough information in the knowledge base to answer this."

Always cite the source document and regulation reference where applicable.

Context:
{context}

Question:
{question}

Answer:
- Response:
- Regulatory Reference (if applicable):
- Source Document:
"""

REPORT_PROMPT = """
You are a senior grid decarbonisation planning engineer.
Generate a comprehensive planning report based on the context below.

Context:
{context}

Planning Request:
{question}

Generate a structured planning report with the following sections:

1. Executive Summary
2. Current Grid Assessment
3. Renewable Integration Feasibility
4. Voltage and Power Quality Impact
5. Regulatory Compliance (CEA / DISCOM / IEC standards)
6. Recommended Grid Upgrades
7. STRUXURE Integration Opportunities
8. Estimated Timeline and Phasing
9. Risk Assessment
10. Next Steps and Action Items

Be specific, technical, and cite relevant standards where applicable.
"""

FEEDER_PROMPT = """
You are a distribution network planning specialist with expertise in
Company STRUXURE Grid and Indian DISCOM operations.

Use ONLY the context below to provide feeder-level recommendations.
If the answer is not in the context, say:
"Insufficient data in knowledge base for this feeder analysis."

Context:
{context}

Feeder Analysis Request:
{question}

Provide structured feeder-level recommendations:

- Feeder Upgrade Priority  : (Critical / High / Medium / Low)
- Voltage Violation Risk   : (Yes / No / Needs Study)
- Protection Relay Changes : (required settings or relay upgrades)
- Reactive Power Compensation : (capacitor bank sizing or STATCOM)
- Smart Metering Upgrade   : (Yes / No / Type recommended)
- STRUXURE Integration  : (relevant modules - PME, ADMS, Grid Edge)
- Regulatory Compliance    : (CEA / DISCOM requirements to meet)
- Recommended Timeline     : (immediate / 3 months / 6 months / 1 year)
- Estimated Cost Range     : (based on retrieved data if available)
- Additional Notes         :
"""


# -- Chain Builder ------------------------------------------------------------

def get_embeddings():
    return OllamaEmbeddings(
        model    = cfg.ollama.embedding,
        base_url = cfg.ollama.base_url,
    )


def get_vectorstore(category_filter: str = None):
    embeddings  = get_embeddings()
    vectorstore = Chroma(
        collection_name    = cfg.chroma.collection_name,
        embedding_function = embeddings,
        persist_directory  = cfg.chroma.db_path,
    )
    return vectorstore


def build_chain(prompt_template: str, category_filter: str = None):
    vectorstore   = get_vectorstore()
    search_kwargs = {"k": cfg.retriever.top_k}

    if category_filter and category_filter != "all":
        search_kwargs["filter"] = {"category": category_filter}

    retriever = vectorstore.as_retriever(
        search_type  = cfg.retriever.search_type,
        search_kwargs= search_kwargs,
    )

    llm = OllamaLLM(
        model      = cfg.ollama.model,
        base_url   = cfg.ollama.base_url,
        temperature= cfg.ollama.temperature,
    )

    prompt = PromptTemplate(
        template       = prompt_template,
        input_variables= ["context", "question"]
    )

    chain = RetrievalQA.from_chain_type(
        llm                    = llm,
        chain_type             = "stuff",
        retriever              = retriever,
        return_source_documents= True,
        chain_type_kwargs      = {"prompt": prompt}
    )

    return chain


def run_query(question: str, category_filter: str = None) -> dict:
    chain  = build_chain(QNA_PROMPT, category_filter)
    result = chain.invoke({"query": question})
    return _format_result(result)


def run_report(question: str, category_filter: str = None) -> dict:
    chain  = build_chain(REPORT_PROMPT, category_filter)
    result = chain.invoke({"query": question})
    return _format_result(result)


def run_feeder(question: str, category_filter: str = None) -> dict:
    chain  = build_chain(FEEDER_PROMPT, category_filter)
    result = chain.invoke({"query": question})
    return _format_result(result)


def _format_result(result: dict) -> dict:
    return {
        "answer": result["result"],
        "sources": [
            {
                "source"  : doc.metadata.get("source", "Unknown"),
                "category": doc.metadata.get("category", "Unknown"),
                "page"    : doc.metadata.get("page", "N/A"),
            }
            for doc in result["source_documents"]
        ]
    }


def get_collection_stats() -> dict:
    vectorstore = get_vectorstore()
    data        = vectorstore.get()
    metadatas   = data.get("metadatas", [])

    category_counts = {}
    for m in metadatas:
        cat = m.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "total_chunks"    : len(metadatas),
        "category_counts" : category_counts,
    }