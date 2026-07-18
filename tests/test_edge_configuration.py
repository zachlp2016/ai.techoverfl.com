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

    def test_secure_origin_install_and_checkpoint_are_tracked(self):
        installer = REPOSITORY_ROOT / "deploy/install-secure-origin.sh"
        checkpoint = (
            REPOSITORY_ROOT
            / "docs/checkpoints/2026-07-17-wireguard-model-proxy.md"
        )

        self.assertTrue(installer.is_file())
        self.assertTrue(checkpoint.is_file())
        self.assertIn("secure-wireguard-origin.conf", installer.read_text())


if __name__ == "__main__":
    unittest.main()
