"""Greedy und Lokalsuche: Handrechnungen, Invarianten (immer unabhängig, nie schlechter als der Start, deterministisch), Rückgängigmachen der Störung."""

import mls_exact as X
import mls_reductions as R
import mls_scenario as S
import mls_search as Q


def test_greedy_takes_the_low_degree_vertices_first(path4, paw, star3):
    assert Q.greedy_min_degree(path4) == (0, 3)                                 # Grad 1 zuerst: 0 sperrt 1, 3 sperrt 2
    assert Q.greedy_min_degree(paw) == (0, 3)                                   # Pendel 3 (Grad 1) sperrt 2, dann 0
    assert Q.greedy_min_degree(star3) == (1, 2, 3)


def test_greedy_is_always_maximal_and_independent():
    for seed in range(30):
        adj = S.random_graph_p(12, 25, seed)
        sol = set(Q.greedy_min_degree(adj))
        assert R.is_independent(adj, sol)
        assert all(v in sol or adj[v] & sol for v in range(len(adj)))           # maximal: jeder andere Knoten hat einen Lösungsnachbarn


def test_the_initial_state_is_the_greedy_solution(paw):
    s = Q.Search(paw)
    assert tuple(v for v in range(4) if s.in_s[v]) == Q.greedy_min_degree(paw) and s.size == 2 and s.tight == [0, 1, 2, 0] and s.ops > 0


def test_two_improvement_swaps_one_solution_vertex_for_two():
    s = Q.Search(S.path_graph(3).adj)
    s.remove(0)
    s.remove(2)
    s.insert(1)                                                                 # Lösung {1}: beide Nachbarn haben nur 1 als Lösungsnachbarn und sind nicht benachbart
    assert s.size == 1 and s.two_improvement(1) == [0, 2]
    assert s.size == 2 and s.in_s == [True, False, True] and s.tight == [0, 2, 0]


def test_two_improvement_finds_nothing_in_a_two_optimal_solution(c5):
    s = Q.Search(c5)
    assert s.size == 2 and all(not s.two_improvement(x) for x in range(5) if s.in_s[x])


def test_local_search_reaches_the_optimum_of_a_path_from_a_bad_start():
    adj = S.path_graph(7).adj                                                   # α = 4
    s = Q.Search(adj)
    for v in range(7):
        if s.in_s[v]:
            s.remove(v)
    s.insert(1)
    s.insert(4)                                                                 # {1, 4} ist maximal erweiterbar, aber nur zwei
    s.insert_free(range(7))
    s.local_search([v for v in range(7) if s.in_s[v]])
    assert s.size == 4 and R.is_independent(adj, [v for v in range(7) if s.in_s[v]])


def test_tight_counts_stay_consistent_through_a_whole_run():
    adj = S.random_graph(80, 12, 3).adj
    s = Q.Search(adj, 3)
    s.run(300)
    assert all(s.tight[v] == sum(s.in_s[w] for w in s.adj[v]) for v in range(s.n)) and s.size == sum(s.in_s)


def test_undo_restores_the_state_exactly():
    adj = S.random_graph(60, 20, 2).adj
    s = Q.Search(adj, 2)
    s.local_search([v for v in range(s.n) if s.in_s[v]])
    flags, tight, size = list(s.in_s), list(s.tight), s.size
    for _ in range(25):
        s.journal = []
        queue = s.perturb()
        if queue is not None:
            s.local_search(queue)
        s.undo(s.journal)
        s.journal = None
        assert (s.in_s, s.tight, s.size) == (flags, tight, size)


def test_run_result_is_independent_never_below_the_start_and_the_curve_never_falls():
    for seed in range(12):
        adj = S.random_graph(120, 16, seed).adj
        r = Q.iterated_local_search(adj, 400, seed, (0, 10, 100, 400))
        assert R.is_independent(adj, r.best) and len(r.best) == r.size >= r.start == len(Q.greedy_min_degree(adj))
        values = [r.curve[k] for k in (0, 10, 100, 400)]
        assert values == sorted(values) and values[-1] == r.size


def test_same_seed_same_result_and_other_seeds_may_differ():
    adj = S.regular_graph(200, 0, 1).adj
    a = Q.iterated_local_search(adj, 500, 7)
    assert a == Q.iterated_local_search(adj, 500, 7)
    assert any(Q.iterated_local_search(adj, 500, s).best != a.best for s in range(1, 6))


def test_zero_iterations_means_only_the_first_descent(grid3):
    r = Q.iterated_local_search(grid3, 0, 1, (0,))
    assert r.iterations == 0 and r.size == r.curve[0] == 5 and r.start == 5


def test_the_search_finds_the_optimum_on_small_graphs():
    for seed in range(40):
        adj = S.random_graph_p(8 + seed % 11, 15 + (seed * 7) % 40, seed)
        assert Q.iterated_local_search(adj, 3000, 1).size == X.brute_force_mwis(adj, (1,) * len(adj))[0], seed


def test_ops_grow_with_the_iterations():
    adj = S.random_graph(100, 12, 1).adj
    assert Q.iterated_local_search(adj, 50, 1).ops < Q.iterated_local_search(adj, 500, 1).ops


def test_the_search_improves_the_greedy_start_on_the_triangle_grid():
    adj = S.tri_graph(144, 0, 0).adj
    r = Q.iterated_local_search(adj, 2000, 1)
    assert r.size > r.start


def test_perturb_gives_up_when_every_vertex_is_in_the_solution():
    s = Q.Search(S.adjacency_from_edges(4, []))                                 # keine Kanten: alle Knoten in der Lösung
    assert s.perturb() is None
