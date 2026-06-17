import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from atlas.config import get_user_name
from atlas.paths import get_procedural_memory_path


PROCEDURE_FILE = get_procedural_memory_path()

DEFAULT_PROCEDURAL_MEMORY = {
    "version": 1,
    "users": {}
}


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def load_procedural_memory():
    if not PROCEDURE_FILE.exists():
        save_procedural_memory(DEFAULT_PROCEDURAL_MEMORY)
        return DEFAULT_PROCEDURAL_MEMORY

    try:
        with open(PROCEDURE_FILE, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        data = DEFAULT_PROCEDURAL_MEMORY

    if "version" not in data:
        data["version"] = 1

    if "users" not in data:
        data["users"] = {}

    return data


def save_procedural_memory(memory_data):
    with open(PROCEDURE_FILE, "w") as file:
        json.dump(memory_data, file, indent=4)


def get_user_bucket(memory_data=None):
    if memory_data is None:
        memory_data = load_procedural_memory()

    user_name = get_user_name()

    if user_name not in memory_data["users"]:
        memory_data["users"][user_name] = {
            "procedures": []
        }

    if "procedures" not in memory_data["users"][user_name]:
        memory_data["users"][user_name]["procedures"] = []

    return memory_data["users"][user_name]


def normalize_procedure(procedure):
    return {
        "id": procedure.get("id", str(uuid4())[:8]),
        "created_at": procedure.get("created_at", now_iso()),
        "updated_at": procedure.get("updated_at", procedure.get("created_at", now_iso())),
        "name": procedure.get("name", "Untitled procedure"),
        "purpose": procedure.get("purpose", ""),
        "steps": procedure.get("steps", []),
        "tags": procedure.get("tags", [])
    }


def add_procedure(name, purpose, steps, tags=None):
    if tags is None:
        tags = []

    memory_data = load_procedural_memory()
    user_bucket = get_user_bucket(memory_data)

    procedure = {
        "id": str(uuid4())[:8],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "name": name,
        "purpose": purpose,
        "steps": steps,
        "tags": tags
    }

    user_bucket["procedures"].append(procedure)
    save_procedural_memory(memory_data)

    return procedure


def list_procedures(limit=None):
    memory_data = load_procedural_memory()
    user_bucket = get_user_bucket(memory_data)

    procedures = [
        normalize_procedure(procedure)
        for procedure in user_bucket.get("procedures", [])
    ]

    procedures.sort(
        key=lambda procedure: procedure["updated_at"],
        reverse=True
    )

    if limit is not None:
        return procedures[:limit]

    return procedures


def delete_procedure(procedure_id):
    memory_data = load_procedural_memory()
    user_bucket = get_user_bucket(memory_data)

    procedures = user_bucket.get("procedures", [])
    original_count = len(procedures)

    user_bucket["procedures"] = [
        procedure for procedure in procedures
        if procedure.get("id") != procedure_id
    ]

    save_procedural_memory(memory_data)

    return len(user_bucket["procedures"]) < original_count


def search_procedures(query):
    query = query.lower().strip()

    if not query:
        return list_procedures()

    results = []

    for procedure in list_procedures():
        name = procedure["name"].lower()
        purpose = procedure["purpose"].lower()
        tags = " ".join(procedure["tags"]).lower()
        steps = " ".join(procedure["steps"]).lower()

        if query in name or query in purpose or query in tags or query in steps:
            results.append(procedure)

    return results


def format_recent_procedures(limit=5):
    procedures = list_procedures(limit=limit)

    if not procedures:
        return "No procedural memories."

    text = ""

    for procedure in procedures:
        text += f"- {procedure['name']}: {procedure['purpose']}\n"

        for i, step in enumerate(procedure["steps"], start=1):
            text += f"  {i}. {step}\n"

    return text.strip()

def wipe_procedural_memory():
    memory_data = load_procedural_memory()
    user_name = get_user_name()

    memory_data["users"][user_name] = {
        "procedures": []
    }

    save_procedural_memory(memory_data)
    return True