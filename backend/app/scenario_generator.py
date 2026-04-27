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
\
\
\
\
   

from __future__ import annotations

import asyncio
import logging
import itertools
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import JsonOutputParser

from app.llm import llm
from app.prompts import CARDS_PROMPT, TREE_PROMPT, FREE_TEXT_PROMPT

logger = logging.getLogger(__name__)

SCENARIO_TYPES  = ["cards", "tree", "free_text"]
RATE_LIMIT_SLEEP = 4                                                     

                                                           
REQUIRED_FIELDS: dict[str, list[str]] = {
    "cards":     ["title", "description", "options", "correct_option_index", "consequences"],
    "tree":      ["title", "description", "blocks", "correct_order"],
    "free_text": ["title", "question", "ideal_answer", "criteria"],
}

                                                                                 
             
                                                                                 

class ChunkTask(TypedDict):
    chunk_id:      str
    chunk_index:   int
    chunk_text:    str
    section_title: str
    scenario_type: str
    attempts:      int                           
    raw_json:      dict | None                
    valid:         bool

class ScenarioGenState(TypedDict):
                  
    doc_id:    str
    doc_title: str

                        
    tasks:     list[ChunkTask]                        

                  
    saved_count: int

                             
    errors: Annotated[list[str], operator.add]

                                                                                 
       
                                                                                 

async def node_load_chunks(state: ScenarioGenState) -> dict:
                                                        
    from sqlalchemy import select
    from app.models import DocumentChunk
    from app.database import AsyncSessionLocal

    doc_id = state["doc_id"]
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == doc_id)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()

        if not chunks:
            return {"tasks": [], "errors": [f"load_chunks: no chunks for doc {doc_id}"]}

                                           
        type_cycle = itertools.cycle(SCENARIO_TYPES)
        tasks: list[ChunkTask] = [
            {
                "chunk_id":      c.id,
                "chunk_index":   c.chunk_index,
                "chunk_text":    c.chunk_text[:2500],
                "section_title": c.section_title or "Раздел",
                "scenario_type": next(type_cycle),
                "attempts":      0,
                "raw_json":      None,
                "valid":         False,
            }
            for c in chunks
        ]

        logger.info(f"[load_chunks] loaded {len(tasks)} tasks for doc {doc_id}")
        return {"tasks": tasks}

    except Exception as exc:
        logger.error(f"[load_chunks] {exc}")
        return {"tasks": [], "errors": [f"load_chunks: {exc}"]}

async def node_generate(state: ScenarioGenState) -> dict:
\
\
\
       
    tasks    = state.get("tasks", [])
    doc_title = state.get("doc_title", "Документ")
    errs: list[str] = []

    prompt_map = {
        "cards":     CARDS_PROMPT,
        "tree":      TREE_PROMPT,
        "free_text": FREE_TEXT_PROMPT,
    }
    parser      = JsonOutputParser()
    temperature = 0.4

    updated_tasks: list[ChunkTask] = []

    for task in tasks:
        if task["valid"]:
            updated_tasks.append(task)
            continue

        prompt   = prompt_map[task["scenario_type"]]
        chain    = prompt | llm(temperature) | parser

        try:
            data: dict = await chain.ainvoke({
                "chunk_text":     task["chunk_text"],
                "section_title":  task["section_title"],
                "document_title": doc_title,
            })
            data["type"] = task["scenario_type"]
            updated_tasks.append({**task, "raw_json": data, "attempts": task["attempts"] + 1})
            logger.debug(f"[generate] chunk {task['chunk_index']} ({task['scenario_type']}) OK")

        except Exception as exc:
            logger.warning(f"[generate] chunk {task['chunk_index']} error: {exc}")
            errs.append(f"generate chunk {task['chunk_index']}: {exc}")
            updated_tasks.append({**task, "attempts": task["attempts"] + 1})

                                                    
        await asyncio.sleep(RATE_LIMIT_SLEEP)

    result = {"tasks": updated_tasks}
    if errs:
        result["errors"] = errs
    return result

def node_validate(state: ScenarioGenState) -> dict:
\
\
\
\
\
       
    tasks = state.get("tasks", [])
    updated: list[ChunkTask] = []

    for task in tasks:
        if task["valid"]:
            updated.append(task)
            continue

        data     = task.get("raw_json")
        required = REQUIRED_FIELDS.get(task["scenario_type"], [])
        is_valid = bool(data) and all(k in data for k in required)

        if is_valid:
            updated.append({**task, "valid": True})
        elif task["attempts"] < 2:
                                                     
            logger.debug(
                f"[validate] chunk {task['chunk_index']} invalid, "
                f"attempt {task['attempts']} — will retry"
            )
            updated.append({**task, "raw_json": None})
        else:
                                                                                
            logger.warning(
                f"[validate] chunk {task['chunk_index']} discarded "
                f"after {task['attempts']} attempts"
            )
            updated.append({**task, "valid": True, "raw_json": None})

    return {"tasks": updated}

def _needs_retry(state: ScenarioGenState) -> str:
                                                                    
    pending = [t for t in state.get("tasks", []) if not t["valid"]]
    return "retry" if pending else "ok"

async def node_save(state: ScenarioGenState) -> dict:
                                                          
    from sqlalchemy import update as sa_update
    from app.models import Document, Scenario
    from app.database import AsyncSessionLocal

    doc_id = state["doc_id"]
    tasks  = state.get("tasks", [])
    valid  = [t for t in tasks if t["valid"] and t.get("raw_json")]

    if not valid:
        logger.warning(f"[save] no valid scenarios for doc {doc_id}")
        await _mark_doc_ready(doc_id, 0)
        return {"saved_count": 0}

    try:
        async with AsyncSessionLocal() as db:
            db_scenarios = [
                Scenario(
                    document_id=doc_id,
                    type=t["scenario_type"],
                    title=t["raw_json"].get("title", "Тренировочное задание"),
                    description=(
                        t["raw_json"].get("description")
                        or t["raw_json"].get("question")
                    ),
                    difficulty=t["raw_json"].get("difficulty", 1),
                    scenario_json=t["raw_json"],
                )
                for t in valid
            ]
            db.add_all(db_scenarios)
            await db.flush()

            await db.execute(
                sa_update(Document)
                .where(Document.id == doc_id)
                .values(status="scenarios_ready", scenario_count=len(db_scenarios))
            )
            await db.commit()

        logger.info(f"[save] saved {len(db_scenarios)} scenarios for doc {doc_id}")
        return {"saved_count": len(db_scenarios)}

    except Exception as exc:
        logger.error(f"[save] {exc}")
        await _mark_doc_ready(doc_id, 0)
        return {"saved_count": 0, "errors": [f"save: {exc}"]}

async def _mark_doc_ready(doc_id: str, count: int):
    from sqlalchemy import update as sa_update
    from app.models import Document
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await db.execute(
            sa_update(Document)
            .where(Document.id == doc_id)
            .values(status="scenarios_ready", scenario_count=count)
        )
        await db.commit()

                                                                                 
                
                                                                                 

def _build_graph():
    g = StateGraph(ScenarioGenState)

    g.add_node("load_chunks", node_load_chunks)
    g.add_node("generate",    node_generate)
    g.add_node("validate",    node_validate)
    g.add_node("save",        node_save)

    g.add_edge(START,        "load_chunks")
    g.add_edge("load_chunks","generate")
    g.add_edge("generate",   "validate")

                                         
    g.add_conditional_edges(
        "validate", _needs_retry,
        {"retry": "generate", "ok": "save"}
    )

    g.add_edge("save", END)

    return g.compile()

_graph = None

def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph

                                                                                 
            
                                                                                 

async def generate_scenarios_for_document(doc_id: str, db=None) -> int:
\
\
\
\
\
       
    from sqlalchemy import select
    from app.models import Document
    from app.database import AsyncSessionLocal

                          
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = result.scalar_one_or_none()

    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    graph = _get_graph()

    initial: ScenarioGenState = {
        "doc_id":      doc_id,
        "doc_title":   doc.title,
        "tasks":       [],
        "saved_count": 0,
        "errors":      [],
    }

    final = await graph.ainvoke(initial)

    if final.get("errors"):
        logger.warning(
            f"[scenario_gen] completed with errors: {final['errors']}"
        )

    return final.get("saved_count", 0)
