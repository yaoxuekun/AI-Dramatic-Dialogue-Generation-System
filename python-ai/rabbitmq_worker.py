# RabbitMQ 后台 Worker 模块
# 负责消费 Java 后端投递的故事类 AI 任务（剧情大纲、分卷、小节、资产、脚本），
# 调用 story_ai 中的大模型函数处理任务，然后将结果发布回 RabbitMQ 供 Java 监听落库。
# 对话类任务不经过此模块，仍由 chat_ai 通过 HTTP 同步处理。

# json：用于 RabbitMQ 消息的序列化和反序列化
import json

# os：用于读取环境变量中的 RabbitMQ 配置
import os

# threading：用于创建后台消费线程，不阻塞 FastAPI 主进程
import threading

# time：用于重连等待
import time

# pathlib.Path：用于定位仓库根目录的 config.txt 配置文件
from pathlib import Path

# typing.Any：用于声明动态类型
from typing import Any

# yaml：用于解析 config.txt 中的 YAML 格式配置
import yaml

# 从 story_ai 导入所有请求模型和生成函数
from story_ai import (
    StorySectionAssetGenerateRequest,        # 小节资产生成请求
    StorySectionScriptGenerateRequest,       # 小节脚本生成请求
    StoryOutlineGenerateRequest,             # 剧情大纲生成请求
    StoryOutlineReviseRequest,               # 剧情大纲修改请求
    StoryVolumeOutlineGenerateRequest,       # 分卷大纲生成请求
    StoryVolumeOutlineReviseRequest,         # 分卷大纲修改请求
    StoryVolumeSectionGenerateRequest,       # 分卷小节生成请求
    StoryVolumeStoryGenerateRequest,         # 分卷正文生成请求
    generate_story_outline,                  # 剧情大纲生成函数
    generate_section_assets,                 # 小节资产生成函数
    generate_section_script,                 # 小节脚本生成函数
    generate_volume_outline,                 # 分卷大纲生成函数
    generate_volume_sections,                # 分卷小节生成函数
    generate_volume_story,                   # 分卷正文生成函数
    revise_story_outline,                    # 剧情大纲修改函数
    revise_volume_outline,                   # 分卷大纲修改函数
)


# ── RabbitMQ 队列和路由键常量 ──────────────────────────────────────────

# 交换机名称，Java 和 Python 共用同一个交换机
EXCHANGE = "aisay.ai.exchange"

# 请求队列：Java 投递任务到此队列，Python 消费
REQUEST_QUEUE = "aisay.ai.story.request"

# 结果队列：Python 投递结果到此队列，Java 监听
RESULT_QUEUE = "aisay.ai.story.result"

# 请求路由键：用于将消息路由到请求队列
REQUEST_ROUTING_KEY = "ai.story.request"

# 结果路由键：用于将消息路由到结果队列
RESULT_ROUTING_KEY = "ai.story.result"


# ── 任务类型常量 ──────────────────────────────────────────────────────
# 与 Java 端 AiRabbitConstants 中的常量一一对应

TASK_STORY_GENERATE = "STORY_GENERATE"                   # 剧情大纲生成
TASK_STORY_REVISE = "STORY_REVISE"                       # 剧情大纲修改
TASK_VOLUME_GENERATE = "VOLUME_GENERATE"                 # 分卷大纲生成
TASK_VOLUME_REVISE = "VOLUME_REVISE"                     # 分卷大纲修改
TASK_VOLUME_STORY_GENERATE = "VOLUME_STORY_GENERATE"     # 分卷正文生成
TASK_VOLUME_SECTION_GENERATE = "VOLUME_SECTION_GENERATE" # 分卷小节生成
TASK_SECTION_ASSET_GENERATE = "SECTION_ASSET_GENERATE"   # 小节资产图片生成
TASK_SECTION_SCRIPT_GENERATE = "SECTION_SCRIPT_GENERATE" # 小节分镜脚本生成

# 后台线程引用，避免重复启动
_worker_thread: threading.Thread | None = None


def start_rabbitmq_worker() -> None:
    """启动非对话类 AI 任务的 RabbitMQ 后台消费线程。

    在 FastAPI 启动时由 main.py 调用。如果线程已在运行则跳过。
    线程设置为 daemon 模式，主进程退出时自动终止。
    """
    global _worker_thread

    # 如果线程已存在且仍在运行，跳过
    if _worker_thread and _worker_thread.is_alive():
        return

    # 创建 daemon 线程，目标函数为 _worker_loop
    _worker_thread = threading.Thread(target=_worker_loop, name="aisay-story-ai-worker", daemon=True)
    _worker_thread.start()
    print("[rabbitmq-worker] background worker started")


def _worker_loop() -> None:
    """保持 RabbitMQ 消费连接，异常断开后自动重连。

    外层无限循环，内部调用 _consume_forever 持续消费。
    如果连接断开，等待 5 秒后自动重试。
    """
    while True:
        try:
            _consume_forever()
        except Exception as exc:
            # 连接异常，打印错误并等待 5 秒后重试
            print(f"[rabbitmq-worker] connection failed: {exc}; retrying in 5s")
            time.sleep(5)


def _consume_forever() -> None:
    """声明队列拓扑并持续消费 Java 投递的故事 AI 任务。

    处理流程：
    1. 从配置文件或环境变量读取 RabbitMQ 连接信息
    2. 建立连接并声明交换机、队列、绑定关系
    3. 设置 prefetch_count=1，一次只消费一条消息
    4. 注册消息回调 on_message，开始持续消费
    """
    # 延迟导入 pika，避免未安装时影响 FastAPI 启动
    import pika

    # 读取 RabbitMQ 连接配置
    config = _load_rabbitmq_config()

    # 创建认证凭据
    credentials = pika.PlainCredentials(config["username"], config["password"])

    # 创建连接参数
    parameters = pika.ConnectionParameters(
        host=config["host"],                              # RabbitMQ 主机地址
        port=config["port"],                              # RabbitMQ 端口
        credentials=credentials,                          # 认证凭据
        heartbeat=600,                                    # 心跳间隔 600 秒
        blocked_connection_timeout=300,                   # 阻塞连接超时 300 秒
    )

    # 建立阻塞连接
    connection = pika.BlockingConnection(parameters)

    # 创建通道
    channel = connection.channel()

    # 声明直连交换机，持久化
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)

    # 声明请求队列，持久化
    channel.queue_declare(queue=REQUEST_QUEUE, durable=True)

    # 声明结果队列，持久化
    channel.queue_declare(queue=RESULT_QUEUE, durable=True)

    # 绑定请求队列到交换机
    channel.queue_bind(queue=REQUEST_QUEUE, exchange=EXCHANGE, routing_key=REQUEST_ROUTING_KEY)

    # 绑定结果队列到交换机
    channel.queue_bind(queue=RESULT_QUEUE, exchange=EXCHANGE, routing_key=RESULT_ROUTING_KEY)

    # 设置预取数量为 1，一次只处理一条消息，避免 Worker 过载
    channel.basic_qos(prefetch_count=1)

    def on_message(ch: Any, method: Any, properties: Any, body: bytes) -> None:
        """RabbitMQ 消息回调函数。

        每收到一条消息就调用一次。处理流程：
        1. 解析 JSON 消息体
        2. 调用 _handle_story_task 处理任务
        3. 将结果发布到结果队列
        4. 确认消息已处理

        Args:
            ch:         通道对象，用于发布结果。
            method:     消息方法，包含 delivery_tag 用于确认。
            properties: 消息属性（未使用）。
            body:       消息体，JSON 编码的字节串。
        """
        # 解析 JSON 消息
        task = json.loads(body.decode("utf-8"))
        print(f"[rabbitmq-worker] received task {task.get('taskId')} type={task.get('taskType')}")

        def publish_result(result: dict[str, Any]) -> None:
            """将结果消息发布到结果队列。

            用于中间进度消息（partial）和最终结果消息。

            Args:
                result: 结果字典，包含 taskId、success、partial、completed 等字段。
            """
            ch.basic_publish(
                exchange=EXCHANGE,                           # 目标交换机
                routing_key=RESULT_ROUTING_KEY,              # 结果路由键
                body=json.dumps(result, ensure_ascii=False).encode("utf-8"),  # JSON 编码
                properties=pika.BasicProperties(
                    content_type="application/json",         # 内容类型
                    delivery_mode=2,                         # 持久化消息
                ),
            )
            # 打印发布日志
            print(
                "[rabbitmq-worker] published result "
                f"{result.get('taskId')} success={result.get('success')} "
                f"partial={result.get('partial')} completed={result.get('completed')}"
            )

        # 处理任务，获取最终结果
        result = _handle_story_task(task, publish_result)

        # 发布最终结果
        publish_result(result)

        # 确认消息已处理，从队列中移除
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # 注册消息回调，开始消费请求队列
    channel.basic_consume(queue=REQUEST_QUEUE, on_message_callback=on_message)
    print(f"[rabbitmq-worker] consuming queue={REQUEST_QUEUE} host={config['host']}:{config['port']}")

    # 开始持续消费，阻塞当前线程
    channel.start_consuming()


def _handle_story_task(
    task: dict[str, Any],
    publish_progress: Any | None = None,
) -> dict[str, Any]:
    """按任务类型调用 story_ai 中已有的大模型函数，并封装 Java 可消费的结果消息。

    支持 8 种任务类型：
    - STORY_GENERATE: 剧情大纲生成
    - STORY_REVISE: 剧情大纲修改
    - VOLUME_GENERATE: 分卷大纲生成（支持逐卷增量回传）
    - VOLUME_REVISE: 分卷大纲修改
    - VOLUME_STORY_GENERATE: 分卷正文生成
    - VOLUME_SECTION_GENERATE: 分卷小节生成（支持逐节增量回传）
    - SECTION_ASSET_GENERATE: 小节资产图片生成
    - SECTION_SCRIPT_GENERATE: 小节分镜脚本生成

    Args:
        task:              任务字典，包含 taskType、userId、storyId 等字段。
        publish_progress:  中间进度发布回调，用于逐卷/逐节增量回传。

    Returns:
        dict: 结果字典，包含 taskId、success、errorMessage、storyOutline 等字段。
    """
    # 初始化结果字典，包含所有可能的字段
    result: dict[str, Any] = {
        "taskId": task.get("taskId"),           # 任务 ID，用于 Java 关联回调
        "taskType": task.get("taskType"),       # 任务类型
        "userId": task.get("userId"),           # 用户 ID
        "storyId": task.get("storyId"),         # 故事 ID
        "volumeId": task.get("volumeId"),       # 分卷 ID
        "volumeNumber": None,                   # 分卷号
        "success": False,                       # 是否成功
        "errorMessage": None,                   # 错误信息
        "storyOutline": None,                   # 剧情大纲结果
        "volumeOutline": None,                  # 分卷大纲结果
        "volumeSection": None,                  # 分卷小节结果
        "sectionScript": None,                  # 分镜脚本结果
        "volumeStory": None,                    # 分卷正文结果
        "partial": False,                       # 是否为中间进度消息
        "completed": False,                     # 是否为最终完成消息
    }

    try:
        task_type = task.get("taskType")

        # ── 剧情大纲生成 ──────────────────────────────────────
        if task_type == TASK_STORY_GENERATE:
            response = generate_story_outline(
                StoryOutlineGenerateRequest(
                    userId=task.get("userId"),
                    genre=task.get("genre"),
                    storyStyle=task.get("storyStyle"),
                    plot=task.get("plot"),
                )
            )
            # 将结构化响应转为字典
            result["storyOutline"] = response.model_dump(by_alias=True)

        # ── 剧情大纲修改 ──────────────────────────────────────
        elif task_type == TASK_STORY_REVISE:
            response = revise_story_outline(
                StoryOutlineReviseRequest(
                    userId=task.get("userId"),
                    storyId=task.get("storyId"),
                    genre=task.get("genre"),
                    storyStyle=task.get("storyStyle"),
                    title=task.get("title") or "",
                    synopsis=task.get("storySummary"),
                    outline=task.get("outline") or "",
                    suggestion=task.get("suggestion") or "",
                )
            )
            result["storyOutline"] = response.model_dump(by_alias=True)

        # ── 分卷大纲生成（支持逐卷增量回传）──────────────────
        elif task_type == TASK_VOLUME_GENERATE:
            def publish_volume(volume: Any) -> None:
                """逐卷进度回调：每生成一卷就发布一条 partial 消息。"""
                if not publish_progress:
                    return
                # 创建进度消息骨架
                progress_result = _base_result(task)
                progress_result["success"] = True
                progress_result["partial"] = True            # 标记为中间进度
                progress_result["completed"] = False         # 尚未完成
                progress_result["volumeOutline"] = {"volumes": [volume.model_dump(by_alias=True)]}
                # 发布到结果队列
                publish_progress(progress_result)

            response = generate_volume_outline(
                StoryVolumeOutlineGenerateRequest(
                    userId=task.get("userId"),
                    storyId=task.get("storyId"),
                    genre=task.get("genre"),
                    storyStyle=task.get("storyStyle"),
                    title=task.get("title") or "",
                    storySummary=task.get("storySummary"),
                    outline=task.get("outline") or "",
                    mainCharacters=task.get("mainCharacters") or [],
                ),
                on_volume_generated=publish_volume,  # 注册逐卷回调
            )
            # 全部生成完成，标记 completed
            result["completed"] = True
            result["volumeOutline"] = None  # 最终消息不重复发送全部分卷

        # ── 分卷大纲修改 ──────────────────────────────────────
        elif task_type == TASK_VOLUME_REVISE:
            response = revise_volume_outline(
                StoryVolumeOutlineReviseRequest(
                    userId=task.get("userId"),
                    storyId=task.get("storyId"),
                    genre=task.get("genre"),
                    storyStyle=task.get("storyStyle"),
                    title=task.get("title") or "",
                    storySummary=task.get("storySummary"),
                    outline=task.get("outline") or "",
                    mainCharacters=task.get("mainCharacters") or [],
                    volumeOutlines=task.get("volumeOutlines") or [],
                    suggestion=task.get("suggestion") or "",
                )
            )
            result["volumeOutline"] = response.model_dump(by_alias=True)
            result["completed"] = True

        # ── 分卷正文生成 ──────────────────────────────────────
        elif task_type == TASK_VOLUME_STORY_GENERATE:
            # 从任务中提取分卷大纲（取第一个）
            volume_outline = (task.get("volumeOutlines") or [None])[0]
            if not volume_outline:
                raise ValueError("Volume outline is required for volume story generation")

            response = generate_volume_story(
                StoryVolumeStoryGenerateRequest(
                    userId=task.get("userId"),
                    storyId=task.get("storyId"),
                    volumeId=task.get("volumeId"),
                    genre=task.get("genre"),
                    title=task.get("title") or "",
                    storyStyle=task.get("storyStyle"),
                    storySummary=task.get("storySummary"),
                    outline=task.get("outline") or "",
                    mainCharacters=task.get("mainCharacters") or [],
                    volumeOutline=volume_outline,
                )
            )
            result["volumeId"] = task.get("volumeId")
            result["volumeNumber"] = volume_outline.get("volumeNumber")
            result["volumeStory"] = response.volume_story
            result["completed"] = True

        # ── 分卷小节生成（支持逐节增量回传）──────────────────
        elif task_type == TASK_VOLUME_SECTION_GENERATE:
            volume_outline = (task.get("volumeOutlines") or [None])[0]
            if not volume_outline:
                raise ValueError("Volume outline is required for volume section generation")

            def publish_section(section: Any) -> None:
                """逐节进度回调：每生成一节就发布一条 partial 消息。"""
                if not publish_progress:
                    return
                progress_result = _base_result(task)
                progress_result["success"] = True
                progress_result["partial"] = True
                progress_result["completed"] = False
                progress_result["volumeId"] = task.get("volumeId")
                progress_result["volumeNumber"] = volume_outline.get("volumeNumber")
                progress_result["volumeSection"] = {"sections": [section.model_dump(by_alias=True)]}
                publish_progress(progress_result)

            generate_volume_sections(
                StoryVolumeSectionGenerateRequest(
                    userId=task.get("userId"),
                    storyId=task.get("storyId"),
                    volumeId=task.get("volumeId"),
                    genre=task.get("genre"),
                    title=task.get("title") or "",
                    storyStyle=task.get("storyStyle"),
                    storySummary=task.get("storySummary"),
                    outline=task.get("outline") or "",
                    mainCharacters=task.get("mainCharacters") or [],
                    volumeOutline=volume_outline,
                    existingAssets=task.get("existingAssets") or [],
                ),
                on_section_generated=publish_section,  # 注册逐节回调
            )
            result["volumeId"] = task.get("volumeId")
            result["volumeNumber"] = volume_outline.get("volumeNumber")
            result["completed"] = True

        # ── 小节资产图片生成 ──────────────────────────────────
        elif task_type == TASK_SECTION_ASSET_GENERATE:
            volume_outline = (task.get("volumeOutlines") or [None])[0]
            if not volume_outline:
                raise ValueError("Volume outline is required for section asset generation")
            section = task.get("section")
            if not section:
                raise ValueError("Section is required for section asset generation")

            response = generate_section_assets(
                StorySectionAssetGenerateRequest(
                    userId=task.get("userId"),
                    storyId=task.get("storyId"),
                    volumeId=task.get("volumeId"),
                    genre=task.get("genre"),
                    title=task.get("title") or "",
                    storyStyle=task.get("storyStyle"),
                    storySummary=task.get("storySummary"),
                    outline=task.get("outline") or "",
                    mainCharacters=task.get("mainCharacters") or [],
                    volumeOutline=volume_outline,
                    section=section,
                    existingAssets=task.get("existingAssets") or [],
                )
            )
            result["volumeId"] = task.get("volumeId")
            result["volumeNumber"] = volume_outline.get("volumeNumber")
            result["volumeSection"] = response.model_dump(by_alias=True)
            result["completed"] = True

        # ── 小节分镜脚本生成 ──────────────────────────────────
        elif task_type == TASK_SECTION_SCRIPT_GENERATE:
            volume_outline = (task.get("volumeOutlines") or [None])[0]
            if not volume_outline:
                raise ValueError("Volume outline is required for section script generation")
            section = task.get("section")
            if not section:
                raise ValueError("Section is required for section script generation")

            response = generate_section_script(
                StorySectionScriptGenerateRequest(
                    userId=task.get("userId"),
                    storyId=task.get("storyId"),
                    volumeId=task.get("volumeId"),
                    genre=task.get("genre"),
                    title=task.get("title") or "",
                    storyStyle=task.get("storyStyle"),
                    storySummary=task.get("storySummary"),
                    outline=task.get("outline") or "",
                    mainCharacters=task.get("mainCharacters") or [],
                    volumeOutline=volume_outline,
                    section=section,
                )
            )
            result["volumeId"] = task.get("volumeId")
            result["volumeNumber"] = volume_outline.get("volumeNumber")
            result["sectionScript"] = response.model_dump(by_alias=True)
            result["completed"] = True

        # ── 未知任务类型 ──────────────────────────────────────
        else:
            raise ValueError(f"Unsupported AI story task type: {task_type}")

        # 标记任务成功
        result["success"] = True

        # 剧情大纲生成和修改在处理完成后直接标记 completed
        if task_type in {TASK_STORY_GENERATE, TASK_STORY_REVISE}:
            result["completed"] = True

    except Exception as exc:
        # 捕获所有异常，记录错误信息
        result["errorMessage"] = str(exc)
        print(f"[rabbitmq-worker] task {task.get('taskId')} failed: {exc}")

    return result


def _base_result(task: dict[str, Any]) -> dict[str, Any]:
    """创建 RabbitMQ AI 结果消息的公共字段骨架。

    用于最终结果消息和中间进度消息，保证字段结构一致。

    Args:
        task: 原始任务字典，用于提取公共字段。

    Returns:
        dict: 结果消息骨架，所有值为默认值。
    """
    return {
        "taskId": task.get("taskId"),           # 任务 ID
        "taskType": task.get("taskType"),       # 任务类型
        "userId": task.get("userId"),           # 用户 ID
        "storyId": task.get("storyId"),         # 故事 ID
        "volumeId": task.get("volumeId"),       # 分卷 ID
        "volumeNumber": None,                   # 分卷号
        "success": False,                       # 是否成功
        "errorMessage": None,                   # 错误信息
        "storyOutline": None,                   # 剧情大纲结果
        "volumeOutline": None,                  # 分卷大纲结果
        "volumeSection": None,                  # 分卷小节结果
        "sectionScript": None,                  # 分镜脚本结果
        "volumeStory": None,                    # 分卷正文结果
        "partial": False,                       # 是否为中间进度
        "completed": False,                     # 是否为最终完成
    }


def _load_rabbitmq_config() -> dict[str, Any]:
    """从环境变量或仓库根目录 config.txt 读取 RabbitMQ 地址与账号。

    优先级：环境变量 > config.txt > 默认值。

    Returns:
        dict: 包含 host、port、username、password 的配置字典。
    """
    # 默认配置
    config = {
        "host": os.getenv("RABBITMQ_HOST", "127.0.0.1"),       # 默认本机
        "port": int(os.getenv("RABBITMQ_PORT", "5672")),       # 默认端口
        "username": os.getenv("RABBITMQ_USERNAME", "guest"),    # 默认用户名
        "password": os.getenv("RABBITMQ_PASSWORD", "guest"),    # 默认密码
    }

    # 定位仓库根目录的 config.txt
    config_path = Path(__file__).resolve().parents[1] / "config.txt"
    if not config_path.exists():
        return config

    # 读取并解析 YAML 配置
    raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    rabbit_config = raw_config.get("rabbitmq") or {}

    # 解析 name-server 格式：host:port
    name_server = rabbit_config.get("name-server")
    if name_server:
        host, _, port = str(name_server).partition(":")
        config["host"] = host or config["host"]
        config["port"] = int(port or config["port"])

    # 覆盖用户名和密码
    config["username"] = rabbit_config.get("username") or config["username"]
    config["password"] = rabbit_config.get("password") or config["password"]

    return config
