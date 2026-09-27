"""Jede Zahl aus README und Konstanten-Kommentar, nachgerechnet über die echten Auswertungsfunktionen (cost_sweep/correlation_sweep sind in cen_evaluation.py selbst zwischengespeichert)."""

import cen_constants as C
import cen_evaluation as ev


def _cost_rows():
    return ev.cost_sweep(C.COST_SIDES)


def _corr_rows():
    return ev.correlation_sweep(C.CORR_BLOCKED)


def test_cost_sweep_matches_constants_comment():
    rows = {r["side"]: r for r in _cost_rows()}
    want_naive = {3: 295, 4: 1698, 5: 5933, 6: 19036, 7: 48651, 8: 109876, 9: 276881, 10: 595376, 11: 1075301, 12: 2294354, 14: 11925316}
    want_brandes = {3: 259, 4: 1110, 5: 2935, 6: 6600, 7: 13106, 8: 22682, 9: 35370, 10: 50922, 11: 77376, 12: 119142, 14: 220050}
    for side in C.COST_SIDES:
        assert rows[side]["naive"] == want_naive[side], side
        assert rows[side]["brandes"] == want_brandes[side], side
    assert rows[14]["naive"] / rows[14]["brandes"] == 11925316 / 220050


def test_cost_ratio_grows_with_size():
    rows = {r["side"]: r for r in _cost_rows()}
    ratios = [rows[side]["naive"] / rows[side]["brandes"] for side in C.COST_SIDES]
    assert ratios == sorted(ratios)                            # streng monoton wachsend
    assert ratios[0] < 2.0 and ratios[-1] > 50.0


def test_correlation_sweep_betweenness_usually_wins():
    rows = _corr_rows()
    wins = sum(1 for r in rows if r["betweenness"] == max(r["degree"], r["closeness"], r["betweenness"], r["pagerank"]))
    assert wins >= len(rows) - 2                                # Betweenness gewinnt fast immer (Ausnahme: ungesperrtes Raster, wo Closeness fast gleichauf liegt)


def test_correlation_sweep_grid_zero_blocked_is_the_exception():
    rows = {(r["nettype"], r["blocked"]): r for r in _corr_rows()}
    row = rows[("grid", 0.0)]
    assert row["closeness"] > 0.98 and row["betweenness"] > 0.98
    assert row["pagerank"] < 0.3                                 # PageRank ist hier der schlechteste Vorhersager


def test_correlation_sweep_random_pagerank_recovers():
    rows = {(r["nettype"], r["blocked"]): r for r in _corr_rows()}
    for blocked in C.CORR_BLOCKED:
        assert rows[("random", blocked)]["pagerank"] > 0.8


def test_bridge_theorem_holds_on_a_large_bridge_sample():
    from cen_scenario import barbell_instance, generate

    instances = [barbell_instance(k) for k in range(3, 11)]
    for side in (3, 4, 5, 6, 7, 8, 9, 10):
        for blocked in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
            for seed in range(1, 6):
                instances.append(generate(side, blocked, "grid", seed))
    frac, total = ev.bridge_betweenness_check(instances)
    assert total >= 200 and frac == 1.0


def test_barbell_by_hand_numbers():
    inst, a = ev.analyse(ev.Settings(kind="barbell", k_barbell=5))
    assert a.n == 10 and a.m == 21
    assert sorted(a.degree) == [4] * 8 + [5, 5]
    u, v = a.ll.bridges[0]
    measured, formula = a.bridge_check[(u, v)]
    assert measured == 25.0 and formula == 25.0
    assert measured == max(a.betweenness_edge.values())
