# TOF AI Dashboard

Static dashboard for `ai.techoverfl.com` with an iPhone connector download link.

## Run Locally

```bash
python3 site/server.py
```

Open `http://localhost:8080`.

Use a different port when needed:

```bash
PORT=8081 python3 site/server.py
```

## Run In Docker

```bash
docker build -t tof-ai-dashboard .
docker run --rm -p 8080:8080 tof-ai-dashboard
```

## Connector File

Place the iPhone connector at:

```text
site/downloads/tof-ai-app.mobileconfig
```

The homepage download button already points to `/downloads/tof-ai-app.mobileconfig`.
