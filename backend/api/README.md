# API

Backend service tying agents together and serving the dashboard.

## Speech-to-text slice

This folder currently exposes the portable Deepgram transcription layer. The code is intentionally split so FastAPI and the CLI both call the same framework-independent service.

### Setup

```bash
cd backend/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `DEEPGRAM_API_KEY` in `.env`, or export it in your shell.

### CLI usage

```bash
cd backend/api
python3 -m transcription.cli ../../demo/voicemails/sample.wav --pretty
python3 -m transcription.cli ../../demo/voicemails/sample.wav --pretty --output result.json
```

### API usage

```bash
cd backend/api
uvicorn main:app --reload --port 8000
```

```bash
curl -X POST \
  -F "file=@../../demo/voicemails/sample.wav" \
  http://localhost:8000/api/transcriptions
```

The API and CLI return the same JSON contract as `contracts/transcription_response.example.json`.
