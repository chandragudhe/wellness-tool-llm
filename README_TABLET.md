# Run on an Android Tablet with a Free Vision LLM

## Recommended mode: Termux + OpenRouter Free Models Router

This is the practical option for an Android tablet because the large vision model runs remotely; the tablet only captures the image and runs the lightweight Python server.

## 1. Install Termux
Install Termux from F-Droid, then open it.

## 2. Give Termux storage access
```
termux-setup-storage
```
Allow the permission.

## 3. Install Python
```
pkg update
pkg install python
```

## 4. Go to the extracted project
Example:
```
cd ~/storage/downloads/wellness-demo-mobile
```
Use `ls` to confirm that `server.py` is present.

## 5. Create a free OpenRouter account and API key
OpenRouter's `openrouter/free` router can select from currently available free models and supports image input when compatible free vision models are available. Availability can change.

Do NOT put the API key into `index.html`.

## 6. Set the key in Termux for this session
```
export OPENROUTER_API_KEY='PASTE_YOUR_KEY_HERE'
export LLM_PROVIDER='openrouter'
export OPENROUTER_MODEL='openrouter/free'
```

## 7. Run the project
```
python server.py
```

## 8. Open Chrome on the SAME tablet
```
http://localhost:8000
```

Capture/upload a photo, enter vitals, and submit for AI wellness analysis.

### Security note
For a school demonstration, the API key stays in the Termux server process and is not exposed to browser JavaScript. Do not publish the key in GitHub or a public website.

## Alternative: local Ollama
Use only on a capable computer or supported device with enough memory/storage. Set:
```
export LLM_PROVIDER='ollama'
export OLLAMA_MODEL='llava'
python server.py
```
A tablet is generally better suited to the OpenRouter remote API option than running a large vision model locally.

## If the free model is unavailable
The free model pool can change. The server will return the provider error instead of pretending that a real image analysis occurred. You can temporarily enable demo fallback:
```
export DEMO_FALLBACK='true'
```
