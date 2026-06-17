import re

from atlas.knowledge.knowledge_manager import list_facts
from atlas.memory.memory_manager import list_episodes
from atlas.procedures.procedure_manager import list_procedures


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "can",
    "do",
    "does",
    "for",
    "from",
    "have",
    "how",
    "i",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "the",
    "to",
    "we",
    "what",
    "when",
    "where",
    "who",
    "why",
    "you",
    "your",
}

SEMANTIC_INTENT_WORDS = {
    "favorite",
    "favorites",
    "know",
    "likes",
    "love",
    "loves",
    "remember",
    "saved",
}

EPISODIC_INTENT_WORDS = {
    "built",
    "created",
    "did",
    "done",
    "happened",
    "milestone",
    "progress",
    "recent",
    "recently",
    "remember",
    "worked",
}

PROCEDURAL_INTENT_WORDS = {
    "how",
    "instructions",
    "launch",
    "procedure",
    "run",
    "setup",
    "start",
    "steps",
}


def tokenize(text):
    words = re.findall(r"[a-z0-9']+", text.lower())
    return [word for word in words if word not in STOP_WORDS and len(word) > 1]


def count_matches(query_tokens, text):
    text_tokens = set(tokenize(text))
    return sum(1 for token in query_tokens if token in text_tokens)


def rank_items(query, items, text_builder, limit=5):
    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scored_items = []

    for index, item in enumerate(items):
        text = text_builder(item)
        score = count_matches(query_tokens, text)

        if query.lower().strip() and query.lower().strip() in text.lower():
            score += 3

        if score > 0:
            scored_items.append((score, index, item))

    scored_items.sort(key=lambda scored: (-scored[0], scored[1]))
    return [item for _, _, item in scored_items[:limit]]


def has_intent(query, intent_words):
    query_words = set(re.findall(r"[a-z0-9']+", query.lower()))
    return bool(query_words & intent_words)


def relevant_facts(query, limit=6):
    return rank_items(
        query=query,
        items=list_facts(),
        text_builder=lambda fact: f"{fact['category']} {fact['fact']}",
        limit=limit,
    )


def relevant_episodes(query, limit=4):
    return rank_items(
        query=query,
        items=list_episodes(),
        text_builder=lambda episode: (
            f"{episode['title']} {episode['summary']} "
            f"{' '.join(episode['tags'])}"
        ),
        limit=limit,
    )


def relevant_procedures(query, limit=3):
    return rank_items(
        query=query,
        items=list_procedures(),
        text_builder=lambda procedure: (
            f"{procedure['name']} {procedure['purpose']} "
            f"{' '.join(procedure['steps'])} {' '.join(procedure['tags'])}"
        ),
        limit=limit,
    )


def format_facts(facts):
    if not facts:
        return "No directly relevant semantic memories."

    return "\n".join(
        f"- [{fact['category']}, confidence {fact['confidence']}] {fact['fact']}"
        for fact in facts
    )


def format_episodes(episodes):
    if not episodes:
        return "No directly relevant episodic memories."

    return "\n".join(
        (
            f"- {episode['title']}: {episode['summary']} "
            f"(created {episode['created_at']}, importance {episode['importance']})"
        )
        for episode in episodes
    )


def format_procedures(procedures):
    if not procedures:
        return "No directly relevant procedural memories."

    lines = []

    for procedure in procedures:
        lines.append(f"- {procedure['name']}: {procedure['purpose']}")

        for index, step in enumerate(procedure["steps"], start=1):
            lines.append(f"  {index}. {step}")

    return "\n".join(lines)


def build_relevant_memory_context(user_input):
    facts = relevant_facts(user_input)
    episodes = relevant_episodes(user_input)
    procedures = relevant_procedures(user_input)

    if has_intent(user_input, SEMANTIC_INTENT_WORDS) and not facts:
        facts = list_facts()[:6]

    if has_intent(user_input, EPISODIC_INTENT_WORDS) and not episodes:
        episodes = list_episodes(limit=4)

    if has_intent(user_input, PROCEDURAL_INTENT_WORDS) and not procedures:
        procedures = list_procedures(limit=3)

    return f"""
Relevant semantic memories:
{format_facts(facts)}

Relevant episodic memories:
{format_episodes(episodes)}

Relevant procedural memories:
{format_procedures(procedures)}
""".strip()
