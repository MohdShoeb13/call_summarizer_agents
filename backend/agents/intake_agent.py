import json
from pathlib import Path
from backend.models import Segment

MAX_BYTES = 24 * 1024 * 1024
MAX_TEXT = 100_000
AUDIO_TYPES = {".mp3", ".wav", ".m4a"}


def intake(filename: str, content: bytes) -> tuple[bool, list[Segment]]:
    suffix = Path(filename).suffix.lower()
    if suffix not in AUDIO_TYPES | {".txt", ".json"}:
        raise ValueError("Choose an MP3, WAV, M4A, TXT, or JSON file.")
    if not content or len(content) > MAX_BYTES:
        raise ValueError("File must be nonempty and smaller than 24 MiB.")
    if suffix in AUDIO_TYPES:
        valid = ((suffix == ".wav" and content[:4] == b"RIFF" and content[8:12] == b"WAVE")
                 or (suffix == ".m4a" and content[4:8] == b"ftyp")
                 or (suffix == ".mp3" and (content[:3] == b"ID3" or (len(content) > 1 and content[0] == 255 and content[1] & 224 == 224))))
        if not valid:
            raise ValueError("Audio content does not match the selected file format.")
        return True, []
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Transcript must use UTF-8 text.") from exc
    if len(text) > MAX_TEXT:
        raise ValueError("Transcript exceeds 100,000 characters. Split the call before uploading.")
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON transcript.") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON must contain a transcript string or segments array.")
        if isinstance(data.get("segments"), list):
            segments = []
            for row in data["segments"]:
                if not isinstance(row, dict) or not isinstance(row.get("text"), str) or not row["text"].strip():
                    raise ValueError("Each segment needs nonempty text.")
                speaker = row.get("speaker", "Unknown")
                if not isinstance(speaker, str):
                    raise ValueError("Speaker must be text.")
                segments.append(Segment(id=len(segments) + 1, speaker=speaker.strip() or "Unknown", text=row["text"].strip()))
            if not segments:
                raise ValueError("Transcript has no segments.")
            return False, segments
        text = data.get("transcript")
        if not isinstance(text, str):
            raise ValueError("JSON needs a transcript string or segments array.")
    return False, split_text(text)


def split_text(text: str) -> list[Segment]:
    if len(text) > MAX_TEXT:
        raise ValueError("Transcript exceeds 100,000 characters.")
    segments = []
    for line in text.splitlines():
        if not line.strip():
            continue
        speaker, sep, body = line.partition(":")
        known = sep and speaker.strip().lower() in {"agent", "customer", "caller", "supervisor"}
        segments.append(Segment(id=len(segments) + 1, speaker=speaker.strip().title() if known else "Unknown", text=(body if known else line).strip()))
    if not segments:
        raise ValueError("Transcript is empty.")
    return segments
