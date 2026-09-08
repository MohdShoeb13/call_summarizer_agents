import json
import time
from langchain_openai import ChatOpenAI
from openai import OpenAI, AuthenticationError, PermissionDeniedError, RateLimitError, APIConnectionError, InternalServerError
from backend.agents.quality_score_agent import validate_evidence


class ProviderFailure(Exception):
    pass


class OpenAIProvider:
    def __init__(self, config):
        self.config = config

    def generate(self, schema, prompt, transcript, stage, event):
        if not self.config.openai_api_key:
            raise ProviderFailure("Add OPENAI_API_KEY to .env and restart the server to analyze your calls.")
        payload = json.dumps([s.model_dump() for s in transcript], ensure_ascii=False)
        for model_index, model in enumerate([self.config.primary_model, self.config.fallback_model]):
            if model_index:
                event(stage, "Switching to fallback model", model)
            for attempt in range(2):
                try:
                    llm = ChatOpenAI(model=model, api_key=self.config.openai_api_key, timeout=60, max_retries=0)
                    chain = llm.with_structured_output(schema, method="function_calling", strict=True)
                    result = chain.invoke([("system", prompt), ("human", payload)])
                    if result is None:
                        raise ValueError("No structured response returned.")
                    result = validate_evidence(schema.model_validate(result), transcript)
                    event(stage, "Validated structured response", model)
                    return result
                except (AuthenticationError, PermissionDeniedError) as exc:
                    raise ProviderFailure("OpenAI rejected the credentials or model permissions. Check server configuration.") from exc
                except (RateLimitError, APIConnectionError, InternalServerError, ValueError) as exc:
                    event(stage, f"Attempt {attempt + 1} failed ({type(exc).__name__})", model)
                    if attempt == 0:
                        time.sleep(0.5)
                except Exception as exc:
                    event(stage, f"Model unavailable ({type(exc).__name__})", model)
                    break
        raise ProviderFailure(f"Both models failed during {stage}. Partial results were preserved. Try again later.")

    def transcribe(self, filename, content, event):
        if not self.config.openai_api_key:
            raise ProviderFailure("Add OPENAI_API_KEY to .env and restart the server.")
        client = OpenAI(api_key=self.config.openai_api_key, timeout=120, max_retries=0)
        for attempt in range(2):
            try:
                result = client.audio.transcriptions.create(model=self.config.transcription_model, file=(filename, content))
                if not result.text.strip():
                    raise ValueError("No speech detected.")
                event("transcription", "Audio transcribed; speaker identities are unknown", self.config.transcription_model)
                return result.text
            except (AuthenticationError, PermissionDeniedError) as exc:
                raise ProviderFailure("OpenAI rejected transcription access. Check server credentials.") from exc
            except (RateLimitError, APIConnectionError, InternalServerError):
                event("transcription", f"Transcription attempt {attempt + 1} failed", self.config.transcription_model)
                if attempt == 0:
                    time.sleep(0.5)
            except Exception as exc:
                raise ProviderFailure("Audio could not be transcribed. Check the recording or upload a transcript.") from exc
        raise ProviderFailure("Transcription unavailable after retry. Upload a transcript or try again later.")
