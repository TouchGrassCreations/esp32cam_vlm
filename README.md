# ESP32-CAM + Laptop VLM Prototype

A minimal prototype:
ESP32-CAM -> Wi-Fi -> FastAPI laptop server -> VLM -> browser dashboard.

The server supports:
1. OpenAI-compatible vision API (recommended for easiest first test)
2. Ollama vision models (optional local inference)

## 1. Laptop setup

Create a Python environment and install:

    pip install -r laptop/requirements.txt

Copy `.env.example` to `.env`.

For an OpenAI-compatible endpoint, set:
    VLM_PROVIDER=openai
    OPENAI_API_KEY=...
    VLM_MODEL=...

For Ollama:
    VLM_PROVIDER=ollama
    OLLAMA_BASE_URL=http://127.0.0.1:11434
    VLM_MODEL=<your vision model>

Start:

    uvicorn laptop.app:app --host 0.0.0.0 --port 8000

Open:
    http://127.0.0.1:8000

## 2. ESP32-CAM

This firmware targets the common AI Thinker ESP32-CAM.

Edit:
- WIFI_SSID
- WIFI_PASSWORD
- SERVER_IP

Then upload with Arduino IDE / PlatformIO.

The ESP32-CAM captures a JPEG and POSTs it to:
    http://SERVER_IP:8000/camera/frame

Press the ESP32 reset button after uploading.

## 3. Finding the laptop IP

On Windows:

    ipconfig

Look for the laptop's IPv4 address on the same Wi-Fi network, e.g.
    192.168.1.20

Put that address in `SERVER_IP`.

## 4. Important

Do not expose port 8000 to the public internet. Keep the prototype on your local Wi-Fi.

The first version intentionally sends one frame at a time rather than continuous video. This is much more practical for VLM inference.
