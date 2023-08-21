import configparser
import json
from enum import Enum
from typing import Dict, List

import openai
import requests
import tiktoken

config = configparser.ConfigParser()
config.read("config.ini")

OPEN_AI_MODERATION_URL = "https://api.openai.com/v1/moderations"
openai.api_key = config.get("api", "OPEN_AI_KEY")

token_limits = {"gpt-3.5-turbo": 4096, "gpt-4": 8000}


def str_token_count(s: str) -> int:
    return len(tiktoken.get_encoding("cl100k_base").encode(s))


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class GptContact:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self._system_message = {"role": "system", "content": ""}
        self.conversation = []
        self.model = model
        self.model_token_limit = token_limits.get(self.model, "2048")

    @property
    def system_message(self) -> str:
        return self._system_message.get("content")

    @system_message.setter
    def system_message(self, message: str):
        self._system_message["content"] = message

    def set_system_message(self, message: str):
        self.system_message = message
        return self

    def add_user_message(self, message: str):
        self.conversation.append({"role": "user", "content": message})
        return self

    def add_message(self, message: str, role: Role):
        self.conversation.append({"role": role.value, "content": message})
        return self

    def get_completion(
        self,
        temperature: float = 1,
        max_response_tokens=1000,
        chat_history_token_limit=None,
        chat_history_recent_messages_limit=None,
    ):
        if not self.conversation:
            raise ValueError("No messages to send!")

        messages = []

        sys_message_tokens = (
            str_token_count(str(self._system_message)) if self.system_message else 0
        )
        chat_history_tokens_available = (
            self.model_token_limit - sys_message_tokens - max_response_tokens
        )

        if chat_history_token_limit:
            chat_history_tokens_available = min(
                chat_history_token_limit, chat_history_tokens_available
            )

        messages_appended = 0
        for message in reversed(self.conversation):
            message_token_count = str_token_count(str(message))
            if (
                chat_history_recent_messages_limit
                and messages_appended >= chat_history_recent_messages_limit
            ):
                break
            elif chat_history_tokens_available < message_token_count:
                break
            messages.insert(0, message)
            chat_history_tokens_available -= message_token_count
            messages_appended += 1

        if self.system_message:
            messages.insert(0, self._system_message)

        answer = GptContact.get_chat_completion_for_formatted_input(
            messages, self.model, temperature, max_response_tokens
        )
        self.conversation.append({"role": "assistant", "content": answer})
        return answer

    @staticmethod
    def get_moderation_info(content: str):
        response = requests.post(
            OPEN_AI_MODERATION_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + openai.api_key,
            },
            data=json.dumps({"input": content}),
        )
        return response.json()

    @staticmethod
    def get_chat_completion_for_formatted_input(
        messages: List[Dict],
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        max_tokens=1999,
    ):
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    @staticmethod
    def get_chat_completion(
        system_message: str,
        user_message: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        max_tokens=1999,
    ):
        inp = (
            ApiInputBuilder()
            .add_message(Role.SYSTEM, system_message)
            .add_message(Role.USER, user_message)
            .build()
        )
        return GptContact.get_chat_completion_for_formatted_input(
            inp, model, temperature, max_tokens
        )

    @staticmethod
    def get_insertion_completion(
        prefix_message: str,
        suffix_message: str = "",
        model: str = "gpt-3.5-turbo",
        max_tokens=20,
    ):
        return (
            openai.Completion.create(
                model=model,
                prompt=prefix_message,
                max_tokens=max_tokens,
                temperature=0.2,
                top_p=1,
                suffix=suffix_message,
            )
            .choices[0]
            .text
        )

    @staticmethod
    def get_edit_completion(
        message: str,
        instruction: str,
        model: str = "text-davinci-edit-001",
    ):
        return (
            openai.Edit.create(
                model=model,
                input=message,
                instruction=instruction,
                temperature=0.7,
                top_p=1,
            )
            .choices[0]
            .text
        )

    def list_models(self):
        return openai.Model.list()


class ApiInputBuilder:
    def __init__(self):
        self.messages = []

    def add_message(self, role: Role, content: str):
        self.messages.append({"role": role.value, "content": content})
        return self

    def build(self):
        return self.messages
