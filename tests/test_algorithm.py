"""Zentrale Korrektheits-Kette (9 Punkte, gegen networkx als Gegenprobe, vor jeder Messung):
1) Grad/Closeness/Betweenness(Brandes)/PageRank == networkx auf >= 300 Instanzen.
2) Betweenness naiv == Brandes auf kleinen Graphen (n <= 10, inkl. Gleichstände).
3) Kanten-Betweenness (Brandes) == networkx.edge_betweenness_centrality auf >= 200 Instanzen.
4) Brücken-Satz: Kanten-Betweenness einer Brücke == a*(S-a) auf >= 200 Instanzen mit Brücken.
5) PageRank: Summe == 1, Fixpunkt-Residuum < Toleranz, == networkx.pagerank.
6) Vitalität nie negativ auf >= 200 Instanzen.
7) Barbell von Hand.
8) Buchführung: naiv gegen Brandes gegen Neuzählung, Determinismus, Nachbarreihenfolge ändert nie ein Zentralitätsmaß.
9) Sonderfälle: n=1, n=2, Stern, vollständiger Graph, unzusammenhängend."""

import networkx as nx
import pytest

import cen_algorithm as A
import cen_scenario as S


def _graph(inst_or_pair):
    if isinstance(inst_or_pair, tuple):
        n, edges = inst_or_pair
        pairs = [(u, v) for u, v in edges]
    else:
        n, pairs = inst_or_pair.n, [(u, v) for u, v, _ in inst_or_pair.edges]
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(pairs)
    return g


def _instances():
    out = [S.barbell_instance(k) for k in range(3, 11)]
    for side in (2, 3, 5, 8):
        for nettype in S.C.NETTYPES:
            for blocked in (0.0, 0.2, 0.3, 0.45, 0.5, 0.6, 0.9):
                for seed in (1, 2, 3):
                    out.append(S.generate(side, blocked, nettype, seed))
    return out


INSTANCES = _instances()          # 8 + 4*2*7*3 = 176 -- extend below to reach >= 300


def _more_instances():
    out = []
    for side in (4, 6, 7):
        for nettype in S.C.NETTYPES:
            for blocked in (0.1, 0.25, 0.4, 0.55, 0.7):
                for seed in (11, 12, 13, 14, 15):
                    out.append(S.generate(side, blocked, nettype, seed))
    return out


ALL_INSTANCES = INSTANCES + _more_instances()


def _special():
    return [(1, []), (2, []), (2, [(0, 1)]), (3, [(0, 1), (1, 2)]), (3, [(0, 1), (1, 2), (0, 2)]), (6, [(i, i + 1) for i in range(5)]), (6, [(0, i) for i in range(1, 6)]),
            (5, [(i, j) for i in range(5) for j in range(i + 1, 5)]), (6, [(i, (i + 1) % 6) for i in range(6)]), (7, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (5, 6)]), (5, [])]


def _bridge_containing_instances():
    """>= 200 Instanzen, die garantiert Brücken enthalten (Raster mit hohem Sperranteil bricht immer Brücken auf; Barbell hat immer genau eine)."""
    out = [S.barbell_instance(k) for k in range(3, 11)]
    for side in (3, 4, 5, 6, 7, 8, 9, 10):
        for blocked in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
            for seed in range(1, 6):
                out.append(S.generate(side, blocked, "grid", seed))
    return out


BRIDGE_INSTANCES = _bridge_containing_instances()


# --- 1. Grad/Closeness/Betweenness(Brandes)/PageRank == networkx ------------------------------------------------------------------------------------


def test_measures_match_networkx_on_many_instances():
    assert len(ALL_INSTANCES) >= 300
    for inst in ALL_INSTANCES:
        g = _graph(inst)
        adj = A.adjacency(inst.n, inst.edges)
        deg = A.degree_centrality(adj)
        assert deg == [d for _, d in sorted(g.degree())]
        close = A.closeness_centrality(adj)
        want_close = nx.closeness_centrality(g)
        for v in range(inst.n):
            assert close[v] == pytest.approx(want_close[v], abs=1e-9)
        node_b, edge_b, _ = A.betweenness_brandes(adj)
        want_b = nx.betweenness_centrality(g, normalized=False)
        for v in range(inst.n):
            assert node_b[v] == pytest.approx(want_b[v], abs=1e-6)
        pr, _, _ = A.pagerank(adj)
        want_pr = nx.pagerank(g, alpha=0.85, tol=1e-10, max_iter=200)
        for v in range(inst.n):
            assert pr[v] == pytest.approx(want_pr[v], abs=1e-6)


# --- 2. Betweenness naiv == Brandes (n <= 10, inkl. Gleichstände) ------------------------------------------------------------------------------------


def _small_tie_instances():
    """Kleine Graphen mit garantierten Gleichständen bei mehreren kürzesten Wegen (Kreise, Gitter, Barbell, vollständige Graphen)."""
    out = [S.barbell_instance(k) for k in (3, 4, 5)]
    for side in (2, 3):
        for nettype in S.C.NETTYPES:
            for blocked in (0.0, 0.2, 0.4):
                for seed in (1, 2, 3, 4):
                    out.append(S.generate(side, blocked, nettype, seed))
    return out


def test_naive_betweenness_equals_brandes_on_small_graphs():
    checked = 0
    for inst in _small_tie_instances():
        assert inst.n <= 10
        adj = A.adjacency(inst.n, inst.edges)
        node_naive, edge_naive, _ = A.betweenness_naive(adj)
        node_brandes, edge_brandes, _ = A.betweenness_brandes(adj)
        for v in range(inst.n):
            assert node_naive[v] == pytest.approx(node_brandes[v], abs=1e-9)
        assert set(edge_naive) == set(edge_brandes)
        for e in edge_naive:
            assert edge_naive[e] == pytest.approx(edge_brandes[e], abs=1e-9)
        checked += 1
    assert checked >= 20


def test_naive_betweenness_on_special_small_cases():
    for n, edges in _special():
        if n > 10:
            continue
        adj = A.adjacency(n, [(u, v, 1.0) for u, v in edges])
        node_naive, edge_naive, _ = A.betweenness_naive(adj)
        node_brandes, edge_brandes, _ = A.betweenness_brandes(adj)
        for v in range(n):
            assert node_naive[v] == pytest.approx(node_brandes[v], abs=1e-9)


# --- 3. Kanten-Betweenness (Brandes) == networkx.edge_betweenness_centrality -------------------------------------------------------------------------


def test_edge_betweenness_matches_networkx():
    checked = 0
    for inst in ALL_INSTANCES:
        g = _graph(inst)
        adj = A.adjacency(inst.n, inst.edges)
        _, edge_b, _ = A.betweenness_brandes(adj)
        want = nx.edge_betweenness_centrality(g, normalized=False)
        want_keyed = {(min(u, v), max(u, v)): val for (u, v), val in want.items()}
        assert set(edge_b) == set(want_keyed)
        for e, val in edge_b.items():
            assert val == pytest.approx(want_keyed[e], abs=1e-6)
        checked += 1
    assert checked >= 200


# --- 4. Brücken-Satz: Kanten-Betweenness einer Brücke == a*(S-a) --------------------------------------------------------------------------------------


def test_bridge_edge_betweenness_equals_a_times_s_minus_a():
    assert len(BRIDGE_INSTANCES) >= 200
    checked_bridges = 0
    for inst in BRIDGE_INSTANCES:
        adj = A.adjacency(inst.n, inst.edges)
        ll = A.low_link(adj)
        if not ll.bridges:
            continue
        _, edge_b, _ = A.betweenness_brandes(adj)
        for u, v in ll.bridges:
            child = v if ll.parent[v] == u else u
            comp_size = ll.comp_size[ll.root[child]]
            a = ll.size[child]
            want = a * (comp_size - a)
            assert edge_b[A._key(u, v)] == pytest.approx(float(want), abs=1e-6)
            checked_bridges += 1
    assert checked_bridges >= 200


# --- 5. PageRank: Summe == 1, Residuum klein, == networkx ----------------------------------------------------------------------------------------------


def test_pagerank_sums_to_one_and_matches_networkx():
    checked = 0
    for inst in ALL_INSTANCES[::3]:
        adj = A.adjacency(inst.n, inst.edges)
        pr, it, err = A.pagerank(adj)
        assert sum(pr) == pytest.approx(1.0, abs=1e-6)
        assert err < inst.n * 1e-10 + 1e-9
        g = _graph(inst)
        want = nx.pagerank(g, alpha=0.85, tol=1e-10, max_iter=200)
        for v in range(inst.n):
            assert pr[v] == pytest.approx(want[v], abs=1e-6)
        checked += 1
    assert checked >= 50


# --- 6. Vitalität nie negativ ------------------------------------------------------------------------------------------------------------------------


def test_vitality_is_never_negative():
    checked = 0
    for inst in ALL_INSTANCES:
        adj = A.adjacency(inst.n, inst.edges)
        vit = A.vitality(adj)
        for v in vit:
            assert v >= -1e-9
        checked += 1
    assert checked >= 200


# --- 7. Barbell von Hand -----------------------------------------------------------------------------------------------------------------------------


def test_barbell_by_hand():
    k = 5
    inst = S.barbell_instance(k)
    adj = A.adjacency(inst.n, inst.edges)
    deg = A.degree_centrality(adj)
    for x in (0, 1, 2, 3, 6, 7, 8, 9):
        assert deg[x] == k - 1
    assert deg[4] == k and deg[5] == k
    node_b, edge_b, _ = A.betweenness_brandes(adj)
    bridge_key = A._key(4, 5)
    assert edge_b[bridge_key] == pytest.approx(float(k * k), abs=1e-9)
    # die Brücke hat die höchste Kanten-Betweenness im ganzen Graphen
    assert edge_b[bridge_key] == max(edge_b.values())
    # aber ihre Endpunkte (Grad k) sind NICHT die einzigen Knoten mit dem höchsten Grad -- alle Brückenenden UND keine Clique-Innenknoten haben ihn
    assert max(deg) == k and deg.count(k) == 2
    # die Brückenendknoten haben auch die höchste Knoten-Betweenness
    assert node_b.index(max(node_b)) in (4, 5)


# --- 8. Buchführung -----------------------------------------------------------------------------------------------------------------------------------


def test_neighbour_order_never_changes_a_centrality_measure():
    for inst in ALL_INSTANCES[::7]:
        adj_fixed = A.adjacency(inst.n, inst.edges, "fixed")
        adj_shuffled = A.adjacency(inst.n, inst.edges, "shuffled", seed=inst.seed + 1)
        assert A.degree_centrality(adj_fixed) == A.degree_centrality(adj_shuffled)
        c1, c2 = A.closeness_centrality(adj_fixed), A.closeness_centrality(adj_shuffled)
        for v in range(inst.n):
            assert c1[v] == pytest.approx(c2[v], abs=1e-9)
        n1, e1, _ = A.betweenness_brandes(adj_fixed)
        n2, e2, _ = A.betweenness_brandes(adj_shuffled)
        for v in range(inst.n):
            assert n1[v] == pytest.approx(n2[v], abs=1e-9)
        assert set(e1) == set(e2)
        for e in e1:
            assert e1[e] == pytest.approx(e2[e], abs=1e-9)
        p1, _, _ = A.pagerank(adj_fixed)
        p2, _, _ = A.pagerank(adj_shuffled)
        for v in range(inst.n):
            assert p1[v] == pytest.approx(p2[v], abs=1e-6)


def test_naive_vs_brandes_vs_recount_agree_and_are_deterministic():
    for inst in _small_tie_instances()[:15]:
        adj = A.adjacency(inst.n, inst.edges)
        n1, e1, _ = A.betweenness_naive(adj)
        n2, e2, _ = A.betweenness_brandes(adj)
        n3, e3, _ = A.betweenness_brandes(adj)          # Neuzählung: Determinismus
        for v in range(inst.n):
            assert n1[v] == pytest.approx(n2[v], abs=1e-9)
            assert n2[v] == pytest.approx(n3[v], abs=1e-9)
        assert e2 == e3


def test_invalid_order_raises():
    with pytest.raises(ValueError):
        A.adjacency(3, [], "sorted")


# --- 9. Sonderfälle -----------------------------------------------------------------------------------------------------------------------------------


def test_n1_n2():
    adj = A.adjacency(1, [])
    assert A.degree_centrality(adj) == [0]
    assert A.closeness_centrality(adj) == [0.0]
    node_b, edge_b, _ = A.betweenness_brandes(adj)
    assert node_b == [0.0] and edge_b == {}
    pr, _, _ = A.pagerank(adj)
    assert pr == pytest.approx([1.0])
    assert A.vitality(adj) == [0.0]

    adj2 = A.adjacency(2, [(0, 1, 1.0)])
    node_b2, edge_b2, _ = A.betweenness_brandes(adj2)
    assert node_b2 == pytest.approx([0.0, 0.0])                                # kein Knoten liegt "zwischen" den beiden Endpunkten
    assert edge_b2[A._key(0, 1)] == pytest.approx(1.0)                         # das einzige Paar (0,1) benutzt genau diese Kante


def test_star_center_has_maximal_closeness_and_betweenness():
    n = 9
    edges = [(0, i, 1.0) for i in range(1, n)]
    adj = A.adjacency(n, edges)
    close = A.closeness_centrality(adj)
    node_b, _, _ = A.betweenness_brandes(adj)
    assert close.index(max(close)) == 0
    assert node_b.index(max(node_b)) == 0
    assert node_b[0] == pytest.approx((n - 1) * (n - 2) / 2.0)
    for leaf in range(1, n):
        assert node_b[leaf] == pytest.approx(0.0)


def test_complete_graph_all_measures_equal():
    n = 7
    edges = [(i, j, 1.0) for i in range(n) for j in range(i + 1, n)]
    adj = A.adjacency(n, edges)
    deg = A.degree_centrality(adj)
    close = A.closeness_centrality(adj)
    node_b, edge_b, _ = A.betweenness_brandes(adj)
    pr, _, _ = A.pagerank(adj)
    assert all(d == n - 1 for d in deg)
    assert all(c == pytest.approx(close[0]) for c in close)
    assert all(b == pytest.approx(0.0, abs=1e-9) for b in node_b)          # kein Knoten liegt je auf einem kuerzesten Weg (alle Kanten direkt)
    assert all(v == pytest.approx(1.0, abs=1e-9) for v in edge_b.values())  # jede Kante traegt genau das eine Paar, das sie direkt verbindet
    assert all(p == pytest.approx(pr[0]) for p in pr)


def test_disconnected_graph_closeness_convention_matches_networkx():
    n = 8
    edges = [(0, 1, 1.0), (1, 2, 1.0), (3, 4, 1.0)]           # Komponenten {0,1,2}, {3,4}, {5}, {6}, {7}
    adj = A.adjacency(n, edges)
    g = _graph((n, [(u, v) for u, v, _ in edges]))
    close = A.closeness_centrality(adj)
    want = nx.closeness_centrality(g)
    for v in range(n):
        assert close[v] == pytest.approx(want[v], abs=1e-9)
    assert close[5] == 0.0 and close[6] == 0.0
