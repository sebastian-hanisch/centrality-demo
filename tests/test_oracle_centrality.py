"""Unabhängiges Orakel: Grad/Closeness/Betweenness (Knoten und Kanten, unnormiert)/Brandes gegen networkx, PageRank gegen die direkte Lösung des linearen Systems, Effizienz und Vitalität EXAKT
als Brüche (Zahl der Paare je Abstand aus networkx), Rangkorrelation mit exakten Gleichständen. Auf einem ungesperrten Raster haben symmetrische Knoten mathematisch gleiche Vitalität - Gleitkomma-
Summen in verschiedener Reihenfolge machten daraus Rundungsreste, die die Gleichstände in eine zufällige Rangfolge verwandelten (Rangkorrelation 0.94 statt 1.0 auf dem 4 x 4-Raster)."""

import itertools
import random
from fractions import Fraction

import numpy as np
import pytest

import cen_algorithm as A
import cen_scenario as S

nx = pytest.importorskip("networkx")


def _nxgraph(n, edges):
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    return g


def _eff_exact(g):
    return sum((Fraction(1, d) for _, dd in nx.all_pairs_shortest_path_length(g) for _, d in dd.items() if d > 0), Fraction(0)) / 2


def _exact_ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return np.array(out)


def _pagerank_linear(n, edges, d):
    P = np.zeros((n, n))
    for u, v in edges:
        P[u, v] = P[v, u] = 1
    deg = P.sum(1)
    M = np.array([P[i] / deg[i] if deg[i] > 0 else np.full(n, 1.0 / n) for i in range(n)])
    w, V = np.linalg.eig((d * M + (1 - d) / n).T)
    x = np.real(V[:, np.argmin(abs(w - 1))])
    return x / x.sum()


def test_measures_match_networkx_on_random_small_graphs():
    rng = random.Random(5)
    for it in range(120):
        n = rng.randrange(1, 12)
        pairs = list(itertools.combinations(range(n), 2))
        rng.shuffle(pairs)
        edges = sorted(pairs[:rng.randrange(0, min(len(pairs), 2 * n) + 1)])
        g = _nxgraph(n, edges)
        adj = A.adjacency(n, edges, "shuffled" if it % 2 else "fixed", seed=it)
        assert A.degree_centrality(adj) == [g.degree(v) for v in range(n)]
        cn, bn, be = nx.closeness_centrality(g), nx.betweenness_centrality(g, normalized=False), nx.edge_betweenness_centrality(g, normalized=False)
        c = A.closeness_centrality(adj)
        nb, eb, _ = A.betweenness_brandes(adj)
        nbn, ebn, _ = A.betweenness_naive(adj)
        for v in range(n):
            assert abs(c[v] - cn[v]) < 1e-9 and abs(nb[v] - bn[v]) < 1e-9 and abs(nbn[v] - bn[v]) < 1e-9
        for e in edges:
            assert abs(eb.get(e, 0.0) - be[e]) < 1e-9 and abs(ebn.get(e, 0.0) - be[e]) < 1e-9
        for d in (0.5, 0.85):
            pr = A.pagerank(adj, damping=d)[0]
            assert np.allclose(pr, _pagerank_linear(n, edges, d), atol=1e-7)
        vit = A.vitality(adj)
        base = _eff_exact(g)
        for v in range(n):
            h = g.copy()
            h.remove_node(v)
            assert vit[v] == float(base - _eff_exact(h)) and vit[v] >= 0.0


def test_rank_correlation_keeps_exact_ties_on_the_unblocked_grid():
    inst = S.generate(4, 0.0, "grid", 100000)
    adj = A.adjacency(inst.n, inst.edges)
    g = _nxgraph(inst.n, [(u, v) for u, v, _ in inst.edges])
    base = _eff_exact(g)
    exact_vit = []
    for v in range(inst.n):
        h = g.copy()
        h.remove_node(v)
        exact_vit.append(base - _eff_exact(h))
    deg = A.degree_centrality(adj)
    want = float(np.corrcoef(_exact_ranks(deg), _exact_ranks(exact_vit))[0, 1])
    assert want == pytest.approx(1.0)                                  # Grad 2/3/4 und Vitalität bilden dieselben Symmetrieklassen
    assert A.spearman(deg, A.vitality(adj)) == pytest.approx(want, abs=1e-12)


def test_spearman_treats_values_equal_up_to_rounding_as_ties():
    assert A.ranks([1.0, 1.0 + 1e-13, 2.0, 0.5]) == [2.5, 2.5, 4.0, 1.0]
