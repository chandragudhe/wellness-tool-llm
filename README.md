# Wellness Tool – HTTPS Free LLM Version 3

## Core flow
Capture/upload image → secure Python backend → OpenRouter vision-capable free router → educational wellness observation + user-entered vitals summary.

## Deploy to Render
1. Upload the **contents** of this folder to a GitHub repository.
2. Create a Render **Web Service** from the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python server.py`
5. Add Render environment variable:
   - `OPENROUTER_API_KEY` = your key (keep secret)
   - `LLM_PROVIDER` = `openrouter`
   - `OPENROUTER_MODEL` = `openrouter/free`
   - `DEMO_FALLBACK` = `false` for real AI-only testing
6. Deploy and open the generated HTTPS URL.
7. Click **Test LLM Connection** before testing image analysis.

## Diagnostics
- `/api/llm-status` checks whether the OpenRouter API is reachable without consuming a chat completion.
- AI failures return the provider HTTP status/message to the browser and Render logs.
- The backend logs the full non-secret error context.

## Important
Free-model availability and quotas can change. `openrouter/free` is a router, so the model actually used may differ from the requested router name.

The tool is educational and non-diagnostic. Do not use it to make medical decisions.
