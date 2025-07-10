import importlib
import sys
import types
from pathlib import Path

# Garante que o pacote da aplicação seja encontrado
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def reload_module():
    """Recarrega módulo de empregados considerando mocks atuais."""
    if "app.processing.employees" in sys.modules:
        del sys.modules["app.processing.employees"]
    return importlib.import_module("app.processing.employees")


# Testa resolução usando dados internos de mock
def test_resolve_with_mock():
    """Verifica resolução usando dados internos."""
    sys.modules.pop("buscaempregados", None)
    employees = reload_module()
    resolver = employees.EmployeeResolver()
    data = resolver.resolve("CSLA")
    assert data["nome"] == "CARLOS SANTANA LIMA ALMEIDA"
    assert data["email"] == "carlos.almeida@petrobras.com.br"
    unknown = resolver.resolve("XXXX")
    assert unknown["nome"] == "DESCONHECIDO"
    assert unknown["chave"] == "XXXX"


# Testa integração com módulo externo de busca
def test_resolve_with_external_module(monkeypatch):
    """Testa resolução chamando módulo externo simulado."""
    module = types.ModuleType("buscaempregados")

    def fake_busca_empregado(chave):
        return {"nome": f"NOME {chave}", "email": "x@y", "lotacao": "L", "cargo": "C"}

    module.busca_empregado = fake_busca_empregado
    sys.modules["buscaempregados"] = module

    employees = reload_module()
    resolver = employees.EmployeeResolver()
    data = resolver.resolve("ABCD")
    assert data == {
        "chave": "ABCD",
        "nome": "NOME ABCD",
        "email": "x@y",
        "lotacao": "L",
        "cargo": "C",
    }

    sys.modules.pop("buscaempregados", None)
