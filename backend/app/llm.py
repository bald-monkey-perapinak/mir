\
\
\
   
import logging
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings

logger = logging.getLogger(__name__)

                                                                                

def get_llm(temperature: float = 0.4) -> ChatGroq:
\
\
\
       
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        max_retries=3,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

_llm_instances: dict[float, ChatGroq] = {}

def llm(temperature: float = 0.4) -> ChatGroq:
                                                                       
    key = round(temperature, 1)
    if key not in _llm_instances:
        _llm_instances[key] = get_llm(temperature=temperature)
    return _llm_instances[key]

                                                                                

class LocalEmbeddings:
    """
    Обёртка над fastembed.TextEmbedding.
    Использует ONNX Runtime вместо PyTorch — старт за ~0.3 с вместо ~5 с,
    образ Docker меньше на ~2 ГБ.
    """

    def __init__(self, model_name: str):
        self._model_name = model_name
        self._model: Any = None

    def _load(self):
        if self._model is None:
            import os
            from fastembed import TextEmbedding
            cache_dir = os.getenv("FASTEMBED_CACHE_DIR", "/tmp/fastembed_cache")
            logger.info(f"[embeddings] loading model {self._model_name}…")
            self._model = TextEmbedding(
                model_name=self._model_name,
                cache_dir=cache_dir,
            )
            logger.info("[embeddings] model ready")

    def embed_query(self, text: str) -> list[float]:
        """Векторизует один запрос (query-prefix для e5)."""
        self._load()
        # fastembed сам добавляет нужные префиксы для e5-моделей
        vec = next(self._model.embed([text]))
        return vec.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Батчевая векторизация документов."""
        self._load()
        return [v.tolist() for v in self._model.embed(texts)]

_embeddings: LocalEmbeddings | None = None

def embeddings() -> LocalEmbeddings:
                                              
    global _embeddings
    if _embeddings is None:
        _embeddings = LocalEmbeddings(settings.EMBEDDING_MODEL)
    return _embeddings

                                                                                

def make_json_chain(system: str, human_template: str, temperature: float = 0.4):
\
\
\
       
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human",  human_template),
    ])
    return prompt | llm(temperature) | JsonOutputParser()
