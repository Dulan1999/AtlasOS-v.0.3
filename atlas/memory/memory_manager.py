import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from atlas.config import get_user_name
from atlas.paths import get_episodic_memory_path


EPISODIC_MEMORY_FILE = get_episodic_memory_path()

DEFAULT_EPISODIC_MEMORY = {
    "version": 1,
    "users": {}
}


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def load_episodic_memory():
    if not EPISODIC_MEMORY_FILE.exists():
        save_episodic_memory(DEFAULT_EPISODIC_MEMORY)
        return DEFAULT_EPISODIC_MEMORY

    try:
        with open(EPISODIC_MEMORY_FILE, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        data = DEFAULT_EPISODIC_MEMORY

    if "version" not in data:
        data["version"] = 1

    if "users" not in data:
        data["users"] = {}

    return data


def save_episodic_memory(memory_data):
    with open(EPISODIC_MEMORY_FILE, "w") as file:
        json.dump(memory_data, file, indent=4)


def get_user_bucket(memory_data=None):
    if memory_data is None:
        memory_data = load_episodic_memory()

    user_name = get_user_name()

    if user_name not in memory_data["users"]:
        memory_data["users"][user_name] = {
            "episodes": []
        }

    if "episodes" not in memory_data["users"][user_name]:
        memory_data["users"][user_name]["episodes"] = []

    return memory_data["users"][user_name]


def normalize_episode(episode):
    return {
        "id": episode.get("id", str(uuid4())[:8]),
        "created_at": episode.get("created_at", now_iso()),
        "title": episode.get("title", "Untitled episode"),
        "summary": episode.get("summary", ""),
        "importance": episode.get("importance", 0.5),
        "tags": episode.get("tags", [])
    }


def add_episode(title, summary, importance=0.5, tags=None):
    if tags is None:
        tags = []

    memory_data = load_episodic_memory()
    user_bucket = get_user_bucket(memory_data)

    episode = {
        "id": str(uuid4())[:8],
        "created_at": now_iso(),
        "title": title,
        "summary": summary,
        "importance": importance,
        "tags": tags
    }

    user_bucket["episodes"].append(episode)
    save_episodic_memory(memory_data)

    return episode


def list_episodes(limit=None):
    memory_data = load_episodic_memory()
    user_bucket = get_user_bucket(memory_data)

    episodes = [
        normalize_episode(episode)
        for episode in user_bucket.get("episodes", [])
    ]

    episodes.sort(
        key=lambda episode: episode["created_at"],
        reverse=True
    )

    if limit is not None:
        return episodes[:limit]

    return episodes


def delete_episode(episode_id):
    memory_data = load_episodic_memory()
    user_bucket = get_user_bucket(memory_data)

    episodes = user_bucket.get("episodes", [])
    original_count = len(episodes)

    user_bucket["episodes"] = [
        episode for episode in episodes
        if episode.get("id") != episode_id
    ]

    save_episodic_memory(memory_data)

    return len(user_bucket["episodes"]) < original_count


def search_episodes(query):
    query = query.lower().strip()

    if not query:
        return list_episodes()

    results = []

    for episode in list_episodes():
        title = episode["title"].lower()
        summary = episode["summary"].lower()
        tags = " ".join(episode["tags"]).lower()

        if query in title or query in summary or query in tags:
            results.append(episode)

    return results


def format_recent_episodes(limit=5):
    episodes = list_episodes(limit=limit)

    if not episodes:
        return "No recent episodic memories."

    text = ""

    for episode in episodes:
        text += (
            f"- {episode['title']}: "
            f"{episode['summary']} "
            f"(created {episode['created_at']})\n"
        )

    return text.strip()


# Backward-compatible aliases.
# These let old code still work if it calls add_memory/list_memories.
def add_memory(content, memory_type="event", importance=0.5, tags=None):
    return add_episode(
        title=memory_type,
        summary=content,
        importance=importance,
        tags=tags
    )


def list_memories(limit=None):
    return list_episodes(limit=limit)


def delete_memory(memory_id):
    return delete_episode(memory_id)


def search_memories(query):
    return search_episodes(query)


def format_recent_memories(limit=5):
    return format_recent_episodes(limit=limit)

def wipe_episodic_memory():
    memory_data = load_episodic_memory()
    user_name = get_user_name()

    memory_data["users"][user_name] = {
        "episodes": []
    }

    save_episodic_memory(memory_data)
    return True
