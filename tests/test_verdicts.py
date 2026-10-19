"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen oder eine Analyse, nicht Seeds. Damit prüft der Test die Grenzen und jede genannte Zahl direkt."""

import dataclasses

import mls_constants as C
import mls_evaluation as ev
import mls_experiments as ex
import mls_search as Q


def _search(size):
    return Q.SearchResult(tuple(range(size)), size, {}, 0, 0, 0)


def _analysis(net="random", n=24, par=12, seed=5, **changes):
    a = ev.analyse(ev.Settings(net=net, n=n, par=par, seed=seed))
    return dataclasses.replace(a, **changes)


def test_number_formats_are_german():
    assert ev._i(1234567) == "1.234.567" and ev._i(12) == "12" and ev._dec(3.14159) == "3,1"


def test_below_and_reference():
    assert ev.below(98, 100) == 2.0 and ev.below(100, 100) == 0.0 and ev.below(5, 0) == 0.0
    a = _analysis()
    assert ev.reference(a) == (9, True)
    unproven = dataclasses.replace(a, exact=ev.ExactResult("too_wide", None, (), None, 0, None), greedy=(0,) * 8, full=_search(9), lifted=(0,) * 10)
    assert ev.reference(unproven) == (10, False)
    koenig = dataclasses.replace(a, exact=ev.ExactResult("koenig", 800, (), None, 0, None))
    assert ev.reference(koenig) == (800, True)


def test_main_verdict_solved_by_the_rules_alone():
    a = _analysis(net="random", n=16, par=4, seed=5)                              # Kern leer, α = 7
    kind, text = ev.verdict_main(a)
    assert kind == "success" and "Kein Kern bleibt, α = **7**, ohne Suche bewiesen." in text
    assert "Die Lokalsuche auf dem ganzen Graphen findet 7 (0,0 % unter dem Optimum), auf dem Kern 7 (0,0 %), der Greedy 7 (0,0 %)." in text


def test_main_verdict_numbers_come_from_the_analysis():
    a = _analysis(net="random", n=16, par=4, seed=5, greedy=(0,) * 5, full=_search(6), lifted=(0,) * 7)
    text = ev.verdict_main(a)[1]
    assert "findet 6 (14,3 % unter dem Optimum), auf dem Kern 7 (0,0 %), der Greedy 5 (28,6 %)" in text


def test_main_verdict_with_a_kernel_and_an_exact_dp():
    a = _analysis()                                                               # Lehrbeispiel: Kern 7 von 24 (29,2 %), Breite 3, 78 Zellen, α = 9
    kind, text = ev.verdict_main(a)
    assert kind == "info" and "7 von 24 Knoten (29,2 %) als Kern" in text and "Breite 3, 78 Zellen" in text and "α = **9**" in text


def test_main_verdict_with_a_koenig_value():
    a = _analysis(net="grid", n=1600, par=0)
    kind, text = ev.verdict_main(a)
    assert kind == "info" and "bipartit" in text and "α = n − ν = **800**" in text and "Satz von König" in text


def test_main_verdict_without_an_exact_value_is_a_warning():
    a = _analysis(net="regular", n=500, par=0)
    kind, text = ev.verdict_main(a)
    assert kind == "warning" and "exakt ist er nicht lösbar (die Min-Grad-Breite des Kerns liegt über 24)" in text and "(nicht bewiesen)" in text and "unter dem besten gefundenen Wert" in text
    over = dataclasses.replace(a, exact=ev.ExactResult("over_budget", None, (), 21, 0, 11_736_638))
    assert "die Zerlegung (Breite 21) bräuchte 11.736.638 Zellen, erlaubt sind 3.000.000" in ev.verdict_main(over)[1]


# --- Experiment-Verdikte -------------------------------------------------------------------------------------------------------------------------------

def _family(name, kernel, n=100, counts=None):
    return {"name": name, "group": "x", "n": n, "m": 150, "kernel": kernel, "share": 100.0 * kernel / n, "offset": n - kernel, "counts": counts or {"fold": 3}}


def test_family_verdict_counts_empty_kernels_and_names_the_extremes():
    rows = [_family("A", 0), _family("B", 0), _family("C", 50), _family("D", 95), _family("E", 100)]
    kind, text = ex.verdict_families(rows)
    assert kind == "success" and "**2 von 5**" in text and "(A; B)" in text and "„E“ mit 100,0 % der Knoten" in text and "mindestens 90 %" in text and "bei 2 Netzen" in text
    assert "kleinsten (50,0 %)" in text and "„C“" in text and "15-mal" in text
    kind, _ = ex.verdict_families([_family("A", 0), _family("B", 40), _family("C", 50), _family("D", 60)])
    assert kind == "info"                                                         # weniger als ein Drittel ohne Kern


def test_toronto_verdict():
    rows = [{"n": 1000, "m": 1, "full_width": 17, "kernel": 34, "kernel_width": 3, "cells": 440, "alpha": 500, "status": "exact"},
            {"n": 5072, "m": 2, "full_width": 50, "kernel": 1036, "kernel_width": 12, "cells": 223388, "alpha": 2448, "status": "exact"}]
    kind, text = ex.verdict_toronto(rows)
    assert kind == "success" and "(5.072 Kreuzungen) von 50 auf 12 (Kern 1.036 Knoten)" in text and "mit 223.388 Zellen exakt: α = **2.448**" in text and "2 von 2 Ausschnitten" in text
    rows[1].update(status="over_budget")
    kind, text = ex.verdict_toronto(rows)
    assert kind == "warning" and "1 von 2 Ausschnitten" in text


def _search_row(name, ref, proven, greedy, size, kernel_size=None, kernel_n=10):
    return {"name": name, "group": "x", "n": 100, "m": 150, "ref": ref, "proven": proven, "source": "exact", "greedy": greedy, "curve": {100: greedy, 1000: size, 20000: size}, "size": size, "ops": 1,
            "kernel_size": size if kernel_size is None else kernel_size, "kernel_n": kernel_n}


def test_search_verdict_names_the_worst_gap_the_exact_hits_and_the_greedy_gap():
    rows = [_search_row("A", 100, True, 90, 100), _search_row("B", 200, True, 150, 199), _search_row("C", 300, False, 270, 297)]
    kind, text = ex.verdict_search(rows)
    assert kind == "info" and "höchstens 1,0 % unter dem Vergleichswert („C“)" in text and "bei 1 von 2 Netzen mit bewiesenem Optimum trifft sie es genau" in text
    assert "Der Greedy liegt dagegen bis zu 25,0 % darunter („B“)" in text and "Bei 1 Netzen ist der Vergleichswert nur der beste gefundene Wert" in text


def test_kernel_vs_full_rows_and_verdict():
    rows3 = [_search_row("A", 100, True, 90, 90, kernel_size=100, kernel_n=50), _search_row("B", 200, True, 150, 200, kernel_n=0), _search_row("C", 300, True, 250, 295, kernel_size=290, kernel_n=70)]
    rows = ex.kernel_vs_full_rows(rows3)
    assert [r["name"] for r in rows] == ["A", "C"]                                # B hat keinen Kern
    kind, text = ex.verdict_kernel_vs_full(rows)
    assert kind == "info" and "bei 1 von 2 Netzen mehr als auf dem ganzen Netz, bei 1 weniger" in text and "der größte Vorsprung ist 10 (A: 100 gegen 90)" in text


def _abl(kernels):
    rows = []
    for name, _ in ex.ABLATION_INSTANCES:
        for i, (label, _) in enumerate(ex.ABLATIONS):
            rows.append({"instance": name, "n": 100, "set": label, "kernel": kernels[i], "offset": 0})
    return rows


def test_ablation_verdict():
    # Reihenfolge: alle fünf, ohne Grad 1, ohne Dreieck, ohne Faltung, ohne Dominanz, ohne Dominanz+Grad 1, ohne Dominanz+Dreieck, nur Grad 0 und 1
    kind, text = ex.verdict_ablation(_abl([10, 10, 10, 40, 30, 90, 60, 80]))
    assert kind == "info" and "bei 5 von 5 Netzen größer, ohne die Dominanz bei 5" in text and "Kern 10 mit, 30 ohne sie" in text and "bei 5 von 5 Netzen nicht" in text
    assert "von 30 auf 90 Knoten ohne Grad 1 und auf 60 ohne Dreieck" in text and "„nur Grad 0 und 1“ (80 Knoten) verkleinern die übrigen Regeln den Kern auf 10" in text
    kind, text = ex.verdict_ablation(_abl([10, 12, 10, 10, 10, 90, 60, 80]))
    assert "bei 0 von 5 Netzen größer, ohne die Dominanz bei 0" in text and "bei 0 von 5 Netzen nicht" in text


def test_ablation_sets_are_named_and_complete():
    assert [label for label, _ in ex.ABLATIONS][0] == "alle fünf" and len(ex.ABLATIONS) == 8 and set(C.RULESETS["all"]) == {"degree0", "degree1", "triangle", "fold", "domination"}
