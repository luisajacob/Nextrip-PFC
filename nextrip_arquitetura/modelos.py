from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Preferencias:
    id: str = ''
    orcamento_maximo: float | None = None
    perfil_embedding: dict[str, float] = field(default_factory=dict)

    def atualizar_preferencias(self, vetor: dict[str, float], orcamento_maximo: float | None = None):
        self.perfil_embedding = dict(vetor)
        if orcamento_maximo is not None:
            self.orcamento_maximo = float(orcamento_maximo)


@dataclass
class Usuario:
    id: str
    nome: str
    email: str = ''
    senha_hash: str = ''
    preferencias: Preferencias | None = None

    def login(self):
        raise NotImplementedError('Autenticação não implementada nas POCs.')

    def atualizar_perfil(self, nome: str | None = None, email: str | None = None):
        if nome is not None:
            self.nome = nome
        if email is not None:
            self.email = email


@dataclass
class PontoDeInteresse:
    id: str
    nome: str
    categoria: str
    lat: float
    lon: float
    duracao_minutos: int = 0
    preco_estimado: float | None = None
    descricao_embedding: dict[str, float] = field(default_factory=dict)
    tags_osm: dict[str, str] = field(default_factory=dict)
    dados_adicionais: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def de_json(cls, dados: dict[str, Any]):
        reservados = {'id', 'nome', 'categoria', 'lat', 'lon', 'duracao_min', 'preco_estimado', 'vetor', 'tags_osm'}
        return cls(
            id=str(dados['id']),
            nome=str(dados['nome']),
            categoria=str(dados.get('categoria', 'atracao')),
            lat=float(dados['lat']),
            lon=float(dados['lon']),
            duracao_minutos=int(dados.get('duracao_min', 0)),
            preco_estimado=dados.get('preco_estimado'),
            descricao_embedding=dict(dados.get('vetor', {})),
            tags_osm=dict(dados.get('tags_osm', {})),
            dados_adicionais={k: v for k, v in dados.items() if k not in reservados},
        )

    def para_json(self):
        resultado = dict(self.dados_adicionais)
        resultado.update({
            'id': self.id, 'nome': self.nome, 'categoria': self.categoria,
            'lat': self.lat, 'lon': self.lon,
            'duracao_min': self.duracao_minutos,
            'vetor': dict(self.descricao_embedding),
        })
        if self.tags_osm:
            resultado['tags_osm'] = dict(self.tags_osm)
        if self.preco_estimado is not None:
            resultado['preco_estimado'] = self.preco_estimado
        return resultado

    def calcular_distancia(self, outro: 'PontoDeInteresse') -> float:
        from math import atan2, cos, radians, sin, sqrt
        lat1, lat2 = radians(self.lat), radians(outro.lat)
        delta_lat = lat2 - lat1
        delta_lon = radians(outro.lon - self.lon)
        a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        return 6371000 * 2 * atan2(sqrt(a), sqrt(1 - a))


@dataclass
class VisitaAtividade:
    id: str
    ponto_de_interesse_id: str
    ordem_sequencia: int
    horario_inicio: str | None = None
    horario_fim: str | None = None
    status: str = 'planejada'

    def marcar_como_concluido(self):
        self.status = 'concluida'


@dataclass
class RoteiroDia:
    id: str
    data_referencia: str
    visitas: list[VisitaAtividade] = field(default_factory=list)

    def adicionar_visita(self, visita: VisitaAtividade):
        if any(v.id == visita.id for v in self.visitas):
            raise ValueError('ID de visita duplicado.')
        self.visitas.append(visita)
        self.visitas.sort(key=lambda v: v.ordem_sequencia)

    def remover_visita(self, visita_id: str):
        self.visitas = [v for v in self.visitas if v.id != visita_id]

    def recalcular_tempos(self):
        raise NotImplementedError('Horários individuais não são calculados nas POCs atuais.')


@dataclass
class Roteiro:
    id: str
    usuario_id: str
    data_inicio: str
    data_fim: str
    custo_total_estimado: float | None = None
    dias: list[RoteiroDia] = field(default_factory=list)

    def gerar_resumo_financeiro(self):
        return {'roteiro_id': self.id, 'custo_total_estimado': self.custo_total_estimado,
                'precos_disponiveis': self.custo_total_estimado is not None}
