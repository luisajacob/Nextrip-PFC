
"""Validacao de chamadas de ferramentas do NexTrip."""

from agente_ia.controlador import AgenteNexTrip


# Acoes existentes no controlador e seus parametros
PARAMETROS_OBRIGATORIOS = {
    "gerar_roteiro": {
        "limite_minutos": int,
        "paradas": int,
    },
    "concluir_visita": {
        "poi_id": str,
        "minutos_gastos": int,
    },
    "bloquear_atracao": {
        "poi_id": str,
    },
    "replanejar_roteiro": {
        "paradas": int,
    },
}

# Acoes que exigem confirmacao do usuario
ACOES_COM_CONFIRMACAO = {
    "concluir_visita",
    "bloquear_atracao",
    "replanejar_roteiro",
}


def validar_chamada(chamada):
    """Valida uma chamada proposta por uma LLM."""

    if not isinstance(chamada, dict):
        raise ValueError("A chamada deve ser um objeto.")

    if set(chamada) != {"name", "arguments"}:
        raise ValueError("Estrutura da chamada invalida.")

    nome = chamada["name"]
    argumentos = chamada["arguments"]

    if not isinstance(nome, str):
        raise ValueError("Nome da ferramenta invalido.")

    if nome not in PARAMETROS_OBRIGATORIOS:
        raise ValueError("Ferramenta nao autorizada.")

    if not isinstance(argumentos, dict):
        raise ValueError("Argumentos devem ser um objeto.")

    esperados = PARAMETROS_OBRIGATORIOS[nome]

    if set(argumentos) != set(esperados):
        raise ValueError(
            "Parametros ausentes ou desconhecidos."
        )

    for campo, tipo in esperados.items():
        valor = argumentos[campo]

        if type(valor) is not tipo:
            raise ValueError(
                f"Tipo invalido para {campo}."
            )

        if tipo is str and not valor.strip():
            raise ValueError(
                f"{campo} nao pode ser vazio."
            )

        if tipo is int:
            minimo = (
                0 if campo == "minutos_gastos" else 1
            )

            if valor < minimo:
                raise ValueError(
                    f"Valor invalido para {campo}."
                )

    return nome, argumentos


def executar_chamada(
    agente: AgenteNexTrip,
    chamada: dict,
    confirmado_pelo_usuario: bool = False,
):
    """Executa uma ferramenta apos validacao."""

    if not isinstance(agente, AgenteNexTrip):
        raise TypeError("Agente NexTrip invalido.")

    nome, argumentos = validar_chamada(chamada)

    # Confirmacao deve vir da aplicacao, nunca da LLM
    if (
        nome in ACOES_COM_CONFIRMACAO
        and not confirmado_pelo_usuario
    ):
        return {
            "status": "confirmacao_pendente",
            "acao": nome,
            "parametros": dict(argumentos),
        }

    return agente.executar(nome, **argumentos)
