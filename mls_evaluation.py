"""Kennzahlen und Verdikt der Hauptansicht: Regeln, Kern, Greedy, Lokalsuche, exakte Lösung über Reduktion und Zerlegung.

Aufwand wird in Knoten, Adjazenzzugriffen und Zellen gezählt, nie in Sekunden. Die Suche bekommt immer dasselbe Zufalls-Seed (SEARCH_SEED): gleiche Einstellungen, gleiches Ergebnis."""

import heapq
from dataclasses import dataclass

import mls_bipartite as B
import mls_constants as C
import mls_exact as X
import mls_reductions as R
import mls_scenario as S
import mls_search as Q


@dataclass(frozen=True)
class Settings:
    net: str = C.DEFAULT_NET
    n: int = C.DEFAULT_N
    par: int = C.DEFAULT_PAR
    seed: int = C.DEFAULT_SEED
    rules: str = C.DEFAULT_RULESET
    iters: int = C.DEFAULT_ITER


@dataclass(frozen=True)
class ExactResult:
    status: str                # "exact" (Regeln und Zerlegung) | "koenig" (bipartit: n minus Matching) | "too_wide" | "over_budget"
    value: int | None          # α des Originals (Offset plus Wert des Kerns), sonst None
    solution: tuple            # eine größte unabhängige Menge des Originals, sonst ()
    width: int | None          # Min-Fill-Breite des Kerns (None, wenn nicht gerechnet)
    cells: int                 # berechnete Zellen
    predicted: int | None      # Summe 2^Beutel vor dem Rechnen


@dataclass(frozen=True)
class Analysis:
    graph: S.Graph
    rules: tuple
    red: R.Reduction
    greedy: tuple              # Greedy auf dem ganzen Graphen
    full: Q.SearchResult       # Lokalsuche auf dem ganzen Graphen
    kernel_search: Q.SearchResult | None   # Lokalsuche auf dem Kern (None bei leerem Kern)
    lifted: tuple              # Lösung des Originals aus der Lokalsuche auf dem Kern (bei leerem Kern: die Lösung der Regeln)
    exact: ExactResult
    brute: int | None          # Brute Force (nur sehr kleine Graphen)
    valid: bool                # alle Lösungen am Original geprüft


def bounded_order(adj, limit=C.ORDER_WIDTH_LIMIT):
    """Min-Fill-Ordnung des Graphen, aber nur wenn die Min-Grad-Elimination mit Beuteln bis `limit` + 1 Knoten auskommt; sonst None („zu breit“, ohne die teure Min-Fill-Rechnung zu versuchen)."""
    n = len(adj)
    h = [set(a) for a in adj]
    heap = [(len(h[v]), v) for v in range(n)]
    heapq.heapify(heap)
    alive = set(range(n))
    while alive:
        d, v = heapq.heappop(heap)
        if v not in alive or d != len(h[v]):
            continue
        if d > limit:
            return None
        nb = sorted(h[v])
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                if nb[j] not in h[nb[i]]:
                    h[nb[i]].add(nb[j])
                    h[nb[j]].add(nb[i])
        for w in nb:
            h[w].discard(v)
            heapq.heappush(heap, (len(h[w]), w))
        h[v] = set()
        alive.discard(v)
    return X.min_fill_order(adj)


def exact_by_reduction_and_dp(adj, red, cell_budget=C.EXACT_CELL_BUDGET):
    """Exakt lösen: Regeln, dann die Zerlegung des Kerns (nur wenn schmal genug), dann die DP. Ist der Kern leer, ist die Lösung durch die Regeln gegeben. Gelingt die Zerlegung nicht, ist bei einem
    bipartiten Graphen α trotzdem bekannt (n minus größtes Matching, nur der Wert, keine Menge)."""
    kernel = red.kernel
    if not kernel:
        return ExactResult("exact", red.offset, R.lift(red, ()), 0, 0, 0)
    order = bounded_order(kernel)
    width = result = None
    if order is not None:
        width = X.eliminate(kernel, order).width
        result = X.max_weight_independent_set(kernel, (1,) * len(kernel), order, cell_budget)
        if not result.aborted:
            return ExactResult("exact", red.offset + result.value, R.lift(red, result.chosen), width, result.cells, result.predicted)
    alpha = B.bipartite_alpha(adj)
    if alpha is not None:
        return ExactResult("koenig", alpha, (), width, 0, None if result is None else result.predicted)
    if order is None:
        return ExactResult("too_wide", None, (), None, 0, None)
    return ExactResult("over_budget", None, (), width, 0, result.predicted)


def search_on_kernel(red, iterations, seed=C.SEARCH_SEED, checkpoints=()):
    """Lokalsuche auf dem Kern, Ergebnis ins Original gehoben. Gibt (SearchResult des Kerns, Lösung des Originals) zurück; bei leerem Kern (None, Lösung der Regeln)."""
    if not red.kernel:
        return None, R.lift(red, ())
    result = Q.iterated_local_search(red.kernel, iterations, seed, checkpoints)
    return result, R.lift(red, result.best)


def analyse(settings: Settings) -> Analysis:
    g = S.build_graph(settings.net, settings.n, settings.par, settings.seed)
    rules = C.RULESETS[settings.rules]
    red = R.reduce_graph(g.adj, rules)
    greedy = Q.greedy_min_degree(g.adj)
    full = Q.iterated_local_search(g.adj, settings.iters, C.SEARCH_SEED, C.CHECKPOINTS)
    kernel_search, lifted = search_on_kernel(red, settings.iters, C.SEARCH_SEED, C.CHECKPOINTS)
    exact = exact_by_reduction_and_dp(g.adj, red)
    brute = None
    if g.n <= C.BRUTE_MAX_N:
        brute = X.brute_force_mwis(g.adj, (1,) * g.n, C.BRUTE_MAX_N)[0]
    valid = all(R.is_independent(g.adj, s) for s in (greedy, full.best, lifted, exact.solution))
    return Analysis(g, rules, red, greedy, full, kernel_search, lifted, exact, brute, valid)


def reference(a: Analysis):
    """Der beste bekannte Wert und ob er bewiesen ist: α, wenn die exakte Lösung gelang, sonst der beste Wert aller gefundenen Lösungen."""
    if a.exact.status in ("exact", "koenig"):
        return a.exact.value, True
    return max(len(a.greedy), a.full.size, len(a.lifted)), False


def below(value, ref):
    """Abstand unter dem Referenzwert in Prozent des Referenzwerts."""
    return 0.0 if not ref else 100.0 * (ref - value) / ref


def _i(x):
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _dec(x):
    """Zahl mit Komma, eine Nachkommastelle."""
    return f"{x:.1f}".replace(".", ",")


def verdict_main(a: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage als (Art, Text); rein: die App ruft st.<Art>(Text), der Test prüft jede Zahl im Text an handgesetzten Werten."""
    g, red = a.graph, a.red
    ref, proven = reference(a)
    search = (f"Die Lokalsuche auf dem ganzen Graphen findet {_i(a.full.size)} ({_dec(below(a.full.size, ref))} % unter dem {'Optimum' if proven else 'besten gefundenen Wert'}), "
              f"auf dem Kern {_i(len(a.lifted))} ({_dec(below(len(a.lifted), ref))} %), der Greedy {_i(len(a.greedy))} ({_dec(below(len(a.greedy), ref))} %).")
    if not red.kernel:
        return "success", f"Die Regeln lösen die Aufgabe vollständig: Kein Kern bleibt, α = **{_i(a.exact.value)}**, ohne Suche bewiesen. {search}"
    share = _dec(red.kernel_share)
    if a.exact.status == "koenig":
        return "info", (f"Die Regeln lassen {_i(len(red.kernel))} von {_i(g.n)} Knoten ({share} %) als Kern, für die Zerlegung ist er zu breit; der Graph ist aber bipartit, deshalb ist α = n − ν = **{_i(a.exact.value)}** "
                        f"exakt bekannt (Satz von König, größtes Matching). {search}")
    if a.exact.status == "exact":
        return "info", (f"Die Regeln lassen {_i(len(red.kernel))} von {_i(g.n)} Knoten ({share} %) als Kern; die Zerlegung des Kerns (Breite {a.exact.width}, {_i(a.exact.cells)} Zellen) löst ihn exakt: "
                        f"α = **{_i(a.exact.value)}**. {search}")
    reason = ("die Min-Grad-Breite des Kerns liegt über " + str(C.ORDER_WIDTH_LIMIT)) if a.exact.status == "too_wide" else f"die Zerlegung (Breite {a.exact.width}) bräuchte {_i(a.exact.predicted)} Zellen, erlaubt sind {_i(C.EXACT_CELL_BUDGET)}"
    return "warning", (f"Die Regeln lassen {_i(len(red.kernel))} von {_i(g.n)} Knoten ({share} %) als Kern; exakt ist er nicht lösbar ({reason}). Der beste gefundene Wert ist **{_i(ref)}** (nicht bewiesen). {search}")
