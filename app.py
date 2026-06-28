# app.py
import streamlit as st
import requests
from config import cfg

API_BASE = f"http://localhost:{cfg.api.port}"

st.set_page_config(
    page_title="Grid Decarbonisation Planning RAG",
    page_icon="",
    layout="wide"
)

st.title("Grid Decarbonisation Planning RAG")
st.caption(
    f"LLM: {cfg.ollama.model} | "
    f"Embeddings: {cfg.ollama.embedding} | "
    f"Backend: FastAPI | "
    f"VectorDB: ChromaDB"
)
st.divider()


# -- Health Check -------------------------------------------------------------
def get_health():
    try:
        return requests.get(f"{API_BASE}/api/health", timeout=3).json()
    except Exception:
        return None


# -- Sidebar ------------------------------------------------------------------
with st.sidebar:
    # st.header("System Status")
    # health = get_health()
    # if health:
    #     st.success(f"API Running")
    #     st.success(f"Ollama: {health.get('ollama')}")
    #     st.success(f"ChromaDB: {health.get('chromadb')}")
    #     st.info(f"Total Chunks: {health.get('total_chunks', 0)}")
    # else:
    #     st.error("API not reachable. Run: uv run python api.py")

    # st.divider()
    st.header("Upload Document")

    category = st.selectbox(
        "Document Category",
        options=list(cfg.categories)
    )
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "txt", "docx", "xlsx", "csv"]
    )

    if st.button("Ingest Document", type="primary", use_container_width=True):
        if uploaded_file and category:
            with st.spinner("Ingesting document..."):
                resp = requests.post(
                    f"{API_BASE}/api/ingest",
                    files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                    data ={"category": category}
                )
            if resp.status_code == 200:
                data = resp.json()
                st.success(
                    f"Ingested: {data['filename']} "
                    f"({data['chunks_stored']} chunks)"
                )
            else:
                st.error(f"Ingestion failed: {resp.text}")
        else:
            st.warning("Please select a file and category.")

    st.divider()
    st.header("Category Filter")
    category_filter = st.radio(
        "Filter knowledge base by:",
        options=["all"] + list(cfg.categories),
        index=0
    )

    st.divider()
    # st.markdown("**Knowledge Base**")
    # try:
    #     docs = requests.get(f"{API_BASE}/api/documents").json()
    #     for cat, count in docs.get("category_counts", {}).items():
    #         st.markdown(f"- {cat}: `{count}` chunks")
    # except Exception:
    #     st.caption("Could not load document stats.")

    # st.divider()
    st.caption("Grid Decarbonisation RAG | Kumar Gaurav")


# -- Main Tabs ----------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "Ask a Question",
    "Generate Planning Report",
    "Feeder Recommendations",
])


# -- Tab 1: QnA ---------------------------------------------------------------
with tab1:
    st.subheader("Ask a Question")
    st.caption("Ask anything from regulations, roadmaps, forecasts, or STRUXURE docs.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Sample Questions:**")
        q1 = st.button("CEA rooftop solar interconnection regulation")
        q2 = st.button("EV charging impact on distribution transformer")
        q3 = st.button("DISCOM net metering policy for commercial consumers")
        q4 = st.button("STRUXURE Grid ADMS capabilities")

        default_q = ""
        if q1: default_q = "What are the CEA regulations for rooftop solar interconnection at 11kV feeder level?"
        elif q2: default_q = "What is the impact of EV charging load on distribution transformers and what upgrades are needed?"
        elif q3: default_q = "What is the DISCOM net metering policy for commercial consumers above 100 kW?"
        elif q4: default_q = "What are the capabilities of STRUXURE Grid ADMS for renewable integration?"

        question = st.text_area(
            "Your question:",
            value      = default_q,
            height     = 120,
            placeholder= "Ask about regulations, grid planning, forecasts..."
        )

        ask_btn = st.button("Get Answer", type="primary", use_container_width=True)

    with col2:
        st.markdown("**Answer:**")
        if ask_btn and question.strip():
            with st.spinner("Searching knowledge base..."):
                resp = requests.post(
                    f"{API_BASE}/api/query",
                    json={
                        "question"       : question,
                        "category_filter": None if category_filter == "all" else category_filter
                    }
                )
            if resp.status_code == 200:
                data = resp.json()
                st.markdown(data["answer"])
                if data["sources"]:
                    st.divider()
                    st.markdown("**Sources Used:**")
                    for i, src in enumerate(data["sources"], 1):
                        with st.expander(f"Source {i}: {src['source']}"):
                            st.write(f"**Category :** {src['category']}")
                            st.write(f"**Document :** {src['source']}")
                            st.write(f"**Page     :** {src['page']}")
            else:
                st.error(f"API Error: {resp.text}")
        elif ask_btn:
            st.warning("Please enter a question.")
        else:
            st.info("Enter a question on the left and click Get Answer.")


# -- Tab 2: Planning Report ---------------------------------------------------
with tab2:
    st.subheader("Generate Planning Report")
    st.caption("Generate a comprehensive grid decarbonisation planning report.")

    col1, col2 = st.columns([1, 1])

    with col1:
        feeder_id    = st.text_input("Feeder / Zone ID", placeholder="e.g. Feeder F-7, Zone-3A")
        capacity_kw  = st.number_input("Renewable Capacity to Add (kW)", min_value=0, value=500, step=50)
        energy_type  = st.selectbox("Energy Type", ["Rooftop Solar", "Ground Mount Solar", "EV Charging", "Wind", "Battery Storage"])
        voltage_level= st.selectbox("Voltage Level", ["415V LT", "11kV", "33kV", "66kV", "132kV"])
        extra_context= st.text_area(
            "Additional Context (optional):",
            height=80,
            placeholder="e.g. urban area, mixed residential-commercial load, aging transformer..."
        )

        report_btn = st.button("Generate Report", type="primary", use_container_width=True)

    with col2:
        st.markdown("**Planning Report:**")
        if report_btn:
            planning_request = (
                f"Generate a decarbonisation planning report for {feeder_id}. "
                f"Planned addition: {capacity_kw} kW of {energy_type} at {voltage_level} level. "
                f"Additional context: {extra_context if extra_context else 'None provided'}. "
                f"Include voltage impact, regulatory compliance, upgrade recommendations, "
                f"and STRUXURE integration opportunities."
            )
            with st.spinner("Generating planning report..."):
                resp = requests.post(
                    f"{API_BASE}/api/report",
                    json={
                        "planning_request": planning_request,
                        "category_filter" : None if category_filter == "all" else category_filter
                    }
                )
            if resp.status_code == 200:
                data = resp.json()
                st.markdown(data["report"])
                if data["sources"]:
                    st.divider()
                    st.markdown("**Sources Used:**")
                    for i, src in enumerate(data["sources"], 1):
                        with st.expander(f"Source {i}: {src['source']}"):
                            st.write(f"**Category :** {src['category']}")
                            st.write(f"**Document :** {src['source']}")
                            st.write(f"**Page     :** {src['page']}")
            else:
                st.error(f"API Error: {resp.text}")
        else:
            st.info("Fill in feeder details on the left and click Generate Report.")


# -- Tab 3: Feeder Recommendations --------------------------------------------
with tab3:
    st.subheader("Feeder Level Recommendations")
    st.caption("Get specific upgrade and compliance recommendations per feeder.")

    col1, col2 = st.columns([1, 1])

    with col1:
        f_feeder_id   = st.text_input("Feeder ID", placeholder="e.g. F-7, Feeder-B3")
        f_load_type   = st.selectbox(
            "Load Type",
            ["Residential", "Commercial", "Industrial", "Mixed", "Agricultural"]
        )
        f_capacity    = st.number_input("Capacity Addition (kW)", min_value=0, value=500, step=50)
        f_voltage     = st.selectbox("Voltage Level", ["415V LT", "11kV", "33kV", "66kV"])

        feeder_btn = st.button("Get Recommendations", type="primary", use_container_width=True)

    with col2:
        st.markdown("**Feeder Recommendations:**")
        if feeder_btn and f_feeder_id:
            with st.spinner("Analysing feeder..."):
                resp = requests.post(
                    f"{API_BASE}/api/feeder",
                    json={
                        "feeder_id"      : f_feeder_id,
                        "load_type"      : f_load_type,
                        "capacity_kw"    : f_capacity,
                        "voltage_level"  : f_voltage,
                        "category_filter": None if category_filter == "all" else category_filter
                    }
                )
            if resp.status_code == 200:
                data = resp.json()
                st.markdown(data["recommendations"])
                if data["sources"]:
                    st.divider()
                    st.markdown("**Sources Used:**")
                    for i, src in enumerate(data["sources"], 1):
                        with st.expander(f"Source {i}: {src['source']}"):
                            st.write(f"**Category :** {src['category']}")
                            st.write(f"**Document :** {src['source']}")
                            st.write(f"**Page     :** {src['page']}")
            else:
                st.error(f"API Error: {resp.text}")
        elif feeder_btn:
            st.warning("Please enter a Feeder ID.")
        else:
            st.info("Enter feeder details on the left and click Get Recommendations.")