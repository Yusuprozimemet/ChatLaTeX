import requests
from typing import Optional
import tiktoken
import yaml

class Chatbot:
    def __init__(
        self,
        api_key: str,
        engine: str = "gpt-3.5-turbo",
        proxy: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.5,
        top_p: float = 1.0,
        timeout: Optional[float] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        truncate_limit: Optional[int] = None,
        reply_count: int = 1,
        system_prompt: str = "You are ChatGPT, a large language model trained by OpenAI. Respond conversationally",
    ) -> None:
        """
        Initialize Chatbot with API key
        """
        self.engine: str = engine
        self.api_key: str = api_key
        self.system_prompt: str = system_prompt
        self.max_tokens: int = max_tokens or (
            31000 if "gpt-4-32k" in engine else 7000 if "gpt-4" in engine else 15000 if "gpt-3.5-turbo-16k" in engine else 4000
        )
        self.truncate_limit: int = truncate_limit or (
            30500 if "gpt-4-32k" in engine else 6500 if "gpt-4" in engine else 14500 if "gpt-3.5-turbo-16k" in engine else 3500
        )
        self.frequency_penalty: float = frequency_penalty
        self.temperature: float = temperature
        self.top_p: float = top_p
        self.presence_penalty: float = presence_penalty
        self.reply_count: int = reply_count
        self.session = requests.Session()
        self.timeout: float = timeout
        self.proxy = proxy
        if proxy:
            self.session.proxies.update(
                {
                    "http": proxy,
                    "https": proxy,
                },
            )

        self.conversation: dict[str, list[dict]] = {
            "default": [],
        }

        if self.get_token_count("default") > self.max_tokens:
            self.max_tokens = 4000  # Set to a default value
            print("Warning: max_tokens was less than 1. It has been set to a default value of 4000.")

    @classmethod
    def from_config(cls, config_path: str):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return cls(**config)

    def get_max_tokens(self, convo_id: str) -> int:
        """
        Get max tokens
        """
        if convo_id not in self.conversation:
            raise KeyError(f"Conversation ID '{convo_id}' does not exist in self.conversation")

        return self.max_tokens - self.get_token_count(convo_id)

    def get_token_count(self, convo_id: str) -> int:
        """
        Get token count for a specific conversation
        """
        if convo_id not in self.conversation:
            raise KeyError(f"Conversation ID '{convo_id}' does not exist in self.conversation")

        num_tokens = sum(self.calculate_num_tokens([msg]) for msg in self.conversation[convo_id])
        return num_tokens

    def add_message(self, role: str, content: str, convo_id: str = "default") -> None:
        """
        Add message to the conversation
        """
        self.conversation.setdefault(convo_id, [])
        # Ensure message fits within the truncate_limit
        while len(content) > self.truncate_limit:
            self.conversation[convo_id].append({"role": role, "content": content[:self.truncate_limit]})
            content = content[self.truncate_limit:]
        self.conversation[convo_id].append({"role": role, "content": content})

    def send_request(self, convo_id: str = "default") -> str:
        """
        Send request to ChatGPT API
        """
        messages = self.conversation[convo_id]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.engine,
            "messages": messages,
            "max_tokens": self.get_max_tokens(convo_id),
            "top_p": self.top_p,
            "temperature": self.temperature,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "n": self.reply_count,
        }

        response = self.session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()

        if response.status_code == 200:
            result = response.json()
            return "\n\n".join([choice['message']['content'].strip() for choice in result['choices']])
        else:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

    def calculate_num_tokens(self, messages):
        """
        Calculate number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(self.engine)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")

        num_tokens = 0
        for message in messages:
            num_tokens += 5  # Initial token count for each message

            # Modify token calculation based on actual implementation
            if isinstance(message, dict):  # Ensure message is a dictionary
                for key, value in message.items():
                    if value:
                        num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += 5  # Additional token count if there's a name (role is always 1 token)

        num_tokens += 5  # Additional token for assistant reply
        return num_tokens
