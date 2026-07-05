"""
Utilitários para extrair informações da requisição HTTP.
"""
from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Obtém o IP real do cliente, considerando cabeçalhos de proxy
    (útil quando a API roda atrás de um load balancer como no Render/Railway).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "0.0.0.0"
