from dataclasses import dataclass, field


@dataclass(frozen=True)
class OllamaConfig:
    base_url   : str   = "http://localhost:11434"
    model      : str   = "llama3.2"
    embedding  : str   = "nomic-embed-text"
    temperature: float = 0.1


@dataclass(frozen=True)
class ChromaConfig:
    db_path        : str = "./chroma_db"
    collection_name: str = "grid_decarb_kb"


@dataclass(frozen=True)
class RetrieverConfig:
    search_type: str = "similarity"
    top_k      : int = 5


@dataclass(frozen=True)
class DataConfig:
    regulations_dir: str = "data/regulations"
    roadmaps_dir   : str = "data/roadmaps"
    forecasts_dir  : str = "data/forecasts"
    grid_platform_dir: str = "data/grid_platform"
    policies_dir   : str = "data/policies"
    chunk_size     : int = 600
    chunk_overlap  : int = 100


@dataclass(frozen=True)
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass(frozen=True)
class AppConfig:
    ollama   : OllamaConfig   = field(default_factory=OllamaConfig)
    chroma   : ChromaConfig   = field(default_factory=ChromaConfig)
    retriever: RetrieverConfig= field(default_factory=RetrieverConfig)
    data     : DataConfig     = field(default_factory=DataConfig)
    api      : APIConfig      = field(default_factory=APIConfig)

    categories: tuple = (
        "regulations",
        "roadmaps",
        "forecasts",
        "ecostuxure",
        "policies",
    )


cfg = AppConfig()