import urllib.request
import json
import re
from config import GITHUB_REPO, GITHUB_TOKEN

def _parse_version(version_str: str) -> tuple:
    """Convierte '1.2.3' en (1, 2, 3) para comparación numérica."""
    clean = version_str.lstrip("v").strip()
    try:
        parts = [int(x) for x in clean.split(".")]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)
    except Exception:
        return (0, 0, 0)


def _fetch_latest_release() -> dict | None:
    """
    Consulta la API de GitHub Releases y retorna el release más reciente.
    Usa GITHUB_TOKEN si está disponible para evitar rate limiting (5000 req/h
    autenticado vs 60 req/h anónimo).
    Retorna None si falla la conexión o no hay releases.
    """
    if not GITHUB_REPO:
        return None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "FletAppUpdater/1.0")

    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _find_apk_url(release: dict) -> str | None:
    """
    Busca el primer asset .apk en los assets del release.
    Retorna la URL de descarga directa o None si no hay APK adjunto.
    """
    for asset in release.get("assets", []):
        if asset.get("name", "").endswith(".apk"):
            return asset.get("browser_download_url")
    return None


def _extract_changelog(body: str) -> list[str]:
    """
    Extrae los items del changelog desde el bloque especial embebido
    por release.py entre los marcadores:
        <!-- APP_CHANGELOG_START -->
        - item 1
        - item 2
        <!-- APP_CHANGELOG_END -->

    Retorna una lista de strings limpios, sin el guión inicial.
    Si no encuentra el bloque, retorna lista vacía.
    """
    match = re.search(
        r"<!-- APP_CHANGELOG_START -->(.*?)<!-- APP_CHANGELOG_END -->",
        body,
        re.DOTALL,
    )
    if not match:
        return []

    block = match.group(1).strip()
    items = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line:
            items.append(line)

    return items


def _extract_target(body: str) -> str:
    match = re.search(
        r'<!--\s*APP_TARGET:\s*(admin|user|all)\s*-->',
        body,
        re.IGNORECASE,
    )
    return match.group(1).lower() if match else "all"


def check_for_updates(current_version: str) -> dict:
    """
    Compara la versión instalada contra el último release de GitHub.

    Retorna un dict con:
        update_available (bool)
        is_critical      (bool)  : True si el título contiene [CRITICAL]
        latest_version   (str)   : ej. "2.1.0"
        changelog        (list)  : items extraídos del body del release
        apk_url          (str|None): URL directa al .apk adjunto
        release_url      (str|None): URL del release en GitHub
        error            (str|None): "no_connection" | "no_repo" | None
    """
    result = {
        "update_available": False,
        "is_critical":      False,
        "latest_version":   current_version,
        "changelog":        [],
        "apk_url":          None,
        "release_url":      None,
        "target":           "all",
        "error":            None,
    }

    if not GITHUB_REPO:
        result["error"] = "no_repo"
        return result

    release = _fetch_latest_release()

    if release is None:
        result["error"] = "no_connection"
        return result

    tag      = release.get("tag_name", "")
    name     = release.get("name", "")
    body     = release.get("body", "")
    html_url = release.get("html_url", "")

    latest_version = tag.lstrip("v").strip()
    result["latest_version"] = latest_version
    result["release_url"]    = html_url

    current_tuple = _parse_version(current_version)
    latest_tuple  = _parse_version(latest_version)

    if latest_tuple <= current_tuple:
        return result

    result["update_available"] = True
    result["is_critical"]      = "[CRITICAL]" in name.upper()
    result["apk_url"]          = _find_apk_url(release)
    result["changelog"]        = _extract_changelog(body)
    result["target"]           = _extract_target(body)

    return result