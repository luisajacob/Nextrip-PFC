
from pathlib import Path

from agente_ia.recomendacao import RepositorioPerfilEmMemoria
from nextrip_arquitetura.servicos import (
    RecomendacaoIA,
    RoteiroService,
)
from nextrip_base import carregar_pontos


# 1. Dados originais da POC
BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

# 2. Preferencias do viajante
preferencias = {
    "cultura": 1.0,
    "historia": 1.0,
    "gastronomia": 0.2,
    "natureza": 0.0,
    "compras": 0.0,
    "vida_noturna": 0.0,
}

perfil = {
    "nome": "Viajante de teste",
    "vetor": preferencias,
}

# 3. Recupera os pontos de interesse do catalogo
_, pontos = carregar_pontos(CATALOGO)

# 4. Matriz SIMULADA de tempos de deslocamento
# Mesma regra utilizada nos testes originais das POCs.
n = len(pontos)

matriz = [
    [
        0 if i == j else 8 + abs(i - j) * 3
        for j in range(n)
    ]
    for i in range(n)
]

# 5. Conecta o perfil dinamico ao recomendador real
repositorio = RepositorioPerfilEmMemoria(perfil)

recomendador = RecomendacaoIA(
    repositorio=repositorio
)

# 6. Cria o servico de roteirizacao existente
servico = RoteiroService(
    recomendacao=recomendador
)

# 7. Executa a POC 3 com OR-Tools
resultado = servico.gerar_roteiro_otimizado(
    pontos=pontos,
    matriz=matriz,
    catalogo_arquivo=CATALOGO,
    perfil_arquivo=None,
    paradas=3,
    limite=360,
    pesos=(0.8,),
    referencia=240,
    segundos=2,
)

# 8. Analisa o resultado
cenario = resultado["resultados"][0]

assert cenario["restricoes_validadas"]
assert cenario["total_min"] <= 360
assert len(cenario["atracoes"]) == 3

print("\n=== ROTEIRO OTIMIZADO NEXTRIP ===")
print("Sequencia:")

for local in cenario["sequencia"]:
    print(" ->", local)

print("\nAtracoes selecionadas:")

for atracao in cenario["atracoes"]:
    print(
        f"{atracao['nome']} | "
        f"Afinidade: {atracao['afinidade']:.4f}"
    )

print("\nTempo de visitas:", cenario["visitas_min"])
print("Tempo de deslocamento:", cenario["deslocamento_min"])
print("Tempo total:", cenario["total_min"])
print("Limite de tempo: 360 minutos")
print("Restricoes validadas:", cenario["restricoes_validadas"])

