"""
Armazenamento local simples para a opção "Lembrar licença".
Salva a chave de forma ofuscada (não é criptografia forte, apenas evita
que a chave fique 100% em texto plano no arquivo).
"""
import base64
import json
import os

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".license_client")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")


def _ensure_dir():
    os.makedirs(_CONFIG_DIR, exist_ok=True)


def save_license(license_key: str, remember: bool):
    _ensure_dir()
    data = {}
    if remember:
        encoded = base64.b64encode(license_key.encode("utf-8")).decode("utf-8")
        data = {"license_key": encoded, "remember": True}
    else:
        data = {"license_key": "", "remember": False}

    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_license() -> str:
    if not os.path.exists(_CONFIG_FILE):
        return ""
    try:
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("remember") and data.get("license_key"):
            return base64.b64decode(data["license_key"]).decode("utf-8")
    except Exception:
        pass
    return ""
