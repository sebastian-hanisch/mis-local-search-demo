"""Jede Zahl der README (Abschnitt Befunde) wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Alle Werte sind ganzzahlig oder Verhältnisse ganzer Zahlen und damit plattformunabhängig exakt; Zeiten stehen in keinem Test."""

import mls_constants as C
import mls_evaluation as ev
import mls_experiments as ex
import mls_reductions as R
import mls_scenario as S


def _preset(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def _row(rows, name, key="name"):
    return next(r for r in rows if r[key] == name)


# --- Standardfall und Presets ---------------------------------------------------------------------------------------------------------------------------

def test_default_case():
    a = ev.analyse(ev.Settings())
    assert (a.graph.n, a.graph.m) == (24, 57)
    assert a.red.counts == {"degree0": 0, "degree1": 0, "triangle": 1, "fold": 5, "domination": 4} and a.red.offset == 6
    assert len(a.red.kernel) == 7 and f"{a.red.kernel_share:.1f}" == "29.2"
    assert (a.exact.status, a.exact.value, a.exact.width, a.exact.cells) == ("exact", 9, 3, 78) and len(a.greedy) == 8 and a.valid


def test_presets():
    toronto = _preset("Toronto: das ganze Netz")
    assert (toronto.graph.n, toronto.graph.m, len(toronto.red.kernel), toronto.red.offset, toronto.exact.value, toronto.exact.width, toronto.exact.cells) == (5072, 7621, 1036, 1996, 2448, 12, 223388)
    assert (len(toronto.greedy), toronto.full.size, len(toronto.lifted)) == (2308, 2428, 2445)
    thin = _preset("Dünn: die Regeln lösen alles")
    assert (thin.graph.n, thin.graph.m, len(thin.red.kernel), thin.exact.value, len(thin.greedy)) == (2000, 2955, 0, 1073, 1026)
    raster = _preset("Raster: die Regeln tun nichts")
    assert (raster.graph.m, len(raster.red.kernel), raster.exact.status, raster.exact.value, len(raster.greedy), raster.full.size) == (3120, 1592, "koenig", 800, 762, 800)
    tri = _preset("Dreiecksgitter: die Suche braucht Zeit")
    assert (tri.graph.m, len(tri.red.kernel), tri.full.size, len(tri.lifted), len(tri.greedy), tri.exact.status) == (2581, 876, 283, 290, 227, "too_wide")
    reg = _preset("3-regulär: die Suche ohne Beweis")
    assert (reg.graph.m, len(reg.red.kernel), len(reg.greedy), reg.full.size, reg.exact.status) == (750, 500, 188, 222, "too_wide")
    king = _preset("King-Graph: nur die Dominanz")
    assert len(king.red.kernel) == 400
    assert len(ev.analyse(ev.Settings(**dict(C.PRESETS["King-Graph: nur die Dominanz"], rules="all"))).red.kernel) == 0


# --- Experiment 1 ---------------------------------------------------------------------------------------------------------------------------------------

def test_experiment_1_families():
    rows = ex.family_rows()
    assert len(rows) == 10 and sum(1 for r in rows if r["kernel"] == 0) == 4
    expected = {"Toronto, ganzer Ausschnitt": (5072, 7621, 1036, "20.4", 1996), "Toronto, 2 000 Kreuzungen": (2000, 2811, 52, "2.6", 969), "Zufall, mittlerer Grad 3": (2000, 3008, 0, "0.0", 1076),
                "Skalenfrei, 2 Kanten je Knoten": (2000, 3996, 0, "0.0", 1156), "Skalenfrei, 3 Kanten je Knoten": (2000, 5991, 0, "0.0", 1004), "Zufall, mittlerer Grad 4,5": (2000, 4473, 1172, "58.6", 424),
                "King-Graph 20×20": (400, 1482, 0, "0.0", 100), "Gitter 40×40": (1600, 3120, 1592, "99.5", 4), "Dreiecksgitter 30×30": (900, 2581, 876, "97.3", 8), "3-regulär, n = 500": (500, 750, 500, "100.0", 0)}
    for name, (n, m, kernel, share, offset) in expected.items():
        r = _row(rows, name)
        assert (r["n"], r["m"], r["kernel"], f"{r['share']:.1f}", r["offset"]) == (n, m, kernel, share, offset), name
    assert sum(r["counts"]["fold"] for r in rows) == 1680
    assert _row(rows, "Toronto, ganzer Ausschnitt")["counts"]["fold"] == 740


def test_experiment_1_rules_agree_with_the_vormessung_kernels():
    """Die Kerngrößen der Vormessung (andere Regelreihenfolge) stimmen überein; nur die Regelzähler weichen ab."""
    rows = ex.family_rows()
    assert [_row(rows, n)["kernel"] for n in ("Toronto, ganzer Ausschnitt", "Zufall, mittlerer Grad 4,5", "Gitter 40×40", "Dreiecksgitter 30×30", "3-regulär, n = 500")] == [1036, 1172, 1592, 876, 500]


# --- Experiment 2 ---------------------------------------------------------------------------------------------------------------------------------------

def test_experiment_2_toronto():
    rows = ex.toronto_rows()
    assert [(r["n"], r["full_width"], r["kernel_width"]) for r in rows] == [(1000, 17, 3), (2000, 24, 5), (3000, 34, 10), (4000, 46, 10), (5072, 50, 12)]
    last = rows[-1]
    assert (last["kernel"], last["cells"], last["alpha"], last["status"]) == (1036, 223388, 2448, "exact")
    assert [r["alpha"] for r in rows] == [500, 991, 1471, 1945, 2448] and all(r["status"] == "exact" for r in rows)


# --- Experiment 3 und 4 --------------------------------------------------------------------------------------------------------------------------------

def test_experiment_3_search_against_exact():
    rows = ex.search_rows()
    toronto = _row(rows, "Toronto, ganzer Ausschnitt")
    assert (toronto["ref"], toronto["proven"], toronto["size"], toronto["greedy"], toronto["ops"]) == (2448, True, 2435, 2308, 2650138)
    assert toronto["curve"] == {0: 2369, 10: 2371, 100: 2375, 1000: 2402, 5000: 2428, 20000: 2435}
    exact_values = {"Toronto, 2 000 Kreuzungen": (991, 989), "Zufall, mittlerer Grad 3": (1076, 1076), "Skalenfrei, 2 Kanten je Knoten": (1156, 1156), "Skalenfrei, 3 Kanten je Knoten": (1004, 1004),
                    "King-Graph 20×20": (100, 100), "Gitter 40×40": (800, 800), "Dreiecksgitter 12×12": (48, 48)}
    for name, (ref, size) in exact_values.items():
        r = _row(rows, name)
        assert (r["ref"], r["size"], r["proven"]) == (ref, size, True), name
    assert _row(rows, "Gitter 40×40")["source"] == "koenig"
    assert sum(1 for r in rows if r["proven"] and r["size"] == r["ref"]) == 6 and sum(1 for r in rows if r["proven"]) == 8
    tri = _row(rows, "Dreiecksgitter 30×30")
    assert (tri["ref"], tri["proven"], tri["greedy"], tri["curve"][100], tri["curve"][1000], tri["curve"][5000], tri["curve"][0]) == (300, False, 227, 245, 283, 300, 227)
    assert round(100 * (300 - 227) / 300, 1) == 24.3
    assert (_row(rows, "Zufall, mittlerer Grad 4,5")["size"], _row(rows, "Zufall, mittlerer Grad 4,5")["ref"]) == (916, 918) and _row(rows, "3-regulär, n = 500")["size"] == 222


def test_experiment_3_greedy_range_on_thin_networks():
    rows = ex.search_rows()
    gaps = [100 * (_row(rows, n)["ref"] - _row(rows, n)["greedy"]) / _row(rows, n)["ref"] for n in ("Toronto, ganzer Ausschnitt", "Zufall, mittlerer Grad 3", "Skalenfrei, 2 Kanten je Knoten", "Skalenfrei, 3 Kanten je Knoten", "Toronto, 2 000 Kreuzungen")]
    assert f"{min(gaps):.1f}" == "2.9" and f"{max(gaps):.1f}" == "5.7"
    assert f"{100 * (2448 - 2435) / 2448:.1f}" == "0.5"


def test_experiment_4_kernel_against_full():
    rows = ex.kernel_vs_full_rows(ex.search_rows())
    assert len(rows) == 7 and sum(1 for r in rows if r["kernel"] > r["full"]) == 3 and sum(1 for r in rows if r["kernel"] < r["full"]) == 0
    by = {r["name"]: (r["kernel"], r["full"]) for r in rows}
    assert by["Toronto, ganzer Ausschnitt"] == (2446, 2435) and by["Toronto, 2 000 Kreuzungen"] == (991, 989) and by["Zufall, mittlerer Grad 4,5"] == (918, 916)
    assert all(by[n][0] == by[n][1] for n in ("Gitter 40×40", "3-regulär, n = 500", "Dreiecksgitter 30×30"))


# --- Experiment 5 ---------------------------------------------------------------------------------------------------------------------------------------

def test_experiment_5_ablation():
    rows = ex.ablation_rows()

    def k(inst, label):
        return next(r["kernel"] for r in rows if r["instance"] == inst and r["set"] == label)
    tor, zuf, ska, king, z45 = [name for name, _ in ex.ABLATION_INSTANCES]
    assert (k(tor, "alle fünf"), k(tor, "ohne Faltung"), k(tor, "ohne Dominanz")) == (52, 897, 154)
    assert (k(zuf, "alle fünf"), k(zuf, "ohne Faltung"), k(zuf, "ohne Dominanz")) == (0, 21, 0)
    assert (k(ska, "alle fünf"), k(ska, "ohne Faltung"), k(ska, "ohne Dominanz")) == (0, 1970, 2000)
    assert (k(king, "alle fünf"), k(king, "ohne Faltung"), k(king, "ohne Dominanz")) == (0, 0, 400)
    assert (k(z45, "alle fünf"), k(z45, "ohne Faltung"), k(z45, "ohne Dominanz")) == (1172, 1718, 1172)
    assert (k(tor, "ohne Dominanz und Grad 1"), k(tor, "ohne Dominanz und Dreieck"), k(tor, "nur Grad 0 und 1")) == (1743, 524, 1036)
    assert all(k(n, "ohne Grad 1") == k(n, "alle fünf") == k(n, "ohne Dreieck") for n in (tor, zuf, ska, king, z45))


def test_degree1_and_triangle_are_special_cases_of_domination():
    """Mit der Dominanz allein (plus Grad 0) kommt dasselbe heraus wie mit allen fünf Regeln, auf Zufalls- und skalenfreien Netzen."""
    for builder, n, par in ((S.random_graph, 60, 4), (S.random_graph, 60, 12), (S.scalefree_graph, 60, 8), (S.toronto_graph, 400, 0)):
        adj = builder(n, par, 2).adj
        full = R.reduce_graph(adj)
        only = R.reduce_graph(adj, ("degree0", "fold", "domination"))
        assert len(only.kernel) == len(full.kernel) and only.offset == full.offset, (builder.__name__, n, par)


# --- Dateien und Daten ----------------------------------------------------------------------------------------------------------------------------------

def test_toronto_extract():
    assert S.toronto_size() == 5072 and S.toronto_graph(5072, 0, 1).m == 7621
