# WireGuard Model Proxy Checkpoint — 2026-07-17

This checkpoint records the reproducible public-edge-to-model-gateway contract.
It deliberately excludes private keys, provider credentials, and application
secrets.

## Host roles

```text
nyc.techoverfl.com
  public edge
  public IP: 137.184.58.57
  WireGuard: 10.77.0.1/30

secure.techoverfl.com
  private model gateway
  WireGuard: 10.77.0.2/30
```

WireGuard is host managed through `wg-quick@wg0`. The tunnel is host-to-host
only; it does not install a default route, LAN route, NAT rule, or forwarding
rule.

## Public route contract

Only these namespaces cross the tunnel from the public edge:

```text
/utility-tiny
/utility-small
/utility-medium
/utility-medium-vision
/vision-genesis
```

Each namespace includes its slash-prefixed children. Caddy sends them to
`http://10.77.0.2:8443`. All other public paths continue through the existing
dashboard/application route.

The secure origin listener includes the existing utility gateway and Vision
Genesis snippets. Its only additional route is the private
`/_edge/health` check. Every other path returns `404`.

The public provider key is shared across utility and Vision Genesis requests.
Nginx authenticates that public key, maps `/vision-genesis/*` to the
`utility-medium-vision` lane, and replaces the public credential with the
lane's internal upstream key before contacting the controller. The internal key
never leaves `secure.techoverfl.com`.

The durable secure-host sources for that translation are:

```text
/home/zachlp2016/ai-gateway-nginx/generate-ai-gateway-nginx
/home/zachlp2016/vision-genesis/nginx/vision-genesis-locations.conf
```

The generator must retain this URI mapping:

```nginx
~^/vision-genesis/ /utility-medium-vision/v1/chat/completions;
```

The generator writes the internal controller key to the root-only
`/etc/nginx/ai-gateway-vision-controller-key.map`. The Vision Genesis snippet
must send `$ai_gateway_vision_controller_api_key` upstream and clear the public
`Authorization` header instead of forwarding the public credential directly.

## Source of truth

```text
Caddyfile
compose.yaml
.env.example
deploy/nginx/secure-wireguard-origin.conf
deploy/install-secure-origin.sh
```

The live secure-host Nginx file is an installed copy at:

```text
/etc/nginx/conf.d/secure-wireguard-origin.conf
```

Reinstall it from a repository checkout on `secure.techoverfl.com`:

```bash
sudo ./deploy/install-secure-origin.sh
```

The installer verifies the WireGuard address and required Nginx snippets,
installs the listener, preserves the firewall boundary, validates Nginx, reloads
it, and checks the private health endpoint.

## Firewall boundary

The secure host permits TCP `8443` on `wg0` only from `10.77.0.1`. The listener
binds only to `10.77.0.2`. Public access to the port is not permitted.

## Verification

From `secure.techoverfl.com`:

```bash
sudo wg show wg0
curl --fail http://10.77.0.2:8443/_edge/health
```

From `nyc.techoverfl.com`:

```bash
ping -c 4 10.77.0.2
curl --fail http://10.77.0.2:8443/_edge/health
curl --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8088/utility-tiny/v1/models
curl --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8088/vision-genesis/v1/health
```

The unauthenticated model and Vision Genesis requests must return `401`.
Credentialed requests must return `200` when their selected backend is healthy.
A non-approved path sent directly to the private origin must return `404`.

## DNS and TLS state

Cloudflare now proxies `ai.techoverfl.com` to the nyc public IPv4 address
`137.184.58.57`. Public resolvers therefore return Cloudflare anycast addresses
rather than the origin address directly.

Certbot installed the nyc origin certificate at:

```text
/etc/letsencrypt/live/ai.techoverfl.com/fullchain.pem
/etc/letsencrypt/live/ai.techoverfl.com/privkey.pem
```

The certificate expires on `2026-10-15`, and Certbot configured scheduled
renewal. Direct origin TLS with SNI and public Cloudflare HTTPS were both
verified after issuance.

Final public HTTPS checks returned:

```text
/edge/health                          200
/status                               200
/utility-tiny/v1/models               200 with provider key
/utility-small/v1/models              200 with provider key
/utility-medium/v1/models             200 with provider key
/utility-medium-vision/v1/models      200 with provider key
/vision-genesis/v1/health             200 with the same provider key
/vision-genesis/v1/health             401 without a provider key
```
