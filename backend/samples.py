import json
import time
from pathlib import Path
from backend.models import Summary, Quality, Dimension
from backend.agents.quality_score_agent import validate_evidence

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_transcripts"


def samples():
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(SAMPLE_DIR.glob("*.json"))]


class ReplayProvider:
    """Curated fixture replay for samples only. Never presented as live inference."""
    def __init__(self, sample, failover=False):
        self.sample = sample
        self.failover = failover

    def generate(self, schema, prompt, transcript, stage, event):
        time.sleep(0.35)
        if self.failover and stage == "summarization":
            event(stage, "SIMULATION: primary request timed out", "sample-primary")
            event(stage, "SIMULATION: retry timed out", "sample-primary")
            event(stage, "SIMULATION: switching to fallback fixture", "sample-fallback")
        if schema is Summary:
            result = Summary.model_validate(self.sample["expected"])
        else:
            dimensions = []
            agent_ids = [s.id for s in transcript if s.speaker == "Agent"]
            for name, value in zip(["empathy", "professionalism", "tone", "resolution"], self.sample["scores"]):
                ids = ([s.id for s in transcript][-2:] if name == "resolution" else agent_ids) if value is not None else []
                excerpt = " / ".join(s.text for s in transcript if s.id in ids)
                dimensions.append(Dimension(name=name, score=value, rationale=(f"Curated example: {excerpt}" if value is not None else "Insufficient evidence in this sample to evaluate agent behavior."), evidence_ids=ids))
            result = Quality(dimensions=dimensions)
        event(stage, "Loaded curated sample result (no AI request)", "sample-replay")
        return validate_evidence(result, transcript)
