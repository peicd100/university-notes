"""Publish g.bat's successful staging build without rebuilding it."""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def publish(site_dir: Path, *, root: Path = ROOT, config_loader=None, deploy=None, check_only=False) -> None:
    site_dir = site_dir.resolve()
    if not (site_dir / "index.html").is_file():
        raise FileNotFoundError("Validated site/index.html is missing; build must succeed before deployment.")
    if config_loader is None:
        from mkdocs.config import load_config
        config_loader = load_config
    config = config_loader(config_file=str(root / "mkdocs.yml"), site_dir=str(site_dir))
    if check_only:
        logging.info("Deployment preflight passed; no Git changes or push performed.")
        return
    if deploy is None:
        from mkdocs.commands.gh_deploy import gh_deploy
        deploy = gh_deploy
    # MkDocs reads the current source HEAD here, after g.bat's source commit.
    # Defaults retain history and never force-push; errors propagate to g.bat.
    deploy(config)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", required=True, type=Path)
    parser.add_argument("--check", action="store_true", help="Validate built artifact/config only, without Git/deployment.")
    args = parser.parse_args()
    os.chdir(ROOT)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    try:
        publish(args.site_dir, check_only=args.check)
    except Exception as error:
        logging.error("Deployment stopped: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
