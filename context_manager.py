import json
import os
from logger import Logger

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class ContextManager:
    def __init__(self, splash_pad_file=None, max_history_len=20):
        self.splash_pad_file = splash_pad_file or os.path.join(SCRIPT_DIR, "splash_pad.json")
        self.max_history_len = max_history_len
        self.history = [ ]  # Space inside empty brackets for JAVASCRIPT BRACKET BUG
        self.splash_pad = {
            "user_name": "User",
            "system_info": "Windows OS, AMD Ryzen 7000 series, 16GB RAM",
            "niche_facts": "Jojo is a fast, recursive, capable Windows AI assistant.",
            "current_session_notes": "Session initialized."
        }
        self.load_splash_pad()

    def load_splash_pad(self):
        if os.path.exists(self.splash_pad_file):
            try:
                with open(self.splash_pad_file, "r", encoding="utf-8") as f:
                    self.splash_pad = json.load(f)
                Logger.system("Loaded persistent Splash Pad data successfully.")
            except Exception as e:
                Logger.error(f"Failed to load Splash Pad: {e}")
        else:
            self.save_splash_pad()

    def save_splash_pad(self):
        try:
            with open(self.splash_pad_file, "w", encoding="utf-8") as f:
                json.dump(self.splash_pad, f, indent=4)
            Logger.system("Saved Splash Pad data successfully.")
        except Exception as e:
            Logger.error(f"Failed to save Splash Pad: {e}")

    def update_splash_pad_fact(self, key, value):
        self.splash_pad[key] = value
        Logger.system(f"Splash Pad updated: {key} = {value}")
        self.save_splash_pad()

    def get_splash_pad_text(self):
        lines = [ ]  # Space inside empty brackets
        lines.append("=== SPLASH PAD (FACTS BOARD) ===")
        for k, v in self.splash_pad.items():
            lines.append(f"- {k.replace('_', ' ').title()}: {v}")
        lines.append("================================")
        return "\n".join(lines)

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})
        # Slide context history window
        if len(self.history) > self.max_history_len:
            removed = self.history.pop(0)
            Logger.system(f"Context sliding: Removed oldest message from history: {removed['role']}")

    def get_messages_for_api(self, system_prompt):
        """
        Assembles system prompt, current Splash Pad facts, and conversation history
        into a clean payload list of messages.
        """
        # We merge system prompt with current Splash Pad facts
        full_system_prompt = (
            f"{system_prompt}\n\n"
            f"Here is your active Scratchpad / Splash Pad context which persists between turns:\n"
            f"{self.get_splash_pad_text()}\n"
        )
        
        payload = [{"role": "system", "content": full_system_prompt}]
        payload.extend(self.history)
        return payload

    def clear_history(self):
        self.history = [ ]  # Space inside empty brackets
        Logger.system("Conversation context history cleared.")
