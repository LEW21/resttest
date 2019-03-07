import typing
import uuid
from dataclasses import dataclass

import requests

from resttest.conf import MAILCATCHER_URL


@dataclass
class Message:
    """Email message"""

    id: str
    sender: str
    recipients: typing.List[str]
    subject: str
    text: str
    size: int


class MailBox:
    """Email account"""

    def __init__(self):
        self.email = f'{uuid.uuid4().hex}@localhost'
        self.read_messages = set()

    @property
    def unread_messages(self) -> typing.Iterable[Message]:
        for message in requests.get(f'{MAILCATCHER_URL}messages').json():
            message_id = message['id']
            if f'<{self.email}>' in message['recipients']:
                if message_id in self.read_messages:
                    continue
                self.read_messages.add(message_id)
                message['text'] = requests.get(f'{MAILCATCHER_URL}messages/{message_id}.plain').text
                yield Message(**{k: message[k] for k in Message.__dataclass_fields__})
