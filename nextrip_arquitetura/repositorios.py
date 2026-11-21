from __future__ import annotations
import json
from pathlib import Path
from .modelos import PontoDeInteresse, Preferencias


class RepositorioJSON:
    def carregar(self, caminho):
        with Path(caminho).open('r', encoding='utf-8-sig') as arquivo:
            return json.load(arquivo)

    def salvar(self, caminho, dados):
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with caminho.open('w', encoding='utf-8') as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    def carregar_catalogo(self, caminho):
        dados = self.carregar(caminho)
        if not isinstance(dados.get('atracoes', dados.get('locais')), list):
            raise ValueError('Catálogo JSON sem lista de atrações.')
        return dados

    def listar_pontos_de_interesse(self, caminho):
        dados = self.carregar_catalogo(caminho)
        return [PontoDeInteresse.de_json(p) for p in dados.get('atracoes', dados.get('locais', []))]

    def carregar_preferencias(self, caminho):
        dados = self.carregar(caminho)
        return Preferencias(perfil_embedding=dict(dados['vetor']))
