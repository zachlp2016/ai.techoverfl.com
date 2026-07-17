# TOF AI Public Edge

Public VPS edge for `ai.techoverfl.com`. It currently serves the existing TOF
AI dashboard and is ready to proxy application traffic to the private Rails
service when the WireGuard connection is available.

The edge owns TLS, public routing, local downloads, the gateway health endpoint,
and the offline page. It does not own users, projects, conversations, HIL state,
notification authorization, or application data.

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
cp .env.example .env
docker compose up -d --build
```

The safe default keeps all normal traffic on the local dashboard. Caddy obtains
and renews TLS automatically when `SITE_ADDRESS` resolves to the VPS and ports
80 and 443 are reachable.

Public routes:

```text
/edge/health   handled directly by Caddy
/status        served by the local dashboard container
/downloads/*   served by the local dashboard container
/.well-known/* served by the local dashboard container
/*             sent to INTERNAL_APP_UPSTREAM
```

When the configured upstream cannot be reached, normal application requests
receive the local offline page with HTTP status `503`.

## Connect The Private Rails Upstream

Do this only after WireGuard routing and the Rails listener are ready. In the
VPS `.env`, replace the dashboard defaults with the private upstream values:

```dotenv
INTERNAL_APP_UPSTREAM=http://10.0.0.2:3000
INTERNAL_APP_HEALTH_PATH=/up
```

Use the actual WireGuard peer address in the VPS secret configuration; do not
commit it if you consider the address sensitive. Caddy preserves request paths
and supports WebSocket upgrades through its standard reverse proxy.

Webhook routes are intentionally not special-cased yet. They should be added
only after Rails has authenticated endpoints for the provider callbacks.

## Connector File

Place the iPhone connector at:

```text
site/downloads/tof-ai-app.mobileconfig
```

The homepage download button already points to `/downloads/tof-ai-app.mobileconfig`.

Do not commit signed profiles, private certificates, WireGuard private keys,
Telegram or SMS provider tokens, APNs keys, or Rails secrets.

## Verify

The dashboard tests use only the Python standard library:

```bash
python3 -m unittest discover -s tests -v
docker compose config --quiet
docker compose run --rm --no-deps edge \
  caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

The final command may pull the Caddy image the first time.

## Deploy

After reviewing `.env` on the VPS:

```bash
./deploy/deploy.sh
```

WireGuard remains host-managed and is not stored or configured by this public
repository.
