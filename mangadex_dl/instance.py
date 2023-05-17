"""
Mangadex-dl: instance.py
"""

import argparse
import tomllib
import logging
from pathlib import Path
from types import SimpleNamespace

from requests import Session

SESSION = Session()

def init() -> None:
    """Initialize mangadex_dl."""

    logging.basicConfig(format="[%(levelname)s] (%(filename)s): %(message)s")
    config_file = Path("config.toml")

    args_cfg = _parse_config(config_file)
    args_cmd = _parse_args()
    args_cfg.update(args_cmd)

    args = SimpleNamespace(**args_cfg)
    args.outdir = Path(args.outdir)

    if args.proxy:
        SESSION.proxies = {
            "http":  f"http://{args.proxy}",
            "https": f"https://{args.proxy}"
        }
    elif args.socks:
        SESSION.proxies = {
            "http":  f"socks5://{args.socks}",
            "https": f"socks5://{args.socks}"
        }

    if args.gui:
        from mangadex_dl.gui import init_gui
        init_gui(args)
    else:
        from mangadex_dl.console import init_console
        init_console(args)

def _parse_config(path: Path) -> dict:
    "Return config file args."

    data = {}

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        logging.warning(f"Config file not found: {path.absolute()}")

    return data

def _parse_args() -> dict:
    """Return command-line args."""

    p = argparse.ArgumentParser()

    p.add_argument("manga_urls", metavar="<manga_urls>", nargs="*",
                   help="specify manga url")

    return vars(p.parse_args())
