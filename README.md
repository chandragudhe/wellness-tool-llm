# Wellness Tool – HTTPS Free LLM Version 3 (Classic UI Merge)

This package combines:

- The earlier WellnessFlow multi-step UI and auto-filled vital snapshot workflow.
- Version 3 secure OpenRouter multimodal backend.
- Camera capture and image upload.
- AI photo + user-entered vitals review.
- Render HTTPS deployment files.
- Detailed LLM error reporting and connection testing.

## Important workflow
1. Complete the earlier UI's Step 1 and Step 2.
2. In Step 3 choose **AI Photo**.
3. Capture or upload a photo.
4. Optionally click **Test AI connection**.
5. Click **AI photo + vitals review**.
6. When the review completes, continue to the vital snapshot.
7. The final snapshot retains the original auto-filled values and now includes the AI observations.

## Render environment variables
- `OPENROUTER_API_KEY` = your secret key
- `LLM_PROVIDER` = `openrouter`
- `OPENROUTER_MODEL` = `openrouter/free`
- `DEMO_FALLBACK` = `false`

Do not commit your API key to GitHub.

## Deployment
Build command:
`pip install -r requirements.txt`

Start command:
`python server.py`

The app listens on Render's `PORT` automatically.
