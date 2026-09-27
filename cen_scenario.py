"""Die Instanz dieser Demo: das Straßennetz eines Distributionsraums als gestörtes Raster (wortgleich übernommen aus `brg_scenario.py` der Brücken-Demo, weil genau dieses Vehikel schon Brücken erzeugt,
deren Kanten-Betweenness hier gemessen wird). Ein Anteil der Straßen ist gesperrt (Baustellen, Hochwasser, Streik); das Netz darf zerfallen. Als zweiter Netztyp gibt es einen **Zufallsgraphen** mit
derselben Knoten- und Kantenzahl. Dazu das Lehrbuchbeispiel **Barbell-Graph**: zwei vollständige Graphen der Größe k, durch eine einzelne Brücke verbunden - von Hand nachrechenbar der dramatischste
Fall, in dem Grad (hoch in den Cliquen) und Betweenness (maximal auf der Brücke) auseinanderfallen.

Knoten sind von 0 bis n - 1 durchnummeriert (Zeile für Zeile, Knoten 0 liegt unten links); Kanten (u, v, w) mit u < v, sortiert; w = Länge (für die Zentralitätsmaße ohne Bedeutung, ungewichtet)."""

import random
from dataclasses import dataclass

import numpy as np

import cen_constants as C


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (n, 2)
    edges: tuple                   # ((u, v, w), ...) sortiert
    side: int
    kind: str = "city"
    nettype: str = "grid"
    blocked: float = 0.0
    seed: int = 0
    blocked_edges: tuple = ()      # gesperrte Straßen (u, v), nur zur Anzeige (nur beim Raster)
    labels: tuple = ()             # Knotennamen (nur Lehrbuchbeispiel)

    @property
    def n(self):
        return len(self.xy)

    @property
    def m(self):
        return len(self.edges)


def grid_edges(side):
    out = []
    for r in range(side):
        for c in range(side):
            v = r * side + c
            if c + 1 < side:
                out.append((v, v + 1))
            if r + 1 < side:
                out.append((v, v + side))
    return out


def make_rng(seed, salt):
    """Zufallsquelle mit fester, plattformunabhängiger Zahlenfolge (Python-`random`, nicht numpy: die Instanzen und alle daraus gezählten Zahlen ändern sich nie mit einer Bibliotheksversion)."""
    return random.Random(int(seed) * 1_000_003 + int(salt))


def block(pairs, share, rng):
    """Sperrt genau `round(share * Zahl der Straßen)` Straßen, zufällig und OHNE Rücksicht auf den Zusammenhang. Gibt (verbleibende, gesperrte) zurück."""
    target = int(round(share * len(pairs)))
    order = list(range(len(pairs)))
    rng.shuffle(order)
    removed = set(order[:target])
    kept = [pairs[j] for j in range(len(pairs)) if j not in removed]
    return kept, [pairs[j] for j in sorted(removed)]


def random_pairs(n, m, rng):
    """`m` verschiedene Kanten zwischen zufälligen verschiedenen Knotenpaaren (einfacher Graph)."""
    max_m = n * (n - 1) // 2
    m = min(m, max_m)
    chosen = set()
    while len(chosen) < m:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v:
            continue
        chosen.add((min(u, v), max(u, v)))
    return sorted(chosen)


def generate(side=C.DEFAULT_SIDE, blocked=C.DEFAULT_BLOCKED, nettype="grid", seed=C.DEFAULT_SEED, jitter=C.JITTER):
    if nettype not in C.NETTYPES:
        raise ValueError(f"unbekannter Netztyp {nettype}")
    side = int(side)
    if side < 2:
        raise ValueError("Seitenlänge mindestens 2")
    n = side * side
    rng = make_rng(seed, 4711)
    xy = np.array([[c * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING, r * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING] for r in range(side) for c in range(side)], dtype=float)
    kept, removed = block(grid_edges(side), float(blocked), rng)
    if nettype == "random":
        rng2 = make_rng(seed, 9173)
        kept = random_pairs(n, len(kept), rng2)
        removed = []
    edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in kept)
    return Instance(xy, edges, side, "city", nettype, float(blocked), int(seed), tuple(removed))


# --- Handgebautes Lehrbuchbeispiel: Barbell-Graph -----------------------------------------------------------------------------------------------------


def barbell_instance(k=C.DEFAULT_BARBELL_K):
    """Der **Barbell-Graph**: zwei vollständige Graphen K_k (Knoten 0..k-1 links, k..2k-1 rechts), verbunden durch eine einzelne Brücke zwischen Knoten k-1 (letzter links) und k (erster rechts).
    Jeder Clique-Knoten ohne Brückenende hat Grad k-1; die beiden Brückenenden haben Grad k. Die Brücke selbst trennt eine Komponente der Größe 2k in a=k und S-a=k Teile, ihre Kanten-Betweenness
    ist also exakt k*k - deutlich mehr als jede Kante innerhalb einer Clique, obwohl die Brückenenden nicht die höchsten Knotengrade tragen."""
    k = int(k)
    if not C.BARBELL_K_MIN <= k <= C.BARBELL_K_MAX:
        raise ValueError(f"k muss zwischen {C.BARBELL_K_MIN} und {C.BARBELL_K_MAX} liegen")
    n = 2 * k
    pairs = [(i, j) for i in range(k) for j in range(i + 1, k)]
    pairs += [(k + i, k + j) for i in range(k) for j in range(i + 1, k)]
    pairs.append((k - 1, k))
    pairs = sorted(pairs)
    # Layout: linke Clique als Kreis um (0,0), rechte Clique als Kreis um (3,0), Brücke waagerecht dazwischen.
    import math
    xy = np.zeros((n, 2), dtype=float)
    for i in range(k):
        ang = 2 * math.pi * i / k
        xy[i] = [-1.5 + 0.9 * math.cos(ang), 0.9 * math.sin(ang)]
        xy[k + i] = [1.5 + 0.9 * math.cos(ang), 0.9 * math.sin(ang)]
    edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in pairs)
    return Instance(xy, edges, k, "barbell", "grid", 0.0, 0, ())
