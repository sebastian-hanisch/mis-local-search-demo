"""Szenarien: Konfliktgraphen, auf denen die größte unabhängige Menge gesucht wird (Zufall, skalenfrei, Gitter, Dreiecksgitter, King-Graph, 3-regulär, Toronto) und feste Vergleichsgraphen.

Ein Graph ist eine Adjazenzliste `adj` (Tupel von Mengen; Knoten 0 .. n-1, ungerichtet, ohne Schleifen) plus Anzeige-Positionen; Kante = „dürfen nicht zusammen verladen werden“. Der Regler `par`
bedeutet je Netztyp etwas anderes (siehe NET_HELP in mls_constants.py); alle Knoten bleiben erhalten. Der Zufall kommt immer aus `random.Random(seed)`."""

import json
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import mls_constants as C

DATA = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class Graph:
    n: int
    adj: tuple          # adj[v] = frozenset der Nachbarn von v
    positions: tuple    # (x, y) je Knoten
    labels: tuple       # Hover-Text je Knoten
    kind: str

    @property
    def m(self):
        return sum(len(a) for a in self.adj) // 2

    def edges(self):
        return [(u, v) for u in range(self.n) for v in sorted(self.adj[u]) if u < v]


def adjacency_from_edges(n, edges):
    """Adjazenzliste aus ungerichteten Kanten; Schleifen und doppelte Kanten werden ignoriert."""
    adj = [set() for _ in range(n)]
    for u, v in edges:
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return tuple(frozenset(a) for a in adj)


def edges_of(adj):
    return [(u, v) for u in range(len(adj)) for v in sorted(adj[u]) if u < v]


def circle_positions(n):
    """Knoten 0 .. n-1 der Reihe nach auf einen Kreis (Radius 1, Start oben)."""
    return tuple((round(math.cos(math.pi / 2 - 2 * math.pi * i / max(n, 1)), 6), round(math.sin(math.pi / 2 - 2 * math.pi * i / max(n, 1)), 6)) for i in range(n))


def normalize(points):
    """Punkte in das Quadrat [-1, 1] einpassen, Seitenverhältnis erhalten."""
    if not points:
        return ()
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 or 1.0
    return tuple((round((x - cx) / half, 6), round((y - cy) / half, 6)) for x, y in points)


def _labels(n, prefix="Sendung"):
    return tuple(f"{prefix} {i + 1}" for i in range(n))


def _family(adj, labels=None):
    n = len(adj)
    return Graph(n, adj, circle_positions(n), labels or _labels(n), "family")


def _remove_pct(edges, pct, rng):
    """Zufällig `pct` Prozent der Kanten sperren (entfernen); die Auswahl ist eine feste Stichprobe."""
    k = round(len(edges) * pct / 100.0)
    drop = set(rng.sample(range(len(edges)), min(k, len(edges)))) if k else set()
    return [e for i, e in enumerate(edges) if i not in drop]


def mean_degree(par):
    """Mittlerer Grad der Netztypen Zufall und skalenfrei: 2 plus Parameter durch 4."""
    return 2.0 + par / 4.0


# --- Netztypen --------------------------------------------------------------------------------------------------------------------------------------

def random_graph(n, par, seed):
    """G(n, p) mit p = mittlerer Grad / (n − 1); jedes Paar unabhängig."""
    rng = random.Random(seed)
    p = min(1.0, mean_degree(par) / max(n - 1, 1))
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
    return Graph(n, adjacency_from_edges(n, edges), circle_positions(n), _labels(n), "random")


def random_graph_p(n, p_pct, seed):
    """G(n, p) mit p in Prozent (für die Vergleiche auf kleinen Graphen); gibt nur die Adjazenzliste zurück."""
    rng = random.Random(seed)
    return adjacency_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p_pct / 100.0])


def scalefree_m(par):
    return max(1, round(mean_degree(par) / 2))


def scalefree_graph(n, par, seed):
    """Barabási–Albert: jeder neue Knoten verbindet sich mit m verschiedenen früheren Knoten, gewählt proportional zum Grad (Wiederholungsliste); die ersten m Knoten sind das Startziel."""
    m = min(scalefree_m(par), max(n - 1, 1))
    rng = random.Random(seed)
    edges, targets, repeated = [], list(range(m)), []
    for v in range(m, n):
        edges.extend((v, t) for t in targets)
        repeated.extend(targets)
        repeated.extend([v] * m)
        chosen = set()
        while len(chosen) < m:
            chosen.add(repeated[rng.randrange(len(repeated))])
        targets = sorted(chosen)
    return Graph(n, adjacency_from_edges(n, edges), circle_positions(n), _labels(n), "scalefree")


@lru_cache(maxsize=1)
def _toronto_payload():
    return json.loads((DATA / "toronto_campus.json").read_text(encoding="utf-8"))


def toronto_size():
    """Zahl der Kreuzungen des Toronto-Ausschnitts."""
    return len(_toronto_payload()["nodes_xy_m"])


@lru_cache(maxsize=1)
def _toronto_edges():
    """Ungerichtete einfache Kanten des Ausschnitts (aus den gerichteten Bögen)."""
    return tuple(sorted({(min(u, v), max(u, v)) for u, v, _ in _toronto_payload()["arcs"] if u != v}))


def toronto_graph(n, par, seed):
    """Die n Kreuzungen, die dem Mittelpunkt des Ausschnitts am nächsten liegen (Knoten nach Abstand nummeriert), mit allen Straßen zwischen ihnen; der Parameter sperrt zufällig `par` Prozent der Kanten."""
    xy = _toronto_payload()["nodes_xy_m"]
    n = min(n, len(xy))
    keep = sorted(range(len(xy)), key=lambda i: (math.hypot(xy[i][0], xy[i][1]), i))[:n]
    index = {old: new for new, old in enumerate(keep)}
    edges = [(index[u], index[v]) for u, v in _toronto_edges() if u in index and v in index]
    rng = random.Random(seed)
    edges = _remove_pct(edges, par, rng)
    pos = normalize(tuple(tuple(xy[old]) for old in keep))
    labels = tuple(f"Kreuzung {i + 1}: {math.hypot(xy[old][0], xy[old][1]):.0f} m vom Mittelpunkt" for i, old in enumerate(keep))
    return Graph(n, adjacency_from_edges(n, edges), pos, labels, "toronto")


def grid_side(n):
    """Seitenlänge des Rasters mit ungefähr n Knoten."""
    return max(2, round(math.sqrt(n)))


def lattice_edges(k, diagonals):
    """Kanten eines k × k-Rasters; `diagonals`: "none" (Gitter), "tri" (eine Diagonale je Zelle: Dreiecksgitter) oder "king" (beide Diagonalen)."""
    edges = []
    for r in range(k):
        for c in range(k):
            v = r * k + c
            if c + 1 < k:
                edges.append((v, v + 1))
            if r + 1 < k:
                edges.append((v, v + k))
    for r in range(k - 1):
        for c in range(k - 1):
            v = r * k + c
            if diagonals in ("tri", "king"):
                edges.append((v, v + k + 1))
            if diagonals == "king":
                edges.append((v + 1, v + k))
    return edges


def lattice_graph(n, par, seed, diagonals):
    """Raster mit k = round(√n); der Parameter sperrt zufällig `par` Prozent der Kanten."""
    k = grid_side(n)
    rng = random.Random(seed)
    edges = _remove_pct(lattice_edges(k, diagonals), par, rng)
    pos = normalize(tuple((c, -r) for r in range(k) for c in range(k)))
    return Graph(k * k, adjacency_from_edges(k * k, edges), pos, _labels(k * k), {"none": "grid", "tri": "tri", "king": "king"}[diagonals])


def grid_graph(n, par, seed):
    return lattice_graph(n, par, seed, "none")


def tri_graph(n, par, seed):
    return lattice_graph(n, par, seed, "tri")


def king_graph(n, par, seed):
    return lattice_graph(n, par, seed, "king")


def regular_edges(n, d, rng):
    """Zufällig d-regulärer Graph auf n Knoten (Paarungsmodell mit Wiederholung, bis keine Schleife und keine Doppelkante entsteht); n * d muss gerade sein."""
    if n * d % 2 or d >= n:
        raise ValueError("kein regulärer Graph mit diesen Parametern")
    while True:
        stubs = [v for v in range(n) for _ in range(d)]
        rng.shuffle(stubs)
        edges = {(min(a, b), max(a, b)) for a, b in zip(stubs[::2], stubs[1::2])}
        if len(edges) == n * d // 2 and all(a != b for a, b in edges):
            return sorted(edges)


def regular_graph(n, par, seed):
    """Zufällig 3-regulärer Graph auf n (bei ungeradem n: n − 1) Knoten, auf einem Kreis angeordnet; der Parameter sperrt zufällig `par` Prozent der Kanten."""
    n = max(4, n - n % 2)
    rng = random.Random(seed)
    edges = _remove_pct(regular_edges(n, 3, rng), par, rng)
    return Graph(n, adjacency_from_edges(n, edges), circle_positions(n), _labels(n), "regular")


def build_graph(net_type, n, par, seed):
    """Der Graph der Hauptansicht."""
    builders = {"random": random_graph, "scalefree": scalefree_graph, "regular": regular_graph, "grid": grid_graph, "tri": tri_graph, "king": king_graph, "toronto": toronto_graph}
    if net_type not in builders:
        raise ValueError(f"unbekannter Netztyp: {net_type}")
    return builders[net_type](n, par, seed)


# --- feste Vergleichsgraphen (Mini-Instanzen, von Hand gerechnet) ----------------------------------------------------------------------------------

def path_graph(k):
    return _family(adjacency_from_edges(k, [(i, i + 1) for i in range(k - 1)]))


def ring_graph(k):
    """Kreis C_k."""
    return _family(adjacency_from_edges(k, [(i, (i + 1) % k) for i in range(k)]))


def complete_graph(k):
    return _family(adjacency_from_edges(k, [(i, j) for i in range(k) for j in range(i + 1, k)]))


def star_graph(leaves):
    return _family(adjacency_from_edges(leaves + 1, [(0, i + 1) for i in range(leaves)]))


def triangle_with_pendant():
    """Dreieck 0-1-2 mit Pendel 3 an Knoten 2."""
    return _family(adjacency_from_edges(4, [(0, 1), (0, 2), (1, 2), (2, 3)]))


def petersen_graph():
    """Petersen-Graph: 10 Knoten, 15 Kanten, α = 4."""
    edges = [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]
    return _family(adjacency_from_edges(10, edges))
