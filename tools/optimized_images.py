"""Lossless, content-addressed build derivatives; never overwrite source images."""
from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any

log = logging.getLogger("mkdocs.hooks.optimized_images")
POLICY_VERSION = "lossless-webp-v1-exact-method4"


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def derive_image(source: Path, config: Any, *, logo: bool = False, favicon: bool = False) -> dict[str, Any] | None:
    """Return a site URL and dimensions, or None to retain the original.

    Cache identity includes input bytes, Pillow/encoder version and policy. Each
    hit checks the output digest before reusing it. Only static PNGs are changed.
    """
    if source.suffix.lower() != ".png" or not source.is_file():
        return None
    try:
        import PIL
        from PIL import Image, ImageOps, features
    except ImportError:
        log.warning("Pillow is unavailable; retaining original images (install requirements.txt)")
        return None
    if not favicon and not features.check("webp"):
        return None
    raw = source.read_bytes()
    encoder = features.version("webp")
    identity = hashlib.sha256(raw + f"{POLICY_VERSION}/{PIL.__version__}/{encoder}/logo={logo}/favicon={favicon}".encode()).hexdigest()
    config_path = config.get("config_file_path") if hasattr(config, "get") else None
    project = Path(config_path).resolve().parent if config_path else Path(config["docs_dir"]).resolve().parent
    cache = project / ".cache/site-images" / identity[:2]
    meta_path = cache / (identity + ".json")
    extension = ".png" if favicon else ".webp"
    image_path = cache / (identity + extension)
    meta = None
    if meta_path.is_file():
        try:
            saved = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and saved.get("identity") == identity:
                if saved.get("use_original") is True:
                    return None
                valid_sizes = all(isinstance(saved.get(key), int) and saved[key] > 0
                                  for key in ("width", "height", "source_bytes", "output_bytes"))
                if valid_sizes and image_path.is_file():
                    cached_bytes = image_path.read_bytes()
                    if (len(cached_bytes) == saved["output_bytes"] and
                            saved["source_bytes"] == len(raw) and
                            hashlib.sha256(cached_bytes).hexdigest() == saved["sha256"]):
                        meta = saved
        except (OSError, ValueError, KeyError):
            pass  # Corrupted/missing cache: recompute only this input.
    if meta is None:
        try:
            with Image.open(io.BytesIO(raw)) as opened:
                if getattr(opened, "n_frames", 1) > 1:
                    return None  # APNG/animation must keep its frames.
                image = ImageOps.exif_transpose(opened).convert("RGBA")
                if logo or favicon:
                    size = 32 if favicon else 96
                    image.thumbnail((size, size), Image.Resampling.LANCZOS)
                out = io.BytesIO()
                if favicon:
                    image.save(out, format="PNG", optimize=True)
                else:
                    image.save(out, format="WEBP", lossless=True, exact=True, method=4,
                               icc_profile=opened.info.get("icc_profile", b""))
                data = out.getvalue()
                if len(data) >= len(raw):
                    _atomic_bytes(meta_path, json.dumps({"identity":identity,"use_original":True}).encode())
                    return None
                # Do not trust an encoder success alone: verify pixel parity.
                with Image.open(io.BytesIO(data)) as check:
                    if check.size != image.size or check.convert("RGBA").tobytes() != image.tobytes():
                        return None
                meta = {"identity":identity,"sha256":hashlib.sha256(data).hexdigest(),
                        "width":image.width,"height":image.height,"source_bytes":len(raw),"output_bytes":len(data)}
                _atomic_bytes(image_path, data)
                _atomic_bytes(meta_path, json.dumps(meta, sort_keys=True).encode())
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            log.warning("Keeping original image %s: %s", source.name, error)
            return None
    asset_url = f"assets/generated/optimized-images/{identity[:2]}/{identity}{extension}"
    destination = Path(config["site_dir"]).joinpath(*asset_url.split("/"))
    if not destination.is_file() or hashlib.sha256(destination.read_bytes()).hexdigest() != meta["sha256"]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        tmp = destination.with_name(destination.name + f".{os.getpid()}.tmp")
        shutil.copyfile(image_path, tmp)
        os.replace(tmp, destination)
    return {**meta, "url":asset_url}
