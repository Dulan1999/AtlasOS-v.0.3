import time
from dotenv import load_dotenv

load_dotenv()

from atlas.config import get_user_name, get_assistant_name
from atlas.brain.chat import get_atlas_reply
from atlas.knowledge.knowledge_manager import list_facts, delete_fact
from atlas.memory.control import (
    WIPE_WARNING,
    is_wipe_confirmation,
    is_wipe_request,
    wipe_long_term_memory,
)
from atlas.memory.memory_manager import list_episodes, add_episode, delete_episode
from atlas.procedures.procedure_manager import list_procedures, add_procedure, delete_procedure
from atlas.speech.listen import listen
from atlas.speech.speak import speak


messages = []

USER_NAME = get_user_name()
ASSISTANT_NAME = get_assistant_name()

print(f"{ASSISTANT_NAME} OS 2.6 Local online.")
print("Ollama local model enabled.")
print("Voice mode enabled.")
print("Memory Control Center enabled.")
print("Type 'quit' to shut down.")
print("Type '/help' to show commands.")
print(f"Type '/voice' to speak to {ASSISTANT_NAME}.")
print(f"Type '/talk' for continuous conversation with {ASSISTANT_NAME}.\n")


def handle_atlas_response(user_input):
    messages.append({"role": "user", "content": user_input})

    assistant_reply = get_atlas_reply(messages, user_input)

    messages.append({"role": "assistant", "content": assistant_reply})

    print(f"{ASSISTANT_NAME}: {assistant_reply}\n")
    speak(assistant_reply)

    return assistant_reply


def is_memory_question(user_input):
    text = user_input.lower()

    memory_phrases = [
        "what do you remember",
        "what do you know about me",
        "what memories do you have",
        "what have you saved about me",
        "what's my cat's name",
        "what is my cat's name",
        "what's my favorite",
        "what is my favorite"
    ]

    return any(phrase in text for phrase in memory_phrases)


def answer_from_memory():
    facts = list_facts()

    if not facts:
        response = "I don't have any saved semantic memories about you yet."
        print(f"{ASSISTANT_NAME}: {response}\n")
        speak(response)
        return

    response = "Here is what I actually have saved about you in semantic memory:\n"

    for fact in facts:
        response += f"- {fact['fact']}\n"

    print(f"{ASSISTANT_NAME}: {response}")
    speak(response)


def parse_tags(tag_text):
    if not tag_text:
        return []

    return [
        tag.strip()
        for tag in tag_text.split(",")
        if tag.strip()
    ]


def show_help():
    print(f"""
{ASSISTANT_NAME} Commands:

General:
  /help
  /voice
  /voice 8
  /talk
  quit

Semantic memory:
  /memory
  /semantic
  /forget 1

Episodic memory:
  /episodes
  /add_episode title | summary | importance | tag1,tag2
  /delete_episode episode_id

Procedural memory:
  /procedures
  /add_procedure name | purpose | step 1; step 2; step 3 | tag1,tag2
  /delete_procedure procedure_id

  Danger zone:
  /wipe
  /wipe CONFIRM
  /wipe_memory
  /wipe_memory CONFIRM

Examples:
  /add_episode Atlas UI milestone | The user created a working Tkinter interface for Atlas. | 0.8 | atlas,ui,milestone

  /add_procedure Start Atlas UI | How to launch the Atlas desktop app. | Open PowerShell in AtlasOS.; Activate the venv.; Run python app.py. | atlas,ui,startup
""")


def show_semantic_memory():
    facts = list_facts()

    if not facts:
        print(f"{ASSISTANT_NAME} Semantic Memory: No saved facts yet.\n")
        return

    print(f"\n{ASSISTANT_NAME} Semantic Memory:")

    for i, fact in enumerate(facts, start=1):
        print(f"{i}. [{fact['category']}] {fact['fact']}")

    print()


def show_episodes():
    episodes = list_episodes()

    if not episodes:
        print(f"{ASSISTANT_NAME} Episodic Memory: No episodes yet.\n")
        return

    print(f"\n{ASSISTANT_NAME} Episodic Memory:")

    for i, episode in enumerate(episodes, start=1):
        tags = ", ".join(episode["tags"]) if episode["tags"] else "none"

        print(f"{i}. {episode['title']}")
        print(f"   ID: {episode['id']}")
        print(f"   Created: {episode['created_at']}")
        print(f"   Summary: {episode['summary']}")
        print(f"   Importance: {episode['importance']}")
        print(f"   Tags: {tags}")
        print()

    print()


def show_procedures():
    procedures = list_procedures()

    if not procedures:
        print(f"{ASSISTANT_NAME} Procedural Memory: No procedures yet.\n")
        return

    print(f"\n{ASSISTANT_NAME} Procedural Memory:")

    for i, procedure in enumerate(procedures, start=1):
        tags = ", ".join(procedure["tags"]) if procedure["tags"] else "none"

        print(f"{i}. {procedure['name']}")
        print(f"   ID: {procedure['id']}")
        print(f"   Purpose: {procedure['purpose']}")
        print(f"   Tags: {tags}")
        print("   Steps:")

        for step_number, step in enumerate(procedure["steps"], start=1):
            print(f"     {step_number}. {step}")

        print()

    print()


def handle_add_episode(user_input):
    body = user_input[len("/add_episode"):].strip()

    if not body:
        print("Usage: /add_episode title | summary | importance | tag1,tag2\n")
        return

    parts = [part.strip() for part in body.split("|")]

    if len(parts) < 2:
        print("Usage: /add_episode title | summary | importance | tag1,tag2\n")
        return

    title = parts[0]
    summary = parts[1]

    importance = 0.5
    if len(parts) >= 3 and parts[2]:
        try:
            importance = float(parts[2])
        except ValueError:
            print("Importance must be a number like 0.5 or 0.9.\n")
            return

    tags = []
    if len(parts) >= 4:
        tags = parse_tags(parts[3])

    episode = add_episode(
        title=title,
        summary=summary,
        importance=importance,
        tags=tags
    )

    print(f"{ASSISTANT_NAME} Episodic Memory: Saved episode '{episode['title']}' with ID {episode['id']}.\n")


def handle_add_procedure(user_input):
    body = user_input[len("/add_procedure"):].strip()

    if not body:
        print("Usage: /add_procedure name | purpose | step 1; step 2; step 3 | tag1,tag2\n")
        return

    parts = [part.strip() for part in body.split("|")]

    if len(parts) < 3:
        print("Usage: /add_procedure name | purpose | step 1; step 2; step 3 | tag1,tag2\n")
        return

    name = parts[0]
    purpose = parts[1]
    steps = [
        step.strip()
        for step in parts[2].split(";")
        if step.strip()
    ]

    if not steps:
        print("Procedure needs at least one step.\n")
        return

    tags = []
    if len(parts) >= 4:
        tags = parse_tags(parts[3])

    procedure = add_procedure(
        name=name,
        purpose=purpose,
        steps=steps,
        tags=tags
    )

    print(f"{ASSISTANT_NAME} Procedural Memory: Saved procedure '{procedure['name']}' with ID {procedure['id']}.\n")

def wipe_all_memory():
    wipe_long_term_memory()
    messages.clear()

    print(f"{ASSISTANT_NAME} Memory: All memory has been wiped.\n")
    speak("All memory has been wiped.")

while True:
    user_input = input(f"{USER_NAME}: ")

    if user_input.lower() in ["quit", "exit", "shutdown"]:
        print(f"{ASSISTANT_NAME}: Shutting down. Later, {USER_NAME}.")
        speak(f"Shutting down. Later, {USER_NAME}.")
        break

    if user_input.lower() == "/help":
        show_help()
        continue

    if user_input.lower() in ["/memory", "/semantic"]:
        show_semantic_memory()
        continue

    if user_input.lower().startswith("/forget "):
        try:
            number = int(user_input.split(" ")[1])
            success = delete_fact(number - 1)

            if success:
                print(f"{ASSISTANT_NAME} Semantic Memory: Deleted fact #{number}.\n")
            else:
                print(f"{ASSISTANT_NAME} Semantic Memory: That fact number does not exist.\n")

        except ValueError:
            print(f"{ASSISTANT_NAME} Semantic Memory: Use /forget followed by a number, like /forget 2.\n")

        continue

    if user_input.lower() == "/episodes":
        show_episodes()
        continue

    if user_input.lower().startswith("/add_episode"):
        handle_add_episode(user_input)
        continue

    if user_input.lower().startswith("/delete_episode "):
        try:
            episode_id = user_input.split(maxsplit=1)[1].strip()
            success = delete_episode(episode_id)

            if success:
                print(f"{ASSISTANT_NAME} Episodic Memory: Deleted episode {episode_id}.\n")
            else:
                print(f"{ASSISTANT_NAME} Episodic Memory: No episode found with ID {episode_id}.\n")

        except IndexError:
            print("Usage: /delete_episode episode_id\n")

        continue

    if user_input.lower() == "/procedures":
        show_procedures()
        continue

    if user_input.lower().startswith("/add_procedure"):
        handle_add_procedure(user_input)
        continue

    if user_input.lower().startswith("/delete_procedure "):
        try:
            procedure_id = user_input.split(maxsplit=1)[1].strip()
            success = delete_procedure(procedure_id)

            if success:
                print(f"{ASSISTANT_NAME} Procedural Memory: Deleted procedure {procedure_id}.\n")
            else:
                print(f"{ASSISTANT_NAME} Procedural Memory: No procedure found with ID {procedure_id}.\n")

        except IndexError:
            print("Usage: /delete_procedure procedure_id\n")

        continue

    if is_wipe_request(user_input):
        print(f"{ASSISTANT_NAME} Memory: {WIPE_WARNING}")
        print("Type /wipe CONFIRM to continue.\n")
        continue

    if is_wipe_confirmation(user_input):
        wipe_all_memory()
        continue
    
    if user_input.lower().startswith("/voice"):
        parts = user_input.split()

        seconds = 5
        if len(parts) > 1:
            try:
                seconds = int(parts[1])
            except ValueError:
                print(f"{ASSISTANT_NAME} Voice: Use /voice or /voice 8.\n")
                continue

        spoken_text = listen(seconds)

        if not spoken_text:
            print(f"{ASSISTANT_NAME} Voice: I didn't catch anything.\n")
            continue

        print(f"{USER_NAME} said: {spoken_text}\n")

        if is_memory_question(spoken_text):
            answer_from_memory()
            continue

        handle_atlas_response(spoken_text)
        continue

    if user_input.lower().startswith("/talk"):
        print(f"{ASSISTANT_NAME} Voice: Continuous conversation mode started.")
        speak("Continuous conversation mode started.")

        while True:
            spoken_text = listen(5)

            if not spoken_text:
                print(f"{ASSISTANT_NAME} Voice: I didn't catch anything.\n")
                continue

            print(f"{USER_NAME} said: {spoken_text}\n")

            lower_spoken = spoken_text.lower()

            if (
                "stop talking" in lower_spoken
                or "exit voice mode" in lower_spoken
                or "quit voice mode" in lower_spoken
            ):
                print(f"{ASSISTANT_NAME} Voice: Exiting continuous conversation mode.\n")
                speak("Exiting continuous conversation mode.")
                break

            if is_memory_question(spoken_text):
                answer_from_memory()
                time.sleep(0.5)
                continue

            handle_atlas_response(spoken_text)
            time.sleep(0.5)

        continue

    if is_memory_question(user_input):
        answer_from_memory()
        continue

    handle_atlas_response(user_input)
