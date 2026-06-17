# AfterMeet Backend

FastAPI backend for the AfterMeet MVP.

## Local Development

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a local environment file:

```bash
cp .env.example .env
```

4. Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Verify the health endpoint:

```bash
curl http://localhost:8000/health
```

## Environment Variables

- `APP_ENV`: runtime environment name, default `development`
- `APP_NAME`: application name shown in FastAPI docs
- `APP_VERSION`: application version shown in FastAPI docs
- `DATABASE_URL`: database connection string, default `sqlite:///./aftermeet.db`
- `UPLOAD_DIR`: local upload directory, default `uploads`
- `MAX_UPLOAD_SIZE_MB`: maximum upload size, default `100`
- `WHISPER_MODEL_NAME`: faster-whisper model size, default `small`
