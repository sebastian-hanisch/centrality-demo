"""Rauchtests der Instanzen: Betriebsnetz (Raster/Zufallsgraph, gesperrter Anteil) und Barbell-Graph."""

import pytest

import cen_scenario as S


def test_generate_grid_basic():
    inst = S.generate(6, 0.0, "grid", 1)
    assert inst.n == 36 and inst.kind == "city" and inst.nettype == "grid"
    assert inst.m == len(S.grid_edges(6))
    for u, v, w in inst.edges:
        assert u < v and w > 0


def test_generate_blocks_the_right_share():
    inst = S.generate(10, 0.3, "grid", 5)
    total = len(S.grid_edges(10))
    assert inst.m == total - int(round(0.3 * total))
    assert len(inst.blocked_edges) == int(round(0.3 * total))


def test_generate_random_same_edge_count_no_blocked_edges():
    inst_grid = S.generate(8, 0.4, "grid", 3)
    inst_rand = S.generate(8, 0.4, "random", 3)
    assert inst_rand.m == inst_grid.m
    assert inst_rand.blocked_edges == ()
    for u, v, w in inst_rand.edges:
        assert u < v


def test_generate_invalid_nettype_or_side_raises():
    with pytest.raises(ValueError):
        S.generate(6, 0.0, "diagonal", 1)
    with pytest.raises(ValueError):
        S.generate(1, 0.0, "grid", 1)


def test_generate_is_deterministic():
    a = S.generate(9, 0.35, "grid", 42)
    b = S.generate(9, 0.35, "grid", 42)
    assert a.edges == b.edges and (a.xy == b.xy).all()


def test_barbell_instance_shape():
    inst = S.barbell_instance(5)
    assert inst.kind == "barbell" and inst.n == 10
    # 2 * C(5,2) Cliquenkanten + 1 Brücke
    assert inst.m == 2 * (5 * 4 // 2) + 1
    degs = {}
    for u, v, _ in inst.edges:
        degs[u] = degs.get(u, 0) + 1
        degs[v] = degs.get(v, 0) + 1
    # Brückenenden (4 und 5) haben Grad k=5, alle anderen Grad k-1=4
    assert degs[4] == 5 and degs[5] == 5
    for x in (0, 1, 2, 3, 6, 7, 8, 9):
        assert degs[x] == 4


def test_barbell_invalid_k_raises():
    with pytest.raises(ValueError):
        S.barbell_instance(2)
    with pytest.raises(ValueError):
        S.barbell_instance(11)


def test_barbell_edges_sorted_u_lt_v():
    inst = S.barbell_instance(4)
    for u, v, _ in inst.edges:
        assert u < v
    assert list(inst.edges) == sorted(inst.edges)
