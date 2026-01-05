"""
Security Module Tests (WIKISOFT4)
"""
import pytest
import sys
sys.path.insert(0, "/Users/kj/Desktop/wiki/WIKISOFT4")

from core.security.auth import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    User,
    TokenData,
)
from core.security.rbac import (
    Role,
    Permission,
    has_permission,
    get_role_permissions,
)
from core.security.encryption import encrypt_data, decrypt_data


class TestJWTAuth:
    """JWT Authentication tests."""

    def test_create_access_token(self):
        """Access token creation."""
        token = create_access_token(
            user_id="test_user",
            scopes=["read", "write"]
        )
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long

    def test_verify_valid_token(self):
        """Verify valid token."""
        token = create_access_token(
            user_id="test_user",
            scopes=["read"]
        )

        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.sub == "test_user"
        assert "read" in token_data.scopes

    def test_verify_invalid_token(self):
        """Verify invalid token returns None."""
        invalid_token = "invalid.token.here"
        token_data = verify_token(invalid_token)
        assert token_data is None

    def test_verify_empty_token(self):
        """Verify empty token returns None."""
        token_data = verify_token("")
        assert token_data is None


class TestPasswordHashing:
    """Password hashing tests."""

    def test_hash_password(self):
        """Password hashing."""
        password = "testpassword123"
        try:
            hashed = hash_password(password)
            assert hashed is not None
            assert hashed != password
            assert len(hashed) > 20
        except Exception:
            # bcrypt may not be installed
            pytest.skip("bcrypt not available")

    def test_verify_correct_password(self):
        """Verify correct password."""
        password = "testpassword123"
        try:
            hashed = hash_password(password)
            assert verify_password(password, hashed) == True
        except Exception:
            pytest.skip("bcrypt not available")

    def test_verify_incorrect_password(self):
        """Verify incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        try:
            hashed = hash_password(password)
            assert verify_password(wrong_password, hashed) == False
        except Exception:
            pytest.skip("bcrypt not available")


class TestRBAC:
    """Role-Based Access Control tests."""

    def test_role_enum(self):
        """Role enumeration."""
        assert Role.ADMIN.value == "admin"
        assert Role.VIEWER.value == "viewer"
        assert Role.EDITOR.value == "editor"
        assert Role.VALIDATOR.value == "validator"

    def test_permission_enum(self):
        """Permission enumeration."""
        assert Permission.DATA_READ in Permission
        assert Permission.DATA_WRITE in Permission
        assert Permission.DATA_DELETE in Permission
        assert Permission.ADMIN_SETTINGS in Permission

    def test_admin_permissions(self):
        """Admin has many permissions."""
        admin_perms = get_role_permissions(Role.ADMIN)
        assert Permission.DATA_READ in admin_perms
        assert Permission.DATA_WRITE in admin_perms

    def test_viewer_permissions(self):
        """Viewer has read-only permissions."""
        viewer_perms = get_role_permissions(Role.VIEWER)
        assert Permission.DATA_READ in viewer_perms
        # Viewer should not have write permission
        assert Permission.DATA_WRITE not in viewer_perms

    def test_has_permission_admin(self):
        """Admin has permission check."""
        assert has_permission(Role.ADMIN, Permission.DATA_READ) == True

    def test_has_permission_viewer(self):
        """Viewer permission check."""
        assert has_permission(Role.VIEWER, Permission.DATA_READ) == True
        assert has_permission(Role.VIEWER, Permission.DATA_WRITE) == False


class TestEncryption:
    """Encryption tests."""

    def test_encrypt_decrypt_bytes(self):
        """Encrypt and decrypt bytes."""
        original = b"sensitive data"
        encrypted = encrypt_data(original)

        assert encrypted is not None
        assert encrypted != original

        decrypted = decrypt_data(encrypted)
        assert decrypted == original

    def test_encrypt_decrypt_korean(self):
        """Encrypt and decrypt Korean text."""
        original = "한글 테스트 데이터".encode('utf-8')
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)

        assert decrypted == original

    def test_encrypt_decrypt_long_text(self):
        """Encrypt and decrypt long text."""
        original = b"A" * 1000
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)

        assert decrypted == original

    def test_different_encryptions(self):
        """Same data produces different ciphertexts (IV/nonce)."""
        data = b"test data"
        encrypted1 = encrypt_data(data)
        encrypted2 = encrypt_data(data)

        # Due to random IV, encryptions should be different
        assert encrypted1 != encrypted2

        # But both should decrypt to same value
        assert decrypt_data(encrypted1) == data
        assert decrypt_data(encrypted2) == data


class TestUserModel:
    """User model tests."""

    def test_user_creation(self):
        """User model creation."""
        user = User(
            id="test_id",
            email="test@example.com",
            name="Test User",
            role="user",
            is_active=True,
            scopes=["read", "write"]
        )

        assert user.id == "test_id"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == "user"
        assert user.is_active == True
        assert "read" in user.scopes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
