"""Regras da Etapa 2: clientes indexados exclusivamente pela Árvore B."""
from app.models.b_tree import BTree
from app.models.client import Client
from app.models.packages import find_package, load_packages, package_covers_region
from app.repository.client_repository import ClientRepository


class ClientModel:
    def __init__(self, repository=None, packages=None):
        self.repository = repository if repository is not None else ClientRepository()
        self.packages = packages if packages is not None else load_packages()
        self.tree = BTree(node_size=3)
        for position, data in enumerate(self.repository.load_all()):
            client = self._validate(data)
            if self.tree.search(client.id) is not None:
                raise ValueError(f"ID de cliente duplicado no arquivo: {client.id}.")
            self.tree.insert(client.id, position)
        self.tree.last_search_comparisons = 0

    @staticmethod
    def parse_id(value):
        if isinstance(value, bool) or not str(value).strip().isdigit() or int(value) <= 0:
            raise ValueError("O ID do cliente deve ser um inteiro positivo.")
        return int(value)

    def _validate(self, data):
        client_id = self.parse_id(data.get("id", ""))
        name = str(data.get("name", data.get("nome")) or "").strip()
        email = str(data.get("email") or "").strip()
        esim = str(data.get("esim") or "").strip()
        status = str(data.get("status", "ativo")).strip().lower()
        try:
            package_code = int(str(data.get("pacote", "")).strip())
        except (TypeError, ValueError):
            raise ValueError("Selecione um pacote válido.") from None
        if not name or not esim:
            raise ValueError("Nome e eSIM são obrigatórios.")
        if email.count("@") != 1 or not all(email.split("@")) or any(c.isspace() for c in email):
            raise ValueError("Informe um e-mail válido.")
        if status not in ("ativo", "inativo", "suspenso"):
            raise ValueError("Status inválido. Use ativo, inativo ou suspenso.")
        if find_package(self.packages, package_code) is None:
            raise ValueError("Selecione um pacote válido.")
        return Client(client_id, name, email, esim, package_code, status)

    def get_by_id(self, client_id):
        position = self.tree.search(self.parse_id(client_id))
        if position is None:
            return None
        return self._validate(self.repository.get_at(position))

    def list_all(self):
        records = self.repository.load_all()
        return [self._validate(records[position]) for _, position in self.tree.list_items()]

    def create(self, data):
        client = self._validate(data)
        if self.tree.search(client.id) is not None:
            raise ValueError(f"Já existe um cliente com ID {client.id}.")
        # Persiste antes de alterar a estrutura em memória, evitando alterações
        # parciais caso o arquivo não possa ser gravado.
        position = self.repository.append_many([client.to_dict()])[0]
        self.tree.insert(client.id, position)
        return client

    def update(self, client_id, data):
        existing = self.get_by_id(client_id)
        if existing is None:
            raise KeyError("Cliente não encontrado.")
        if "id" in data and self.parse_id(data["id"]) != existing.id:
            raise ValueError("O ID do cliente não pode ser alterado.")
        client = self._validate({**existing.to_dict(), **data, "id": existing.id})
        position = self.tree.search(existing.id)
        self.repository.update_at(position, client.to_dict())
        return client

    def consult_destination(self, client_id, destination, countries):
        client = self.get_by_id(client_id)
        comparisons = self.tree.last_search_comparisons
        if client is None:
            raise KeyError("Cliente não encontrado.")
        if not destination.strip():
            raise ValueError("Informe o código do país de destino.")

        country = countries.get_by_code(destination)
        package = find_package(self.packages, client.pacote)
        client_active = client.status == "ativo"
        package_covers = (
            package_covers_region(package, country["region"])
            if (country and package)
            else None
        )

        reasons = []
        if country is None:
            reasons.append(f"O código {destination.strip().upper()} não possui cobertura na Tabela Hash.")
        else:
            if not package_covers:
                pkg_label = f"{package['name']} (#{package['code']})" if package else f"#{client.pacote}"
                reasons.append(
                    f"O pacote {pkg_label} não cobre {country['country']} ({country['region']})."
                )
            if client.status == "suspenso":
                reasons.append("O cliente está com status suspenso e não pode usar a conexão.")
            elif client.status == "inativo":
                reasons.append("O cliente está com status inativo; é necessário ativar a linha antes do uso.")

        can_connect = bool(country and package_covers and client_active)
        if can_connect:
            compatibility_status = "ok"
            compatibility_message = (
                f"Compatível: o pacote {package['name']} cobre {country['country']} "
                f"({country['region']}) e o eSIM está ativo."
            )
        elif country is not None and package_covers and client.status == "inativo":
            compatibility_status = "warning"
            compatibility_message = " ".join(reasons)
        else:
            compatibility_status = "error"
            compatibility_message = " ".join(reasons)

        return {
            "client": client,
            "package": package,
            "country": country,
            "tree_comparisons": comparisons,
            "hash_comparisons": countries.get_instrumentation()["last_search_comparisons"],
            "package_covers_destination": package_covers,
            "client_active": client_active,
            "can_connect": can_connect,
            "compatibility_status": compatibility_status,
            "compatibility_message": compatibility_message,
            "compatibility_reasons": reasons,
        }

    def assign_recommended_package(self, client_id, itinerary, countries):
        if self.get_by_id(client_id) is None:
            raise KeyError("Cliente não encontrado.")
        result = countries.recommend_package_for_itinerary(itinerary)
        if not result["valid"] or result.get("uncovered") or not result.get("recommended_package"):
            raise ValueError("O roteiro deve conter apenas destinos com cobertura para associar o pacote.")
        return self.update(client_id, {"pacote": result["recommended_package"]["code"]})

    def generate_clients(self, count=1000):
        """Acrescenta dados fictícios sem substituir cadastros existentes."""
        generated = []
        candidate = 10001
        while len(generated) < count:
            if self.tree.search(candidate) is None:
                package = self.packages[len(generated) % len(self.packages)]["code"]
                generated.append(Client(candidate, f"Cliente Demonstração {candidate}",
                                        f"cliente{candidate}@example.com", f"ESIM-{candidate}", package))
            candidate += 1
        positions = self.repository.append_many([client.to_dict() for client in generated])
        for client, position in zip(generated, positions):
            self.tree.insert(client.id, position)
        return len(generated)
