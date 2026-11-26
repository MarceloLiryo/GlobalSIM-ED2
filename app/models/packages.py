"""Catálogo auxiliar: os pacotes não substituem as estruturas principais."""
import json
import unicodedata
from pathlib import Path


def load_packages(filepath=None):
    path = Path(filepath) if filepath else Path(__file__).resolve().parent.parent / "data" / "packages.json"
    return json.loads(path.read_text(encoding="utf-8"))


def find_package(packages, code):
    return next((package for package in packages if package["code"] == code), None)


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).strip().lower()


def package_covers_region(package: dict | None, region: str) -> bool:
    """Verifica se o pacote contratado oferece cobertura na região do país consultado."""
    if not package or not region:
        return False

    norm_region = _normalize_text(region)
    configured_regions = package.get("regions")
    if isinstance(configured_regions, list):
        normalized = {_normalize_text(item) for item in configured_regions}
        return "global" in normalized or "*" in normalized or norm_region in normalized

    code = package.get("code")
    name = _normalize_text(package.get("name", ""))
    if code == 301 or "global" in name:
        return True
    if code in (101, 102) or "europa" in name:
        return "europa" in norm_region
    if code in (201, 202) or "america" in name:
        return "america" in norm_region
    return False

