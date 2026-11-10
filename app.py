"""Unabhängige Menge im großen Maßstab: Reduktionen und Lokalsuche - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Achtes Stück der Härte-und-Struktur-Reihe: Wie viel eines großen Konfliktgraphen lösen Reduktionsregeln vorab, wie nah kommt eine Lokalsuche an das Optimum, und wann reicht beides zusammen für ein
exaktes Ergebnis?

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import mls_constants as C
import mls_evaluation as ev
import mls_experiments as ex
import mls_scenario as S
from mls_layout import dunkles_design, kopf_css
from mls_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from mls_reductions import RULE_NAMES
from mls_visualization import (
    build_ablation_figure,
    build_curve_figure,
    build_families_figure,
    build_kernel_figure,
    build_kernel_vs_full_figure,
    build_search_figure,
    build_solution_figure,
    build_toronto_figure,
)

st.set_page_config(page_title="Reduktionen und Lokalsuche – Sebastian Hanisch", layout="wide")

_i = ev._i
LOG_MAX_N = 200            # bis zu dieser Knotenzahl zeigt die App das Protokoll der Schritte


def _show(verdict):
    kind, text = verdict
    {"success": st.success, "info": st.info, "warning": st.warning}[kind](text)


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _families():
    return ex.family_rows()


@st.cache_data(show_spinner=False)
def _toronto():
    return ex.toronto_rows()


@st.cache_data(show_spinner=False)
def _searches():
    return ex.search_rows()


@st.cache_data(show_spinner=False)
def _ablation():
    return ex.ablation_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mls_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧹 Unabhängige Menge im großen Maßstab")
st.markdown(
    """
Welche **Fuhre** ist die größte, wenn Sendungen, die im Konflikt stehen, nicht zusammen fahren dürfen? Das ist die **größte unabhängige Menge**; auf großen Graphen sind die exakten Verfahren der Stücke 2, 3 und 6 am Ende. Zwei Werkzeuge gehen weiter: **Reduktionsregeln** verkleinern den Graphen vorab **exakt** (was übrig bleibt, heißt **Kern**), und eine **Lokalsuche** verbessert eine Lösung durch Tauschzüge, ohne Beweis. Die Frage der Demo: **Wie viel löst die Vorverarbeitung, wie nah kommt die Suche, und wann reicht beides sogar für ein exaktes Ergebnis?**

Das ist das achte Stück der **Härte-und-Struktur-Reihe** und der Zusammenfluss der Stücke 3 (Reduktion), 6 (Zerlegung) und der Lokalsuche aus den Trajektorien-Metaheuristiken. Weiter unten: die Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So arbeiten Reduktionen und Lokalsuche", expanded=True):
    st.markdown(
        """
1. **Reduzieren:** Fünf Regeln verändern den Graphen so, dass sich die Größe α der größten unabhängigen Menge **berechenbar** ändert: ein Knoten ohne Nachbarn oder mit nur einem Nachbarn darf in die Lösung, ein Knoten mit zwei verbundenen Nachbarn auch, zwei nicht verbundene Nachbarn werden mit ihm **gefaltet**, ein **dominierter** Knoten entfällt.
2. **Kern:** Bleibt nichts übrig, ist die Aufgabe durch die Regeln gelöst. Sonst bleibt ein kleinerer Graph mit demselben Optimum (plus dem Offset der festgelegten Knoten).
3. **Suchen:** Die **Lokalsuche** startet beim Greedy, tauscht einen Lösungsknoten gegen zwei (der **(1,2)-Tausch**), stört die Lösung zufällig und steigt wieder ab; ein gleich gutes Ergebnis wird angenommen (**Plateau**).
4. **Exakt?** Ist der Kern schmal genug, löst die Zerlegung aus Stück 6 ihn exakt; mit dem **Rücklift** entsteht eine größte unabhängige Menge des ganzen Graphen.

| Begriff | Bedeutung |
|---|---|
| **Kern** | der Graph, der nach den Regeln übrig bleibt; α(G) = Offset + α(Kern) |
| **Offset** | die Zahl der Knoten, die die Regeln schon festgelegt haben (Faltungen zählen mit) |
| **Faltung** | v mit den nicht benachbarten Nachbarn u, w wird mit ihnen zu einem Knoten verschmolzen; α sinkt um genau 1 |
| **Dominanz** | gilt N[v] ⊆ N[u] für benachbarte u, v, kann u gelöscht werden |
| **(1,2)-Tausch** | einen Lösungsknoten entfernen und zwei nicht benachbarte Nachbarn einfügen, die nur ihn als Lösungsnachbarn haben |
| **Plateau, Störung** | ein Ergebnis gleicher Größe wird angenommen; ein zufälliger Knoten wird erzwungen, seine Lösungsnachbarn gehen |
| **Rücklift** | aus einer Lösung des Kerns wird in umgekehrter Reihenfolge eine des Originals |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Konfliktgraph**")
    net = st.selectbox("Netztyp", list(C.NET_TYPES), format_func=C.NET_TYPES.get, key="net_select", help=C.NET_HELP)
    n = st.slider("Sendungen n", *bounds("n_slider"), key="n_slider", help="Zahl der Knoten (Raster: ungefähr, Seitenlänge ⌊√n⌉; 3-regulär: gerade Zahl; Toronto: die n Kreuzungen um den Mittelpunkt, höchstens 5 072).")
    par = st.slider(C.PAR_LABEL, *bounds("par_slider"), key="par_slider", help=C.NET_HELP)
    seed = st.number_input("Zufalls-Seed des Graphen", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Graphen erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Regeln und Suche**")
    rules = st.radio("Regelmenge", list(C.RULESET_ORDER), format_func=C.RULESET_NAMES.get, key="rules_radio",
                     help="Welche Reduktionsregeln vor der Suche laufen. „Keine Regel“ übergibt der Suche das ganze Netz; ohne Faltung oder Dominanz bleibt meist ein größerer Kern.")
    iters = st.slider("Iterationen der Lokalsuche", C.ITER_MIN, C.ITER_MAX, key="iters_slider", step=C.ITER_STEP,
                      help="Wie viele Störungen die Lokalsuche versucht (jeweils mit Abstieg). 0 heißt: nur der erste Abstieg vom Greedy.")

sync_query_params({"net_select": net, "n_slider": int(n), "par_slider": int(par), "seed_input": int(seed), "rules_radio": rules, "iters_slider": int(iters)})

settings = ev.Settings(net=net, n=int(n), par=int(par), seed=int(seed), rules=rules, iters=int(iters))
with st.spinner("Rechne..."):
    a = _analysis(settings)
g, red = a.graph, a.red
ref, proven = ev.reference(a)

tab_red, tab_search, tab_exact = st.tabs(["🧹 Reduzieren", "🔎 Suchen", "🎯 Exakt?"])

# --- Tab 1: Reduzieren ----------------------------------------------------------------------------------------------------------------------------

with tab_red:
    st.markdown("## 🧹 Was die Regeln erledigen")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Knoten", _i(g.n), delta=f"{_i(g.m)} Kanten", delta_color="off")
    m2.metric("Kern", _i(len(red.kernel)), delta=f"{ev._dec(red.kernel_share)} % der Knoten", delta_color="off", help="Knoten, die nach den Regeln noch übrig sind. Leer heißt: gelöst.")
    m3.metric("Offset", _i(red.offset), delta="von den Regeln festgelegt", delta_color="off", help="α(G) = Offset + α(Kern). Jede Faltung zählt eins.")
    m4.metric("Regelanwendungen", _i(sum(red.counts.values())), delta=f"{_i(red.counts['fold'])} Faltungen", delta_color="off")
    if g.n <= C.DRAW_MAX_N:
        st.plotly_chart(build_kernel_figure(g, red), width="stretch", key="kernel_main")
        st.caption("Orange: Knoten und Kanten des Kerns. Blass: von den Regeln erledigt. Gefaltete Knoten des Kerns stehen für drei Originalknoten und sind nicht eingezeichnet.")
    else:
        st.caption(f"Das Netz hat mehr als {_i(C.DRAW_MAX_N)} Knoten und wird nicht gezeichnet.")
    counts = pd.DataFrame({"Regel": [RULE_NAMES[r] for r in red.counts], "Anwendungen": [red.counts[r] for r in red.counts], "in der gewählten Regelmenge": ["ja" if r in a.rules else "nein" for r in red.counts]})
    st.dataframe(counts, hide_index=True, width="stretch")
    if g.n <= LOG_MAX_N and red.log:
        with st.expander("Protokoll der Schritte"):
            shown = red.log[: C.LOG_ROWS]
            st.dataframe(pd.DataFrame({"Schritt": [e["step"] for e in shown], "Regel": [RULE_NAMES[e["rule"]] for e in shown], "Was geschah": [e["text"] for e in shown]}), hide_index=True, width="stretch")
            if len(red.log) > C.LOG_ROWS:
                st.caption(f"Die ersten {C.LOG_ROWS} von {_i(len(red.log))} Schritten.")
    st.markdown("---")
    st.subheader("🔬 Experiment 1: Wie viel lösen die Regeln?")
    st.caption("Alle fünf Regeln, feste Instanzen. Grün: kein Kern (gelöst), orange: Teile bleiben, rot: mindestens 90 % bleiben.")
    rows1 = _families()
    st.plotly_chart(build_families_figure(rows1), width="stretch", key="families_chart")
    _show(ex.verdict_families(rows1))
    st.markdown("---")
    st.subheader("🔬 Experiment 5: Welche Regel bringt wie viel?")
    st.caption("Kern (Knoten) bei fünf festen Instanzen, wenn je eine Regel fehlt.")
    rows5 = _ablation()
    st.plotly_chart(build_ablation_figure(rows5), width="stretch", key="ablation_chart")
    _show(ex.verdict_ablation(rows5))

# --- Tab 2: Suchen ----------------------------------------------------------------------------------------------------------------------------------

with tab_search:
    st.markdown("## 🔎 Die Lokalsuche")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Greedy", _i(len(a.greedy)), delta=f"{ev._dec(ev.below(len(a.greedy), ref))} % unter {'dem Optimum' if proven else 'dem besten Wert'}", delta_color="off",
              help="Knoten nach kleinstem Grad, jeder freie Knoten kommt hinein.")
    s2.metric("Lokalsuche, ganzes Netz", _i(a.full.size), delta=f"{ev._dec(ev.below(a.full.size, ref))} % unter {'dem Optimum' if proven else 'dem besten Wert'}", delta_color="off",
              help=f"Nach {_i(a.full.iterations)} Iterationen; Start beim Greedy.")
    s3.metric("Lokalsuche, Kern", _i(len(a.lifted)), delta=f"{ev._dec(ev.below(len(a.lifted), ref))} % unter {'dem Optimum' if proven else 'dem besten Wert'}", delta_color="off",
              help="Auf dem Kern gesucht und mit dem Rücklift ins Original gehoben.")
    s4.metric("Zugriffe", _i(a.full.ops), delta="ganzes Netz", delta_color="off", help="Adjazenzzugriffe der Suche auf dem ganzen Netz: ein Maß für den Aufwand, keine Laufzeit.")
    if not a.valid:
        st.error("Eine der Lösungen besteht die Prüfung am Original nicht (zwei benachbarte Knoten in der Menge): Das darf nicht passieren, bitte melden.")
    st.plotly_chart(build_curve_figure(a), width="stretch", key="curve_main")
    st.caption("Beste Größe über den Iterationen, auf dem ganzen Netz und auf dem Kern (plus Offset). Die rote Linie ist das Optimum bzw., wenn keines bekannt ist, der beste gefundene Wert.")
    if g.n <= C.DRAW_MAX_N:
        st.plotly_chart(build_solution_figure(g, a.exact.solution or a.lifted), width="stretch", key="solution_main")
        st.caption("Rot: die gezeigte Lösung (die exakte, wenn sie berechnet wurde, sonst die der Lokalsuche auf dem Kern). Zwei rote Knoten sind nie benachbart.")
    st.markdown("---")
    st.subheader("🔬 Experiment 3: Wie nah kommt die Lokalsuche an das Optimum?")
    st.caption(f"Alle fünf Regeln, Zufalls-Seed {C.SEARCH_SEED} der Suche, bis {_i(C.SEARCH_ITERATIONS)} Iterationen. Vergleichswert: das Optimum (aus Regeln, Zerlegung oder Satz von König), sonst der beste gefundene Wert (dann nicht bewiesen).")
    with st.spinner("Rechne die Lokalsuche auf den Netzfamilien (einige Sekunden)..."):
        rows3 = _searches()
    st.plotly_chart(build_search_figure(rows3), width="stretch", key="search_chart")
    _show(ex.verdict_search(rows3))
    with st.expander("Tabelle zu Experiment 3"):
        st.dataframe(pd.DataFrame({
            "Netz": [r["name"] for r in rows3], "Knoten": [_i(r["n"]) for r in rows3], "Vergleichswert": [_i(r["ref"]) + ("" if r["proven"] else " (nicht bewiesen)") for r in rows3], "Greedy": [_i(r["greedy"]) for r in rows3],
            "100": [_i(r["curve"][100]) for r in rows3], "1 000": [_i(r["curve"][1000]) for r in rows3], "20 000 Iterationen": [_i(r["curve"][20000]) for r in rows3]}), hide_index=True, width="stretch")
    st.markdown("---")
    st.subheader("🔬 Experiment 4: Lohnt es, vor der Suche zu reduzieren?")
    st.caption(f"Dieselben Netze, die nach den Regeln einen Kern behalten: die Lokalsuche nach {_i(C.SEARCH_ITERATIONS)} Iterationen auf dem ganzen Netz gegen die auf dem Kern.")
    rows4 = ex.kernel_vs_full_rows(rows3)
    st.plotly_chart(build_kernel_vs_full_figure(rows4), width="stretch", key="kernel_vs_full_chart")
    _show(ex.verdict_kernel_vs_full(rows4))

# --- Tab 3: Exakt? ------------------------------------------------------------------------------------------------------------------------------------

with tab_exact:
    st.markdown("## 🎯 Reicht die Vorverarbeitung für ein exaktes Ergebnis?")
    ex_res = a.exact
    e1, e2, e3, e4 = st.columns(4)
    if ex_res.status in ("exact", "koenig"):
        e1.metric("α", _i(ex_res.value), delta=("durch die Regeln allein" if not red.kernel else "durch die Zerlegung des Kerns" if ex_res.status == "exact" else "bipartit: n − Matching"), delta_color="off",
                  help="Größe einer größten unabhängigen Menge, bewiesen.")
    else:
        e1.metric("α", "–", delta="nicht exakt bekannt", delta_color="off", help="Die Zerlegung ist zu breit; der beste gefundene Wert steht im Reiter „Suchen“.")
    e2.metric("Breite der Zerlegung des Kerns", "–" if ex_res.width is None else _i(ex_res.width), delta=("Min-Grad-Breite über " + str(C.ORDER_WIDTH_LIMIT)) if ex_res.status == "too_wide" else None, delta_color="off",
              help="Größter Beutel minus 1 (Min-Fill-Ordnung aus Stück 5), nur gerechnet, wenn die Min-Grad-Elimination mit höchstens 25 Knoten je Beutel auskommt.")
    e3.metric("Zellen", _i(ex_res.cells) if ex_res.status == "exact" else "–", delta=(f"Vorhersage {_i(ex_res.predicted)}" if ex_res.predicted else None), delta_color="off",
              help=f"Summe über alle Beutel von 2^Beutelgröße; das Budget ist {_i(C.EXACT_CELL_BUDGET)} Zellen.")
    if a.brute is not None:
        e4.metric("Brute-Force-Probe", "bestanden" if (ex_res.value == a.brute) else "NICHT bestanden", delta=f"alle 2^{g.n} Teilmengen: α = {a.brute}", delta_color="off", help=f"Gleicher Wert durch Aufzählen aller Teilmengen (nur bis n = {C.BRUTE_MAX_N}).")
    else:
        e4.metric("Brute-Force-Probe", "–", help=f"Nur bis n = {C.BRUTE_MAX_N} Knoten.")
    st.markdown("## ❓ Kernfrage: Wie viel löst die Vorverarbeitung, wie nah kommt die Suche, und geht es sogar exakt?")
    _show(ev.verdict_main(a))
    st.markdown("---")
    st.subheader("🔬 Experiment 2: Reduktion macht die Zerlegung auf einem Straßennetz möglich")
    st.caption(f"Toronto-Ausschnitte, alle fünf Regeln, Min-Fill-Zerlegung (Stück 5) und DP (Stück 6) mit Zellbudget {_i(C.EXACT_CELL_BUDGET)}.")
    with st.spinner("Rechne die Toronto-Ausschnitte..."):
        rows2 = _toronto()
    st.plotly_chart(build_toronto_figure(rows2), width="stretch", key="toronto_chart")
    _show(ex.verdict_toronto(rows2))
    with st.expander("Tabelle zu Experiment 2"):
        st.dataframe(pd.DataFrame({
            "Kreuzungen": [_i(r["n"]) for r in rows2], "Kanten": [_i(r["m"]) for r in rows2], "Breite ganz": [r["full_width"] for r in rows2], "Kern": [_i(r["kernel"]) for r in rows2],
            "Breite Kern": [r["kernel_width"] for r in rows2], "Zellen": [_i(r["cells"]) for r in rows2], "α": [_i(r["alpha"]) for r in rows2]}), hide_index=True, width="stretch")

st.markdown("---")

# --- Brücken -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔗 Brücken: Stück 3, Stück 6 und die Trajektorien-Metaheuristiken")
st.markdown(
    "**Stück 3** ([vertex-cover-demo](https://github.com/sebastian-hanisch/vertex-cover-demo)) hat die Grad-1-Regel und den LP-Kern, aber keine Faltung, keine Dominanz und keine Lokalsuche. "
    "**Stück 6** ([tree-decomposition-dp-demo](https://github.com/sebastian-hanisch/tree-decomposition-dp-demo)) rechnet auf der Zerlegung exakt, scheiterte aber an der Breite des ganzen Straßennetzes (50); nach den Regeln hier ist der Kern des Ausschnitts schmal genug (Experiment 2). "
    "Die Lokalsuche verwandt mit der iterierten Lokalsuche der Trajektorien-Metaheuristiken ([iterated-local-search-demo](https://github.com/sebastian-hanisch/iterated-local-search-demo)): dort stört eine Doppelbrücke eine Rundtour, hier erzwingt die Störung einen Knoten der Menge."
)

st.markdown("---")

# --- Grenzen ---------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Vereinfachte Lokalsuche** | Es ist die iterierte (1,2)-Lokalsuche nach Andrade, Resende und Werneck ohne ihre Neustarts, ohne den (2,3)-Tausch und ohne inkrementelle Kandidatenlisten; die Ergebnisse gelten für diese Fassung. | – |
| **Stand der Technik nur als Einordnung** | Branch-and-Reduce-Löser (Akiba und Iwata), evolutionäre Verfahren mit Kernbildung (ReduMIS, Lamm u. a.) und Reduktionen mit linearer Laufzeit (Chang, Li, Zhang) sind stärker und nicht nachgebaut. | – |
| **Kein Beweis der Lokalsuche** | Ohne exakten Vergleichswert ist „bester gefundener Wert“ nur eine Untergrenze; auf dem 3-regulären Netz und dem großen Dreiecksgitter ist das Optimum hier nicht bekannt. | – |
| **Exakt nur bei schmalem Kern** | Die Zerlegung rechnet bis etwa Breite 18 bis 19 (Zellbudget {_i(C.EXACT_CELL_BUDGET)}); bipartite Netze löst der Satz von König trotzdem. | – |
| **Ungewichtet** | Jeder Knoten zählt eins; gewichtete Regeln und Gewichte in der Suche kennt die Demo nicht (gewichtet: Stück 6). | – |
| **Aufwand in Zugriffen und Zellen** | Verglichen wird in Adjazenzzugriffen, Zellen und Knoten, nicht in Sekunden. | – |
| **Synthetische Netze** | Außer dem Toronto-Ausschnitt ({_i(S.toronto_size())} Kreuzungen) sind alle Netze erzeugt. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** Gegeben ein ungerichteter Graph $G = (V, E)$. Eine **unabhängige Menge** $I \subseteq V$ enthält keine Kante; gesucht ist die Größe

$$\alpha(G) = \max \{\, |I| : I \text{ unabhängig} \,\}.$$

**Grad 0 und Grad 1.** Hat $v$ höchstens einen Nachbarn $u$, so gibt es eine größte unabhängige Menge mit $v$, und

$$\alpha(G) = 1 + \alpha\bigl(G - N[v]\bigr),$$

wobei $N[v]$ die geschlossene Nachbarschaft ist. Dasselbe gilt für einen Knoten, dessen Nachbarn eine Clique bilden (Dreieck bei Grad 2).

**Faltung.** Hat $v$ genau zwei nicht benachbarte Nachbarn $u, w$, so entsteht $G'$, indem $v, u, w$ zu einem neuen Knoten $x$ mit $N(x) = (N(u) \cup N(w)) \setminus \{v\}$ verschmolzen werden. Dann gilt

$$\alpha(G) = \alpha(G') + 1.$$

**Rücklift.** Aus einer größten unabhängigen Menge $I'$ von $G'$ entsteht eine von $G$: liegt $x$ in $I'$, ersetzt man $x$ durch $u$ und $w$, sonst fügt man $v$ hinzu. In beiden Fällen wächst die Menge um genau einen Knoten.

**Dominanz.** Gilt $N[v] \subseteq N[u]$ für benachbarte $u, v$, dann gibt es eine größte unabhängige Menge ohne $u$ (ersetzt man $u$ in ihr durch $v$, bleibt sie unabhängig), also

$$\alpha(G) = \alpha(G - u).$$

**Kern.** Nach allen Regeln gilt mit dem Offset $o$ (Zahl der festgelegten Knoten einschließlich der Faltungen)

$$\alpha(G) = o + \alpha(K).$$

**(1,2)-Tausch.** Für eine unabhängige Menge $I$ und $x \in I$ sei $T(x)$ die Menge der Nachbarn von $x$, die außer $x$ keinen Nachbarn in $I$ haben. Gibt es zwei nicht benachbarte $u, w \in T(x)$, so ist $(I \setminus \{x\}) \cup \{u, w\}$ unabhängig und um einen Knoten größer. Eine Menge ohne solchen Tausch heißt (1,2)-optimal.

**Satz von König.** Ist $G$ bipartit mit einem größten Matching der Größe $\nu$, so gilt

$$\alpha(G) = |V| - \nu.$$

**Annahmen.**

| Annahme | Inhalt | Wer setzt an |
|---|---|---|
| Einfacher Graph | keine Schleifen, keine Mehrfachkanten | – |
| Ungewichtet | jeder Knoten zählt eins | – |
| Feste Regelreihenfolge | immer die einfachste anwendbare Regel zuerst, Gleichstand: kleinster Knoten | – |

**Literatur.** Alle Angaben sind vor dem Zitieren geprüft:
- Andrade, D. V., Resende, M. G. C., & Werneck, R. F. (2012). *Fast local search for the maximum independent set problem.* Journal of Heuristics 18(4), 525–547.
- Akiba, T., & Iwata, Y. (2016). *Branch-and-reduce exponential/FPT algorithms in practice: A case study of vertex cover.* Theoretical Computer Science 609, 211–225.
- Lamm, S., Sanders, P., Schulz, C., Strash, D., & Werneck, R. F. (2017). *Finding near-optimal independent sets at scale.* Journal of Heuristics 23(4), 207–229.
- Chang, L., Li, W., & Zhang, W. (2017). *Computing a near-maximum independent set in linear time by reducing-peeling.* Proceedings of SIGMOD 2017.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
