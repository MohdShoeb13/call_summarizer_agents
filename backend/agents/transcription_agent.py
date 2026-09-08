from backend.agents.intake_agent import split_text


def transcribe(provider, filename, content, event):
    text = provider.transcribe(filename, content, event)
    # Whisper does not establish speaker identity. Preserve unknown attribution.
    segments = split_text(text)
    for segment in segments:
        segment.speaker = "Unknown"
    return segments
