"""Die fünf Experimente: Reduktionskraft über Netzfamilien, Reduktion + Zerlegung auf Toronto, Lokalsuche gegen den exakten Wert, Lokalsuche auf dem Kern gegen das ganze Netz und die Ablation der Regeln.

Jede Funktion rechnet auf festen Instanzen und gibt Zeilen (Wörterbücher) zurück; die Verdikte stehen darunter und sind rein (Art, Text). Aufwand in Knoten, Zellen und Adjazenzzugriffen, nie in Sekunden."""

import mls_constants as C
import mls_evaluation as ev
import mls_exact as X
import mls_reductions as R
import mls_scenario as S
import mls_search as Q
from mls_evaluation import _dec, _i, below

SEED = C.FAMILY_SEED

FAMILY_SPECS = (
    ("Toronto, ganzer Ausschnitt", "Straßen", lambda: S.toronto_graph(S.toronto_size(), 0, SEED)),
    ("Toronto, 2 000 Kreuzungen", "Straßen", lambda: S.toronto_graph(2000, 0, SEED)),
    ("Zufall, mittlerer Grad 3", "dünn", lambda: S.random_graph(2000, 4, SEED)),
    ("Skalenfrei, 2 Kanten je Knoten", "dünn", lambda: S.scalefree_graph(2000, 8, SEED)),
    ("Skalenfrei, 3 Kanten je Knoten", "dünn", lambda: S.scalefree_graph(2000, 16, SEED)),
    ("Zufall, mittlerer Grad 4,5", "mittel", lambda: S.random_graph(2000, 10, SEED)),
    ("King-Graph 20×20", "Raster", lambda: S.king_graph(400, 0, SEED)),
    ("Gitter 40×40", "Raster", lambda: S.grid_graph(1600, 0, SEED)),
    ("Dreiecksgitter 30×30", "Raster", lambda: S.tri_graph(900, 0, SEED)),
    ("3-regulär, n = 500", "regulär", lambda: S.regular_graph(500, 0, SEED)),
)


# --- Experiment 1: Reduktionskraft ---------------------------------------------------------------------------------------------------------------

def family_rows(rules=C.RULESETS[C.DEFAULT_RULESET]):
    rows = []
    for name, group, build in FAMILY_SPECS:
        g = build()
        red = R.reduce_graph(g.adj, rules)
        rows.append({"name": name, "group": group, "n": g.n, "m": g.m, "kernel": len(red.kernel), "share": red.kernel_share, "offset": red.offset, "counts": dict(red.counts)})
    return rows


def verdict_families(rows):
    empty = [r for r in rows if r["kernel"] == 0]
    full = [r for r in rows if r["share"] >= 90]
    best = min((r for r in rows if r["kernel"] > 0), key=lambda r: r["share"])
    worst = max(rows, key=lambda r: r["share"])
    folds = sum(r["counts"]["fold"] for r in rows)
    text = (f"Bei **{len(empty)} von {len(rows)}** Netzen bleibt kein Kern: Die Regeln lösen sie vollständig ({'; '.join(r['name'] for r in empty)}). "
            f"Am anderen Ende steht „{worst['name']}“ mit {_dec(worst['share'])} % der Knoten im Kern; bei {len(full)} Netzen sind es mindestens 90 %. "
            f"Von den Netzen mit Kern lässt „{best['name']}“ den kleinsten ({_dec(best['share'])} %). Die Faltung greift in diesen Netzen insgesamt {_i(folds)}-mal.")
    return ("success" if len(empty) * 3 >= len(rows) else "info"), text


# --- Experiment 2: Reduktion + Zerlegung auf Toronto -----------------------------------------------------------------------------------------------

def toronto_rows(ns=C.TORONTO_NS):
    rows = []
    for n in tuple(ns) + (S.toronto_size(),):
        g = S.toronto_graph(n, 0, SEED)
        red = R.reduce_graph(g.adj)
        full_width = X.eliminate(g.adj, X.min_fill_order(g.adj)).width
        exact = ev.exact_by_reduction_and_dp(g.adj, red)
        rows.append({"n": g.n, "m": g.m, "full_width": full_width, "kernel": len(red.kernel), "kernel_width": exact.width, "cells": exact.cells, "alpha": exact.value, "status": exact.status})
    return rows


def verdict_toronto(rows):
    last = rows[-1]
    solved = [r for r in rows if r["status"] == "exact"]
    text = (f"Mit den Regeln fällt die Breite des ganzen Ausschnitts ({_i(last['n'])} Kreuzungen) von {last['full_width']} auf {last['kernel_width']} (Kern {_i(last['kernel'])} Knoten); "
            f"die Zerlegung des Kerns löst ihn mit {_i(last['cells'])} Zellen exakt: α = **{_i(last['alpha'])}**. "
            f"{len(solved)} von {len(rows)} Ausschnitten werden exakt gelöst; ohne Regeln liegt die Breite des ganzen Ausschnitts über dem, was die DP in Python noch rechnet (Zellbudget {_i(C.EXACT_CELL_BUDGET)}).")
    return ("success" if last["status"] == "exact" else "warning"), text


# --- Experiment 3: Lokalsuche gegen exakt ----------------------------------------------------------------------------------------------------------

SEARCH_SPECS = FAMILY_SPECS + (("Dreiecksgitter 12×12", "Raster", lambda: S.tri_graph(144, 0, SEED)),)


def search_rows(iterations=C.SEARCH_ITERATIONS, checkpoints=C.CHECKPOINTS):
    rows = []
    for name, group, build in SEARCH_SPECS:
        g = build()
        red = R.reduce_graph(g.adj)
        exact = ev.exact_by_reduction_and_dp(g.adj, red)
        greedy = len(Q.greedy_min_degree(g.adj))
        full = Q.iterated_local_search(g.adj, iterations, C.SEARCH_SEED, checkpoints)
        kernel_result, lifted = ev.search_on_kernel(red, iterations, C.SEARCH_SEED, checkpoints)
        best_found = max(full.size, len(lifted), greedy)
        if exact.status in ("exact", "koenig"):
            ref, proven = exact.value, True
        else:
            ref, proven = best_found, False
        rows.append({"name": name, "group": group, "n": g.n, "m": g.m, "ref": ref, "proven": proven, "source": exact.status, "greedy": greedy, "curve": dict(full.curve), "size": full.size, "ops": full.ops,
                     "kernel_size": len(lifted), "kernel_n": len(red.kernel)})
    return rows


def verdict_search(rows):
    proven = [r for r in rows if r["proven"]]
    worst = max(rows, key=lambda r: below(r["size"], r["ref"]))
    exact_hit = [r for r in proven if r["size"] == r["ref"]]
    greedy_gap = max(rows, key=lambda r: below(r["greedy"], r["ref"]))
    text = (f"Nach {_i(C.SEARCH_ITERATIONS)} Iterationen liegt die Lokalsuche auf dem ganzen Netz höchstens {_dec(below(worst['size'], worst['ref']))} % unter dem Vergleichswert („{worst['name']}“); "
            f"bei {len(exact_hit)} von {len(proven)} Netzen mit bewiesenem Optimum trifft sie es genau. Der Greedy liegt dagegen bis zu {_dec(below(greedy_gap['greedy'], greedy_gap['ref']))} % darunter („{greedy_gap['name']}“). "
            f"Bei {len(rows) - len(proven)} Netzen ist der Vergleichswert nur der beste gefundene Wert, nicht bewiesen.")
    return "info", text


# --- Experiment 4: Lokalsuche auf dem Kern gegen das ganze Netz --------------------------------------------------------------------------------------

def kernel_vs_full_rows(rows=None):
    """Aus den Zeilen des Experiments 3: je Netz mit Kern die Größe der Lokalsuche auf dem ganzen Netz gegen die auf dem Kern (beide nach derselben Zahl Iterationen)."""
    rows = rows if rows is not None else search_rows()
    return [{"name": r["name"], "kernel_n": r["kernel_n"], "n": r["n"], "full": r["size"], "kernel": r["kernel_size"], "ref": r["ref"], "proven": r["proven"]} for r in rows if r["kernel_n"] > 0]


def verdict_kernel_vs_full(rows):
    better = [r for r in rows if r["kernel"] > r["full"]]
    worse = [r for r in rows if r["kernel"] < r["full"]]
    top = max(rows, key=lambda r: r["kernel"] - r["full"])
    return "info", (f"Bei gleicher Iterationszahl ({_i(C.SEARCH_ITERATIONS)}) erreicht die Lokalsuche auf dem Kern bei {len(better)} von {len(rows)} Netzen mehr als auf dem ganzen Netz, bei {len(worse)} weniger; "
                    f"der größte Vorsprung ist {_i(top['kernel'] - top['full'])} ({top['name']}: {_i(top['kernel'])} gegen {_i(top['full'])}). Wo die Regeln nichts verkleinern, sind beide gleich.")


# --- Experiment 5: Ablation -------------------------------------------------------------------------------------------------------------------------

ABLATION_INSTANCES = (
    ("Toronto, 2 000 Kreuzungen", lambda: S.toronto_graph(2000, 0, SEED)),
    ("Zufall, mittlerer Grad 3", lambda: S.random_graph(2000, 4, SEED)),
    ("Skalenfrei, 3 Kanten je Knoten", lambda: S.scalefree_graph(2000, 16, SEED)),
    ("King-Graph 20×20", lambda: S.king_graph(400, 0, SEED)),
    ("Zufall, mittlerer Grad 4,5", lambda: S.random_graph(2000, 10, SEED)),
)
ABLATIONS = (
    ("alle fünf", C.RULESETS["all"]),
    ("ohne Grad 1", ("degree0", "triangle", "fold", "domination")),
    ("ohne Dreieck", ("degree0", "degree1", "fold", "domination")),
    ("ohne Faltung", C.RULESETS["no_fold"]),
    ("ohne Dominanz", C.RULESETS["no_domination"]),
    ("ohne Dominanz und Grad 1", ("degree0", "triangle", "fold")),
    ("ohne Dominanz und Dreieck", ("degree0", "degree1", "fold")),
    ("nur Grad 0 und 1", C.RULESETS["basic"]),
)


def ablation_rows():
    rows = []
    for name, build in ABLATION_INSTANCES:
        g = build()
        for label, rules in ABLATIONS:
            red = R.reduce_graph(g.adj, rules)
            rows.append({"instance": name, "n": g.n, "set": label, "kernel": len(red.kernel), "offset": red.offset})
    return rows


def _k(rows, instance, label):
    return next(r["kernel"] for r in rows if r["instance"] == instance and r["set"] == label)


def verdict_ablation(rows):
    names = [name for name, _ in ABLATION_INSTANCES]
    fold_matters = [n for n in names if _k(rows, n, "ohne Faltung") > _k(rows, n, "alle fünf")]
    dom_matters = [n for n in names if _k(rows, n, "ohne Dominanz") > _k(rows, n, "alle fünf")]
    redundant = [n for n in names if _k(rows, n, "ohne Grad 1") == _k(rows, n, "alle fünf") and _k(rows, n, "ohne Dreieck") == _k(rows, n, "alle fünf")]
    king, tor = "King-Graph 20×20", "Toronto, 2 000 Kreuzungen"
    return "info", (f"Ohne die Faltung wird der Kern bei {len(fold_matters)} von {len(names)} Netzen größer, ohne die Dominanz bei {len(dom_matters)}; im King-Graphen wirkt nur die Dominanz (Kern {_i(_k(rows, king, 'alle fünf'))} mit, "
                    f"{_i(_k(rows, king, 'ohne Dominanz'))} ohne sie). **Grad 1 und Dreieck sind Sonderfälle der Dominanz:** Mit ihr ändert das Weglassen einer der beiden Regeln den Kern bei {len(redundant)} von {len(names)} Netzen nicht; ohne sie wächst der Kern des Toronto-Ausschnitts "
                    f"von {_i(_k(rows, tor, 'ohne Dominanz'))} auf {_i(_k(rows, tor, 'ohne Dominanz und Grad 1'))} Knoten ohne Grad 1 und auf {_i(_k(rows, tor, 'ohne Dominanz und Dreieck'))} ohne Dreieck. "
                    f"Gegenüber „nur Grad 0 und 1“ ({_i(_k(rows, tor, 'nur Grad 0 und 1'))} Knoten) verkleinern die übrigen Regeln den Kern auf {_i(_k(rows, tor, 'alle fünf'))}.")
