"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


# --- Zusätzlich: die echten Regler dieser Demo (Auswahlfelder, Optionsfelder, Seed, Permalink, Verdikte) --------------------------------------------------

def _slider(at, label_start):
    """Slider nach Beschriftung."""
    return next(s for s in at.slider if s.label.startswith(label_start))


def _selectbox(at, label):
    return next(s for s in at.selectbox if s.label == label)


def _radio(at, label_start):
    return next(r for r in at.radio if r.label.startswith(label_start))


def _texts(at):
    return [x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning]


def _metric(at, label):
    return next(m for m in at.metric if m.label == label)


def test_every_net_type_and_every_rule_set_renders_without_exception():
    import mls_constants as C
    for key in C.NET_TYPES:
        at = _fresh_app()
        _selectbox(at, "Netztyp").set_value(key).run(timeout=TIMEOUT)         # roher Schlüssel (select_index kollidiert in AppTest mit format_func)
        assert not at.exception, (key, [str(e) for e in at.exception])
    for key in C.RULESET_ORDER:
        at = _fresh_app()
        _radio(at, "Regelmenge").set_value(key).run(timeout=TIMEOUT)
        assert not at.exception, (key, [str(e) for e in at.exception])


def test_extreme_seeds_do_not_raise():
    for seed in (0, 999999):
        at = _fresh_app()
        at.number_input[0].set_value(seed).run(timeout=TIMEOUT)
        assert not at.exception, (seed, [str(e) for e in at.exception])


def test_the_slowest_corner_still_renders():
    at = _fresh_app()
    _selectbox(at, "Netztyp").set_value("scalefree").run(timeout=TIMEOUT)
    _slider(at, "Sendungen").set_value(5072).run(timeout=TIMEOUT)
    _slider(at, "Parameter").set_value(60).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("nicht lösbar" in t for t in _texts(at))


def test_permalink_parameters_are_applied():
    at = AppTest.from_file(APP_PATH)
    for k, v in (("net", "tri"), ("n", "36"), ("p", "10"), ("seed", "5"), ("r", "no_fold"), ("it", "1500")):
        at.query_params[k] = v
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert _slider(at, "Sendungen").value == 36 and _slider(at, "Parameter").value == 10 and _slider(at, "Iterationen").value == 1500 and at.number_input[0].value == 5
    assert _selectbox(at, "Netztyp").value == "tri" and _radio(at, "Regelmenge").value == "no_fold"


def test_invalid_permalink_values_fall_back_to_the_defaults():
    at = AppTest.from_file(APP_PATH)
    at.query_params["net"] = "kreis"
    at.query_params["n"] = "viel"
    at.query_params["r"] = "alles"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert _selectbox(at, "Netztyp").value == "random" and _slider(at, "Sendungen").value == 24 and _radio(at, "Regelmenge").value == "all"


def test_the_core_question_verdict_and_the_experiment_verdicts_are_shown():
    at = _fresh_app()
    texts = _texts(at)
    assert any(t.startswith("Die Regeln lassen 7 von 24 Knoten (29,2 %) als Kern") for t in texts)                      # Standardfall: Lehrbeispiel
    assert any(t.startswith("Bei **4 von 10** Netzen bleibt kein Kern") for t in texts)
    assert any(t.startswith("Mit den Regeln fällt die Breite des ganzen Ausschnitts (5.072 Kreuzungen) von 50 auf 12") for t in texts)
    assert any(t.startswith("Nach 20.000 Iterationen liegt die Lokalsuche auf dem ganzen Netz höchstens") for t in texts)
    assert any(t.startswith("Bei gleicher Iterationszahl (20.000) erreicht die Lokalsuche auf dem Kern bei 3 von 7 Netzen mehr") for t in texts)
    assert any(t.startswith("Ohne die Faltung wird der Kern bei 4 von 5 Netzen größer") for t in texts)


def test_the_default_metrics_show_the_hand_checked_lesson_example():
    at = _fresh_app()
    assert _metric(at, "Knoten").value == "24" and _metric(at, "Kern").value == "7" and _metric(at, "Offset").value == "6"
    assert _metric(at, "Greedy").value == "8" and _metric(at, "α").value == "9"
    assert not at.error


def test_the_brute_force_probe_only_appears_for_tiny_graphs():
    at = _fresh_app()
    assert _metric(at, "Brute-Force-Probe").value == "–"                                                                  # n = 24 > 18
    _slider(at, "Sendungen").set_value(14).run(timeout=TIMEOUT)
    assert _metric(at, "Brute-Force-Probe").value == "bestanden"


def test_the_toronto_preset_is_solved_exactly():
    at = _fresh_app()
    at.sidebar.button(key="preset_Toronto: das ganze Netz").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert _metric(at, "α").value == "2.448"
    assert any("α = **2.448**" in t for t in _texts(at))


def test_the_grid_preset_uses_the_koenig_theorem():
    at = _fresh_app()
    at.sidebar.button(key="preset_Raster: die Regeln tun nichts").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Satz von König" in t for t in _texts(at))


def test_the_three_regular_preset_reports_that_nobody_solves_it_exactly():
    at = _fresh_app()
    at.sidebar.button(key="preset_3-regulär: die Suche ohne Beweis").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("exakt ist er nicht lösbar" in t for t in _texts(at)) and _metric(at, "α").value == "–"
