"""Figuren: jede baut ohne Fehler, sperrt die Achsen (fixedrange) und zeigt die richtigen Dinge."""

import plotly.graph_objects as go

import mls_constants as C
import mls_evaluation as ev
import mls_experiments as ex
import mls_reductions as R
import mls_scenario as S
import mls_visualization as Vz


def _locked(fig):
    return all(ax.fixedrange for ax in (fig.layout.xaxis, fig.layout.yaxis))


def test_kernel_figure_separates_kernel_edges_from_finished_edges():
    g = S.petersen_graph()
    red = R.reduce_graph(g.adj, ())                                             # keine Regel: alle zehn Knoten und alle 15 Kanten im Kern
    fig = Vz.build_kernel_figure(g, red)
    assert isinstance(fig, go.Figure) and _locked(fig)
    kernel_trace = next(t for t in fig.data if t.name == "Kern (Kanten zwischen Kernknoten)")
    done_trace = next(t for t in fig.data if t.name == "von den Regeln erledigt")
    assert len(kernel_trace.x) // 3 == 15 and len(done_trace.x) == 0


def test_kernel_figure_colours_kernel_vertices():
    g = S.ring_graph(5)
    red = R.reduce_graph(g.adj)                                                 # C5: Kern leer
    fig = Vz.build_kernel_figure(g, red)
    nodes = next(t for t in fig.data if t.mode and "markers" in t.mode and t.showlegend is False and t.hovertext is not None)
    assert set(nodes.marker.color) == {C.COLOR_FREE}


def test_solution_figure_colours_the_chosen_vertices():
    g = S.path_graph(4)
    fig = Vz.build_solution_figure(g, (0, 2))
    nodes = next(t for t in fig.data if t.hovertext is not None and t.mode and "markers" in t.mode)
    assert list(nodes.marker.color) == [C.COLOR_CHOSEN, C.COLOR_FREE, C.COLOR_CHOSEN, C.COLOR_FREE] and _locked(fig)


def test_graph_figures_drop_the_labels_for_large_graphs():
    small = Vz.build_solution_figure(S.path_graph(4), ())
    big = Vz.build_solution_figure(S.path_graph(C.DRAW_LABEL_MAX_N + 10), ())
    assert [t.mode for t in small.data if t.hovertext is not None][0] == "markers+text"
    assert [t.mode for t in big.data if t.hovertext is not None][0] == "markers"


def test_curve_figure_has_both_searches_greedy_and_reference():
    a = ev.analyse(ev.Settings(net="random", n=80, par=20, seed=3))
    fig = Vz.build_curve_figure(a)
    names = [t.name for t in fig.data if t.name]
    assert names[0] == "Lokalsuche, ganzes Netz" and "Lokalsuche, Kern (plus Offset)" in names and _locked(fig) and fig.layout.xaxis.type == "log"
    assert len(fig.layout.shapes) == 2                                          # Greedy und Vergleichswert


def test_curve_figure_without_a_kernel_has_no_kernel_series():
    a = ev.analyse(ev.Settings(net="random", n=16, par=4, seed=5))
    assert a.kernel_search is None
    assert "Lokalsuche, Kern (plus Offset)" not in [t.name for t in Vz.build_curve_figure(a).data]


def test_experiment_figures_build_with_locked_axes():
    rows3 = ex.search_rows()
    for fig in (Vz.build_families_figure(ex.family_rows()), Vz.build_toronto_figure(ex.toronto_rows()), Vz.build_search_figure(rows3), Vz.build_kernel_vs_full_figure(ex.kernel_vs_full_rows(rows3)),
                Vz.build_ablation_figure(ex.ablation_rows())):
        assert isinstance(fig, go.Figure) and fig.data and fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_families_figure_colours_by_kernel_share():
    rows = [{"name": "a", "share": 0.0, "kernel": 0, "n": 5, "offset": 5}, {"name": "b", "share": 50.0, "kernel": 3, "n": 6, "offset": 3}, {"name": "c", "share": 95.0, "kernel": 19, "n": 20, "offset": 1}]
    bar = Vz.build_families_figure(rows).data[0]
    assert list(bar.marker.color) == [C.COLOR_OK, C.COLOR_KERNEL, C.COLOR_BAD] and list(bar.x) == [0.0, 50.0, 95.0]


def test_ablation_figure_has_one_series_per_rule_set_and_one_bar_per_instance():
    fig = Vz.build_ablation_figure(ex.ablation_rows())
    assert len(fig.data) == len(ex.ABLATIONS) and all(len(t.x) == len(ex.ABLATION_INSTANCES) for t in fig.data)


def test_search_figure_has_greedy_and_three_checkpoints():
    fig = Vz.build_search_figure(ex.search_rows())
    assert [t.name for t in fig.data] == ["Greedy", "Lokalsuche, 100 Iterationen", "Lokalsuche, 1.000 Iterationen", "Lokalsuche, 20.000 Iterationen"]


def test_toronto_figure_shows_full_and_kernel_width():
    fig = Vz.build_toronto_figure(ex.toronto_rows())
    assert [t.name for t in fig.data] == ["ganzer Ausschnitt", "Kern nach den Regeln"] and list(fig.data[0].y)[-1] == 50 and list(fig.data[1].y)[-1] == 12
