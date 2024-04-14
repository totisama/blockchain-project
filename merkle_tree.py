import hashlib


class MerkleNode:
    def __init__(self, hash):
        self.hash = hash
        self.parent = None
        self.left_child = None
        self.right_child = None


class MerkleTree:
    def __init__(self):
        self.leaves = []
        self.root = None

    def add_leaf(self, leaf_hash):
        new_leaf = MerkleNode(leaf_hash)
        self.leaves.append(new_leaf)
        self.recalculate_tree()

    def recalculate_tree(self):
        nodes = self.leaves
        while len(nodes) > 1:
            new_level = []
            for i in range(0, len(nodes), 2):
                left_child = nodes[i]
                right_child = nodes[i + 1] if i + 1 < len(nodes) else None
                if right_child:
                    node_hash = hashlib.sha256((left_child.hash + right_child.hash).encode('utf-8')).hexdigest()
                    parent_node = MerkleNode(node_hash)
                    parent_node.left_child, parent_node.right_child = left_child, right_child
                    left_child.parent = parent_node
                    right_child.parent = parent_node
                else:
                    parent_node = left_child
                new_level.append(parent_node)
            nodes = new_level
        self.root = nodes[0]

    def get_root_hash(self):
        return self.root.hash if self.root else ''
