from __future__ import annotations

import argparse
import asyncio
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

import edge_tts


TTS_MARKER = '<span class="tts">'
NUMERIC_MD_PATTERN = re.compile(r"^(\d+)\.md$")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
HIGHLIGHT_MARK_PATTERN = re.compile(r"\^\^([^^]*)\^\^")
FFMPEG_ENCODER_FLAG_PATTERN = re.compile(r"[A-Z\.]{6}")
DEFAULT_OUTPUT_DIR_NAME = "產生複習檔案"
DEFAULT_THEME_COLOR = "#72e3fd"
OUTPUT_SAMPLE_RATE = 44100
OUTPUT_CHANNELS = 2
OUTPUT_BITRATE = "128k"
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 30
VIDEO_FONT_SIZE = 220
VIDEO_FONT_COLOR = "white"
SUBTITLE_RENDER_SIGNATURE = "bilingual-subtitles-v4"
TRANSLATION_CACHE_FILENAME = "_translation_cache.json"
TRANSLATE_FROM = "en"
TRANSLATE_TO = "zh-TW"
TRANSLATE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
TRANSLATION_REQUEST_TIMEOUT_SECONDS = 12.0
TRANSLATION_CONCURRENCY = 4
SUBTITLE_TOP_FONT_SIZE = 44
SUBTITLE_BOTTOM_FONT_SIZE = 34
SUBTITLE_MARGIN_LR = 96
SUBTITLE_TOP_MARGIN = 128
SUBTITLE_BOTTOM_MARGIN = 110
SUBTITLE_OUTLINE = 2.4
SUBTITLE_SHADOW = 0
ESTIMATED_CHARS_PER_SECOND = 13.0
ESTIMATED_VIDEO_BITRATE_BPS_GPU = 220_000
ESTIMATED_VIDEO_BITRATE_BPS_CPU = 300_000
ESTIMATED_CONTAINER_OVERHEAD_BYTES = 180 * 1024
GPU_MONITOR_TIMEOUT_SECONDS = 0.35
GPU_MONITOR_MIN_INTERVAL_SECONDS = 0.25
GPU_MONITOR_STALE_SECONDS = 5.0
RESOURCE_MONITOR_INTERVAL_MS = 1500
PROGRESS_SCAN_MIN_INTERVAL_SECONDS = 0.25
CLI_PROGRESS_REPORT_MIN_INTERVAL_SECONDS = 0.1
CLI_PROGRESS_BAR_WIDTH = 20
CLI_USAGE_BAR_WIDTH = 20
CLI_SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
TEMP_WORK_DIR_PREFIX = "tts_tmp_"
OUTPUT_DIR_KEEP_NAMES = {"一次", "兩次"}
MAX_FILE_CONCURRENCY = 6
MAX_GPU_VIDEO_ENCODE_CONCURRENCY = 2
MAX_CPU_VIDEO_ENCODE_CONCURRENCY = 4
MANIFEST_FILENAME = "_convert_manifest.json"
SENTENCE_CACHE_FILENAME = "_sentence_cache.json"
BLOCKING_PROXY_HOSTS = {"127.0.0.1", "localhost", "::1"}
PROXY_ENV_KEYS = (
    "ALL_PROXY",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "all_proxy",
    "http_proxy",
    "https_proxy",
    "GIT_HTTP_PROXY",
    "GIT_HTTPS_PROXY",
    "git_http_proxy",
    "git_https_proxy",
)
PREFERRED_DEFAULT_VOICES = (
    "en-US-JennyNeural",
    "en-US-AriaNeural",
    "en-US-GuyNeural",
)
NVIDIA_SMI_CANDIDATES = (
    "nvidia-smi",
    r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
    r"C:\Windows\System32\nvidia-smi.exe",
)

_NVIDIA_SMI_RESOLVED = False
_NVIDIA_SMI_COMMAND: str | None = None
_GPU_USAGE_CACHE_AT = 0.0
_GPU_USAGE_CACHE_VALUE: float | None = None
_PSUTIL_RESOLVED = False
_PSUTIL_MODULE = None
QT_NOISY_WARNING_PATTERNS = (
    "QWindowsBackingStore::flush: BitBlt failed",
    "QBackingStore::endPaint() called with active painter",
)


class ConversionError(RuntimeError):
    pass


class ConversionCancelled(ConversionError):
    pass


@dataclass
class ExecutionControl:
    stop_event: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    running_processes: set[subprocess.Popen] = field(default_factory=set)

    def register_process(self, proc: subprocess.Popen) -> None:
        with self.lock:
            self.running_processes.add(proc)

    def unregister_process(self, proc: subprocess.Popen) -> None:
        with self.lock:
            self.running_processes.discard(proc)

    def terminate_all_processes(self) -> None:
        with self.lock:
            processes = list(self.running_processes)
        for proc in processes:
            terminate_process(proc)


_EXECUTION_CONTEXT = threading.local()


class execution_context:
    def __init__(self, control: ExecutionControl | None):
        self.control = control
        self.previous: ExecutionControl | None = None

    def __enter__(self) -> None:
        self.previous = getattr(_EXECUTION_CONTEXT, "control", None)
        _EXECUTION_CONTEXT.control = self.control
        return None

    def __exit__(self, exc_type, exc, tb) -> None:
        _EXECUTION_CONTEXT.control = self.previous
        return None


def get_execution_control() -> ExecutionControl | None:
    return getattr(_EXECUTION_CONTEXT, "control", None)


def assert_not_cancelled() -> None:
    control = get_execution_control()
    if control is not None and control.stop_event.is_set():
        raise ConversionCancelled("使用者已強制停止轉換。")


def terminate_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=1.0)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=1.0)
        except Exception:
            pass


@dataclass
class ConvertOptions:
    voice: str
    rate_multiplier: float  # 倍率：1.0=1倍速，1.5=1.5倍速
    gap_seconds: float
    use_gpu: bool
    repeat_mode: str  # "once" 或 "twice" 或 "both"


@dataclass(frozen=True)
class SubtitleSentence:
    english: str
    chinese: str


@dataclass(frozen=True)
class SubtitleCue:
    start_seconds: float
    end_seconds: float
    english: str
    chinese: str


@dataclass(frozen=True)
class RenderedMarkdownOutput:
    video_file: Path
    audio_file: Path
    subtitle_cues: list[SubtitleCue]
    audio_duration_seconds: float


def scan_numeric_markdown_files(workspace_root: Path) -> list[Path]:
    files: list[tuple[int, Path]] = []
    for item in workspace_root.iterdir():
        if not item.is_file():
            continue
        match = NUMERIC_MD_PATTERN.match(item.name)
        if match:
            files.append((int(match.group(1)), item))
    files.sort(key=lambda pair: pair[0])
    return [path for _, path in files]


def build_range_mp4_name(markdown_files: list[Path], suffix: str = "") -> str:
    if not markdown_files:
        return f"0~0{suffix}.mp4"
    min_stem = markdown_files[0].stem
    max_stem = markdown_files[-1].stem
    return f"{min_stem}~{max_stem}{suffix}.mp4"


def compute_file_hash(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(data).hexdigest()


def read_file_stat_signature(path: Path) -> tuple[int, int]:
    stat = path.stat()
    size = int(stat.st_size)
    mtime_ns = int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)))
    return size, mtime_ns


def _safe_int(value: object, fallback: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def options_signature(options: ConvertOptions) -> str:
    return "|".join(
        [
            SUBTITLE_RENDER_SIGNATURE,
            options.voice,
            f"{options.rate_multiplier:.4f}",
            f"{options.gap_seconds:.4f}",
            "gpu" if options.use_gpu else "cpu",
            options.repeat_mode,
        ]
    )


def load_manifest(root_output_dir: Path) -> dict:
    path = root_output_dir / MANIFEST_FILENAME
    if not path.exists():
        return {"options_signature": "", "files": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"options_signature": "", "files": {}}

    if not isinstance(raw, dict):
        return {"options_signature": "", "files": {}}

    options_sig = raw.get("options_signature")
    if not isinstance(options_sig, str):
        legacy_options = raw.get("options")
        options_sig = legacy_options if isinstance(legacy_options, str) else ""
    files = raw.get("files")
    if not isinstance(files, dict):
        files = {}
    return {"options_signature": options_sig, "files": files}


def save_manifest(root_output_dir: Path, manifest: dict) -> None:
    path = root_output_dir / MANIFEST_FILENAME
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def load_sentence_cache(root_output_dir: Path) -> dict:
    path = root_output_dir / SENTENCE_CACHE_FILENAME
    if not path.exists():
        return {"files": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"files": {}}
    if not isinstance(raw, dict):
        return {"files": {}}
    files = raw.get("files")
    if not isinstance(files, dict):
        files = {}
    return {"files": files}


def save_sentence_cache(root_output_dir: Path, cache_doc: dict) -> None:
    path = root_output_dir / SENTENCE_CACHE_FILENAME
    path.write_text(json.dumps(cache_doc, ensure_ascii=False, indent=2), encoding="utf-8")


def load_translation_cache(root_output_dir: Path) -> dict:
    path = root_output_dir / TRANSLATION_CACHE_FILENAME
    if not path.exists():
        return {"translations": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"translations": {}}
    if not isinstance(raw, dict):
        return {"translations": {}}
    translations = raw.get("translations")
    if not isinstance(translations, dict):
        translations = {}
    return {"translations": translations}


def save_translation_cache(root_output_dir: Path, cache_doc: dict) -> None:
    path = root_output_dir / TRANSLATION_CACHE_FILENAME
    path.write_text(json.dumps(cache_doc, ensure_ascii=False, indent=2), encoding="utf-8")


def build_markdown_metadata(
    markdown_files: list[Path],
    previous_files: dict[str, dict],
) -> tuple[dict[Path, dict[str, int | str]], int, int]:
    metadata: dict[Path, dict[str, int | str]] = {}
    reused_hash_count = 0
    recomputed_hash_count = 0
    for md_path in markdown_files:
        assert_not_cancelled()
        size, mtime_ns = read_file_stat_signature(md_path)
        previous = previous_files.get(md_path.name, {})
        if not isinstance(previous, dict):
            previous = {}
        previous_hash = previous.get("hash")
        previous_size = _safe_int(previous.get("size"))
        previous_mtime_ns = _safe_int(previous.get("mtime_ns"))
        if (
            isinstance(previous_hash, str)
            and previous_size == size
            and previous_mtime_ns == mtime_ns
        ):
            md_hash = previous_hash
            reused_hash_count += 1
        else:
            md_hash = compute_file_hash(md_path)
            recomputed_hash_count += 1
        metadata[md_path] = {
            "name": md_path.name,
            "size": size,
            "mtime_ns": mtime_ns,
            "hash": md_hash,
        }
    return metadata, reused_hash_count, recomputed_hash_count


def build_effective_sentence_cache(
    markdown_files: list[Path],
    markdown_metadata: dict[Path, dict[str, int | str]],
    provided_sentence_cache: dict[Path, list[str]] | None,
    sentence_cache_doc: dict,
) -> tuple[dict[Path, list[str]], dict, int]:
    persisted_files = sentence_cache_doc.get("files", {})
    if not isinstance(persisted_files, dict):
        persisted_files = {}
    effective_cache: dict[Path, list[str]] = {}
    updated_files: dict[str, dict] = {}
    reused_sentence_files = 0

    for md_path in markdown_files:
        assert_not_cancelled()
        md_meta = markdown_metadata[md_path]
        md_hash = str(md_meta["hash"])
        md_size = int(md_meta["size"])
        md_mtime_ns = int(md_meta["mtime_ns"])
        sentences: list[str] | None = None

        if provided_sentence_cache is not None:
            provided = provided_sentence_cache.get(md_path)
            if provided is not None:
                sentences = [str(item) for item in provided]

        if sentences is None:
            persisted = persisted_files.get(md_path.name, {})
            if not isinstance(persisted, dict):
                persisted = {}
            persisted_hash = persisted.get("hash")
            persisted_size = _safe_int(persisted.get("size"))
            persisted_mtime_ns = _safe_int(persisted.get("mtime_ns"))
            persisted_sentences = persisted.get("sentences")
            if (
                isinstance(persisted_hash, str)
                and persisted_hash == md_hash
                and persisted_size == md_size
                and persisted_mtime_ns == md_mtime_ns
                and isinstance(persisted_sentences, list)
            ):
                sentences = [str(item) for item in persisted_sentences]
                reused_sentence_files += 1
            else:
                sentences = extract_tts_sentences(md_path)

        effective_cache[md_path] = sentences
        updated_files[md_path.name] = {
            "hash": md_hash,
            "size": md_size,
            "mtime_ns": md_mtime_ns,
            "sentences": sentences,
        }

    return effective_cache, {"files": updated_files}, reused_sentence_files


def format_size_bytes(size_bytes: int) -> str:
    value = float(max(0, size_bytes))
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{int(size_bytes)} B"


def bitrate_to_bps(bitrate: str) -> int:
    text = bitrate.strip().lower()
    if text.endswith("k"):
        return int(float(text[:-1]) * 1_000)
    if text.endswith("m"):
        return int(float(text[:-1]) * 1_000_000)
    return int(float(text))


def estimate_sentence_duration_seconds(text: str, rate_multiplier: float) -> float:
    cleaned = re.sub(r"\s+", "", text)
    char_count = len(cleaned)
    if char_count <= 0:
        return 0.0
    base_seconds = char_count / ESTIMATED_CHARS_PER_SECOND
    speed = max(0.5, min(2.0, float(rate_multiplier)))
    return max(0.25, base_seconds / speed)


def estimate_mode_duration_seconds(
    sentences: list[str],
    rate_multiplier: float,
    gap_seconds: float,
    repeat_sentences: bool,
) -> float:
    if not sentences:
        return 0.0
    per_sentence_seconds = sum(
        estimate_sentence_duration_seconds(sentence, rate_multiplier) for sentence in sentences
    )
    playback_count = len(sentences) * (2 if repeat_sentences else 1)
    speech_seconds = per_sentence_seconds * (2 if repeat_sentences else 1)
    gap_count = max(0, playback_count - 1)
    return speech_seconds + gap_count * max(0.0, gap_seconds)


def estimate_mp4_size_bytes(duration_seconds: float, use_gpu: bool) -> int:
    audio_bps = bitrate_to_bps(OUTPUT_BITRATE)
    video_bps = ESTIMATED_VIDEO_BITRATE_BPS_GPU if use_gpu else ESTIMATED_VIDEO_BITRATE_BPS_CPU
    payload_bytes = max(0.0, duration_seconds) * (audio_bps + video_bps) / 8.0
    return int(payload_bytes + ESTIMATED_CONTAINER_OVERHEAD_BYTES)


def build_size_progress_plan(
    workspace_root: Path,
    markdown_files: list[Path],
    sentence_cache: dict[Path, list[str]],
    options: ConvertOptions,
) -> tuple[int, list[Path]]:
    root_output_dir = workspace_root / DEFAULT_OUTPUT_DIR_NAME
    tracked_files: list[Path] = []
    estimated_total_bytes = 0
    selected_modes: list[tuple[str, bool, str]] = []

    if options.repeat_mode in ("once", "both"):
        selected_modes.append(("一次", False, "_一次"))
    if options.repeat_mode in ("twice", "both"):
        selected_modes.append(("兩次", True, "_兩次"))

    for mode_name, repeat_sentences, suffix in selected_modes:
        mode_output_dir = root_output_dir / mode_name
        per_file_durations: list[float] = []
        generated_count = 0
        for md_path in markdown_files:
            sentences = sentence_cache.get(md_path, [])
            if not sentences:
                continue
            duration_seconds = estimate_mode_duration_seconds(
                sentences=sentences,
                rate_multiplier=options.rate_multiplier,
                gap_seconds=options.gap_seconds,
                repeat_sentences=repeat_sentences,
            )
            per_file_durations.append(duration_seconds)
            output_path = mode_output_dir / f"{md_path.stem}{suffix}.mp4"
            tracked_files.append(output_path)
            estimated_total_bytes += estimate_mp4_size_bytes(
                duration_seconds=duration_seconds,
                use_gpu=options.use_gpu,
            )
            generated_count += 1

        if generated_count > 0:
            merged_name = build_range_mp4_name(markdown_files, suffix)
            merged_path = mode_output_dir / merged_name
            tracked_files.append(merged_path)
            merged_seconds = sum(per_file_durations)
            if options.gap_seconds > 0 and generated_count > 1:
                merged_seconds += options.gap_seconds * (generated_count - 1)
            estimated_total_bytes += estimate_mp4_size_bytes(
                duration_seconds=merged_seconds,
                use_gpu=options.use_gpu,
            )

    return max(1, estimated_total_bytes), tracked_files


def read_cpu_usage_percent() -> float | None:
    global _PSUTIL_RESOLVED, _PSUTIL_MODULE
    if not _PSUTIL_RESOLVED:
        _PSUTIL_RESOLVED = True
        try:
            import psutil  # type: ignore
        except Exception:
            _PSUTIL_MODULE = None
        else:
            _PSUTIL_MODULE = psutil

    if _PSUTIL_MODULE is None:
        return None
    try:
        return float(_PSUTIL_MODULE.cpu_percent(interval=None))
    except Exception:
        return None


def resolve_nvidia_smi_command() -> str | None:
    global _NVIDIA_SMI_RESOLVED, _NVIDIA_SMI_COMMAND
    if _NVIDIA_SMI_RESOLVED:
        return _NVIDIA_SMI_COMMAND

    _NVIDIA_SMI_RESOLVED = True
    for candidate in NVIDIA_SMI_CANDIDATES:
        if candidate == "nvidia-smi":
            found = shutil.which(candidate)
            if found:
                _NVIDIA_SMI_COMMAND = found
                return _NVIDIA_SMI_COMMAND
            continue
        if Path(candidate).exists():
            _NVIDIA_SMI_COMMAND = candidate
            return _NVIDIA_SMI_COMMAND
    _NVIDIA_SMI_COMMAND = None
    return None


def read_gpu_usage_percent() -> float | None:
    global _GPU_USAGE_CACHE_AT, _GPU_USAGE_CACHE_VALUE

    now = time.monotonic()
    cache_age = now - _GPU_USAGE_CACHE_AT
    if _GPU_USAGE_CACHE_VALUE is not None and cache_age < GPU_MONITOR_MIN_INTERVAL_SECONDS:
        return _GPU_USAGE_CACHE_VALUE

    nvidia_smi = resolve_nvidia_smi_command()
    if not nvidia_smi:
        if _GPU_USAGE_CACHE_VALUE is not None and cache_age <= GPU_MONITOR_STALE_SECONDS:
            return _GPU_USAGE_CACHE_VALUE
        return None

    query_fields_list = (
        "utilization.gpu,utilization.encoder",
        "utilization.gpu",
    )
    proc: subprocess.CompletedProcess[str] | None = None
    for query_fields in query_fields_list:
        try:
            proc = subprocess.run(
                [
                    nvidia_smi,
                    f"--query-gpu={query_fields}",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=GPU_MONITOR_TIMEOUT_SECONDS,
            )
        except (subprocess.TimeoutExpired, OSError, ValueError):
            proc = None
            continue
        if proc.returncode == 0:
            break
        proc = None

    if proc is None:
        if _GPU_USAGE_CACHE_VALUE is not None and cache_age <= GPU_MONITOR_STALE_SECONDS:
            return _GPU_USAGE_CACHE_VALUE
        return None

    gpu_values: list[float] = []
    for line in proc.stdout.splitlines():
        text = line.strip()
        if not text:
            continue
        parts = [part.strip() for part in text.split(",")]
        numeric_values: list[float] = []
        for part in parts:
            if not part:
                continue
            try:
                numeric_values.append(float(part))
            except ValueError:
                continue
        if not numeric_values:
            continue
        # NVENC 轉檔時 encoder utilization 常比 core utilization 更能反映實際負載。
        gpu_values.append(max(numeric_values))

    if not gpu_values:
        if _GPU_USAGE_CACHE_VALUE is not None and cache_age <= GPU_MONITOR_STALE_SECONDS:
            return _GPU_USAGE_CACHE_VALUE
        return None
    # 多 GPU 時取最高利用率的那張卡，避免平均值稀釋。
    usage = max(gpu_values)
    usage = max(0.0, min(100.0, usage))
    _GPU_USAGE_CACHE_VALUE = usage
    _GPU_USAGE_CACHE_AT = now
    return usage


def extract_tts_sentences(md_path: Path) -> list[str]:
    raw = md_path.read_text(encoding="utf-8")
    sentences: list[str] = []
    for line in raw.splitlines():
        if TTS_MARKER not in line:
            continue
        text = line.split(TTS_MARKER, 1)[1]
        text = HTML_TAG_PATTERN.sub("", text)
        text = html.unescape(text).strip()
        text = HIGHLIGHT_MARK_PATTERN.sub(r"\1", text)  # 移除^^符號，保留內容
        if text and is_speakable_text(text):
            sentences.append(text)
    return sentences


def translate_text_to_zh(text: str, retries: int = 2) -> str:
    disable_blocking_proxy_env()
    normalized = text.strip()
    if not normalized:
        return ""
    encoded_text = quote(normalized, safe="")
    url = (
        f"{TRANSLATE_ENDPOINT}?client=gtx&sl={quote(TRANSLATE_FROM)}"
        f"&tl={quote(TRANSLATE_TO)}&dt=t&q={encoded_text}"
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        assert_not_cancelled()
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urlopen(request, timeout=TRANSLATION_REQUEST_TIMEOUT_SECONDS) as response:
                payload = response.read().decode("utf-8")
            data = json.loads(payload)
            translated = (
                "".join(str(item[0]) for item in data[0] if isinstance(item, list) and item)
                if isinstance(data, list) and data and isinstance(data[0], list)
                else ""
            )
            translated = translated.strip()
            if translated:
                return html.unescape(translated)
            raise ConversionError("翻譯結果為空字串。")
        except Exception as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(0.35 * (attempt + 1))
    preview = normalized if len(normalized) <= 80 else normalized[:77] + "..."
    raise ConversionError(f"無法取得中文翻譯：{preview}（{last_error}）")


async def build_translation_map(
    root_output_dir: Path,
    sentences: Iterable[str],
    progress: Callable[[str], None],
) -> tuple[dict[str, str], int, int]:
    cache_doc = load_translation_cache(root_output_dir)
    cached_translations = cache_doc.get("translations", {})
    if not isinstance(cached_translations, dict):
        cached_translations = {}

    unique_sentences: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        normalized = sentence.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_sentences.append(normalized)

    translation_map: dict[str, str] = {}
    cache_hits = 0
    missing_sentences: list[str] = []
    for sentence in unique_sentences:
        cached = cached_translations.get(sentence)
        if isinstance(cached, str) and cached.strip():
            translation_map[sentence] = cached.strip()
            cache_hits += 1
        else:
            missing_sentences.append(sentence)

    translated_count = 0
    if missing_sentences:
        progress(f"字幕翻譯：新增 {len(missing_sentences)} 句")
        semaphore = asyncio.Semaphore(TRANSLATION_CONCURRENCY)

        async def run_one(sentence: str) -> tuple[str, str]:
            async with semaphore:
                translated = await asyncio.to_thread(translate_text_to_zh, sentence)
                return sentence, translated

        translated_pairs = await asyncio.gather(*(run_one(sentence) for sentence in missing_sentences))
        for sentence, translated in translated_pairs:
            cleaned = translated.strip()
            if not cleaned:
                raise ConversionError(f"翻譯失敗，無法產生字幕：{sentence}")
            translation_map[sentence] = cleaned
            cached_translations[sentence] = cleaned
            translated_count += 1
        save_translation_cache(root_output_dir, {"translations": cached_translations})

    missing_after = [sentence for sentence in unique_sentences if not translation_map.get(sentence, "").strip()]
    if missing_after:
        raise ConversionError(f"翻譯快取缺少字幕內容：{missing_after[0]}")
    return translation_map, cache_hits, translated_count


def build_subtitle_sentences(
    source_sentences: list[str],
    translation_map: dict[str, str],
) -> list[SubtitleSentence]:
    subtitle_sentences: list[SubtitleSentence] = []
    for sentence in source_sentences:
        translated = translation_map.get(sentence.strip(), "").strip()
        if not translated:
            raise ConversionError(f"找不到句子的中文字幕：{sentence}")
        subtitle_sentences.append(SubtitleSentence(english=sentence, chinese=translated))
    return subtitle_sentences


def multiplier_to_edge_rate(rate_multiplier: float) -> str:
    """將倍率轉換成 edge-tts 的百分比格式"""
    rate_multiplier = max(0.5, min(2.0, float(rate_multiplier)))
    rate_percent = int((rate_multiplier - 1.0) * 100)
    sign = "+" if rate_percent >= 0 else ""
    return f"{sign}{rate_percent}%"


def _is_blocking_proxy(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    parsed = urlparse(text if "://" in text else f"http://{text}")
    host = (parsed.hostname or "").strip("[]").lower()
    return host in BLOCKING_PROXY_HOSTS and parsed.port == 9


def disable_blocking_proxy_env() -> list[str]:
    removed: list[str] = []
    blocking_found = any(_is_blocking_proxy(os.environ.get(key, "")) for key in PROXY_ENV_KEYS)
    if not blocking_found:
        return removed
    for key in PROXY_ENV_KEYS:
        if key in os.environ:
            removed.append(key)
            os.environ.pop(key, None)
    return removed


def make_temp_work_dir(base_dir: Path, prefix: str = TEMP_WORK_DIR_PREFIX) -> Path:
    for _ in range(100):
        candidate = base_dir / f"{prefix}{uuid.uuid4().hex[:10]}"
        try:
            candidate.mkdir(parents=False, exist_ok=False)
            return candidate
        except FileExistsError:
            continue
    raise ConversionError("無法建立暫存資料夾，請檢查目錄權限。")


def ensure_del_root(del_root: Path) -> Path:
    del_root.mkdir(parents=True, exist_ok=True)
    return del_root


def build_del_destination(del_root: Path, source_path: Path) -> Path:
    candidate = del_root / source_path.name
    if not candidate.exists():
        return candidate
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    suffix = "".join(source_path.suffixes)
    base_name = source_path.name[: -len(suffix)] if suffix else source_path.name
    return del_root / f"{base_name}__{timestamp}_{uuid.uuid4().hex[:6]}{suffix}"


def move_path_to_del(source_path: Path, del_root: Path) -> Path | None:
    if not source_path.exists():
        return None
    ensure_del_root(del_root)
    destination = build_del_destination(del_root, source_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(destination))
    return destination


def cleanup_temp_artifacts(root_output_dir: Path) -> tuple[int, int]:
    moved_dirs = 0
    moved_files = 0

    if not root_output_dir.exists():
        return moved_dirs, moved_files

    try:
        candidates = list(root_output_dir.iterdir())
    except OSError:
        return moved_dirs, moved_files

    del_root = root_output_dir.parent / "del"

    for candidate in candidates:
        if candidate.name in OUTPUT_DIR_KEEP_NAMES and candidate.is_dir():
            continue
        try:
            moved = move_path_to_del(candidate, del_root)
            if moved is None:
                continue
            if moved.is_dir():
                moved_dirs += 1
            else:
                moved_files += 1
        except FileNotFoundError:
            continue
        except OSError:
            continue

    return moved_dirs, moved_files


def is_speakable_text(text: str) -> bool:
    # 僅含標點或分隔線（如 "----"）時，edge-tts 可能不回傳音訊。
    return any(ch.isalnum() for ch in text)


def locate_binary(name: str) -> Path:
    found = shutil.which(name)
    if found:
        return Path(found)

    suffix = ".exe" if sys.platform == "win32" else ""
    executable = Path(sys.executable).resolve()
    env_root = executable.parent.parent
    candidates = [
        executable.parent / f"{name}{suffix}",
        executable.parent / "Library" / "bin" / f"{name}{suffix}",
        env_root / "Library" / "bin" / f"{name}{suffix}",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ConversionError(f"找不到 {name} 可執行檔，請先安裝。")


def run_checked(cmd: list[str], cwd: Path | None = None) -> None:
    assert_not_cancelled()
    control = get_execution_control()
    if control is None:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd) if cwd else None,
        )
        if proc.returncode != 0:
            msg = (
                f"命令失敗（exit={proc.returncode}）:\n"
                f"{' '.join(cmd)}\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr:\n{proc.stderr}"
            )
            raise ConversionError(msg)
        return

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd) if cwd else None,
    )
    control.register_process(proc)
    stdout = ""
    stderr = ""
    try:
        while True:
            if control.stop_event.is_set():
                terminate_process(proc)
                raise ConversionCancelled("使用者已強制停止轉換。")
            try:
                stdout, stderr = proc.communicate(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                continue
    finally:
        control.unregister_process(proc)

    if proc.returncode != 0:
        if control.stop_event.is_set():
            raise ConversionCancelled("使用者已強制停止轉換。")
        msg = (
            f"命令失敗（exit={proc.returncode}）:\n"
            f"{' '.join(cmd)}\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        )
        raise ConversionError(msg)


def list_available_ffmpeg_encoders(ffmpeg_bin: Path) -> set[str]:
    cmd = [str(ffmpeg_bin), "-hide_banner", "-encoders"]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise ConversionError("無法讀取 ffmpeg encoder 清單。")

    available: set[str] = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("------"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        flags, name = parts[0], parts[1]
        if FFMPEG_ENCODER_FLAG_PATTERN.fullmatch(flags):
            available.add(name)
    return available


def _pick_encoder(
    available: set[str],
    candidates: tuple[str, ...],
    error_message: str,
) -> str:
    for encoder in candidates:
        if encoder in available:
            return encoder
    raise ConversionError(error_message)


def detect_mp3_encoder(ffmpeg_bin: Path, available: set[str] | None = None) -> str:
    available = available if available is not None else list_available_ffmpeg_encoders(ffmpeg_bin)
    return _pick_encoder(
        available,
        ("libmp3lame", "mp3_mf", "mp3"),
        "ffmpeg 找不到可用 MP3 編碼器（libmp3lame/mp3/mp3_mf）。",
    )


def detect_aac_encoder(ffmpeg_bin: Path, available: set[str] | None = None) -> str:
    available = available if available is not None else list_available_ffmpeg_encoders(ffmpeg_bin)
    return _pick_encoder(
        available,
        ("aac", "libfdk_aac"),
        "ffmpeg 找不到可用 AAC 編碼器（aac/libfdk_aac）。",
    )


def detect_h264_encoder(
    ffmpeg_bin: Path,
    available: set[str] | None = None,
    use_gpu: bool = True,
) -> str:
    available = available if available is not None else list_available_ffmpeg_encoders(ffmpeg_bin)
    if use_gpu:
        return _pick_encoder(
            available,
            ("h264_nvenc", "h264_qsv", "h264_amf"),
            "ffmpeg could not find a GPU H.264 encoder (h264_nvenc/h264_qsv/h264_amf).",
        )
    return _pick_encoder(
        available,
        ("libx264", "h264_mf", "mpeg4"),
            "ffmpeg could not find a CPU H.264 encoder (libx264/h264_mf/mpeg4).",
        )


def validate_h264_encoder(ffmpeg_bin: Path, encoder: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [
            str(ffmpeg_bin),
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:r=1",
            "-frames:v",
            "1",
            "-c:v",
            encoder,
            "-pix_fmt",
            "yuv420p",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stderr = proc.stderr.strip()
    if proc.returncode == 0:
        return True, stderr
    return False, stderr or f"ffmpeg exit={proc.returncode}"


def create_silence_mp3(ffmpeg_bin: Path, mp3_encoder: str, duration_sec: float, out_path: Path) -> None:
    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={OUTPUT_SAMPLE_RATE}:cl=stereo",
        "-t",
        f"{duration_sec:.3f}",
        "-c:a",
        mp3_encoder,
        "-ar",
        str(OUTPUT_SAMPLE_RATE),
        "-ac",
        str(OUTPUT_CHANNELS),
        "-b:a",
        OUTPUT_BITRATE,
        str(out_path),
    ]
    run_checked(cmd)


def write_concat_list(input_files: Iterable[Path], list_file: Path) -> None:
    base_dir = list_file.parent
    lines: list[str] = []
    for input_file in input_files:
        relative = os.path.relpath(str(input_file), str(base_dir))
        escaped = Path(relative).as_posix().replace("'", r"'\''")
        lines.append(f"file '{escaped}'")
    list_file.write_text("\n".join(lines), encoding="utf-8")


def concat_audio_mp3(
    ffmpeg_bin: Path,
    mp3_encoder: str,
    input_files: list[Path],
    out_path: Path,
    list_file: Path,
) -> None:
    if not input_files:
        raise ConversionError("沒有可供串接的音訊檔案。")
    write_concat_list(input_files, list_file)
    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c:a",
        mp3_encoder,
        "-ar",
        str(OUTPUT_SAMPLE_RATE),
        "-ac",
        str(OUTPUT_CHANNELS),
        "-b:a",
        OUTPUT_BITRATE,
        str(out_path),
    ]
    run_checked(cmd, cwd=list_file.parent)


def find_drawtext_font() -> Path | None:
    candidates = [
        Path(r"C:\Windows\Fonts\msjh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def escape_drawtext_text(text: str) -> str:
    escaped = text.replace("\\", r"\\")
    escaped = escaped.replace(":", r"\:")
    escaped = escaped.replace(",", r"\,")
    escaped = escaped.replace(";", r"\;")
    escaped = escaped.replace("[", r"\[")
    escaped = escaped.replace("]", r"\]")
    escaped = escaped.replace("'", r"\'")
    escaped = escaped.replace("%", r"\%")
    return escaped.replace("\n", r"\n").strip()


def resolve_drawtext_font_name(fontfile: Path | None) -> str:
    if fontfile is None:
        return "Arial"
    name = fontfile.name.lower()
    if name == "msjh.ttc":
        return "Microsoft JhengHei"
    if name == "msyh.ttc":
        return "Microsoft YaHei"
    if name == "simsun.ttc":
        return "SimSun"
    return "Arial"


def wrap_subtitle_lines(text: str, width: int) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return []
    if re.search(r"[\u4e00-\u9fff]", normalized) and " " not in normalized:
        return [normalized[idx : idx + width] for idx in range(0, len(normalized), width)]
    return textwrap.wrap(
        normalized,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def write_utf8_lf_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(normalized)


def compute_subtitle_line_positions(
    line_count: int,
    area_top: int,
    area_bottom: int,
    font_size: int,
    line_step: int,
) -> list[int]:
    if line_count <= 0:
        return []
    area_height = max(font_size, area_bottom - area_top)
    block_height = font_size + max(0, line_count - 1) * line_step
    if block_height >= area_height:
        start_y = area_top
    else:
        start_y = area_top + (area_height - block_height) / 2
    return [int(round(start_y + idx * line_step)) for idx in range(line_count)]


def build_drawtext_segment(
    textfile_path: str,
    fontfile: Path | None,
    fontsize: int,
    y_expr: str,
    start_seconds: float,
    end_seconds: float,
) -> str:
    parts: list[str] = []
    font_name = resolve_drawtext_font_name(fontfile).replace("'", r"\'")
    parts.append(f"font='{font_name}'")
    parts.extend(
        [
            f"textfile='{textfile_path}'",
            "reload=0",
            "expansion=none",
            f"fontcolor={VIDEO_FONT_COLOR}",
            f"fontsize={fontsize}",
            "line_spacing=12",
            "bordercolor=black",
            "borderw=3",
            "fix_bounds=true",
            "x=(w-text_w)/2",
            f"y={y_expr}",
            f"enable='between(t\\,{start_seconds:.3f}\\,{end_seconds:.3f})'",
        ]
    )
    return "drawtext=" + ":".join(parts)


def locate_ffprobe_binary(ffmpeg_bin: Path) -> Path:
    try:
        return locate_binary("ffprobe")
    except ConversionError:
        suffix = ffmpeg_bin.suffix
        sibling = ffmpeg_bin.with_name(f"ffprobe{suffix}")
        if sibling.exists():
            return sibling
        raise


def get_media_duration_seconds(ffprobe_bin: Path, media_path: Path) -> float:
    proc = subprocess.run(
        [
            str(ffprobe_bin),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise ConversionError(f"無法讀取媒體長度：{media_path.name}")
    try:
        duration = float(proc.stdout.strip())
    except ValueError as exc:
        raise ConversionError(f"媒體長度格式異常：{media_path.name}") from exc
    return max(0.0, duration)


def build_subtitle_cues(
    subtitle_sentences: list[SubtitleSentence],
    sentence_audio_files: list[Path],
    ffprobe_bin: Path,
    repeat_sentences: bool,
    gap_duration_seconds: float,
) -> list[SubtitleCue]:
    if len(subtitle_sentences) != len(sentence_audio_files):
        raise ConversionError("字幕句數與音訊片段數量不一致。")
    duration_cache: dict[Path, float] = {}

    def get_cached_duration(path: Path) -> float:
        cached = duration_cache.get(path)
        if cached is None:
            cached = get_media_duration_seconds(ffprobe_bin, path)
            duration_cache[path] = cached
        return cached

    playback_pairs = list(zip(subtitle_sentences, sentence_audio_files))
    if repeat_sentences:
        playback_pairs = [pair for pair in playback_pairs for _ in range(2)]

    cues: list[SubtitleCue] = []
    current_seconds = 0.0
    for idx, (subtitle, audio_path) in enumerate(playback_pairs):
        duration = get_cached_duration(audio_path)
        start_seconds = current_seconds
        end_seconds = start_seconds + duration
        cues.append(
            SubtitleCue(
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                english=subtitle.english,
                chinese=subtitle.chinese,
            )
        )
        current_seconds = end_seconds
        if idx < len(playback_pairs) - 1 and gap_duration_seconds > 0:
            current_seconds += gap_duration_seconds
    return cues


def offset_subtitle_cues(cues: list[SubtitleCue], offset_seconds: float) -> list[SubtitleCue]:
    return [
        SubtitleCue(
            start_seconds=cue.start_seconds + offset_seconds,
            end_seconds=cue.end_seconds + offset_seconds,
            english=cue.english,
            chinese=cue.chinese,
        )
        for cue in cues
    ]


def merge_subtitle_cues(
    rendered_outputs: list[RenderedMarkdownOutput],
    inter_file_gap_seconds: float,
) -> list[SubtitleCue]:
    merged_cues: list[SubtitleCue] = []
    current_offset = 0.0
    for idx, rendered_output in enumerate(rendered_outputs):
        merged_cues.extend(offset_subtitle_cues(rendered_output.subtitle_cues, current_offset))
        current_offset += rendered_output.audio_duration_seconds
        if idx < len(rendered_outputs) - 1 and inter_file_gap_seconds > 0:
            current_offset += inter_file_gap_seconds
    return merged_cues


def write_drawtext_filter_script(
    filter_script_file: Path,
    cues: list[SubtitleCue],
    fontfile: Path | None,
) -> None:
    english_area_top = 72
    english_area_bottom = 340
    english_line_step = 68
    chinese_area_top = 430
    chinese_area_bottom = 642
    chinese_line_step = 54
    text_dir_name = f"texts_{hashlib.sha1(filter_script_file.name.encode('utf-8')).hexdigest()[:8]}"
    text_dir = filter_script_file.parent / text_dir_name
    text_dir.mkdir(parents=True, exist_ok=True)
    segments: list[str] = []
    for idx, cue in enumerate(cues, start=1):
        english_lines = wrap_subtitle_lines(cue.english, 34)
        chinese_lines = wrap_subtitle_lines(cue.chinese, 22)
        english_positions = compute_subtitle_line_positions(
            len(english_lines),
            english_area_top,
            english_area_bottom,
            SUBTITLE_TOP_FONT_SIZE,
            english_line_step,
        )
        chinese_positions = compute_subtitle_line_positions(
            len(chinese_lines),
            chinese_area_top,
            chinese_area_bottom,
            SUBTITLE_BOTTOM_FONT_SIZE,
            chinese_line_step,
        )
        for line_idx, (line_text, y_pos) in enumerate(zip(english_lines, english_positions), start=1):
            english_file = text_dir / f"eng_{idx:04d}_{line_idx:02d}.txt"
            write_utf8_lf_text(english_file, line_text)
            english_textfile_path = f"{text_dir_name}/{english_file.name}"
            segments.append(
                build_drawtext_segment(
                    textfile_path=english_textfile_path,
                    fontfile=fontfile,
                    fontsize=SUBTITLE_TOP_FONT_SIZE,
                    y_expr=str(y_pos),
                    start_seconds=cue.start_seconds,
                    end_seconds=cue.end_seconds,
                )
            )
        for line_idx, (line_text, y_pos) in enumerate(zip(chinese_lines, chinese_positions), start=1):
            chinese_file = text_dir / f"zho_{idx:04d}_{line_idx:02d}.txt"
            write_utf8_lf_text(chinese_file, line_text)
            chinese_textfile_path = f"{text_dir_name}/{chinese_file.name}"
            segments.append(
                build_drawtext_segment(
                    textfile_path=chinese_textfile_path,
                    fontfile=fontfile,
                    fontsize=SUBTITLE_BOTTOM_FONT_SIZE,
                    y_expr=str(y_pos),
                    start_seconds=cue.start_seconds,
                    end_seconds=cue.end_seconds,
                )
            )
    write_utf8_lf_text(filter_script_file, ",\n".join(segments))


def create_subtitled_video_mp4(
    ffmpeg_bin: Path,
    h264_encoder: str,
    aac_encoder: str,
    audio_file: Path,
    subtitle_file: Path,
    out_path: Path,
    fontfile: Path | None,
) -> None:
    video_input = f"color=c=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}"
    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-f",
        "lavfi",
        "-i",
        video_input,
        "-i",
        str(audio_file),
        "-filter_script:v",
        str(subtitle_file),
        "-c:v",
        h264_encoder,
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        aac_encoder,
        "-ar",
        str(OUTPUT_SAMPLE_RATE),
        "-ac",
        str(OUTPUT_CHANNELS),
        "-b:a",
        OUTPUT_BITRATE,
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    run_checked(cmd, cwd=subtitle_file.parent)


async def create_subtitled_video_mp4_async(
    ffmpeg_bin: Path,
    h264_encoder: str,
    aac_encoder: str,
    audio_file: Path,
    subtitle_file: Path,
    out_path: Path,
    fontfile: Path | None,
    video_encode_semaphore: asyncio.Semaphore | None = None,
) -> None:
    if video_encode_semaphore is None:
        await asyncio.to_thread(
            create_subtitled_video_mp4,
            ffmpeg_bin,
            h264_encoder,
            aac_encoder,
            audio_file,
            subtitle_file,
            out_path,
            fontfile,
        )
        return

    async with video_encode_semaphore:
        await asyncio.to_thread(
            create_subtitled_video_mp4,
            ffmpeg_bin,
            h264_encoder,
            aac_encoder,
            audio_file,
            subtitle_file,
            out_path,
            fontfile,
        )


def with_gap(items: list[Path], gap_file: Path | None) -> list[Path]:
    if not items:
        return []
    if gap_file is None:
        return list(items)
    result: list[Path] = []
    for idx, item in enumerate(items):
        if idx > 0:
            result.append(gap_file)
        result.append(item)
    return result


async def synthesize_sentence(
    text: str,
    voice: str,
    rate: str,
    out_path: Path,
    retries: int = 1,
) -> None:
    disable_blocking_proxy_env()
    for attempt in range(retries + 1):
        assert_not_cancelled()
        try:
            communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
            await communicator.save(str(out_path))
            assert_not_cancelled()
            return
        except Exception:
            if attempt >= retries:
                raise
            await asyncio.sleep(0.4)


def sentence_audio_cache_key(text: str, voice: str, rate: str) -> str:
    payload = f"{voice}\n{rate}\n{text}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


class SentenceAudioCache:
    def __init__(self, cache_dir: Path, del_root: Path):
        self.cache_dir = cache_dir
        self.del_root = del_root
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._inflight: dict[str, asyncio.Task[Path]] = {}

    @staticmethod
    def _is_ready(path: Path) -> bool:
        try:
            return path.exists() and path.stat().st_size > 0
        except OSError:
            return False

    async def get_or_create(
        self,
        text: str,
        voice: str,
        rate: str,
        retries: int = 1,
    ) -> Path:
        key = sentence_audio_cache_key(text, voice, rate)
        target = self.cache_dir / f"{key}.mp3"
        if self._is_ready(target):
            return target

        async with self._lock:
            task = self._inflight.get(key)
            if task is None:
                task = asyncio.create_task(
                    self._create_cached_file(target, text, voice, rate, retries=retries)
                )
                self._inflight[key] = task

        try:
            return await task
        finally:
            async with self._lock:
                if self._inflight.get(key) is task:
                    self._inflight.pop(key, None)

    async def _create_cached_file(
        self,
        target: Path,
        text: str,
        voice: str,
        rate: str,
        retries: int = 1,
    ) -> Path:
        if self._is_ready(target):
            return target

        temp_target = target.with_suffix(".tmp.mp3")
        if temp_target.exists():
            move_path_to_del(temp_target, self.del_root)

        try:
            await synthesize_sentence(
                text=text,
                voice=voice,
                rate=rate,
                out_path=temp_target,
                retries=retries,
            )
            temp_target.replace(target)
            return target
        except Exception:
            if temp_target.exists():
                move_path_to_del(temp_target, self.del_root)
            raise


async def synthesize_sentence_audio_files(
    md_path: Path,
    source_sentences: list[str],
    part_dir: Path,
    voice: str,
    rate: str,
    progress: Callable[[str], None],
    audio_cache: SentenceAudioCache | None = None,
) -> list[Path]:
    assert_not_cancelled()
    total_sentences = len(source_sentences)
    sentence_audio_files: list[Path] = []
    for idx, sentence in enumerate(source_sentences, start=1):
        assert_not_cancelled()
        segment = part_dir / f"{idx:04d}.mp3"
        try:
            if audio_cache is None:
                await synthesize_sentence(
                    text=sentence,
                    voice=voice,
                    rate=rate,
                    out_path=segment,
                    retries=1,
                )
                sentence_audio_files.append(segment)
            else:
                cached_segment = await audio_cache.get_or_create(
                    text=sentence,
                    voice=voice,
                    rate=rate,
                    retries=1,
                )
                shutil.copy2(cached_segment, segment)
                sentence_audio_files.append(segment)
        except ConversionCancelled:
            raise
        except Exception as exc:
            raise ConversionError(f"{md_path.name} sentence {idx} synthesis failed: {exc}") from exc

        if idx % 20 == 0 or idx == total_sentences:
            progress(f"{md_path.name} progress {idx}/{total_sentences}")
    return sentence_audio_files


async def fetch_voice_choices() -> list[tuple[str, str]]:
    disable_blocking_proxy_env()
    voices = await edge_tts.list_voices()
    choices: list[tuple[str, str]] = []
    for voice in voices:
        short_name = voice.get("ShortName") or voice.get("Name")
        if not short_name:
            continue
        locale = voice.get("Locale", "")
        gender = voice.get("Gender", "")
        label = f"{short_name} | {locale} | {gender}".strip(" |")
        choices.append((label, short_name))
    choices.sort(key=lambda x: x[1])
    return choices


async def convert_markdown_file(
    md_path: Path,
    tmp_root: Path,
    output_dir: Path,
    voice: str,
    rate: str,
    gap_file: Path | None,
    gap_duration_seconds: float,
    ffmpeg_bin: Path,
    ffprobe_bin: Path,
    mp3_encoder: str,
    h264_encoder: str,
    aac_encoder: str,
    drawtext_font: Path | None,
    progress: Callable[[str], None],
    repeat_sentences: bool = False,
    sentences: list[str] | None = None,
    translation_map: dict[str, str] | None = None,
    audio_cache: SentenceAudioCache | None = None,
    video_encode_semaphore: asyncio.Semaphore | None = None,
) -> tuple[RenderedMarkdownOutput | None, list[str]]:
    assert_not_cancelled()
    warnings: list[str] = []
    source_sentences = list(sentences) if sentences is not None else extract_tts_sentences(md_path)
    if not source_sentences:
        warning = f"{md_path.name} has no tts sentences"
        warnings.append(warning)
        progress(f"warning: {warning}")
        return None, warnings

    total_sentences = len(source_sentences)
    progress(f"start {md_path.name}: {total_sentences} sentences (repeat={repeat_sentences})")
    part_dir = tmp_root / md_path.stem
    part_dir.mkdir(parents=True, exist_ok=True)
    sentence_audio_files = await synthesize_sentence_audio_files(
        md_path=md_path,
        source_sentences=source_sentences,
        part_dir=part_dir,
        voice=voice,
        rate=rate,
        progress=progress,
        audio_cache=audio_cache,
    )

    if translation_map is None:
        raise ConversionError("缺少字幕翻譯資料，無法產生影片。")
    subtitle_sentences = build_subtitle_sentences(source_sentences, translation_map)

    rendered_output = await build_markdown_outputs_from_segments(
        md_path=md_path,
        part_dir=part_dir,
        output_dir=output_dir,
        sentence_audio_files=sentence_audio_files,
        subtitle_sentences=subtitle_sentences,
        repeat_sentences=repeat_sentences,
        gap_file=gap_file,
        gap_duration_seconds=gap_duration_seconds,
        ffmpeg_bin=ffmpeg_bin,
        ffprobe_bin=ffprobe_bin,
        mp3_encoder=mp3_encoder,
        h264_encoder=h264_encoder,
        aac_encoder=aac_encoder,
        drawtext_font=drawtext_font,
        video_encode_semaphore=video_encode_semaphore,
    )
    progress(f"done {rendered_output.video_file.name}")
    return rendered_output, warnings


async def build_markdown_outputs_from_segments(
    md_path: Path,
    part_dir: Path,
    output_dir: Path,
    sentence_audio_files: list[Path],
    subtitle_sentences: list[SubtitleSentence],
    repeat_sentences: bool,
    gap_file: Path | None,
    gap_duration_seconds: float,
    ffmpeg_bin: Path,
    ffprobe_bin: Path,
    mp3_encoder: str,
    h264_encoder: str,
    aac_encoder: str,
    drawtext_font: Path | None,
    video_encode_semaphore: asyncio.Semaphore | None = None,
) -> RenderedMarkdownOutput:
    if repeat_sentences:
        playback_files = [segment for segment in sentence_audio_files for _ in range(2)]
        audio_suffix = "twice"
    else:
        playback_files = sentence_audio_files
        audio_suffix = "once"

    concat_inputs = with_gap(playback_files, gap_file)
    audio_file = part_dir / f"{md_path.stem}_{audio_suffix}_audio.mp3"
    audio_concat_list_file = part_dir / f"concat_audio_{audio_suffix}.txt"
    await asyncio.to_thread(
        concat_audio_mp3,
        ffmpeg_bin,
        mp3_encoder,
        concat_inputs,
        audio_file,
        audio_concat_list_file,
    )

    output_stem = f"{md_path.stem}_兩次" if repeat_sentences else f"{md_path.stem}_一次"
    output_file = output_dir / f"{output_stem}.mp4"
    subtitle_cues = build_subtitle_cues(
        subtitle_sentences=subtitle_sentences,
        sentence_audio_files=sentence_audio_files,
        ffprobe_bin=ffprobe_bin,
        repeat_sentences=repeat_sentences,
        gap_duration_seconds=gap_duration_seconds,
    )
    subtitle_file = part_dir / f"{output_stem}.ffmpeg-filter"
    write_drawtext_filter_script(subtitle_file, subtitle_cues, drawtext_font)
    await create_subtitled_video_mp4_async(
        ffmpeg_bin,
        h264_encoder,
        aac_encoder,
        audio_file,
        subtitle_file,
        output_file,
        drawtext_font,
        video_encode_semaphore=video_encode_semaphore,
    )
    audio_duration_seconds = await asyncio.to_thread(get_media_duration_seconds, ffprobe_bin, audio_file)
    return RenderedMarkdownOutput(
        video_file=output_file,
        audio_file=audio_file,
        subtitle_cues=subtitle_cues,
        audio_duration_seconds=audio_duration_seconds,
    )


def pick_default_voice(choices: list[tuple[str, str]]) -> str:
    if not choices:
        raise ConversionError("取得 voice 清單失敗。")
    choice_ids = {voice_id for _, voice_id in choices}
    for preferred in PREFERRED_DEFAULT_VOICES:
        if preferred in choice_ids:
            return preferred
    for _, voice_id in choices:
        if voice_id.startswith("en-US-"):
            return voice_id
    return choices[0][1]


async def convert_workspace(
    workspace_root: Path,
    options: ConvertOptions,
    progress: Callable[[str], None] | None = None,
    sentence_cache: dict[Path, list[str]] | None = None,
) -> dict[str, tuple[list[Path], Path, list[str]]]:
    assert_not_cancelled()
    progress = progress or (lambda _: None)
    removed_proxy_keys = disable_blocking_proxy_env()
    if removed_proxy_keys:
        progress("偵測到無效 proxy（127.0.0.1:9），已自動停用代理連線設定。")
    ffmpeg_bin = locate_binary("ffmpeg")
    ffprobe_bin = locate_ffprobe_binary(ffmpeg_bin)
    available_encoders = list_available_ffmpeg_encoders(ffmpeg_bin)
    mp3_encoder = detect_mp3_encoder(ffmpeg_bin, available_encoders)
    aac_encoder = detect_aac_encoder(ffmpeg_bin, available_encoders)
    h264_encoder = detect_h264_encoder(
        ffmpeg_bin,
        available_encoders,
        use_gpu=options.use_gpu,
    )
    if options.use_gpu:
        gpu_encoder_ok, gpu_encoder_error = validate_h264_encoder(ffmpeg_bin, h264_encoder)
        if not gpu_encoder_ok:
            fallback_encoder = detect_h264_encoder(
                ffmpeg_bin,
                available_encoders,
                use_gpu=False,
            )
            progress(
                "GPU 編碼器自我檢查失敗，已自動改用 CPU。"
                + (f" 原因：{gpu_encoder_error}" if gpu_encoder_error else "")
            )
            options.use_gpu = False
            h264_encoder = fallback_encoder
    drawtext_font = find_drawtext_font()
    markdown_files = scan_numeric_markdown_files(workspace_root)
    if not markdown_files:
        raise ConversionError("找不到任何 <數字>.md 檔案。")

    root_output_dir = workspace_root / DEFAULT_OUTPUT_DIR_NAME
    root_output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(root_output_dir)
    sentence_cache_doc = load_sentence_cache(root_output_dir)
    previous_manifest_files = manifest.get("files", {})
    if not isinstance(previous_manifest_files, dict):
        previous_manifest_files = {}
    markdown_metadata, reused_hash_count, recomputed_hash_count = build_markdown_metadata(
        markdown_files,
        previous_manifest_files,
    )
    if reused_hash_count > 0:
        progress(f"hash 快取命中：{reused_hash_count} 個檔案")
    if recomputed_hash_count > 0:
        progress(f"hash 重算：{recomputed_hash_count} 個檔案")

    current_signature = options_signature(options)
    previous_signature = manifest.get("options_signature", "")
    if not isinstance(previous_signature, str):
        previous_signature = ""
    current_file_names = {md_path.name for md_path in markdown_files}

    def _outputs_exist_for_mode(mode_name: str) -> bool:
        mode_dir = root_output_dir / mode_name
        suffix = "_一次" if mode_name == "一次" else "_兩次"
        for md_path in markdown_files:
            out_path = mode_dir / f"{md_path.stem}{suffix}.mp4"
            if not out_path.exists():
                return False
        merged_name = build_range_mp4_name(markdown_files, suffix)
        return (mode_dir / merged_name).exists()

    can_skip = previous_signature == current_signature
    if can_skip and set(previous_manifest_files.keys()) != current_file_names:
        can_skip = False
    for md_path in markdown_files:
        recorded = previous_manifest_files.get(md_path.name, {})
        if not isinstance(recorded, dict):
            recorded = {}
        if not recorded or recorded.get("hash") != markdown_metadata[md_path]["hash"]:
            can_skip = False
            break
    if can_skip:
        if options.repeat_mode in ("once", "both") and not _outputs_exist_for_mode("一次"):
            can_skip = False
        if options.repeat_mode in ("twice", "both") and not _outputs_exist_for_mode("兩次"):
            can_skip = False

    if can_skip:
        progress("偵測到內容與設定皆未變更，沿用既有輸出，跳過轉換。")
        results: dict[str, tuple[list[Path], Path, list[str]]] = {}
        if options.repeat_mode in ("once", "both"):
            once_dir = root_output_dir / "一次"
            once_files = [once_dir / f"{md.stem}_一次.mp4" for md in markdown_files]
            once_full = once_dir / build_range_mp4_name(markdown_files, "_一次")
            results["once"] = (once_files, once_full, [])
        if options.repeat_mode in ("twice", "both"):
            twice_dir = root_output_dir / "兩次"
            twice_files = [twice_dir / f"{md.stem}_兩次.mp4" for md in markdown_files]
            twice_full = twice_dir / build_range_mp4_name(markdown_files, "_兩次")
            results["twice"] = (twice_files, twice_full, [])
        return results

    effective_sentence_cache, updated_sentence_cache_doc, reused_sentence_files = (
        build_effective_sentence_cache(
            markdown_files=markdown_files,
            markdown_metadata=markdown_metadata,
            provided_sentence_cache=sentence_cache,
            sentence_cache_doc=sentence_cache_doc,
        )
    )
    if reused_sentence_files > 0:
        progress(f"句子快取命中：{reused_sentence_files} 個檔案")
    save_sentence_cache(root_output_dir, updated_sentence_cache_doc)

    all_sentences = [
        sentence
        for md_path in markdown_files
        for sentence in effective_sentence_cache.get(md_path, [])
    ]
    translation_map, translation_cache_hits, translated_count = await build_translation_map(
        root_output_dir=root_output_dir,
        sentences=all_sentences,
        progress=progress,
    )
    if translation_cache_hits > 0:
        progress(f"字幕翻譯快取命中：{translation_cache_hits} 句")
    if translated_count > 0:
        progress(f"字幕翻譯新增完成：{translated_count} 句")

    sentence_audio_cache = SentenceAudioCache(
        root_output_dir / "_tts_sentence_cache",
        workspace_root / "del",
    )
    assert_not_cancelled()
    video_encode_limit = (
        MAX_GPU_VIDEO_ENCODE_CONCURRENCY if options.use_gpu else MAX_CPU_VIDEO_ENCODE_CONCURRENCY
    )
    video_encode_limit = max(1, min(len(markdown_files), video_encode_limit))
    video_encode_semaphore = asyncio.Semaphore(video_encode_limit)

    warnings: list[str] = []
    results: dict[str, tuple[list[Path], Path, list[str]]] = {}
    rate = multiplier_to_edge_rate(options.rate_multiplier)
    progress(f"video mode: {'GPU' if options.use_gpu else 'CPU'}")

    progress(f"ffmpeg MP3 編碼器：{mp3_encoder}（句間靜音）")
    progress(f"ffmpeg AAC 編碼器：{aac_encoder}（MP4 輸出）")
    progress(f"ffmpeg 視訊編碼器：{h264_encoder}")
    progress(f"ffprobe：{ffprobe_bin.name}")
    progress(f"ffmpeg 視訊編碼併發上限：{video_encode_limit}")
    if drawtext_font is not None:
        progress(f"字幕字型：{drawtext_font.name}")
    else:
        progress("字幕字型：使用 ffmpeg 預設字型")
    progress(f"已找到 {len(markdown_files)} 個 .md，開始轉換。")
    progress(f"轉換模式：{options.repeat_mode}")

    # 決定要轉換的類型
    convert_once = options.repeat_mode in ("once", "both")
    convert_twice = options.repeat_mode in ("twice", "both")

    if convert_once and convert_twice:
        progress("\n=== 開始「一次 + 兩次（共用 TTS）」轉換 ===")
        progress(f"已找到 {len(markdown_files)} 個 .md，開始同時轉換（同句只合成一次）。")
        once_results, twice_results = await _convert_both_modes_shared_tts(
            markdown_files=markdown_files,
            root_output_dir=root_output_dir,
            options=options,
            ffmpeg_bin=ffmpeg_bin,
            ffprobe_bin=ffprobe_bin,
            mp3_encoder=mp3_encoder,
            aac_encoder=aac_encoder,
            h264_encoder=h264_encoder,
            drawtext_font=drawtext_font,
            progress=progress,
            sentence_cache=effective_sentence_cache,
            translation_map=translation_map,
            audio_cache=sentence_audio_cache,
            video_encode_semaphore=video_encode_semaphore,
        )
        results["once"] = once_results
        results["twice"] = twice_results
        warnings.extend(once_results[2])
        warnings.extend(twice_results[2])
    elif convert_once:
        progress("\n=== 開始「一次」轉換 ===")
        progress(f"已找到 {len(markdown_files)} 個 .md，開始同時轉換。")
        once_results = await _convert_with_mode(
            markdown_files,
            root_output_dir,
            "一次",
            options,
            ffmpeg_bin,
            ffprobe_bin,
            mp3_encoder,
            aac_encoder,
            h264_encoder,
            drawtext_font,
            progress,
            repeat_sentences=False,
            sentence_cache=effective_sentence_cache,
            translation_map=translation_map,
            audio_cache=sentence_audio_cache,
            video_encode_semaphore=video_encode_semaphore,
        )
        results["once"] = once_results
        warnings.extend(once_results[2])

    elif convert_twice:
        progress("\n=== 開始「兩次」轉換 ===")
        progress(f"已找到 {len(markdown_files)} 個 .md，開始同時轉換（每句重複兩次）。")
        twice_results = await _convert_with_mode(
            markdown_files,
            root_output_dir,
            "兩次",
            options,
            ffmpeg_bin,
            ffprobe_bin,
            mp3_encoder,
            aac_encoder,
            h264_encoder,
            drawtext_font,
            progress,
            repeat_sentences=True,
            sentence_cache=effective_sentence_cache,
            translation_map=translation_map,
            audio_cache=sentence_audio_cache,
            video_encode_semaphore=video_encode_semaphore,
        )
        results["twice"] = twice_results
        warnings.extend(twice_results[2])

    manifest_files: dict[str, dict] = {}
    for md_path in markdown_files:
        md_meta = markdown_metadata[md_path]
        manifest_files[md_path.name] = {
            "hash": md_meta["hash"],
            "size": md_meta["size"],
            "mtime_ns": md_meta["mtime_ns"],
        }
    manifest = {
        "options_signature": current_signature,
        "files": manifest_files,
    }
    save_manifest(root_output_dir, manifest)

    return results


async def _convert_both_modes_shared_tts(
    markdown_files: list[Path],
    root_output_dir: Path,
    options: ConvertOptions,
    ffmpeg_bin: Path,
    ffprobe_bin: Path,
    mp3_encoder: str,
    aac_encoder: str,
    h264_encoder: str,
    drawtext_font: Path | None,
    progress: Callable[[str], None],
    sentence_cache: dict[Path, list[str]] | None = None,
    translation_map: dict[str, str] | None = None,
    audio_cache: SentenceAudioCache | None = None,
    video_encode_semaphore: asyncio.Semaphore | None = None,
) -> tuple[tuple[list[Path], Path, list[str]], tuple[list[Path], Path, list[str]]]:
    assert_not_cancelled()
    once_output_dir = root_output_dir / "一次"
    twice_output_dir = root_output_dir / "兩次"
    once_output_dir.mkdir(parents=True, exist_ok=True)
    twice_output_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    once_generated_files: list[Path] = []
    twice_generated_files: list[Path] = []
    once_rendered_outputs: list[RenderedMarkdownOutput] = []
    twice_rendered_outputs: list[RenderedMarkdownOutput] = []

    tmp_root = make_temp_work_dir(root_output_dir)
    try:
        gap_file: Path | None = None
        gap_duration_seconds = 0.0
        if options.gap_seconds > 0:
            gap_file = tmp_root / "gap.mp3"
            progress(f"建立靜音片段：{options.gap_seconds:.2f} 秒")
            await asyncio.to_thread(
                create_silence_mp3, ffmpeg_bin, mp3_encoder, options.gap_seconds, gap_file
            )
            gap_duration_seconds = await asyncio.to_thread(get_media_duration_seconds, ffprobe_bin, gap_file)

        rate = multiplier_to_edge_rate(options.rate_multiplier)
        semaphore = asyncio.Semaphore(max(1, min(len(markdown_files), MAX_FILE_CONCURRENCY)))

        async def run_one(
            md_path: Path,
        ) -> tuple[RenderedMarkdownOutput | None, RenderedMarkdownOutput | None, list[str]]:
            async with semaphore:
                assert_not_cancelled()
                local_warnings: list[str] = []
                source_sentences = (
                    list(sentence_cache.get(md_path, []))
                    if sentence_cache is not None
                    else extract_tts_sentences(md_path)
                )
                if not source_sentences:
                    warning = f"{md_path.name} 沒有 tts 句子，已略過。"
                    local_warnings.append(warning)
                    progress(f"警告：{warning}")
                    return None, None, None, None, local_warnings

                total_sentences = len(source_sentences)
                progress(f"處理 {md_path.name}（{total_sentences} 句，重複：both-共用）")
                part_dir = tmp_root / md_path.stem
                part_dir.mkdir(parents=True, exist_ok=True)
                sentence_audio_files = await synthesize_sentence_audio_files(
                    md_path=md_path,
                    source_sentences=source_sentences,
                    part_dir=part_dir,
                    voice=options.voice,
                    rate=rate,
                    progress=progress,
                    audio_cache=audio_cache,
                )

                if translation_map is None:
                    raise ConversionError("缺少翻譯快取，無法產生雙語字幕。")
                subtitle_sentences = build_subtitle_sentences(source_sentences, translation_map)

                once_rendered = await build_markdown_outputs_from_segments(
                    md_path=md_path,
                    part_dir=part_dir,
                    output_dir=once_output_dir,
                    sentence_audio_files=sentence_audio_files,
                    subtitle_sentences=subtitle_sentences,
                    repeat_sentences=False,
                    gap_file=gap_file,
                    gap_duration_seconds=gap_duration_seconds,
                    ffmpeg_bin=ffmpeg_bin,
                    ffprobe_bin=ffprobe_bin,
                    mp3_encoder=mp3_encoder,
                    h264_encoder=h264_encoder,
                    aac_encoder=aac_encoder,
                    drawtext_font=drawtext_font,
                    video_encode_semaphore=video_encode_semaphore,
                )
                progress(f"完成 一次/{once_rendered.video_file.name}")

                twice_rendered = await build_markdown_outputs_from_segments(
                    md_path=md_path,
                    part_dir=part_dir,
                    output_dir=twice_output_dir,
                    sentence_audio_files=sentence_audio_files,
                    subtitle_sentences=subtitle_sentences,
                    repeat_sentences=True,
                    gap_file=gap_file,
                    gap_duration_seconds=gap_duration_seconds,
                    ffmpeg_bin=ffmpeg_bin,
                    ffprobe_bin=ffprobe_bin,
                    mp3_encoder=mp3_encoder,
                    h264_encoder=h264_encoder,
                    aac_encoder=aac_encoder,
                    drawtext_font=drawtext_font,
                    video_encode_semaphore=video_encode_semaphore,
                )
                progress(f"完成 兩次/{twice_rendered.video_file.name}")

                return once_rendered, twice_rendered, local_warnings

        tasks = [run_one(md_path) for md_path in markdown_files]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in all_results:
            if isinstance(result, Exception):
                raise result
            once_rendered, twice_rendered, local_warnings = result
            warnings.extend(local_warnings)
            if once_rendered is not None:
                once_generated_files.append(once_rendered.video_file)
                once_rendered_outputs.append(once_rendered)
            if twice_rendered is not None:
                twice_generated_files.append(twice_rendered.video_file)
                twice_rendered_outputs.append(twice_rendered)

        if not once_generated_files or not once_rendered_outputs:
            raise ConversionError("沒有任何檔案完成「一次」轉換，請檢查 .md 內容。")
        if not twice_generated_files or not twice_rendered_outputs:
            raise ConversionError("沒有任何檔案完成「兩次」轉換，請檢查 .md 內容。")

        once_full_output_name = build_range_mp4_name(markdown_files, "_一次")
        twice_full_output_name = build_range_mp4_name(markdown_files, "_兩次")

        async def build_full_output(
            mode_name: str,
            mode_output_dir: Path,
            rendered_outputs: list[RenderedMarkdownOutput],
        ) -> Path:
            generated_audio_files = [item.audio_file for item in rendered_outputs]
            all_audio_inputs = with_gap(generated_audio_files, gap_file)
            all_audio_concat_list_file = tmp_root / f"concat_all_audio_{mode_name}.txt"
            full_audio_file = tmp_root / f"full_audio_{mode_name}.mp3"
            await asyncio.to_thread(
                concat_audio_mp3,
                ffmpeg_bin,
                mp3_encoder,
                all_audio_inputs,
                full_audio_file,
                all_audio_concat_list_file,
            )
            full_output_name = twice_full_output_name if mode_name == "兩次" else once_full_output_name
            full_output = mode_output_dir / full_output_name
            full_subtitle_file = tmp_root / f"{mode_name}_full.ffmpeg-filter"
            full_subtitle_cues = merge_subtitle_cues(rendered_outputs, gap_duration_seconds)
            write_drawtext_filter_script(full_subtitle_file, full_subtitle_cues, drawtext_font)
            await create_subtitled_video_mp4_async(
                ffmpeg_bin,
                h264_encoder,
                aac_encoder,
                full_audio_file,
                full_subtitle_file,
                full_output,
                drawtext_font,
                video_encode_semaphore=video_encode_semaphore,
            )
            progress(f"完成 {mode_name}/{full_output_name}")
            return full_output

        once_full_output = await build_full_output("一次", once_output_dir, once_rendered_outputs)
        twice_full_output = await build_full_output("兩次", twice_output_dir, twice_rendered_outputs)
    finally:
        move_path_to_del(tmp_root, root_output_dir.parent / "del")

    once_result = (once_generated_files, once_full_output, warnings)
    twice_result = (twice_generated_files, twice_full_output, [])
    return once_result, twice_result


async def _convert_with_mode(
    markdown_files: list[Path],
    root_output_dir: Path,
    mode_name: str,
    options: ConvertOptions,
    ffmpeg_bin: Path,
    ffprobe_bin: Path,
    mp3_encoder: str,
    aac_encoder: str,
    h264_encoder: str,
    drawtext_font: Path | None,
    progress: Callable[[str], None],
    repeat_sentences: bool = False,
    sentence_cache: dict[Path, list[str]] | None = None,
    translation_map: dict[str, str] | None = None,
    audio_cache: SentenceAudioCache | None = None,
    video_encode_semaphore: asyncio.Semaphore | None = None,
) -> tuple[list[Path], Path, list[str]]:
    assert_not_cancelled()
    """轉換一種模式（一次或兩次）"""
    output_dir = root_output_dir / mode_name
    output_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    generated_files: list[Path] = []
    rendered_outputs: list[RenderedMarkdownOutput] = []

    tmp_root = make_temp_work_dir(root_output_dir)
    try:
        gap_file: Path | None = None
        gap_duration_seconds = 0.0
        if options.gap_seconds > 0:
            gap_file = tmp_root / "gap.mp3"
            progress(f"建立靜音片段：{options.gap_seconds:.2f} 秒")
            await asyncio.to_thread(
                create_silence_mp3, ffmpeg_bin, mp3_encoder, options.gap_seconds, gap_file
            )
            gap_duration_seconds = await asyncio.to_thread(get_media_duration_seconds, ffprobe_bin, gap_file)

        rate = multiplier_to_edge_rate(options.rate_multiplier)
        semaphore = asyncio.Semaphore(max(1, min(len(markdown_files), MAX_FILE_CONCURRENCY)))

        async def run_one(md_path: Path) -> tuple[RenderedMarkdownOutput | None, list[str]]:
            async with semaphore:
                assert_not_cancelled()
                rendered_output, local_warnings = await convert_markdown_file(
                    md_path=md_path,
                    tmp_root=tmp_root,
                    output_dir=output_dir,
                    voice=options.voice,
                    rate=rate,
                    gap_file=gap_file,
                    gap_duration_seconds=gap_duration_seconds,
                    ffmpeg_bin=ffmpeg_bin,
                    ffprobe_bin=ffprobe_bin,
                    mp3_encoder=mp3_encoder,
                    h264_encoder=h264_encoder,
                    aac_encoder=aac_encoder,
                    drawtext_font=drawtext_font,
                    progress=progress,
                    repeat_sentences=repeat_sentences,
                    sentences=sentence_cache.get(md_path) if sentence_cache is not None else None,
                    translation_map=translation_map,
                    audio_cache=audio_cache,
                    video_encode_semaphore=video_encode_semaphore,
                )
                return rendered_output, local_warnings

        tasks = [run_one(md_path) for md_path in markdown_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                raise result
            rendered_output, local_warnings = result
            warnings.extend(local_warnings)
            if rendered_output is not None:
                generated_files.append(rendered_output.video_file)
                rendered_outputs.append(rendered_output)

        if not generated_files or not rendered_outputs:
            raise ConversionError("沒有任何檔案完成轉換，請檢查 .md 內容。")

        generated_audio_files = [item.audio_file for item in rendered_outputs]
        all_audio_inputs = with_gap(generated_audio_files, gap_file)
        all_audio_concat_list_file = tmp_root / "concat_all_audio.txt"
        full_audio_file = tmp_root / "full_audio.mp3"
        await asyncio.to_thread(
            concat_audio_mp3,
            ffmpeg_bin,
            mp3_encoder,
            all_audio_inputs,
            full_audio_file,
            all_audio_concat_list_file,
        )

        full_output_name = build_range_mp4_name(
            markdown_files,
            "_兩次" if mode_name == "兩次" else "_一次",
        )

        full_output = output_dir / full_output_name
        full_subtitle_file = tmp_root / f"{mode_name}_full.ffmpeg-filter"
        full_subtitle_cues = merge_subtitle_cues(rendered_outputs, gap_duration_seconds)
        write_drawtext_filter_script(full_subtitle_file, full_subtitle_cues, drawtext_font)
        await create_subtitled_video_mp4_async(
            ffmpeg_bin,
            h264_encoder,
            aac_encoder,
            full_audio_file,
            full_subtitle_file,
            full_output,
            drawtext_font,
            video_encode_semaphore=video_encode_semaphore,
        )
        progress(f"完成 {full_output.name}")
    finally:
        move_path_to_del(tmp_root, root_output_dir.parent / "del")

    return generated_files, full_output, warnings


def run_once_cli(
    workspace_root: Path,
    voice: str | None,
    rate: float,
    gap: float,
    repeat_mode: str,
    use_gpu: bool,
) -> int:
    chosen_voice = voice
    try:
        if not chosen_voice:
            choices = asyncio.run(fetch_voice_choices())
            chosen_voice = pick_default_voice(choices)
    except Exception as exc:
        root_output_dir = workspace_root / DEFAULT_OUTPUT_DIR_NAME
        if root_output_dir.exists():
            removed_dirs, removed_files = cleanup_temp_artifacts(root_output_dir)
            if removed_dirs > 0 or removed_files > 0:
                print(f"執行結束已移動暫存到 del：{removed_dirs} 個資料夾、{removed_files} 個檔案")
        print(f"取得 voice 失敗：{exc}", file=sys.stderr)
        return 1

    options = ConvertOptions(
        voice=str(chosen_voice),
        rate_multiplier=rate,
        gap_seconds=max(0.0, gap),
        repeat_mode=repeat_mode,
        use_gpu=use_gpu,
    )
    return run_conversion_with_options(workspace_root, options)


def _format_usage_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    percent = int(max(0, min(100, round(value))))
    return f"{percent}%"


def ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                continue


class CliProgressReporter:
    def __init__(
        self,
        tracked_output_files: list[Path],
        predicted_total_bytes: int,
    ):
        self.tracked_output_files = tracked_output_files
        self.predicted_total_bytes = max(1, predicted_total_bytes)
        self.run_started_at = time.time()
        self._tracked_size_cache: dict[Path, tuple[float, int]] = {}
        self._last_measured_at = 0.0
        self._last_measured_total = 0
        self._last_reported_at = 0.0
        self._is_tty = bool(sys.stdout.isatty())
        self._status_visible = False
        self._status_line_count = 4
        self._last_lines: list[str] = []
        self._spinner_index = 0
        self._io_lock = threading.RLock()
        self._refresh_stop_event = threading.Event()
        self._refresh_thread: threading.Thread | None = None

    def _measure_output_bytes(self, force: bool = False) -> int:
        now = time.monotonic()
        if (not force) and (now - self._last_measured_at < PROGRESS_SCAN_MIN_INTERVAL_SECONDS):
            return self._last_measured_total
        total = 0
        active_paths = set(self.tracked_output_files)
        for path in self.tracked_output_files:
            try:
                if not path.exists():
                    self._tracked_size_cache.pop(path, None)
                    continue
                stat = path.stat()
                if self.run_started_at > 0 and stat.st_mtime + 1e-6 < self.run_started_at:
                    self._tracked_size_cache[path] = (stat.st_mtime, 0)
                    continue
                cached = self._tracked_size_cache.get(path)
                if cached is not None and abs(cached[0] - stat.st_mtime) < 1e-6:
                    size_bytes = cached[1]
                else:
                    size_bytes = stat.st_size
                    self._tracked_size_cache[path] = (stat.st_mtime, size_bytes)
                total += size_bytes
            except OSError:
                continue
        for stale_path in list(self._tracked_size_cache):
            if stale_path not in active_paths:
                self._tracked_size_cache.pop(stale_path, None)
        self._last_measured_at = now
        self._last_measured_total = total
        return total

    def emit_usage_progress(self, force: bool = False) -> None:
        with self._io_lock:
            now = time.monotonic()
            if (not force) and (now - self._last_reported_at < CLI_PROGRESS_REPORT_MIN_INTERVAL_SECONDS):
                return
            current = self._measure_output_bytes(force=force)
            total = max(1, self.predicted_total_bytes, current)
            ratio = current / total
            cpu_value = read_cpu_usage_percent()
            gpu_value = read_gpu_usage_percent()
            lines = self._build_status_lines(
                ratio=ratio,
                current_bytes=current,
                total_bytes=total,
                cpu_value=cpu_value,
                gpu_value=gpu_value,
                finished=False,
            )
            self._render_status(lines)
            self._last_reported_at = now

    def on_progress_message(self, message: str) -> None:
        with self._io_lock:
            self._clear_status_block()
            print(message, flush=True)
        self.emit_usage_progress(force=False)

    def emit_completed(self) -> None:
        with self._io_lock:
            current = self._measure_output_bytes(force=True)
            if current <= 0:
                total = max(1, self.predicted_total_bytes)
                current = total
            else:
                total = current
            cpu_value = read_cpu_usage_percent()
            gpu_value = read_gpu_usage_percent()
            lines = self._build_status_lines(
                ratio=1.0,
                current_bytes=current,
                total_bytes=total,
                cpu_value=cpu_value,
                gpu_value=gpu_value,
                finished=True,
            )
            self._render_status(lines, force_newline=True)

    def clear_for_summary(self) -> None:
        with self._io_lock:
            self._clear_status_block()

    def start_auto_refresh(self) -> None:
        if not self._is_tty:
            return
        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            return
        self._refresh_stop_event.clear()
        self._refresh_thread = threading.Thread(
            target=self._refresh_loop,
            name="cli-progress-refresh",
            daemon=True,
        )
        self._refresh_thread.start()

    def stop_auto_refresh(self) -> None:
        self._refresh_stop_event.set()
        thread = self._refresh_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self._refresh_thread = None

    def _refresh_loop(self) -> None:
        while not self._refresh_stop_event.wait(CLI_PROGRESS_REPORT_MIN_INTERVAL_SECONDS):
            try:
                self.emit_usage_progress(force=True)
            except Exception:
                # 監控刷新失敗不影響轉換流程
                continue

    def _progress_bar(self, ratio: float) -> str:
        clamped = max(0.0, min(1.0, ratio))
        filled_units = CLI_PROGRESS_BAR_WIDTH * clamped
        full_cells = int(filled_units)
        fraction = filled_units - full_cells

        chars = ["⣿"] * max(0, min(CLI_PROGRESS_BAR_WIDTH, full_cells))
        if len(chars) < CLI_PROGRESS_BAR_WIDTH:
            if fraction >= 0.66:
                chars.append("⣷")
            elif fraction >= 0.33:
                chars.append("⣦")
            else:
                chars.append("⣀")
        while len(chars) < CLI_PROGRESS_BAR_WIDTH:
            chars.append("⣀")
        return "".join(chars[:CLI_PROGRESS_BAR_WIDTH])

    def _usage_bar(self, value: float | None) -> str:
        if value is None:
            return "-" * CLI_USAGE_BAR_WIDTH
        clamped = max(0.0, min(100.0, float(value)))
        filled = int(round(CLI_USAGE_BAR_WIDTH * (clamped / 100.0)))
        return "#" * filled + "-" * (CLI_USAGE_BAR_WIDTH - filled)

    def _spinner_line(self, finished: bool) -> str:
        spinner = CLI_SPINNER_FRAMES[-1] if finished else CLI_SPINNER_FRAMES[
            self._spinner_index % len(CLI_SPINNER_FRAMES)
        ]
        self._spinner_index += 1
        return f"{spinner}    "

    def _build_status_lines(
        self,
        ratio: float,
        current_bytes: int,
        total_bytes: int,
        cpu_value: float | None,
        gpu_value: float | None,
        finished: bool,
    ) -> list[str]:
        percent_text = f"{int(round(max(0.0, min(1.0, ratio)) * 100))}%"
        return [
            f"{self._progress_bar(ratio)} {percent_text}",
            f"[CPU ] [{self._usage_bar(cpu_value)}] {_format_usage_percent(cpu_value)}",
            f"[GPU ] [{self._usage_bar(gpu_value)}] {_format_usage_percent(gpu_value)}",
            self._spinner_line(finished=finished),
        ]

    def _terminal_width(self) -> int:
        try:
            return max(40, shutil.get_terminal_size((120, 20)).columns)
        except Exception:
            return 120

    def _trim_line(self, text: str) -> str:
        width = self._terminal_width()
        if len(text) <= width:
            return text
        return text[: max(1, width - 1)]

    def _clear_status_block(self) -> None:
        if not self._is_tty or not self._status_visible:
            return
        for idx in range(self._status_line_count):
            sys.stdout.write("\r\033[2K")
            if idx < self._status_line_count - 1:
                sys.stdout.write("\033[1A")
        sys.stdout.write("\r")
        sys.stdout.flush()
        self._status_visible = False

    def _render_status(self, lines: list[str], force_newline: bool = False) -> None:
        safe_lines = [self._trim_line(line) for line in lines]
        self._status_line_count = len(safe_lines)
        if not self._is_tty:
            print("\n".join(safe_lines), flush=True)
            return

        self._clear_status_block()
        for idx, line in enumerate(safe_lines):
            if idx > 0:
                sys.stdout.write("\n")
            sys.stdout.write("\r\033[2K")
            sys.stdout.write(line)
        if force_newline:
            sys.stdout.write("\n")
            self._status_visible = False
        else:
            self._status_visible = True
        sys.stdout.flush()
        self._last_lines = safe_lines


def run_conversion_with_options(workspace_root: Path, options: ConvertOptions) -> int:
    progress_reporter: CliProgressReporter | None = None
    root_output_dir = workspace_root / DEFAULT_OUTPUT_DIR_NAME
    root_output_dir.mkdir(parents=True, exist_ok=True)
    pre_removed_dirs, pre_removed_files = cleanup_temp_artifacts(root_output_dir)
    if pre_removed_dirs > 0 or pre_removed_files > 0:
        print(f"啟動前已移動暫存到 del：{pre_removed_dirs} 個資料夾、{pre_removed_files} 個檔案")
    try:
        markdown_files = scan_numeric_markdown_files(workspace_root)

        sentence_cache_for_convert: dict[Path, list[str]] | None = None
        predicted_total_bytes = 1
        tracked_output_files: list[Path] = []

        if markdown_files:
            preview_manifest = load_manifest(root_output_dir)
            preview_files = preview_manifest.get("files", {})
            if not isinstance(preview_files, dict):
                preview_files = {}
            markdown_metadata, _, _ = build_markdown_metadata(markdown_files, preview_files)
            sentence_cache_doc = load_sentence_cache(root_output_dir)
            sentence_cache_for_convert, updated_sentence_cache_doc, _ = build_effective_sentence_cache(
                markdown_files=markdown_files,
                markdown_metadata=markdown_metadata,
                provided_sentence_cache=None,
                sentence_cache_doc=sentence_cache_doc,
            )
            save_sentence_cache(root_output_dir, updated_sentence_cache_doc)
            predicted_total_bytes, tracked_output_files = build_size_progress_plan(
                workspace_root=workspace_root,
                markdown_files=markdown_files,
                sentence_cache=sentence_cache_for_convert,
                options=options,
            )
        progress_reporter = CliProgressReporter(
            tracked_output_files=tracked_output_files,
            predicted_total_bytes=predicted_total_bytes,
        )

        print(f"使用 voice: {options.voice}")
        print(f"預估輸出總大小: {format_size_bytes(predicted_total_bytes)}")
        progress_reporter.start_auto_refresh()

        results = asyncio.run(
            convert_workspace(
                workspace_root,
                options,
                progress=progress_reporter.on_progress_message,
                sentence_cache=sentence_cache_for_convert,
            )
        )
        progress_reporter.stop_auto_refresh()
        progress_reporter.emit_completed()
        summary_lines = []
        for mode, (generated, full_output, _) in results.items():
            summary_lines.append(f"{mode}: {len(generated)} 個單檔 + {full_output.name}")
        print("成功：" + "；".join(summary_lines))
        all_warnings = []
        for _, (_, _, warns) in results.items():
            all_warnings.extend(warns)
        for warning in all_warnings:
            print(f"警告：{warning}")
        return 0
    except KeyboardInterrupt:
        if progress_reporter is not None:
            progress_reporter.stop_auto_refresh()
            progress_reporter.clear_for_summary()
        print("使用者中斷。", file=sys.stderr)
        return 130
    except Exception as exc:
        if progress_reporter is not None:
            progress_reporter.stop_auto_refresh()
            progress_reporter.clear_for_summary()
        print(f"失敗：{exc}", file=sys.stderr)
        return 1
    finally:
        post_removed_dirs, post_removed_files = cleanup_temp_artifacts(root_output_dir)
        if post_removed_dirs > 0 or post_removed_files > 0:
            print(f"執行結束已移動暫存到 del：{post_removed_dirs} 個資料夾、{post_removed_files} 個檔案")


def _prompt_choice(
    title: str,
    options: list[tuple[str, str]],
    default_value: str,
) -> str:
    option_values = [value for value, _ in options]
    while True:
        print(f"\n{title}")
        for idx, (value, label) in enumerate(options, start=1):
            default_tag = "（預設）" if value == default_value else ""
            print(f"  {idx}. {label} [{value}] {default_tag}".rstrip())
        raw = input(f"請輸入編號或值（Enter={default_value}）：").strip()
        if not raw:
            return default_value
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(options):
                return options[index - 1][0]
        if raw in option_values:
            return raw
        print("輸入無效，請重新輸入。")


def _prompt_float(
    label: str,
    default_value: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    while True:
        raw = input(f"{label}（Enter={default_value}）：").strip()
        if not raw:
            return default_value
        try:
            value = float(raw)
        except ValueError:
            print("請輸入數字。")
            continue
        if min_value is not None and value < min_value:
            print(f"數值必須 >= {min_value}")
            continue
        if max_value is not None and value > max_value:
            print(f"數值必須 <= {max_value}")
            continue
        return value


def _prompt_yes_no(label: str, default_yes: bool = True) -> bool:
    default_hint = "Y/n" if default_yes else "y/N"
    while True:
        raw = input(f"{label} [{default_hint}]：").strip().lower()
        if not raw:
            return default_yes
        if raw in {"y", "yes", "1", "是"}:
            return True
        if raw in {"n", "no", "0", "否"}:
            return False
        print("請輸入 y 或 n。")


def _prompt_voice(default_voice: str, choices: list[tuple[str, str]]) -> str:
    voice_ids = [voice_id for _, voice_id in choices]
    preferred: list[str] = []
    for candidate in PREFERRED_DEFAULT_VOICES:
        if candidate in voice_ids and candidate not in preferred:
            preferred.append(candidate)
    for voice_id in voice_ids:
        if voice_id.startswith(("en-US-", "en-CA-", "en-GB-")) and voice_id not in preferred:
            preferred.append(voice_id)
        if len(preferred) >= 12:
            break
    if default_voice in voice_ids and default_voice not in preferred:
        preferred.insert(0, default_voice)
    if not preferred:
        preferred = [default_voice]

    while True:
        print("\n聲音選擇")
        for idx, voice_id in enumerate(preferred, start=1):
            default_tag = "（預設）" if voice_id == default_voice else ""
            print(f"  {idx}. {voice_id} {default_tag}".rstrip())
        print("  m. 手動輸入 voice id")
        raw = input(f"請輸入編號（Enter={default_voice}）：").strip()
        if not raw:
            return default_voice
        if raw.lower() == "m":
            manual = input("請輸入完整 voice id：").strip()
            if not manual:
                return default_voice
            if manual in voice_ids:
                return manual
            print("找不到此 voice id，可先用 --list-voices 查詢。")
            continue
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(preferred):
                return preferred[index - 1]
        if raw in voice_ids:
            return raw
        print("輸入無效，請重新輸入。")


def run_interactive_cli(
    workspace_root: Path,
    voice: str | None,
    rate: float,
    gap: float,
    repeat_mode: str,
    use_gpu: bool,
) -> int:
    print("=== 互動式 CLI 設定精靈 ===")
    print(f"workspace: {workspace_root}")

    voice_choices: list[tuple[str, str]] = []
    default_voice = voice or "en-US-JennyNeural"
    try:
        voice_choices = asyncio.run(fetch_voice_choices())
        if voice:
            available_voice_ids = {voice_id for _, voice_id in voice_choices}
            if voice not in available_voice_ids:
                print(f"警告：指定 voice 不在清單中，改用預設 {default_voice}")
                default_voice = pick_default_voice(voice_choices)
        else:
            default_voice = pick_default_voice(voice_choices)
        print(f"已載入 {len(voice_choices)} 個 voice。")
    except Exception as exc:
        print(f"警告：載入 voice 清單失敗：{exc}")
        print(f"將使用 voice: {default_voice}")

    current_mode = repeat_mode
    current_use_gpu = use_gpu
    current_rate = max(0.5, min(2.0, float(rate)))
    current_gap = max(0.0, float(gap))
    current_voice = default_voice

    startup_mode = _prompt_choice(
        "啟動方式",
        [
            ("all-defaults", "全部預設（直接開始，不再逐題詢問）"),
            ("custom", "手動設定參數"),
        ],
        "all-defaults",
    )
    if startup_mode == "all-defaults":
        print("\n=== 全部預設設定 ===")
        print(f"voice: {current_voice}")
        print(f"mode: {current_mode}")
        print(f"video-device: {'gpu' if current_use_gpu else 'cpu'}")
        print(f"rate: {current_rate}")
        print(f"gap: {current_gap}")
        options = ConvertOptions(
            voice=current_voice,
            rate_multiplier=current_rate,
            gap_seconds=current_gap,
            repeat_mode=current_mode,
            use_gpu=current_use_gpu,
        )
        return run_conversion_with_options(workspace_root, options)

    try:
        while True:
            mode_options = [
                ("once", "一次"),
                ("twice", "兩次（每句重複兩次）"),
                ("both", "一次 + 兩次"),
            ]
            device_options = [
                ("gpu", "GPU 視訊編碼"),
                ("cpu", "CPU 視訊編碼"),
            ]

            current_mode = _prompt_choice("轉換模式", mode_options, current_mode)
            selected_device = _prompt_choice(
                "視訊編碼後端",
                device_options,
                "gpu" if current_use_gpu else "cpu",
            )
            current_use_gpu = selected_device == "gpu"
            current_rate = _prompt_float("語速倍率（0.5 ~ 2.0）", current_rate, min_value=0.5, max_value=2.0)
            current_gap = _prompt_float("每句間隔秒數（>= 0）", current_gap, min_value=0.0)
            if voice_choices:
                current_voice = _prompt_voice(current_voice, voice_choices)
            else:
                raw_voice = input(f"聲音 voice id（Enter={current_voice}）：").strip()
                if raw_voice:
                    current_voice = raw_voice

            print("\n=== 目前設定 ===")
            print(f"voice: {current_voice}")
            print(f"mode: {current_mode}")
            print(f"video-device: {'gpu' if current_use_gpu else 'cpu'}")
            print(f"rate: {current_rate}")
            print(f"gap: {current_gap}")

            if not _prompt_yes_no("開始轉換？", default_yes=True):
                if _prompt_yes_no("要重新設定參數嗎？", default_yes=True):
                    continue
                print("已取消。")
                return 0

            options = ConvertOptions(
                voice=current_voice,
                rate_multiplier=current_rate,
                gap_seconds=current_gap,
                repeat_mode=current_mode,
                use_gpu=current_use_gpu,
            )
            result_code = run_conversion_with_options(workspace_root, options)
            if result_code != 0:
                if _prompt_yes_no("轉換失敗，是否重新設定後重試？", default_yes=True):
                    continue
                return result_code
            if not _prompt_yes_no("轉換完成，是否再執行一次不同設定？", default_yes=False):
                return result_code
    except KeyboardInterrupt:
        print("\n使用者中斷。", file=sys.stderr)
        return 130


def run_gui(workspace_root: Path) -> int:
    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")

    from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot, qInstallMessageHandler
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QProgressBar,
        QVBoxLayout,
        QWidget,
    )

    def qt_message_handler(msg_type, context, message) -> None:
        if any(pattern in message for pattern in QT_NOISY_WARNING_PATTERNS):
            return
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    qInstallMessageHandler(qt_message_handler)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)

    class ConvertWorker(QObject):
        progress = Signal(str)
        progressUpdate = Signal(int, int)  # (current_bytes, predicted_total_bytes)
        finished = Signal(bool, str, dict)

        def __init__(self, root: Path, options: ConvertOptions):
            super().__init__()
            self.root = root
            self.options = options
            self.predicted_total_bytes = 1
            self.current_output_bytes = 0
            self.tracked_output_files: list[Path] = []
            self.run_started_at = 0.0
            self._tracked_size_cache: dict[Path, tuple[float, int]] = {}
            self._last_measured_at = 0.0
            self._last_measured_total = 0
            self.execution_control = ExecutionControl()

        @Slot()
        def request_stop(self) -> None:
            self.execution_control.stop_event.set()
            self.execution_control.terminate_all_processes()

        def _measure_output_bytes(self, force: bool = False) -> int:
            now = time.monotonic()
            if (not force) and (now - self._last_measured_at < PROGRESS_SCAN_MIN_INTERVAL_SECONDS):
                return self._last_measured_total
            total = 0
            active_paths = set(self.tracked_output_files)
            for path in self.tracked_output_files:
                try:
                    if not path.exists():
                        self._tracked_size_cache.pop(path, None)
                        continue
                    stat = path.stat()
                    if self.run_started_at > 0 and stat.st_mtime + 1e-6 < self.run_started_at:
                        # 舊檔不納入本輪進度，避免重跑時直接出現高進度
                        self._tracked_size_cache[path] = (stat.st_mtime, 0)
                        continue
                    cached = self._tracked_size_cache.get(path)
                    if cached is not None and abs(cached[0] - stat.st_mtime) < 1e-6:
                        size_bytes = cached[1]
                    else:
                        size_bytes = stat.st_size
                        self._tracked_size_cache[path] = (stat.st_mtime, size_bytes)
                    total += size_bytes
                except OSError:
                    continue
            for stale_path in list(self._tracked_size_cache):
                if stale_path not in active_paths:
                    self._tracked_size_cache.pop(stale_path, None)
            self._last_measured_at = now
            self._last_measured_total = total
            return total

        @Slot()
        def run(self) -> None:
            try:
                with execution_context(self.execution_control):
                    self.run_started_at = time.time()
                    # 先掃描並建立句子快取，供預估與轉換共用
                    markdown_files = scan_numeric_markdown_files(self.root)
                    root_output_dir = self.root / DEFAULT_OUTPUT_DIR_NAME
                    root_output_dir.mkdir(parents=True, exist_ok=True)
                    preview_manifest = load_manifest(root_output_dir)
                    preview_files = preview_manifest.get("files", {})
                    if not isinstance(preview_files, dict):
                        preview_files = {}
                    markdown_metadata, reused_hash_count, recomputed_hash_count = build_markdown_metadata(
                        markdown_files,
                        preview_files,
                    )
                    sentence_cache_doc = load_sentence_cache(root_output_dir)
                    sentence_cache, updated_sentence_cache_doc, reused_sentence_files = (
                        build_effective_sentence_cache(
                            markdown_files=markdown_files,
                            markdown_metadata=markdown_metadata,
                            provided_sentence_cache=None,
                            sentence_cache_doc=sentence_cache_doc,
                        )
                    )
                    save_sentence_cache(root_output_dir, updated_sentence_cache_doc)
                    if reused_hash_count > 0:
                        self.progress.emit(f"hash 快取命中：{reused_hash_count} 個檔案")
                    if recomputed_hash_count > 0:
                        self.progress.emit(f"hash 重算：{recomputed_hash_count} 個檔案")
                    if reused_sentence_files > 0:
                        self.progress.emit(f"句子快取命中：{reused_sentence_files} 個檔案")

                    predicted_total_bytes, tracked_output_files = build_size_progress_plan(
                        workspace_root=self.root,
                        markdown_files=markdown_files,
                        sentence_cache=sentence_cache,
                        options=self.options,
                    )
                    self.predicted_total_bytes = max(1, predicted_total_bytes)
                    self.tracked_output_files = tracked_output_files
                    self.current_output_bytes = self._measure_output_bytes(force=True)
                    self.progressUpdate.emit(self.current_output_bytes, self.predicted_total_bytes)
                    self.progress.emit(
                        f"預估輸出總大小: {format_size_bytes(self.predicted_total_bytes)}"
                    )

                    def progress_with_tracking(msg: str) -> None:
                        self.progress.emit(msg)
                        self.current_output_bytes = self._measure_output_bytes()
                        if self.current_output_bytes > self.predicted_total_bytes:
                            self.predicted_total_bytes = self.current_output_bytes
                        self.progressUpdate.emit(self.current_output_bytes, self.predicted_total_bytes)

                    results = asyncio.run(
                        convert_workspace(
                            self.root,
                            self.options,
                            progress=progress_with_tracking,
                            sentence_cache=sentence_cache,
                        )
                    )
                summary_lines = []
                for mode, (generated, full_output, _) in results.items():
                    summary_lines.append(f"{mode}: {len(generated)} 個單檔 + {full_output.name}")
                summary = "完成轉換：" + "；".join(summary_lines)
                all_warnings = []
                for _, (_, _, warns) in results.items():
                    all_warnings.extend(warns)
                self.current_output_bytes = self._measure_output_bytes(force=True)
                self.predicted_total_bytes = max(self.predicted_total_bytes, self.current_output_bytes, 1)
                self.progressUpdate.emit(self.current_output_bytes, self.predicted_total_bytes)
                self.progressUpdate.emit(self.predicted_total_bytes, self.predicted_total_bytes)  # 完成
                self.finished.emit(True, summary, {"warnings": all_warnings, "results": results})
            except ConversionCancelled:
                self.finished.emit(
                    False,
                    "已強制停止轉換。",
                    {"warnings": [], "results": {}, "cancelled": True},
                )
            except Exception as exc:
                detail = f"{exc}\n\n{traceback.format_exc()}"
                self.finished.emit(False, detail, {})

    class MainWindow(QWidget):
        def __init__(self, root: Path):
            super().__init__()
            self.workspace_root = root
            self.thread: QThread | None = None
            self.worker: ConvertWorker | None = None
            self.resource_timer: QTimer | None = None
            self.stop_requested = False

            self.setWindowTitle("複習檔案產生工具")
            self.resize(880, 620)
            self._build_ui()
            self._apply_theme()
            self._setup_resource_monitor()
            self._load_voices()

        def _build_ui(self) -> None:
            main_layout = QVBoxLayout(self)

            title = QLabel("批次產生複習音檔（一次/兩次重複）")
            main_layout.addWidget(title)

            form = QFormLayout()
            self.voice_combo = QComboBox()
            self.rate_spin = QDoubleSpinBox()  # 倍率表示
            self.rate_spin.setRange(0.5, 2.0)
            self.rate_spin.setValue(1.0)  # 1.0 = 1倍速
            self.rate_spin.setDecimals(1)
            self.rate_spin.setSingleStep(0.1)
            self.rate_spin.setSuffix("x")
            self.gap_spin = QDoubleSpinBox()
            self.gap_spin.setRange(0.0, 10.0)
            self.gap_spin.setDecimals(2)
            self.gap_spin.setSingleStep(0.1)
            self.gap_spin.setValue(0.40)
            self.gap_spin.setSuffix(" 秒")

            # 轉換模式選項
            self.once_check = QCheckBox("產生「一次」")
            self.once_check.setChecked(True)
            self.twice_check = QCheckBox("產生「兩次」（每句重複兩次）")
            self.twice_check.setChecked(True)
            self.use_gpu_check = QCheckBox("使用 GPU 視訊編碼")
            self.use_gpu_check.setChecked(True)

            form.addRow("聲音樣式", self.voice_combo)
            form.addRow("語速（倍率）", self.rate_spin)
            form.addRow("每句間隔時間", self.gap_spin)
            form.addRow("", self.once_check)
            form.addRow("", self.twice_check)
            form.addRow("", self.use_gpu_check)
            main_layout.addLayout(form)

            button_layout = QHBoxLayout()
            self.reload_button = QPushButton("重新載入聲音")
            self.convert_button = QPushButton("轉換")
            self.stop_button = QPushButton("強制停止")
            self.convert_button.setObjectName("convertButton")
            self.stop_button.setObjectName("stopButton")
            self.reload_button.clicked.connect(self._load_voices)
            self.convert_button.clicked.connect(self._start_convert)
            self.stop_button.clicked.connect(self._force_stop_convert)
            self.stop_button.setEnabled(False)
            button_layout.addWidget(self.reload_button)
            button_layout.addWidget(self.convert_button)
            button_layout.addWidget(self.stop_button)
            button_layout.addStretch()
            main_layout.addLayout(button_layout)

            resource_form = QFormLayout()
            self.cpu_usage_bar = QProgressBar()
            self.cpu_usage_bar.setRange(0, 100)
            self.cpu_usage_bar.setValue(0)
            self.cpu_usage_bar.setFormat("CPU: N/A")
            self.gpu_usage_bar = QProgressBar()
            self.gpu_usage_bar.setRange(0, 100)
            self.gpu_usage_bar.setValue(0)
            self.gpu_usage_bar.setFormat("GPU: N/A")
            resource_form.addRow("CPU 使用率", self.cpu_usage_bar)
            resource_form.addRow("GPU 使用率", self.gpu_usage_bar)
            main_layout.addLayout(resource_form)

            # 進度條
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("轉換進度: 0.0% (0 B / 0 B)")
            self.progress_bar.setVisible(False)
            main_layout.addWidget(self.progress_bar)

            self.status_box = QPlainTextEdit()
            self.status_box.setReadOnly(True)
            main_layout.addWidget(self.status_box)

            self._append_status(f"workspace: {self.workspace_root}")
            self._append_status(f"輸出目錄: {self.workspace_root / DEFAULT_OUTPUT_DIR_NAME}")

        def _apply_theme(self) -> None:
            self.setStyleSheet(
                f"""
                QWidget {{
                    font-size: 13px;
                }}
                QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {{
                    border: 1px solid #c6d1d8;
                    border-radius: 6px;
                    padding: 4px;
                }}
                QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {{
                    border: 1px solid {DEFAULT_THEME_COLOR};
                }}
                QPushButton {{
                    border: 1px solid #9aa7ad;
                    border-radius: 7px;
                    padding: 7px 14px;
                }}
                QPushButton#convertButton {{
                    background: {DEFAULT_THEME_COLOR};
                    border: 1px solid #42bdd8;
                    color: #06323a;
                    font-weight: 700;
                }}
                QPushButton#stopButton {{
                    background: #fbe9e7;
                    border: 1px solid #e57373;
                    color: #7a1c1c;
                    font-weight: 700;
                }}
                QPushButton:disabled {{
                    color: #7c8a90;
                    background: #edf2f4;
                }}
                """
            )

        def _append_status(self, message: str) -> None:
            self.status_box.appendPlainText(message)

        def _setup_resource_monitor(self) -> None:
            self.resource_timer = QTimer(self)
            self.resource_timer.setInterval(RESOURCE_MONITOR_INTERVAL_MS)
            self.resource_timer.timeout.connect(self._refresh_resource_usage)
            self.resource_timer.start()
            self._refresh_resource_usage()

        def _set_usage_bar(self, bar: QProgressBar, name: str, value: float | None) -> None:
            if value is None:
                bar.setValue(0)
                bar.setFormat(f"{name}: N/A")
                return
            percent = int(max(0, min(100, round(value))))
            bar.setValue(percent)
            bar.setFormat(f"{name}: {percent}%")

        @Slot()
        def _refresh_resource_usage(self) -> None:
            self._set_usage_bar(self.cpu_usage_bar, "CPU", read_cpu_usage_percent())
            self._set_usage_bar(self.gpu_usage_bar, "GPU", read_gpu_usage_percent())

        def _load_voices(self) -> None:
            self.reload_button.setEnabled(False)
            self._append_status("讀取 voice 清單中...")
            try:
                choices = asyncio.run(fetch_voice_choices())
                self.voice_combo.clear()
                for label, voice_id in choices:
                    self.voice_combo.addItem(label, voice_id)
                default_voice = pick_default_voice(choices)
                idx = self.voice_combo.findData(default_voice)
                if idx >= 0:
                    self.voice_combo.setCurrentIndex(idx)
                self._append_status(f"已載入 {len(choices)} 個聲音。")
            except Exception as exc:
                self._append_status(f"載入 voice 失敗：{exc}")
                QMessageBox.warning(self, "voice 載入失敗", str(exc))
            finally:
                self.reload_button.setEnabled(True)

        def _current_options(self) -> ConvertOptions:
            voice = self.voice_combo.currentData()
            if not voice:
                raise ConversionError("請先選擇聲音樣式。")

            # 判斷轉換模式
            if self.once_check.isChecked() and self.twice_check.isChecked():
                repeat_mode = "both"
            elif self.twice_check.isChecked():
                repeat_mode = "twice"
            elif self.once_check.isChecked():
                repeat_mode = "once"
            else:
                raise ConversionError("請至少選擇產生「一次」或「兩次」中的一個。")

            return ConvertOptions(
                voice=str(voice),
                rate_multiplier=float(self.rate_spin.value()),
                gap_seconds=float(self.gap_spin.value()),
                use_gpu=bool(self.use_gpu_check.isChecked()),
                repeat_mode=repeat_mode,
            )

        def _start_convert(self) -> None:
            if self.thread is not None:
                self._append_status("目前已有轉換進行中。")
                return

            try:
                options = self._current_options()
            except Exception as exc:
                QMessageBox.warning(self, "設定錯誤", str(exc))
                return

            self.convert_button.setEnabled(False)
            self.reload_button.setEnabled(False)
            self.once_check.setEnabled(False)
            self.twice_check.setEnabled(False)
            self.use_gpu_check.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.stop_requested = False
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("轉換進度: 0.0% (0 B / 0 B)")

            self.thread = QThread(self)
            self.worker = ConvertWorker(self.workspace_root, options)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.progress.connect(self._append_status)
            self.worker.progressUpdate.connect(self._on_progress_update)
            self.worker.finished.connect(self._on_finished)
            self.worker.finished.connect(self.thread.quit)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self._cleanup_thread)
            self.thread.start()

        @Slot()
        def _force_stop_convert(self) -> None:
            if self.thread is None or self.worker is None:
                self._append_status("目前沒有進行中的轉換。")
                return
            if self.stop_requested:
                self._append_status("已送出強制停止請求，請稍候。")
                return
            self.stop_requested = True
            self.stop_button.setEnabled(False)
            self._append_status("已送出強制停止請求，正在中止目前轉換...")
            self.worker.request_stop()

        @Slot(int, int)
        def _on_progress_update(self, current: int, total: int) -> None:
            if total <= 0:
                self.progress_bar.setRange(0, 1000)
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("轉換進度: 0.0% (0 B / 0 B)")
                return
            clamped = max(0, min(current, total))
            ratio = clamped / total
            scaled_value = int(ratio * 1000)
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(scaled_value)
            self.progress_bar.setFormat(
                f"轉換進度: {ratio * 100:.1f}% ({format_size_bytes(clamped)} / {format_size_bytes(total)})"
            )

        @Slot(bool, str, dict)
        def _on_finished(self, ok: bool, message: str, data: dict) -> None:
            self.convert_button.setEnabled(True)
            self.reload_button.setEnabled(True)
            self.once_check.setEnabled(True)
            self.twice_check.setEnabled(True)
            self.use_gpu_check.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.stop_requested = False
            self.progress_bar.setVisible(False)
            self._append_status(message)
            warnings = data.get("warnings", [])
            for warning in warnings:
                self._append_status(f"警告：{warning}")

            if data.get("cancelled"):
                QMessageBox.information(self, "已停止", message)
            elif ok:
                if warnings:
                    QMessageBox.information(
                        self,
                        "轉換完成（含警告）",
                        message + "\n\n" + "\n".join(warnings),
                    )
                else:
                    QMessageBox.information(self, "轉換完成", message)
            else:
                QMessageBox.critical(self, "轉換失敗", message)

        @Slot()
        def _cleanup_thread(self) -> None:
            if self.worker is not None:
                self.worker.deleteLater()
            self.thread = None
            self.worker = None
            self.stop_button.setEnabled(False)
            self.stop_requested = False

    app = QApplication(sys.argv)
    window = MainWindow(workspace_root)
    window.show()
    return app.exec()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="複習檔案產生工具（批次 TTS 轉檔）")
    parser.add_argument(
        "--workspace",
        default=str(Path(__file__).resolve().parent),
        help="工作目錄（預設為本腳本所在資料夾）",
    )
    parser.add_argument("--run-once", action="store_true", help="不進入互動設定，直接執行一次轉換")
    parser.add_argument("--voice", default=None, help="edge-tts voice，例如 en-US-JennyNeural")
    parser.add_argument("--rate", type=float, default=1.0, help="語速倍率（0.5~2.0，預設 1.0=1倍速）")
    parser.add_argument("--gap", type=float, default=0.4, help="每句間隔秒數（>=0）")
    parser.add_argument(
        "--mode",
        default="both",
        choices=["once", "twice", "both"],
        help="轉換模式：once=一次，twice=兩次，both=兩者都產生",
    )
    parser.add_argument(
        "--video-device",
        default="gpu",
        choices=["gpu", "cpu"],
        help="視訊編碼後端：gpu 或 cpu",
    )
    parser.add_argument("--list-voices", action="store_true", help="列出可用 voice 後離開")
    return parser


def main() -> int:
    ensure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args()
    workspace_root = Path(os.path.abspath(os.path.expanduser(args.workspace)))

    if not workspace_root.exists():
        print(f"workspace 不存在：{workspace_root}", file=sys.stderr)
        return 2

    if args.list_voices:
        try:
            choices = asyncio.run(fetch_voice_choices())
            for label, voice_id in choices:
                print(f"{voice_id}\t{label}")
            return 0
        except Exception as exc:
            print(f"列出 voice 失敗：{exc}", file=sys.stderr)
            return 1

    if args.run_once:
        return run_once_cli(
            workspace_root,
            args.voice,
            args.rate,
            args.gap,
            args.mode,
            use_gpu=(args.video_device == "gpu"),
        )

    return run_interactive_cli(
        workspace_root=workspace_root,
        voice=args.voice,
        rate=args.rate,
        gap=args.gap,
        repeat_mode=args.mode,
        use_gpu=(args.video_device == "gpu"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
