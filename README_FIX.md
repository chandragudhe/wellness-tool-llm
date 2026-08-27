# Fix for OpenRouter JSON Error

This version fixes the error:
`Expecting value: line 1 column 1 (char 0)`.

The previous backend attempted `json.loads()` directly on the model response. Free routed models can occasionally return an empty response, explanatory text, or an API error body. The revised backend:

- checks HTTP errors and displays the OpenRouter response body;
- checks for empty responses;
- extracts JSON from code fences or surrounding text;
- gives a clear error when the selected route does not return usable structured output.

Recommended Render environment variables:

- `LLM_PROVIDER=openrouter`
- `OPENROUTER_API_KEY=<your key>`
- `OPENROUTER_MODEL=openrouter/free`
- `DEMO_FALLBACK=true` (optional, for school demonstrations)

If OpenRouter returns an image-input availability error, retry later or select a specific currently available vision-capable `:free` model from OpenRouter's model catalog.
