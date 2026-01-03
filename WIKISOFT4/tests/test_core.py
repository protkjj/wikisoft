"""
WIKISOFT 4.1 Core Module Tests
"""

import pytest


class TestValidators:
    """Validator tests."""

    def test_layer1_import(self):
        """Test Layer1 validator can be imported."""
        from core.validators import validate_layer1
        assert validate_layer1 is not None

    def test_layer2_import(self):
        """Test Layer2 validator can be imported."""
        from core.validators import validate_layer2
        assert validate_layer2 is not None


class TestParsers:
    """Parser tests."""

    def test_parser_import(self):
        """Test parser can be imported."""
        from core.parsers.parser import parse_roster
        assert parse_roster is not None


class TestSecurity:
    """Security module tests."""

    def test_auth_import(self):
        """Test auth module can be imported."""
        from core.security.auth import create_jwt_token, verify_jwt_token
        assert create_jwt_token is not None
        assert verify_jwt_token is not None

    def test_encryption_import(self):
        """Test encryption module can be imported."""
        from core.security.encryption import encrypt_data, decrypt_data
        assert encrypt_data is not None
        assert decrypt_data is not None

    def test_rbac_import(self):
        """Test RBAC module can be imported."""
        from core.security.rbac import check_permission, Role
        assert check_permission is not None
        assert Role is not None


class TestPrivacy:
    """Privacy module tests."""

    def test_detector_import(self):
        """Test PII detector can be imported."""
        from core.privacy.detector import detect_pii, PIIType
        assert detect_pii is not None
        assert PIIType is not None

    def test_masker_import(self):
        """Test masker can be imported."""
        from core.privacy.masker import mask_value, MaskingStrategy
        assert mask_value is not None
        assert MaskingStrategy is not None


class TestIntegrations:
    """Integration module tests."""

    def test_webhook_import(self):
        """Test webhook module can be imported."""
        from integrations.webhook.events import create_cloud_event
        assert create_cloud_event is not None

    def test_n8n_import(self):
        """Test n8n adapter can be imported."""
        from integrations.n8n.adapter import N8nWebhookAdapter
        assert N8nWebhookAdapter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
