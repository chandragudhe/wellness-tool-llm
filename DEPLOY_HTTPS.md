# HTTPS deployment (free-tier friendly)

## Recommended: Render + OpenRouter

1. Create a GitHub repository and upload all files in this folder.
2. Create a Render account and select **New > Blueprint** (or Web Service).
3. Connect the GitHub repository. Render reads `render.yaml`.
4. Add the secret environment variable `OPENROUTER_API_KEY` in the Render dashboard. Do not put the key in GitHub or `index.html`.
5. Deploy. Render provides an HTTPS URL.
6. Open the HTTPS URL on a phone/tablet/laptop and allow camera permission.

### Environment variables
- `LLM_PROVIDER=openrouter`
- `OPENROUTER_MODEL=openrouter/free`
- `OPENROUTER_API_KEY=your_secret_key`
- `DEMO_FALLBACK=true`

If the free LLM router cannot serve a compatible vision model, the app returns a clearly labelled demo fallback rather than pretending that AI analysis occurred.

## Security
The browser sends the image and vitals only to your deployed backend. The backend holds the API key as a server-side secret and sends the request to the LLM provider.

## Important
Free plans, quotas, and available free vision models can change. Check the provider dashboard for current availability.
