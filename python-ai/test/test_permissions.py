"""chat_agent_pkg/permissions.py 单元测试。

测试角色归一化、权限校验和模块权限映射。
"""
from chat_agent_pkg.permissions import has_permission, module_required_role, normalize_role


class TestNormalizeRole:
    """normalize_role 函数测试。"""

    def test_none_returns_user(self):
        assert normalize_role(None) == "USER"

    def test_empty_string_returns_user(self):
        assert normalize_role("") == "USER"

    def test_whitespace_only_returns_user(self):
        assert normalize_role("   ") == "USER"

    def test_lowercase_admin(self):
        assert normalize_role("admin") == "ADMIN"

    def test_uppercase_admin(self):
        assert normalize_role("ADMIN") == "ADMIN"

    def test_mixed_case_root(self):
        assert normalize_role("Root") == "ROOT"

    def test_invalid_role_returns_user(self):
        assert normalize_role("superadmin") == "USER"

    def test_whitespace_trimmed(self):
        assert normalize_role("  ADMIN  ") == "ADMIN"

    def test_user_role(self):
        assert normalize_role("USER") == "USER"


class TestHasPermission:
    """has_permission 函数测试。"""

    def test_user_has_user_permission(self):
        assert has_permission("USER", "USER") is True

    def test_admin_has_user_permission(self):
        assert has_permission("ADMIN", "USER") is True

    def test_root_has_user_permission(self):
        assert has_permission("ROOT", "USER") is True

    def test_user_lacks_admin_permission(self):
        assert has_permission("USER", "ADMIN") is False

    def test_admin_has_admin_permission(self):
        assert has_permission("ADMIN", "ADMIN") is True

    def test_root_has_admin_permission(self):
        assert has_permission("ROOT", "ADMIN") is True

    def test_user_lacks_root_permission(self):
        assert has_permission("USER", "ROOT") is False

    def test_admin_lacks_root_permission(self):
        assert has_permission("ADMIN", "ROOT") is False

    def test_root_has_root_permission(self):
        assert has_permission("ROOT", "ROOT") is True

    def test_none_user_treated_as_user(self):
        assert has_permission(None, "USER") is True
        assert has_permission(None, "ADMIN") is False

    def test_none_required_treated_as_user(self):
        assert has_permission("USER", None) is True

    def test_both_none(self):
        assert has_permission(None, None) is True

    def test_invalid_roles_default_to_user(self):
        assert has_permission("invalid", "ADMIN") is False
        assert has_permission("ADMIN", "invalid") is True


class TestModuleRequiredRole:
    """module_required_role 函数测试。"""

    def test_user_permission_requires_root(self):
        assert module_required_role("user_permission") == "ROOT"

    def test_outline_config_requires_admin(self):
        assert module_required_role("outline_config") == "ADMIN"

    def test_prompt_management_requires_admin(self):
        assert module_required_role("prompt_management") == "ADMIN"

    def test_feature_permission_requires_root(self):
        assert module_required_role("feature_permission") == "ROOT"

    def test_manga_requires_user(self):
        assert module_required_role("manga") == "USER"

    def test_general_requires_user(self):
        assert module_required_role("general") == "USER"

    def test_none_module_requires_user(self):
        assert module_required_role(None) == "USER"

    def test_unknown_module_requires_user(self):
        assert module_required_role("unknown_module") == "USER"

    def test_case_insensitive(self):
        assert module_required_role("USER_PERMISSION") == "ROOT"
        assert module_required_role("Manga") == "USER"
