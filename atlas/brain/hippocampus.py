import json
import re
from ollama import chat

from atlas.config import get_user_name, get_assistant_name, get_local_model
from atlas.knowledge.knowledge_manager import add_fact
from atlas.memory.memory_manager import add_episode
from atlas.procedures.procedure_manager import add_procedure


def get_ollama_content(response):
    if isinstance(response, dict):
        return response["message"]["content"]

    return response.message.content


def parse_json(raw_text):
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    return None


def normalize_tags(tags):
    if tags is None:
        return []

    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]

    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]

    return []


def normalize_steps(steps):
    if steps is None:
        return []

    if isinstance(steps, list):
        return [str(step).strip() for step in steps if str(step).strip()]

    if isinstance(steps, str):
        return [step.strip() for step in steps.split(";") if step.strip()]

    return []


def clamp_importance(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.5

    return max(0.0, min(1.0, value))


def route_memory(user_input, assistant_reply=""):
    """
    Atlas's hippocampus.

    Decides whether a conversation moment should become:
    - semantic memory
    - episodic memory
    - procedural memory
    - no saved memory
    """

    user_name = get_user_name()
    assistant_name = get_assistant_name()
    local_model = get_local_model()

    prompt = f"""
You are {assistant_name}'s hippocampus: a memory routing system.

Your job is to decide whether this conversation moment should be saved to long-term memory.

User name:
{user_name}

User message:
"{user_input}"

Assistant reply:
"{assistant_reply}"

Choose exactly one memory type:

1. "semantic"
Stable facts about the user.
Examples:
- "{user_name} has a cat named Stubbz."
- "{user_name}'s favorite game is Subnautica."
- "{user_name} is studying psychology."

2. "episodic"
Events, milestones, project progress, or things that happened.
Examples:
- "{user_name} got Atlas voice mode working."
- "{user_name} created a UI for Atlas."
- "{user_name} decided to make Atlas usable by anyone."

3. "procedural"
Repeatable instructions, routines, how-to knowledge, setup steps, or workflows.
Examples:
- "How to start Atlas terminal mode."
- "How to launch the Atlas UI."
- "How to test voice input."

4. "none"
Small talk, temporary moods, random questions, jokes, or anything not worth saving.

Return ONLY valid JSON in this exact format:

{{
  "save": true or false,
  "memory_type": "semantic | episodic | procedural | none",

  "semantic": {{
    "category": "pets | preferences | goals | identity | relationships | projects | interests | routine | general",
    "fact": "",
    "confidence": 0.0
  }},

  "episodic": {{
    "title": "",
    "summary": "",
    "importance": 0.0,
    "tags": []
  }},

  "procedural": {{
    "name": "",
    "purpose": "",
    "steps": [],
    "tags": []
  }}
}}

Rules:
- Save only genuinely useful long-term information.
- Prefer "none" if the memory would be trivial.
- Semantic memory should only contain stable facts about {user_name}.
- Episodic memory should only contain events or milestones.
- Procedural memory should only contain repeatable instructions or workflows.
- Do not invent details.
- Use the user's name in semantic facts.
- Keep memories concise.
- Importance should be between 0 and 1.
"""

    response = chat(
        model=local_model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    raw = get_ollama_content(response)
    decision = parse_json(raw)

    if not decision:
        return None

    if decision.get("save") is not True:
        return decision

    memory_type = decision.get("memory_type", "none")

    if memory_type == "semantic":
        semantic = decision.get("semantic", {})

        fact = semantic.get("fact", "").strip()

        if not fact:
            return decision

        saved = {
            "category": semantic.get("category", "general"),
            "fact": fact,
            "confidence": clamp_importance(semantic.get("confidence", 0.75))
        }

        add_fact(saved)
        print(f"[hippocampus saved semantic] {saved['fact']}")

    elif memory_type == "episodic":
        episodic = decision.get("episodic", {})

        title = episodic.get("title", "").strip()
        summary = episodic.get("summary", "").strip()

        if not title or not summary:
            return decision

        episode = add_episode(
            title=title,
            summary=summary,
            importance=clamp_importance(episodic.get("importance", 0.5)),
            tags=normalize_tags(episodic.get("tags", []))
        )

        print(f"[hippocampus saved episode] {episode['title']}")

    elif memory_type == "procedural":
        procedural = decision.get("procedural", {})

        name = procedural.get("name", "").strip()
        purpose = procedural.get("purpose", "").strip()
        steps = normalize_steps(procedural.get("steps", []))

        if not name or not purpose or not steps:
            return decision

        procedure = add_procedure(
            name=name,
            purpose=purpose,
            steps=steps,
            tags=normalize_tags(procedural.get("tags", []))
        )

        print(f"[hippocampus saved procedure] {procedure['name']}")

    return decision