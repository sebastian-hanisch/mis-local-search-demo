"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): ein Knoten, keine Kante, Iterationen null, Budgetgrenzen inklusive, Gleichstände."""

import mls_constants as C
import mls_evaluation as ev
import mls_exact as X
import mls_reductions as R
import mls_scenario as S
import mls_search as Q


def test_a_single_vertex_and_the_empty_graph():
    one = S.adjacency_from_edges(1, [])
    red = R.reduce_graph(one)
    assert red.offset == 1 and red.kernel == () and R.lift(red, ()) == (0,)
    assert Q.greedy_min_degree(one) == (0,) and Q.iterated_local_search(one, 10).size == 1
    empty = R.reduce_graph(())
    assert empty.offset == 0 and empty.kernel == () and R.lift(empty, ()) == ()
    assert Q.greedy_min_degree(()) == ()


def test_a_graph_without_edges_is_solved_by_degree0():
    adj = S.adjacency_from_edges(5, [])
    red = R.reduce_graph(adj)
    assert red.offset == 5 and red.counts["degree0"] == 5 and R.lift(red, ()) == (0, 1, 2, 3, 4)
    exact = ev.exact_by_reduction_and_dp(adj, red)
    assert exact.status == "exact" and exact.value == 5 and exact.cells == 0 and exact.width == 0


def test_two_adjacent_vertices():
    adj = S.complete_graph(2).adj
    red = R.reduce_graph(adj)
    assert red.offset == 1 and len(R.lift(red, ())) == 1
    assert Q.iterated_local_search(adj, 20, 1).size == 1


def test_the_search_on_a_complete_graph_keeps_one_vertex():
    adj = S.complete_graph(6).adj
    r = Q.iterated_local_search(adj, 200, 1)
    assert r.size == 1 and R.is_independent(adj, r.best)


def test_exact_cell_budget_is_inclusive():
    adj = S.petersen_graph().adj
    red = R.reduce_graph(adj)
    order = ev.bounded_order(red.kernel)
    predicted = X.max_weight_independent_set(red.kernel, (1,) * 10, order).predicted
    assert ev.exact_by_reduction_and_dp(adj, red, cell_budget=predicted).status == "exact"
    over = ev.exact_by_reduction_and_dp(adj, red, cell_budget=predicted - 1)
    assert over.status == "over_budget" and over.predicted == predicted and over.value is None


def test_the_width_limit_is_inclusive():
    adj = S.complete_graph(8).adj                                               # K8: Min-Grad-Beutel 8, also Grad 7 beim ersten Schritt
    assert ev.bounded_order(adj, limit=7) is not None
    assert ev.bounded_order(adj, limit=6) is None


def test_bounded_order_of_an_empty_graph():
    assert ev.bounded_order(()) == ()


def test_koenig_is_used_only_when_the_decomposition_fails():
    grid = S.grid_graph(36, 0, 1).adj                                           # klein genug für die Zerlegung: DP, nicht König
    assert ev.exact_by_reduction_and_dp(grid, R.reduce_graph(grid)).status == "exact"
    wide = S.grid_graph(1600, 0, 1).adj
    assert ev.exact_by_reduction_and_dp(wide, R.reduce_graph(wide)).status == "koenig"


def test_zero_iterations_in_the_analysis():
    a = ev.analyse(ev.Settings(iters=0))
    assert a.full.iterations == 0 and a.valid and a.full.size >= len(a.greedy)


def test_extreme_slider_corners_stay_inside_the_limits():
    for net in C.NET_TYPES:
        for n, par in ((C.N_MIN, C.PAR_MIN), (C.N_MIN, C.PAR_MAX), (60, C.PAR_MIN), (60, C.PAR_MAX)):
            a = ev.analyse(ev.Settings(net=net, n=n, par=par, seed=1, iters=100))
            assert a.valid and a.graph.n >= 4, (net, n, par)


def test_the_largest_corner_runs():
    a = ev.analyse(ev.Settings(net="toronto", n=C.N_MAX, par=0, seed=1, iters=0))
    assert a.graph.n == 5072 and a.valid and a.exact.status == "exact"


def test_empty_graph_branch_of_the_analysis(monkeypatch):
    empty = S.Graph(6, S.adjacency_from_edges(6, []), S.circle_positions(6), tuple(str(i) for i in range(6)), "random")
    monkeypatch.setattr(ev.S, "build_graph", lambda *args: empty)
    a = ev.analyse(ev.Settings())
    assert a.exact.value == 6 and a.red.kernel == () and ev.verdict_main(a)[0] == "success"


def test_ties_in_the_reduction_follow_the_smaller_vertex_number():
    adj = S.path_graph(3).adj                                                   # beide Enden haben Grad 1: 0 wird genommen, nicht 2
    assert R.lift(R.reduce_graph(adj), ()) == (0, 2) and R.reduce_graph(adj).stack[0] == ("take", 0)
