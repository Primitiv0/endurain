"""Tests for profile utility functions."""

import profile.utils as profile_utils
from profile.exceptions import MemoryAllocationError
from unittest.mock import MagicMock, patch

import pytest


class TestBasePerformanceConfig:
    """Test suite for BasePerformanceConfig."""

    def test_default_values(self):
        config = profile_utils.BasePerformanceConfig()
        assert config.batch_size == 1000
        assert config.max_memory_mb == 1024
        assert config.timeout_seconds == 3600
        assert config.chunk_size == 8192
        assert config.enable_memory_monitoring is True

    def test_custom_values(self):
        config = profile_utils.BasePerformanceConfig(
            batch_size=100,
            max_memory_mb=512,
            timeout_seconds=1800,
            chunk_size=4096,
            enable_memory_monitoring=False,
        )
        assert config.batch_size == 100
        assert config.max_memory_mb == 512
        assert config.timeout_seconds == 1800
        assert config.chunk_size == 4096
        assert config.enable_memory_monitoring is False

    def test_get_tier_configs_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            profile_utils.BasePerformanceConfig._get_tier_configs()

    @patch("profile.utils.detect_system_memory_tier")
    def test_get_auto_config_calls_get_tier_configs(self, mock_detect):
        mock_detect.return_value = ("high", 4096)

        class TestConfig(profile_utils.BasePerformanceConfig):
            @classmethod
            def _get_tier_configs(cls):
                return {"high": {"batch_size": 5000, "max_memory_mb": 2048}}

        config = TestConfig.get_auto_config()
        assert config.batch_size == 5000
        assert config.max_memory_mb == 2048

    @patch("profile.utils.detect_system_memory_tier")
    def test_get_auto_config_unknown_tier_defaults(self, mock_detect):
        mock_detect.return_value = ("unknown", 1024)

        class TestConfig(profile_utils.BasePerformanceConfig):
            @classmethod
            def _get_tier_configs(cls):
                return {"high": {"batch_size": 5000}}

        config = TestConfig.get_auto_config()
        assert config.batch_size == 1000

    @patch("profile.utils.detect_system_memory_tier")
    def test_get_auto_config_detect_failure_defaults(self, mock_detect):
        mock_detect.side_effect = Exception("detect failed")

        class TestConfig(profile_utils.BasePerformanceConfig):
            @classmethod
            def _get_tier_configs(cls):
                return {"high": {"batch_size": 5000}}

        config = TestConfig.get_auto_config()
        assert config.batch_size == 1000


class TestGenerateTOTPSecret:
    """Test suite for generate_totp_secret function."""

    @patch("profile.utils.pyotp.random_base32")
    def test_returns_base32_secret(self, mock_random_base32):
        mock_random_base32.return_value = "JBSWY3DPEHPK3PXP"
        result = profile_utils.generate_totp_secret()
        assert result == "JBSWY3DPEHPK3PXP"
        mock_random_base32.assert_called_once()


class TestVerifyTOTP:
    """Test suite for verify_totp function."""

    @patch("profile.utils.pyotp.TOTP")
    def test_verify_valid_token(self, mock_totp_class):
        mock_totp = MagicMock()
        mock_totp.verify.return_value = True
        mock_totp_class.return_value = mock_totp

        result = profile_utils.verify_totp("secret", "123456")
        assert result is True
        mock_totp.verify.assert_called_once_with("123456", valid_window=1)

    @patch("profile.utils.pyotp.TOTP")
    def test_verify_invalid_token(self, mock_totp_class):
        mock_totp = MagicMock()
        mock_totp.verify.return_value = False
        mock_totp_class.return_value = mock_totp

        result = profile_utils.verify_totp("secret", "000000")
        assert result is False


class TestGenerateQRCode:
    """Test suite for generate_qr_code function."""

    @patch("profile.utils.qrcode.QRCode")
    @patch("profile.utils.pyotp.TOTP")
    def test_generates_qr_code(self, mock_totp_class, mock_qr_class):
        mock_totp = MagicMock()
        mock_totp.provisioning_uri.return_value = "otpauth://totp/Endurain:testuser?secret=SECRET"
        mock_totp_class.return_value = mock_totp

        mock_qr = MagicMock()
        mock_qr_class.return_value = mock_qr

        mock_img = MagicMock()
        mock_qr.make_image.return_value = mock_img

        mock_img.save = MagicMock()

        with patch("profile.utils.BytesIO") as mock_bytesio:
            mock_buffer = MagicMock()
            mock_bytesio.return_value = mock_buffer
            mock_buffer.getvalue.return_value = b"png_data"

            with patch("profile.utils.base64.b64encode") as mock_b64:
                mock_b64.return_value = b"cG5nX2RhdGE="
                result = profile_utils.generate_qr_code("SECRET", "testuser")

        assert result == "data:image/png;base64,cG5nX2RhdGE="
        mock_totp.provisioning_uri.assert_called_once_with(name="testuser", issuer_name="Endurain")
        mock_qr.add_data.assert_called_once_with("otpauth://totp/Endurain:testuser?secret=SECRET")
        mock_qr.make.assert_called_once_with(fit=True)

    @patch("profile.utils.pyotp.TOTP")
    def test_generates_qr_code_with_custom_app_name(self, mock_totp_class):
        mock_totp = MagicMock()
        mock_totp.provisioning_uri.return_value = "otpauth://totp/CustomApp:testuser?secret=SECRET"
        mock_totp_class.return_value = mock_totp

        with patch("profile.utils.qrcode.QRCode") as mock_qr_class:
            mock_qr = MagicMock()
            mock_qr_class.return_value = mock_qr
            mock_img = MagicMock()
            mock_qr.make_image.return_value = mock_img

            with patch("profile.utils.BytesIO") as mock_bytesio:
                mock_buffer = MagicMock()
                mock_bytesio.return_value = mock_buffer
                mock_buffer.getvalue.return_value = b"png_data"

                with patch("profile.utils.base64.b64encode") as mock_b64:
                    mock_b64.return_value = b"cG5nX2RhdGE="
                    result = profile_utils.generate_qr_code("SECRET", "testuser", "CustomApp")

        mock_totp.provisioning_uri.assert_called_once_with(name="testuser", issuer_name="CustomApp")
        assert "data:image/png;base64" in result


class TestSetupUserMFA:
    """Test suite for setup_user_mfa function."""

    @patch("profile.utils.generate_qr_code")
    @patch("profile.utils.generate_totp_secret")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_successful_setup(self, mock_get_user, mock_gen_secret, mock_gen_qr):
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.auth_mfa = None
        mock_get_user.return_value = mock_user
        mock_gen_secret.return_value = "NEWSECRET"
        mock_gen_qr.return_value = "data:image/png;base64,QRCODE"

        result = profile_utils.setup_user_mfa(1, MagicMock())

        assert result.secret == "NEWSECRET"
        assert result.qr_code == "data:image/png;base64,QRCODE"
        assert result.app_name == "Endurain"
        mock_gen_qr.assert_called_once_with("NEWSECRET", "testuser")

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_user_not_found(self, mock_get_user):
        mock_get_user.return_value = None

        with pytest.raises(Exception) as exc_info:
            profile_utils.setup_user_mfa(1, MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 404

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_already_enabled(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_get_user.return_value = mock_user

        with pytest.raises(Exception) as exc_info:
            profile_utils.setup_user_mfa(1, MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 400


class TestEnableUserMFA:
    """Test suite for enable_user_mfa function."""

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.encrypt_token_fernet")
    @patch("profile.utils.users_crud.update_user_mfa")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_successful_enable(self, mock_get_user, mock_update_mfa, mock_encrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa = None
        mock_get_user.return_value = mock_user
        mock_encrypt.return_value = "encrypted_secret"
        mock_verify.return_value = True

        mock_identity_service = MagicMock()
        mock_identity_service.create_mfa_backup_codes.return_value = ["CODE1", "CODE2"]

        result = profile_utils.enable_user_mfa(1, "secret", "123456", mock_identity_service, MagicMock())

        assert result == ["CODE1", "CODE2"]
        mock_update_mfa.assert_called_once()
        mock_identity_service.create_mfa_backup_codes.assert_called_once_with(1)

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_user_not_found(self, mock_get_user):
        mock_get_user.return_value = None

        with pytest.raises(Exception) as exc_info:
            profile_utils.enable_user_mfa(1, "secret", "123456", MagicMock(), MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 404

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_already_enabled(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_get_user.return_value = mock_user

        with pytest.raises(Exception) as exc_info:
            profile_utils.enable_user_mfa(1, "secret", "123456", MagicMock(), MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 400

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_invalid_mfa_code(self, mock_get_user, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa = None
        mock_get_user.return_value = mock_user
        mock_verify.return_value = False

        with pytest.raises(Exception) as exc_info:
            profile_utils.enable_user_mfa(1, "secret", "000000", MagicMock(), MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 400

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.encrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_encryption_failure(self, mock_get_user, mock_encrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa = None
        mock_get_user.return_value = mock_user
        mock_encrypt.return_value = None
        mock_verify.return_value = True

        with pytest.raises(Exception) as exc_info:
            profile_utils.enable_user_mfa(1, "secret", "123456", MagicMock(), MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 500


class TestDisableUserMFA:
    """Test suite for disable_user_mfa function."""

    @patch("profile.utils.mfa_backup_codes_crud.delete_user_backup_codes")
    @patch("profile.utils.users_crud.update_user_mfa")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_successful_disable(self, mock_get_user, mock_update_mfa, mock_delete_codes):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_get_user.return_value = mock_user

        profile_utils.disable_user_mfa(1, MagicMock())
        mock_update_mfa.assert_called_once_with(1, mock_update_mfa._mock_mock_calls[0][1][1])
        mock_delete_codes.assert_called_once()

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_user_not_found(self, mock_get_user):
        mock_get_user.return_value = None

        with pytest.raises(Exception) as exc_info:
            profile_utils.disable_user_mfa(1, MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 404

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_not_enabled(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = False
        mock_get_user.return_value = mock_user

        with pytest.raises(Exception) as exc_info:
            profile_utils.disable_user_mfa(1, MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 400


class TestVerifyUserMFA:
    """Test suite for verify_user_mfa function."""

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.decrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_totp_verification_success(self, mock_get_user, mock_decrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user
        mock_decrypt.return_value = "decrypted_secret"
        mock_verify.return_value = True

        result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())
        assert result is True
        mock_decrypt.assert_called_once_with("encrypted_secret")
        mock_verify.assert_called_once_with("decrypted_secret", "123456")

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.decrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_totp_verify_value_error_returns_false(self, mock_get_user, mock_decrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user
        mock_decrypt.return_value = "decrypted_secret"
        mock_verify.side_effect = ValueError("invalid token")

        with patch("profile.utils.pyotp.OTPError", Exception, create=True):
            result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())
        assert result is False

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.decrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_totp_verify_generic_exception_returns_false(self, mock_get_user, mock_decrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user
        mock_decrypt.return_value = "decrypted_secret"
        mock_verify.side_effect = RuntimeError("unexpected error")

        with patch("profile.utils.pyotp.OTPError", ValueError, create=True):
            result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())
        assert result is False

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_user_not_found(self, mock_get_user):
        mock_get_user.return_value = None

        with pytest.raises(Exception) as exc_info:
            profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())

        assert exc_info.typename == "HTTPException"
        assert exc_info.value.status_code == 404

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_not_enabled_returns_false(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa = None
        mock_get_user.return_value = mock_user

        result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())
        assert result is False

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_disabled_returns_false(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = False
        mock_get_user.return_value = mock_user

        result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())
        assert result is False

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_no_secret_returns_false(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = None
        mock_get_user.return_value = mock_user

        result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())
        assert result is False

    @patch("profile.utils.core_cryptography.decrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_totp_decrypt_failure_returns_false(self, mock_get_user, mock_decrypt):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user
        mock_decrypt.return_value = None

        result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), MagicMock())
        assert result is False

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.decrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_backup_code_verification_success(self, mock_get_user, mock_decrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user
        mock_verify.return_value = False

        mock_identity_service = MagicMock()
        mock_identity_service.verify_and_consume_mfa_backup_code.return_value = True

        result = profile_utils.verify_user_mfa(1, "ABCD-EFGH", mock_identity_service, MagicMock())
        assert result is True
        mock_identity_service.verify_and_consume_mfa_backup_code.assert_called_once_with(1, "ABCD-EFGH")

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.decrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_backup_code_verification_failure_returns_false(self, mock_get_user, mock_decrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user
        mock_verify.return_value = False

        mock_identity_service = MagicMock()
        mock_identity_service.verify_and_consume_mfa_backup_code.return_value = False

        result = profile_utils.verify_user_mfa(1, "ABCD-EFGH", mock_identity_service, MagicMock())
        assert result is False

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_invalid_code_format_returns_false(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user

        result = profile_utils.verify_user_mfa(1, "invalid", MagicMock(), MagicMock())
        assert result is False

    @patch("profile.utils.verify_totp")
    @patch("profile.utils.core_cryptography.decrypt_token_fernet")
    @patch("profile.utils.users_crud.get_user_by_id")
    def test_backup_code_exception_returns_false(self, mock_get_user, mock_decrypt, mock_verify):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "encrypted_secret"
        mock_get_user.return_value = mock_user
        mock_verify.return_value = False

        mock_identity_service = MagicMock()
        mock_identity_service.verify_and_consume_mfa_backup_code.side_effect = Exception("service error")

        result = profile_utils.verify_user_mfa(1, "ABCD-EFGH", mock_identity_service, MagicMock())
        assert result is False


class TestIsMFAEnabledForUser:
    """Test suite for is_mfa_enabled_for_user function."""

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_enabled(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = "secret"
        mock_get_user.return_value = mock_user

        result = profile_utils.is_mfa_enabled_for_user(1, MagicMock())
        assert result is True

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_user_not_found_returns_false(self, mock_get_user):
        mock_get_user.return_value = None

        result = profile_utils.is_mfa_enabled_for_user(1, MagicMock())
        assert result is False

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_not_enabled_returns_false(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa = None
        mock_get_user.return_value = mock_user

        result = profile_utils.is_mfa_enabled_for_user(1, MagicMock())
        assert result is False

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_disabled_returns_false(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = False
        mock_get_user.return_value = mock_user

        result = profile_utils.is_mfa_enabled_for_user(1, MagicMock())
        assert result is False

    @patch("profile.utils.users_crud.get_user_by_id")
    def test_mfa_no_secret_returns_false(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.auth_mfa.mfa_enabled = True
        mock_user.auth_mfa.mfa_secret = None
        mock_get_user.return_value = mock_user

        result = profile_utils.is_mfa_enabled_for_user(1, MagicMock())
        assert result is False


class TestSQLAlchemyObjToDict:
    """Test suite for sqlalchemy_obj_to_dict function."""

    def test_with_sqlalchemy_object(self):
        col_id = MagicMock()
        col_id.name = "id"
        col_name = MagicMock()
        col_name.name = "name"

        table_mock = MagicMock()
        table_mock.columns.__iter__.return_value = iter([col_id, col_name])

        obj = MagicMock()
        obj.__table__ = table_mock
        obj.id = 1
        obj.name = "Test"

        result = profile_utils.sqlalchemy_obj_to_dict(obj)
        assert result == {"id": 1, "name": "Test"}

    def test_without_table_attribute(self):
        result = profile_utils.sqlalchemy_obj_to_dict("not_an_sa_obj")
        assert result == "not_an_sa_obj"

    def test_with_dict(self):
        result = profile_utils.sqlalchemy_obj_to_dict({"key": "value"})
        assert result == {"key": "value"}


class TestWriteJsonToZip:
    """Test suite for write_json_to_zip function."""

    def test_with_data_list(self):
        mock_zip = MagicMock()
        counts = {}

        profile_utils.write_json_to_zip(mock_zip, "activities/data.json", [{"id": 1}], counts)

        assert counts["data"] == 1
        mock_zip.writestr.assert_called_once()
        args = mock_zip.writestr.call_args[0]
        assert args[0] == "activities/data.json"

    def test_with_data_dict(self):
        mock_zip = MagicMock()
        counts = {}

        profile_utils.write_json_to_zip(mock_zip, "user/profile.json", {"name": "test"}, counts)

        assert counts["profile"] == 1

    def test_with_empty_data(self):
        mock_zip = MagicMock()
        counts = {}

        profile_utils.write_json_to_zip(mock_zip, "activities/data.json", {}, counts)

        assert "data" not in counts
        mock_zip.writestr.assert_not_called()

    def test_with_none_data(self):
        mock_zip = MagicMock()
        counts = {}

        profile_utils.write_json_to_zip(mock_zip, "activities/data.json", None, counts)

        assert "data" not in counts
        mock_zip.writestr.assert_not_called()


class TestCheckTimeout:
    """Test suite for check_timeout function."""

    @patch("profile.utils.time.time")
    def test_timeout_not_exceeded(self, mock_time):
        mock_time.return_value = 5.0

        profile_utils.check_timeout(10, 0.0, TimeoutError, "test")

    @patch("profile.utils.time.time")
    def test_timeout_exceeded(self, mock_time):
        mock_time.return_value = 15.0

        with pytest.raises(TimeoutError, match="test exceeded 10 seconds"):
            profile_utils.check_timeout(10, 0.0, TimeoutError, "test")

    def test_timeout_none_skips_check(self):
        profile_utils.check_timeout(None, 0.0, TimeoutError, "test")


class TestGetMemoryUsageMB:
    """Test suite for get_memory_usage_mb function."""

    @patch("profile.utils.psutil.Process")
    def test_returns_memory_usage(self, mock_process):
        mock_proc = MagicMock()
        mock_proc.memory_info.return_value.rss = 104857600
        mock_process.return_value = mock_proc

        result = profile_utils.get_memory_usage_mb(True)
        assert result == 100.0

    @patch("profile.utils.psutil.Process")
    def test_monitoring_disabled_returns_zero(self, mock_process):
        result = profile_utils.get_memory_usage_mb(False)
        assert result == 0.0
        mock_process.assert_not_called()

    @patch("profile.utils.psutil.Process")
    def test_exception_returns_zero(self, mock_process):
        mock_process.side_effect = Exception("process error")

        result = profile_utils.get_memory_usage_mb(True)
        assert result == 0.0


class TestCheckMemoryUsage:
    """Test suite for check_memory_usage function."""

    @patch("profile.utils.get_memory_usage_mb")
    def test_memory_within_limits(self, mock_get_memory):
        mock_get_memory.return_value = 500.0

        profile_utils.check_memory_usage("export", 1024)

    @patch("profile.utils.get_memory_usage_mb")
    def test_memory_exceeds_limit(self, mock_get_memory):
        mock_get_memory.return_value = 1100.0

        with pytest.raises(MemoryAllocationError):
            profile_utils.check_memory_usage("export", 1024)

    @patch("profile.utils.get_memory_usage_mb")
    def test_monitoring_disabled_skips_check(self, mock_get_memory):
        profile_utils.check_memory_usage("export", 1024, enable_monitoring=False)
        mock_get_memory.assert_not_called()

    @patch("profile.utils.get_memory_usage_mb")
    def test_memory_intensive_operation_higher_threshold(self, mock_get_memory):
        mock_get_memory.return_value = 1500.0

        profile_utils.check_memory_usage("data collection export", 1024)

    @patch("profile.utils.get_memory_usage_mb")
    def test_memory_intensive_operation_still_exceeds(self, mock_get_memory):
        mock_get_memory.return_value = 2000.0

        with pytest.raises(MemoryAllocationError):
            profile_utils.check_memory_usage("data collection export", 1024)

    @patch("profile.utils.get_memory_usage_mb")
    def test_custom_memory_intensive_operations_still_exceeds(self, mock_get_memory):
        mock_get_memory.return_value = 2000.0

        with pytest.raises(MemoryAllocationError):
            profile_utils.check_memory_usage("custom operation", 1024, memory_intensive_operations=["custom operation"])

    @patch("profile.utils.get_memory_usage_mb")
    def test_custom_ops_not_matched_raises_at_normal_limit(self, mock_get_memory):
        mock_get_memory.return_value = 1100.0

        with pytest.raises(MemoryAllocationError):
            profile_utils.check_memory_usage("random task", 1024, memory_intensive_operations=["specific op"])


class TestInitializeOperationCounts:
    """Test suite for initialize_operation_counts function."""

    def test_all_counts_initialized_to_zero(self):
        counts = profile_utils.initialize_operation_counts()
        assert counts["media"] == 0
        assert counts["activities"] == 0
        assert counts["user"] == 0
        assert len(counts) == 21

    def test_with_user_count(self):
        counts = profile_utils.initialize_operation_counts(include_user_count=True)
        assert counts["user"] == 1

    def test_all_expected_keys_present(self):
        counts = profile_utils.initialize_operation_counts()
        expected_keys = {
            "media",
            "activity_files",
            "activities",
            "activity_laps",
            "activity_sets",
            "activity_streams",
            "activity_workout_steps",
            "activity_media",
            "activity_exercise_titles",
            "gears",
            "gear_components",
            "health_weight",
            "health_targets",
            "notifications",
            "user_images",
            "user",
            "user_default_gear",
            "user_goals",
            "user_identity_providers",
            "user_integrations",
            "user_privacy_settings",
        }
        assert set(counts.keys()) == expected_keys


class TestDetectSystemMemoryTier:
    """Test suite for detect_system_memory_tier function."""

    @patch("profile.utils.psutil.virtual_memory")
    def test_high_tier(self, mock_vm):
        mock_mem = MagicMock()
        mock_mem.available = 3000 * 1024 * 1024
        mock_vm.return_value = mock_mem

        tier, mb = profile_utils.detect_system_memory_tier()
        assert tier == "high"
        assert mb == 3000

    @patch("profile.utils.psutil.virtual_memory")
    def test_medium_tier(self, mock_vm):
        mock_mem = MagicMock()
        mock_mem.available = 1500 * 1024 * 1024
        mock_vm.return_value = mock_mem

        tier, mb = profile_utils.detect_system_memory_tier()
        assert tier == "medium"
        assert mb == 1500

    @patch("profile.utils.psutil.virtual_memory")
    def test_low_tier(self, mock_vm):
        mock_mem = MagicMock()
        mock_mem.available = 500 * 1024 * 1024
        mock_vm.return_value = mock_mem

        tier, mb = profile_utils.detect_system_memory_tier()
        assert tier == "low"
        assert mb == 500

    @patch("profile.utils.psutil.virtual_memory")
    def test_exception_defaults_to_medium(self, mock_vm):
        mock_vm.side_effect = Exception("memory detection failed")

        tier, mb = profile_utils.detect_system_memory_tier()
        assert tier == "medium"
        assert mb == 1024
