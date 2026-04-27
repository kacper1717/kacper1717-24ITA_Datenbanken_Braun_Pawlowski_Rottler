# btree_k2.py
# B-Baum nach Knuth-Konvention, Ordnung k = 2
# - min. k = 2 Schlüssel pro Knoten (außer Wurzel)
# - max. 2*k = 4 Schlüssel pro Knoten
# - Wurzel: 1..2*k Schlüssel
#
# Didaktik-Ziel (passend zur Vorlesung):
# - insert(): Splits bei vollem Knoten (4 Schlüssel) -> medianer wird "promoted"
# - delete(): Underflow (< 2 Schlüssel) -> Redistribute mit Nachbar, sonst Merge
# - search(): zeigt Navigationspfad
# - print_tree(): levelweise Ausgabe
# - to_dot(): Graphviz-Export

from __future__ import annotations
from typing import List, Optional, Tuple


class BTreeNode:
    def __init__(self, k: int, leaf: bool = True):
        self.k = k                        # Ordnung k (min. Schlüssel pro Nicht-Wurzel-Knoten)
        self.leaf = leaf
        self.keys: List[int] = []
        self.children: List[BTreeNode] = []  # bei inneren Knoten: len(children) = len(keys)+1

    def is_full(self) -> bool:
        # voll = 2*k Schlüssel (darf NICHT überschritten werden)
        return len(self.keys) == 2 * self.k

    def has_min(self) -> bool:
        # hat genau die Mindestanzahl k Schlüssel
        return len(self.keys) == self.k


class BTree:
    def __init__(self, k: int = 2):
        """
        k = Ordnung (Knuth-Konvention).
        - min. k Schlüssel pro Knoten (außer Wurzel)
        - max. 2*k Schlüssel pro Knoten
        Default k=2  -> 2..4 Schlüssel pro Knoten (wie in der Vorlesung).
        """
        self.k = k
        self.root = BTreeNode(k, leaf=True)

    # =========================================================
    # SUCHE (mit Pfad-Ausgabe)
    # =========================================================
    def search(self, key: int, node: Optional[BTreeNode] = None, path=None):
        if node is None:
            node = self.root
        if path is None:
            path = []

        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        path.append((node.keys.copy(), i))

        if i < len(node.keys) and node.keys[i] == key:
            return True, path
        if node.leaf:
            return False, path
        return self.search(key, node.children[i], path)

    # =========================================================
    # EINFÜGEN
    # =========================================================
    def insert(self, key: int) -> None:
        r = self.root
        if r.is_full():
            s = BTreeNode(self.k, leaf=False)
            s.children = [r]
            self.root = s
            self._split_child(parent=s, index=0)
            self._insert_nonfull(s, key)
        else:
            self._insert_nonfull(r, key)

    def _insert_nonfull(self, node: BTreeNode, key: int) -> None:
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(0)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
            return

        while i >= 0 and key < node.keys[i]:
            i -= 1
        i += 1

        if node.children[i].is_full():
            self._split_child(parent=node, index=i)
            if key > node.keys[i]:
                i += 1
        self._insert_nonfull(node.children[i], key)

    def _split_child(self, parent: BTreeNode, index: int) -> None:
        """
        Splittet parent.children[index] (voll, 2*k Schlüssel) in zwei Knoten.
        Bei k=2: voller Knoten hat 4 Schlüssel [a,b,c,d].
                 -> y bekommt [a,b], median = c steigt auf, z bekommt [d]
                 (klassische Knuth-Variante: linke Hälfte = k Schlüssel,
                  rechte Hälfte = k-1 Schlüssel, mittlerer steigt auf)
        """
        k = self.k
        y = parent.children[index]
        z = BTreeNode(k, leaf=y.leaf)

        median = y.keys[k]               # bei k=2: y.keys[2]
        z.keys = y.keys[k + 1:]          # rechte Hälfte (k+1 .. 2k-1)  -> k-1 Schlüssel
        y.keys = y.keys[:k]              # linke  Hälfte (0 .. k-1)    -> k   Schlüssel

        if not y.leaf:
            z.children = y.children[k + 1:]
            y.children = y.children[:k + 1]

        parent.keys.insert(index, median)
        parent.children.insert(index + 1, z)

    # =========================================================
    # LÖSCHEN
    # =========================================================
    def delete(self, key: int) -> None:
        self._delete(self.root, key)
        # Wurzel könnte leer geworden sein -> Baum schrumpft eine Ebene
        if not self.root.keys and not self.root.leaf:
            self.root = self.root.children[0]

    def _delete(self, node: BTreeNode, key: int) -> None:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        # Fall 1: Schlüssel im aktuellen Knoten gefunden
        if i < len(node.keys) and node.keys[i] == key:
            if node.leaf:
                # 1a) Blatt: einfach entfernen
                node.keys.pop(i)
            else:
                # 1b) Innerer Knoten
                self._delete_internal(node, i)
            return

        # Fall 2: nicht hier - in Blatt? -> nicht im Baum
        if node.leaf:
            return  # Schlüssel nicht vorhanden

        # Fall 3: Schlüssel ist im Teilbaum children[i].
        # Bevor wir absteigen, sicherstellen, dass das Kind > k Schlüssel hat
        # (sonst Underflow vorbeugen durch Redistribute / Merge).
        if len(node.children[i].keys) == self.k:
            self._fix_underflow(node, i)
            # Nach einem Merge kann sich i verschoben haben, neu positionieren:
            if i > len(node.keys):
                i = len(node.keys)
        self._delete(node.children[i], key)

    def _delete_internal(self, node: BTreeNode, i: int) -> None:
        """Schlüssel node.keys[i] ist in einem inneren Knoten zu löschen."""
        key = node.keys[i]
        left = node.children[i]
        right = node.children[i + 1]

        if len(left.keys) > self.k:
            # Vorgänger nehmen (größter Schlüssel im linken Teilbaum)
            pred = self._max_key(left)
            node.keys[i] = pred
            self._delete(left, pred)
        elif len(right.keys) > self.k:
            # Nachfolger nehmen (kleinster Schlüssel im rechten Teilbaum)
            succ = self._min_key(right)
            node.keys[i] = succ
            self._delete(right, succ)
        else:
            # Beide Nachbarn haben nur k Schlüssel -> Merge
            self._merge_children(node, i)
            self._delete(left, key)  # left enthält jetzt key + alles aus right

    def _max_key(self, node: BTreeNode) -> int:
        while not node.leaf:
            node = node.children[-1]
        return node.keys[-1]

    def _min_key(self, node: BTreeNode) -> int:
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]

    def _fix_underflow(self, parent: BTreeNode, i: int) -> None:
        """
        Sorgt dafür, dass parent.children[i] mehr als k Schlüssel hat.
        Reihenfolge gemäß Vorlesung:
          1. Redistribute mit linkem Nachbarn (falls > k Schlüssel)
          2. Redistribute mit rechtem Nachbarn (falls > k Schlüssel)
          3. sonst Merge
        """
        child = parent.children[i]

        # 1) Linker Nachbar kann abgeben?
        if i > 0 and len(parent.children[i - 1].keys) > self.k:
            self._redistribute_from_left(parent, i)
            return

        # 2) Rechter Nachbar kann abgeben?
        if i < len(parent.children) - 1 and len(parent.children[i + 1].keys) > self.k:
            self._redistribute_from_right(parent, i)
            return

        # 3) Merge
        if i > 0:
            self._merge_children(parent, i - 1)  # mit linkem Nachbarn mergen
        else:
            self._merge_children(parent, i)      # mit rechtem Nachbarn mergen

    def _redistribute_from_left(self, parent: BTreeNode, i: int) -> None:
        """Nimm Schlüssel vom linken Nachbarn über den Parent-Schlüssel."""
        child = parent.children[i]
        left = parent.children[i - 1]

        # Parent-Schlüssel runter ans Kind, größter Key vom linken Nachbarn hoch in Parent
        child.keys.insert(0, parent.keys[i - 1])
        parent.keys[i - 1] = left.keys.pop()
        if not left.leaf:
            child.children.insert(0, left.children.pop())

    def _redistribute_from_right(self, parent: BTreeNode, i: int) -> None:
        """Nimm Schlüssel vom rechten Nachbarn über den Parent-Schlüssel."""
        child = parent.children[i]
        right = parent.children[i + 1]

        child.keys.append(parent.keys[i])
        parent.keys[i] = right.keys.pop(0)
        if not right.leaf:
            child.children.append(right.children.pop(0))

    def _merge_children(self, parent: BTreeNode, i: int) -> None:
        """
        Mergt parent.children[i] und parent.children[i+1] zu einem Knoten.
        Der Trennschlüssel parent.keys[i] wandert mit nach unten in den
        zusammengeführten Knoten. Ergebnis: parent verliert einen Schlüssel
        und ein Kind.
        """
        left = parent.children[i]
        right = parent.children[i + 1]

        left.keys.append(parent.keys[i])
        left.keys.extend(right.keys)
        if not left.leaf:
            left.children.extend(right.children)

        parent.keys.pop(i)
        parent.children.pop(i + 1)

    # =========================================================
    # AUSGABE
    # =========================================================
    def print_tree(self) -> str:
        lines = []
        queue = [self.root]
        level = 0
        while queue:
            lines.append(f"Level {level}: " + " | ".join(str(n.keys) for n in queue))
            next_q = []
            for n in queue:
                if not n.leaf:
                    next_q.extend(n.children)
            queue = next_q
            level += 1
        return "\n".join(lines)

    # =========================================================
    # GRAPHVIZ DOT EXPORT
    # =========================================================
    def to_dot(self) -> str:
        lines = [
            "digraph BTree {",
            "  rankdir=TB;",
            "  graph [splines=true, nodesep=0.35, ranksep=0.45];",
            "  node  [shape=record, height=.1, fontname=Helvetica];",
            "  edge  [fontname=Helvetica];",
        ]
        counter = {"id": 0}

        def record_label(keys: list[int]) -> str:
            parts = ["<p0>"]
            for i, key in enumerate(keys):
                parts.append(str(key))
                parts.append(f"<p{i+1}>")
            return " | ".join(parts) if keys else "<p0>"

        def add_node(n: BTreeNode) -> int:
            my_id = counter["id"]
            counter["id"] += 1
            label = record_label(n.keys).replace('"', '\\"')
            lines.append(f'  n{my_id} [label="{label}"];')
            if not n.leaf:
                for i, child in enumerate(n.children):
                    cid = add_node(child)
                    lines.append(f"  n{my_id}:p{i} -> n{cid}:p0;")
            return my_id

        add_node(self.root)
        lines.append("}")
        return "\n".join(lines)


# =============================================================
# DEMO – passend zu den Übungen aus der Vorlesung
# =============================================================
def main():
    # ----- Übung 1: 10, 20, 5, 30, 25 -----
    print("=== Übung 1: einfache Einfügesequenz ===")
    b = BTree(k=2)
    for v in [10, 20, 5, 30, 25]:
        b.insert(v)
        print(f"\nAfter insert {v}")
        print(b.print_tree())

    # ----- Übung 2: 8, 14, 2, 19, 23, 11, 5, 17, 28, 6, 4 -----
    print("\n\n=== Übung 2: zwei Splits ===")
    b = BTree(k=2)
    for v in [8, 14, 2, 19, 23, 11, 5, 17, 28, 6, 4]:
        b.insert(v)
        print(f"\nAfter insert {v}")
        print(b.print_tree())

    # ----- Übung 3: ausgehend vom Endzustand löschen 4, 19, 11 -----
    print("\n\n=== Übung 3: Löschen mit Redistribute / Merge ===")
    for v in [4, 19, 11]:
        b.delete(v)
        print(f"\nAfter delete {v}")
        print(b.print_tree())

    # Suche
    found, path = b.search(17)
    print("\nSearch(17) found:", found)
    for step in path:
        print(step)

    # DOT
    with open("btree.dot", "w", encoding="utf-8") as f:
        f.write(b.to_dot())
    print("\nWrote btree.dot")


if __name__ == "__main__":
    main()