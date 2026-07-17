# TLS Preparation Checkpoint — 2026-07-17

## Completed

- Confirmed repository ownership is zachlp2016:zachlp2016.
- Confirmed the Caddy proxy foundation is local commit d18c912 on main.
- Kept the dashboard service as the default upstream.
- Changed the edge container to HTTP on container port 8080, published only as
  127.0.0.1:8088 on the VPS.
- Added an Nginx bootstrap virtual host for ai.techoverfl.com that preserves the
  host, client address, forwarded protocol, and WebSocket upgrade headers.
- Configured Caddy to trust the private proxy hop from host Nginx.
- Documented the Nginx and Certbot cutover procedure.
- Confirmed all six Python dashboard tests pass.

## Not Activated

- Public DNS still resolves ai.techoverfl.com to 104.182.148.218. The VPS public
  address is 137.184.58.57.
- Docker Engine and the Compose plugin are not installed; the installation
  attempt stopped at an unterminated shell heredoc.
- The edge Compose stack has not been built or started.
- The Nginx bootstrap virtual host has not been copied into /etc/nginx.
- No certificate has been requested or installed for ai.techoverfl.com.
- No production deployment or GitHub push has occurred.
- WireGuard, the private Rails /up connection, and webhook authority remain out
  of scope and unconfigured.

## Remaining Cutover

1. Point the Cloudflare DNS-only A record for ai.techoverfl.com to
   137.184.58.57 and wait for public resolution.
2. Finish installing Docker Engine and the Compose plugin.
3. Create the deployment .env from .env.example and start the Compose stack.
4. Install and enable the Nginx bootstrap virtual host.
5. Run the Nginx configuration test and reload Nginx.
6. Run Certbot with the Nginx plugin, enable HTTPS redirection, and test renewal.
7. Verify /edge/health, /status, normal dashboard routing, and offline fallback
   over public HTTPS.
