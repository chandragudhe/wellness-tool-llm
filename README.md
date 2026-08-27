# Wellness Tool – HTTPS + Free LLM Ready

## Objective
Capture or upload an image, collect optional user-entered vitals, and request a multimodal LLM to produce educational wellness observations within the application's safety limits.

## Architecture
Browser (HTTPS camera/upload) -> Python backend -> free-tier multimodal LLM provider -> structured JSON results.

See `DEPLOY_HTTPS.md` for deployment steps.
