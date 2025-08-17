import io

from openai import OpenAI
from openai.types import AudioModel


class Transcriber:
    def __init__(self, model: AudioModel = "whisper-1") -> None:
        self.client = OpenAI()
        self.model = model

    def transcribe(self, audio: bytes, mime_type: str) -> str:
        assert mime_type == "audio/ogg", "Only OGG audio format is supported"
        buf = io.BytesIO(audio)
        buf.name = "voice_message.ogg"  # Set a name for the file
        buf.seek(0)  # Reset the buffer position
        transcription = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=buf,
        )
        return transcription.text
