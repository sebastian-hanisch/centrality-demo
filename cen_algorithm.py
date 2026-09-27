"""Vier Zentralitätsmaße - Grad, Closeness, Betweenness (naiv gegen Brandes 2001), PageRank - dazu globale Effizienz und Vitalität. Low-Link (Tarjans Brücken/Artikulationspunkte, wortgleiche Kopie
aus `brg_algorithm.py` der Brücken-Demo) liefert die Brücken für den zentralen Satz: die Kanten-Betweenness einer Brücke, die eine Komponente der Größe S in a und S-a teilt, ist exakt a*(S-a).

**Elementarschritte** (das Aufwandsmaß dieser Reihe, keine Laufzeit): jeder abgearbeitete Knoten und jede von einem Ende angesehene Kante zählt 1 (wie in der BFS-und-DFS- und der Brücken-Demo).

**Betweenness-Normierung**: hier immer die UNNORMIERTE Zählung (jedes ungeordnete Knotenpaar zählt genau einmal - Freemans ursprüngliche Definition, `networkx` mit `normalized=False`), nicht die auf
[0,1] skalierte Variante. Nur so ist die Kanten-Betweenness einer Brücke exakt a*(S-a) (eine ganze Zahl = Zahl der getrennten Knotenpaare), ohne einen zusätzlichen Skalierungsfaktor einzuführen."""

import math
import random
from collections import deque
from dataclasses import dataclass, field


def adjacency(n, edges, order="fixed", seed=0):
    """Adjazenzliste aus Kanten (u, v, ...); "fixed" = aufsteigende Nachbarn, "shuffled" = je Knoten gemischt (Seed fest, Python-`random`)."""
    adj = [[] for _ in range(n)]
    for e in edges:
        u, v = int(e[0]), int(e[1])
        adj[u].append(v)
        adj[v].append(u)
    for lst in adj:
        lst.sort()
    if order == "shuffled":
        rng = random.Random(int(seed) * 1_000_003 + 5150)
        for lst in adj:
            rng.shuffle(lst)
    elif order != "fixed":
        raise ValueError(f"unbekannte Reihenfolge {order}")
    return adj


def _key(u, v):
    return (u, v) if u < v else (v, u)


# --- Low-Link (wortgleiche Kopie aus brg_algorithm.py) --------------------------------------------------------------------------------------------


@dataclass
class LowLink:
    disc: list                                            # Entdeckungszeit je Knoten (1, 2, ...)
    low: list                                             # kleinste Entdeckungszeit, die vom Teilbaum des Knotens über höchstens eine Rückwärtskante erreichbar ist
    parent: list
    root: list                                            # Wurzel der Tiefensuche-Komponente je Knoten
    size: list                                            # Größe des Teilbaums je Knoten
    bridges: list = field(default_factory=list)           # (u, v) mit u < v, in Fundreihenfolge
    articulation: set = field(default_factory=set)
    blocks: list = field(default_factory=list)            # frozenset von Straßen (u, v) je Block, in Fundreihenfolge
    steps: int = 0
    events: list = field(default_factory=list)            # ("root", s) | ("discover", v, u) | ("back", u, v) | ("finish", u, parent, low, bridge_flag, artic_flag); artic_flag gehört zum Elternknoten
    comp_size: dict = field(default_factory=dict)         # Wurzel -> Größe der Komponente


def low_link(adj):
    """Tarjans Low-Link, iterativ: Baumkante (p, u) ist Brücke, wenn low[u] > disc[p]; p ist Artikulationspunkt, wenn ein Kind u low[u] >= disc[p] hat (Wurzel: mindestens zwei Kinder).
    Die Blöcke werden mit einem Kantenstapel abgetrennt (Hopcroft und Tarjan 1973)."""
    n = len(adj)
    disc, low, parent, root, size = [0] * n, [0] * n, [-1] * n, [-1] * n, [1] * n
    r = LowLink(disc, low, parent, root, size)
    clock = 0
    children = [0] * n
    pos = [0] * n
    edge_stack = []
    for s in range(n):
        if disc[s]:
            continue
        clock += 1
        disc[s] = low[s] = clock
        root[s] = s
        r.steps += 1
        r.events.append(("root", s))
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                r.steps += 1                              # Kante von u aus angesehen
                if not disc[v]:
                    parent[v] = u
                    root[v] = s
                    children[u] += 1
                    edge_stack.append(_key(u, v))
                    clock += 1
                    disc[v] = low[v] = clock
                    r.steps += 1                          # Knoten v abgearbeitet
                    stack.append(v)
                    r.events.append(("discover", v, u))
                elif v != parent[u] and disc[v] < disc[u]:
                    edge_stack.append(_key(u, v))         # Rückwärtskante zu einem Vorfahren (einmal, vom Nachkommen aus)
                    if disc[v] < low[u]:
                        low[u] = disc[v]
                    r.events.append(("back", u, v))
            else:
                stack.pop()
                p = parent[u]
                bridge_flag = artic_flag = False
                if p != -1:
                    size[p] += size[u]
                    if low[u] < low[p]:
                        low[p] = low[u]
                    if low[u] > disc[p]:
                        r.bridges.append(_key(p, u))
                        bridge_flag = True
                    if low[u] >= disc[p]:                # p trennt den Teilbaum von u ab: ein Block ist fertig
                        block = []
                        while True:
                            e = edge_stack.pop()
                            block.append(e)
                            if e == _key(p, u):
                                break
                        r.blocks.append(frozenset(block))
                        if parent[p] != -1:
                            r.articulation.add(p)
                            artic_flag = True
                r.events.append(("finish", u, p, low[u], bridge_flag, artic_flag))
        if children[s] >= 2:
            r.articulation.add(s)
        r.comp_size[s] = size[s]
    return r


# --- BFS-Abstände (Erbe aus Stück 1: BFS und DFS) --------------------------------------------------------------------------------------------------


def bfs_distances(adj, s):
    """Abstand von s zu jedem erreichbaren Knoten (-1 = unerreichbar). Gibt (dist, Schritte) zurück."""
    n = len(adj)
    dist = [-1] * n
    dist[s] = 0
    queue = deque([s])
    steps = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            steps += 1
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
                steps += 1
    return dist, steps


# --- Grad ------------------------------------------------------------------------------------------------------------------------------------------


def degree_centrality(adj):
    """Grad je Knoten (Zahl der Nachbarn) - die einfachste der vier Kennzahlen."""
    return [len(nbrs) for nbrs in adj]


# --- Closeness (Wasserman-Faust-Variante, wie networkx) --------------------------------------------------------------------------------------------


def closeness_centrality(adj):
    """1 / (Summe der Abstände von v zu allen erreichbaren Knoten), skaliert mit (erreichbar-1)/(n-1) bei unzusammenhängenden Graphen (Wasserman und Faust 1994, `wf_improved`-Variante von networkx:
    ein Knoten, der nur einen kleinen Teil des Graphen erreicht, bekommt dadurch KEINEN künstlich hohen Wert nur weil seine Nachbarn nah beieinander liegen)."""
    n = len(adj)
    out = [0.0] * n
    for v in range(n):
        dist, _ = bfs_distances(adj, v)
        reach = [d for d in dist if d >= 0]
        totsp = sum(reach)
        reachable = len(reach)                            # inklusive v selbst (Abstand 0)
        if totsp > 0.0 and n > 1:
            c = (reachable - 1.0) / totsp
            c *= (reachable - 1.0) / (n - 1.0)
            out[v] = c
    return out


# --- Betweenness: naiv (alle kürzesten Wege aufzählen) ----------------------------------------------------------------------------------------------


def _shortest_path_dag(adj, s):
    """BFS-Vorgänger-DAG von s: (dist, sigma, order (Entdeckungsreihenfolge), preds, Schritte)."""
    n = len(adj)
    dist = [-1] * n
    sigma = [0] * n
    dist[s] = 0
    sigma[s] = 1
    preds = [[] for _ in range(n)]
    order = [s]
    queue = deque([s])
    steps = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            steps += 1
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
                order.append(v)
                steps += 1
            if dist[v] == dist[u] + 1:
                sigma[v] += sigma[u]
                preds[v].append(u)
    return dist, sigma, order, preds, steps


def betweenness_naive(adj):
    """Für jedes Knotenpaar (s,t) ALLE kürzesten Wege aufzählen (rekursiv über den Vorgänger-DAG, mit Zwischenspeicher je Startknoten) und 1/sigma(s,t) auf jeden Zwischenknoten und jede Kante jedes
    Weges addieren. Exponentiell im schlimmsten Fall (viele gleich lange Wege) - nur für kleine Graphen (`NAIVE_MAX_N`), zeigt aber unmittelbar, warum Brandes' Trick nötig ist."""
    n = len(adj)
    node_raw = [0.0] * n
    edge_raw = {}
    steps = 0
    for s in range(n):
        dist, sigma, order, preds, st = _shortest_path_dag(adj, s)
        steps += st
        cache = {s: [[s]]}

        def paths_to(t):
            if t in cache:
                return cache[t]
            result = []
            for p in preds[t]:
                for path in paths_to(p):
                    result.append(path + [t])
            cache[t] = result
            return result

        for t in range(n):
            if t == s or dist[t] < 0:
                continue
            all_paths = paths_to(t)
            steps += len(all_paths) * max(1, dist[t])
            w = 1.0 / len(all_paths)
            for path in all_paths:
                for node in path[1:-1]:
                    node_raw[node] += w
                for i in range(len(path) - 1):
                    e = _key(path[i], path[i + 1])
                    edge_raw[e] = edge_raw.get(e, 0.0) + w
    node_between = [v * 0.5 for v in node_raw]
    edge_between = {e: c * 0.5 for e, c in edge_raw.items()}
    return node_between, edge_between, steps


# --- Betweenness: Brandes 2001 (Knoten UND Kanten in einem Durchlauf) --------------------------------------------------------------------------------


@dataclass
class BrandesRun:
    source: int
    dist: list
    sigma: list
    order: list             # BFS-Entdeckungsreihenfolge (Vorwärtsphase)
    preds: list
    delta: list = field(default_factory=list)          # Abhängigkeit je Knoten NACH der Rückwärtsphase
    edge_delta: dict = field(default_factory=dict)      # Kanten-Abhängigkeit dieser einen Quelle
    steps: int = 0


def brandes_source(adj, s):
    """Ein Brandes-Durchlauf von einer einzigen Quelle s: Vorwärtsphase (BFS, sigma) wie `_shortest_path_dag`, dann die Rückwärtsphase (Abhängigkeit delta, vom zuletzt entdeckten Knoten rückwärts) -
    die Kanten-Abhängigkeit fällt dabei als Nebenprodukt derselben Rückwärtsphase mit ab. Wird auch für die Schritt-für-Schritt-Wiedergabe in der App benutzt."""
    dist, sigma, order, preds, steps = _shortest_path_dag(adj, s)
    n = len(adj)
    delta = [0.0] * n
    edge_delta = {}
    for w in reversed(order):
        coeff = (1.0 + delta[w]) / sigma[w]
        steps += 1
        for v in preds[w]:
            steps += 1
            c = sigma[v] * coeff
            delta[v] += c
            e = _key(v, w)
            edge_delta[e] = edge_delta.get(e, 0.0) + c
    return BrandesRun(s, dist, sigma, order, preds, delta, edge_delta, steps)


def betweenness_brandes(adj):
    """Brandes (2001): eine BFS je Startknoten (O(n*m) insgesamt), liefert Knoten- UND Kanten-Betweenness (unnormiert, s. Moduldoc). Gibt (Knoten-Liste, Kanten-Dict, Elementarschritte) zurück."""
    n = len(adj)
    node_raw = [0.0] * n
    edge_raw = {}
    steps = 0
    for s in range(n):
        run = brandes_source(adj, s)
        steps += run.steps
        for v in range(n):
            if v != s:                                     # delta[s] selbst zählt nicht: die Quelle liegt nie "zwischen" sich selbst und einem Ziel
                node_raw[v] += run.delta[v]
        for e, c in run.edge_delta.items():
            edge_raw[e] = edge_raw.get(e, 0.0) + c
    node_between = [v * 0.5 for v in node_raw]
    edge_between = {e: c * 0.5 for e, c in edge_raw.items()}
    return node_between, edge_between, steps


# --- PageRank (Brin und Page 1998, Potenzmethode) --------------------------------------------------------------------------------------------------


def pagerank(adj, damping=0.85, tol=1e-10, max_iter=200):
    """Potenzmethode auf der Übergangsmatrix eines gleichverteilten Zufallslaufs mit Dämpfung `damping` und gleichverteilter Teleportation (isolierte Knoten - "dangling nodes" - verteilen ihre Masse
    ebenfalls gleichverteilt, wie bei networkx). Gibt (Rang je Knoten, Iterationen, Fixpunkt-Residuum) zurück; die Ränge summieren sich zu 1."""
    n = len(adj)
    if n == 0:
        return [], 0, 0.0
    x = [1.0 / n] * n
    dangling = [v for v in range(n) if not adj[v]]
    teleport = 1.0 / n
    it = 0
    err = float("inf")
    for it in range(1, max_iter + 1):
        nxt = [0.0] * n
        dangling_sum = damping * sum(x[v] for v in dangling)
        for u in range(n):
            deg = len(adj[u])
            if deg == 0:
                continue
            share = damping * x[u] / deg
            for v in adj[u]:
                nxt[v] += share
        for v in range(n):
            nxt[v] += dangling_sum * teleport + (1.0 - damping) * teleport
        err = sum(abs(nxt[v] - x[v]) for v in range(n))
        x = nxt
        if err < n * tol:
            break
    return x, it, err


# --- Globale Effizienz und Vitalität (Latora und Marchiori 2001) ------------------------------------------------------------------------------------


def efficiency(adj):
    """Globale Effizienz: Summe von 1/d(u,v) über alle erreichbaren ungeordneten Knotenpaare (unnormiert - eine Summe, kein Mittelwert)."""
    n = len(adj)
    total = 0.0
    for u in range(n):
        dist, _ = bfs_distances(adj, u)
        for v in range(u + 1, n):
            if dist[v] > 0:
                total += 1.0 / dist[v]
    return total


def _remove_node(adj, x):
    """Adjazenzliste ohne Knoten x (die übrigen Knoten behalten ihre Nummer, x hat dann keine Nachbarn mehr - er zählt nicht mehr mit, weil er in keiner Nachbarliste mehr auftaucht)."""
    n = len(adj)
    out = [[] for _ in range(n)]
    for u in range(n):
        if u == x:
            continue
        out[u] = [v for v in adj[u] if v != x]
    return out


def vitality(adj):
    """Vitalität je Knoten v: efficiency(adj) - efficiency(adj ohne v). Satz: nie negativ - das Entfernen eines Knotens kann Abstände nur vergrößern oder gleich lassen, nie verkleinern, also die
    globale Effizienz nur senken oder gleich lassen."""
    n = len(adj)
    base = efficiency(adj)
    out = []
    for v in range(n):
        reduced = _remove_node(adj, v)
        out.append(base - efficiency(reduced))
    return out


# --- Rangkorrelation (ohne scipy, wie in random-spanning-tree-demo) --------------------------------------------------------------------------------


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return out


def spearman(xs, ys):
    """Rangkorrelation (ohne scipy)."""
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0
