# Free LLM image analysis
This project supports a free local multimodal LLM through Ollama. Recommended setup for a school demo on a laptop/server:

1. Install Ollama from its official site.
2. Run `ollama pull llava`
3. Start Ollama (normally starts automatically).
4. Run `python server.py`
5. Open the app over HTTPS when using a remote mobile camera.

The backend sends the captured/uploaded image and user-entered vitals to the local model. No API key is stored in the browser.

For cloud deployment, a free host normally cannot run a large vision model reliably. Deploy this app separately and point `OLLAMA_URL` to a permitted private/local Ollama service, or use another provider's free tier subject to its current limits.

The model is instructed to provide educational, non-diagnostic observations only.
