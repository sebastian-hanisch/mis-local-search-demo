"""Die kopierte Zerlegung und DP (Stück 5 und 6): Breite von Hand, Zellen, Werte gegen Brute Force."""

import pytest

import mls_exact as X
import mls_scenario as S


@pytest.mark.parametrize("name,width", [("path4", 1), ("c5", 2), ("k4", 3), ("star3", 1)])
def test_min_fill_width_by_hand(request, name, width):
    adj = request.getfixturevalue(name)
    assert X.eliminate(adj, X.min_fill_order(adj)).width == width


def test_eliminate_rejects_an_order_that_is_not_a_permutation(path4):
    with pytest.raises(ValueError):
        X.eliminate(path4, (0, 1, 2))


def test_min_degree_and_min_fill_are_valid_orders(grid3):
    for order in (X.min_degree_order(grid3), X.min_fill_order(grid3)):
        assert sorted(order) == list(range(9)) and X.eliminate(grid3, order).width == 3


def test_dp_value_cells_and_set_on_the_path(path4):
    r = X.max_weight_independent_set(path4, (1, 1, 1, 1), (0, 1, 2, 3))
    assert r.value == 2 and r.chosen in {(0, 2), (0, 3), (1, 3)} and r.cells == 14 == r.predicted and not r.aborted     # Beutel 2+2+2+1: 4+4+4+2 Zellen


def test_dp_respects_the_cell_budget(path4):
    r = X.max_weight_independent_set(path4, (1, 1, 1, 1), (0, 1, 2, 3), cell_budget=13)
    assert r.aborted and r.cells == 0 and r.predicted == 14
    assert not X.max_weight_independent_set(path4, (1, 1, 1, 1), (0, 1, 2, 3), cell_budget=14).aborted


def test_dp_matches_brute_force_on_random_graphs():
    for seed in range(80):
        adj = S.random_graph_p(6 + seed % 10, 15 + (seed * 11) % 50, seed)
        order = X.min_fill_order(adj)
        r = X.max_weight_independent_set(adj, (1,) * len(adj), order)
        assert r.value == X.brute_force_mwis(adj, (1,) * len(adj))[0] and X.is_independent_set(adj, r.chosen) and len(r.chosen) == r.value, seed


def test_brute_force_limit_and_value(path4):
    with pytest.raises(ValueError):
        X.brute_force_mwis(S.path_graph(25).adj, (1,) * 25, limit=20)
    assert X.brute_force_mwis(path4, (1, 1, 1, 1))[0] == 2


def test_dp_value_does_not_depend_on_the_order(c5):
    values = {X.max_weight_independent_set(c5, (1,) * 5, order).value for order in ((0, 1, 2, 3, 4), (4, 2, 0, 3, 1), (2, 4, 1, 3, 0))}
    assert values == {2}


def test_is_independent_set_checks_every_pair_including_the_last(path4):
    assert X.is_independent_set(path4, (0, 2)) and X.is_independent_set(path4, (0, 3)) and X.is_independent_set(path4, (1, 3)) and X.is_independent_set(path4, ())
    assert not X.is_independent_set(path4, (0, 1)) and not X.is_independent_set(path4, (1, 2)) and not X.is_independent_set(path4, (2, 3))
    assert not X.is_independent_set(path4, (0, 2, 3))                           # das letzte Paar (2, 3) ist benachbart
