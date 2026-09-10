# 资产业务模块
# 本文件负责小节中人物/场景资产的识别、复用和图片生成。
# 包含一个 FastAPI 端点和多个工具函数：
# - POST /api/story/section-assets：小节资产生成入口
# - resolve_section_assets：批量识别并处理小节资产
# - resolve_single_section_asset：处理单个资产（复用或生成图片）
# - save_doubao_image_file：调用豆包 API 生成图片并保存到本地

# uuid：用于生成图片文件名
import uuid

# time：用于计算请求耗时
import time

# date：用于生成图片存储目录名
from datetime import date

# Path：用于构建本地文件路径
from pathlib import Path

# urlopen：用于下载豆包返回的图片 URL
from urllib.request import urlopen

# HTTPException：FastAPI HTTP 异常
from fastapi import HTTPException

# 从 ai_runtime 导入共享的 LLM 实例和工具函数
from ai_runtime import (
    ConsoleStreamingCallback,
    get_doubao_image_client,
    invoke_structured_output_with_guard,
    llm_temperature_0,
    log_progress,
)

# 从 formatters 导入文本格式化工具
from .formatters import build_characters_text

# 从 models 导入数据模型
from .models import (
    ExistingStoryAsset,                    # 已有资产引用
    SectionAssetExtractionItem,            # LLM 识别出的单个资产
    SectionAssetExtractionOutput,          # LLM 资产识别输出
    SectionAssetItem,                      # 当前小节资产
    StorySectionAssetGenerateRequest,      # 小节资产生成请求
    StoryVolumeSectionGenerateRequest,     # 小节生成请求（用于类型联合）
    StoryVolumeSectionGenerateResponse,    # 小节生成响应
    VolumeSectionItem,                     # 单个小节
)

# 从 router 导入路由器
from .router import router

# 从 templates 导入提示词模板加载函数
from .templates import load_prompt_template


def normalize_asset_key(asset_type: str, name: str) -> str:
    """将资产类型和名称归一化为查重 key。

    格式：{大写类型}::{小写名称}
    用于在资产字典中快速查找已有资产。

    Args:
        asset_type: 资产类型，如 "CHARACTER"、"SCENE"。
        name:       资产名称。

    Returns:
        str: 归一化后的 key，如 "CHARACTER::林澈"。
    """
    return f"{asset_type.strip().upper()}::{name.strip().lower()}"


def build_asset_registry(existing_assets: list[ExistingStoryAsset]) -> dict[str, SectionAssetItem]:
    """将 Java 已有资产列表转为可快速查找的字典。

    字典 key 为归一化的资产 key，value 为 SectionAssetItem。
    用于判断人物/场景是否首次出现。

    Args:
        existing_assets: Java 传入的已有资产列表。

    Returns:
        dict: 资产字典，key 为归一化 key，value 为 SectionAssetItem。
    """
    registry: dict[str, SectionAssetItem] = {}
    for asset in existing_assets:
        # 跳过没有名称的资产
        if not asset.name:
            continue

        # 归一化类型
        asset_type = asset.asset_type.strip().upper()

        # 构建 SectionAssetItem 并存入字典
        registry[normalize_asset_key(asset_type, asset.name)] = SectionAssetItem(
            assetType=asset_type,
            name=asset.name,
            description=asset.description,
            imagePrompt=asset.image_prompt,
            imagePath=asset.image_path,
            audioPath=asset.audio_path,
            firstAppearance=False,  # 已有资产都不是首次出现
        )
    return registry


def format_existing_asset_context(asset_registry: dict[str, SectionAssetItem]) -> str:
    """将已有故事资产整理为 LLM 识别人物/场景时的上下文文本。

    每个资产一行，包含类型、名称、描述、图片提示词、图片路径和音频路径。
    用于资产识别提示词的 {ExistingAssets} 变量。

    Args:
        asset_registry: 资产字典。

    Returns:
        str: 格式化的资产上下文文本。如果字典为空，返回 "暂无"。
    """
    if not asset_registry:
        return "暂无"

    return "\n".join(
        [
            (
                f"- [{asset.asset_type}] {asset.name}：{asset.description or '无描述'}；"
                f"图片提示词：{asset.image_prompt or '暂无'}；"
                f"图片：{asset.image_path or '暂无'}；音频：{asset.audio_path or '暂无'}"
            )
            for asset in asset_registry.values()
        ]
    )


def save_doubao_image_file(prompt: str) -> str:
    """调用豆包图片生成接口并把返回图片保存到本地 storage 目录。

    处理流程：
    1. 获取豆包 OpenAI 客户端
    2. 调用 SeedDream 4.5 模型生成图片
    3. 下载返回的图片 URL
    4. 保存到 backend/storage/generated-assets/{日期}/{uuid}.png

    Args:
        prompt: 豆包图片生成提示词。

    Returns:
        str: 图片的相对路径，如 "generated-assets/2026-05-22/xxx.png"。

    Raises:
        RuntimeError: 如果豆包返回的响应中没有图片 URL。
    """
    # 获取豆包客户端（懒加载）
    client = get_doubao_image_client()

    # 打印分隔线，便于日志阅读
    print("------------------------------------------------------------------------------")

    # 调用豆包图片生成 API
    images_response = client.images.generate(
        model="doubao-seedream-4-5-251128",  # 豆包 SeedDream 4.5 模型
        prompt=prompt,                        # 图片生成提示词
        size="2K",                            # 图片分辨率 2K
        response_format="url",                # 返回 URL 格式
        extra_body={
            "watermark": True,                # 添加水印
        },
    )

    # 打印提示词和响应（调试用）
    print(prompt)
    print(images_response)

    # 提取图片 URL
    image_url = images_response.data[0].url
    if not image_url:
        raise RuntimeError("Doubao image response does not contain url")

    # 构建本地存储路径
    category = "generated-assets"                           # 存储分类
    current_date = date.today().isoformat()                 # 当前日期，如 "2026-05-22"
    filename = f"{uuid.uuid4()}.png"                        # UUID 文件名，避免冲突
    storage_root = Path(__file__).resolve().parents[2] / "backend" / "storage"  # storage 根目录
    target_directory = storage_root / category / current_date  # 目标目录
    target_directory.mkdir(parents=True, exist_ok=True)     # 创建目录（如果不存在）
    target_file = target_directory / filename               # 目标文件路径

    # 下载图片并保存
    with urlopen(image_url, timeout=180) as response:
        target_file.write_bytes(response.read())

    # 返回相对路径，供 Java 文件服务读取
    return f"{category}/{current_date}/{filename}"


def resolve_storage_file(relative_path: str | None) -> Path | None:
    """将 Java storage 中保存的相对路径解析为本地绝对路径。

    Args:
        relative_path: 相对路径，如 "generated-assets/2026-05-22/xxx.png"。

    Returns:
        Path | None: 本地绝对路径。如果输入为空，返回 None。
    """
    if not relative_path or not relative_path.strip():
        return None

    # 规范化路径分隔符
    normalized_path = relative_path.strip().replace("\\", "/").lstrip("/")

    # 拼接为绝对路径
    return Path(__file__).resolve().parents[2] / "backend" / "storage" / normalized_path


def has_local_image_file(relative_path: str | None) -> bool:
    """判断资产图片路径是否真的已经落在本地文件系统。

    数据库中可能有路径字符串，但文件可能已被删除。

    Args:
        relative_path: 图片相对路径。

    Returns:
        bool: 如果文件存在返回 True，否则返回 False。
    """
    file_path = resolve_storage_file(relative_path)
    return bool(file_path and file_path.is_file())


def generate_asset_image_path(
    title: str,
    story_style: str | None,
    asset_type: str,
    asset_name: str,
    image_prompt: str,
    trace_id: str,
    started_at: float,
    scope: str,
) -> tuple[str | None, str | None, bool]:
    """调用豆包为指定人物/场景生成图片。

    Args:
        title:        故事标题。
        story_style:  漫剧视觉风格。
        asset_type:   资产类型（CHARACTER 或 SCENE）。
        asset_name:   资产名称。
        image_prompt: 图片生成提示词。
        trace_id:     追踪 ID。
        started_at:   请求开始时间。
        scope:        业务范围。

    Returns:
        tuple: (图片相对路径, 错误信息, 是否尝试过生成)
            - 成功时：("generated-assets/...", None, True)
            - 失败时：(None, "错误信息", True)
    """
    log_progress(trace_id, f"calling doubao image generation for {asset_type}: {asset_name}", started_at, scope)
    try:
        # 构建豆包提示词（根据资产类型分流：人物三视图 vs 场景概念图）
        prompt_doubao = build_doubao_prompt(title, story_style, asset_type, asset_name, image_prompt)

        # 调用豆包生成并保存图片
        image_path = save_doubao_image_file(prompt_doubao)
        return image_path, None, True
    except Exception as exc:
        # 图片生成失败，记录错误但不中断流程
        print("图片生成失败")
        return None, str(exc), True


def build_doubao_prompt(
    title: str,
    story_style: str | None,
    asset_type: str,
    asset_name: str,
    image_prompt: str,
) -> str:
    """根据资产类型补全豆包图片生成提示词，统一漫剧资源视觉风格。

    人物类型：生成三视图设定图（正面、侧面、背面）
    场景类型：生成环境概念图

    Args:
        title:        故事标题。
        story_style:  漫剧视觉风格。
        asset_type:   资产类型。
        asset_name:   资产名称。
        image_prompt: 基础图片提示词。

    Returns:
        str: 完整的豆包图片生成提示词。
    """
    # 解析风格：如果未指定，使用默认风格
    resolved_style = story_style.strip() if story_style and story_style.strip() else "高质量国漫/漫剧视觉"

    # 归一化类型
    normalized_type = asset_type.strip().upper()

    # 根据类型选择不同的提示词模板
    if normalized_type == "CHARACTER":
        return build_character_three_view_prompt(title, resolved_style, asset_name, image_prompt)
    return build_scene_concept_prompt(title, resolved_style, asset_name, image_prompt)


def build_character_three_view_prompt(
    title: str,
    resolved_style: str,
    asset_name: str,
    image_prompt: str,
) -> str:
    """构造人物三视图提示词，用于角色首次成图和后续视频制作参考。

    三视图包含正面、侧面、背面，保持完全一致的外观设计。

    Args:
        title:         故事标题。
        resolved_style: 解析后的漫剧风格。
        asset_name:    角色名称。
        image_prompt:  角色描述。

    Returns:
        str: 人物三视图提示词。
    """
    return (
        f"为漫剧《{title}》生成角色“{asset_name}”的人物三视图设定图。\n"
        f"用户设定的统一漫剧风格：{resolved_style}\n"
        f"角色描述：{image_prompt}\n"
        "画面要求：同一角色必须在同一张图中展示正面、侧面、背面三视图，三视图保持完全一致的发型、脸型、服装、配饰、身材比例和色彩方案。\n"
        "构图要求：白色或浅灰纯色背景，角色站姿自然，正面/侧面/背面横向排列，比例统一，无遮挡，不要出现多名不同角色。\n"
        "细节要求：强调可复用的角色设计、服装结构、标志性道具、面部特征和配色，适合后续分镜、建模、视频生成和角色一致性参考。\n"
        f"最终画面必须严格遵循“{resolved_style}”。"
    )


def build_scene_concept_prompt(
    title: str,
    resolved_style: str,
    asset_name: str,
    image_prompt: str,
) -> str:
    """构造场景概念图提示词，用于环境资产首次成图和后续视频制作参考。

    概念图突出空间结构、时代质感和光影氛围。

    Args:
        title:         故事标题。
        resolved_style: 解析后的漫剧风格。
        asset_name:    场景名称。
        image_prompt:  场景描述。

    Returns:
        str: 场景概念图提示词。
    """
    return (
        f"为漫剧《{title}》生成场景“{asset_name}”的环境概念图。\n"
        f"用户设定的统一漫剧风格：{resolved_style}\n"
        f"场景描述：{image_prompt}\n"
        "画面要求：突出空间结构、时代质感、光影氛围、关键道具、可复用背景元素和镜头调度空间。\n"
        "构图要求：单一完整场景，不要画成人物三视图，不要把角色作为主体；可以保留少量远景人物作为尺度参考，但重点必须是环境。\n"
        "细节要求：适合后续分镜、视频生成和同场景复用，画面层次清晰，色彩和材质统一。\n"
        f"最终画面必须严格遵循“{resolved_style}”。"
    )


def resolve_single_section_asset(
    title: str,
    story_style: str | None,
    asset_type: str,
    extracted: SectionAssetExtractionItem,
    asset_registry: dict[str, SectionAssetItem],
    trace_id: str,
    started_at: float,
    scope: str,
) -> SectionAssetItem:
    """判断单个资产是否首次出现，首次出现时调用豆包生成图片。

    判断逻辑：
    1. 如果 LLM 返回了 matchedExistingName，优先按匹配名查找已有资产
    2. 如果匹配到且本地图片存在，直接复用
    3. 如果匹配到但图片缺失，重新生成
    4. 如果没有 matchedExistingName，按归一化 key 查找
    5. 如果找到且图片存在，复用
    6. 如果找到但图片缺失，重新生成
    7. 如果都没找到，标记为首次出现并生成图片

    Args:
        title:         故事标题。
        story_style:   漫剧风格。
        asset_type:    资产类型（CHARACTER 或 SCENE）。
        extracted:     LLM 识别出的资产信息。
        asset_registry: 已有资产字典。
        trace_id:      追踪 ID。
        started_at:    请求开始时间。
        scope:         业务范围。

    Returns:
        SectionAssetItem: 处理后的资产信息。
    """
    # 归一化类型
    normalized_type = asset_type.strip().upper()

    # ── 优先按 matchedExistingName 匹配 ────────────────────────────────
    if extracted.matched_existing_name:
        matched_key = normalize_asset_key(normalized_type, extracted.matched_existing_name)
        matched = asset_registry.get(matched_key)

        # 匹配到且本地图片存在，直接复用
        if matched and has_local_image_file(matched.image_path):
            log_progress(trace_id, f"reuse matched {normalized_type} image: {matched.name} -> {matched.image_path}", started_at, scope)
            return SectionAssetItem(
                assetType=normalized_type,
                name=matched.name,
                description=matched.description or extracted.description,
                imagePrompt=matched.image_prompt or extracted.image_prompt,
                imagePath=matched.image_path,
                audioPath=matched.audio_path,
                firstAppearance=False,
            )

        # 匹配到但图片缺失，重新生成
        if matched:
            log_progress(
                trace_id,
                f"matched {normalized_type} asset record but image is missing, regenerating: {matched.name}, image_path={matched.image_path}",
                started_at,
                scope,
            )
            image_path, generation_error, _ = generate_asset_image_path(
                title, story_style, normalized_type, matched.name, extracted.image_prompt,
                trace_id, started_at, scope,
            )
            return SectionAssetItem(
                assetType=normalized_type,
                name=matched.name,
                description=matched.description or extracted.description,
                imagePrompt=matched.image_prompt or extracted.image_prompt,
                imagePath=image_path,
                audioPath=matched.audio_path,
                firstAppearance=False,
                generationError=generation_error,
            )

    # ── 按归一化 key 匹配 ─────────────────────────────────────────────
    key = normalize_asset_key(normalized_type, extracted.name)
    existing = asset_registry.get(key)

    # 找到且本地图片存在，直接复用
    if existing and has_local_image_file(existing.image_path):
        log_progress(trace_id, f"reuse existing {normalized_type} image: {existing.name} -> {existing.image_path}", started_at, scope)
        return SectionAssetItem(
            assetType=normalized_type,
            name=existing.name,
            description=existing.description or extracted.description,
            imagePrompt=existing.image_prompt or extracted.image_prompt,
            imagePath=existing.image_path,
            audioPath=existing.audio_path,
            firstAppearance=False,
        )

    # 找到但图片缺失，重新生成
    if existing:
        log_progress(
            trace_id,
            f"existing {normalized_type} asset record has no usable image, regenerating: {existing.name}, image_path={existing.image_path}",
            started_at,
            scope,
        )
        image_path, generation_error, _ = generate_asset_image_path(
            title, story_style, normalized_type, existing.name, extracted.image_prompt,
            trace_id, started_at, scope,
        )
        return SectionAssetItem(
            assetType=normalized_type,
            name=existing.name,
            description=existing.description or extracted.description,
            imagePrompt=existing.image_prompt or extracted.image_prompt,
            imagePath=image_path,
            audioPath=existing.audio_path,
            firstAppearance=False,
            generationError=generation_error,
        )

    # ── 首次出现，生成新图片 ──────────────────────────────────────────
    log_progress(trace_id, f"no existing {normalized_type} asset record, generating image: {extracted.name}", started_at, scope)
    image_path, generation_error, _ = generate_asset_image_path(
        title, story_style, normalized_type, extracted.name, extracted.image_prompt,
        trace_id, started_at, scope,
    )

    # 创建新资产并注册到字典
    asset = SectionAssetItem(
        assetType=normalized_type,
        name=extracted.name,
        description=extracted.description,
        imagePrompt=extracted.image_prompt,
        imagePath=image_path,
        audioPath=None,
        firstAppearance=True,  # 标记为首次出现
        generationError=generation_error,
    )
    asset_registry[key] = asset
    return asset


def resolve_section_assets(
    request: StoryVolumeSectionGenerateRequest | StorySectionAssetGenerateRequest,
    section: VolumeSectionItem,
    asset_registry: dict[str, SectionAssetItem],
    characters_text: str,
    trace_id: str,
    started_at: float,
    scope: str,
) -> list[SectionAssetItem]:
    """用温度为 0 的结构化 LLM 识别本节人物/场景，并生成或复用本地资产。

    处理流程：
    1. 调用大模型识别小节中出现的人物和场景
    2. 遍历识别结果，逐个判断是否首次出现
    3. 首次出现的调用豆包生成图片，已有的复用本地图片

    Args:
        request:         小节生成或资产生成请求。
        section:         当前小节。
        asset_registry:  已有资产字典。
        characters_text: 角色设定文本。
        trace_id:        追踪 ID。
        started_at:      请求开始时间。
        scope:           业务范围。

    Returns:
        list[SectionAssetItem]: 本节的资产列表。
    """
    # 创建结构化输出 LLM，绑定 SectionAssetExtractionOutput 模型
    extraction_llm = llm_temperature_0.with_structured_output(SectionAssetExtractionOutput)
    extraction_chain = load_prompt_template(
        "extract_section_assets",
        genre=request.genre,
        story_style=request.story_style,
    ) | extraction_llm

    # 打印识别开始日志
    log_progress(trace_id, f"extracting assets for section {section.section_number}", started_at, scope)

    # 调用大模型识别资产
    extraction = invoke_structured_output_with_guard(
        extraction_chain,
        {
            "Title": request.title,
            "Theme": request.genre or "未指定",
            "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
            "StorySummary": request.story_summary or "",
            "Outline": request.outline,
            "Characters": characters_text,
            "VolumeNumber": request.volume_outline.volume_number,
            "VolumeTitle": request.volume_outline.title,
            "SectionNumber": section.section_number,
            "SectionTitle": section.title,
            "SectionSummary": section.summary or "",
            "SectionContent": section.content,
            "ExistingAssets": format_existing_asset_context(asset_registry),
        },
        SectionAssetExtractionOutput,
        config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
        trace_id=trace_id,
        started_at=started_at,
        scope=scope,
    )

    # 打印识别结果日志
    section_assets: list[SectionAssetItem] = []
    log_progress(
        trace_id,
        f"asset extraction result: characters={len(extraction.characters)}, scenes={len(extraction.scenes)}",
        started_at,
        scope,
    )

    # 遍历识别出的人物，逐个处理
    for character in extraction.characters:
        section_assets.append(resolve_single_section_asset(request.title, request.story_style, "CHARACTER", character, asset_registry, trace_id, started_at, scope))

    # 遍历识别出的场景，逐个处理
    for scene in extraction.scenes:
        section_assets.append(resolve_single_section_asset(request.title, request.story_style, "SCENE", scene, asset_registry, trace_id, started_at, scope))

    # 打印完成日志
    log_progress(trace_id, f"section {section.section_number} assets resolved: {len(section_assets)}", started_at, scope)
    return section_assets


@router.post("/api/story/section-assets", response_model=StoryVolumeSectionGenerateResponse)
def generate_section_assets(request: StorySectionAssetGenerateRequest) -> StoryVolumeSectionGenerateResponse:
    """只为指定小节识别并生成/复用人物与场景资产。

    处理流程：
    1. 校验小节内容是否存在
    2. 构建已有资产字典
    3. 调用 resolve_section_assets 识别并处理资产
    4. 返回包含资产信息的小节

    Args:
        request: 小节资产生成请求体。

    Returns:
        StoryVolumeSectionGenerateResponse: 包含资产信息的小节列表。
    """
    # 生成追踪 ID
    trace_id = uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    scope = "section-assets"

    # 校验小节内容
    if not request.section.content or not request.section.content.strip():
        raise HTTPException(status_code=400, detail="Section content is required before generating section assets")

    # 打印请求接收日志
    log_progress(
        trace_id,
        (
            f"request accepted, user_id={request.user_id}, story_id={request.story_id}, "
            f"volume_id={request.volume_id}, section={request.section.section_number}"
        ),
        started_at,
        scope,
    )

    # 构建已有资产字典
    asset_registry = build_asset_registry(request.existing_assets)

    # 将角色设定转为文本
    characters_text = build_characters_text(request.main_characters)

    # 获取小节引用
    section = request.section

    # 识别并处理资产
    section.assets = resolve_section_assets(
        request, section, asset_registry, characters_text, trace_id, started_at, scope,
    )

    # 打印完成日志
    log_progress(trace_id, f"section assets generated: {len(section.assets)}", started_at, scope)

    # 返回包含资产信息的小节
    return StoryVolumeSectionGenerateResponse(sections=[section])
