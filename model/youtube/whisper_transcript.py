import os

import whisper

class WhisperTranscript:
    def __init__(self, model: str = "base"):
        self.model = whisper.load_model(model)

    def transcribe(self, audio_file_path: str, delete_after: bool = True) -> str:
        text = self.model.transcribe(audio_file_path)["text"]
        # delete the audio file
        if delete_after:
            try:
                os.remove(audio_file_path)
            except FileNotFoundError:
                print(f"file {audio_file_path} not found")
        return text
