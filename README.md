# TOF AI Public Edge

Public VPS edge for `ai.techoverfl.com`. It currently serves the existing TOF
AI dashboard and is ready to proxy application traffic to the private Rails
service when the WireGuard connection is available.

Nginx owns public TLS on this multi-site VPS. The edge Caddy container owns
public routing, local downloads, the gateway health endpoint, and the offline
page behind Nginx. It is published only on `127.0.0.1:8088`; it does not compete
with the existing public web server for ports 80 or 443.

The edge does not own users, projects, conversations, HIL state, notification
authorization, or application data.

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

The safe default keeps all normal traffic on the local dashboard. Nginx sends
requests to Caddy over loopback; Certbot obtains and renews the public Nginx
certificate.

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

## Enable Production TLS

The authoritative DNS zone is hosted by Cloudflare. Set the DNS-only `A` record
for `ai.techoverfl.com` to the VPS public address, `137.184.58.57`, before
requesting a certificate. Confirm that public DNS and the VPS agree:

    getent ahostsv4 ai.techoverfl.com
    curl -4 https://api.ipify.org

Bring up the edge stack, then install the bootstrap Nginx virtual host:

    cp .env.example .env
    ./deploy/deploy.sh

    sudo install -m 0644 deploy/nginx/ai.techoverfl.com.conf /etc/nginx/sites-available/ai.techoverfl.com.conf
    sudo ln -s /etc/nginx/sites-available/ai.techoverfl.com.conf /etc/nginx/sites-enabled/ai.techoverfl.com.conf
    sudo nginx -t
    sudo systemctl reload nginx

Request and install the real certificate through the existing Certbot Nginx
integration:

    sudo certbot --nginx --redirect --domain ai.techoverfl.com --email ops@techoverfl.com --agree-tos --no-eff-email
    sudo certbot renew --dry-run

Certbot owns the installed copy under `/etc/nginx` after this step; do not copy
the bootstrap file over it again. Verify both edge-controlled routes through the
public TLS listener:

    curl --fail --show-error --silent https://ai.techoverfl.com/edge/health
    curl --fail --show-error --silent https://ai.techoverfl.com/status >/dev/null
