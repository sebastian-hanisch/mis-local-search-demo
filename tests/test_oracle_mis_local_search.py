"""Orakel-Tests mis-local-search-demo (ORACLE-PLAYBOOK, Verfahrenstyp „exakter kombinatorischer Löser plus Heuristik“).

Orakel (jeweils ein ANDERER Rechenweg als der der Demo):
- `scipy.optimize.milp` auf der Kanten-Formulierung (x_u + x_v <= 1, maximiere die Summe): α eines Graphen;
- Brute Force über alle Teilmengen (n <= 16);
- `networkx` für das größte Matching bipartiter Graphen (Satz von König).
Geprüft werden jede Regelmenge und jede Regel allein (Offset + α(Kern) = α, Rücklift unabhängig und genau so groß), die Zerlegung des Kerns, die Lokalsuche (nie über α, immer unabhängig)
und die ganze Kette auf Toronto-Ausschnitten."""

import numpy as np
import pytest

import mls_constants as C
import mls_evaluation as ev
import mls_exact as X
import mls_reductions as R
import mls_scenario as S
import mls_search as Q

scipy_optimize = pytest.importorskip("scipy.optimize")


def milp_alpha(adj):
    """α per milp (Kantenformulierung); nur für Instanzen, die HiGHS sicher beweist."""
    n = len(adj)
    edges = S.edges_of(adj)
    if not edges:
        return n
    matrix = np.zeros((len(edges), n))
    for r, (u, v) in enumerate(edges):
        matrix[r, u] = matrix[r, v] = 1
    res = scipy_optimize.milp(-np.ones(n), constraints=scipy_optimize.LinearConstraint(matrix, ub=1), integrality=np.ones(n), bounds=scipy_optimize.Bounds(0, 1))
    assert res.status == 0
    return round(-res.fun)


def _instances(count, n_low=5, n_span=20):
    for seed in range(count):
        yield seed, S.random_graph_p(n_low + seed % n_span, 8 + (seed * 5) % 40, seed)


def _solve_kernel(red):
    k = red.kernel
    if not k:
        return ()
    result = X.max_weight_independent_set(k, (1,) * len(k), X.min_fill_order(k))
    assert not result.aborted
    return result.chosen


def test_reduction_plus_kernel_dp_matches_milp_on_300_instances_for_every_rule_set():
    count = 0
    for seed, adj in _instances(300):
        alpha = milp_alpha(adj)
        for rules_key in C.RULESET_ORDER:
            red = R.reduce_graph(adj, C.RULESETS[rules_key])
            chosen = _solve_kernel(red)
            sol = R.lift(red, chosen)
            assert red.offset + len(chosen) == alpha == len(sol), (rules_key, seed)
            assert R.is_independent(adj, sol), (rules_key, seed)
        count += 1
    assert count == 300


@pytest.mark.parametrize("rule", R.RULES)
def test_every_single_rule_alone_is_exact(rule):
    for seed, adj in _instances(150):
        red = R.reduce_graph(adj, (rule,))
        chosen = _solve_kernel(red)
        sol = R.lift(red, chosen)
        assert red.offset + len(chosen) == milp_alpha(adj) and R.is_independent(adj, sol), (rule, seed)


def test_brute_force_agrees_with_the_chain_on_small_graphs():
    for seed in range(80):
        adj = S.random_graph_p(6 + seed % 10, 10 + (seed * 9) % 50, seed)
        red = R.reduce_graph(adj)
        assert red.offset + len(_solve_kernel(red)) == X.brute_force_mwis(adj, (1,) * len(adj))[0], seed


def test_the_whole_chain_on_larger_structured_graphs_matches_milp():
    graphs = [S.scalefree_graph(80, 16, 1), S.scalefree_graph(60, 8, 2), S.random_graph(80, 10, 3), S.tri_graph(64, 0, 1), S.king_graph(49, 0, 1), S.regular_graph(40, 0, 2), S.toronto_graph(150, 0, 1), S.toronto_graph(250, 20, 2)]
    for index, g in enumerate(graphs):
        red = R.reduce_graph(g.adj)
        exact = ev.exact_by_reduction_and_dp(g.adj, red)
        alpha = milp_alpha(g.adj)
        assert exact.status in ("exact", "koenig", "too_wide", "over_budget")
        if exact.status == "exact":
            assert exact.value == alpha and R.is_independent(g.adj, exact.solution) and len(exact.solution) == alpha, index


def test_the_local_search_is_independent_never_above_alpha_and_never_below_greedy():
    for seed, adj in _instances(60, 8, 14):
        alpha = milp_alpha(adj)
        r = Q.iterated_local_search(adj, 500, seed)
        assert R.is_independent(adj, r.best) and len(Q.greedy_min_degree(adj)) <= r.size <= alpha, seed


def test_the_search_on_the_kernel_lifts_to_an_independent_set_of_the_original():
    for seed, adj in _instances(60, 10, 25):
        red = R.reduce_graph(adj)
        result, lifted = ev.search_on_kernel(red, 300, seed)
        assert R.is_independent(adj, lifted) and len(lifted) <= milp_alpha(adj), seed
        if result is not None:
            assert len(lifted) == red.offset + result.size, seed                 # jede Faltung zählt im Offset, die Menge des Originals ist genau so groß


def test_bipartite_alpha_matches_milp():
    for g in (S.grid_graph(36, 0, 1), S.grid_graph(49, 25, 2), S.grid_graph(64, 10, 3), S.ring_graph(8), S.path_graph(9)):
        assert ev.B.bipartite_alpha(g.adj) == milp_alpha(g.adj)


def test_toronto_subsets_end_to_end_match_milp():
    for n in (60, 150, 300, 600):
        g = S.toronto_graph(n, 0, 1)
        exact = ev.exact_by_reduction_and_dp(g.adj, R.reduce_graph(g.adj))
        assert exact.status == "exact" and exact.value == milp_alpha(g.adj), n


def test_triangle_grid_and_cycles_have_their_closed_forms():
    assert milp_alpha(S.tri_graph(36, 0, 1).adj) == 12                           # 6×6 mit einer Diagonale: drei Farben, 36 / 3
    for k in (5, 7, 9):
        assert milp_alpha(S.ring_graph(k).adj) == k // 2
