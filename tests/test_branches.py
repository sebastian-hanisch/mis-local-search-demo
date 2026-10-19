"""Zweige und Nullspalten (Lehre aus der Linie): jede Regel greift auf mindestens einer Instanz, ihre Ablation vergrößert den Kern auf mindestens einer, und jeder Weg der Hauptansicht kommt vor."""

import dataclasses

import mls_constants as C
import mls_evaluation as ev
import mls_experiments as ex
import mls_reductions as R
import mls_scenario as S


def _k(rows, instance, label):
    return next(r["kernel"] for r in rows if r["instance"] == instance and r["set"] == label)


def test_every_rule_fires_on_at_least_one_ablation_instance():
    fired = {r: 0 for r in R.RULES}
    for _, build in ex.ABLATION_INSTANCES:
        for rule, count in R.reduce_graph(build().adj).counts.items():
            fired[rule] += count
    assert all(count > 0 for count in fired.values()), fired


def test_the_ablation_enlarges_the_kernel_for_every_rule_on_at_least_one_instance():
    rows = ex.ablation_rows()
    names = [name for name, _ in ex.ABLATION_INSTANCES]
    full = "alle fünf"
    assert any(_k(rows, n, "ohne Faltung") > _k(rows, n, full) for n in names)
    assert any(_k(rows, n, "ohne Dominanz") > _k(rows, n, full) for n in names)
    # Grad 1 und Dreieck sind Sonderfälle der Dominanz: erst ohne Dominanz machen sie einen Unterschied
    assert all(_k(rows, n, "ohne Grad 1") == _k(rows, n, full) == _k(rows, n, "ohne Dreieck") for n in names)
    assert any(_k(rows, n, "ohne Dominanz und Grad 1") > _k(rows, n, "ohne Dominanz") for n in names)
    assert any(_k(rows, n, "ohne Dominanz und Dreieck") > _k(rows, n, "ohne Dominanz") for n in names)


def test_degree0_matters_on_a_found_instance():
    adj = S.random_graph(10, 0, 0).adj                                                         # in der Vormessung gefunden
    full = R.reduce_graph(adj)
    without = R.reduce_graph(adj, tuple(r for r in R.RULES if r != "degree0"))
    assert len(full.kernel) == 0 and len(without.kernel) == 6


def test_every_status_of_the_exact_step_occurs():
    statuses = {ev.analyse(ev.Settings(**p)).exact.status for p in C.PRESETS.values()}
    assert statuses == {"exact", "koenig", "too_wide"}
    g140 = S.regular_graph(140, 4, 5)
    over = ev.exact_by_reduction_and_dp(g140.adj, R.reduce_graph(g140.adj))
    assert over.status == "over_budget" and over.predicted > C.EXACT_CELL_BUDGET


def test_the_search_experiment_has_proven_and_unproven_references():
    rows = ex.search_rows()
    assert any(r["proven"] and r["source"] == "exact" for r in rows) and any(r["source"] == "koenig" for r in rows) and any(not r["proven"] for r in rows)
    assert all(r["size"] <= r["ref"] for r in rows if r["proven"])


def test_the_kernel_search_beats_the_full_search_somewhere_and_never_loses_badly():
    rows = ex.kernel_vs_full_rows(ex.search_rows())
    assert any(r["kernel"] > r["full"] for r in rows)


def test_the_main_analysis_reaches_every_verdict_branch():
    kinds = set()
    for p in C.PRESETS.values():
        kinds.add(ev.verdict_main(ev.analyse(ev.Settings(**p)))[0])
    assert kinds == {"success", "info", "warning"}


def test_the_brute_force_probe_only_runs_for_tiny_graphs():
    assert ev.analyse(ev.Settings(net="random", n=C.BRUTE_MAX_N, par=8, seed=1)).brute is not None
    assert ev.analyse(ev.Settings(net="random", n=C.BRUTE_MAX_N + 1, par=8, seed=1)).brute is None


def test_validity_flag_detects_a_bad_solution():
    a = ev.analyse(ev.Settings())
    assert a.valid
    bad_pair = next(iter(S.edges_of(a.graph.adj)))
    assert not R.is_independent(a.graph.adj, bad_pair)
    assert dataclasses.replace(a, valid=False).valid is False
