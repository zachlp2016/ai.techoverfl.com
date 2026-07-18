# Portainer Operations Edge and Kubeadm Renewal — 2026-07-18

This checkpoint records the private Portainer route, the Manatree certificate
renewal, and the remaining public activation gates. It contains no credentials,
private keys, kubeconfigs, or Cloudflare tokens.

## URL authority

```text
ai.techoverfl.com/        existing public dashboard
ai.techoverfl.com/app/    reserved for Rails
ops.ai.techoverfl.com/    Portainer only
192.168.20.152:6443       private Kubernetes API
```

The Kubernetes API is not published through the web edge. Lens and kubectl use
a kubeconfig through private network access.

## Operations traffic path

```text
Cloudflare Access
  -> nyc public Nginx and Certbot TLS
  -> WireGuard 10.77.0.1 to 10.77.0.2
  -> secure.techoverfl.com Nginx
  -> worker NodePort pool on TCP 30779
  -> Portainer service TCP 9443
```

NYC contains no Kubernetes worker addresses and Caddy is not part of this
hostname's path. Its bootstrap virtual host preserves the public hostname and
forwards the request directly to the secure WireGuard listener.

The NYC operations vhost permits only Cloudflare's published IPv4 and IPv6
source networks and forwards the trusted `CF-Connecting-IP` value. Direct
origin requests therefore cannot bypass Cloudflare Access.

Secure Nginx is the internal routing authority. The named server accepts only
`ops.ai.techoverfl.com` and balances across:

```text
192.168.15.42:30779
192.168.15.43:30779
192.168.15.44:30779
```

The Portainer pod IP is deliberately not part of the configuration. Unknown
hosts continue through the default-deny server and return `404`.

Portainer currently runs with `--http-disabled`. Its generated TLS certificate
expires in 2031 but identifies only `localhost` and `0.0.0.0`. Secure Nginx uses
HTTPS to the NodePort with verification explicitly disabled. A later internal
CA certificate can replace this bounded exception.

## Kubernetes certificate renewal

All kubeadm-managed certificates previously expired on July 20, 2026. On July
18 they were backed up and renewed through July 18, 2027. The root-only recovery
copy is stored on Manatree at:

```text
/var/backups/kubernetes-20260718-pre-renewal
```

etcd, kube-apiserver, kube-controller-manager, and kube-scheduler were restarted
so the renewed certificates took effect. API readiness, etcd readiness, all
four current nodes, and the TOF-AI workloads were verified afterward.

The installed persistence contract is:

```text
/usr/local/sbin/renew-kubeadm-certificates
/etc/systemd/system/kubeadm-certificate-renewal.service
/etc/systemd/system/kubeadm-certificate-renewal.timer
```

The timer checks weekly with a randomized delay. It renews only when the
shortest-lived kubeadm-managed certificate has no more than 60 days remaining,
creates a new root-only backup, updates the administrator kubeconfig, and
performs the required controlled static-pod restarts. Its initial installation
run exited successfully without renewal because 364 days remained.

## Verified state

```text
secure Nginx syntax                         valid
ops host over the WireGuard listener       200
unexpected host over the listener          404
Portainer through each worker NodePort      200
kube-apiserver /readyz                      passed
renewed API certificate served externally  Jul 18 2027
kubeadm renewal timer                       enabled and active
Python repository tests                     11 passed
Docker Compose configuration                valid
Caddy configuration                         valid
NYC bootstrap Nginx configuration           valid
```

## Public activation gates

The private route is installed, but the NYC virtual host must remain disabled
until Cloudflare Access protects the entire hostname. Public activation is:

1. Confirm Cloudflare Access redirects unauthenticated requests for the full
   `ops.ai.techoverfl.com` hostname.
2. Add an Access bypass only for `/.well-known/acme-challenge/*` so Certbot can
   issue and renew the origin certificate.
3. Install the tracked Cloudflare allowlist and operations vhost on NYC.
4. Validate and reload Nginx.
5. Run Certbot for `ops.ai.techoverfl.com`.
6. Test login, session persistence, logs, console attachment, and WebSockets.
7. Confirm direct-origin requests are denied and the worker NodePort has no
   public route.

At this checkpoint, DNS resolves through Cloudflare but its public TLS handshake
is not yet ready, and the NYC virtual host is intentionally not installed.
