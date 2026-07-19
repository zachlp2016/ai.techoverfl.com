#!/bin/sh
set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this installer as root on the Manatree control plane." >&2
    exit 1
fi

for required_command in kubeadm kubectl jq flock; do
    if ! command -v "$required_command" >/dev/null 2>&1; then
        echo "Missing required command: $required_command" >&2
        exit 1
    fi
done

for required_manifest in \
    /etc/kubernetes/manifests/etcd.yaml \
    /etc/kubernetes/manifests/kube-apiserver.yaml \
    /etc/kubernetes/manifests/kube-controller-manager.yaml \
    /etc/kubernetes/manifests/kube-scheduler.yaml
do
    if [ ! -f "$required_manifest" ]; then
        echo "Missing static pod manifest: $required_manifest" >&2
        exit 1
    fi
done

install -o root -g root -m 0755 \
    "$repository_root/deploy/manatree/renew-kubeadm-certificates" \
    /usr/local/sbin/renew-kubeadm-certificates
install -o root -g root -m 0644 \
    "$repository_root/deploy/manatree/kubeadm-certificate-renewal.service" \
    /etc/systemd/system/kubeadm-certificate-renewal.service
install -o root -g root -m 0644 \
    "$repository_root/deploy/manatree/kubeadm-certificate-renewal.timer" \
    /etc/systemd/system/kubeadm-certificate-renewal.timer

systemctl daemon-reload
systemctl enable --now kubeadm-certificate-renewal.timer
systemctl start kubeadm-certificate-renewal.service
systemctl status kubeadm-certificate-renewal.timer --no-pager
