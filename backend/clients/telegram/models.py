from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    language_code: str | None = None


class Chat(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    type: str  # e.g., "private", "group", "supergroup", "channel"


class Image(BaseModel):
    file_id: str
    file_unique_id: str
    file_size: int | None = None
    width: int | None = None
    height: int | None = None


class Voice(BaseModel):
    duration: int
    mime_type: str
    file_id: str
    file_unique_id: str
    file_size: int | None = None


class Document(BaseModel):
    file_name: str
    mime_type: str
    file_id: str
    file_unique_id: str
    file_size: int | None = None


class Message(BaseModel):
    message_id: int
    chat: Chat
    user: User = Field(alias="from")
    date: int


class TextMessage(Message):
    text: str


class ImageMessage(Message):
    images: list[Image] = Field(alias="photo")


class VoiceMessage(Message):
    voice: Voice


class DocumentMessage(Message):
    document: Document


class Update(BaseModel):
    update_id: int
    message: TextMessage | VoiceMessage | ImageMessage | DocumentMessage
    caption: str | None = None
