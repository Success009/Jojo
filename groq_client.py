import time
from groq import Groq
from logger import Logger

GROQ_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

class GroqRotator:
    def __init__(self, keys=None):
        self.keys = keys or GROQ_KEYS
        self.current_index = 0
        self.last_request_time = 0.0
        self.cooldown_seconds = 3.5  # Enforce 3-4 second cooldown as requested
        self.clients = [Groq(api_key=k) for k in self.keys]

    def _get_current_client(self):
        return self.clients[self.current_index], self.keys[self.current_index]

    def _rotate_key(self):
        old_idx = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        Logger.system(f"Rotating API Key: index {old_idx} -> {self.current_index}")

    def send_chat_completion(self, messages, model="llama-3.3-70b-versatile", temperature=0.7, max_tokens=1500):
        """
        Sends chat completion request to Groq with key rotation and rate limit backoff.
        """
        # Enforce global cooldown to prevent overwhelming keys
        elapsed = time.time() - self.last_request_time
        if elapsed < self.cooldown_seconds:
            wait_time = self.cooldown_seconds - elapsed
            Logger.system(f"Enforcing rate-limit cooldown. Sleeping for {wait_time:.2f}s...")
            time.sleep(wait_time)

        attempts = 0
        max_attempts = len(self.keys) * 2  # allow cycling through all keys twice

        while attempts < max_attempts:
            client, key_str = self._get_current_client()
            masked_key = f"{key_str[:12]}...{key_str[-8:]}"
            
            try:
                Logger.groq(f"Sending request with Key Index {self.current_index} ({masked_key})")
                self.last_request_time = time.time()
                
                response = client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Success
                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = response.usage.completion_tokens if response.usage else 0
                total_tokens = response.usage.total_tokens if response.usage else 0
                Logger.groq(f"Request succeeded. Tokens Used: {total_tokens} (Prompt: {prompt_tokens}, Completion: {completion_tokens})")
                
                return response.choices[0].message.content
                
            except Exception as e:
                err_msg = str(e)
                Logger.error(f"Error with Key Index {self.current_index}: {err_msg}")
                
                # Rotate key and retry
                self._rotate_key()
                attempts += 1
                # Add a brief pause before retry
                time.sleep(1.0)
                
        raise RuntimeError("All Groq API keys failed or rate limits exceeded globally.")
