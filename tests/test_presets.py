"""Presets: gültige Werte und jede Zahl der Hilfetexte gegen die echten Auswertungsfunktionen."""

import cen_constants as C
import cen_evaluation as ev
from cen_presets import PRESET_KEYS, SETTING_SPECS


def _settings(name):
    p = C.PRESETS[name]
    return ev.Settings(p.get("kind", "city"), p.get("side", C.DEFAULT_SIDE), p.get("blocked", C.DEFAULT_BLOCKED), p.get("nettype", "grid"), p.get("kbarbell", C.DEFAULT_BARBELL_K),
                        p.get("seed", C.DEFAULT_SEED), p.get("order", "fixed"), C.DEFAULT_DAMPING)


def _has(name, *values):
    for v in values:
        assert v in C.PRESET_HELP[name], (name, v)


def test_every_preset_has_valid_values_and_a_help_text():
    assert list(C.PRESETS) == list(C.PRESET_HELP) and len(C.PRESETS) == 7
    for name, p in C.PRESETS.items():
        assert set(p) <= set(PRESET_KEYS) and {"kind", "step"} <= set(p) and p["step"] in C.STEPS
        for key, state_key in PRESET_KEYS.items():
            if key in p and state_key in SETTING_SPECS:
                spec = SETTING_SPECS[state_key]
                assert spec.caster(p[key]) == p[key], (name, key)
                if spec.lo is not None:
                    assert spec.lo <= p[key] <= spec.hi, (name, key)
        assert C.PRESET_HELP[name].strip()


def test_help_barbell_preset():
    inst, a = ev.analyse(_settings("Barbell (Lehrbuch)"))
    assert a.n == 10 and a.m == 21
    u, v = a.ll.bridges[0]
    measured, formula = a.bridge_check[(u, v)]
    assert measured == formula == 25.0
    assert max(a.betweenness_node) == 20.0
    _has("Barbell (Lehrbuch)", "25", "5*5", "20")


def test_help_standard_and_many_bridges_presets():
    inst, a = ev.analyse(_settings("Standardfall (Voreinstellung)"))
    assert (a.n, a.m, len(a.ll.bridges), len(a.ll.articulation)) == (144, 185, 21, 17)
    _has("Standardfall (Voreinstellung)", "144 Knoten", "185 Straßen", "21 Brücken", "17 Artikulationspunkte")

    inst2, a2 = ev.analyse(_settings("Viele Brücken (hoher Sperranteil)"))
    assert (a2.n, a2.m, len(a2.ll.bridges), len(a2.ll.articulation), len(a2.ll.comp_size)) == (144, 106, 90, 61, 42)
    assert max(a2.ll.comp_size.values()) == 31
    _has("Viele Brücken (hoher Sperranteil)", "106 Straßen", "42 Komponenten", "90 Brücken", "61 Artikulationspunkte")


def test_help_random_preset():
    inst, a = ev.analyse(_settings("Zufallsgraph"))
    assert (a.n, a.m, len(a.ll.bridges), len(a.ll.articulation)) == (144, 264, 19, 17)
    _has("Zufallsgraph", "264 Straßen", "19 Brücken", "17 Artikulationspunkte")


def test_help_cost_and_correlation_presets():
    rows = ev.cost_sweep(C.COST_SIDES)
    last = rows[-1]
    assert last["n"] == 196 and last["naive"] == 11925316 and last["brandes"] == 220050
    _has("Aufwand: naiv gegen Brandes", "11925316", "220050", "54-Fache")


def test_help_pagerank_uneven_preset():
    inst, a = ev.analyse(_settings("PageRank auf ungleichmäßigem Netz"))
    assert a.n == 144 and a.m == 79
    assert round(min(a.pagerank), 4) == 0.0014 and round(max(a.pagerank), 4) == 0.0195
    _has("PageRank auf ungleichmäßigem Netz", "79 Straßen", "0.0014", "0.0195")
