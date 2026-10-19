"""Szenarien: jede Familie hat die dokumentierte Größe, ist reproduzierbar und bedeutet den Parameter so, wie die Hilfe sagt."""

import pytest

import mls_constants as C
import mls_scenario as S


def test_every_net_type_builds_a_simple_undirected_graph():
    for net in C.NET_TYPES:
        g = S.build_graph(net, 36, 10, 3)
        assert g.n == len(g.adj) == len(g.positions) == len(g.labels)
        for u in range(g.n):
            assert u not in g.adj[u]
            assert all(u in g.adj[v] for v in g.adj[u])
        assert g.m == len(g.edges())


def test_same_seed_same_graph_and_different_seed_different_graph():
    for net in ("random", "scalefree", "regular", "toronto"):
        par = 12 if net in ("random", "scalefree") else 20
        assert S.build_graph(net, 40, par, 5) == S.build_graph(net, 40, par, 5)
        assert S.build_graph(net, 40, par, 5).adj != S.build_graph(net, 40, par, 6).adj


def test_unknown_net_type_is_rejected():
    with pytest.raises(ValueError):
        S.build_graph("ring", 10, 0, 1)


def test_mean_degree_formula_and_its_use():
    assert S.mean_degree(0) == 2.0 and S.mean_degree(60) == 17.0 and S.mean_degree(12) == 5.0
    degrees = [S.random_graph(300, 36, seed).m * 2 / 300 for seed in range(5)]
    assert 10.0 < sum(degrees) / 5 < 12.5                                                     # par 36 -> Grad 11, im Mittel um 11


def test_scalefree_edges_per_node():
    assert S.scalefree_m(0) == 1 and S.scalefree_m(16) == 3 and S.scalefree_m(60) == 8
    g = S.scalefree_graph(50, 16, 1)
    assert g.m == 3 * (50 - 3)                                                                 # jeder Knoten ab dem vierten bringt genau drei neue Kanten mit
    assert max(len(a) for a in g.adj) > 3 * 3                                                 # mindestens eine Nabe


def test_regular_graph_has_degree_three_and_an_even_number_of_vertices():
    g = S.regular_graph(101, 0, 1)
    assert g.n == 100 and all(len(a) == 3 for a in g.adj) and g.m == 150
    assert S.regular_graph(3, 0, 1).n == 4                                                     # mindestens vier Knoten
    assert S.regular_graph(100, 20, 1).m == 150 - round(150 * 0.2)


def test_regular_edges_rejects_impossible_parameters():
    import random
    with pytest.raises(ValueError):
        S.regular_edges(5, 3, random.Random(1))                                                # n * d ungerade
    with pytest.raises(ValueError):
        S.regular_edges(3, 3, random.Random(1))                                                # d >= n


def test_lattice_sizes_and_edge_counts():
    assert S.grid_graph(36, 0, 1).m == 2 * 6 * 5 and S.grid_graph(36, 0, 1).n == 36
    assert S.tri_graph(36, 0, 1).m == 60 + 25 and S.king_graph(36, 0, 1).m == 60 + 50
    assert S.grid_side(50) == 7 and S.grid_side(1) == 2


def test_lattice_disturbance_removes_that_share_of_edges():
    full = S.grid_graph(100, 0, 1).m
    assert S.grid_graph(100, 25, 1).m == full - round(full * 0.25)
    assert S.grid_graph(100, 25, 1).adj != S.grid_graph(100, 25, 2).adj                         # andere Stichprobe


def test_toronto_takes_the_closest_intersections_and_caps_n():
    g = S.toronto_graph(200, 0, 1)
    assert g.n == 200 and "vom Mittelpunkt" in g.labels[0]
    assert S.toronto_graph(10 ** 6, 0, 1).n == S.toronto_size() == 5072 == C.N_MAX
    assert S.toronto_graph(200, 50, 1).m == g.m - round(g.m * 0.5)
    assert S.toronto_graph(S.toronto_size(), 0, 1).m == 7621


def test_positions_are_inside_the_unit_square():
    for net in C.NET_TYPES:
        g = S.build_graph(net, 50, 10, 2)
        assert all(-1.0001 <= x <= 1.0001 and -1.0001 <= y <= 1.0001 for x, y in g.positions)


def test_normalize_and_circle_positions():
    assert S.normalize(((0, 0), (2, 1))) == ((-1.0, -0.5), (1.0, 0.5))
    assert S.normalize(()) == ()
    assert S.circle_positions(4)[0] == (0.0, 1.0)


def test_mini_instances():
    assert S.path_graph(4).m == 3 and S.ring_graph(5).m == 5 and S.complete_graph(4).m == 6 and S.star_graph(3).m == 3 and S.triangle_with_pendant().m == 4 and S.petersen_graph().m == 15
    assert all(len(a) == 3 for a in S.petersen_graph().adj)


def test_adjacency_from_edges_ignores_loops_and_duplicates():
    adj = S.adjacency_from_edges(3, [(0, 1), (1, 0), (2, 2)])
    assert adj == (frozenset({1}), frozenset({0}), frozenset())
