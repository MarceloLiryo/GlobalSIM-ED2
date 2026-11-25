"""Persistência de clientes; buscas são responsabilidade da Árvore B."""
import json
from pathlib import Path


class ClientRepository:
    def __init__(self, filepath=None):
        self.filepath = Path(filepath) if filepath else Path(__file__).resolve().parent.parent / "data" / "clients.json"

    def load_all(self):
        if not self.filepath.exists():
            return []
        records = json.loads(self.filepath.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("O arquivo de clientes deve conter uma lista de registros.")
        return records

    def get_at(self, position):
        """Lê pela posição (RRN, base zero) obtida na Árvore B, sem busca por ID."""
        return self.load_all()[position]

    def update_at(self, position, record):
        """Altera o registro sem reordenar o arquivo nem invalidar posições."""
        records = self.load_all()
        records[position] = record
        self.save_all(records)

    def append_many(self, new_records):
        """Acrescenta ao final; posições anteriores permanecem estáveis."""
        records = self.load_all()
        start = len(records)
        records.extend(new_records)
        self.save_all(records)
        return list(range(start, len(records)))

    def save_all(self, records):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.filepath.with_suffix(self.filepath.suffix + ".tmp")
        temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.filepath)
