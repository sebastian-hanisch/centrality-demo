"""Auswertung: Analyse einer Instanz (alle vier Maße, Vitalität, Brücken-Betweenness-Satz), Aufwand naiv gegen Brandes über die Größe, Rangkorrelation jedes Maßes gegen Vitalität über Netztyp und
Sperranteil, Anteil der Brücken mit exakter a*(S-a)-Kanten-Betweenness."""

from dataclasses import dataclass
from functools import lru_cache

import cen_algorithm as A
import cen_constants as C
import cen_scenario as S


@dataclass
class Settings:
    kind: str = "city"                  # "city" | "barbell"
    side: int = C.DEFAULT_SIDE
    blocked: float = C.DEFAULT_BLOCKED
    nettype: str = "grid"               # "grid" | "random" (nur kind == "city")
    k_barbell: int = C.DEFAULT_BARBELL_K
    seed: int = C.DEFAULT_SEED
    order: str = "fixed"                # "fixed" | "shuffled"
    damping: float = C.DEFAULT_DAMPING


@dataclass
class Analysis:
    n: int
    m: int
    degree: list
    closeness: list
    betweenness_node: list
    betweenness_edge: dict
    pagerank: list
    pagerank_iters: int
    vitality: list
    efficiency: float
    ll: object                          # cen_algorithm.LowLink (Brücken, Artikulationspunkte, ...)
    bridge_check: dict                  # {(u, v): (gemessene Kanten-Betweenness, a*(S-a))} je Brücke


def instance(settings):
    if settings.kind == "city":
        return S.generate(settings.side, settings.blocked, settings.nettype, settings.seed)
    if settings.kind == "barbell":
        return S.barbell_instance(settings.k_barbell)
    raise ValueError(f"unbekannte Instanzart {settings.kind}")


def analyse(settings, compute_vitality=True):
    inst = instance(settings)
    adj = A.adjacency(inst.n, inst.edges, settings.order, settings.seed)
    degree = A.degree_centrality(adj)
    closeness = A.closeness_centrality(adj)
    node_b, edge_b, _ = A.betweenness_brandes(adj)
    pr, iters, _ = A.pagerank(adj, damping=settings.damping)
    vit = A.vitality(adj) if compute_vitality else None
    eff = A.efficiency(adj)
    ll = A.low_link(adj)
    bridge_check = {}
    for u, v in ll.bridges:
        child = v if ll.parent[v] == u else u
        comp_size = ll.comp_size[ll.root[child]]
        a = ll.size[child]
        bridge_check[(u, v)] = (edge_b[A._key(u, v)], float(a * (comp_size - a)))
    return inst, Analysis(inst.n, inst.m, degree, closeness, node_b, edge_b, pr, iters, vit, eff, ll, bridge_check)


def _median(vals):
    vals = sorted(vals)
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


# --- Aufwand: naiv gegen Brandes über die Größe -------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=None)
def cost_sweep(sides, blocked=C.DEFAULT_BLOCKED, nettype="grid", seeds=C.SWEEP_SEEDS):
    """Elementarschritte der naiven Betweenness gegen Brandes über die Seitenlänge (Median über `seeds`). Ergebnis pro Argumentkombination zwischengespeichert (teuer, in Tests und App mehrfach
    mit denselben Argumenten aufgerufen)."""
    sides = tuple(sides)
    seeds = tuple(seeds)
    out = []
    for side in sides:
        naive_steps, brandes_steps, ns = [], [], []
        for seed in seeds:
            inst = S.generate(side, blocked, nettype, seed)
            adj = A.adjacency(inst.n, inst.edges)
            _, _, st_naive = A.betweenness_naive(adj)
            _, _, st_brandes = A.betweenness_brandes(adj)
            naive_steps.append(st_naive)
            brandes_steps.append(st_brandes)
            ns.append(inst.n)
        out.append({"side": side, "n": _median(ns), "naive": _median(naive_steps), "brandes": _median(brandes_steps)})
    return out


# --- Rangkorrelation je Maß gegen Vitalität, über Netztyp und Sperranteil ------------------------------------------------------------------------------


@lru_cache(maxsize=None)
def correlation_sweep(blockeds, nettypes=C.NETTYPES, side=C.CORR_SIDE, seeds=C.SWEEP_SEEDS):
    """Median der Spearman-Rangkorrelation von Grad/Closeness/Betweenness/PageRank gegen die Vitalität, je Netztyp und Sperranteil. Ergebnis pro Argumentkombination zwischengespeichert."""
    blockeds = tuple(blockeds)
    nettypes = tuple(nettypes)
    seeds = tuple(seeds)
    out = []
    for nettype in nettypes:
        for blocked in blockeds:
            rows = {"degree": [], "closeness": [], "betweenness": [], "pagerank": []}
            for seed in seeds:
                inst = S.generate(side, blocked, nettype, seed)
                adj = A.adjacency(inst.n, inst.edges)
                degree = A.degree_centrality(adj)
                closeness = A.closeness_centrality(adj)
                node_b, _, _ = A.betweenness_brandes(adj)
                pr, _, _ = A.pagerank(adj)
                vit = A.vitality(adj)
                rows["degree"].append(A.spearman(degree, vit))
                rows["closeness"].append(A.spearman(closeness, vit))
                rows["betweenness"].append(A.spearman(node_b, vit))
                rows["pagerank"].append(A.spearman(pr, vit))
            out.append({"nettype": nettype, "blocked": blocked, **{k: _median(v) for k, v in rows.items()}})
    return out


# --- Brücken-Satz: Anteil exakt --------------------------------------------------------------------------------------------------------------------


def bridge_betweenness_check(instances, tol=1e-6):
    """Anteil der Brücken (über alle `instances`), deren gemessene Kanten-Betweenness (Brandes) exakt a*(S-a) ist. Gibt (Anteil, Zahl geprüfter Brücken) zurück - sollte immer 1.0 sein (Satz, nicht
    nur Beobachtung)."""
    total = matched = 0
    for inst in instances:
        adj = A.adjacency(inst.n, inst.edges)
        ll = A.low_link(adj)
        if not ll.bridges:
            continue
        _, edge_b, _ = A.betweenness_brandes(adj)
        for u, v in ll.bridges:
            child = v if ll.parent[v] == u else u
            comp_size = ll.comp_size[ll.root[child]]
            a = ll.size[child]
            want = float(a * (comp_size - a))
            total += 1
            matched += int(abs(edge_b[A._key(u, v)] - want) <= tol)
    return (matched / total if total else None), total
