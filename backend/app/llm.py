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
\
\
\
       

    def __init__(self, model_name: str):
        self._model_name = model_name
        self._model: Any = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"[embeddings] loading model {self._model_name}…")
            self._model = SentenceTransformer(self._model_name)
            logger.info("[embeddings] model ready")

    def embed_query(self, text: str) -> list[float]:
                                                                  
        self._load()
        vec = self._model.encode(
            f"passage: {text}",
            normalize_embeddings=True,
        )
        return vec.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
                          
        self._load()
        vecs = self._model.encode(
            [f"passage: {t}" for t in texts],
            normalize_embeddings=True,
            batch_size=8,
        )
        return [v.tolist() for v in vecs]

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
