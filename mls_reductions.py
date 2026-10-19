"""Reduktionsregeln für die größte unabhängige Menge (eine Regel = eine Funktion) mit Rücklift.

Jede Regel verkleinert den Graphen so, dass sich α (die Größe einer größten unabhängigen Menge) berechenbar ändert; der Rücklift setzt aus einer Lösung des Kerns eine Lösung des Originals zusammen.

  degree0    Knoten ohne Nachbarn: in die Lösung
  degree1    Knoten v mit einem Nachbarn u: v in die Lösung, u raus (α(G) = α(G − N[v]) + 1)
  triangle   Knoten v mit zwei benachbarten Nachbarn: v in die Lösung, beide Nachbarn raus (v ist simplizial)
  fold       Knoten v mit zwei nicht benachbarten Nachbarn u, w: v, u, w werden zu einem neuen Knoten x verschmolzen, dessen Nachbarn die von u und w sind;
             α(G) = α(G') + 1, und x in der Lösung von G' heißt u und w in G, sonst v (Rücklift)
  domination sind u, v benachbart mit N[v] ⊆ N[u], kann u gelöscht werden (α ändert sich nicht)

Zustand: lebender Graph (Knoten -> Menge der Nachbarn), Stapel der Schritte für den Rücklift, Offset (so viele Knoten sind schon fest) und Protokoll. Neue Knoten der Faltung bekommen die Nummern ab n.
Gleichstände: immer der kleinste Knoten zuerst; das Ergebnis ist deterministisch."""

from dataclasses import dataclass, field

RULES = ("degree0", "degree1", "triangle", "fold", "domination")
RULE_NAMES = {
    "degree0": "Grad 0 (Knoten ohne Nachbarn)",
    "degree1": "Grad 1 (Knoten mit einem Nachbarn)",
    "triangle": "Dreieck (Grad 2, Nachbarn verbunden)",
    "fold": "Faltung (Grad 2, Nachbarn nicht verbunden)",
    "domination": "Dominanz (N[v] ⊆ N[u])",
}
LOG_CAP = 400                 # so viele Schritte stehen höchstens im Protokoll


@dataclass
class State:
    g: dict                                     # lebender Graph: Knoten -> Menge der Nachbarn
    n: int                                      # Zahl der Knoten des Originals
    next_id: int = 0
    stack: list = field(default_factory=list)   # ("take", v) | ("fold", v, u, w, x) in der Reihenfolge der Schritte
    offset: int = 0                             # Zahl der Knoten, die die Regeln schon festgelegt haben
    counts: dict = field(default_factory=lambda: {r: 0 for r in RULES})
    log: list = field(default_factory=list)

    def note(self, rule, text):
        if len(self.log) < LOG_CAP:
            self.log.append({"step": len(self.log) + 1, "rule": rule, "text": text})

    def remove(self, v):
        for w in self.g[v]:
            self.g[w].discard(v)
        del self.g[v]

    def take(self, v):
        """v in die Lösung: v und alle seine Nachbarn verlassen den Graphen."""
        for w in list(self.g[v]):
            self.remove(w)
        self.remove(v)
        self.stack.append(("take", v))
        self.offset += 1


def initial_state(adj):
    n = len(adj)
    return State({v: set(adj[v]) for v in range(n)}, n, n)


def _name(v, n):
    """Anzeigename: Originalknoten als 1-basierte Nummer, gefaltete Knoten als F plus Nummer."""
    return str(v + 1) if v < n else f"F{v - n + 1}"


# --- die Regeln: jede wendet ihre Regel einmal auf alle passenden Stellen an und gibt die Zahl der Anwendungen zurück -------------------------------

def rule_degree0(st):
    applied = 0
    for v in sorted(st.g):
        if v in st.g and not st.g[v]:
            st.take(v)
            st.counts["degree0"] += 1
            st.note("degree0", f"Knoten {_name(v, st.n)} hat keinen Nachbarn: in die Lösung")
            applied += 1
    return applied


def rule_degree1(st):
    applied = 0
    for v in sorted(st.g):
        if v in st.g and len(st.g[v]) == 1:
            (u,) = st.g[v]
            st.take(v)
            st.counts["degree1"] += 1
            st.note("degree1", f"Knoten {_name(v, st.n)} hat nur den Nachbarn {_name(u, st.n)}: {_name(v, st.n)} in die Lösung, {_name(u, st.n)} raus")
            applied += 1
    return applied


def rule_triangle(st):
    applied = 0
    for v in sorted(st.g):
        if v in st.g and len(st.g[v]) == 2:
            u, w = sorted(st.g[v])
            if w in st.g[u]:
                st.take(v)
                st.counts["triangle"] += 1
                st.note("triangle", f"Knoten {_name(v, st.n)} und seine Nachbarn {_name(u, st.n)}, {_name(w, st.n)} bilden ein Dreieck: {_name(v, st.n)} in die Lösung")
                applied += 1
    return applied


def rule_fold(st):
    applied = 0
    for v in sorted(st.g):
        if v in st.g and len(st.g[v]) == 2:
            u, w = sorted(st.g[v])
            if w in st.g[u]:
                continue
            x = st.next_id
            st.next_id += 1
            nb = (st.g[u] | st.g[w]) - {v}
            for y in (v, u, w):
                st.remove(y)
            st.g[x] = set(nb)
            for y in nb:
                st.g[y].add(x)
            st.stack.append(("fold", v, u, w, x))
            st.offset += 1
            st.counts["fold"] += 1
            st.note("fold", f"Knoten {_name(v, st.n)} mit den nicht benachbarten Nachbarn {_name(u, st.n)}, {_name(w, st.n)}: zu {_name(x, st.n)} gefaltet")
            applied += 1
    return applied


def rule_domination(st):
    applied = 0
    for v in sorted(st.g):
        if v not in st.g:
            continue
        for u in sorted(st.g[v]):
            if u in st.g and len(st.g[u]) >= len(st.g[v]) and (st.g[v] | {v}) <= (st.g[u] | {u}):
                st.remove(u)
                st.counts["domination"] += 1
                st.note("domination", f"N[{_name(v, st.n)}] ⊆ N[{_name(u, st.n)}]: Knoten {_name(u, st.n)} entfällt")
                applied += 1
    return applied


RULE_FUNCTIONS = {"degree0": rule_degree0, "degree1": rule_degree1, "triangle": rule_triangle, "fold": rule_fold, "domination": rule_domination}


@dataclass(frozen=True)
class Reduction:
    n: int
    rules: tuple
    offset: int               # Knoten, die die Regeln festgelegt haben (α(G) = offset + α(Kern))
    kernel: tuple             # Adjazenzliste des Kerns (frozensets, neu nummeriert 0 .. k-1)
    kernel_ids: tuple         # Knotennummer im reduzierten Graphen (< n: Originalknoten, sonst gefaltet) je Kernknoten
    stack: tuple              # Schritte für den Rücklift
    counts: dict
    log: tuple
    m: int                    # Kanten des Originals

    @property
    def kernel_share(self):
        return 100.0 * len(self.kernel) / self.n if self.n else 0.0


def reduce_graph(adj, rules=RULES):
    """Regeln bis zum Fixpunkt. Nach einer Anwendung beginnt die Runde von vorn (Reihenfolge Grad 0, Grad 1, Dreieck, Faltung, Dominanz), damit die einfachen Regeln Vorrang haben."""
    st = initial_state(adj)
    rules = tuple(r for r in RULES if r in rules)
    while True:
        for name in rules:
            if RULE_FUNCTIONS[name](st):
                break
        else:
            break
    ids = tuple(sorted(st.g))
    index = {v: i for i, v in enumerate(ids)}
    kernel = tuple(frozenset(index[w] for w in st.g[v]) for v in ids)
    return Reduction(st.n, rules, st.offset, kernel, ids, tuple(st.stack), dict(st.counts), tuple(st.log), sum(len(a) for a in adj) // 2)


def lift(red, kernel_solution):
    """Lösung des Originals aus einer unabhängigen Menge des Kerns (Kernknoten-Nummern): zuerst die Kernlösung in Knotennummern des reduzierten Graphen übersetzen, dann die Schritte in
    umgekehrter Reihenfolge auflösen (genommene Knoten dazu; bei einer Faltung ersetzt der gefaltete Knoten die beiden äußeren Nachbarn, sonst kommt der mittlere Knoten dazu)."""
    sol = {red.kernel_ids[i] for i in kernel_solution}
    for step in reversed(red.stack):
        if step[0] == "take":
            sol.add(step[1])
        else:
            _, v, u, w, x = step
            if x in sol:
                sol.discard(x)
                sol.update((u, w))
            else:
                sol.add(v)
    return tuple(sorted(sol))


def is_independent(adj, vertices):
    s = set(vertices)
    return all(not (set(adj[v]) & s) for v in s)
