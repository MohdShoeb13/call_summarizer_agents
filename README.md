# Resonant — Call intelligence

A React workspace and Python multi-agent pipeline for turning support recordings and transcripts into evidence-linked summaries, quality scores, and next steps. Built from the AI Call Center Assistant capstone, with React replacing Streamlit as requested.

## Run on Windows

Requires Node.js 22+, npm, and [uv](https://docs.astral.sh/uv/). Run from this directory:

```powershell
uv sync --frozen
Copy-Item .env.example .env
```

Edit `.env` to add your OpenAI API key. Never place it in the frontend or a `VITE_` variable. A key is unnecessary for the 12 curated sample replays. Do not overwrite an existing `.env` when updating.

```powershell
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8018
```

Open **http://127.0.0.1:8018**. The Python server serves the production React build. Port 8018 avoids another local service on port 8000. `start.cmd` performs the install/build/start sequence without changing an existing `.env`.

For development, run the backend command above in one terminal and `npm.cmd run dev` inside `frontend` in another. Open http://127.0.0.1:5173; Vite proxies `/api` to Python.

## Try it without an API key

Open the workspace → **Explore a sample** → **The duplicate charge** → keep **Replay curated example** checked → **Replay sample**. These are explicitly labeled, prewritten fixtures, not AI-generated results. Enable **Demonstrate model fallback** to replay a simulated timeout and recovery in Activity. Uploaded user files cannot use replay mode.

For real processing, add `OPENAI_API_KEY`, restart the backend, then upload a recording/transcript or uncheck replay on a sample. API calls incur usage charges. Live provider validation requires your account's model access.

## Inputs and outputs

- Audio: MP3, WAV, M4A; nonempty, at most 24 MiB. File signatures are checked; the transcription service validates the recording. Longer files must be split before upload.
- Text: UTF-8 TXT or JSON, at most 100,000 characters. Recognized TXT labels: Agent, Customer, Caller, Supervisor. All other speaker identities remain Unknown.
- JSON: `{"transcript":"Agent: Hello\nCustomer: I need help"}` or `{"segments":[{"speaker":"Agent","text":"Hello"},{"text":"Unattributed speech"}]}`. Segment IDs are normalized to start at 1.
- Outputs: transcript segments, issue, key points, resolution status/details, explicit action items, tags, evidence IDs, four quality dimensions, aggregate score, routing events, elapsed time, and status/error.
- Click an evidence chip to focus its transcript segment. Export JSON includes both results and execution metadata.

## Architecture

`frontend/`: React, TypeScript, Vite, Tailwind, Motion, Radix Tabs, and a shadcn-style Button primitive. Original dark navy/cyan visual design, animated waveform, responsive workspace, and reduced-motion support. Scrolltide informed the cinematic composition; 21st.dev informed component patterns. No premium assets or template source were copied.

`backend/agents/`: intake → optional transcription → summarization → quality. LangGraph owns conditional routing; each agent delegates only its focused responsibility. `backend/provider.py` owns bounded provider retries and fallback. Summarization and scoring use LangChain structured function calling validated by Pydantic.

`backend/store.py`: SQLite result history, with independent connections closed after transactions. Calls never implicitly contribute context to other calls. The backend starts a two-worker executor with eight queued slots; saturation returns HTTP 429. Use **one Uvicorn process**. Restart marks queued/processing calls interrupted; it does not silently rerun billable work.

API: `POST /api/calls` (multipart: one `file` or `sample_id`, optional `demo`, `simulate_failure`) returns HTTP 202 and a CallResult. `GET /api/calls`, `GET /api/calls/{id}`, `GET /api/calls/{id}/export`, `GET /api/samples`, and `GET /api/health` support the workspace. Poll active calls once per second. Interactive API docs: `/docs`.

Generate TypeScript API types after Pydantic/API changes: `npm.cmd run generate-types` in `frontend`, after `uv sync`. Generated types are committed with source for builds without a running server.

## Model policy and quality rubric

Defaults: `gpt-4o-mini` primary, `gpt-4o` fallback, `whisper-1` transcription. All are configurable in `.env`. Each generation stage makes at most two primary attempts and two fallback attempts. Transient errors and invalid structured/evidence responses trigger a retry; authentication/permission errors stop immediately. Transcription retries once on transient errors and otherwise offers transcript upload. Provider exceptions are reduced to safe user-facing messages, not raw response bodies.

Scores: 1 clearly poor, 2 weak, 3 adequate, 4 good, 5 excellent. Empathy = acknowledgment and understanding; professionalism = respect, clarity, ownership; tone = word choice only; resolution = supported outcome and useful next steps. Unknown speaker identity can make agent behavior unscorable. Unscorable dimensions use null; the aggregate averages scored dimensions only. Prompts live beside the respective agents.

Transcript content is untrusted input, not instructions. Evidence IDs must exist, and every scored dimension must cite evidence. These checks ensure structural grounding, not a guarantee of semantic truth; human review remains necessary. Whisper does not provide speaker attribution here, and audio tone is not analyzed.

## Data and limitations

Call text/results remain in local `runtime/calls.sqlite3`; this database is not encrypted and must be protected as local user data. Raw audio is held in request/worker memory and a browser object URL, never persisted by application code. Playback is available during the active workspace session. No external tracing or transcript logging is enabled by default. `.env`, runtime data, dependencies, screenshots, and build artifacts are excluded from version control.

Local, single-user prototype: no public authentication, distributed workers, production tenancy, audio chunking, or automatic call-context retrieval. Bind to localhost. No public deployment is performed. The PDF's control-plane/MCP concepts are implemented as provider routing policy; this app does not claim to expose a Model Context Protocol server.

## Validation

```powershell
uv run pytest
cd frontend
npm.cmd test
npm.cmd run build
cd ..
```

Browser acceptance checks use Playwright with installed Microsoft Edge. Start the production app, then run `uv run python tests/browser_check.py`. Output screenshots and a synthetic JSON export go to `test-results/`. The browser checks exercise real replay endpoints and mock only the upload response path. Python tests inject providers to verify real pipeline routing, retry bounds, authentication failures, and partial results. No tests make paid API calls.

See `docs/demo-walkthrough.md` for a capstone demonstration script and `docs/design.md` for design decisions.
