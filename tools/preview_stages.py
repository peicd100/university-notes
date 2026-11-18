"""Cache only deterministic text transformations during a local preview build."""
from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
import json
import logging
import os
from pathlib import Path
import sys
from uuid import uuid4

_active = ContextVar("preview_stages", default=None)


@contextmanager
def preview_stages(directory, versions):
    token = _active.set((directory, repr((sys.version, versions)), {}))
    try:
        yield
    finally:
        _active.reset(token)


def transform_text(function, source, page_key):
    context = _active.get()
    if context is None:
        return function(source)
    directory, runtime, signatures = context
    if function not in signatures:
        signatures[function] = sha256(Path(function.__code__.co_filename).read_bytes()
                                      + runtime.encode()).digest()
    key = sha256(signatures[function] + source.encode()).hexdigest()
    slot = directory / function.__name__ / (sha256(page_key.encode()).hexdigest() + ".json")
    try:
        saved_key, checksum, payload = json.loads(slot.read_bytes())
        if key == saved_key and checksum == sha256(payload.encode()).hexdigest():
            return json.loads(payload)
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    value = function(source)
    temporary = slot.with_suffix("." + uuid4().hex + ".tmp")
    try:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        slot.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps([key, sha256(payload.encode()).hexdigest(), payload],
                                       ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, slot)
    except OSError as error:
        logging.getLogger("mkdocs.preview_cache").warning("Preview stage cache write failed: %s", error)
    return value
