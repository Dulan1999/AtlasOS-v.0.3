import json
import re
from ollama import chat
from atlas.brain.hippocampus import route_memory
from atlas.brain.retrieval import build_relevant_memory_context
from atlas.config import get_user_name, get_assistant_name, get_local_model
from atlas.personality.identity import get_identity
from atlas.knowledge.knowledge_manager import add_fact

def get_ollama_content(response):
    if isinstance(response, dict):
        return response["message"]["content"]

    return response.message.content


def build_system_prompt(user_input):
    user_name = get_user_name()
    assistant_name = get_assistant_name()

    relevant_memory = build_relevant_memory_context(user_input)

    identity = get_identity(assistant_name, user_name)

    return identity + f"""

Memory architecture:

1. Working memory:
- The current conversation messages.
- Temporary.
- Used to follow the current conversation.

2. Semantic memory:
- Stable facts about {user_name}.
- These are stored in Known structured facts.
- Use these for questions like "what do you know about me?"

3. Episodic memory:
- Timestamped events, milestones, and things that happened.
- Use these for questions like "what have we worked on?" or "what happened recently?"

4. Procedural memory:
- Saved routines, instructions, and how-to knowledge.
- Use these for questions like "how do I start Atlas?" or "what procedure do you know?"

Relevant long-term memory for this message:
{relevant_memory}

Memory rules:
- Semantic facts are the ONLY stable personal facts you truly remember about {user_name}.
- Episodic memories are events, not identity facts.
- Procedural memories are instructions, not identity facts.
- If {user_name} asks what you remember about them personally, only list semantic facts.
- If {user_name} asks what you have worked on together, use episodic memory.
- If {user_name} asks how to do something, use procedural memory when relevant.
- Do not infer, guess, or embellish memories.
- It is okay to say "I don't have that saved yet."
- Do not mention confidence scores unless {user_name} asks about your memory system.
"""

def parse_memory_json(raw_text):
    """
    Tries to parse JSON even if the model adds extra text around it.
    """
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


def extract_memory(user_input):
    user_name = get_user_name()
    assistant_name = get_assistant_name()
    local_model = get_local_model()

    prompt = f"""
You are {assistant_name}'s memory extraction system.

Analyze {user_name}'s message and decide whether it contains a long-term fact worth remembering.

Message:
"{user_input}"

Return ONLY valid JSON in this exact format:

{{
  "remember": true or false,
  "category": "pets | preferences | goals | identity | relationships | projects | interests | routine | general",
  "fact": "A concise third-person fact about {user_name}.",
  "confidence": number between 0 and 1
}}

Rules:
- Remember stable personal facts, preferences, goals, pets, projects, studies, routines, relationships, and important interests.
- Do not remember greetings, small talk, jokes, temporary moods, or random questions.
- Write facts using the user's name, not "the user."
- If there is nothing worth remembering, return:
{{
  "remember": false,
  "category": "general",
  "fact": "",
  "confidence": 0
}}

Examples:
"My favorite food is spaghetti."
{{
  "remember": true,
  "category": "preferences",
  "fact": "{user_name}'s favorite food is spaghetti.",
  "confidence": 0.98
}}

"I have a cat named Stubbz."
{{
  "remember": true,
  "category": "pets",
  "fact": "{user_name} has a cat named Stubbz.",
  "confidence": 0.99
}}

"I love Subnautica."
{{
  "remember": true,
  "category": "interests",
  "fact": "{user_name} loves Subnautica.",
  "confidence": 0.95
}}

"yo what's up"
{{
  "remember": false,
  "category": "general",
  "fact": "",
  "confidence": 0
}}
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

    raw_memory = get_ollama_content(response)
    memory = parse_memory_json(raw_memory)

    if not memory:
        return

    if memory.get("remember") is True and memory.get("fact"):
        structured_fact = {
            "category": memory.get("category", "general"),
            "fact": memory.get("fact", ""),
            "confidence": memory.get("confidence", 0.75)
        }

        add_fact(structured_fact)
        print(f"[memory saved] {structured_fact['fact']}")


def get_atlas_reply(messages, user_input):
    local_model = get_local_model()
    system_prompt = build_system_prompt(user_input)

    full_messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ] + messages

    response = chat(
        model=local_model,
        messages=full_messages,
        options={
            "temperature": 0.7
        }
    )

    assistant_reply = get_ollama_content(response)

    route_memory(user_input, assistant_reply)

    return assistant_reply
