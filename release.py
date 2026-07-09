"""
release.py — Script de publicacion a GitHub Releases (proyecto Flutter)
Ubicacion: raiz del proyecto (junto a pubspec.yaml)

Estructura esperada:
    release.py                   <- este archivo
    pubspec.yaml                 <- debe contener version: x.y.z+n
    env.json                     <- debe contener GITHUB_REPO (config de la app, sin token)
    .env                         <- debe contener GITHUB_TOKEN (solo para este script,
                                     nunca se embebe en el APK — nunca va en env.json)
    release_info.json            <- opcional, generado o editado a mano
    build/
        app/outputs/flutter-apk/
            app-release.apk      <- generado por: flutter build apk --release --dart-define-from-file=env.json

Formato de release_info.json:
{
  "title": "titulo del release",
  "target": "all",       <- "all", "admin" o "user"
  "changelog": ["cambio 1", "cambio 2"],
  "changelog_user": ["..."],   <- opcional: mensaje que ve el rol user
  "changelog_admin": ["..."],  <- opcional: mensaje que ve el rol admin
  "description": ""
}

Los bloques changelog_user/changelog_admin solo los entienden las apps con
version >= 1.3.0 (extract_changelog con soporte de rol); las versiones
anteriores siempre muestran el bloque generico "changelog".

Uso:
    python release.py
"""

import re
import sys
import json
import socket
import http.client
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path


# ─── Colores para consola ─────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
GREY   = "\033[90m"

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def ok(msg):   print(f"  {GREEN}[OK]{RESET}  {msg}")
def info(msg): print(f"  {CYAN}[>]{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}[!]{RESET}  {msg}")
def err(msg):  print(f"  {RED}[X]{RESET}  {msg}")
def step(msg): print(f"\n{BOLD}{msg}{RESET}")


# ─── Lectura de .env manual (solo GITHUB_TOKEN) ──────────────────────────────

def load_env(env_path: Path) -> dict:
    env = {}
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    except Exception as e:
        err(f"No se pudo leer .env: {e}")
    return env


# ─── Extraccion de version desde pubspec.yaml ────────────────────────────────

def extract_app_version(pubspec_path: Path) -> str | None:
    """
    pubspec.yaml tiene una linea como:
        version: 1.2.3+4
    El "+4" es el build number de Android/iOS, no forma parte del tag de
    GitHub — el tag usa solo la parte x.y.z.
    """
    try:
        content = pubspec_path.read_text(encoding="utf-8")
        match = re.search(r'^version:\s*([0-9]+\.[0-9]+\.[0-9]+)(?:\+\d+)?\s*$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None


# ─── Lectura de env.json (solo GITHUB_REPO) ──────────────────────────────────

def load_github_repo(env_json_path: Path) -> str | None:
    try:
        data = json.loads(env_json_path.read_text(encoding="utf-8"))
        repo = data.get("GITHUB_REPO", "")
        return repo or None
    except Exception as e:
        err(f"No se pudo leer env.json: {e}")
        return None


# ─── Lectura de release_info.json ────────────────────────────────────────────

def load_release_info(project_path: Path) -> dict | None:
    json_path = project_path / "release_info.json"
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        required = {"title", "changelog", "description"}
        if not required.issubset(data.keys()):
            warn("release_info.json no tiene todos los campos requeridos (title, changelog, description). Se ignorara.")
            return None
        if not isinstance(data["changelog"], list) or not data["changelog"]:
            warn("release_info.json: 'changelog' debe ser una lista no vacia. Se ignorara.")
            return None
        # target es opcional — default "all"
        if "target" not in data:
            data["target"] = "all"
        if data["target"] not in ("all", "admin", "user"):
            warn(f"release_info.json: target '{data['target']}' no es valido. Usando 'all'.")
            data["target"] = "all"
        # changelogs por rol opcionales — deben ser listas si estan presentes
        for role_key in ("changelog_user", "changelog_admin"):
            if role_key in data and not isinstance(data[role_key], list):
                warn(f"release_info.json: '{role_key}' debe ser una lista. Se ignorara.")
                del data[role_key]
        return data
    except Exception as e:
        warn(f"No se pudo leer release_info.json: {e}")
        return None


# ─── Busqueda del APK ────────────────────────────────────────────────────────

def find_apk(project_path: Path) -> Path | None:
    apk_path = project_path / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
    return apk_path if apk_path.exists() else None


# ─── GitHub API helpers ──────────────────────────────────────────────────────

def github_request(method: str, url: str, token: str, data: dict = None) -> dict | None:
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "SkusAppReleaseScript/1.0")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err(f"GitHub API error {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        err(f"Error de red: {e}")
        return None


def delete_release_and_tag(repo: str, token: str, tag: str):
    releases = github_request("GET", f"https://api.github.com/repos/{repo}/releases", token)
    if releases:
        for release in releases:
            if release.get("tag_name") == tag:
                github_request(
                    "DELETE",
                    f"https://api.github.com/repos/{repo}/releases/{release['id']}",
                    token,
                )
                break
    github_request("DELETE", f"https://api.github.com/repos/{repo}/git/refs/tags/{tag}", token)


def _draw_progress(sent: int, total: int, bar_width: int = 38):
    pct      = sent / total if total else 0
    filled   = int(bar_width * pct)
    bar      = "#" * filled + "-" * (bar_width - filled)
    sent_mb  = sent  / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    print(
        f"\r  [>]  [{bar}] {pct*100:5.1f}%  "
        f"{sent_mb:.1f}/{total_mb:.1f} MB",
        end="",
        flush=True,
    )


def upload_asset(upload_url: str, token: str, apk_path: Path) -> bool:
    """
    Sube el APK a GitHub en chunks de 256 KB con barra de progreso.
    Usa http.client directamente para control total del socket.
    """
    CHUNK_SIZE = 256 * 1024

    clean_url = upload_url.split("{")[0]
    parsed    = urllib.parse.urlparse(clean_url)
    host      = parsed.netloc
    path      = f"{parsed.path}?name={urllib.parse.quote(apk_path.name)}"

    apk_bytes = apk_path.read_bytes()
    total     = len(apk_bytes)

    headers = {
        "Authorization":        f"Bearer {token}",
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent":           "SkusAppReleaseScript/1.0",
        "Content-Type":         "application/vnd.android.package-archive",
        "Content-Length":       str(total),
    }

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(None)

    try:
        conn = http.client.HTTPSConnection(host)
        conn.connect()
        conn.putrequest("POST", path)
        for key, value in headers.items():
            conn.putheader(key, value)
        conn.endheaders()

        sent = 0
        _draw_progress(0, total)

        while sent < total:
            chunk = apk_bytes[sent: sent + CHUNK_SIZE]
            conn.send(chunk)
            sent += len(chunk)
            _draw_progress(sent, total)

        print()

        response = conn.getresponse()
        body     = response.read().decode("utf-8")

        if response.status not in (200, 201):
            err(f"GitHub respondio {response.status}: {body}")
            return False

        result = json.loads(body)
        return result.get("state") == "uploaded"

    except Exception as e:
        print()
        err(f"Error de red al subir APK: {e}")
        return False
    finally:
        socket.setdefaulttimeout(old_timeout)
        try:
            conn.close()
        except Exception:
            pass


def check_tag_exists(repo: str, token: str, tag: str) -> bool:
    url = f"https://api.github.com/repos/{repo}/git/refs/tags/{tag}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "SkusAppReleaseScript/1.0")
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception:
        return False


# ─── Construccion del body del release ───────────────────────────────────────

def build_release_body(
    changelog_items: list,
    description: str,
    target: str,
    changelog_user: list = None,
    changelog_admin: list = None,
) -> str:
    """
    El changelog visible en GitHub se escribe en Markdown normal.
    Los bloques entre marcadores HTML son extraidos por la app (ver
    lib/features/updates/domain/extract_changelog.dart y extract_target.dart)
    para mostrar el banner/dialogo de actualizacion — invisibles en la UI de
    GitHub.

    APP_TARGET indica a que rol va dirigida la actualizacion:
      all   = todos los usuarios
      admin = solo administradores
      user  = solo usuarios regulares

    changelog_user/changelog_admin generan bloques APP_CHANGELOG_USER /
    APP_CHANGELOG_ADMIN que las apps >= 1.3.0 muestran segun el rol del
    usuario; las versiones anteriores solo leen el bloque generico.
    """
    lines = []

    lines.append("## Cambios en esta version")
    lines.append("")
    for item in changelog_items:
        lines.append(f"- {item.strip()}")

    if description.strip():
        lines.append("")
        lines.append("## Descripcion")
        lines.append("")
        lines.append(description.strip())

    lines.append("")
    # Marcador de target — extraido por la app
    lines.append(f"<!-- APP_TARGET: {target} -->")
    lines.append("")
    # Marcador de changelog — extraido por la app
    lines.append("<!-- APP_CHANGELOG_START -->")
    for item in changelog_items:
        lines.append(f"- {item.strip()}")
    lines.append("<!-- APP_CHANGELOG_END -->")

    for role, items in (("USER", changelog_user), ("ADMIN", changelog_admin)):
        if not items:
            continue
        lines.append("")
        lines.append(f"<!-- APP_CHANGELOG_{role}_START -->")
        for item in items:
            lines.append(f"- {item.strip()}")
        lines.append(f"<!-- APP_CHANGELOG_{role}_END -->")

    return "\n".join(lines)


# ─── Input helpers ───────────────────────────────────────────────────────────

def ask(prompt: str, required: bool = True) -> str:
    while True:
        value = input(f"  {CYAN}?{RESET}  {prompt}: ").strip()
        if value or not required:
            return value
        warn("Este campo es obligatorio.")


def ask_target() -> str:
    """Pregunta interactivamente a quien va dirigida la actualizacion."""
    print(f"\n  {GREY}Dirigido a:{RESET}")
    print(f"    1. Todos los usuarios {GREY}(all){RESET}")
    print(f"    2. Solo administradores {GREY}(admin){RESET}")
    print(f"    3. Solo usuarios regulares {GREY}(user){RESET}")
    while True:
        value = input(f"  {CYAN}?{RESET}  Selecciona [1/2/3] (default 1): ").strip()
        if value == "" or value == "1":
            return "all"
        if value == "2":
            return "admin"
        if value == "3":
            return "user"
        warn("Opcion invalida. Ingresa 1, 2 o 3.")


def confirm(prompt: str) -> bool:
    value = input(f"  {CYAN}?{RESET}  {prompt} {GREY}[s/n]{RESET}: ").strip().lower()
    return value in ("s", "si", "y", "yes")


# ─── Labels de target ────────────────────────────────────────────────────────

TARGET_LABELS = {
    "all":   "Todos",
    "admin": "Solo admins",
    "user":  "Solo usuarios",
}


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{'=' * 50}{RESET}")
    print(f"{BOLD}  SKUs App — Release Publisher{RESET}")
    print(f"{BOLD}{'=' * 50}{RESET}")

    project_path = Path.cwd()

    # ── Paso 1: Credenciales ─────────────────────────────────────────────────
    step("Paso 1 — Credenciales")

    env_path = project_path / ".env"
    if not env_path.exists():
        err("No se encontro .env en la raiz del proyecto.")
        err('Crea un archivo .env con: GITHUB_TOKEN=tu_token')
        err("(Nunca pongas el token en env.json — ese archivo se embebe en el APK.)")
        sys.exit(1)

    token = load_env(env_path).get("GITHUB_TOKEN", "")
    if not token:
        err("GITHUB_TOKEN no encontrado en .env")
        sys.exit(1)

    env_json_path = project_path / "env.json"
    if not env_json_path.exists():
        err("No se encontro env.json en la raiz del proyecto.")
        sys.exit(1)

    repo = load_github_repo(env_json_path)
    if not repo:
        err("GITHUB_REPO no encontrado en env.json")
        sys.exit(1)

    ok(f"Repositorio : {repo}")
    ok(f"Token       : {'*' * (len(token) - 4)}{token[-4:]}")

    # ── Paso 2: Version ──────────────────────────────────────────────────────
    step("Paso 2 — Version")

    pubspec_path = project_path / "pubspec.yaml"
    if not pubspec_path.exists():
        err("No se encontro pubspec.yaml en la raiz del proyecto.")
        sys.exit(1)

    version = extract_app_version(pubspec_path)
    if not version:
        err("No se encontro una version valida en pubspec.yaml")
        err('Asegurate de que tenga una linea como: version: 1.2.3+4')
        sys.exit(1)

    tag = f"v{version}"
    ok(f"Version detectada: {version}  ->  tag: {tag}")

    if check_tag_exists(repo, token, tag):
        warn(f"El tag '{tag}' ya existe en GitHub.")
        if not confirm("Deseas sobreescribir el release existente?"):
            info("Operacion cancelada.")
            sys.exit(0)
        delete_release_and_tag(repo, token, tag)
        ok(f"Release y tag '{tag}' eliminados. Se creara uno nuevo.")

    # ── Paso 3: APK ──────────────────────────────────────────────────────────
    step("Paso 3 — APK")

    apk_path = find_apk(project_path)
    if not apk_path:
        err("No se encontro build/app/outputs/flutter-apk/app-release.apk")
        err("Ejecuta primero: flutter build apk --release --dart-define-from-file=env.json")
        sys.exit(1)

    apk_size_mb = apk_path.stat().st_size / (1024 * 1024)
    ok(f"APK encontrado : {apk_path.name}  ({apk_size_mb:.1f} MB)")

    # ── Paso 4: Informacion del release ─────────────────────────────────────
    step("Paso 4 — Informacion del release")

    release_info = load_release_info(project_path)

    if release_info:
        ok("release_info.json detectado — datos cargados automaticamente.")
        title           = release_info["title"]
        changelog_items = release_info["changelog"]
        description     = release_info.get("description", "")
        target          = release_info.get("target", "all")
        changelog_user  = release_info.get("changelog_user")
        changelog_admin = release_info.get("changelog_admin")
    else:
        info("No se encontro release_info.json — ingresa los datos manualmente.")
        print(f"\n  {GREY}Para marcar como critico incluye [CRITICAL] en el titulo.{RESET}")
        print(f"  {GREY}Ejemplo: [CRITICAL] Fix de seguridad v{version}{RESET}\n")
        title = ask("Titulo del release")

        print(f"\n  {GREY}Ingresa los cambios separados por comas.{RESET}")
        print(f"  {GREY}Ejemplo: correccion de login, nuevo diseno del perfil{RESET}\n")
        changelog_raw   = ask("Changelog")
        changelog_items = [i.strip() for i in changelog_raw.split(",") if i.strip()]

        print(f"\n  {GREY}Descripcion larga para GitHub (opcional, Enter para omitir).{RESET}\n")
        description = ask("Descripcion", required=False)

        target = ask_target()
        changelog_user  = None
        changelog_admin = None

    is_critical   = "[CRITICAL]" in title.upper()
    target_label  = TARGET_LABELS.get(target, target)

    # ── Paso 5: Confirmacion ─────────────────────────────────────────────────
    step("Paso 5 — Confirmacion")

    print(f"\n  {'=' * 44}")
    print(f"  Repositorio  : {BOLD}{repo}{RESET}")
    print(f"  Tag          : {BOLD}{tag}{RESET}")
    print(f"  Titulo       : {BOLD}{title}{RESET}")
    print(f"  Target       : {BOLD}{target_label}{RESET}")
    print(f"  Changelog    :")
    for item in changelog_items:
        print(f"    {GREEN}*{RESET} {item}")
    if changelog_user:
        print(f"  Changelog (rol user, apps >= 1.3.0):")
        for item in changelog_user:
            print(f"    {GREEN}*{RESET} {item}")
    if changelog_admin:
        print(f"  Changelog (rol admin, apps >= 1.3.0):")
        for item in changelog_admin:
            print(f"    {GREEN}*{RESET} {item}")
    if description:
        print(f"  Descripcion  : {description[:60]}{'...' if len(description) > 60 else ''}")
    print(f"  APK          : {apk_path.name} ({apk_size_mb:.1f} MB)")
    print(f"  Tipo         : {RED + 'CRITICO' if is_critical else GREEN + 'Normal'}{RESET}")
    print(f"  {'=' * 44}\n")

    if not confirm("Publicar este release?"):
        info("Operacion cancelada.")
        sys.exit(0)

    # ── Paso 6: Crear release en GitHub ─────────────────────────────────────
    step("Paso 6 — Publicando")

    release_body = build_release_body(
        changelog_items,
        description,
        target,
        changelog_user=changelog_user,
        changelog_admin=changelog_admin,
    )

    info("Creando release en GitHub...")
    release_data = github_request(
        "POST",
        f"https://api.github.com/repos/{repo}/releases",
        token,
        {
            "tag_name":         tag,
            "target_commitish": "main",
            "name":             title,
            "body":             release_body,
            "draft":            False,
            "prerelease":       False,
        },
    )

    if not release_data:
        err("No se pudo crear el release. Revisa el token y el repositorio.")
        sys.exit(1)

    ok(f"Release creado: {release_data.get('html_url', '')}")

    # ── Paso 7: Subir el APK ─────────────────────────────────────────────────
    upload_url = release_data.get("upload_url", "")
    if not upload_url:
        err("No se obtuvo upload_url. El APK no fue subido.")
        sys.exit(1)

    info(f"Subiendo {apk_path.name} ({apk_size_mb:.1f} MB)")
    uploaded = upload_asset(upload_url, token, apk_path)

    if not uploaded:
        err("El APK no pudo subirse.")
        warn("Eliminando el release huerfano para que puedas reintentar limpiamente...")
        delete_release_and_tag(repo, token, tag)
        ok(f"Release '{tag}' eliminado. Corrige el problema y vuelve a ejecutar release.py.")
        sys.exit(1)

    # ── Finalizacion ─────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'=' * 50}{RESET}")
    ok(f"Release {tag} publicado correctamente.")
    ok(f"Dirigido a : {target_label}")
    ok(f"URL        : {release_data.get('html_url', '')}")
    print(f"{BOLD}{'=' * 50}{RESET}\n")


if __name__ == "__main__":
    main()
