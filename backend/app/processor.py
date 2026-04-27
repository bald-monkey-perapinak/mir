\
\
\
\
\
\
\
\
\
\
\
\
\
\
   

from __future__ import annotations

import re
import logging
import asyncio
from typing import TypedDict, Annotated
import operator

import chardet
from langgraph.graph import StateGraph, START, END

from app.llm import embeddings as get_embeddings_model

logger = logging.getLogger(__name__)

                                                                                 
             
                                                                                 

class DocumentState(TypedDict):
                  
    doc_id:      str
    file_path:   str
    file_format: str

                        
    raw_text:      str
    clean_text:    str
                                                
    chunks:        list[dict]

                  
    chunk_objects: list[dict]                                                
    chunk_count:   int

                                                                             
    errors: Annotated[list[str], operator.add]

                                                                                 
       
                                                                                 

def node_extract(state: DocumentState) -> dict:
                                                           
    fmt = state["file_format"].lower()
    path = state["file_path"]
    try:
        if fmt == "pdf":
            text = _extract_pdf(path)
        elif fmt == "docx":
            text = _extract_docx(path)
        elif fmt == "txt":
            text = _extract_txt(path)
        else:
            raise ValueError(f"Unsupported file format: {fmt}")

        if not text.strip():
            raise ValueError("Document produced no extractable text")

        logger.info(f"[extract] {len(text):,} chars from {fmt.upper()}")
        return {"raw_text": text}

    except Exception as exc:
        logger.error(f"[extract] {exc}")
        return {"raw_text": "", "errors": [f"extract: {exc}"]}

def node_clean(state: DocumentState) -> dict:
                                                                    
    text = state.get("raw_text", "")
    if not text:
        return {"clean_text": "", "errors": ["clean: no raw_text available"]}

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[^\S\n]+\n", "\n", text)
    text = text.strip()

    logger.info(f"[clean] {len(text):,} chars after normalisation")
    return {"clean_text": text}

def node_chunk(state: DocumentState) -> dict:
                                                                      
    text = state.get("clean_text", "")
    if not text:
        return {"chunks": [], "errors": ["chunk: clean_text is empty"]}

    chunks = _split_into_chunks(text)
    if not chunks:
        return {"chunks": [], "errors": ["chunk: splitting produced 0 chunks"]}

    logger.info(f"[chunk] produced {len(chunks)} chunks")
    return {"chunks": chunks}

async def node_embed(state: DocumentState) -> dict:
                                                                                        
    chunks = state.get("chunks", [])
    if not chunks:
        return {"chunk_objects": [], "errors": ["embed: no chunks to embed"]}

    emb_model = get_embeddings_model()
    texts = [c["chunk_text"] for c in chunks]

    try:
                                                                          
        vectors: list[list[float]] = await asyncio.to_thread(
            emb_model.embed_documents, texts
        )
    except Exception as exc:
        logger.error(f"[embed] batch embedding failed: {exc}")
                                                       
        vectors = [[0.0] * 384 for _ in chunks]

    chunk_objects = [
        {**chunk, "chunk_index": idx, "embedding": vector}
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    logger.info(f"[embed] embedded {len(chunk_objects)} chunks in batch")
    return {"chunk_objects": chunk_objects, "chunk_count": len(chunk_objects)}

async def node_persist(state: DocumentState) -> dict:
                                                           
    from sqlalchemy import update as sa_update
    from app.models import Document, DocumentChunk
    from app.database import AsyncSessionLocal

    doc_id = state["doc_id"]
    objects = state.get("chunk_objects", [])

    if not objects:
        return {"errors": ["persist: chunk_objects list is empty"]}

    try:
        async with AsyncSessionLocal() as db:
            db_chunks = [
                DocumentChunk(
                    document_id=doc_id,
                    chunk_index=c["chunk_index"],
                    section_title=c.get("section_title"),
                    chunk_text=c["chunk_text"],
                    token_count=c.get("token_count", 0),
                    embedding=c["embedding"],
                )
                for c in objects
            ]
            db.add_all(db_chunks)
            await db.flush()

            await db.execute(
                sa_update(Document)
                .where(Document.id == doc_id)
                .values(status="indexed", chunk_count=len(db_chunks))
            )
            await db.commit()

        logger.info(f"[persist] saved {len(objects)} chunks for doc {doc_id}")
        return {"chunk_count": len(objects)}

    except Exception as exc:
        logger.error(f"[persist] {exc}")
        return {"chunk_count": 0, "errors": [f"persist: {exc}"]}

def node_error_handler(state: DocumentState) -> dict:
                                                            
    errs = state.get("errors", [])
    logger.error(
        f"[doc_pipeline] FAILED doc_id={state['doc_id']} "
        f"errors={errs}"
    )
    return {"chunk_count": 0}

                                                                                 
                     
                                                                                 

def _route(state: DocumentState) -> str:
                                                                          
    return "error" if state.get("errors") else "ok"

                                                                                 
                
                                                                                 

def _build_graph():
    g = StateGraph(DocumentState)

    g.add_node("extract",       node_extract)
    g.add_node("clean",         node_clean)
    g.add_node("chunk",         node_chunk)
    g.add_node("embed",         node_embed)
    g.add_node("persist",       node_persist)
    g.add_node("error_handler", node_error_handler)

    g.add_edge(START, "extract")

                                                             
    sequence = [
        ("extract", "clean"),
        ("clean",   "chunk"),
        ("chunk",   "embed"),
        ("embed",   "persist"),
    ]
    for src, dst in sequence:
        g.add_conditional_edges(
            src, _route, {"ok": dst, "error": "error_handler"}
        )

    g.add_edge("persist",       END)
    g.add_edge("error_handler", END)

    return g.compile()

_graph = None

def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph

                                                                                 
            
                                                                                 

async def process_document(doc_id: str, file_path: str, file_format: str, db=None) -> int:
\
\
\
\
\
\
\
       
    graph = _get_graph()

    initial: DocumentState = {
        "doc_id":        doc_id,
        "file_path":     file_path,
        "file_format":   file_format,
        "raw_text":      "",
        "clean_text":    "",
        "chunks":        [],
        "chunk_objects": [],
        "chunk_count":   0,
        "errors":        [],
    }

    final = await graph.ainvoke(initial)

    if final.get("errors"):
        raise ValueError("; ".join(final["errors"]))

    return final.get("chunk_count", 0)

                                                                                 
                                              
                                                                                 

def _extract_pdf(path: str) -> str:
    import pdfplumber
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
            else:
                try:
                    import pytesseract
                    img = page.to_image(resolution=200).original
                    text = pytesseract.image_to_string(img, lang="rus+eng")
                    pages.append(text)
                except Exception as exc:
                    logger.warning(f"OCR page skipped: {exc}")
    return "\n\n".join(pages)

def _extract_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    parts: list[str] = []
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        style = para.style.name if para.style else ""
        parts.append(
            f"\n## {para.text.strip()}\n" if "Heading" in style
            else para.text.strip()
        )
    return "\n".join(parts)

def _extract_txt(path: str) -> str:
    with open(path, "rb") as fh:
        raw = fh.read()
    enc = chardet.detect(raw)["encoding"] or "utf-8"
    return raw.decode(enc, errors="replace")

def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) / 0.75))

def _split_into_chunks(text: str, target: int = 700) -> list[dict]:
\
\
\
\
\
\
\
\
\
\
\
       
    MIN_TOKENS = 20                                                    

                                                                              
                                                                        
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", "\n\n", text)

    chunks: list[dict] = []
    section = "Документ"
    paragraphs = re.split(r"\n{2,}", text)
    buf:   list[str] = []
    btoks: int = 0

    def _is_heading(para: str) -> bool:
        return bool(re.match(r"^#{1,3}\s+", para)) or (
            len(para) < 120 and para.isupper() and len(para.split()) >= 2
        )

    def _flush(force: bool = False):
        nonlocal btoks
        body = "\n\n".join(buf).strip()
        toks = _estimate_tokens(body)
        if toks >= MIN_TOKENS or (force and toks > 0):
            chunks.append({
                "section_title": section,
                "chunk_text":    body,
                "token_count":   toks,
            })
        buf.clear()
        btoks = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if _is_heading(para):
            _flush()
            section = para.lstrip("#").strip()
                                                                              
                                                                          
                                                      
            buf.append(f"[{section}]")
            btoks += _estimate_tokens(section)
            continue

        pt = _estimate_tokens(para)
        if btoks + pt > target and buf:
            _flush()

        buf.append(para)
        btoks += pt

    _flush(force=True)                                                 

                                                                              
    if not chunks:
        logger.warning(
            "[chunk] primary splitter yielded 0 chunks — using character fallback")
        char_limit = target * 4                                
        for i in range(0, max(len(text), 1), char_limit):
            fragment = text[i: i + char_limit].strip()
            if fragment:
                chunks.append({
                    "section_title": "Документ",
                    "chunk_text":    fragment,
                    "token_count":   _estimate_tokens(fragment),
                })

    return chunks
