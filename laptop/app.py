import base64
import io
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image

load_dotenv()

BASE = Path(__file__).resolve().parent
CAPTURE_DIR = BASE / "captures"
CAPTURE_DIR.mkdir(exist_ok=True)

app = FastAPI(title="ESP32-CAM VLM Prototype")

last_result = {
    "timestamp": None,
    "vlm": "Waiting for frame...",
    "filename": None,
    "size": None,
}

def normalize_image(data: bytes) -> bytes:
    """Resize large images before VLM submission."""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((1024, 1024))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=82)
    return out.getvalue()

def ask_openrouter(image_bytes: bytes) -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("VLM_MODEL", "openrouter/free")

    if not key:
        return "OpenRouter API key not configured."

    prompt = os.getenv(
        "VLM_PROMPT",
        "Describe what is happening in this image. "
        "Focus on people, posture, objects, unusual events, "
        "and anything that may require attention. Be concise."
    )

    b64 = base64.b64encode(image_bytes).decode("ascii")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 180
    }

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "ESP32-CAM VLM Prototype"
        },
        json=payload,
        timeout=120
    )

    r.raise_for_status()

    data = r.json()

    return data["choices"][0]["message"]["content"]

def ask_ollama(image_bytes: bytes) -> str:
    model = os.getenv("VLM_MODEL", "")
    base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    if not model:
        return "Ollama VLM not configured. Set VLM_MODEL in .env."

    prompt = os.getenv(
        "VLM_PROMPT",
        "Describe what is happening in this image. Focus on people, posture, objects, unusual events, and anything that may require attention. Be concise."
    )
    b64 = base64.b64encode(image_bytes).decode("ascii")

    r = requests.post(
        f"{base}/api/generate",
        json={"model": model, "prompt": prompt, "images": [b64], "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("response", "")

def ask_vlm(image_bytes: bytes) -> str:
    provider = os.getenv("VLM_PROVIDER", "openrouter").lower()

    if provider == "openrouter":
        return ask_openrouter(image_bytes)

    if provider == "ollama":
        return ask_ollama(image_bytes)

    return "Unknown VLM provider."

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse("""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>ESP32-CAM VLM</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 900px; margin: 30px auto; padding: 0 20px; }
img { max-width: 100%; border-radius: 12px; border: 1px solid #ccc; }
.card { padding: 18px; border: 1px solid #ddd; border-radius: 12px; margin-top: 18px; }
pre { white-space: pre-wrap; }
</style>
</head>
<body>
<h1>ESP32-CAM → VLM</h1>
<p id="status">Waiting for camera...</p>
<div class="card"><img id="camera" src="" alt="Latest frame"></div>
<div class="card"><h2>VLM interpretation</h2><pre id="vlm">Waiting...</pre></div>
<script>
async function refresh() {
  const r = await fetch('/status');
  const d = await r.json();
  document.getElementById('status').textContent =
    d.timestamp ? 'Last frame: ' + d.timestamp + ' | ' + d.size + ' bytes' : 'Waiting for camera...';
  document.getElementById('vlm').textContent = d.vlm;
  if (d.filename) document.getElementById('camera').src = '/captures/' + d.filename + '?t=' + Date.now();
}
setInterval(refresh, 2500);
refresh();
</script>
</body>
</html>""")

@app.get("/status")
def status():
    return JSONResponse(last_result)

@app.get("/captures/{filename}")
def capture(filename: str):
    from fastapi.responses import FileResponse
    path = CAPTURE_DIR / filename
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="image/jpeg")

@app.post("/camera/frame")
async def receive_frame(request: Request):
    global last_result
    raw = await request.body()

    try:
        image_bytes = normalize_image(raw)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{stamp}_{int(time.time()*1000)%1000:03d}.jpg"
        (CAPTURE_DIR / filename).write_bytes(image_bytes)

        try:
            vlm_text = ask_vlm(image_bytes)
        except Exception as exc:
            vlm_text = f"VLM error: {type(exc).__name__}: {exc}"

        last_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "vlm": vlm_text,
            "filename": filename,
            "size": len(image_bytes),
        }
        return last_result
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
