"""Catálogo auxiliar: os pacotes não substituem as estruturas principais."""
import json
from pathlib import Path


def load_packages(filepath=None):
    path = Path(filepath) if filepath else Path(__file__).resolve().parent.parent / "data" / "packages.json"
    return json.loads(path.read_text(encoding="utf-8"))


def find_package(packages, code):
    return next((package for package in packages if package["code"] == code), None)
