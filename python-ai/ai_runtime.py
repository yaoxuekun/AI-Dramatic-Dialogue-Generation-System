# AI 运行时配置模块
# 集中管理大模型 API Key 读取、LLM 实例初始化、回调处理器和进度日志函数
# 所有需要调用大模型的模块（story_ai、chat_ai）都从这里导入共享实例

# os：用于设置环境变量，通义千问和豆包 SDK 通过环境变量读取 API Key
import os

# json：用于校验和修复大模型返回的 JSON 结构化输出
import json

# re：用于从 LangChain 结构化输出异常中提取原始 JSON 参数
import re

# time：用于计算请求耗时，打印进度日志
import time

# random：用于给重试等待增加轻微抖动，避免并发请求同时重试
import random

# pathlib.Path：用于定位 api.yml 配置文件路径
from pathlib import Path

# typing.Any：用于声明通用结构化输出类型
from typing import Any

# yaml：用于解析 api.yml 中的 YAML 格式配置
import yaml

# ChatTongyi：LangChain 对通义千问（Tongyi）大模型的封装，支持 structured output 和流式调用
from langchain_community.chat_models import ChatTongyi

# BaseCallbackHandler：LangChain 回调基类，用于监听大模型调用的生命周期事件
from langchain_core.callbacks import BaseCallbackHandler


LLM_RETRYABLE_ERROR_MARKERS = (
    "RemoteDisconnected",
    "Connection aborted",
    "Connection reset",
    "Connection refused",
    "Read timed out",
    "Timeout",
    "timed out",
    "Max retries exceeded",
    "temporarily unavailable",
    "502",
    "503",
    "504",
)


def load_api_config() -> dict:
    """从 python-ai/api.yml 读取大模型 API 配置。

    配置文件包含通义千问和豆包的 API Key，格式示例：
        tongyi:
          api_key: "sk-xxx"
        doubao:
          ARK_API_KEY: "xxx"

    Returns:
        dict: 解析后的配置字典，文件不存在时返回空字典。
    """
    # 定位 api.yml：与本文件（ai_runtime.py）同目录
    api_config_path = Path(__file__).with_name("api.yml")

    # 如果配置文件不存在，返回空字典，避免启动报错
    if not api_config_path.exists():
        return {}

    # 读取并解析 YAML 配置，空文件返回空字典
    return yaml.safe_load(api_config_path.read_text(encoding="utf-8")) or {}


# 模块加载时立即读取配置，后续 LLM 实例初始化依赖这些环境变量
api_config = load_api_config()

# 提取通义千问 API Key，strip() 去除可能的首尾空白
tongyi_api_key = str(api_config.get("tongyi", {}).get("api_key", "")).strip()

# 提取豆包 API Key，用于豆包图片生成（SeedDream 模型）
doubao_api_key = str(api_config.get("doubao", {}).get("ARK_API_KEY", "")).strip()


# 将 API Key 写入环境变量，LangChain ChatTongyi 和豆包 OpenAI SDK 通过环境变量自动读取
if tongyi_api_key:
    os.environ["DASHSCOPE_API_KEY"] = tongyi_api_key
if doubao_api_key:
    os.environ["ARK_API_KEY"] = doubao_api_key


# ── LLM 实例定义 ──────────────────────────────────────────────────────
# 通义千问 qwen-max 模型，不同场景使用不同参数配置

# 温度为 0 的 LLM：用于需要确定性输出的场景（如判断分卷数量、小节数量、资产识别）
# temperature=0 表示输出最确定性的结果，top_p=0.2 进一步限制采样范围
# streaming=False 因为结构化输出不支持流式
llm_temperature_0 = ChatTongyi(
    model="qwen-max",       # 通义千问最强大的模型
    temperature=0,           # 温度为 0，输出最确定性
    top_p=0.2,               # 核采样概率，限制为最可能的 20% token
    streaming=False,         # 非流式，用于结构化输出
)

# 结构化输出 LLM：用于需要返回 JSON 结构的场景（如大纲生成、分卷生成、脚本生成）
# temperature=0.8 提供适度创造性，streaming=False 因为 with_structured_output 需要完整 JSON
structured_llm_base = ChatTongyi(
    model="qwen-max",       # 通义千问最强大的模型
    temperature=0.8,         # 适度创造性
    streaming=False,         # 非流式，结构化输出需要完整 JSON
)

# 流式文本 LLM：用于生成长篇正文的场景（如小节故事生成）
# streaming=True 开启流式输出，控制台可以实时看到生成的 token
streaming_text_llm_base = ChatTongyi(
    model="qwen-max",       # 通义千问最强大的模型
    temperature=0.8,         # 适度创造性
    streaming=True,          # 流式输出，控制台实时打印 token
)

# 路由LLM
Router = ChatTongyi(
    model="qwen-max",   # 通义千问最强大的模型
    temperature=0,           # 温度为 0，输出最确定性
    top_p=0.2,               # 核采样概率，限制为最可能的 20% token
    streaming=False,         # 非流式，用于结构化输出
)


def get_doubao_image_client():
    """懒加载豆包图片生成客户端。

    使用 OpenAI SDK 兼容接口调用豆包 SeedDream 4.5 模型生成图片。
    采用懒加载模式，避免未安装 openai 包时影响 FastAPI 启动。

    Returns:
        OpenAI: 配置好豆包 API 的 OpenAI 客户端实例。

    Raises:
        RuntimeError: 如果 ARK_API_KEY 环境变量未设置。
    """
    # 延迟导入 openai，只有实际调用图片生成时才需要
    from openai import OpenAI

    # 从环境变量读取豆包 API Key
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise RuntimeError("ARK_API_KEY is required for Doubao image generation")

    # 创建 OpenAI 客户端，指向豆包 API 端点
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",  # 豆包 API 地址
        api_key=api_key,                                        # 豆包 API Key
    )


class ConsoleStreamingCallback(BaseCallbackHandler):
    """LangChain 控制台回调处理器。

    在大模型调用的各个生命周期阶段打印进度日志到 Python 控制台，
    便于开发调试时实时观察生成进度。支持流式 token 打印。
    """

    def __init__(self, trace_id: str, scope: str = "story-outline"):
        """初始化一次大模型调用的控制台日志上下文。

        Args:
            trace_id:  本次请求的唯一追踪 ID（8 位十六进制），用于关联日志。
            scope:     业务范围标识，如 "story-outline"、"volume-outline"、"chat-agent"。
        """
        # 追踪 ID，用于在日志中区分不同请求
        self.trace_id = trace_id

        # 业务范围标识，用于日志前缀
        self.scope = scope

        # 记录请求开始时间，用于计算各阶段耗时
        self.started_at = time.perf_counter()

        # 标记是否已经开始打印流式 token，用于控制首行前缀
        self.has_streamed_tokens = False

    def _elapsed(self) -> str:
        """计算当前请求从开始到现在的耗时文本。

        Returns:
            str: 格式化的耗时，如 "1.2s"、"30.5s"。
        """
        return f"{time.perf_counter() - self.started_at:.1f}s"

    def on_chat_model_start(self, serialized, messages, **kwargs) -> None:
        """LangChain ChatModel 请求开始时的回调。

        当 LangChain 调用 ChatTongyi 时自动触发，打印请求开始日志。

        Args:
            serialized: 模型序列化信息（未使用）。
            messages:   发送给模型的消息列表（未使用）。
        """
        print(f"[{self.scope}][{self.trace_id}][{self._elapsed()}] chat model request started", flush=True)

    def on_llm_start(self, serialized, prompts, **kwargs) -> None:
        """LangChain LLM 请求开始时的回调。

        当 LangChain 调用 LLM 时自动触发，打印请求开始日志。

        Args:
            serialized: 模型序列化信息（未使用）。
            prompts:    发送给模型的提示词列表（未使用）。
        """
        print(f"[{self.scope}][{self.trace_id}][{self._elapsed()}] llm request started", flush=True)

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """流式打印模型生成的 token。

        当模型开启 streaming=True 时，每生成一个 token 就会触发此回调。
        结构化输出（streaming=False）通常不会触发此回调。

        Args:
            token: 模型生成的单个 token 文本。
        """
        # 空 token 跳过
        if not token:
            return

        # 首次收到 token 时打印一行前缀，后续 token 直接追加
        if not self.has_streamed_tokens:
            self.has_streamed_tokens = True
            print(f"[{self.scope}][{self.trace_id}][{self._elapsed()}] streaming tokens:", flush=True)

        # 打印 token，不换行，实现流式效果
        print(token, end="", flush=True)

    def on_llm_end(self, response, **kwargs) -> None:
        """大模型返回结束时的回调。

        如果之前有流式 token 输出，先补一个换行；然后打印完成日志。

        Args:
            response: 模型返回的完整响应（未使用）。
        """
        # 如果有流式输出过，补一个换行
        if self.has_streamed_tokens:
            print("", flush=True)
        print(f"[{self.scope}][{self.trace_id}][{self._elapsed()}] llm response finished", flush=True)

    def on_llm_error(self, error, **kwargs) -> None:
        """大模型调用异常时的回调。

        打印错误日志，便于排查问题。

        Args:
            error: 异常对象。
        """
        # 如果有流式输出过，补一个换行
        if self.has_streamed_tokens:
            print("", flush=True)
        print(f"[{self.scope}][{self.trace_id}][{self._elapsed()}] llm error: {error}", flush=True)


def log_progress(trace_id: str, message: str, started_at: float, scope: str = "story-outline") -> None:
    """打印阶段性进度日志。

    在业务逻辑的关键节点调用，记录当前阶段和耗时，
    便于排查慢请求和定位问题。

    Args:
        trace_id:   本次请求的唯一追踪 ID。
        message:    进度描述信息。
        started_at: 请求开始时间戳（time.perf_counter()）。
        scope:      业务范围标识，默认 "story-outline"。
    """
    # 计算从请求开始到现在的耗时
    elapsed = time.perf_counter() - started_at

    # 打印格式：[scope][trace_id][耗时] 消息内容
    print(f"[{scope}][{trace_id}][{elapsed:.1f}s] {message}", flush=True)


def invoke_llm_with_retry(
    chain,
    payload: dict,
    *,
    config: dict | None = None,
    trace_id: str = "-",
    started_at: float | None = None,
    scope: str = "llm",
    max_attempts: int = 3,
    base_delay_seconds: float = 2.0,
):
    """Invoke a LangChain chain with retry for transient upstream/network errors.

    Args:
        chain:              LangChain runnable chain.
        payload:            Prompt variables passed to .invoke().
        config:             Optional LangChain invoke config.
        trace_id:           Request trace id used in logs.
        started_at:         Request start time. If omitted, a new timer is used.
        scope:              Business scope used in logs.
        max_attempts:       Maximum total attempts, including the first one.
        base_delay_seconds: Initial retry delay before exponential backoff.

    Returns:
        The chain.invoke(...) result.

    Raises:
        Exception: Re-raises the last exception when it is not retryable or retries are exhausted.
    """
    timer = started_at if started_at is not None else time.perf_counter()
    attempt = 1

    while True:
        try:
            if attempt > 1:
                log_progress(trace_id, f"llm retry attempt {attempt}/{max_attempts} started", timer, scope)
            return chain.invoke(payload, config=config)
        except Exception as exc:
            if attempt >= max_attempts or not is_retryable_llm_error(exc):
                raise

            delay = base_delay_seconds * (2 ** (attempt - 1)) + random.uniform(0, 0.8)
            log_progress(
                trace_id,
                f"llm transient error, retrying in {delay:.1f}s ({attempt}/{max_attempts}): {exc}",
                timer,
                scope,
            )
            time.sleep(delay)
            attempt += 1


def invoke_structured_output_with_guard(
    chain,
    payload: dict,
    output_model: type,
    *,
    config: dict | None = None,
    trace_id: str = "-",
    started_at: float | None = None,
    scope: str = "llm",
    max_generation_attempts: int = 3,
):
    """Invoke a structured-output chain with JSON validation, local repair, and bounded regeneration.

    This guard protects calls using ``with_structured_output(...)``. Some providers occasionally
    return malformed tool-call JSON, for example an unterminated string in a long ``content`` field.
    The flow is:
    1. Invoke the chain and validate the returned object against ``output_model``.
    2. If LangChain exposes malformed JSON in the exception, try a local JSON repair and validate it.
    3. If repair fails, regenerate. At most ``max_generation_attempts`` model generations are made.
    4. If all generations fail validation, re-raise the final exception as a real failure.
    """
    timer = started_at if started_at is not None else time.perf_counter()
    attempts = max(max_generation_attempts, 1)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            if attempt > 1:
                log_progress(trace_id, f"structured output regeneration attempt {attempt}/{attempts} started", timer, scope)
            result = invoke_llm_with_retry(
                chain,
                payload,
                config=config,
                trace_id=trace_id,
                started_at=timer,
                scope=scope,
            )
            return validate_structured_output(result, output_model)
        except Exception as exc:
            last_error = exc

            repaired = repair_structured_output_from_exception(exc, output_model)
            if repaired is not None:
                log_progress(trace_id, f"structured output repaired locally on attempt {attempt}/{attempts}", timer, scope)
                return repaired

            # Network/upstream failures are already retried by invoke_llm_with_retry. Do not turn
            # them into extra structured-output regenerations, otherwise a real outage may fan out
            # into many slow attempts.
            if is_retryable_llm_error(exc):
                raise

            if attempt >= attempts:
                log_progress(trace_id, f"structured output validation failed after {attempts} attempts: {exc}", timer, scope)
                raise

            log_progress(
                trace_id,
                f"structured output invalid and repair failed; regenerating ({attempt}/{attempts}): {exc}",
                timer,
                scope,
            )

    raise last_error  # pragma: no cover; loop always returns or raises before this point.


def validate_structured_output(value: Any, output_model: type):
    """Validate a structured LLM value against the expected Pydantic model."""
    if isinstance(value, output_model):
        return value

    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True)
    elif hasattr(value, "dict"):
        value = value.dict(by_alias=True)

    if hasattr(output_model, "model_validate"):
        return output_model.model_validate(value)
    return output_model.parse_obj(value)


def repair_structured_output_from_exception(error: Exception, output_model: type):
    """Try to repair malformed JSON embedded in a LangChain structured-output exception."""
    raw_json = extract_malformed_json_from_exception(error)
    if not raw_json:
        return None

    repaired_data = parse_json_with_repair(raw_json)
    if repaired_data is None:
        return None

    try:
        return validate_structured_output(repaired_data, output_model)
    except Exception:
        return None


def extract_malformed_json_from_exception(error: Exception) -> str | None:
    """Extract the raw JSON-like tool-call arguments from common LangChain parser errors."""
    message = str(error)
    patterns = [
        r"arguments:\s*(.*?)\s*are not valid JSON",
        r"Invalid json output:\s*(.*)",
        r"Could not parse.*?json.*?:\s*(.*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def parse_json_with_repair(raw_text: str) -> Any | None:
    """Parse JSON, applying small deterministic repairs for common LLM formatting mistakes."""
    candidates = build_json_repair_candidates(raw_text)
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def build_json_repair_candidates(raw_text: str) -> list[str]:
    """Build increasingly repaired JSON candidates from raw LLM output."""
    stripped = strip_json_markdown_fence(raw_text).strip()
    extracted = extract_outer_json_candidate(stripped)
    quote_escaped = escape_unescaped_quotes_and_controls(extracted)
    completed = complete_truncated_json(extracted)
    quote_escaped_completed = complete_truncated_json(quote_escaped)

    candidates: list[str] = []
    for candidate in [stripped, extracted, quote_escaped, completed, quote_escaped_completed]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def strip_json_markdown_fence(text: str) -> str:
    """Remove a surrounding Markdown code fence if the model emitted one."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def extract_outer_json_candidate(text: str) -> str:
    """Keep the text from the first JSON opener to the last JSON closer when possible."""
    first_object = text.find("{")
    first_array = text.find("[")
    starts = [index for index in [first_object, first_array] if index >= 0]
    if not starts:
        return text
    start = min(starts)

    last_object = text.rfind("}")
    last_array = text.rfind("]")
    end = max(last_object, last_array)
    if end > start:
        return text[start:end + 1]
    return text[start:]


def escape_unescaped_quotes_and_controls(text: str) -> str:
    """Escape raw newlines and quote characters that appear inside JSON strings."""
    output: list[str] = []
    in_string = False
    escaped = False
    length = len(text)

    for index, char in enumerate(text):
        if not in_string:
            output.append(char)
            if char == '"':
                in_string = True
                escaped = False
            continue

        if escaped:
            output.append(char)
            escaped = False
            continue

        if char == "\\":
            output.append(char)
            escaped = True
            continue

        if char == '"':
            next_non_space = next((text[pos] for pos in range(index + 1, length) if not text[pos].isspace()), "")
            if next_non_space in {":", ",", "}", "]", ""}:
                output.append(char)
                in_string = False
            else:
                output.append('\\"')
            continue

        if char == "\n":
            output.append("\\n")
        elif char == "\r":
            output.append("\\r")
        elif char == "\t":
            output.append("\\t")
        else:
            output.append(char)

    return "".join(output)


def complete_truncated_json(text: str) -> str:
    """Close a truncated JSON object/array/string when the ending was cut off."""
    in_string = False
    escaped = False
    stack: list[str] = []

    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in {"}", "]"} and stack and stack[-1] == char:
            stack.pop()

    suffix = ""
    if in_string:
        stripped_length = len(text.rstrip())
        trailing_whitespace = text[stripped_length:]
        if stack and stripped_length > 0 and text[stripped_length - 1] == stack[-1]:
            expected_closer = stack.pop()
            return text[:stripped_length - 1] + '"' + expected_closer + trailing_whitespace + "".join(reversed(stack))
        if text.rstrip().endswith("\\"):
            suffix += "\\"
        suffix += '"'
    if stack:
        suffix += "".join(reversed(stack))
    return text + suffix


def is_retryable_llm_error(error: Exception) -> bool:
    """Return True when an LLM exception looks like a transient network/upstream failure."""
    message = repr(error)
    return any(marker in message for marker in LLM_RETRYABLE_ERROR_MARKERS)
