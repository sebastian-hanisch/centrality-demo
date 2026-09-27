"""Rauchtests der Auswertung: analyse (Standardfall, Barbell), cost_sweep, correlation_sweep, bridge_betweenness_check."""

import cen_algorithm as A
import cen_constants as C
import cen_evaluation as ev


def test_analyse_city_default():
    inst, a = ev.analyse(ev.Settings(kind="city", side=8, blocked=0.3, nettype="grid", seed=1))
    assert a.n == 64 and a.m == inst.m
    assert len(a.degree) == a.n and len(a.closeness) == a.n and len(a.betweenness_node) == a.n and len(a.pagerank) == a.n
    assert len(a.vitality) == a.n
    for v in a.vitality:
        assert v >= -1e-9
    assert sum(a.pagerank) == 1.0 or abs(sum(a.pagerank) - 1.0) < 1e-6


def test_analyse_skips_vitality_when_asked():
    inst, a = ev.analyse(ev.Settings(kind="city", side=6, blocked=0.3, nettype="grid", seed=1), compute_vitality=False)
    assert a.vitality is None


def test_analyse_barbell_bridge_check():
    inst, a = ev.analyse(ev.Settings(kind="barbell", k_barbell=5))
    assert a.n == 10 and len(a.ll.bridges) == 1
    u, v = a.ll.bridges[0]
    measured, formula = a.bridge_check[(u, v)]
    assert measured == formula == 25.0


def test_cost_sweep_increasing_and_naive_ge_brandes():
    rows = ev.cost_sweep((3, 4, 5))
    assert [r["side"] for r in rows] == [3, 4, 5]
    for r in rows:
        assert r["naive"] >= r["brandes"] > 0


def test_correlation_sweep_values_in_range():
    rows = ev.correlation_sweep((0.3,), nettypes=("grid",), side=8, seeds=(100000, 100001))
    assert len(rows) == 1
    row = rows[0]
    for key in ("degree", "closeness", "betweenness", "pagerank"):
        assert -1.0 <= row[key] <= 1.0


def test_bridge_betweenness_check_is_always_exact():
    from cen_scenario import barbell_instance, generate
    instances = [barbell_instance(k) for k in (3, 4, 5, 6)] + [generate(6, 0.4, "grid", s) for s in range(1, 6)]
    frac, total = ev.bridge_betweenness_check(instances)
    assert frac == 1.0 and total > 0


def test_bridge_betweenness_check_handles_no_bridges():
    from cen_scenario import generate
    instances = [generate(5, 0.0, "grid", 1)]                    # ein vollstaendiges Raster hat idR Rundwege, kann aber auch Bruecken haben - nur sicherstellen, dass es nicht crasht
    frac, total = ev.bridge_betweenness_check(instances)
    assert frac is None or 0.0 <= frac <= 1.0


def test_instance_invalid_kind_raises():
    import pytest
    with pytest.raises(ValueError):
        ev.instance(ev.Settings(kind="nope"))


def test_naive_max_n_is_practical():
    """Buchführung: die naive Betweenness läuft bei NAIVE_MAX_N (Worst Case: ungesperrtes Raster) in praktikabler Zeit."""
    import math
    import cen_scenario as S
    side = int(math.isqrt(C.NAIVE_MAX_N))
    inst = S.generate(side, 0.0, "grid", 1)
    adj = A.adjacency(inst.n, inst.edges)
    assert inst.n <= C.NAIVE_MAX_N
    A.betweenness_naive(adj)                                     # nur: läuft ohne Timeout durch
