"""
LangChain prompt templates for scenario generation.
Each prompt is a ChatPromptTemplate (system + human) used inside the
Scenario Generation Graph nodes.
"""

from langchain_core.prompts import ChatPromptTemplate

                                                                                 

CARDS_SYSTEM = (
    "Ты — опытный методист медицинского симулятора. "
    "Создаёшь интерактивные тренировочные задания.\n"
    "ПРАВИЛА:\n"
    "1. Используй ТОЛЬКО информацию из фрагмента регламента.\n"
    "2. Ситуация должна быть реалистичной и конкретной.\n"
    "3. Неправильные варианты — типичные ошибки практики.\n"
    "4. Объяснения ошибок ссылаются на пункт регламента.\n"
    "5. Отвечай СТРОГО в JSON без Markdown-обёрток.\n"
    "6. Текст — на русском языке."
)

CARDS_HUMAN = """\
Фрагмент регламента:
---
{chunk_text}
---
Раздел: {section_title}
Документ: {document_title}

Создай задание «выбор одного из трёх вариантов».
Один вариант верный, два — типичные ошибки практики.

JSON:
{{
  "title": "Краткое название (до 80 символов)",
  "description": "Подробное описание ситуации (3-5 предложений)",
  "options": ["Вариант A", "Вариант B", "Вариант C"],
  "correct_option_index": <0|1|2>,
  "explanations": {{
    "<индекс неверного>": "Объяснение + ссылка на регламент"
  }},
  "consequences": {{
    "0": "Последствие A", "1": "Последствие B", "2": "Последствие C"
  }},
  "visual_hint": {{
    "0": "<visual_id>", "1": "<visual_id>", "2": "<visual_id>"
  }},
  "difficulty": <1|2|3>
}}
Допустимые visual_id: patient_calm, patient_distressed, patient_critical,
doctor_approve, doctor_concern, error_medical, emergency_red, success_green,
form_ok, form_error, time_critical."""

CARDS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CARDS_SYSTEM),
    ("human",  CARDS_HUMAN),
])

                                                                                 

TREE_SYSTEM = (
    "Ты — методист медицинского симулятора. "
    "Создаёшь задания на расстановку алгоритма в правильном порядке.\n"
    "Используй ТОЛЬКО текст регламента. "
    "Отвечай СТРОГО в JSON без Markdown, на русском языке."
)

TREE_HUMAN = """\
Фрагмент регламента:
---
{chunk_text}
---
Раздел: {section_title}

Выдели последовательный алгоритм (4-6 шагов). Каждый шаг — самодостаточный.
В поле blocks — шаги в СЛУЧАЙНОМ порядке (не совпадает с correct_order).

JSON:
{{
  "title": "Название алгоритма",
  "description": "Контекст задания для врача",
  "blocks": [
    {{"id": "b1", "text": "..."}},
    {{"id": "b2", "text": "..."}},
    {{"id": "b3", "text": "..."}},
    {{"id": "b4", "text": "..."}}
  ],
  "correct_order": ["b2", "b4", "b1", "b3"],
  "step_explanations": {{
    "b1": "Почему этот шаг здесь",
    "b2": "Почему первый",
    "b3": "Почему последний",
    "b4": "Почему здесь"
  }},
  "difficulty": <1|2|3>
}}"""

TREE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TREE_SYSTEM),
    ("human",  TREE_HUMAN),
])

                                                                                 

FREE_TEXT_SYSTEM = (
    "Ты — методист медицинского образования. "
    "Создаёшь открытые вопросы для проверки понимания регламентов.\n"
    "Используй только текст регламента. "
    "Отвечай СТРОГО в JSON, на русском языке."
)

FREE_TEXT_HUMAN = """\
Фрагмент регламента:
---
{chunk_text}
---

Создай открытый вопрос, требующий развёрнутого ответа (не механического воспроизведения).

JSON:
{{
  "title": "Название задания",
  "question": "Полный текст вопроса",
  "ideal_answer": "Эталонный ответ",
  "criteria": {{
    "criterion_1": "Критерий 1 (1 балл)",
    "criterion_2": "Критерий 2 (1 балл)",
    "criterion_3": "Критерий 3 (1 балл)"
  }},
  "difficulty": <1|2|3>
}}"""

FREE_TEXT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", FREE_TEXT_SYSTEM),
    ("human",  FREE_TEXT_HUMAN),
])

                                                                                

EVALUATE_SYSTEM = (
    "Ты — строгий, но справедливый экзаменатор медицинских знаний. "
    "Оцениваешь ответы строго по критериям. "
    "Не засчитывай балл если критерий выполнен лишь частично. "
    "Отвечай СТРОГО в JSON без Markdown, на русском языке."
)

EVALUATE_HUMAN = """\
Вопрос: {question}

Эталонный ответ: {ideal_answer}

Критерии оценки:
{criteria_text}

Ответ обучаемого: {user_answer}

JSON:
{{
  "total_score": <0|1|2|3>,
  "criteria_results": {{
    "criterion_1": {{"passed": true, "comment": "..."}},
    "criterion_2": {{"passed": false, "comment": "..."}},
    "criterion_3": {{"passed": true, "comment": "..."}}
  }},
  "overall_feedback": "Общий комментарий (2-3 предложения)",
  "missing_points": "Что нужно было упомянуть (если балл неполный)"
}}"""

EVALUATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", EVALUATE_SYSTEM),
    ("human",  EVALUATE_HUMAN),
])

                                                                                

TREE_EXPLAIN_SYSTEM = (
    "Ты — методист, объясняющий ошибки в расстановке алгоритмов. "
    "Объясняй коротко, ссылайся на логику регламента. "
    "Отвечай СТРОГО в JSON, на русском языке."
)

TREE_EXPLAIN_HUMAN = """\
Алгоритм из регламента:
---
{chunk_text}
---

Правильный порядок: {correct_order_text}
Шаг расставлен неверно: {wrong_step_text}
Поставлен на позицию: {user_position}
Правильная позиция: {correct_position}

JSON:
{{
  "explanation": "Объяснение (2-3 предложения)",
  "hint": "Подсказка для запоминания"
}}"""

TREE_EXPLAIN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TREE_EXPLAIN_SYSTEM),
    ("human",  TREE_EXPLAIN_HUMAN),
])
