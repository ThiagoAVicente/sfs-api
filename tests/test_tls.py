"""Integration tests for TLS/HTTPS configuration."""

import pytest
import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.mark.integration
class TestTLS:
    """Basic TLS integration tests."""

    def test_https_works(self):
        """Test HTTPS connection works."""
        response = requests.get("https://localhost/health", verify=False)
        assert response.status_code == 200

    def test_http_redirects_to_https(self):
        """Test HTTP redirects to HTTPS."""
        response = requests.get("http://localhost/health", allow_redirects=False)
        assert response.status_code in [301, 302, 307, 308]
        assert "https://" in response.headers.get("Location", "")

    def test_security_headers_present(self):
        """Test security headers are set."""
        response = requests.get("https://localhost/search", verify=False)
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert "Content-Security-Policy" in response.headers

    def test_swagger_ui_works(self):
        """Test Swagger UI is accessible."""
        response = requests.get("https://localhost/docs", verify=False)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
