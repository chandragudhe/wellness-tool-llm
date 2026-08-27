
import os, json, base64, re, logging
from flask import Flask, request, jsonify, send_from_directory
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = Flask(__name__, static_folder=".", static_url_path="")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"

def cfg(name, default=None):
    return os.environ.get(name, default)

def safe_error(resp):
    try:
        data = resp.json()
        return data.get("error", {}).get("message") or data.get("message") or json.dumps(data)[:1000]
    except Exception:
        return (resp.text or "Empty non-JSON response")[:1000]

def normalize_image(data_url):
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        raise ValueError("A valid image data URL is required.")
    head, b64 = data_url.split(",", 1)
    mime = head.split(";")[0].replace("data:", "").lower()
    if mime not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise ValueError("Supported image formats: JPEG, PNG, WEBP, GIF.")
    raw = base64.b64decode(b64, validate=True)
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("Image is too large. Please use an image under 8 MB.")
    return data_url

def extract_json(text):
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find the first balanced object, accounting for quoted strings.
    start = text.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': in_str = False
        else:
            if ch == '"': in_str = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except Exception:
                        return None
    return None

def build_prompt(vitals):
    return f"""
You are an educational wellness observation assistant for a school demonstration.
Analyze ONLY visible, non-sensitive wellness-related appearance cues in the supplied image,
and combine them with the user-entered measurements below.

IMPORTANT SAFETY RULES:
- Do not diagnose diseases, medical conditions, deficiencies, or mental health conditions.
- Do not infer a person's identity, age, ethnicity, religion, or other sensitive traits.
- Do not claim that facial appearance proves sleep quality, hydration status, anemia, infection,
  stress level, or any medical condition.
- Treat measurements as user-entered data; do not validate or diagnose from them.
- If the image is unclear, say so.
- Keep language supportive, neutral, and educational.
- State that photo observations are not a medical assessment.
- Do not provide emergency instructions or certainty-based medical conclusions.

User-entered wellness measurements:
BMI: {vitals.get("bmi", "Not provided")}
Blood pressure: {vitals.get("blood_pressure", "Not provided")}
SpO2: {vitals.get("spo2", "Not provided")}
Resting pulse: {vitals.get("pulse", "Not provided")}
Temperature: {vitals.get("temperature", "Not provided")}

Return ONLY valid JSON using exactly this structure:
{{
  "image_quality": "good|fair|poor",
  "image_observations": ["2 to 4 careful visual observations limited to what is visible"],
  "vitals_summary": "Brief neutral summary of the values supplied by the user; do not diagnose.",
  "wellness_focus": ["2 to 4 general wellness areas"],
  "suggestions": ["3 to 5 general, low-risk wellness suggestions"],
  "limitations": "Photo-based observations are informational only and are not a medical assessment."
}}
""".strip()

def call_openrouter(image_data_url, vitals):
    api_key = cfg("OPENROUTER_API_KEY", "").strip()
    model = cfg("OPENROUTER_MODEL", "openrouter/free").strip() or "openrouter/free"
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured on the server.")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You follow the user's requested JSON schema exactly. Never diagnose from an image."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_prompt(vitals)},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ],
        "temperature": 0.2,
        "max_tokens": 700,
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-OpenRouter-Metadata": "enabled",
        "HTTP-Referer": cfg("APP_URL", "https://example.invalid"),
        "X-Title": "Wellness Tool School Demo"
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
    except requests.RequestException as e:
        raise RuntimeError(f"Network request to OpenRouter failed: {type(e).__name__}: {e}")

    if not response.ok:
        msg = safe_error(response)
        logging.error("OpenRouter HTTP %s: %s", response.status_code, msg)
        raise RuntimeError(f"OpenRouter HTTP {response.status_code}: {msg}")

    try:
        result = response.json()
    except Exception:
        body = (response.text or "").strip()
        logging.error("OpenRouter returned non-JSON response: %s", body[:1000])
        raise RuntimeError("OpenRouter returned a non-JSON response.")

    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenRouter returned no choices: {json.dumps(result)[:1000]}")

    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(str(x.get("text", "")) for x in content if isinstance(x, dict))
    content = (content or "").strip()
    if not content:
        raise RuntimeError("OpenRouter returned an empty analysis.")

    parsed = extract_json(content)
    if parsed is None:
        parsed = {
            "image_quality": "fair",
            "image_observations": ["The model returned a narrative response instead of the requested structured format."],
            "vitals_summary": "User-entered measurements were included in the AI request.",
            "wellness_focus": ["General wellness awareness"],
            "suggestions": [],
            "limitations": "Photo-based observations are informational only and are not a medical assessment.",
            "raw_model_response": content
        }

    return {
        "analysis": parsed,
        "model_requested": model,
        "model_used": result.get("model", model),
        "request_id": result.get("id")
    }

def demo_analysis(vitals):
    return {
        "image_quality": "not AI-verified",
        "image_observations": ["Demo fallback is active; no live AI image interpretation was returned."],
        "vitals_summary": "Values received: " + ", ".join(
            f"{k}={v}" for k, v in vitals.items() if v not in (None, "", "Not provided")
        ) if any(v not in (None, "", "Not provided") for v in vitals.values())
        else "No measurements were provided.",
        "wellness_focus": ["General wellness awareness"],
        "suggestions": ["Use the live LLM result when available; this fallback is for interface demonstration only."],
        "limitations": "Demo fallback only. This is not AI image analysis and is not a medical assessment."
    }

@app.get("/")
def home():
    return send_from_directory(".", "index.html")

@app.get("/manifest.json")
def manifest():
    return send_from_directory(".", "manifest.json")

@app.get("/api/llm-status")
def llm_status():
    api_key = cfg("OPENROUTER_API_KEY", "").strip()
    model = cfg("OPENROUTER_MODEL", "openrouter/free").strip() or "openrouter/free"
    status = {
        "provider": cfg("LLM_PROVIDER", "openrouter"),
        "model": model,
        "api_key_configured": bool(api_key),
        "connectivity": "not_tested",
        "detail": ""
    }
    if not api_key:
        status["connectivity"] = "failed"
        status["detail"] = "OPENROUTER_API_KEY is not configured."
        return jsonify(status), 503
    try:
        r = requests.get(MODELS_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=20)
        if r.ok:
            status["connectivity"] = "reachable"
            status["detail"] = "OpenRouter API is reachable. This check does not consume a chat completion."
            return jsonify(status)
        status["connectivity"] = "failed"
        status["detail"] = f"OpenRouter HTTP {r.status_code}: {safe_error(r)}"
        return jsonify(status), 503
    except requests.RequestException as e:
        status["connectivity"] = "failed"
        status["detail"] = f"Network error: {type(e).__name__}: {e}"
        return jsonify(status), 503

@app.post("/api/wellness-analysis")
def wellness_analysis():
    try:
        data = request.get_json(force=True, silent=False) or {}
        image = normalize_image(data.get("image", ""))
        vitals = data.get("vitals") or {}
        vitals = {
            "bmi": vitals.get("bmi", "Not provided"),
            "blood_pressure": vitals.get("blood_pressure", "Not provided"),
            "spo2": vitals.get("spo2", "Not provided"),
            "pulse": vitals.get("pulse", "Not provided"),
            "temperature": vitals.get("temperature", "Not provided"),
        }
        result = call_openrouter(image, vitals)
        return jsonify({"ok": True, "source": "live_llm", **result})
    except Exception as e:
        detail = str(e)
        logging.exception("Wellness analysis failed: %s", detail)
        if cfg("DEMO_FALLBACK", "false").lower() == "true":
            data = request.get_json(silent=True) or {}
            vitals = (data.get("vitals") or {})
            return jsonify({
                "ok": True,
                "source": "demo_fallback",
                "warning": "Live LLM analysis was unavailable. Demo fallback was used.",
                "live_error": detail,
                "analysis": demo_analysis(vitals)
            })
        return jsonify({"ok": False, "error": detail}), 502

if __name__ == "__main__":
    port = int(cfg("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
