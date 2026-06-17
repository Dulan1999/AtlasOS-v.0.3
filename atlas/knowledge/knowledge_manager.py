import json
import os

from atlas.config import get_user_name
from atlas.paths import get_semantic_memory_path


KNOWLEDGE_FILE = get_semantic_memory_path()


def default_knowledge():
    return {
        "user": {
            "name": get_user_name(),
            "facts": []
        }
    }


def load_knowledge():
    if not os.path.exists(KNOWLEDGE_FILE):
        knowledge = default_knowledge()
        save_knowledge(knowledge)
        return knowledge

    with open(KNOWLEDGE_FILE, "r") as file:
        return json.load(file)


def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, "w") as file:
        json.dump(knowledge, file, indent=4)


def normalize_fact(fact):
    if isinstance(fact, str):
        return {
            "category": "general",
            "fact": fact,
            "confidence": 0.75
        }

    return {
        "category": fact.get("category", "general"),
        "fact": fact.get("fact", ""),
        "confidence": fact.get("confidence", 0.75)
    }


def fact_exists(existing_facts, new_fact):
    new_text = new_fact["fact"].strip().lower()

    for fact in existing_facts:
        normalized = normalize_fact(fact)
        existing_text = normalized["fact"].strip().lower()

        if existing_text == new_text:
            return True

    return False


def add_fact(fact):
    knowledge = load_knowledge()
    facts = knowledge["user"].get("facts", [])

    structured_fact = normalize_fact(fact)

    if structured_fact["fact"] and not fact_exists(facts, structured_fact):
        facts.append(structured_fact)

    knowledge["user"]["name"] = get_user_name()
    knowledge["user"]["facts"] = facts

    save_knowledge(knowledge)


def list_facts():
    knowledge = load_knowledge()
    facts = knowledge["user"].get("facts", [])

    return [normalize_fact(fact) for fact in facts]


def delete_fact(index):
    knowledge = load_knowledge()
    facts = knowledge["user"].get("facts", [])

    if index < 0 or index >= len(facts):
        return False

    del facts[index]

    knowledge["user"]["facts"] = facts
    save_knowledge(knowledge)

    return True

def wipe_semantic_memory():
    knowledge = default_knowledge()
    save_knowledge(knowledge)
    return True