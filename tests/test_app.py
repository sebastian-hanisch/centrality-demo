"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt für jede Instanz, Brandes-Regler, Randwerte, Permalink-Grenzen, bedingte Regler, Berechnungen auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import cen_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=300)
    state.setdefault("cen_step", step)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _click(at, key):
    next(b for b in at.button if b.key == key).click().run()


def test_default_run_shows_the_summary():
    at = _run()
    _ok(at)
    assert {"Knoten", "Kanten", "Brücken", "Artikulationspunkte"} <= {m.label for m in at.metric}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run(kind_select="city", side_slider=8)
    _click(at, f"preset_{name}")
    _ok(at)
    p, ss = C.PRESETS[name], at.session_state
    assert ss["kind_select"] == p["kind"] and ss["cen_step"] == p["step"]
    for key, state_key in (("side", "side_slider"), ("blocked", "blocked_select"), ("nettype", "nettype_select"), ("kbarbell", "kbarbell_slider"), ("seed", "seed_input"), ("order", "order_select")):
        if key in p:
            assert ss[state_key] == p[key], (name, key)


@pytest.mark.parametrize("step", [1, 2, 3, 4])
@pytest.mark.parametrize("kind", ["city", "barbell"])
def test_every_step_runs_for_every_kind(step, kind):
    at = _run(step=step, kind_select=kind, side_slider=8, kbarbell_slider=4)
    _ok(at)
    assert at.session_state["cen_step"] == step


@pytest.mark.parametrize("nettype", ["grid", "random"])
def test_step1_every_measure(nettype):
    for measure in C.MEASURES:
        at = _run(step=1, kind_select="city", side_slider=8, nettype_select=nettype, measure_select=measure)
        _ok(at)


def test_pagerank_damping_slider_only_shown_for_pagerank_measure():
    at = _run(step=1, measure_select="pagerank")
    assert any(s.key == "damping_widget" for s in at.slider)
    at2 = _run(step=1, measure_select="degree")
    assert not any(s.key == "damping_widget" for s in at2.slider)


def test_brandes_replay_slider_every_position():
    at = _run(step=2, kind_select="city", side_slider=6)
    n_total = at.session_state.get("brandes_step")
    if n_total and n_total > 1:
        for k in sorted({1, max(1, n_total // 2), n_total}):
            at2 = _run(step=2, kind_select="city", side_slider=6, brandes_step=k)
            _ok(at2)
            assert at2.session_state["brandes_step"] == k


def test_bridge_selection_step3_barbell_always_has_a_bridge():
    at = _run(step=3, kind_select="barbell", kbarbell_slider=5)
    _ok(at)
    assert any(sb.key == "bridge_select" for sb in at.selectbox)


def test_step3_handles_no_bridge_case():
    at = _run(step=3, kind_select="city", side_slider=8, nettype_select="random", blocked_select=0.0)
    _ok(at)


def test_on_demand_experiments_step4():
    at = _run(step=4, kind_select="city", side_slider=8)
    for key in ("cost_start", "corr_start"):
        _click(at, key)
        _ok(at)
    assert len(at.get("plotly_chart")) >= 1


def test_large_instance_gates_vitality_behind_a_button():
    at = _run(step=4, kind_select="city", side_slider=24)                    # 576 Knoten > VITALITY_MAX_N
    _ok(at)
    assert any("Vitalität" in w.value for w in at.warning)
    assert any(b.key == "vitality_force_btn" for b in at.button)


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="nope", side="9999", blocked="0.33", nettype="sideways", kbarbell="99", seed="-4", order="up", step="9").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["kind_select"], ss["side_slider"], ss["blocked_select"], ss["nettype_select"], ss["kbarbell_slider"], ss["seed_input"], ss["order_select"], ss["cen_step"]) == (
        "city", C.SIDE_MAX, C.DEFAULT_BLOCKED, "grid", C.BARBELL_K_MAX, 0, "fixed", 1)


def test_permalink_accepts_valid_values_and_writes_them_back():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="city", side="9", blocked="0.5", nettype="random", seed="7", step="2").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["side_slider"], ss["blocked_select"], ss["nettype_select"], ss["seed_input"], ss["cen_step"]) == (9, 0.5, "random", 7, 2)
    assert at.query_params["seed"] in (["7"], "7") and at.query_params["step"] in (["2"], "2")
    assert ss["side_widget"] == 9 and ss["seed_widget"] == 7


def test_sidebar_shows_the_controls_that_belong_to_the_instance():
    city = _run(kind_select="city")
    assert any(w.key == "side_widget" for w in city.slider) and not any(w.key == "kbarbell_widget" for w in city.slider)
    barbell = _run(kind_select="barbell")
    assert any(w.key == "kbarbell_widget" for w in barbell.slider) and not any(w.key == "side_widget" for w in barbell.slider)


def test_switching_kind_back_and_forth_keeps_the_stored_values():
    at = _run(kind_select="city", side_slider=20, blocked_select=0.5, seed_input=11)
    at.session_state["kind_select"] = "barbell"
    at.run()
    _ok(at)
    at.session_state["kind_select"] = "city"
    at.run()
    _ok(at)
    assert at.session_state["side_widget"] == 20 and at.session_state["blocked_widget"] == 0.5 and at.session_state["seed_widget"] == 11


def test_dice_button_changes_the_seed_and_the_visible_widget():
    at = _run(kind_select="city")
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old and at.session_state["seed_widget"] == at.session_state["seed_input"]


@pytest.mark.parametrize("kw", [dict(kind_select="city", side_slider=C.SIDE_MIN), dict(kind_select="city", side_slider=C.SIDE_MAX), dict(kind_select="barbell", kbarbell_slider=C.BARBELL_K_MIN),
                                 dict(kind_select="barbell", kbarbell_slider=C.BARBELL_K_MAX), dict(kind_select="city", blocked_select=min(C.BLOCKED_OPTIONS)),
                                 dict(kind_select="city", blocked_select=max(C.BLOCKED_OPTIONS))])
def test_extreme_settings_run_on_every_step(kw):
    for step in (1, 2, 3):
        _ok(_run(step=step, **kw))


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Brandes" in m.value and "Freeman" in m.value for e in at.expander for m in e.markdown)
