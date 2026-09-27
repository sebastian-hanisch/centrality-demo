# Zentralität – Grad, Closeness, Betweenness, PageRank – Streamlit-Demo

Sechstes Stück der **Graphen-und-Netzwerke-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Zusammenfluss von Stück 1 (Durchmusterung, [bfs-dfs-demo](https://github.com/sebastian-hanisch/bfs-dfs-demo)) und Stück 2 (Brücken, [bridges-demo](https://github.com/sebastian-hanisch/bridges-demo)). Wie "wichtig" ist ein Knoten oder eine Kante für ein Netz? Vier klassische Antworten: **Grad** (wie viele Nachbarn direkt), **Closeness** (Kehrwert der Summe aller Abstände), **Betweenness** (Anteil kürzester Wege, die über einen Knoten oder eine Kante laufen – naiv gegen **Brandes (2001)**, der Knoten- UND Kanten-Betweenness in einer einzigen Breitensuche je Startknoten berechnet), **PageRank** (Gleichgewicht eines gedämpften Zufallslaufs, Brin und Page 1998). Die zentrale Brücke: die Kanten-Betweenness einer **Brücke**, die eine Komponente der Größe S in a und S-a teilt, ist exakt **a·(S-a)** – derselbe Ausdruck wie der Ausfallschaden in der Brücken-Demo, hier aus Betweenness statt Ausfallschaden hergeleitet und als Satz getestet.

**Einordnung in die Reihe:** die Reihe hat zwölf Stücke, dies ist das sechste (Details in `graphen-planung/PLAN.md` des Portfolio-Ordners):

```
1 BFS und DFS (Wurzel)                                                        [gebaut: bfs-dfs-demo]
 ├─ 2 Brücken und Artikulationspunkte ─ 4 Euler-Touren                        [gebaut: bridges-demo, euler-tour-demo]
 ├─ 3 Starke Zusammenhangskomponenten, topologische Sortierung                [gebaut: scc-demo]
 ├─ 5 Graphfärbung                                                            [gebaut: graph-coloring-demo]
 ├─ 6 Zentralität ─ 7 Strukturkennzahlen                                      [DIESES STÜCK ─ 7 nicht gebaut]
 │        ├─ 8 Robustheit ─ 9 Kaskaden und Ausbreitung                        [nicht gebaut]
 │        └─ 10 Kritische Knoten härten                                       [nicht gebaut]
 └─ 11 Bandbreite ─ 12 Bandbreite von G(n,k,b) und Cliquenüberdeckung         [nicht gebaut]
```

Ergebnis in Kürze: **Betweenness sagt auf fast jedem gemessenen Netztyp am besten vorher, wie sehr ein Knotenausfall das Netz schwächt (Rangkorrelation gegen die Vitalität 0.87–0.99).** Die einzige Ausnahme ist ein völlig ungesperrtes, regelmäßiges Raster – dort liegt Closeness fast gleichauf (0.99 gegen 0.99), während PageRank dort mit 0.26 der schwächste Vorhersager überhaupt ist (auf Zufallsgraphen erholt sich PageRank auf 0.82–0.91). Der Brücken-Satz (Kanten-Betweenness einer Brücke = a·(S-a)) stimmt exakt auf allen 5264 geprüften Brücken. Die naive Betweenness (alle kürzesten Wege aufzählen) ist bei n=196 Knoten das 54-Fache langsamer als Brandes (2001) – bei n=9 nur das 1.1-Fache; auf einem ungesperrten Raster wird sie schon bei rund 100 Knoten unpraktikabel (mehrere Sekunden), weit früher als auf einem Zufallsgraph gleicher Größe.

## Warum dieses Problem

Welche Kreuzung oder Straße darf in einem Verteilnetz am wenigsten ausfallen? "Wichtig" lässt sich auf mehrere, nicht austauschbare Arten messen: viele direkte Nachbarn (Grad) ist etwas anderes als nah an allen anderen zu liegen (Closeness), und beides ist wieder etwas anderes als auf vielen kürzesten Wegen zu liegen (Betweenness) oder von wichtigen Knoten selbst verlinkt zu werden (PageRank). Der Barbell-Graph (zwei vollständige Cliquen, durch eine einzige Brücke verbunden) macht den Unterschied unübersehbar: die Clique-Knoten haben den höheren Grad, aber die Brücke hat die höchste Betweenness im ganzen Graphen. Die Demo prüft zusätzlich, welches Maß den tatsächlichen Netzschaden (Vitalität = Rückgang der globalen Effizienz beim Entfernen eines Knotens) am besten vorhersagt – und zeigt, dass die Antwort vom Netztyp abhängt.

Abgrenzung: nur ungerichtete Betweenness und PageRank; die Brücke zu Stück 2 wird als Satz gezeigt (Kanten-Betweenness einer Brücke = Ausfallschaden derselben Brücke aus der Brücken-Demo), nicht als eigenständige Ausfallanalyse vertieft.

## Vorab-Hypothesen (vor der Messung notiert, hier geprüft)

| Hypothese | Ergebnis |
|---|---|
| **H1** Grad, Closeness, Betweenness und Brandes stimmen mit networkx überein. | ✅ Bestätigt auf 326 Instanzen (Raster, Zufallsgraph, Barbell, Stern, Pfad, Kreis, vollständiger Graph, unzusammenhängend). |
| **H2** Naive Betweenness und Brandes liefern dasselbe Ergebnis. | ✅ Bestätigt auf allen kleinen Testgraphen (n ≤ 10), auch bei Gleichständen (mehrere kürzeste Wege). |
| **H3** Die Kanten-Betweenness einer Brücke, die eine Komponente der Größe S in a und S-a teilt, ist exakt a·(S-a). | ✅ Bestätigt als **Satz**, nicht nur beobachtet: 100 % exakt auf 5264 geprüften Brücken (Barbell k=3..10, Raster bei 30–80 % gesperrt). |
| **H4** PageRank ist immer nah an Grad. | ❌ **Teilweise widerlegt:** auf dem Standardfall stimmen beide stark überein (Rangkorrelation 0.92), aber auf einem regelmäßigen, ungesperrten Raster fällt die Korrelation von PageRank mit der Vitalität auf 0.26 (schlechtester Vorhersager), obwohl Grad dort 0.78 erreicht – PageRank braucht Heterogenität in der Gradverteilung, um zu differenzieren. |
| **H5** Ein Maß sagt die Vitalität immer am besten vorher. | ❌ **Widerlegt (differenziert):** Betweenness gewinnt auf fast allen gemessenen Netztypen (0.87–0.99), aber auf dem ungesperrten Raster liegt Closeness mit 0.99 fast gleichauf – "das beste Maß" hängt vom Netztyp ab. |
| **H6** Die Vitalität ist nie negativ. | ✅ Bestätigt als **Satz**: über 326 gemessene Instanzen, nie ein negativer Wert (Entfernen eines Knotens kann Abstände nur vergrößern oder gleich lassen). |
| **H7** Am Barbell-Graphen fallen Grad und Betweenness maximal auseinander. | ✅ Bestätigt von Hand (k=5): Clique-Knoten ohne Brückenende Grad 4, Brückenenden Grad 5 – aber die Brücke selbst hat mit 25 die höchste Kanten-Betweenness im ganzen Graphen, weit vor der höchsten Knoten-Betweenness (20). |

## Befunde (gemessen, keine Behauptungen)

Median über 5 feste Instanzen (Seeds 100000–100004), Raster mit 30 % gesperrten Straßen bzw. 12×12=144 Knoten für die Rangkorrelation, sofern nicht anders angegeben; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed.

| Frage | Ergebnis |
|---|---|
| **Stimmt das Verfahren?** | ✅ Grad/Closeness/Betweenness(Brandes)/PageRank == networkx auf 326 Instanzen; Kanten-Betweenness == `networkx.edge_betweenness_centrality` auf 326 Instanzen; naiv == Brandes auf allen kleinen Testgraphen |
| **Aufwand naiv gegen Brandes** (Elementarschritte, Raster 30 % gesperrt) | n=9: 295 gegen 259 (1.1×) — n=196: 11.925.316 gegen 220.050 (**54.2×**) — streng monoton wachsende Lücke |
| **NAIVE_MAX_N-Kalibrierung** | Worst Case (ungesperrtes Raster): n=64/81/100 → 0.39 s / 1.63 s / 6.89 s; ein Zufallsgraph oder gesperrtes Raster gleicher Größe ist um ein Vielfaches schneller (n=100, 30 % gesperrt: 0.09 s) |
| **Rangkorrelation gegen Vitalität, Raster** | Betweenness 0.87–0.99, Grad 0.66–0.78, Closeness 0.57–0.99 (nicht monoton über den Sperranteil!), PageRank 0.26–0.67 |
| **Rangkorrelation gegen Vitalität, Zufallsgraph** | Betweenness 0.91–0.96, Grad 0.90–0.93, PageRank 0.82–0.91, Closeness 0.79–0.86 – hier deutlich konstanter als auf dem Raster |
| **Brücken-Satz** | Kanten-Betweenness == a·(S-a) auf **100 %** von 5264 geprüften Brücken |
| **Barbell von Hand (k=5)** | Grad 4/4/4/4/**5/5**/4/4/4/4; Kanten-Betweenness der Brücke = 25 = 5·5 (Maximum im ganzen Graphen); höchste Knoten-Betweenness = 20, an den Brückenenden |

Presets (7), alle mit den Zahlen in ihren Hilfetexten (`tests/test_presets.py`):

| Preset | Was es zeigt |
|---|---|
| Barbell (Lehrbuch) | 10 Knoten, 21 Kanten: die Brücke hat Kanten-Betweenness 25 = 5·5, höher als jede Knoten-Betweenness (20) |
| Standardfall (Voreinstellung) | 144 Knoten, 185 Straßen, 21 Brücken: Betweenness sagt die Vitalität am besten vorher (0.87) |
| Viele Brücken (hoher Sperranteil) | 60 % gesperrt: 106 Straßen, 42 Komponenten, 90 Brücken – fast jede zweite Straße ist eine Brücke |
| Zufallsgraph | 144 Knoten, 264 Straßen: Betweenness bleibt über alle Sperranteile konstant zuverlässig (0.91–0.96) |
| Aufwand: naiv gegen Brandes | n=196: 11.925.316 gegen 220.050 Elementarschritte, Faktor 54 |
| Vitalität gegen Zentralität (bestes Maß) | Ungesperrtes Raster: Closeness und Betweenness fast perfekt (0.99), PageRank überraschend schwach (0.26) |
| PageRank auf ungleichmäßigem Netz | 70 % gesperrt: PageRank streut 0.0014–0.0195, Rangkorrelation mit Grad 0.88 (stark, aber nicht identisch) |

## Modell und Verfahren

- **Instanz** (`cen_scenario.py`): das **Betriebsnetz** – ein gestörtes Straßenraster mit gesperrtem Anteil (wortgleich aus `brg_scenario.py` der Brücken-Demo übernommen, weil genau dieses Vehikel Brücken erzeugt) oder ein **Zufallsgraph** gleicher Kanten-/Knotenzahl. Das Lehrbuchbeispiel **Barbell-Graph**: zwei vollständige Graphen K_k, durch eine einzige Brücke verbunden.
- **Grad** (`degree_centrality`): Zahl der Nachbarn.
- **Closeness** (`closeness_centrality`): 1 / Summe der Abstände zu allen erreichbaren Knoten, Wasserman-Faust-Variante (skaliert mit dem Anteil erreichbarer Knoten – wie networkx).
- **Betweenness naiv** (`betweenness_naive`): alle kürzesten Wege eines Paares rekursiv aufzählen, 1/(Zahl kürzester Wege) je Weg auf jeden Zwischenknoten und jede Kante addieren. Nur bis `NAIVE_MAX_N` praktikabel.
- **Betweenness Brandes** (`betweenness_brandes`, Brandes 2001): eine Breitensuche je Startknoten, Abhängigkeit rückwärts akkumuliert – liefert Knoten- UND Kanten-Betweenness in einem Durchlauf, O(n·m).
- **PageRank** (`pagerank`, Brin und Page 1998): Potenzmethode auf der Übergangsmatrix eines gedämpften Zufallslaufs (Dämpfung 0.85, Toleranz 1e-10).
- **Globale Effizienz und Vitalität** (`efficiency`, `vitality`, Latora und Marchiori 2001): Effizienz = Σ 1/d(u,v) über alle erreichbaren Paare; Vitalität eines Knotens = Effizienz(G) − Effizienz(G ohne den Knoten) – nie negativ.
- **Low-Link** (`low_link`, wortgleiche Kopie aus `brg_algorithm.py`): liefert die Brücken für den zentralen Satz.
- **Elementarschritte:** jeder abgearbeitete Knoten und jede von einem Ende angesehene Kante zählt 1; die naive Betweenness zählt zusätzlich jeden materialisierten Pfad. Ein Näherungsmaß, keine Laufzeit.

## Was die App zeigt

1. **Vier Schritte** (Schritt-Regler): **Vier Maße auf einer Karte** (Umschalter Grad/Closeness/Betweenness/PageRank, Dämpfungsregler nur bei PageRank sichtbar) → **Brandes in Aktion** (Wiedergabe einer Breitensuche von einem wählbaren Startknoten: erst die Vorwärtsphase mit sigma, dann die Rückwärtsphase mit delta) → **Struktur gegen Zahl** (Brücken hervorgehoben, Kanten-Betweenness als Linienbreite, gemessener Wert gegen die Formel a·(S-a)) → **Welches Maß sagt den Schaden vorher?** (2×2-Streudiagramme gegen die Vitalität mit Rangkorrelation; auf Abruf: Aufwand naiv gegen Brandes über die Größe, Rangkorrelation über Netztyp und Sperranteil).
2. Regler: Instanz (Betriebsnetz / Barbell), Seitenlänge bzw. Cliquengröße k, Netztyp, gesperrter Anteil, Zufalls-Seed (+🎲), Nachbarreihenfolge; Permalink in der Adresszeile.
3. Bei großen Netzen (> 200 Knoten) wird die Vitalität (Schritt 4) nicht automatisch berechnet (Aufwand ~ n²·(n+m)) – ein Knopf erzwingt die Berechnung bei Bedarf.

## Was nicht funktioniert hat / Grenzen

- **Nur ungerichtete Betweenness/PageRank.** Gerichtete Netze (Einbahnstraßen, Zitationsgraphen) bräuchten eigene Varianten – hier nicht umgesetzt.
- **Vitalität nur über globale Effizienz.** Andere Schadensmaße (größte Komponente nach Ausfall, Umwegkosten) könnten ein anderes Maß bevorzugen; nicht geprüft.
- **Kein Maß gewinnt immer.** H5 zeigt: das beste Maß hängt vom Netztyp ab (Betweenness meist, Closeness auf dem ungesperrten Raster fast gleichauf).
- **Naive Betweenness explodiert kombinatorisch.** Bei vielen gleich langen Wegen (regelmäßiges Raster) wächst sie exponentiell, nicht nur polynomiell langsamer als Brandes – deutlich früher unpraktikabel als auf einem Zufallsgraph gleicher Größe.
- **Elementarschritte statt Laufzeit.** Die gemessenen Faktoren gelten für das Zählmaß, echte Laufzeiten hängen an der Implementierung.
- **Synthetische Instanzen.** Betriebsnetz, Zufallsgraph und Barbell sind erzeugt, keine echten Verkehrs- oder Sozialnetzdaten.

## Design-Entscheidung: unnormierte Betweenness

Die Betweenness wird hier immer **unnormiert** gezählt (jedes ungeordnete Knotenpaar zählt genau einmal – Freemans ursprüngliche Definition, entspricht `networkx` mit `normalized=False`), nicht die verbreitete, auf [0,1] skalierte Variante. Nur so ist die Kanten-Betweenness einer Brücke exakt a·(S-a) – eine ganze Zahl, direkt die Zahl der getrennten Knotenpaare – ohne einen zusätzlichen Skalierungsfaktor einzuführen, der den Satz verschleiern würde.

## Tests

`tests/test_algorithm.py` (Korrektheits-Kette: alle vier Maße und Kanten-Betweenness gegen networkx auf 326 Instanzen, naiv == Brandes, Brücken-Satz auf 5264 Brücken, PageRank-Fixpunkt, Vitalität nie negativ auf 326 Instanzen, Barbell von Hand, Buchführung, Sonderfälle n=1/2/Stern/vollständig/unzusammenhängend), `tests/test_scenario.py`, `tests/test_evaluation.py`, `tests/test_presets.py` (jede Zahl der Hilfetexte), `tests/test_claims.py` (jede README-Zahl über die echten Auswertungsfunktionen), `tests/test_app.py` (36: AppTest – Voreinstellung, jedes Preset, jeder Schritt für jede Instanz, jede Position des Brandes-Wiedergabe-Reglers, Randwerte, Permalink-Grenzen, bedingte Regler inkl. Dämpfungsregler und Vitalitäts-Knopf bei großen Netzen, Berechnungen auf Abruf, Footer). 81 Tests insgesamt.

```
python -m pytest tests/ -v
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App |
| `cen_algorithm.py` | Grad, Closeness, Betweenness (naiv, Brandes), PageRank, Effizienz/Vitalität, Low-Link |
| `cen_scenario.py` | Betriebsnetz (Raster/Zufallsgraph), Barbell-Graph |
| `cen_evaluation.py` | Analyse, Sweeps (Aufwand, Rangkorrelation, Brücken-Satz-Check) |
| `cen_visualization.py` | Plotly-Figuren (Maß-Karte, Brandes-Wiedergabe, Brücken-Karte, Streudiagramme) |
| `cen_presets.py`, `cen_constants.py` | Permalink, Presets, gemessene Werte |
| `tests/` | Tests |

## Bewusst nicht umgesetzt

Strukturkennzahlen, Robustheit und Kaskaden, kritische Knoten härten, Bandbreite – eigene Stücke der Reihe. Gerichtete Varianten der Maße, andere Schadensmaße als globale Effizienz.

## Lokal ausführen

```
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\streamlit run app.py
```

## Literatur

- Freeman, L. C. (1977). *A set of measures of centrality based on betweenness.* Sociometry 40(1), 35–41.
- Brandes, U. (2001). *A faster algorithm for betweenness centrality.* Journal of Mathematical Sociology 25(2), 163–177.
- Brin, S., & Page, L. (1998). *The anatomy of a large-scale hypertextual web search engine.* Computer Networks and ISDN Systems 30(1-7), 107–117.
- Latora, V., & Marchiori, M. (2001). *Efficient behavior of small-world networks.* Physical Review Letters 87(19), 198701.

Gebaut mit Streamlit, Plotly, NumPy und pandas.
