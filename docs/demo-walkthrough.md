# Capstone demonstration

1. Open the landing page. Explain the waveform-to-insight concept and enter the workspace.
2. Choose the duplicate-charge sample and enable curated replay. Point out that replay uses prewritten results and no API request.
3. Enable simulated fallback, process the sample, and show the intake → summarization → scoring progression. Transcripts skip transcription.
4. Review summary, refund status, and next steps. The refund is issued, not claimed to have settled.
5. Open Quality score. Select an evidence chip and show keyboard focus moving to the cited transcript segment.
6. Open Activity and show the explicitly simulated primary timeout, retry, and fallback.
7. Export JSON and reload the page to demonstrate persisted history.
8. For the live audio demonstration, configure a server-side OpenAI key, restart, and upload a short authorized recording. Show transcription, unknown speaker labels, summary and supported scores. Do not call replay a live audio demonstration.
9. Try the incomplete and unattributed samples to show insufficient evidence, then poor service and embedded-instruction samples to show contrasting outcomes.

Live demonstration acceptance: one transcript and one audio call complete using OpenAI; inspect factual accuracy and evidence manually. If credentials are absent, record live verification as pending. This repository contains a walkthrough, not a recorded video.
