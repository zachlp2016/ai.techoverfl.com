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
/utility-*     proxied to the path-restricted secure gateway through WireGuard
/vision-genesis/* proxied to the Vision Genesis controller through WireGuard
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

## Connect The Model Gateway

The four utility namespaces are independent of the future Rails upstream:

```text
/utility-tiny/*
/utility-small/*
/utility-medium/*
/utility-medium-vision/*
/vision-genesis/*
```

Caddy sends only those namespaces to `UTILITY_GATEWAY_UPSTREAM`. Vision Genesis
uses a separate long response-header timeout for image-generation requests. The
default is the dedicated Nginx listener on `secure.techoverfl.com` over
WireGuard:

```dotenv
UTILITY_GATEWAY_UPSTREAM=http://10.77.0.2:8443
```

Install the repository-managed origin configuration on the secure host. The
installer also preserves the firewall rule that permits only the nyc WireGuard
peer:

```bash
sudo ./deploy/install-secure-origin.sh
```

The origin listener contains the existing utility and Vision Genesis routes and
a private health check. It returns `404` for every other path. Provider
credentials remain on the secure host and are never stored in this repository
or on the VPS.

Clients use the same public provider key for utility and Vision Genesis routes.
The secure Nginx gateway translates it to the internal vision-lane key before
contacting the controller; internal credentials never cross WireGuard back to
the public edge.

The complete restoration contract is recorded in
`docs/checkpoints/2026-07-17-wireguard-model-proxy.md`.

## Connect The Portainer Operations Host

`ops.ai.techoverfl.com` belongs entirely to Portainer. The nyc Nginx virtual
host is deliberately thin: it terminates public TLS and forwards the original
host over WireGuard directly to `secure.techoverfl.com`. Caddy is not part of
the operations path.

Secure Nginx is the internal routing authority. It accepts the exact operations
hostname and balances requests across the stable worker NodePort addresses:

```text
192.168.15.42:30779
192.168.15.43:30779
192.168.15.44:30779
```

The Portainer pod IP is intentionally absent because it is ephemeral. The
default WireGuard origin server continues returning `404` for unrecognized
hosts and paths. Install the updated secure route before enabling the public
virtual host:

```bash
sudo ./deploy/install-secure-origin.sh
```

Configure Cloudflare Access for the entire operations hostname before enabling
the nyc site. Then install the bootstrap site and let Certbot own its live copy:

```bash
sudo install -m 0644 deploy/nginx/ops.ai.techoverfl.com.conf \
  /etc/nginx/sites-available/ops.ai.techoverfl.com.conf
sudo ln -s /etc/nginx/sites-available/ops.ai.techoverfl.com.conf \
  /etc/nginx/sites-enabled/ops.ai.techoverfl.com.conf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx --redirect --domain ops.ai.techoverfl.com \
  --email ops@techoverfl.com --agree-tos --no-eff-email
```

Portainer currently exposes HTTPS only and its generated certificate identifies
only `localhost` and `0.0.0.0`. Secure Nginx therefore keeps the trusted LAN hop
encrypted with upstream verification explicitly disabled. A later internal CA
certificate can enable authenticated TLS without changing the public route.

## Maintain Manatree Certificates

The Manatree kubeadm certificates are checked weekly by a systemd timer and are
renewed only when the shortest-lived managed certificate has no more than 60
days remaining. A renewal creates a root-only backup, renews all kubeadm
certificates, updates the local administrator kubeconfig, and restarts each
static control-plane pod so the certificates take effect.

Install and immediately exercise the no-op expiration check on Manatree:

```bash
sudo ./deploy/install-kubeadm-certificate-renewal.sh
```

Inspect its schedule and logs with:

```bash
systemctl list-timers kubeadm-certificate-renewal.timer --no-pager
journalctl -u kubeadm-certificate-renewal.service --no-pager
```

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

After both peers are deployed, verify the private origin from the VPS and the
public routing layer separately:

```bash
curl --fail --show-error --silent http://10.77.0.2:8443/_edge/health
curl --show-error --silent --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8088/utility-tiny/v1/models
curl --show-error --silent --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8088/vision-genesis/v1/health
```

The model and Vision Genesis requests should return `401` without a provider
key. Credentialed requests should return `200` when their backends are healthy.

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
