"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; jedes Preset rechnet durch und hält, was sein Name verspricht."""

import mls_constants as C
import mls_evaluation as ev
import mls_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name] and "Platzhalter" not in C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.PAR_MIN <= preset["par"] <= C.PAR_MAX and 0 <= preset["seed"] <= C.SEED_MAX and C.ITER_MIN <= preset["iters"] <= C.ITER_MAX, name
        assert preset["iters"] % C.ITER_STEP == 0 and preset["net"] in C.NET_TYPES and preset["rules"] in C.RULESETS, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(**first) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_choice_specs_carry_their_options():
    assert P.SETTING_SPECS["net_select"].options == tuple(C.NET_TYPES) and P.SETTING_SPECS["rules_radio"].options == C.RULESET_ORDER


def test_rule_sets_are_complete_and_named():
    assert set(C.RULESETS) == set(C.RULESET_NAMES) == set(C.RULESET_ORDER) and C.DEFAULT_RULESET in C.RULESETS
    assert all(isinstance(rules, tuple) for rules in C.RULESETS.values())


def test_every_preset_analyses_and_passes_the_check_at_the_original():
    for name, preset in C.PRESETS.items():
        a = ev.analyse(ev.Settings(**preset))
        assert a.valid and a.exact is not None, name


def test_the_preset_names_do_not_promise_more_than_the_numbers_show():
    r = {name: ev.analyse(ev.Settings(**preset)) for name, preset in C.PRESETS.items()}
    assert len(r["Dünn: die Regeln lösen alles"].red.kernel) == 0
    assert r["Toronto: das ganze Netz"].exact.status == "exact" and len(r["Toronto: das ganze Netz"].red.kernel) > 0
    raster = r["Raster: die Regeln tun nichts"]
    assert raster.red.kernel_share > 99 and raster.exact.status == "koenig"
    tri = r["Dreiecksgitter: die Suche braucht Zeit"]
    assert tri.exact.status == "too_wide" and tri.full.size < 300 and len(tri.greedy) < tri.full.size
    reg = r["3-regulär: die Suche ohne Beweis"]
    assert len(reg.red.kernel) == 500 and reg.exact.status == "too_wide"
    king = r["King-Graph: nur die Dominanz"]
    assert len(king.red.kernel) == 400 and len(ev.analyse(ev.Settings(**dict(C.PRESETS["King-Graph: nur die Dominanz"], rules="all"))).red.kernel) == 0
