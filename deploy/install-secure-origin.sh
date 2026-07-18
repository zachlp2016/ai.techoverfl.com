#!/bin/sh
set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_config="$repository_root/deploy/nginx/secure-wireguard-origin.conf"
destination_config=/etc/nginx/conf.d/secure-wireguard-origin.conf

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer as root on secure.techoverfl.com." >&2
  exit 1
fi

if ! ip -4 address show dev wg0 | grep -q '10\.77\.0\.2/30'; then
  echo "WireGuard address 10.77.0.2/30 is not active on wg0." >&2
  exit 1
fi

for required_file in \
  /etc/nginx/snippets/ai-gateway-locations.conf \
  /etc/nginx/snippets/vision-genesis-locations.conf
do
  if [ ! -f "$required_file" ]; then
    echo "Missing required Nginx snippet: $required_file" >&2
    exit 1
  fi
done

install -o root -g root -m 0644 "$source_config" "$destination_config"
ufw allow in on wg0 from 10.77.0.1 to 10.77.0.2 \
  port 8443 proto tcp comment 'TOF model gateway from nyc'

/usr/sbin/nginx -t
systemctl reload nginx

attempt=1
while ! curl --fail --show-error --silent \
  http://10.77.0.2:8443/_edge/health
do
  if [ "$attempt" -ge 10 ]; then
    echo "Secure origin did not become healthy after Nginx reload." >&2
    exit 1
  fi

  attempt=$((attempt + 1))
  sleep 1
done
