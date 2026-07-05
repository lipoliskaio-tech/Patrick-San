"""
Geração de um identificador único de hardware (HWID) para o computador
onde o cliente está sendo executado.

A abordagem combina múltiplos identificadores do sistema (quando disponíveis)
e gera um hash SHA-256 estável entre execuções na mesma máquina.
"""
import hashlib
import platform
import subprocess
import uuid


def _get_windows_machine_guid() -> str:
    """Lê o MachineGuid do registro do Windows (identificador estável por instalação)."""
    try:
        import winreg  # type: ignore

        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return value
    except Exception:
        return ""


def _get_windows_disk_serial() -> str:
    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "SerialNumber"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if len(lines) > 1:
            return lines[1]
    except Exception:
        pass
    return ""


def get_hwid() -> str:
    """
    Retorna um HWID estável (hash hexadecimal) para a máquina atual.
    Funciona em Windows (uso principal), com fallback multiplataforma
    baseado em uuid.getnode() para outros sistemas operacionais.
    """
    components = []

    if platform.system() == "Windows":
        machine_guid = _get_windows_machine_guid()
        if machine_guid:
            components.append(machine_guid)
        disk_serial = _get_windows_disk_serial()
        if disk_serial:
            components.append(disk_serial)

    # Fallback multiplataforma: endereço MAC estável (uuid.getnode)
    components.append(str(uuid.getnode()))
    components.append(platform.node())

    raw = "|".join(components)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
