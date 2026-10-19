"""Die Reduktionsregeln einzeln und zusammen, mit Rücklift, an Mini-Instanzen von Hand gerechnet (DEMO-PLAYBOOK §1b)."""

import pytest

import mls_constants as C
import mls_reductions as R
import mls_scenario as S


def _state(adj):
    return R.initial_state(adj)


def test_initial_state(path4):
    st = _state(path4)
    assert st.g == {0: {1}, 1: {0, 2}, 2: {1, 3}, 3: {2}} and st.n == 4 and st.next_id == 4 and st.offset == 0 and st.stack == []


def test_rule_degree0_takes_isolated_vertices():
    st = _state(S.adjacency_from_edges(3, [(0, 1)]))
    assert R.rule_degree0(st) == 1
    assert st.stack == [("take", 2)] and st.offset == 1 and set(st.g) == {0, 1} and st.counts["degree0"] == 1


def test_rule_degree1_takes_leaves_and_removes_their_neighbours(path4):
    st = _state(path4)
    assert R.rule_degree1(st) == 2                                              # 0 nimmt, 1 fällt; dann hat 2 nur noch den Nachbarn 3
    assert st.stack == [("take", 0), ("take", 2)] and st.offset == 2 and not st.g


def test_rule_triangle_takes_a_vertex_whose_two_neighbours_are_connected(triangle):
    st = _state(triangle)
    assert R.rule_triangle(st) == 1
    assert st.stack == [("take", 0)] and st.offset == 1 and not st.g


def test_rule_fold_merges_a_degree_two_vertex_with_its_unconnected_neighbours(c5):
    st = _state(c5)
    assert R.rule_fold(st) == 1                                                 # 0 mit 1 und 4 wird zu 5; danach bilden 2, 3, 5 ein Dreieck: keine zweite Faltung
    assert st.stack == [("fold", 0, 1, 4, 5)] and st.offset == 1 and st.g == {2: {3, 5}, 3: {2, 5}, 5: {2, 3}} and st.next_id == 6


def test_rule_fold_leaves_a_triangle_alone(triangle):
    assert R.rule_fold(_state(triangle)) == 0


def test_rule_domination_removes_dominated_neighbours(k4):
    st = _state(k4)
    assert R.rule_domination(st) == 3                                           # N[0] ⊆ N[1], N[2], N[3]: alle drei fallen
    assert st.g == {0: set()} and st.stack == []


def test_rule_domination_needs_the_degree_condition_and_containment():
    st = _state(S.path_graph(4).adj)
    assert R.rule_domination(st) >= 1                                           # N[0] = {0,1} ⊆ N[1] = {0,1,2}: 1 entfällt
    assert 1 not in st.g
    petersen = _state(S.petersen_graph().adj)
    assert R.rule_domination(petersen) == 0                                     # dreiecksfrei und regulär: nie N[v] ⊆ N[u]


@pytest.mark.parametrize("name,alpha,offset,expected", [("path4", 2, 2, (0, 2)), ("paw", 2, 2, (0, 3)), ("star3", 3, 3, (1, 2, 3)), ("triangle", 1, 1, (0,)), ("c5", 2, 2, (0, 2)), ("k4", 1, 1, (0,))])
def test_the_rules_solve_the_mini_instances_completely(request, name, alpha, offset, expected):
    adj = request.getfixturevalue(name)
    red = R.reduce_graph(adj)
    assert red.kernel == () and red.offset == offset == alpha
    assert R.lift(red, ()) == expected and R.is_independent(adj, expected)


def test_no_rule_applies_to_the_petersen_graph(petersen):
    red = R.reduce_graph(petersen)
    assert len(red.kernel) == 10 and red.offset == 0 and sum(red.counts.values()) == 0 and red.kernel_share == 100.0 and red.kernel_ids == tuple(range(10))


def test_the_counters_name_the_rules_that_fired(k4, c5):
    assert R.reduce_graph(k4).counts == {"degree0": 1, "degree1": 0, "triangle": 0, "fold": 0, "domination": 3}
    assert R.reduce_graph(c5).counts == {"degree0": 0, "degree1": 0, "triangle": 1, "fold": 1, "domination": 0}


def test_lift_translates_kernel_numbers_back_to_the_original(petersen):
    red = R.reduce_graph(petersen)
    assert R.lift(red, (0, 2, 6, 8)) == (0, 2, 6, 8)


def test_lift_of_a_folded_kernel_vertex_uses_both_outer_neighbours():
    adj = S.ring_graph(7).adj                                                   # C7: Faltung am Knoten 0 (Nachbarn 1 und 6), danach bleibt ein Kern
    red = R.reduce_graph(adj, ("fold",))
    assert red.stack and red.stack[0][0] == "fold" and any(v >= 7 for v in red.kernel_ids)
    folded = [i for i, v in enumerate(red.kernel_ids) if v >= 7]
    sol = R.lift(red, folded)                                                   # der gefaltete Knoten in der Kernlösung heißt: seine beiden Gründer in der Lösung
    assert 1 in sol and 6 in sol and 0 not in sol


def test_ruleset_none_returns_the_whole_graph(c5):
    red = R.reduce_graph(c5, ())
    assert len(red.kernel) == 5 and red.offset == 0 and red.kernel == c5


def test_unknown_rule_names_are_ignored_and_the_order_is_fixed(k4):
    assert R.reduce_graph(k4, ("domination", "degree0", "nonsense")).rules == ("degree0", "domination")


def test_the_log_names_folded_vertices_with_an_f(c5):
    red = R.reduce_graph(c5)
    assert red.log[0]["rule"] == "fold" and "F1" in red.log[0]["text"] and red.log[0]["step"] == 1


def test_log_is_capped(monkeypatch):
    monkeypatch.setattr(R, "LOG_CAP", 2)
    red = R.reduce_graph(S.path_graph(6).adj)
    assert len(red.log) == 2


def test_is_independent(path4):
    assert R.is_independent(path4, (0, 2)) and R.is_independent(path4, ()) and not R.is_independent(path4, (0, 1))


def test_kernel_share_of_the_empty_graph_is_zero():
    assert R.reduce_graph(()).kernel_share == 0.0


@pytest.mark.parametrize("rules_key", C.RULESET_ORDER)
def test_every_rule_set_keeps_the_value_of_the_mini_instances(rules_key, path4, c5, petersen):
    from mls_exact import max_weight_independent_set, min_fill_order
    for adj, alpha in ((path4, 2), (c5, 2), (petersen, 4)):
        red = R.reduce_graph(adj, C.RULESETS[rules_key])
        k = red.kernel
        chosen = max_weight_independent_set(k, (1,) * len(k), min_fill_order(k)).chosen if k else ()
        sol = R.lift(red, chosen)
        assert R.is_independent(adj, sol) and len(sol) == alpha
