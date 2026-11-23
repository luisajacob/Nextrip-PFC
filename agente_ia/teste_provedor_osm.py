
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

from nextrip_base import carregar_pontos
from agente_ia.provedor_osm import ProvedorHorariosOSM


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

provedor = ProvedorHorariosOSM(pontos)

# Testar primeiro usando horarios do catalogo original
cafe = next(
    p for p in pontos
    if p["nome"] == "Cafeteria São Bento"
)

fuso = ZoneInfo("America/Sao_Paulo")

chegada = datetime(2026, 11, 24, 10, 0, tzinfo=fuso)
saida = chegada + timedelta(minutes=35)

resultado = provedor(cafe, chegada, saida)

print("\n=== HORARIO CADASTRADO ===")
print("Atracao:", cafe["nome"])
print("Status:", resultado["status"])
print("Fonte:", resultado["fonte"])

assert resultado["status"] == "aberto"

# Testar uma visita que ultrapassa o fechamento
chegada_tarde = datetime(
    2026, 11, 24, 18, 15, tzinfo=fuso
)
saida_tarde = chegada_tarde + timedelta(minutes=35)

tarde = provedor(cafe, chegada_tarde, saida_tarde)

assert tarde["status"] == "fechado"

print("Visita fora do horario bloqueada: OK")

# POI sem opening_hours nao pode ser considerado aberto
sem_horario = next(
    p for p in pontos
    if p["nome"] == "Abertura"
)

desconhecido = provedor(
    sem_horario, chegada, saida
)

assert desconhecido["status"] == "desconhecido"

print("Horario ausente tratado: OK")

# Consulta externa opcional
if "--online" in sys.argv:
    print("\n=== CONSULTA OVERPASS ===")

    sucesso = provedor.atualizar_pela_api()
    print("Consulta realizada:", sucesso)


    if not sucesso:
        print(
            "Motivo da falha:",
            getattr(
                provedor,
                "ultimo_erro",
                "Erro nao identificado",
            ),
        )
        print("CONSULTA ONLINE: NAO VALIDADA")
    else:
        print("CONSULTA ONLINE: REALIZADA")


    for ponto in pontos[1:6]:
        consulta = provedor(
            ponto, chegada, saida
        )
        print(
            ponto["nome"],
            "|", consulta["status"],
            "|", consulta["fonte"],
        )

print("\nTESTE DO PROVEDOR OSM: OK")
