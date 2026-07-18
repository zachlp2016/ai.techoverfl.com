import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class EdgeConfigurationTest(unittest.TestCase):
    def test_caddy_routes_all_utility_namespaces_to_private_gateway(self):
        caddyfile = (REPOSITORY_ROOT / "Caddyfile").read_text()

        for namespace in (
            "/utility-tiny",
            "/utility-small",
            "/utility-medium",
            "/utility-medium-vision",
        ):
            self.assertIn(namespace, caddyfile)
            self.assertIn(f"{namespace}/*", caddyfile)

        self.assertIn("UTILITY_GATEWAY_UPSTREAM", caddyfile)
        self.assertIn("health_uri /_edge/health", caddyfile)
        self.assertIn("@vision_genesis path /vision-genesis /vision-genesis/*", caddyfile)
        self.assertIn("response_header_timeout 3600s", caddyfile)

    def test_secure_origin_is_wireguard_bound_and_default_deny(self):
        origin = (
            REPOSITORY_ROOT / "deploy/nginx/secure-wireguard-origin.conf"
        ).read_text()

        self.assertIn("listen 10.77.0.2:8443;", origin)
        self.assertIn("set_real_ip_from 10.77.0.1;", origin)
        self.assertIn(
            "include /etc/nginx/snippets/ai-gateway-locations.conf;", origin
        )
        self.assertIn(
            "include /etc/nginx/snippets/vision-genesis-locations.conf;", origin
        )
        self.assertIn("location / {\n        return 404;", origin)

    def test_ops_origin_is_host_scoped_and_uses_worker_nodeports(self):
        origin = (
            REPOSITORY_ROOT / "deploy/nginx/secure-wireguard-origin.conf"
        ).read_text()
        public_site = (
            REPOSITORY_ROOT / "deploy/nginx/ops.ai.techoverfl.com.conf"
        ).read_text()

        self.assertIn("server_name ops.ai.techoverfl.com;", origin)
        self.assertIn("proxy_pass https://tof_portainer_workers;", origin)
        self.assertIn("proxy_ssl_verify off;", origin)
        self.assertNotIn("172.16.91.211", origin)

        for worker in ("192.168.15.42", "192.168.15.43", "192.168.15.44"):
            self.assertIn(f"server {worker}:30779", origin)

        self.assertIn("server_name ops.ai.techoverfl.com;", public_site)
        self.assertIn("proxy_pass http://10.77.0.2:8443;", public_site)
        self.assertNotIn("192.168.15.", public_site)
        self.assertIn("proxy_set_header Host $host;", public_site)

    def test_kubeadm_renewal_is_thresholded_and_systemd_managed(self):
        renewal = (
            REPOSITORY_ROOT / "deploy/manatree/renew-kubeadm-certificates"
        ).read_text()
        timer = (
            REPOSITORY_ROOT
            / "deploy/manatree/kubeadm-certificate-renewal.timer"
        ).read_text()

        self.assertIn("KUBEADM_RENEWAL_THRESHOLD_SECONDS", renewal)
        self.assertIn("kubeadm certs renew all", renewal)
        self.assertIn("restart_component kube-apiserver", renewal)
        self.assertIn("OnCalendar=Sun", timer)
        self.assertIn("Persistent=true", timer)

    def test_secure_origin_install_and_checkpoint_are_tracked(self):
        installer = REPOSITORY_ROOT / "deploy/install-secure-origin.sh"
        checkpoint = (
            REPOSITORY_ROOT
            / "docs/checkpoints/2026-07-17-wireguard-model-proxy.md"
        )

        self.assertTrue(installer.is_file())
        self.assertTrue(checkpoint.is_file())
        self.assertIn("secure-wireguard-origin.conf", installer.read_text())
        self.assertIn("Host: ops.ai.techoverfl.com", installer.read_text())


if __name__ == "__main__":
    unittest.main()
