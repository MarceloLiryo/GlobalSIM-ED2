from collections import deque
from typing import Any


class Node:
    """
    Nó da Árvore B.
    Armazena uma lista ordenada de chaves (keys), valores associados opcionais (values)
    e referências para os nós filhos (lower_nodes).
    """

    def __init__(
        self,
        keys: list[Any] | None = None,
        values: list[Any] | None = None,
    ):
        self.keys: list[Any] = list(keys) if keys is not None else []
        self.values: list[Any] = list(values) if values is not None else []
        self.lower_nodes: list["Node"] = []
        self.full: bool = False

    @property
    def is_leaf(self) -> bool:
        """Retorna True se o nó for folha (não possui nós filhos)."""
        return len(self.lower_nodes) == 0

    def __repr__(self) -> str:
        return f"Node(keys={self.keys}, full={self.full}, children={len(self.lower_nodes)})"


class BTree:
    """
    Árvore B com ordem parametrizada por node_size (capacidade máxima de chaves por nó).
    Por padrão, node_size = 3 (similar a uma árvore 2-3-4).
    Garante balanceamento perfeito onde todas as folhas permanecem rigorosamente no mesmo nível.
    """

    def __init__(self, keys: list[Any] | int | None = None, node_size: int = 3):
        if isinstance(keys, int):
            self.node_size: int = keys
            self.root: Node = Node([])
        else:
            self.node_size: int = node_size
            self.root: Node = Node([])
            if keys is not None:
                self.__tree_create_layer(keys)

        self.min_keys: int = max(1, self.node_size // 2)
        self.last_search_comparisons: int = 0

    def __tree_create_layer(self, keys: list[Any] | Any) -> None:
        """
        Insere chaves sequencialmente na Árvore B para criar/popular as camadas da árvore.
        """
        if isinstance(keys, (list, tuple, set)):
            for key in keys:
                self.tree_insert(key)
        else:
            self.tree_insert(keys)

    def _update_node_full(self, node: Node) -> None:
        """Atualiza a flag full do nó com base em node_size."""
        node.full = len(node.keys) >= self.node_size

    def tree_insert(
        self,
        input: Any,
        node: Node | None = None,
        value: Any = None,
    ) -> bool:
        """
        Insere uma chave (e valor opcional) na Árvore B.
        A inserção ocorre nas folhas. Caso um nó atinja capacidade superior a node_size,
        ele é dividido (split) promovendo a chave mediana para o nó pai.
        Se a raiz se dividir, cria uma nova raiz aumentando a altura da árvore.
        """
        if node is None or node is self.root:
            target_node = self.root
            inserted, promoted_key, right_node, promoted_val = self._insert_recursive(
                target_node, input, value
            )

            # Se a raiz transbordou e dividiu, cria uma nova raiz
            if promoted_key is not None and right_node is not None:
                new_root = Node(
                    keys=[promoted_key],
                    values=[promoted_val] if promoted_val is not None else [],
                )
                new_root.lower_nodes = [self.root, right_node]
                self._update_node_full(new_root)
                self._update_node_full(self.root)
                self._update_node_full(right_node)
                self.root = new_root

            return inserted
        else:
            # Inserção a partir de um subnó específico
            inserted, _, _, _ = self._insert_recursive(node, input, value)
            return inserted

    def _insert_recursive(
        self,
        current: Node,
        key: Any,
        value: Any = None,
    ) -> tuple[bool, Any | None, Node | None, Any | None]:
        """
        Método recursivo auxiliar de descida até as folhas para inserção.
        Retorna (inserido, chave_promovida, novo_no_direito, valor_promovido).
        """
        # Se a chave já existir no nó atual, atualiza o valor se fornecido e não duplica
        if key in current.keys:
            idx = current.keys.index(key)
            if value is not None and current.values and idx < len(current.values):
                current.values[idx] = value
            return False, None, None, None

        # Caso 1: Nó atual é folha -> insere mantendo ordenado
        if current.is_leaf:
            # Encontrar o índice correto de inserção
            insert_idx = len(current.keys)
            for i, k in enumerate(current.keys):
                if key < k:
                    insert_idx = i
                    break

            current.keys.insert(insert_idx, key)
            if value is not None or current.values:
                current.values.insert(insert_idx, value)

            self._update_node_full(current)

            # Verificar se excedeu a capacidade máxima (overflow)
            if len(current.keys) > self.node_size:
                return self._split_node(current)

            return True, None, None, None

        # Caso 2: Nó interno -> navega para o nó filho apropriado (lower_nodes)
        child_idx = len(current.keys)
        for i, k in enumerate(current.keys):
            if key < k:
                child_idx = i
                break

        child = current.lower_nodes[child_idx]
        inserted, promoted_key, right_child, promoted_val = self._insert_recursive(
            child, key, value
        )

        # Se o nó filho não dividiu, atualiza o nó atual e propaga
        if promoted_key is None or right_child is None:
            self._update_node_full(current)
            return inserted, None, None, None

        # Nó filho dividiu: insere a chave promovida e o novo nó filho à direita
        current.keys.insert(child_idx, promoted_key)
        if promoted_val is not None or current.values:
            current.values.insert(child_idx, promoted_val)

        current.lower_nodes.insert(child_idx + 1, right_child)
        self._update_node_full(current)

        # Verifica se o nó atual também transbordou
        if len(current.keys) > self.node_size:
            return self._split_node(current)

        return True, None, None, None

    def _split_node(
        self,
        node: Node,
    ) -> tuple[bool, Any, Node, Any]:
        """
        Realiza a cisão (split) de um nó que excedeu node_size.
        Calcula o elemento mediano, reparte as chaves e filhos entre o nó esquerdo e o novo nó direito.
        """
        mid = len(node.keys) // 2
        promoted_key = node.keys[mid]
        promoted_val = node.values[mid] if node.values and mid < len(node.values) else None

        # O nó atual se torna o nó esquerdo
        left_keys = node.keys[:mid]
        left_values = node.values[:mid] if node.values else []

        right_keys = node.keys[mid + 1 :]
        right_values = node.values[mid + 1 :] if node.values else []

        right_node = Node(keys=right_keys, values=right_values)

        # Se não for folha, divide também os ponteiros de filhos
        if not node.is_leaf:
            left_children = node.lower_nodes[: mid + 1]
            right_children = node.lower_nodes[mid + 1 :]
            node.lower_nodes = left_children
            right_node.lower_nodes = right_children

        node.keys = left_keys
        node.values = left_values

        self._update_node_full(node)
        self._update_node_full(right_node)

        return True, promoted_key, right_node, promoted_val

    def tree_node_fix(self, target: Any = None) -> None:
        """
        Método de ajuste/correção da árvore (cisão de nós cheios/overflow).
        Mantido para compatibilidade com o esboço original do código.
        """
        if isinstance(target, Node):
            if len(target.keys) > self.node_size:
                self._split_node(target)
            return

        # Verifica e corrige nós que porventura excedam a capacidade
        self._check_and_fix_overflow(self.root)

    def _check_and_fix_overflow(self, node: Node) -> None:
        """Varre recursivamente a árvore corrigindo eventuais nós em overflow."""
        if not node:
            return
        for child in node.lower_nodes:
            self._check_and_fix_overflow(child)
        if len(node.keys) > self.node_size:
            self._split_node(node)

    def tree_search_key(self, input: Any, node: Node | None = None) -> bool:
        """
        Busca uma chave na Árvore B a partir de um nó (padrão: raiz).
        Retorna True se encontrada, False caso contrário.
        Registra a quantidade de comparações em self.last_search_comparisons.
        """
        if node is None:
            node = self.root
            self.last_search_comparisons = 0

        self.last_search_comparisons += 1
        if input in node.keys:
            return True

        if len(node.lower_nodes) == 0:
            return False

        for i, key in enumerate(node.keys):
            self.last_search_comparisons += 1
            if input < key:
                return self.tree_search_key(input, node.lower_nodes[i])

        return self.tree_search_key(input, node.lower_nodes[-1])

    def search(self, key: Any, node: Node | None = None) -> Any | None:
        """
        Busca uma chave na Árvore B e retorna o valor associado (ou a própria chave).
        Retorna None se a chave não for encontrada.
        """
        if node is None:
            node = self.root
            self.last_search_comparisons = 0

        for i, k in enumerate(node.keys):
            self.last_search_comparisons += 1
            if k == key:
                if node.values and i < len(node.values) and node.values[i] is not None:
                    return node.values[i]
                return k
            elif key < k:
                if len(node.lower_nodes) > i:
                    return self.search(key, node.lower_nodes[i])
                return None

        if len(node.lower_nodes) > len(node.keys):
            return self.search(key, node.lower_nodes[len(node.keys)])
        return None

    def search_node(
        self, key: Any, node: Node | None = None
    ) -> tuple[Node | None, int | None]:
        """
        Retorna o nó e o índice onde a chave foi encontrada, ou (None, None).
        """
        if node is None:
            node = self.root

        for i, k in enumerate(node.keys):
            if k == key:
                return (node, i)
            elif key < k:
                if len(node.lower_nodes) > i:
                    return self.search_node(key, node.lower_nodes[i])
                return (None, None)

        if len(node.lower_nodes) > len(node.keys):
            return self.search_node(key, node.lower_nodes[len(node.keys)])
        return (None, None)

    def insert(self, key: Any, value: Any = None) -> bool:
        """Alias para tree_insert."""
        return self.tree_insert(key, value=value)

    def tree_delete(self, key: Any) -> bool:
        """
        Remove uma chave da Árvore B com rebalanceamento (empréstimo de irmãos ou fusão).
        Retorna True se removida com sucesso, False se a chave não existir.
        """
        # Localiza o caminho até o nó contendo a chave
        path: list[tuple[Node, int]] = []
        curr = self.root
        target_node: Node | None = None
        key_idx: int = -1

        while curr:
            found = False
            for i, k in enumerate(curr.keys):
                if k == key:
                    target_node = curr
                    key_idx = i
                    found = True
                    break
                elif key < k:
                    if curr.is_leaf:
                        return False
                    path.append((curr, i))
                    curr = curr.lower_nodes[i]
                    found = True
                    break

            if not found:
                if curr.is_leaf:
                    return False
                path.append((curr, len(curr.keys)))
                curr = curr.lower_nodes[-1]

            if target_node is not None:
                break

        if target_node is None:
            return False

        # Caso 1: A chave está em uma folha
        if target_node.is_leaf:
            target_node.keys.pop(key_idx)
            if target_node.values and key_idx < len(target_node.values):
                target_node.values.pop(key_idx)
            self._update_node_full(target_node)

            # Rebalancear o caminho se o nó folha ficar com menos chaves que o mínimo
            self._rebalance_path(path)
            self._adjust_root()
            return True

        # Caso 2: A chave está em um nó interno -> substituir pelo predecessor
        pred_path: list[tuple[Node, int]] = list(path)
        pred_path.append((target_node, key_idx))

        pred_node = target_node.lower_nodes[key_idx]
        while not pred_node.is_leaf:
            pred_path.append((pred_node, len(pred_node.keys)))
            pred_node = pred_node.lower_nodes[-1]

        # pred_node é a folha que contém o antecessor máximo
        predecessor_key = pred_node.keys.pop()
        predecessor_val = (
            pred_node.values.pop()
            if pred_node.values and len(pred_node.values) > len(pred_node.keys)
            else None
        )
        self._update_node_full(pred_node)

        # Substitui a chave no target_node pelo predecessor
        target_node.keys[key_idx] = predecessor_key
        if target_node.values and key_idx < len(target_node.values):
            target_node.values[key_idx] = predecessor_val

        # Rebalanceia o caminho do predecessor
        self._rebalance_path(pred_path)
        self._adjust_root()
        return True

    def _rebalance_path(self, path: list[tuple[Node, int]]) -> None:
        """Percorre a pilha de ancestrais rebalanceando nós em underflow."""
        for p, child_idx in reversed(path):
            child = p.lower_nodes[child_idx]
            if len(child.keys) < self.min_keys:
                self._rebalance_child(p, child_idx)
            else:
                self._update_node_full(child)

    def _rebalance_child(self, parent: Node, child_idx: int) -> None:
        """Rebalanceia um filho emprestando de um irmão ou realizando fusão (merge)."""
        child = parent.lower_nodes[child_idx]

        # 1. Tenta emprestar do irmão à esquerda
        if child_idx > 0:
            left_sibling = parent.lower_nodes[child_idx - 1]
            if len(left_sibling.keys) > self.min_keys:
                # Rotaciona para a direita
                borrowed_parent_key = parent.keys[child_idx - 1]
                borrowed_parent_val = (
                    parent.values[child_idx - 1]
                    if parent.values and child_idx - 1 < len(parent.values)
                    else None
                )

                child.keys.insert(0, borrowed_parent_key)
                if borrowed_parent_val is not None or child.values:
                    child.values.insert(0, borrowed_parent_val)

                parent.keys[child_idx - 1] = left_sibling.keys.pop()
                if left_sibling.values and len(left_sibling.values) > len(left_sibling.keys):
                    parent.values[child_idx - 1] = left_sibling.values.pop()

                if left_sibling.lower_nodes:
                    child.lower_nodes.insert(0, left_sibling.lower_nodes.pop())

                self._update_node_full(child)
                self._update_node_full(left_sibling)
                self._update_node_full(parent)
                return

        # 2. Tenta emprestar do irmão à direita
        if child_idx < len(parent.lower_nodes) - 1:
            right_sibling = parent.lower_nodes[child_idx + 1]
            if len(right_sibling.keys) > self.min_keys:
                # Rotaciona para a esquerda
                borrowed_parent_key = parent.keys[child_idx]
                borrowed_parent_val = (
                    parent.values[child_idx]
                    if parent.values and child_idx < len(parent.values)
                    else None
                )

                child.keys.append(borrowed_parent_key)
                if borrowed_parent_val is not None or child.values:
                    child.values.append(borrowed_parent_val)

                parent.keys[child_idx] = right_sibling.keys.pop(0)
                if right_sibling.values:
                    parent.values[child_idx] = right_sibling.values.pop(0)

                if right_sibling.lower_nodes:
                    child.lower_nodes.append(right_sibling.lower_nodes.pop(0))

                self._update_node_full(child)
                self._update_node_full(right_sibling)
                self._update_node_full(parent)
                return

        # 3. Nenhum irmão pode emprestar -> Fusão (Merge)
        if child_idx > 0:
            # Funde com o irmão esquerdo
            left_sibling = parent.lower_nodes[child_idx - 1]
            sep_key = parent.keys.pop(child_idx - 1)
            sep_val = (
                parent.values.pop(child_idx - 1)
                if parent.values and child_idx - 1 < len(parent.values)
                else None
            )

            left_sibling.keys.append(sep_key)
            if sep_val is not None or left_sibling.values:
                left_sibling.values.append(sep_val)

            left_sibling.keys.extend(child.keys)
            if child.values:
                left_sibling.values.extend(child.values)
            left_sibling.lower_nodes.extend(child.lower_nodes)

            parent.lower_nodes.pop(child_idx)
            self._update_node_full(left_sibling)
            self._update_node_full(parent)
        else:
            # Funde com o irmão direito
            right_sibling = parent.lower_nodes[child_idx + 1]
            sep_key = parent.keys.pop(child_idx)
            sep_val = (
                parent.values.pop(child_idx)
                if parent.values and child_idx < len(parent.values)
                else None
            )

            child.keys.append(sep_key)
            if sep_val is not None or child.values:
                child.values.append(sep_val)

            child.keys.extend(right_sibling.keys)
            if right_sibling.values:
                child.values.extend(right_sibling.values)
            child.lower_nodes.extend(right_sibling.lower_nodes)

            parent.lower_nodes.pop(child_idx + 1)
            self._update_node_full(child)
            self._update_node_full(parent)

    def _adjust_root(self) -> None:
        """Ajusta a raiz se ela ficou vazia após fusão sucessiva."""
        if len(self.root.keys) == 0 and len(self.root.lower_nodes) > 0:
            self.root = self.root.lower_nodes[0]
        self._update_node_full(self.root)

    def remove(self, key: Any) -> bool:
        """Alias para tree_delete."""
        return self.tree_delete(key)

    def inorder(self, node: Node | None = None) -> list[Any]:
        """Retorna uma lista ordenada com todas as chaves da Árvore B (in-order traversal)."""
        if node is None:
            if len(self.root.keys) == 0 and len(self.root.lower_nodes) == 0:
                return []
            node = self.root

        result: list[Any] = []
        if node.is_leaf:
            result.extend(node.keys)
        else:
            for i in range(len(node.keys)):
                if i < len(node.lower_nodes):
                    result.extend(self.inorder(node.lower_nodes[i]))
                result.append(node.keys[i])
            if len(node.lower_nodes) > len(node.keys):
                result.extend(self.inorder(node.lower_nodes[len(node.keys)]))

        return result

    def list_keys(self) -> list[Any]:
        """Retorna todas as chaves em ordem crescente."""
        return self.inorder()

    def list_items(self, node: Node | None = None) -> list[tuple[Any, Any]]:
        """Retorna pares (chave, valor) em ordem crescente."""
        if node is None:
            if len(self.root.keys) == 0 and len(self.root.lower_nodes) == 0:
                return []
            node = self.root

        items: list[tuple[Any, Any]] = []
        if node.is_leaf:
            for i, k in enumerate(node.keys):
                v = node.values[i] if node.values and i < len(node.values) else None
                items.append((k, v))
        else:
            for i in range(len(node.keys)):
                if i < len(node.lower_nodes):
                    items.extend(self.list_items(node.lower_nodes[i]))
                v = node.values[i] if node.values and i < len(node.values) else None
                items.append((node.keys[i], v))
            if len(node.lower_nodes) > len(node.keys):
                items.extend(self.list_items(node.lower_nodes[len(node.keys)]))

        return items

    def height(self) -> int:
        """Calcula a altura da Árvore B (0 se apenas a raiz existir)."""
        h = 0
        curr = self.root
        while curr and not curr.is_leaf and len(curr.lower_nodes) > 0:
            h += 1
            curr = curr.lower_nodes[0]
        return h

    def count_nodes(self, node: Node | None = None) -> int:
        """Conta a quantidade total de nós na Árvore B."""
        if node is None:
            if len(self.root.keys) == 0 and len(self.root.lower_nodes) == 0:
                return 0
            node = self.root

        total = 1
        for child in node.lower_nodes:
            total += self.count_nodes(child)
        return total

    def get_metrics(self) -> dict[str, Any]:
        """
        Retorna as métricas de instrumentação da Árvore B para monitoramento no sistema.
        """
        keys = self.list_keys()
        return {
            "node_size": self.node_size,
            "min_keys": self.min_keys,
            "total_keys": len(keys),
            "height": self.height(),
            "total_nodes": self.count_nodes(),
            "last_search_comparisons": self.last_search_comparisons,
            "root_keys": list(self.root.keys),
            "root_full": self.root.full,
        }

    def to_dict(self, node: Node | None = None) -> dict[str, Any]:
        """Exporta a estrutura da árvore em formato de dicionário hierárquico."""
        if node is None:
            node = self.root
        return {
            "keys": list(node.keys),
            "full": node.full,
            "is_leaf": node.is_leaf,
            "children": [self.to_dict(child) for child in node.lower_nodes],
        }

    def print_tree(self) -> None:
        """Exibe uma representação visual nível a nível da Árvore B no terminal."""
        if not self.root or (len(self.root.keys) == 0 and self.root.is_leaf):
            print("Árvore B vazia.")
            return

        queue: deque[tuple[Node, int]] = deque([(self.root, 0)])
        current_level = 0
        level_nodes: list[str] = []

        while queue:
            node, level = queue.popleft()
            if level > current_level:
                print(f"Nível {current_level}: " + " | ".join(level_nodes))
                current_level = level
                level_nodes = []

            status = " [CHEIO]" if node.full else ""
            level_nodes.append(f"{node.keys}{status}")

            for child in node.lower_nodes:
                queue.append((child, level + 1))

        if level_nodes:
            print(f"Nível {current_level}: " + " | ".join(level_nodes))

    def __len__(self) -> int:
        return len(self.list_keys())

    def __contains__(self, key: Any) -> bool:
        return self.tree_search_key(key)

    def __iter__(self):
        return iter(self.list_keys())

    def __repr__(self) -> str:
        return f"BTree(node_size={self.node_size}, keys={self.list_keys()})"
