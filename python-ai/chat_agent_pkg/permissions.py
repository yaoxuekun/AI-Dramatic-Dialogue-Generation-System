# 角色权限校验模块
# 本文件定义用户角色等级和权限校验逻辑。
# 角色分为三级：ROOT（超级管理员）> ADMIN（管理员）> USER（普通用户）

# 角色等级映射表：角色名 → 数值等级，数值越大权限越高
ROLE_LEVELS = {
    "USER": 1,   # 普通用户：可使用漫剧和对话功能
    "ADMIN": 2,  # 管理员：可管理大纲配置和 Prompt
    "ROOT": 3,   # 超级管理员：可管理用户权限
}


def normalize_role(role: str | None) -> str:
    """将角色名归一化为大写格式。

    如果角色为空或不在 ROLE_LEVELS 中，返回 "USER"。

    Args:
        role: 原始角色名，可能为 None 或大小写不一致。

    Returns:
        str: 归一化后的角色名，如 "USER"、"ADMIN"、"ROOT"。
    """
    # 转大写并去除空白
    normalized = (role or "USER").strip().upper()

    # 如果不在等级表中，降级为 USER
    return normalized if normalized in ROLE_LEVELS else "USER"


def has_permission(user_role: str | None, required_role: str | None) -> bool:
    """判断用户是否有足够的权限执行操作。

    比较用户角色等级和所需角色等级，用户等级 >= 所需等级则有权限。

    Args:
        user_role:    用户当前角色。
        required_role: 操作所需的最低角色。

    Returns:
        bool: 有权限返回 True，否则返回 False。
    """
    # 获取用户等级，默认为 USER（1）
    user_level = ROLE_LEVELS.get(normalize_role(user_role), 1)

    # 获取所需等级，默认为 USER（1）
    required_level = ROLE_LEVELS.get(normalize_role(required_role), 1)

    # 用户等级 >= 所需等级则有权限
    return user_level >= required_level


def module_required_role(module: str | None) -> str:
    """获取指定模块所需的最低角色。

    不同模块有不同的权限要求：
    - user_permission: 需要 ROOT（只有超级管理员可管理用户权限）
    - outline_config、prompt_management: 需要 ADMIN（管理员可管理配置和提示词）
    - 其他模块: 需要 USER（普通用户即可使用）

    Args:
        module: 模块名。

    Returns:
        str: 所需的最低角色名。
    """
    # 归一化模块名
    module_name = (module or "general").strip().lower()

    # 用户权限和功能权限模块需要 ROOT
    if module_name in {"user_permission", "feature_permission"}:
        return "ROOT"

    # 大纲配置和 Prompt 管理需要 ADMIN
    if module_name in {"outline_config", "prompt_management"}:
        return "ADMIN"

    # 其他模块只需 USER
    return "USER"
