# What Version 3 fixes
- Correct OpenRouter multimodal request using a text part followed by `image_url`.
- Accepts base64 data URLs from camera capture and uploads.
- Handles non-JSON API responses safely.
- Handles model responses that contain JSON inside Markdown.
- Adds `/api/llm-status`.
- Shows detailed, non-secret provider errors instead of only “LLM unavailable”.
- Returns the actual model used when OpenRouter supplies it.
- Demo fallback is optional and defaults to OFF in `render.yaml`.
