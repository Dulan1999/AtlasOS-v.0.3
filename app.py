import threading
import tkinter as tk
import os
import subprocess
import shutil
import webbrowser
from tkinter import messagebox, scrolledtext

from dotenv import load_dotenv

load_dotenv()

from atlas.config import (
    get_config,
    get_user_name,
    get_assistant_name,
    needs_first_run_setup,
    save_config,
)
from atlas.brain.chat import get_atlas_reply
from atlas.knowledge.knowledge_manager import list_facts


USER_NAME = "User"
ASSISTANT_NAME = "Atlas"

messages = []


def speak_text(text):
    from atlas.speech.speak import speak

    speak(text)


def find_ollama():
    ollama_path = shutil.which("ollama")

    if ollama_path:
        return ollama_path

    candidates = []
    local_app_data = os.getenv("LOCALAPPDATA")
    program_files = os.getenv("ProgramFiles")

    if local_app_data:
        candidates.append(os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe"))

    if program_files:
        candidates.append(os.path.join(program_files, "Ollama", "ollama.exe"))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return None


class FirstRunSetup:
    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        self.config = get_config()
        self.model_ready = False
        self.ollama_ready = False
        self.is_busy = False

        self.root.title("AtlasOS Setup")
        self.root.geometry("620x520")

        self.container = tk.Frame(root, padx=24, pady=20)
        self.container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            self.container,
            text="AtlasOS Setup",
            font=("Segoe UI", 22, "bold")
        ).pack(anchor="w")

        tk.Label(
            self.container,
            text="Personalize Atlas and prepare the local model.",
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(4, 18))

        self.user_name = tk.StringVar(value=self.config.get("user_name", "User"))
        self.assistant_name = tk.StringVar(value=self.config.get("assistant_name", "Atlas"))
        self.local_model = tk.StringVar(value=self.config.get("local_model", "qwen2.5:7b"))

        self.add_labeled_entry("Your name", self.user_name)
        self.add_labeled_entry("Assistant name", self.assistant_name)
        self.add_labeled_entry("Ollama model", self.local_model)

        self.status_box = scrolledtext.ScrolledText(
            self.container,
            height=8,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            state="disabled"
        )
        self.status_box.pack(fill=tk.BOTH, expand=True, pady=(18, 12))

        self.button_frame = tk.Frame(self.container)
        self.button_frame.pack(fill=tk.X)

        self.check_button = tk.Button(
            self.button_frame,
            text="Check Ollama",
            command=self.check_ollama
        )
        self.check_button.pack(side=tk.LEFT, padx=(0, 8))

        self.pull_button = tk.Button(
            self.button_frame,
            text="Pull Model",
            command=self.pull_model
        )
        self.pull_button.pack(side=tk.LEFT, padx=(0, 8))

        self.download_button = tk.Button(
            self.button_frame,
            text="Get Ollama",
            command=lambda: webbrowser.open("https://ollama.com/download")
        )
        self.download_button.pack(side=tk.LEFT, padx=(0, 8))

        self.finish_button = tk.Button(
            self.button_frame,
            text="Finish Setup",
            command=self.finish_setup
        )
        self.finish_button.pack(side=tk.RIGHT)

        self.write_status("Welcome. Start with Check Ollama.")

    def add_labeled_entry(self, label, variable):
        frame = tk.Frame(self.container)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(
            frame,
            text=label,
            width=16,
            anchor="w",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT)

        tk.Entry(
            frame,
            textvariable=variable,
            font=("Segoe UI", 11)
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def write_status(self, text):
        self.status_box.config(state="normal")
        self.status_box.insert(tk.END, f"{text}\n")
        self.status_box.config(state="disabled")
        self.status_box.see(tk.END)

    def set_busy(self, busy):
        self.is_busy = busy
        state = "disabled" if busy else "normal"

        self.check_button.config(state=state)
        self.pull_button.config(state=state)
        self.finish_button.config(state=state)

    def run_task(self, task):
        if self.is_busy:
            return

        def worker():
            self.root.after(0, lambda: self.set_busy(True))

            try:
                task()
            finally:
                self.root.after(0, lambda: self.set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def current_model(self):
        return self.local_model.get().strip() or "qwen2.5:7b"

    def check_ollama(self):
        self.run_task(self.check_ollama_task)

    def check_ollama_task(self):
        model = self.current_model()
        ollama_path = find_ollama()

        if not ollama_path:
            self.ollama_ready = False
            self.model_ready = False
            self.root.after(0, lambda: self.write_status("Ollama was not found. Install it, then run Check Ollama again."))
            return

        self.ollama_ready = True
        self.root.after(0, lambda: self.write_status("Ollama is installed."))

        try:
            result = subprocess.run(
                [ollama_path, "list"],
                capture_output=True,
                text=True,
                timeout=20
            )
        except subprocess.TimeoutExpired:
            self.model_ready = False
            self.root.after(0, lambda: self.write_status("Ollama did not respond in time. Make sure it is running."))
            return
        except OSError as error:
            self.model_ready = False
            self.root.after(0, lambda: self.write_status(f"Ollama check failed: {error}"))
            return

        if result.returncode != 0:
            self.model_ready = False
            self.root.after(0, lambda: self.write_status("Ollama is installed, but the model list could not be read. Make sure Ollama is running."))
            return

        self.model_ready = model.lower() in result.stdout.lower()

        if self.model_ready:
            self.root.after(0, lambda: self.write_status(f"Model ready: {model}"))
        else:
            self.root.after(0, lambda: self.write_status(f"Model not found yet: {model}"))

    def pull_model(self):
        self.run_task(self.pull_model_task)

    def pull_model_task(self):
        model = self.current_model()
        ollama_path = find_ollama()

        if not ollama_path:
            self.ollama_ready = False
            self.root.after(0, lambda: self.write_status("Ollama was not found. Use Get Ollama first."))
            return

        self.root.after(0, lambda: self.write_status(f"Pulling {model}. This can take a while."))

        try:
            result = subprocess.run(
                [ollama_path, "pull", model],
                capture_output=True,
                text=True
            )
        except OSError as error:
            self.model_ready = False
            self.root.after(0, lambda: self.write_status(f"Model pull failed: {error}"))
            return

        if result.returncode == 0:
            self.ollama_ready = True
            self.model_ready = True
            self.root.after(0, lambda: self.write_status(f"Model ready: {model}"))
            return

        self.model_ready = False
        self.root.after(0, lambda: self.write_status("Model pull failed. Check your internet connection and Ollama install."))

    def finish_setup(self):
        user_name = self.user_name.get().strip()
        assistant_name = self.assistant_name.get().strip()
        local_model = self.current_model()

        if not user_name:
            messagebox.showerror("AtlasOS Setup", "Enter your name before finishing setup.")
            return

        if not assistant_name:
            messagebox.showerror("AtlasOS Setup", "Enter an assistant name before finishing setup.")
            return

        if not self.model_ready:
            should_continue = messagebox.askyesno(
                "AtlasOS Setup",
                "The Ollama model is not marked ready yet. Save setup anyway?"
            )

            if not should_continue:
                return

        save_config({
            "user_name": user_name,
            "assistant_name": assistant_name,
            "local_model": local_model,
            "setup_complete": True
        })

        for child in self.root.winfo_children():
            child.destroy()

        self.on_complete()


class AtlasApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{ASSISTANT_NAME} OS")
        self.root.geometry("800x600")

        self.is_busy = False

        self.title_label = tk.Label(
            root,
            text=f"{ASSISTANT_NAME} OS",
            font=("Segoe UI", 20, "bold")
        )
        self.title_label.pack(pady=10)

        self.chat_box = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            state="disabled"
        )
        self.chat_box.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(padx=15, pady=10, fill=tk.X)

        self.user_input = tk.Entry(
            self.input_frame,
            font=("Segoe UI", 12)
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message
        )
        self.send_button.pack(side=tk.LEFT)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5)

        self.voice_button = tk.Button(
            self.button_frame,
            text="Voice",
            command=self.voice_message
        )
        self.voice_button.pack(side=tk.LEFT, padx=5)

        self.memory_button = tk.Button(
            self.button_frame,
            text="Memory",
            command=self.show_memory
        )
        self.memory_button.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            root,
            text="Ready.",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=5)

        self.add_message(ASSISTANT_NAME, f"{ASSISTANT_NAME} OS online. Hello, {USER_NAME}.")

    def add_message(self, speaker, text):
        self.chat_box.config(state="normal")
        self.chat_box.insert(tk.END, f"{speaker}: {text}\n\n")
        self.chat_box.config(state="disabled")
        self.chat_box.see(tk.END)

    def set_status(self, text):
        self.status_label.config(text=text)

    def set_busy(self, busy):
        self.is_busy = busy

        if busy:
            self.send_button.config(state="disabled")
            self.voice_button.config(state="disabled")
            self.memory_button.config(state="disabled")
        else:
            self.send_button.config(state="normal")
            self.voice_button.config(state="normal")
            self.memory_button.config(state="normal")

    def send_message(self, event=None):
        if self.is_busy:
            return

        user_text = self.user_input.get().strip()

        if not user_text:
            return

        self.user_input.delete(0, tk.END)
        self.add_message(USER_NAME, user_text)

        thread = threading.Thread(
            target=self.get_assistant_response,
            args=(user_text,),
            daemon=True
        )
        thread.start()

    def get_assistant_response(self, user_text):
        self.root.after(0, lambda: self.set_busy(True))
        self.root.after(0, lambda: self.set_status(f"{ASSISTANT_NAME} is thinking..."))

        try:
            messages.append({"role": "user", "content": user_text})

            assistant_reply = get_atlas_reply(messages, user_text)

            messages.append({"role": "assistant", "content": assistant_reply})

            self.root.after(0, lambda: self.add_message(ASSISTANT_NAME, assistant_reply))
            self.root.after(0, lambda: self.set_status("Speaking..."))

            speak_text(assistant_reply)

            self.root.after(0, lambda: self.set_status("Ready."))

        except Exception as e:
            error_message = f"Something went wrong: {e}"
            self.root.after(0, lambda: self.add_message("System", error_message))
            self.root.after(0, lambda: self.set_status("Error."))

        finally:
            self.root.after(0, lambda: self.set_busy(False))

    def voice_message(self):
        if self.is_busy:
            return

        thread = threading.Thread(
            target=self.listen_once,
            daemon=True
        )
        thread.start()

    def listen_once(self):
        self.root.after(0, lambda: self.set_busy(True))
        self.root.after(0, lambda: self.set_status("Listening for 5 seconds..."))

        try:
            from atlas.speech.listen import listen

            spoken_text = listen(5)

            if not spoken_text:
                self.root.after(0, lambda: self.add_message("System", "I didn't catch anything."))
                self.root.after(0, lambda: self.set_status("Ready."))
                return

            self.root.after(0, lambda: self.add_message(USER_NAME, spoken_text))
            self.get_assistant_response(spoken_text)

        except Exception as e:
            error_message = f"Voice error: {e}"
            self.root.after(0, lambda: self.add_message("System", error_message))
            self.root.after(0, lambda: self.set_status("Error."))

        finally:
            self.root.after(0, lambda: self.set_busy(False))

    def show_memory(self):
        facts = list_facts()

        if not facts:
            self.add_message(f"{ASSISTANT_NAME} Memory", "No saved facts yet.")
            return

        memory_text = "Here is what I actually have saved:\n"

        for i, fact in enumerate(facts, start=1):
            memory_text += f"{i}. [{fact['category']}] {fact['fact']}\n"

        self.add_message(f"{ASSISTANT_NAME} Memory", memory_text)


def start_main_app(root):
    global USER_NAME, ASSISTANT_NAME

    USER_NAME = get_user_name()
    ASSISTANT_NAME = get_assistant_name()

    AtlasApp(root)


if __name__ == "__main__":
    root = tk.Tk()

    if needs_first_run_setup():
        FirstRunSetup(root, lambda: start_main_app(root))
    else:
        start_main_app(root)

    root.mainloop()
