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

import logging
from typing import TypedDict, Optional, Any, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import JsonOutputParser

from app.llm import llm
from app.prompts import EVALUATE_PROMPT, TREE_EXPLAIN_PROMPT

logger = logging.getLogger(__name__)

                                                                                 
             
                                                                                 

class CheckState(TypedDict):
                  
    scenario_type: str                                            
    scenario_data: dict                                             

                             
    selected_option_index: Optional[int]
    blocks_order:          Optional[list[str]]
    free_text:             Optional[str]

                                              
    correct:     bool
    score_delta: int
    explanation: Optional[str]
    consequence: Optional[str]
    visual_hint: Optional[str]
    detail:      Optional[Any]                                                       

                   
    check_type: str                                              

                             
    errors: Annotated[list[str], operator.add]

                                                                                 
       
                                                                                 

def node_route_check(state: CheckState) -> dict:
                                                         
    return {"check_type": state["scenario_type"]}

def node_check_cards(state: CheckState) -> dict:
                                                            
    data = state["scenario_data"]
    idx  = state.get("selected_option_index")

    if idx is None:
        return {"correct": False, "score_delta": 0,
                "errors": ["cards: selected_option_index missing"]}

    correct_idx  = data.get("correct_option_index", 0)
    is_correct   = idx == correct_idx
    explanations = data.get("explanations", {})
    consequences = data.get("consequences", {})
    visual_hints = data.get("visual_hint", {})

    if is_correct:
        explanation = "✓ Правильно! " + consequences.get(str(idx), "")
    else:
        explanation = explanations.get(str(idx), "Неверный вариант.")

    return {
        "correct":     is_correct,
        "score_delta": 10 if is_correct else 0,
        "explanation": explanation,
        "consequence": consequences.get(str(idx)),
        "visual_hint": visual_hints.get(str(idx)),
        "detail":      None,
    }

async def node_check_tree(state: CheckState) -> dict:
                                                                         
    data         = state["scenario_data"]
    user_order   = state.get("blocks_order", [])
    correct_order = data.get("correct_order", [])
    visual_hints  = data.get("visual_hint", {})

    if not user_order:
        return {"correct": False, "score_delta": 0,
                "errors": ["tree: blocks_order missing"]}

                                                                              
    sentinel = "__missing__"
    padded_user    = list(user_order)    + [sentinel] * max(0, len(correct_order) - len(user_order))
    padded_correct = list(correct_order) + [sentinel] * max(0, len(user_order) - len(correct_order))

    blocks_map = {b["id"]: b["text"] for b in data.get("blocks", [])}
    errors     = []

    for pos, (u, c) in enumerate(zip(padded_user, padded_correct)):
        if u != c:
            errors.append({
                "position":      pos,
                "user_block":    u,
                "correct_block": c,
                "explanation":   data.get("step_explanations", {}).get(u, ""),
            })

    is_correct = len(errors) == 0

                                                 
    if errors:
        first = errors[0]
        try:
            parser = JsonOutputParser()
            chain  = TREE_EXPLAIN_PROMPT | llm(0.2) | parser
            correct_texts = [blocks_map.get(bid, bid) for bid in correct_order]
            result: dict = await chain.ainvoke({
                "chunk_text":       "\n".join(
                    f"{i+1}. {t}" for i, t in enumerate(correct_texts)
                ),
                "correct_order_text": ", ".join(correct_texts),
                "wrong_step_text":    blocks_map.get(first["user_block"], first["user_block"]),
                "user_position":      first["position"] + 1,
                "correct_position":   (
                    correct_order.index(first["user_block"]) + 1
                    if first["user_block"] in correct_order else -1
                ),
            })
            errors[0]["llm_explanation"] = result.get("explanation", "")
            errors[0]["hint"]            = result.get("hint", "")
        except Exception as exc:
            logger.warning(f"[check_tree] LLM explain failed: {exc}")

    return {
        "correct":     is_correct,
        "score_delta": 10 if is_correct else max(0, 10 - len(errors) * 2),
        "explanation": "Алгоритм выполнен верно!" if is_correct else f"Ошибок: {len(errors)}",
        "visual_hint": visual_hints.get("success" if is_correct else "error"),
        "detail":      errors if not is_correct else None,
    }

async def node_check_free(state: CheckState) -> dict:
                                                       
    data   = state["scenario_data"]
    answer = state.get("free_text", "").strip()

    if not answer:
        return {"correct": False, "score_delta": 0,
                "errors": ["free_text: no answer provided"]}

    criteria      = data.get("criteria", {})
    criteria_text = "\n".join(f"- {k}: {v}" for k, v in criteria.items())

    try:
        parser = JsonOutputParser()
        chain  = EVALUATE_PROMPT | llm(0.2) | parser
        result: dict = await chain.ainvoke({
            "question":      data.get("question", ""),
            "ideal_answer":  data.get("ideal_answer", ""),
            "criteria_text": criteria_text,
            "user_answer":   answer,
        })

                                                                      
        raw_score  = result.get("total_score") or 0
        score      = max(0, min(3, int(raw_score)))                 
        is_correct = score >= 2

        return {
            "correct":     is_correct,
            "score_delta": score * 3,                      
            "explanation": result.get("overall_feedback"),
            "detail":      result,
        }
    except Exception as exc:
        logger.error(f"[check_free] LLM evaluation error: {exc}")
        return {
            "correct": False, "score_delta": 0,
            "errors":  [f"free_text evaluation failed: {exc}"]
        }

def node_format_result(state: CheckState) -> dict:
                                                                         
    return {
        "correct":     state.get("correct", False),
        "score_delta": state.get("score_delta", 0),
        "explanation": state.get("explanation"),
        "consequence": state.get("consequence"),
        "visual_hint": state.get("visual_hint"),
        "detail":      state.get("detail"),
    }

                                                                                 
         
                                                                                 

def _route_by_type(state: CheckState) -> str:
    return state.get("check_type", "cards")

                                                                                 
                
                                                                                 

def _build_graph():
    g = StateGraph(CheckState)

    g.add_node("route_check",    node_route_check)
    g.add_node("check_cards",    node_check_cards)
    g.add_node("check_tree",     node_check_tree)
    g.add_node("check_free",     node_check_free)
    g.add_node("format_result",  node_format_result)

    g.add_edge(START, "route_check")

    g.add_conditional_edges(
        "route_check", _route_by_type,
        {
            "cards":     "check_cards",
            "tree":      "check_tree",
            "free_text": "check_free",
        }
    )

    for check_node in ["check_cards", "check_tree", "check_free"]:
        g.add_edge(check_node, "format_result")

    g.add_edge("format_result", END)

    return g.compile()

_graph = None

def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph

                                                                                 
            
                                                                                 

async def check_answer(
    scenario_type: str,
    scenario_data: dict,
    selected_option_index: int | None = None,
    blocks_order: list[str] | None = None,
    free_text: str | None = None,
) -> dict:
\
\
\
\
       
    graph = _get_graph()

    initial: CheckState = {
        "scenario_type":         scenario_type,
        "scenario_data":         scenario_data,
        "selected_option_index": selected_option_index,
        "blocks_order":          blocks_order,
        "free_text":             free_text,
        "check_type":            "",
        "correct":               False,
        "score_delta":           0,
        "explanation":           None,
        "consequence":           None,
        "visual_hint":           None,
        "detail":                None,
        "errors":                [],
    }

    final = await graph.ainvoke(initial)

    if final.get("errors"):
        logger.warning(f"[training_engine] errors: {final['errors']}")

    return {
        "correct":     final["correct"],
        "score_delta": final["score_delta"],
        "explanation": final.get("explanation"),
        "consequence": final.get("consequence"),
        "visual_hint": final.get("visual_hint"),
        "detail":      final.get("detail"),
    }
