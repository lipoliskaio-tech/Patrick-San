"""
Geração de chaves de licença únicas e legíveis, no formato:
XXXXX-XXXXX-XXXXX-XXXXX
"""
import secrets
import string

_ALPHABET = string.ascii_uppercase + string.digits
_BLOCK_SIZE = 5
_NUM_BLOCKS = 4


def generate_license_key() -> str:
    blocks = []
    for _ in range(_NUM_BLOCKS):
        block = "".join(secrets.choice(_ALPHABET) for _ in range(_BLOCK_SIZE))
        blocks.append(block)
    return "-".join(blocks)


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)
