import json
import random

import pytest

from app.models.client_service import ClientModel
from app.models.country import CountryModel
from app.repository.client_repository import ClientRepository
from app.repository.country_repository import CountryRepository
from run import create_app


def record(client_id=58372, **changes):
    return dict(id=client_id, name="Maria Silva", email="maria@example.com",
                esim=f"ESIM-{client_id}", pacote=102, status="ativo", **changes)


@pytest.fixture
def service(tmp_path):
    return ClientModel(ClientRepository(tmp_path / "clients.json"))


@pytest.fixture
def countries(tmp_path):
    model = CountryModel(CountryRepository(tmp_path / "countries.json"))
    for code, name, region in [("IT", "Itália", "Europa"), ("PT", "Portugal", "Europa"),
                               ("FR", "França", "Europa"), ("BR", "Brasil", "América")]:
        model.create(code, dict(country=name, region=region, provider="Operadora", tech="5G"))
    return model


def test_thousand_clients_keep_balanced_tree_and_records(service):
    ids = list(range(1, 1001))
    random.Random(42).shuffle(ids)
    records = [record(i) for i in ids]
    service.repository.save_all(records)
    service = ClientModel(service.repository)
    assert [client.id for client in service.list_all()] == list(range(1, 1001))
    depths = set()

    def check(node, depth=0, low=0, high=1001):
        assert node.keys == sorted(node.keys)
        assert 1 <= len(node.keys) <= 3
        assert all(low < key < high for key in node.keys)
        assert len(node.values) == len(node.keys)
        for key, value in zip(node.keys, node.values):
            assert type(value) is int
            assert records[value]["id"] == key
        if node.is_leaf:
            depths.add(depth)
        else:
            assert len(node.lower_nodes) == len(node.keys) + 1
            bounds = [low, *node.keys, high]
            for i, child in enumerate(node.lower_nodes):
                check(child, depth + 1, bounds[i], bounds[i + 1])
    check(service.tree.root)
    assert len(depths) == 1
    for i in range(1, 1001):
        assert service.get_by_id(i).esim == f"ESIM-{i}"
    assert service.tree.get_metrics()["height"] > 0
    # Atualiza também uma chave promovida para um nó interno.
    promoted = service.tree.root.keys[0]
    service.update(promoted, {"name": "Cliente alterado", "pacote": 301})
    reloaded = ClientModel(service.repository)
    assert reloaded.get_by_id(promoted).name == "Cliente alterado"
    assert reloaded.get_by_id(promoted).pacote == 301
    assert len(reloaded.list_all()) == 1000


def test_create_validation_duplicates_and_immutable_id(service):
    service.create(record())
    before = service.repository.filepath.read_bytes()
    for invalid in [record(), {**record(4), "id": "1.5"}, {**record(4), "email": "inválido"},
                    {**record(4), "pacote": 999}, {**record(4), "esim": " "},
                    {**record(4), "status": "qualquer"}]:
        with pytest.raises(ValueError):
            service.create(invalid)
    with pytest.raises(ValueError):
        service.update(58372, {"id": 5})
    with pytest.raises(KeyError):
        service.update(999, {"name": "Ausente"})
    assert service.repository.filepath.read_bytes() == before
    assert service.get_by_id(999) is None


def test_persistence_failure_does_not_change_tree(service, monkeypatch):
    service.create(record())
    def fail(_):
        raise OSError("Arquivo indisponível")
    monkeypatch.setattr(service.repository, "save_all", fail)
    with pytest.raises(OSError):
        service.update(58372, {"name": "Não salvar"})
    with pytest.raises(OSError):
        service.create(record(10))
    assert service.get_by_id(58372).name == "Maria Silva"
    assert service.get_by_id(10) is None


def test_integrated_search_and_recommendation(service, countries, monkeypatch):
    service.create(record())
    # A busca usa a Árvore B para obter a posição e só então lê o registro.
    reads = []
    original = service.repository.get_at
    def read_position(position):
        reads.append(position)
        return original(position)
    monkeypatch.setattr(service.repository, "get_at", read_position)
    result = service.consult_destination("58372", "it", countries)
    assert result["client"].name == "Maria Silva"
    assert reads == [0]
    reads.clear()
    assert service.get_by_id(999) is None
    assert reads == []
    assert result["country"]["country"] == "Itália"
    assert result["package"]["code"] == 102
    assert result["tree_comparisons"] > 0
    assert result["hash_comparisons"] > 0
    assert service.consult_destination(58372, "XX", countries)["country"] is None
    with pytest.raises(KeyError):
        service.consult_destination(1, "IT", countries)
    service.assign_recommended_package(58372, "IT,BR", countries)
    assert service.get_by_id(58372).pacote == 301
    assert ClientModel(ClientRepository(service.repository.filepath)).get_by_id(58372).pacote == 301
    for itinerary in ["", ",", "XX", "IT,XX"]:
        with pytest.raises(ValueError):
            service.assign_recommended_package(58372, itinerary, countries)
    assert service.get_by_id(58372).pacote == 301


def test_generator_preserves_existing_records(service):
    service.create(record(10001))
    assert service.generate_clients(1000) == 1000
    assert len(service.list_all()) == 1001
    assert service.get_by_id(10001).name == "Maria Silva"
    assert len(ClientModel(service.repository).list_all()) == 1001


def test_invalid_persisted_data_is_not_silently_discarded(tmp_path):
    repo = ClientRepository(tmp_path / "clients.json")
    repo.save_all([record(), record()])
    with pytest.raises(ValueError, match="duplicado"):
        ClientModel(repo)
    repo.filepath.write_text("{inválido", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        ClientModel(repo)


@pytest.fixture
def web(tmp_path, countries):
    app = create_app({"TESTING": True, "CLIENTS_FILE": str(tmp_path / "web-clients.json"),
                      "COUNTRY_SERVICE": countries})
    return app, app.test_client()


def test_client_web_flow(web):
    app, browser = web
    assert browser.get("/clientes/").status_code == 200
    assert browser.post("/clientes/criar", data=record()).status_code == 302
    result = browser.get("/clientes/?id=58372&destino=IT")
    assert result.status_code == 200
    assert "Cobertura disponível: Itália" in result.text
    assert "Europa Plus" in result.text
    assert "5G" in result.text
    assert browser.get("/clientes/?editar=58372").status_code == 200
    assert browser.post("/clientes/58372/atualizar", data={**record(), "name": "Maria Atualizada"}).status_code == 302
    preview = browser.get("/clientes/?id=58372&roteiro=IT,BR")
    assert "Associar a Maria Atualizada" in preview.text
    # Não confia em um pacote enviado pelo formulário: recalcula pelo roteiro.
    assert browser.post("/clientes/recomendar", data={"id": 58372, "roteiro": "IT,BR", "pacote": 101}).status_code == 302
    assert app.extensions["clients"].get_by_id(58372).pacote == 301
    for url in ["/clientes/criar", "/clientes/58372/atualizar", "/clientes/recomendar"]:
        assert browser.get(url).status_code == 405
    for query in ["id=abc", "id=1", "editar=abc", "editar=1", "pagina=abc", "pagina=999"]:
        assert browser.get("/clientes/?" + query).status_code == 200
    assert "Sem cobertura" in browser.get("/clientes/?id=58372&destino=XX").text
    browser.post("/clientes/recomendar", data={"id": 58372, "roteiro": "IT,XX"})
    assert app.extensions["clients"].get_by_id(58372).pacote == 301
    assert browser.get("/").status_code == 200
    assert browser.get("/cobertura").status_code == 200
    assert browser.get("/?codigo=IT").status_code == 302
    assert browser.get("/admin/").status_code == 200


def test_cli_generation_and_pagination(web):
    app, browser = web
    result = app.test_cli_runner().invoke(args=["gerar-clientes", "--quantidade", "1000"])
    assert result.exit_code == 0, result.output
    assert len(app.extensions["clients"].list_all()) == 1000
    assert "Página 1 de 20" in browser.get("/clientes/").text
    assert "Página 20 de 20" in browser.get("/clientes/?pagina=20").text
    assert app.test_cli_runner().invoke(args=["gerar-clientes", "--quantidade", "0"]).exit_code != 0


def test_index_positions_stay_stable_after_create_update_and_reload(service):
    # IDs fora de ordem distinguem posição física de ordem da chave.
    for key in [50, 10, 90, 30, 70]:
        service.create(record(key))
    expected = [(10, 1), (30, 3), (50, 0), (70, 4), (90, 2)]
    assert service.tree.list_items() == expected
    service.update(50, {"name": "Nome mais longo para testar a posição lógica"})
    service.create(record(5))
    service.generate_clients(3)
    assert service.tree.list_items()[1:6] == expected
    reloaded = ClientModel(service.repository)
    assert reloaded.tree.list_items() == service.tree.list_items()
    assert reloaded.get_by_id(50).name == "Nome mais longo para testar a posição lógica"
    assert reloaded.get_by_id(10).esim == "ESIM-10"
    assert reloaded.tree.search(50) == 0


def test_package_compatibility_and_status_colors(web):
    app, browser = web
    browser.post("/clientes/criar", data={**record(6767), "status": "inativo", "pacote": 101})
    browser.post("/clientes/criar", data={**record(6768), "status": "suspenso", "pacote": 301})
    browser.post("/clientes/criar", data={**record(6769), "status": "ativo", "pacote": 301})

    res_inativo_br = browser.get("/clientes/?id=6767&destino=BR")
    assert res_inativo_br.status_code == 200
    assert "result-warning" in res_inativo_br.text
    assert "result-error" in res_inativo_br.text
    assert "não cobre Brasil (América)" in res_inativo_br.text
    assert "status inativo" in res_inativo_br.text

    # Cliente inativo com Europa Basic consultando Itália (Europa) -> pacote cobre, alerta amarelo.
    res_inativo_it = browser.get("/clientes/?id=6767&destino=IT")
    assert "result-error" not in res_inativo_it.text
    assert res_inativo_it.text.count("result-warning") >= 2

    # Cliente suspenso com pacote Global -> card vermelho (result-error).
    res_suspenso = browser.get("/clientes/?id=6768&destino=BR")
    assert "result-error" in res_suspenso.text
    assert "status suspenso" in res_suspenso.text

    # Cliente ativo com pacote Global -> ambos verdes (result-success) e uso liberado.
    res_ativo = browser.get("/clientes/?id=6769&destino=BR")
    assert "USO LIBERADO" in res_ativo.text
    assert "result-warning" not in res_ativo.text
    assert "result-error" not in res_ativo.text

