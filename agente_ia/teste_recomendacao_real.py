
import json
from pathlib import Path

from nextrip_arquitetura.servicos import RecomendacaoIA

# Localiza a raiz do projeto NexTrip
BASE = Path(__file__).resolve().parents[1]

# Utiliza os arquivos originais das PoCs
catalogo = BASE / "dados" / "catalogo_teste.json"
perfil = BASE / "dados" / "perfil_usuario.json"

# Instancia o recomendador desenvolvido pelo grupo
recomendador = RecomendacaoIA()

# Calcula o ranking utilizando a similaridade de cosseno
resultado = recomendador.gerar_ranking(
    catalogo_arquivo=catalogo,
    perfil_arquivo=perfil,
    metrica="cosseno",
)

print("RECOMENDACOES DO NEXTRIP")
print("Atracoes avaliadas:", len(resultado["ranking"]))

# Exibe as cinco atracoes mais compativeis
print(
    json.dumps(
        resultado["ranking"][:5],
        ensure_ascii=False,
        indent=2,
    )
)
