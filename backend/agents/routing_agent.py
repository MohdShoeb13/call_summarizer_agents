import time
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from backend.agents.intake_agent import intake
from backend.agents.transcription_agent import transcribe
from backend.agents.summarization_agent import summarize
from backend.agents.quality_score_agent import score
from backend.models import CallResult, Event
from backend.provider import ProviderFailure


class State(TypedDict):
    call: CallResult
    audio: bool


def process(call, filename, content, provider, store):
    start = time.monotonic()

    def event(stage, message, model=None):
        call.stage = stage
        call.events.append(Event(stage=stage, message=message, model=model))
        call.elapsed_seconds = round(time.monotonic() - start, 2)
        store.save(call)

    def intake_node(state):
        event("intake", "Validating input and extracting metadata")
        audio, segments = intake(filename, content)
        call.transcript = segments
        event("intake", "Audio accepted" if audio else "Transcript accepted; transcription skipped")
        return {"call": call, "audio": audio}

    def transcription_node(state):
        event("transcription", "Converting audio to text")
        call.transcript = transcribe(provider, filename, content, event)
        store.save(call)
        return {"call": call}

    def summary_node(state):
        event("summarization", "Extracting issue, outcome and next steps")
        call.summary = summarize(provider, call.transcript, event)
        store.save(call)
        return {"call": call}

    def quality_node(state):
        event("quality", "Evaluating four evidence-based dimensions")
        call.quality = score(provider, call.transcript, event)
        values = [d.score for d in call.quality.dimensions if d.score is not None]
        call.overall_score = round(sum(values) / len(values), 2) if values else None
        store.save(call)
        return {"call": call}

    graph = StateGraph(State)
    for name, node in [("intake", intake_node), ("transcription", transcription_node), ("summarization", summary_node), ("quality", quality_node)]:
        graph.add_node(name, node)
    graph.add_edge(START, "intake")
    graph.add_conditional_edges("intake", lambda state: "transcription" if state["audio"] else "summarization")
    graph.add_edge("transcription", "summarization")
    graph.add_edge("summarization", "quality")
    graph.add_edge("quality", END)
    call.status = "processing"
    try:
        graph.compile().invoke({"call": call, "audio": False})
        call.status = "completed"
        event("complete", "Analysis complete")
    except Exception as exc:
        call.status = "failed"
        call.error = str(exc) if isinstance(exc, (ProviderFailure, ValueError)) else "Processing failed. Try uploading the call again."
        event(call.stage, "Processing stopped; partial results retained")
    finally:
        call.elapsed_seconds = round(time.monotonic() - start, 2)
        store.save(call)
