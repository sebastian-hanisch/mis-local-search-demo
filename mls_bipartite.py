"""Bipartite Graphen: Zweifärbung und größtes Matching (Hopcroft-Karp). Für bipartite Graphen gilt α = n − ν (Satz von König: ν = Größe eines größten Matchings, n − ν = Größe einer größten
unabhängigen Menge), das liefert für Raster einen exakten Vergleichswert ohne Zerlegung."""

from collections import deque


def two_colouring(adj):
    """Zweifärbung (Farbe 0 oder 1 je Knoten) oder None, wenn der Graph einen ungeraden Kreis enthält."""
    n = len(adj)
    colour = [-1] * n
    for s in range(n):
        if colour[s] >= 0:
            continue
        colour[s] = 0
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in sorted(adj[x]):
                if colour[y] < 0:
                    colour[y] = 1 - colour[x]
                    queue.append(y)
                elif colour[y] == colour[x]:
                    return None
    return colour


def maximum_matching_size(adj, colour):
    """Größe eines größten Matchings eines bipartiten Graphen (Hopcroft-Karp: abwechselnd Breitensuche der kürzesten erweiternden Wege und Tiefensuche entlang der Schichten, iterativ)."""
    left = [v for v in range(len(adj)) if colour[v] == 0]
    match = {}                                  # Knoten -> Partner (beide Seiten)
    size = 0
    while True:
        dist = {}
        queue = deque()
        for u in left:
            if u not in match:
                dist[u] = 0
                queue.append(u)
        found = False
        while queue:
            u = queue.popleft()
            for v in sorted(adj[u]):
                w = match.get(v)
                if w is None:
                    found = True
                elif w not in dist:
                    dist[w] = dist[u] + 1
                    queue.append(w)
        if not found:
            return size
        pointer = {u: iter(sorted(adj[u])) for u in left}
        for root in left:
            if root in match:
                continue
            path, u = [], root                  # (linker Knoten, rechter Knoten) entlang des Weges
            stack = [root]
            while stack:
                u = stack[-1]
                advanced = False
                for v in pointer[u]:
                    w = match.get(v)
                    if w is None:
                        # erweiternder Weg: alle Paare auf dem Stapel umdrehen
                        path.append((u, v))
                        for a, b in path:
                            match[a], match[b] = b, a
                        size += 1
                        stack = []
                        advanced = True
                        break
                    if dist.get(w) == dist[u] + 1:
                        path.append((u, v))
                        stack.append(w)
                        advanced = True
                        break
                if not advanced:
                    dist[u] = -1                # Sackgasse
                    stack.pop()
                    if path:
                        path.pop()


def bipartite_alpha(adj):
    """α eines bipartiten Graphen als n − ν; None, wenn der Graph nicht bipartit ist."""
    colour = two_colouring(adj)
    if colour is None:
        return None
    return len(adj) - maximum_matching_size(adj, colour)
