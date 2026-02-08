import os, json, ollama
from rich import print

# Private global DEBUG flag inherited from OPTIONS.json
_options_path = os.path.join(os.path.dirname(__file__), "OPTIONS.json")
DEBUG = False
options = {}
try:
    with open(_options_path, "r") as _f:
        options = json.load(_f)
    DEBUG = options.get("DEBUG", False)
except Exception:
    pass

class OllamaManager:
    # Previously used hardcoded "deepseek-r1:8b" as the model
    def __init__(self, system_prompt=None, chat_history_backup=None, model=options.get("MODEL_NAME", "gemma3")):
        self.model = model
        self.logging = True
        self.chat_history = []
        self.chat_history_backup = chat_history_backup
        if chat_history_backup and os.path.exists(chat_history_backup):
            with open(chat_history_backup, 'r') as file:
                self.chat_history = json.load(file)
        elif system_prompt:
            self.chat_history.append(system_prompt)

    def save_chat_to_backup(self):
        if self.chat_history_backup:
            with open(self.chat_history_backup, 'w') as file:
                json.dump(self.chat_history, file)

    def respond(self) -> str:
        try:
            response = ollama.chat(self.model,messages=self.chat_history)
            return response.message.content.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        except Exception as e:
            print("[OLLAMA EXCEPTION]", e)
            return None

    def chat(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return
        self.chat_history = [{"role": "user", "content": prompt}]
        answer = self.respond()
        if self.logging:
            print(f"[green]\n{answer}\n")
        return answer

    def chat_with_history(self, prompt=""):
        if prompt:
            self.chat_history.append({"role": "user", "content": prompt})
        # Ensure last message is user
        elif self.chat_history and self.chat_history[-1]["role"] != "user":
            self.chat_history.append({
                "role": "user",
                "content": "Continue."
            })
        answer = self.respond()
        self.chat_history.append({"role": "assistant", "content": answer})
        self.save_chat_to_backup()
        if self.logging:
            print(f"[green]\n{answer}\n")
        return answer