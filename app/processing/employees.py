from __future__ import annotations

try:
    from buscaempregados import busca_empregado
except ImportError:  # pragma: no cover - library may not be available
    busca_empregado = None


# Resolve dados de empregados, consultando serviço externo ou dados locais
class EmployeeResolver:
    """Resolve employee information either via real service or internal mock."""

    # Dados simulados para uso quando o serviço externo não estiver disponível
    _MOCK_DATA: dict[str, dict[str, str]] = {
        "CSLA": {
            "nome": "CARLOS SANTANA LIMA ALMEIDA",
            "email": "carlos.almeida@petrobras.com.br",
            "lotacao": "TI/DEVOPS",
            "cargo": "ANALISTA DE SISTEMAS PLENO",
        },
        "EVIJ": {
            "nome": "EDUARDO VIEIRA JUNQUEIRA",
            "email": "eduardo.junqueira@petrobras.com.br",
            "lotacao": "AUDITORIA/ADG/ACI",
            "cargo": "AUDITOR SÊNIOR",
        },
        "AB9V": {
            "nome": "ANA BEATRIZ VASCONCELOS",
            "email": "ana.vasconcelos@petrobras.com.br",
            "lotacao": "GEOLOGIA/EXPLORAÇÃO",
            "cargo": "ENGENHEIRA DE PETRÓLEO JUNIOR",
        },
        "YUD1": {
            "nome": "YURI DUARTE DOMINGUES",
            "email": "yuri.domingues@petrobras.com.br",
            "lotacao": "SUPRIMENTO/LOGÍSTICA",
            "cargo": "ESPECIALISTA EM LOGÍSTICA",
        },
    }

    # Resolve dados para uma chave de empregado
    def resolve(self, chave: str) -> dict[str, str]:
        """Retorna os dados de empregado para a chave informada."""
        data: dict[str, str] | None = None
        if busca_empregado is not None:
            try:
                data = busca_empregado(chave=chave)  # tenta serviço real
            except Exception:
                data = None
        if not data:
            data = self._MOCK_DATA.get(chave)
        if not data:
            data = {
                "nome": "DESCONHECIDO",
                "email": "DESCONHECIDO",
                "lotacao": "DESCONHECIDO",
                "cargo": "DESCONHECIDO",
            }
        # Always include the queried key
        data = {**data, "chave": chave}  # inclui a chave consultada no resultado
        return data

