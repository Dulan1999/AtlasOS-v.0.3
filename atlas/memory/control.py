from atlas.knowledge.knowledge_manager import wipe_semantic_memory
from atlas.memory.memory_manager import wipe_episodic_memory
from atlas.procedures.procedure_manager import wipe_procedural_memory


WIPE_WARNING = (
    "This will permanently wipe semantic, episodic, procedural, "
    "and current working memory."
)


def normalize_command(user_input):
    return " ".join(user_input.strip().split()).lower()


def is_wipe_request(user_input):
    return normalize_command(user_input) in {"/wipe", "/wipe_memory"}


def is_wipe_confirmation(user_input):
    return normalize_command(user_input) in {
        "/wipe confirm",
        "/wipe_memory confirm",
    }


def wipe_long_term_memory():
    wipe_semantic_memory()
    wipe_episodic_memory()
    wipe_procedural_memory()
    return True
