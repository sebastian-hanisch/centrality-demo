"""Regler-Grenzen, feste Annahmen, gemessene Werte und Presets."""

SPACING = 1.0                    # Abstand der Kreuzungen im Raster
JITTER = 0.18                    # Störung der Kreuzungslage (Anteil des Abstands)
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 4, 30, 12
SEED_MAX = 999999
DEFAULT_SEED = 35
KINDS = ("city", "barbell")
KIND_LABELS = {"city": "Betriebsnetz (Karte)", "barbell": "Lehrbuchbeispiel: Barbell-Graph"}
NETTYPES = ("grid", "random")
NETTYPE_LABELS = {"grid": "Raster (Straßennetz)", "random": "Zufallsgraph (gleiche Kantenzahl)"}
BLOCKED_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9)
DEFAULT_BLOCKED = 0.3
ORDERS = ("fixed", "shuffled")
ORDER_LABELS = {"fixed": "feste Reihenfolge (nach Knotennummer)", "shuffled": "gemischt (nach Seed)"}
BARBELL_K_MIN, BARBELL_K_MAX, DEFAULT_BARBELL_K = 3, 10, 5
DAMPING_MIN, DAMPING_MAX, DEFAULT_DAMPING = 0.5, 0.95, 0.85
MEASURES = ("degree", "closeness", "betweenness", "pagerank")
MEASURE_LABELS = {"degree": "Grad", "closeness": "Closeness", "betweenness": "Betweenness", "pagerank": "PageRank"}
STEPS = {1: "1 · Vier Maße auf einer Karte", 2: "2 · Brandes in Aktion", 3: "3 · Struktur gegen Zahl", 4: "4 · Welches Maß sagt den Schaden vorher?"}
SWEEP_SEEDS = tuple(range(100000, 100005))

NAIVE_MAX_N = 80                                            # bis zu dieser Knotenzahl läuft die naive Betweenness auch für die aktuelle Instanz (Worst Case: ungesperrtes Raster, siehe unten)
VITALITY_MAX_N = 200                                        # bis zu dieser Knotenzahl läuft Schritt 4 (Vitalität) automatisch mit; darüber erst auf Knopfdruck (O(n^2*(n+m)), siehe unten)
COST_SIDES = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14)          # Seitenlängen im Aufwands-Sweep (9 bis 196 Knoten)
CORR_SIDE = 12                                               # Seitenlänge der Instanzen im Rangkorrelations-Sweep (144 Knoten)
CORR_BLOCKED = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)

# --- Gemessene Werte (MEDIAN über 5 feste Instanzen, Seeds 100000-100004, sofern nicht anders angegeben; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed
# --- und ändern sich nie mit einer Bibliotheksversion; 2026-09-27, alle Werte über ev.* nachgerechnet, s. tests/test_claims.py) ---
# NAIVE_MAX_N-KALIBRIERUNG: der Worst Case für die naive Betweenness ist ein UNGESPERRTES Raster (die meisten gleich langen Wege): bei n=64/81/100 Knoten braucht sie 0.39/1.63/6.89 Sekunden (Python,
#   diese Maschine) - bei einem Zufallsgraph oder gesperrtem Raster gleicher Größe ist sie um ein Vielfaches schneller (n=100, 30 % gesperrt: 0.09 s). NAIVE_MAX_N=80 bleibt darum unter der 2-Sekunden-Grenze.
# AUFWAND (naiv gegen Brandes, Raster, 30 % gesperrt, Median über 5 Seeds): Elementarschritte bei n=9/16/25/36/49/64/81/100/121/144/196: naiv 295/1698/5933/19036/48651/109876/276881/595376/1075301/
#   2294354/11925316, Brandes 259/1110/2935/6600/13106/22682/35370/50922/77376/119142/220050 - Faktor 1.1x bei n=9 bis 54.2x bei n=196 (streng monoton wachsend).
# RANGKORRELATION je Maß gegen Vitalität (Raster 12x12=144 Knoten, Median über 5 Seeds, Spearman über alle Knoten): Betweenness gewinnt fast immer (0.87-0.99 auf dem Raster, 0.91-0.96 auf dem
#   Zufallsgraph). ÜBERRASCHUNG: Closeness ist auf dem UNGESPERRTEN Raster (0.0) fast gleichauf (0.99), fällt dann bei 20-40 % gesperrt auf 0.57-0.61 und steigt erst nahe der Zerfallsschwelle (50 %)
#   wieder auf 0.85 - nicht monoton, kein verlässlicher Vorhersager über den ganzen Bereich. PageRank ist auf dem REGELMÄSSIGEN Raster (0 % gesperrt) mit 0.26 der schlechteste Vorhersager überhaupt,
#   erholt sich aber auf Zufallsgraphen (0.82-0.91) deutlich - PageRank braucht Heterogenität in der Gradverteilung, um zu unterscheiden.
# BRÜCKEN-SATZ: Anteil der Brücken (Barbell k=3..10 + Raster bei 30-80 % gesperrt, 5264 geprüfte Brücken), deren Kanten-Betweenness (Brandes) exakt a*(S-a) ist: 100 %.
# BARBELL VON HAND (k=5): Clique-Knoten ohne Brückenende haben Grad k-1=4, die zwei Brückenenden Grad k=5; die Brücke selbst hat die höchste Kanten-Betweenness im ganzen Graphen (a*(S-a) = 5*5=25 >
#   20 = höchste Knoten-Betweenness), obwohl ihre Endpunkte nicht die höchsten Knotengrade tragen (Grad 5 statt z. B. 8 in einer größeren Clique).
# PAGERANK GEGEN GRAD (Standardfall, 12x12, 30 % gesperrt): Rangkorrelation 0.92 - PageRank und Grad stimmen auf dieser Instanz weitgehend überein, sind aber NICHT identisch (verschiedene Top-5-Knoten).
#   Bei hohem Sperranteil (70 %, viele Sternstrukturen durch Brücken) bleibt die Übereinstimmung mit 0.88 hoch, aber PageRank differenziert stärker (Spanne 0.0014-0.0195 gegen Grad 0-4).

PRESETS = {
    "Barbell (Lehrbuch)": {"kind": "barbell", "kbarbell": 5, "step": 3},
    "Standardfall (Voreinstellung)": {"kind": "city", "side": 12, "blocked": 0.3, "nettype": "grid", "seed": 35, "order": "fixed", "step": 1},
    "Viele Brücken (hoher Sperranteil)": {"kind": "city", "side": 12, "blocked": 0.6, "nettype": "grid", "seed": 35, "order": "fixed", "step": 3},
    "Zufallsgraph": {"kind": "city", "side": 12, "blocked": 0.0, "nettype": "random", "seed": 35, "order": "fixed", "step": 1},
    "Aufwand: naiv gegen Brandes": {"kind": "city", "side": 12, "blocked": 0.3, "nettype": "grid", "seed": 35, "order": "fixed", "step": 4},
    "Vitalität gegen Zentralität (bestes Maß)": {"kind": "city", "side": 12, "blocked": 0.0, "nettype": "grid", "seed": 35, "order": "fixed", "step": 4},
    "PageRank auf ungleichmäßigem Netz": {"kind": "city", "side": 12, "blocked": 0.7, "nettype": "grid", "seed": 35, "order": "fixed", "step": 1},
}
PRESET_HELP = {
    "Barbell (Lehrbuch)": "Zwei vollständige Graphen K5, verbunden durch eine einzige Brücke (10 Knoten, 21 Kanten): die Clique-Knoten ohne Brückenende haben Grad 4, die beiden Brückenenden Grad 5 - "
                          "aber die Brücke selbst hat mit 25 (= 5*5) die höchste Kanten-Betweenness im ganzen Graphen, weit vor der höchsten Knoten-Betweenness (20, an den Brückenenden). Grad und "
                          "Betweenness fallen hier maximal auseinander.",
    "Standardfall (Voreinstellung)": "12 × 12 Kreuzungen (144 Knoten), 30 % der Straßen gesperrt (185 Straßen, 4 Komponenten): 21 Brücken und 17 Artikulationspunkte. Über 5 Seeds gemessen: Betweenness "
                                     "sagt die Vitalität am besten vorher (Rangkorrelation 0.87), Grad und PageRank folgen (0.70 / 0.65), Closeness am schlechtesten (0.57).",
    "Viele Brücken (hoher Sperranteil)": "Dasselbe Raster, 60 % gesperrt: nur noch 106 Straßen, das Netz zerfällt in 42 Komponenten (größte: 31 Knoten), davon 90 Brücken und 61 Artikulationspunkte - "
                                         "fast jede zweite verbliebene Straße ist jetzt eine Brücke.",
    "Zufallsgraph": "Zufallsgraph mit 144 Knoten und derselben Kantenzahl wie das ungesperrte Raster (264 Straßen): 19 Brücken und 17 Artikulationspunkte - auf Zufallsgraphen sagt Betweenness die "
                    "Vitalität besonders zuverlässig vorher (Rangkorrelation 0.91-0.96 über alle gemessenen Sperranteile), deutlich konstanter als auf dem Raster.",
    "Aufwand: naiv gegen Brandes": "Über die Größe gemessen (Raster, 30 % gesperrt, Median über 5 Seeds): bei n=196 Knoten braucht die naive Betweenness 11925316 Elementarschritte gegen 220050 bei "
                                   "Brandes - das 54-Fache; bei n=9 sind es nur 295 gegen 259 (Faktor 1.1) - die Lücke wächst mit der Größe.",
    "Vitalität gegen Zentralität (bestes Maß)": "Auf dem UNGESPERRTEN Raster (144 Knoten) sagen Closeness (0.99) und Betweenness (0.99) die Vitalität fast perfekt vorher, Grad nur mittelmäßig (0.78) "
                                                "und PageRank überraschend schwach (0.26) - auf einem sehr regelmäßigen Netz gibt es für PageRank kaum Struktur zum Unterscheiden.",
    "PageRank auf ungleichmäßigem Netz": "70 % gesperrtes Raster (144 Knoten, nur noch 79 Straßen, viele sternförmige Restkomponenten durch Brücken): PageRank streut zwischen 0.0014 und 0.0195, "
                                         "stimmt mit dem Grad stark überein (Rangkorrelation 0.88), ist aber nicht identisch - PageRank gewichtet die Wichtigkeit der Nachbarn mit, der Grad nicht.",
}
