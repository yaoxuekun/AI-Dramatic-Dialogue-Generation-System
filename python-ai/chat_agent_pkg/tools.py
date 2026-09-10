# LangChain Tool 定义模块
# 本文件定义各业务模块的 LangChain Tool，供 ReAct Agent 选择使用。
# 每个 Tool 对应一个 Java 后端方法，Agent 选择 Tool 后会返回方法名和参数。
#
# 工具分类：
# - 系统工具：ask_missing_info（询问缺失信息）、deny_permission（权限不足提示）
# - 漫剧工具：story_list、story_detail、story_generate_outline 等
# - 大纲配置工具：outline_config_list、outline_config_create 等
# - Prompt 管理工具：prompt_list、prompt_create 等
# - 用户权限工具：user_list、user_update_role

# json：用于 JSON 序列化和反序列化
import json

# collections.able.Callable：用于声明工厂函数类型
from collections.abc import Callable

# typing.Any：用于声明动态类型
from typing import Any

# LangChain Tool 类
from langchain_core.tools import Tool


def to_json(data: dict[str, Any]) -> str:
    """将字典序列化为 JSON 字符串。

    Args:
        data: 要序列化的字典。

    Returns:
        str: JSON 字符串。
    """
    return json.dumps(data, ensure_ascii=False)


def parse_tool_input(raw_input: str) -> dict[str, Any]:
    """解析 Tool 的输入参数。

    输入可能是 JSON 字符串或普通文本，统一解析为字典。

    Args:
        raw_input: 原始输入字符串。

    Returns:
        dict: 解析后的参数字典。
    """
    if not raw_input:
        return {}

    # 如果已经是字典，直接返回
    if isinstance(raw_input, dict):
        return raw_input

    # 尝试 JSON 解析
    try:
        parsed = json.loads(raw_input)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        # 解析失败，将原始文本作为 rawText 返回
        return {"rawText": str(raw_input)}


def ask_missing_info(raw_input: str) -> str:
    """系统工具：询问用户补充缺失信息。

    当 Agent 判断用户输入缺少必要信息时调用此工具。

    Args:
        raw_input: JSON 字符串，包含 missingInfo 数组和可选的 question。

    Returns:
        str: JSON 格式的执行结果。
    """
    data = parse_tool_input(raw_input)

    # 提取缺失信息列表
    missing = data.get("missingInfo") or data.get("missing") or []
    if isinstance(missing, str):
        missing = [missing]

    # 提取询问消息
    question = data.get("question") or data.get("assistantMessage")
    if not question:
        question = "还缺少一些必要信息，请补充：" + "、".join(missing or ["必要参数"])

    return to_json({
        "javaMethod": "story.none",      # 不执行 Java 方法
        "javaMethodArgs": {},             # 无参数
        "assistantMessage": question,     # 询问消息
        "missingInfo": missing,           # 缺失信息列表
    })


def deny_permission(raw_input: str) -> str:
    """系统工具：提示用户权限不足。

    当 Agent 判断用户权限不足以执行操作时调用此工具。

    Args:
        raw_input: JSON 字符串，包含 requiredPermission。

    Returns:
        str: JSON 格式的执行结果。
    """
    data = parse_tool_input(raw_input)

    # 提取所需权限
    required = data.get("requiredPermission") or data.get("requiredRole") or "更高权限"

    return to_json({
        "javaMethod": "story.none",      # 不执行 Java 方法
        "javaMethodArgs": {},             # 无参数
        "assistantMessage": f"当前账号没有执行该操作的权限，需要 {required} 权限。",
        "missingInfo": [],
    })


def make_action_tool(
        name: str,
        description: str,
        java_method: str,
        required_fields: list[str] | None = None,
        optional_fields: list[str] | None = None,
        aliases: dict[str, str] | None = None,
) -> Tool:
    """创建业务动作 Tool 工厂函数。

    每个 Tool 对应一个 Java 方法，Agent 选择 Tool 后会：
    1. 解析输入参数
    2. 校验必填字段
    3. 返回 Java 方法名和参数

    Args:
        name:            工具名称。
        description:     工具描述，Agent 根据描述选择工具。
        java_method:     对应的 Java 方法名。
        required_fields: 必填字段列表。
        optional_fields: 可选字段列表。
        aliases:         字段别名映射，如 {"id": "storyId"}。

    Returns:
        Tool: LangChain Tool 实例。
    """
    required = required_fields or []
    optional = optional_fields or []
    field_aliases = aliases or {}

    def run(raw_input: str) -> str:
        """Tool 执行函数。

        Args:
            raw_input: JSON 格式的输入参数。

        Returns:
            str: JSON 格式的执行结果。
        """
        # 解析输入
        data = parse_tool_input(raw_input)

        # 归一化参数（处理别名）
        normalized = normalize_args(data, field_aliases)

        # 校验必填字段
        missing = [field for field in required if is_blank(normalized.get(field))]
        if missing:
            return to_json({
                "javaMethod": "story.none",
                "javaMethodArgs": {},
                "assistantMessage": "执行这个操作还缺少：" + "、".join(missing) + "。请补充后我会继续。",
                "missingInfo": missing,
            })

        # 提取参数（只保留 required + optional 中定义的字段）
        args = {
            field: normalized.get(field)
            for field in required + optional
            if normalized.get(field) is not None
        }

        return to_json({
            "javaMethod": java_method,       # Java 方法名
            "javaMethodArgs": args,           # 方法参数
            "assistantMessage": "我已经准备好执行该操作。",
            "missingInfo": [],
        })

    # 创建 LangChain Tool
    return Tool.from_function(
        name=name,
        description=description,
        func=run,
    )


def normalize_args(data: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
    """归一化参数，处理字段别名。

    如果源字段存在但目标字段不存在，将源字段的值复制到目标字段。

    Args:
        data:    原始参数字典。
        aliases: 别名映射，如 {"id": "storyId"}。

    Returns:
        dict: 归一化后的参数字典。
    """
    normalized = dict(data)
    for source, target in aliases.items():
        if source in normalized and target not in normalized:
            normalized[target] = normalized[source]
    return normalized


def is_blank(value: Any) -> bool:
    """判断值是否为空（None 或空字符串）。

    Args:
        value: 要判断的值。

    Returns:
        bool: 为空返回 True。
    """
    return value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value)


# ── 系统工具 ──────────────────────────────────────────────────────────

def system_tools() -> list[Tool]:
    """获取系统工具列表。

    系统工具包括：
    - ask_missing_info: 询问用户补充缺失信息
    - deny_permission: 提示用户权限不足

    Returns:
        list[Tool]: 系统工具列表。
    """
    return [
        Tool.from_function(
            name="ask_missing_info",
            description="缺少必要信息时使用。输入 JSON：missingInfo 字符串数组，question 可选。",
            func=ask_missing_info,
        ),
        Tool.from_function(
            name="deny_permission",
            description="用户权限不足时使用。输入 JSON：requiredPermission。",
            func=deny_permission,
        ),
    ]


# ── 漫剧工具 ──────────────────────────────────────────────────────────

def manga_tools() -> list[Tool]:
    """获取漫剧模块工具列表。

    包含漫剧的增删改查、大纲生成/修改、分卷/小节/资产/脚本生成等操作。

    Returns:
        list[Tool]: 漫剧工具列表。
    """
    return system_tools() + [
        make_action_tool(
            "story_list",
            "查询当前用户的漫剧列表。输入 JSON：page 可选，size 可选。",
            "story.list",
            optional_fields=["page", "size"],
        ),
        make_action_tool(
            "story_detail",
            "查询指定漫剧详情。输入 JSON：storyId 必填。",
            "story.detail",
            required_fields=["storyId"],
            aliases={"id": "storyId"},
        ),
        make_action_tool(
            "story_generate_outline",
            "生成新的漫剧剧情大纲并录入数据库。输入 JSON：genre 必填，style 必填，plot 可选。",
            "story.generate",
            required_fields=["genre", "style"],
            optional_fields=["plot"],
            aliases={"theme": "genre", "storyStyle": "style"},
        ),
        make_action_tool(
            "story_update_basic",
            "修改漫剧基础信息。输入 JSON：storyId 必填，title/genre/style/synopsis 可选。",
            "story.updateBasic",
            required_fields=["storyId"],
            optional_fields=["title", "genre", "style", "synopsis"],
        ),
        make_action_tool(
            "story_update_detail",
            "手动保存漫剧摘要、大纲或角色设定。输入 JSON：storyId 必填，synopsis/fullContent/characters 可选。",
            "story.updateDetail",
            required_fields=["storyId"],
            optional_fields=["synopsis", "fullContent", "characters"],
        ),
        make_action_tool(
            "story_revise_outline",
            "根据修改意见自动修改剧情大纲。输入 JSON：storyId 必填，suggestion 必填。",
            "story.reviseOutline",
            required_fields=["storyId", "suggestion"],
        ),
        make_action_tool(
            "story_generate_volume_outline",
            "为指定漫剧生成分卷大纲。输入 JSON：storyId 必填。",
            "story.generateVolumeOutline",
            required_fields=["storyId"],
        ),
        make_action_tool(
            "story_revise_volume_outline",
            "根据意见自动修改分卷大纲。输入 JSON：storyId 必填，suggestion 必填。",
            "story.reviseVolumeOutline",
            required_fields=["storyId", "suggestion"],
        ),
        make_action_tool(
            "story_generate_volume_sections",
            "根据某卷分卷大纲生成小节故事。输入 JSON：storyId 必填，volumeId 必填。",
            "story.generateVolumeSections",
            required_fields=["storyId", "volumeId"],
        ),
        make_action_tool(
            "story_generate_section_assets",
            "根据小节故事生成或复用人物/场景图片资产。输入 JSON：storyId 必填，sectionId 必填。",
            "story.generateSectionAssets",
            required_fields=["storyId", "sectionId"],
        ),
        make_action_tool(
            "story_generate_section_script",
            "根据小节故事生成分镜故事脚本。输入 JSON：storyId 必填，sectionId 必填。",
            "story.generateSectionScript",
            required_fields=["storyId", "sectionId"],
        ),
        make_action_tool(
            "story_delete",
            "删除指定漫剧。输入 JSON：storyId 必填。",
            "story.delete",
            required_fields=["storyId"],
        ),
    ]


# ── 大纲配置工具 ──────────────────────────────────────────────────────

def outline_config_tools() -> list[Tool]:
    """获取大纲配置模块工具列表。

    包含题材和漫剧风格配置的增删改查操作。

    Returns:
        list[Tool]: 大纲配置工具列表。
    """
    return system_tools() + [
        make_action_tool(
            "outline_config_list",
            "查询大纲配置。输入 JSON：type 可选 GENRE/STYLE，enabled 可选。",
            "outlineConfig.list",
            optional_fields=["type", "enabled"],
            aliases={"optionType": "type"},
        ),
        make_action_tool(
            "outline_config_create",
            "新增题材或漫剧风格配置。输入 JSON：type 必填 GENRE/STYLE，name 必填，description/sortOrder/enabled 可选。",
            "outlineConfig.create",
            required_fields=["type", "name"],
            optional_fields=["description", "sortOrder", "enabled"],
            aliases={"optionType": "type", "optionName": "name"},
        ),
        make_action_tool(
            "outline_config_update",
            "修改题材或漫剧风格配置。输入 JSON：id 必填，type 必填，name 必填，description/sortOrder/enabled 可选。",
            "outlineConfig.update",
            required_fields=["id", "type", "name"],
            optional_fields=["description", "sortOrder", "enabled"],
            aliases={"optionId": "id", "optionType": "type", "optionName": "name"},
        ),
        make_action_tool(
            "outline_config_delete",
            "删除题材或漫剧风格配置。输入 JSON：id 必填。",
            "outlineConfig.delete",
            required_fields=["id"],
            aliases={"optionId": "id"},
        ),
    ]


# ── Prompt 管理工具 ──────────────────────────────────────────────────

def prompt_management_tools() -> list[Tool]:
    """获取 Prompt 管理模块工具列表。

    包含 Prompt 的增删改查和默认/特定配置操作。

    Returns:
        list[Tool]: Prompt 管理工具列表。
    """
    return system_tools() + [
        make_action_tool(
            "prompt_list",
            "查询 Prompt 列表。输入 JSON：category/enabled/keyword 可选。",
            "prompt.list",
            optional_fields=["category", "enabled", "keyword"],
        ),
        make_action_tool(
            "prompt_detail",
            "查询 Prompt 详情。输入 JSON：id 必填。",
            "prompt.detail",
            required_fields=["id"],
            aliases={"promptId": "id"},
        ),
        make_action_tool(
            "prompt_create",
            "新增 Prompt。输入 JSON：promptKey、promptName、templateContent 必填；promptScope/basePromptKey/matchGenre/matchStyle/priority/category/description/enabled/parameters 可选。",
            "prompt.create",
            required_fields=["promptKey", "promptName", "templateContent"],
            optional_fields=[
                "promptScope", "basePromptKey", "matchGenre", "matchStyle", "priority",
                "category", "description", "enabled", "parameters",
            ],
        ),
        make_action_tool(
            "prompt_update",
            "修改 Prompt。输入 JSON：id、promptKey、promptName、templateContent 必填；其他字段同新增。",
            "prompt.update",
            required_fields=["id", "promptKey", "promptName", "templateContent"],
            optional_fields=[
                "promptScope", "basePromptKey", "matchGenre", "matchStyle", "priority",
                "category", "description", "enabled", "parameters",
            ],
            aliases={"promptId": "id"},
        ),
        make_action_tool(
            "prompt_delete",
            "删除 Prompt。输入 JSON：id 必填。",
            "prompt.delete",
            required_fields=["id"],
            aliases={"promptId": "id"},
        ),
    ]


# ── 用户权限工具 ──────────────────────────────────────────────────────

def user_permission_tools() -> list[Tool]:
    """获取用户权限模块工具列表。

    包含用户列表查询和权限等级修改操作。

    Returns:
        list[Tool]: 用户权限工具列表。
    """
    return system_tools() + [
        make_action_tool(
            "user_list",
            "查询用户及权限列表。输入 JSON 可以为空。",
            "user.list",
        ),
        make_action_tool(
            "user_update_role",
            "修改用户权限等级。输入 JSON：targetUserId 必填，role 必填，role 只能是 ROOT/ADMIN/USER。",
            "user.updateRole",
            required_fields=["targetUserId", "role"],
            aliases={"userId": "targetUserId", "id": "targetUserId"},
        ),
    ]


def feature_permission_update(raw_input: str) -> str:
    """构造功能权限更新动作。

    调用方：feature_permission_tools。
    """
    data = parse_tool_input(raw_input)
    normalized = normalize_args(
        data,
        {
            "key": "featureKey",
            "permissionKey": "featureKey",
            "featureId": "id",
            "roles": "allowedRoles",
            "roleList": "allowedRoles",
        },
    )

    missing = []
    if is_blank(normalized.get("id")) and is_blank(normalized.get("featureKey")):
        missing.append("featureKey or id")
    if is_blank(normalized.get("allowedRoles")):
        missing.append("allowedRoles")

    if missing:
        return to_json({
            "javaMethod": "story.none",
            "javaMethodArgs": {},
            "assistantMessage": "执行功能权限修改还缺少：" + "、".join(missing) + "。请补充后我会继续。",
            "missingInfo": missing,
        })

    args = {
        field: normalized.get(field)
        for field in ["id", "featureKey", "allowedRoles", "enabled"]
        if normalized.get(field) is not None
    }
    return to_json({
        "javaMethod": "featurePermission.update",
        "javaMethodArgs": args,
        "assistantMessage": "我已经准备好修改功能权限配置。",
        "missingInfo": [],
    })


def feature_permission_tools() -> list[Tool]:
    """获取功能权限管理模块工具列表。

    包含功能权限列表查询和按功能 key/id 修改允许角色。

    Returns:
        list[Tool]: 功能权限管理工具列表。
    """
    feature_key_hint = (
        "Common featureKey values: chat.use, story.list, story.detail, story.generate, "
        "story.updateBasic, story.updateDetail, story.reviseOutline, "
        "story.generateVolumeOutline, story.reviseVolumeOutline, story.updateVolumeOutline, "
        "story.generateVolumeSections, story.generateSectionAssets, story.generateSectionScript, "
        "story.uploadAssetAudio, story.delete, outlineConfig.manage, prompt.manage, "
        "user.manage, featurePermission.manage."
    )
    return system_tools() + [
        make_action_tool(
            "feature_permission_list",
            "List all feature permission configs. Input JSON can be empty.",
            "featurePermission.list",
        ),
        Tool.from_function(
            name="feature_permission_update",
            description=(
                "Update allowed roles/enabled for a feature permission. "
                "Input JSON: featureKey or id required; allowedRoles required as array/string "
                "of ROOT/ADMIN/USER; enabled optional. " + feature_key_hint
            ),
            func=feature_permission_update,
        ),
    ]


# ── 模块工具工厂映射 ──────────────────────────────────────────────────

# 模块名 → 工具工厂函数的映射表
MODULE_TOOL_FACTORY: dict[str, Callable[[], list[Tool]]] = {
    "manga": manga_tools,                        # 漫剧模块
    "outline_config": outline_config_tools,      # 大纲配置模块
    "prompt_management": prompt_management_tools, # Prompt 管理模块
    "user_permission": user_permission_tools,    # 用户权限模块
    "feature_permission": feature_permission_tools, # 功能权限模块
}


def get_tools_for_module(module: str) -> list[Tool]:
    """获取指定模块的工具列表。

    如果模块名不在映射表中，返回系统工具列表。

    Args:
        module: 模块名。

    Returns:
        list[Tool]: 该模块的工具列表。
    """
    # 查找工厂函数
    factory = MODULE_TOOL_FACTORY.get((module or "").strip().lower())

    # 如果找不到，返回系统工具
    if factory is None:
        return system_tools()

    # 调用工厂函数生成工具列表
    return factory()
