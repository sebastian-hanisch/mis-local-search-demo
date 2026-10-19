"""Plotly-Figuren: Netz mit Kern bzw. Lösung, Verlauf der Lokalsuche, Kern je Netzfamilie, Breite auf Toronto, Lokalsuche gegen exakt, Kern gegen ganzes Netz und Ablation. Alle Achsen fest (fixedrange)."""

import plotly.graph_objects as go

import mls_constants as C

_FONT = dict(size=13)


def _fix(fig, height=420, **layout):
    layout.setdefault("margin", dict(l=40, r=20, t=30, b=40))
    fig.update_layout(height=height, font=_FONT, **layout)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _lines(pos, edges, color, width, name=None, show=False):
    xs, ys = [], []
    for u, v in edges:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width), hoverinfo="skip", showlegend=show, name=name)


def _frame(fig, height):
    fig.add_trace(go.Scatter(x=[-1.25, 1.25], y=[-1.25, 1.25], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return _fix(fig, height, legend=dict(orientation="h", y=-0.02, x=0.5, xanchor="center"), margin=dict(l=10, r=10, t=10, b=40))


def _nodes(graph, colors):
    n = graph.n
    big = n > C.DRAW_LABEL_MAX_N
    pos = graph.positions
    return go.Scatter(x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers" if big else "markers+text", text=None if big else [str(i + 1) for i in range(n)], textposition="middle center",
                      textfont=dict(color="white", size=10), marker=dict(color=colors, size=5 if big else 20, line=dict(color="white", width=1)), hovertext=list(graph.labels), hoverinfo="text", showlegend=False)


def build_kernel_figure(graph, red, height=520):
    """Das Netz nach den Regeln: Knoten des Kerns orange und ihre Kanten dick, von den Regeln erledigte Knoten und Kanten blass. Die Kernknoten, die zu gefalteten Knoten gehören, sind nicht eingezeichnet
    (ein gefalteter Knoten steht für drei Originalknoten), ihre Kanten zu Originalknoten erscheinen als Kanten des Originals."""
    kernel_vertices = {v for v in red.kernel_ids if v < graph.n}
    inside = [e for e in graph.edges() if e[0] in kernel_vertices and e[1] in kernel_vertices]
    rest = [e for e in graph.edges() if e not in set(inside)]
    fig = go.Figure()
    pos = graph.positions
    fig.add_trace(_lines(pos, rest, C.COLOR_EDGE, 1, "von den Regeln erledigt", True))
    fig.add_trace(_lines(pos, inside, C.COLOR_KERNEL, 2.5, "Kern (Kanten zwischen Kernknoten)", True))
    fig.add_trace(_nodes(graph, [C.COLOR_KERNEL if v in kernel_vertices else C.COLOR_FREE for v in range(graph.n)]))
    return _frame(fig, height)


def build_solution_figure(graph, solution, height=520):
    """Das Netz mit einer unabhängigen Menge: gewählte Knoten rot (nie zwei benachbart), die übrigen blau."""
    chosen = set(solution)
    fig = go.Figure()
    fig.add_trace(_lines(graph.positions, graph.edges(), C.COLOR_EDGE, 1))
    fig.add_trace(_nodes(graph, [C.COLOR_CHOSEN if v in chosen else C.COLOR_FREE for v in range(graph.n)]))
    for name, color in (("in der Lösung", C.COLOR_CHOSEN), ("nicht in der Lösung", C.COLOR_FREE)):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=color, size=12), name=name))
    return _frame(fig, height)


def build_curve_figure(a, height=380):
    """Beste Größe der Lokalsuche an den Haltepunkten, auf dem ganzen Netz und auf dem (zurückgehobenen) Kern, dazu Greedy und der bekannte Wert als waagerechte Linien."""
    ref = a.exact.value if a.exact.value is not None else max(len(a.greedy), a.full.size, len(a.lifted))
    pts = sorted(set(a.full.curve) | {a.full.iterations})
    xs = [max(p, 0.5) for p in pts]
    full = [a.full.curve.get(p, a.full.size) for p in pts]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=full, mode="lines+markers", name="Lokalsuche, ganzes Netz", line=dict(color=C.COLOR_BLUE, width=3), marker=dict(size=8),
                             hovertemplate="%{x:.0f} Iterationen: %{y}<extra>ganzes Netz</extra>"))
    if a.kernel_search is not None:
        ks = [a.red.offset + a.kernel_search.curve.get(p, a.kernel_search.size) for p in pts]
        fig.add_trace(go.Scatter(x=xs, y=ks, mode="lines+markers", name="Lokalsuche, Kern (plus Offset)", line=dict(color=C.COLOR_OK, width=3, dash="dash"), marker=dict(size=8),
                                 hovertemplate="%{x:.0f} Iterationen: %{y}<extra>Kern</extra>"))
    fig.add_hline(y=len(a.greedy), line_dash="dot", line_color="#888888", annotation_text="Greedy", annotation_position="bottom right")
    fig.add_hline(y=ref, line_dash="dash", line_color=C.COLOR_BAD, annotation_text="Optimum" if a.exact.value is not None else "bester gefundener Wert", annotation_position="top left")
    fig.update_xaxes(title="Iterationen (logarithmisch; 0 = nach dem ersten Abstieg)", type="log")
    fig.update_yaxes(title="Größe der unabhängigen Menge")
    return _fix(fig, height, legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center"))


def build_families_figure(rows):
    """Kern in Prozent der Knoten je Netzfamilie; 0 % heißt: die Regeln lösen das Netz vollständig."""
    shares = [r["share"] for r in rows]
    fig = go.Figure(go.Bar(y=[r["name"] for r in rows], x=shares, orientation="h", marker_color=[C.COLOR_OK if s == 0 else C.COLOR_KERNEL if s < 90 else C.COLOR_BAD for s in shares],
                           text=[f"{s:.1f} %".replace(".", ",") for s in shares], textposition="outside", cliponaxis=False,
                           hovertext=[f"{r['name']}: Kern {r['kernel']} von {r['n']} Knoten, {r['offset']} von den Regeln festgelegt" for r in rows], hoverinfo="text"))
    fig.update_xaxes(title="Kern in % der Knoten", range=[0, 115])
    fig.update_yaxes(autorange="reversed")
    return _fix(fig, 120 + 30 * len(rows), margin=dict(l=250, r=40, t=20, b=50))


def build_toronto_figure(rows):
    """Breite der Min-Fill-Zerlegung des ganzen Ausschnitts gegen die des Kerns, über der Zahl der Kreuzungen."""
    ns = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[r["full_width"] for r in rows], mode="lines+markers", name="ganzer Ausschnitt", line=dict(color=C.COLOR_BAD, width=3), marker=dict(size=9),
                             hovertemplate="%{x} Kreuzungen: Breite %{y}<extra>ohne Regeln</extra>"))
    fig.add_trace(go.Scatter(x=ns, y=[r["kernel_width"] for r in rows], mode="lines+markers", name="Kern nach den Regeln", line=dict(color=C.COLOR_OK, width=3), marker=dict(size=9),
                             hovertemplate="%{x} Kreuzungen: Breite %{y}<extra>Kern</extra>"))
    fig.update_xaxes(title="Kreuzungen")
    fig.update_yaxes(title="Breite der Zerlegung", rangemode="tozero")
    return _fix(fig, 360, legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center"))


def build_search_figure(rows):
    """Abstand unter dem Vergleichswert in Prozent: Greedy gegen die Lokalsuche nach 100, 1 000 und 20 000 Iterationen, je Netz."""
    names = [r["name"] for r in rows]

    def gap(value, r):
        return 100.0 * (r["ref"] - value) / r["ref"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=[gap(r["greedy"], r) for r in rows], name="Greedy", marker_color="#999999"))
    for i, it in enumerate((100, 1000, 20000)):
        fig.add_trace(go.Bar(x=names, y=[gap(r["curve"].get(it, r["size"]), r) for r in rows], name="Lokalsuche, " + f"{it:,}".replace(",", ".") + " Iterationen", marker_color=C.COLOR_PALETTE[(i + 1) % len(C.COLOR_PALETTE)]))
    fig.update_yaxes(title="% unter dem Vergleichswert", rangemode="tozero")
    return _fix(fig, 430, barmode="group", legend=dict(orientation="h", y=1.25, x=0.5, xanchor="center"), margin=dict(l=50, r=20, t=60, b=130))


def build_kernel_vs_full_figure(rows):
    """Gefundene Größe nach gleicher Iterationszahl: ganzes Netz gegen Kern, als Abstand unter dem Vergleichswert."""
    names = [r["name"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=[r["ref"] - r["full"] for r in rows], name="Lokalsuche auf dem ganzen Netz", marker_color=C.COLOR_BLUE))
    fig.add_trace(go.Bar(x=names, y=[r["ref"] - r["kernel"] for r in rows], name="Lokalsuche auf dem Kern", marker_color=C.COLOR_OK))
    fig.update_yaxes(title="Knoten unter dem Vergleichswert", rangemode="tozero")
    return _fix(fig, 380, barmode="group", legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center"), margin=dict(l=50, r=20, t=50, b=110))


def build_ablation_figure(rows):
    """Kern (Knoten) je Instanz und Regelmenge, gruppierte Balken."""
    instances = list(dict.fromkeys(r["instance"] for r in rows))
    sets = list(dict.fromkeys(r["set"] for r in rows))
    fig = go.Figure()
    for i, label in enumerate(sets):
        fig.add_trace(go.Bar(x=instances, y=[next(r["kernel"] for r in rows if r["instance"] == inst and r["set"] == label) for inst in instances], name=label,
                             marker_color=C.COLOR_PALETTE[i % len(C.COLOR_PALETTE)], hovertemplate="%{y} Knoten im Kern<extra>" + label + "</extra>"))
    fig.update_yaxes(title="Knoten im Kern")
    return _fix(fig, 430, barmode="group", legend=dict(orientation="h", y=1.35, x=0.5, xanchor="center"), margin=dict(l=50, r=20, t=60, b=110))
