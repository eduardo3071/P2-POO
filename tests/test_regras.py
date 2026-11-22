from datetime import datetime, timedelta

import pytest

from app.controllers.chamado_controller import ChamadoController
from app.controllers.pessoa_controller import PessoaController
from app.data.repositorio import Repositorio, RepositorioJson
from app.models.chamado import Chamado, Hardware, Rede, Software
from app.models.excecoes import (
    ConflitoErro,
    DadoInvalidoErro,
    ErroNegocio,
    NaoEncontradoErro,
)
from app.models.pessoas import Solicitante, Tecnico


@pytest.fixture
def solicitante():
    return Solicitante("Ana Souza", "ana@fatec.sp.gov.br", id=1)


@pytest.fixture
def ctrl(tmp_path):
    repos = {
        "repo_chamados": RepositorioJson(tmp_path / "chamados.json"),
        "repo_solicitantes": RepositorioJson(tmp_path / "solicitantes.json"),
        "repo_tecnicos": RepositorioJson(tmp_path / "tecnicos.json"),
    }
    pessoas = PessoaController(repos["repo_solicitantes"], repos["repo_tecnicos"])
    pessoas.criar_solicitante("Ana Souza", "ana@fatec.sp.gov.br")
    pessoas.criar_tecnico("Carlos Lima")
    return ChamadoController(**repos)


# ---- Requisito 1: classe abstrata ----
def test_chamado_abstrato_nao_instancia(solicitante):
    with pytest.raises(TypeError):
        Chamado("Titulo", "Descricao", solicitante)


def test_repositorio_abstrato_nao_instancia():
    with pytest.raises(TypeError):
        Repositorio()


# ---- Requisitos 2 e 3: herança e polimorfismo ----
@pytest.mark.parametrize("classe,horas", [(Hardware, 48), (Software, 24), (Rede, 8)])
def test_prazo_sla_por_tipo(classe, horas, solicitante):
    chamado = classe("Titulo", "Descricao", solicitante)
    assert isinstance(chamado, Chamado)
    assert chamado.prazo_sla() == horas


def test_polimorfismo_mesmo_metodo_para_todas_as_filhas(solicitante):
    chamados = [c("Titulo", "Descricao", solicitante) for c in (Hardware, Software, Rede)]
    assert [c.prazo_sla() for c in chamados] == [48, 24, 8]


# ---- Requisito 4: encapsulamento e validação ----
def test_titulo_curto_e_rejeitado(solicitante):
    with pytest.raises(DadoInvalidoErro):
        Rede("ab", "Descricao", solicitante)


def test_descricao_vazia_e_rejeitada(solicitante):
    chamado = Rede("Titulo", "Descricao", solicitante)
    with pytest.raises(DadoInvalidoErro):
        chamado.descricao = "   "


def test_email_invalido_e_rejeitado():
    with pytest.raises(DadoInvalidoErro):
        Solicitante("Ana", "sem-arroba")


# ---- Regra: não fecha sem solução escrita ----
def test_nao_fecha_sem_solucao(solicitante):
    chamado = Software("Titulo", "Descricao", solicitante)
    with pytest.raises(DadoInvalidoErro):
        chamado.fechar("   ")
    assert chamado.status == Chamado.ABERTO


def test_fecha_com_solucao(solicitante):
    chamado = Software("Titulo", "Descricao", solicitante)
    chamado.fechar("Reinstalado")
    assert chamado.status == Chamado.FECHADO
    assert chamado.fechado_em is not None


def test_nao_fecha_duas_vezes(solicitante):
    chamado = Software("Titulo", "Descricao", solicitante)
    chamado.fechar("Reinstalado")
    with pytest.raises(ConflitoErro):
        chamado.fechar("Outra vez")


# ---- Regra: técnico com no máximo 5 chamados abertos ----
def test_tecnico_no_limite_nao_recebe_mais(solicitante):
    tecnico = Tecnico("Carlos", id=1)
    chamado = Rede("Titulo", "Descricao", solicitante)
    with pytest.raises(ConflitoErro):
        chamado.atribuir(tecnico, abertos_do_tecnico=Tecnico.MAX_ABERTOS)


def test_tecnico_abaixo_do_limite_recebe(solicitante):
    tecnico = Tecnico("Carlos", id=1)
    chamado = Rede("Titulo", "Descricao", solicitante)
    chamado.atribuir(tecnico, abertos_do_tecnico=Tecnico.MAX_ABERTOS - 1)
    assert chamado.tecnico is tecnico
    assert chamado.status == Chamado.EM_ANDAMENTO


def test_controller_bloqueia_sexto_chamado_do_tecnico(ctrl):
    for i in range(5):
        ctrl.criar("rede", f"Chamado {i}", "Descricao", solicitante_id=1, tecnico_id=1)
    with pytest.raises(ConflitoErro):
        ctrl.criar("rede", "Chamado 6", "Descricao", solicitante_id=1, tecnico_id=1)


def test_fechar_libera_vaga_do_tecnico(ctrl):
    criados = [
        ctrl.criar("rede", f"Chamado {i}", "Descricao", solicitante_id=1, tecnico_id=1)
        for i in range(5)
    ]
    ctrl.fechar(criados[0].id, "Resolvido")
    ctrl.criar("rede", "Chamado novo", "Descricao", solicitante_id=1, tecnico_id=1)


# ---- Composição ----
def test_chamado_guarda_solicitante_e_tecnico(ctrl):
    criado = ctrl.criar("hardware", "Monitor", "Sem imagem", solicitante_id=1, tecnico_id=1)
    recarregado = ctrl.buscar(criado.id)
    assert recarregado.solicitante.nome == "Ana Souza"
    assert recarregado.tecnico.nome == "Carlos Lima"


# ---- Cálculo: fora do prazo ----
def test_fora_do_prazo(solicitante):
    chamado = Rede("Titulo", "Descricao", solicitante)  # SLA 8h
    assert not chamado.fora_do_prazo(chamado.aberto_em + timedelta(hours=7))
    assert chamado.fora_do_prazo(chamado.aberto_em + timedelta(hours=9))


def test_rota_de_calculo_lista_so_os_vencidos(ctrl):
    rede = ctrl.criar("rede", "Wi-Fi", "Caiu", solicitante_id=1)
    hardware = ctrl.criar("hardware", "Teclado", "Falha", solicitante_id=1)
    daqui_12h = datetime.now() + timedelta(hours=12)
    vencidos = ctrl.fora_do_prazo(daqui_12h)
    assert [c.id for c in vencidos] == [rede.id]
    assert hardware.id not in [c.id for c in vencidos]


# ---- Erros 404 / 409 / 422 ----
def test_hierarquia_de_excecoes():
    for erro in (NaoEncontradoErro, ConflitoErro, DadoInvalidoErro):
        assert issubclass(erro, ErroNegocio)


def test_buscar_inexistente_gera_nao_encontrado(ctrl):
    with pytest.raises(NaoEncontradoErro):
        ctrl.buscar(999)


def test_criar_com_solicitante_inexistente(ctrl):
    with pytest.raises(NaoEncontradoErro):
        ctrl.criar("rede", "Titulo", "Descricao", solicitante_id=99)


def test_tipo_invalido_gera_dado_invalido(ctrl):
    with pytest.raises(DadoInvalidoErro):
        ctrl.criar("impressora", "Titulo", "Descricao", solicitante_id=1)
    with pytest.raises(DadoInvalidoErro):
        ctrl.listar(tipo="impressora")


def test_chamado_fechado_nao_pode_ser_alterado(ctrl):
    criado = ctrl.criar("software", "Office", "Nao abre", solicitante_id=1)
    ctrl.fechar(criado.id, "Reinstalado")
    with pytest.raises(ConflitoErro):
        ctrl.alterar(criado.id, titulo="Novo titulo")


def test_email_duplicado_gera_conflito(tmp_path):
    pessoas = PessoaController(
        RepositorioJson(tmp_path / "s.json"), RepositorioJson(tmp_path / "t.json")
    )
    pessoas.criar_solicitante("Ana", "ana@x.com")
    with pytest.raises(ConflitoErro):
        pessoas.criar_solicitante("Outra Ana", "ANA@x.com")


def test_filtro_por_tipo(ctrl):
    ctrl.criar("rede", "Wi-Fi", "Caiu", solicitante_id=1)
    ctrl.criar("software", "Office", "Nao abre", solicitante_id=1)
    assert [c.TIPO for c in ctrl.listar(tipo="rede")] == ["rede"]
    assert len(ctrl.listar()) == 2


def test_remover(ctrl):
    criado = ctrl.criar("rede", "Wi-Fi", "Caiu", solicitante_id=1)
    ctrl.remover(criado.id)
    with pytest.raises(NaoEncontradoErro):
        ctrl.remover(criado.id)


# ---- Requisito 7: persistência em arquivo ----
def test_dados_continuam_depois_de_reiniciar(tmp_path):
    caminho = tmp_path / "chamados.json"
    RepositorioJson(caminho).salvar({"nome": "persistido"})
    reaberto = RepositorioJson(caminho)  # simula reiniciar o servidor
    assert reaberto.listar() == [{"nome": "persistido", "id": 1}]
