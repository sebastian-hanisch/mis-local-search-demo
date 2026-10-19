"""Zweifärbung, Hopcroft-Karp und der Satz von König, von Hand und gegen networkx."""

import pytest

import mls_bipartite as B
import mls_scenario as S


def test_two_colouring_of_even_and_odd_cycles():
    assert B.two_colouring(S.ring_graph(6).adj) == [0, 1, 0, 1, 0, 1]
    assert B.two_colouring(S.ring_graph(5).adj) is None


def test_two_colouring_of_a_forest_and_isolated_vertices():
    colour = B.two_colouring(S.adjacency_from_edges(5, [(0, 1), (2, 3)]))
    assert colour[0] != colour[1] and colour[2] != colour[3] and colour[4] == 0


def test_matching_sizes_by_hand(path4, star3):
    assert B.maximum_matching_size(path4, B.two_colouring(path4)) == 2          # {0,1} und {2,3}
    assert B.maximum_matching_size(star3, B.two_colouring(star3)) == 1
    k23 = S.adjacency_from_edges(5, [(i, 2 + j) for i in range(2) for j in range(3)])
    assert B.maximum_matching_size(k23, B.two_colouring(k23)) == 2


def test_bipartite_alpha_by_hand(path4, star3, grid3):
    assert B.bipartite_alpha(path4) == 2 and B.bipartite_alpha(star3) == 3 and B.bipartite_alpha(grid3) == 5
    assert B.bipartite_alpha(S.complete_graph(3).adj) is None
    assert B.bipartite_alpha(S.grid_graph(1600, 0, 0).adj) == 800


@pytest.mark.parametrize("seed", range(60))
def test_matching_matches_networkx(seed):
    nx = pytest.importorskip("networkx")
    n = 4 + seed % 20
    graph = nx.bipartite.random_graph(n // 2, n - n // 2, 0.15 + (seed % 5) * 0.1, seed=seed)
    adj = tuple(frozenset(graph[v]) for v in range(n))
    nu = len(nx.bipartite.maximum_matching(graph, top_nodes=range(n // 2))) // 2
    assert B.bipartite_alpha(adj) == n - nu
