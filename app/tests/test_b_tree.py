import unittest
import random
from app.models.b_tree import BTree, Node
from app.models.client import Client


class TestBTree(unittest.TestCase):

    def test_node_creation(self):
        node = Node([10, 20])
        self.assertEqual(node.keys, [10, 20])
        self.assertTrue(node.is_leaf)
        self.assertFalse(node.full)
        self.assertEqual(node.lower_nodes, [])

    def test_btree_initialization_empty(self):
        tree = BTree(node_size=3)
        self.assertEqual(tree.node_size, 3)
        self.assertEqual(len(tree), 0)
        self.assertEqual(tree.list_keys(), [])
        self.assertFalse(tree.tree_search_key(10))

    def test_btree_initialization_with_list(self):
        tree = BTree([30, 10, 20], node_size=3)
        self.assertEqual(tree.list_keys(), [10, 20, 30])
        self.assertTrue(tree.tree_search_key(10))
        self.assertTrue(tree.tree_search_key(20))
        self.assertTrue(tree.tree_search_key(30))
        self.assertFalse(tree.tree_search_key(40))

    def test_btree_insert_without_split(self):
        tree = BTree(node_size=3)
        tree.tree_insert(20)
        tree.tree_insert(10)
        tree.tree_insert(30)

        self.assertEqual(tree.list_keys(), [10, 20, 30])
        self.assertEqual(tree.root.keys, [10, 20, 30])
        self.assertTrue(tree.root.full)
        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(tree.height(), 0)

    def test_btree_root_split(self):
        tree = BTree(node_size=3)
        tree.tree_insert(10)
        tree.tree_insert(20)
        tree.tree_insert(30)
        # Inserção do 4o elemento excede node_size (3) e divide a raiz
        tree.tree_insert(25)

        self.assertEqual(tree.list_keys(), [10, 20, 25, 30])
        self.assertEqual(tree.height(), 1)
        self.assertFalse(tree.root.is_leaf)
        # Raiz deve ter a chave promovida (25) e 2 filhos
        self.assertEqual(tree.root.keys, [25])
        self.assertEqual(len(tree.root.lower_nodes), 2)
        left_child, right_child = tree.root.lower_nodes
        self.assertEqual(left_child.keys, [10, 20])
        self.assertEqual(right_child.keys, [30])

    def test_btree_search_comparisons(self):
        tree = BTree([10, 20, 30, 40, 50, 60, 70], node_size=3)
        found = tree.tree_search_key(40)
        self.assertTrue(found)
        self.assertGreater(tree.last_search_comparisons, 0)

        not_found = tree.tree_search_key(999)
        self.assertFalse(not_found)
        self.assertGreater(tree.last_search_comparisons, 0)

    def test_btree_many_sequential_insertions(self):
        tree = BTree(node_size=3)
        elements = list(range(1, 31))
        for x in elements:
            tree.tree_insert(x)

        self.assertEqual(tree.list_keys(), elements)
        self.assertEqual(len(tree), 30)

        for x in elements:
            self.assertTrue(x in tree)
            self.assertTrue(tree.tree_search_key(x))

    def test_btree_random_insertions(self):
        random.seed(42)
        items = list(range(1, 101))
        shuffled = items.copy()
        random.shuffle(shuffled)

        tree = BTree(node_size=3)
        for x in shuffled:
            tree.tree_insert(x)

        self.assertEqual(tree.list_keys(), items)
        self.assertEqual(len(tree), 100)

        for x in items:
            self.assertTrue(tree.tree_search_key(x))

    def test_btree_no_duplicate_keys(self):
        tree = BTree(node_size=3)
        res1 = tree.tree_insert(10)
        res2 = tree.tree_insert(10)
        self.assertTrue(res1)
        self.assertFalse(res2)
        self.assertEqual(tree.list_keys(), [10])
        self.assertEqual(len(tree), 1)

    def test_btree_no_duplicate_keys_across_levels(self):
        elements = list(range(10, 200, 10))
        tree = BTree(elements, node_size=3)
        self.assertGreaterEqual(tree.height(), 2)

        root_key = tree.root.keys[0]
        internal_key = tree.root.lower_nodes[0].keys[0]
        leaf = tree.root.lower_nodes[0].lower_nodes[0]

        self.assertFalse(tree.tree_insert(root_key))
        self.assertFalse(tree.tree_insert(internal_key))
        self.assertFalse(tree.tree_insert(root_key, node=leaf))
        self.assertEqual(tree.list_keys(), elements)
        self.assertEqual(len(tree), len(elements))

    def test_btree_with_values(self):
        tree = BTree(node_size=3)
        tree.tree_insert(1, value="Cliente A")
        tree.tree_insert(2, value="Cliente B")
        tree.tree_insert(3, value="Cliente C")
        tree.tree_insert(4, value="Cliente D")

        self.assertEqual(tree.search(1), "Cliente A")
        self.assertEqual(tree.search(2), "Cliente B")
        self.assertEqual(tree.search(3), "Cliente C")
        self.assertEqual(tree.search(4), "Cliente D")
        self.assertIsNone(tree.search(99))

    def test_btree_deletion_leaf(self):
        tree = BTree([10, 20, 30, 40, 50], node_size=3)
        self.assertTrue(tree.tree_delete(50))
        self.assertFalse(50 in tree)
        self.assertEqual(tree.list_keys(), [10, 20, 30, 40])

    def test_btree_deletion_internal_node(self):
        tree = BTree([10, 20, 30, 40, 50, 60, 70], node_size=3)
        root_key = tree.root.keys[0]
        self.assertTrue(tree.tree_delete(root_key))
        self.assertFalse(root_key in tree)
        remaining = [x for x in [10, 20, 30, 40, 50, 60, 70] if x != root_key]
        self.assertEqual(tree.list_keys(), remaining)

    def test_btree_deletion_until_empty(self):
        items = [15, 5, 25, 10, 20, 30, 35]
        tree = BTree(items, node_size=3)

        for item in items:
            self.assertTrue(tree.tree_delete(item))
            self.assertFalse(item in tree)

        self.assertEqual(len(tree), 0)
        self.assertEqual(tree.list_keys(), [])

    def test_btree_metrics(self):
        tree = BTree([10, 20, 30, 40, 50], node_size=3)
        metrics = tree.get_metrics()

        self.assertEqual(metrics["node_size"], 3)
        self.assertEqual(metrics["total_keys"], 5)
        self.assertGreaterEqual(metrics["height"], 1)
        self.assertGreaterEqual(metrics["total_nodes"], 2)
        self.assertIn("last_search_comparisons", metrics)
        self.assertIn("root_keys", metrics)

    def test_btree_with_client_model(self):
        c1 = Client(101, "Alice", "alice@example.com", "ESIM-101", "Europa Basic")
        c2 = Client(102, "Bob", "bob@example.com", "ESIM-102", "Europa Plus")
        c3 = Client(103, "Carlos", "carlos@example.com", "ESIM-103", "Global")
        c4 = Client(104, "Diana", "diana@example.com", "ESIM-104", "América Plus")

        tree = BTree(node_size=3)
        tree.tree_insert(c1.id, value=c1)
        tree.tree_insert(c2.id, value=c2)
        tree.tree_insert(c3.id, value=c3)
        tree.tree_insert(c4.id, value=c4)

        self.assertEqual(tree.search(101), c1)
        self.assertEqual(tree.search(102), c2)
        self.assertEqual(tree.search(103), c3)
        self.assertEqual(tree.search(104), c4)

        items = tree.list_items()
        self.assertEqual(len(items), 4)
        self.assertEqual([item[0] for item in items], [101, 102, 103, 104])

    def test_btree_to_dict_and_print(self):
        tree = BTree([10, 20, 30, 40], node_size=3)
        tree_dict = tree.to_dict()
        self.assertIn("keys", tree_dict)
        self.assertIn("children", tree_dict)
        self.assertIn("is_leaf", tree_dict)
        # Não deve lançar exceção ao imprimir
        tree.print_tree()


if __name__ == "__main__":
    unittest.main()

