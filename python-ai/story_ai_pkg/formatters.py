# 文本格式化工具模块
# 本文件提供将结构化数据转换为提示词可读文本的工具函数，
# 以及从大模型输出中提取和解析文本的工具函数。

# re：正则表达式库，用于从标签格式文本中提取内容
import re

# HTTPException：FastAPI HTTP 异常，用于返回错误响应
from fastapi import HTTPException

# 从 models 导入需要格式化的数据模型
from .models import MainCharacterSetting, VolumeOutlineItem, VolumeSectionItem


def build_characters_text(main_characters: list[MainCharacterSetting]) -> str:
    """将结构化角色设定列表压缩为提示词可读的纯文本。

    每个角色一行，格式为：- 姓名: 角色; 描述; 性格; appearance={...}
    如果角色列表为空，返回 "No character settings were provided."

    Args:
        main_characters: 主要角色设定列表。

    Returns:
        str: 格式化的角色文本，用于大模型提示词。
    """
    return "\n".join(
        [
            (
                f"- {character.name}: {character.role or ''}; "
                f"{character.description or ''}; {character.personality or ''}; "
                f"appearance={character.appearance or {}}"
            )
            for character in main_characters
        ]
    ) or "No character settings were provided."


def format_volume_outline_context(volumes: list[VolumeOutlineItem]) -> str:
    """将已生成的分卷大纲列表整理为下一次模型调用的上下文文本。

    每卷包含卷号、标题、摘要、详细大纲和卷末钩子。
    用于逐卷生成时，让后续卷了解前序卷的内容，保证连续性。

    Args:
        volumes: 已生成的分卷大纲列表。

    Returns:
        str: 格式化的分卷上下文文本。如果列表为空，返回 "暂无"。
    """
    if not volumes:
        return "暂无"

    return "\n\n".join(
        [
            (
                f"第 {volume.volume_number} 卷：{volume.title}\n"
                f"摘要：{volume.summary}\n"
                f"详细大纲：\n{volume.content}\n"
                f"卷末钩子：{volume.ending_hook}"
            )
            for volume in volumes
        ]
    )


def format_volume_section_context(sections: list[VolumeSectionItem]) -> str:
    """将已生成的小节列表整理为下一节生成时的上下文文本。

    每节包含节号、标题、摘要、具体故事细节和小节钩子。
    用于逐节生成时，让后续节了解前序节的内容，保证连续性。

    Args:
        sections: 已生成的小节列表。

    Returns:
        str: 格式化的小节上下文文本。如果列表为空，返回 "暂无"。
    """
    if not sections:
        return "暂无"

    return "\n\n".join(
        [
            (
                f"第 {section.section_number} 节：{section.title}\n"
                f"摘要：{section.summary}\n"
                f"具体故事细节：\n{section.content}\n"
                f"小节钩子：{section.ending_hook}"
            )
            for section in sections
        ]
    )


def extract_llm_text(raw_result: object) -> str:
    """从普通 ChatModel 响应中提取纯文本内容。

    大模型返回的响应可能是字符串、消息对象或列表格式。
    本函数统一提取为纯文本字符串。

    Args:
        raw_result: 大模型返回的原始结果，可能是 str、AIMessage 或 list。

    Returns:
        str: 提取后的纯文本内容。如果结果为 None，返回空字符串。
    """
    if raw_result is None:
        return ""

    # 尝试获取 content 属性（AIMessage 对象），如果没有则使用原始值
    content = getattr(raw_result, "content", raw_result)

    # 如果是字符串，直接返回
    if isinstance(content, str):
        return content.strip()

    # 如果是列表（多模态响应），遍历提取文本
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                # 字符串元素直接添加
                parts.append(item)
            elif isinstance(item, dict):
                # 字典元素尝试提取 text 或 content 字段
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()

    # 其他类型转为字符串
    return str(content).strip()


def extract_tagged_text(raw_text: str, tag: str) -> str:
    """从纯文本输出中提取指定 XML 风格标签包裹的内容。

    大模型输出格式示例：
        <title>小节标题</title>
        <summary>小节摘要</summary>
        <content>具体内容</content>

    Args:
        raw_text: 大模型返回的原始文本。
        tag:      要提取的标签名，如 "title"、"summary"、"content"。

    Returns:
        str: 标签内的内容。如果标签不存在，返回空字符串。
    """
    # 构建正则表达式：匹配 <tag>...</tag>，支持跨行
    pattern = rf"<{tag}>(.*?)</{tag}>"

    # 使用 DOTALL 模式让 . 匹配换行符，IGNORECASE 忽略大小写
    match = re.search(pattern, raw_text, flags=re.DOTALL | re.IGNORECASE)

    if not match:
        return ""

    # 提取第一个捕获组并去除首尾空白
    return match.group(1).strip()


def parse_volume_section_text(raw_text: str, section_number: int) -> VolumeSectionItem:
    """将单节纯文本输出解析为 VolumeSectionItem 结构。

    大模型使用 <title>、<summary>、<content>、<endingHook> 标签包裹输出，
    本函数提取这些标签的内容并组装为结构化对象。
    使用纯文本标签而非 JSON，避免长正文中的引号和换行导致 JSON 转义失败。

    Args:
        raw_text:      大模型返回的原始文本。
        section_number: 当前小节号。

    Returns:
        VolumeSectionItem: 解析后的小节结构。

    Raises:
        HTTPException: 如果 <content> 标签缺失或为空（502 错误）。
    """
    # 提取各个标签的内容
    title = extract_tagged_text(raw_text, "title")
    summary = extract_tagged_text(raw_text, "summary")
    content = extract_tagged_text(raw_text, "content")
    ending_hook = extract_tagged_text(raw_text, "endingHook")

    # content 是必填字段，缺失则报错
    if not content:
        raise HTTPException(status_code=502, detail="Tongyi model returned malformed volume section text")

    # 组装为结构化对象
    return VolumeSectionItem(
        sectionNumber=section_number,
        title=title or f"第 {section_number} 节",  # 标题缺失时使用默认值
        summary=summary,
        content=content,
        endingHook=ending_hook,
    )
