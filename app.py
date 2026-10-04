"""Zentralität: Grad, Closeness, Betweenness (naiv gegen Brandes 2001), PageRank - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Sechstes Stück der Graphen-und-Netzwerke-Reihe. Zusammenfluss von Stück 1 (BFS/DFS) und Stück 2 (Brücken): Zentralität misst, wie "wichtig" ein Knoten oder eine Kante für den Zusammenhalt und die
Wegeführung eines Netzes ist. Die Kanten-Betweenness einer Brücke, die eine Komponente der Größe S in a und S-a teilt, ist exakt a*(S-a) - derselbe Ausdruck wie der Ausfallschaden in der Brücken-Demo,
hier aus Betweenness statt Ausfallschaden hergeleitet.

Lauffähig mit: streamlit run app.py
"""

import dataclasses

import streamlit as st

import cen_algorithm as A
import cen_constants as C
import cen_evaluation as ev
import cen_visualization as viz
from cen_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, store_from_widget, sync_query_params

st.set_page_config(page_title="Zentralität – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings, need_vitality):
    return ev.analyse(settings, compute_vitality=need_vitality)


@st.cache_data(show_spinner=False)
def _cost_sweep():
    return ev.cost_sweep(C.COST_SIDES)


@st.cache_data(show_spinner=False)
def _correlation_sweep():
    return ev.correlation_sweep(C.CORR_BLOCKED)


def _german(x):
    return f"{x:,}".replace(",", ".") if isinstance(x, int) else x


st.title("🕸️ Zentralität – Grad, Closeness, Betweenness, PageRank")
st.markdown(
    """
**Sechstes Stück der Graphen-und-Netzwerke-Reihe.** Wie "wichtig" ist ein Knoten oder eine Kante für ein Netz? Vier klassische Antworten: **Grad** (wie viele Nachbarn direkt), **Closeness** (Kehrwert
der Summe aller Abstände - wie nah an allen anderen), **Betweenness** (Anteil kürzester Wege, die über einen Knoten oder eine Kante laufen - wie sehr ein "Verkehrsknotenpunkt"), **PageRank** (Gleichgewicht
eines zufälligen Surfers, gewichtet nach der Wichtigkeit der Nachbarn selbst). Betweenness naiv (alle kürzesten Wege aufzählen) gegen **Brandes (2001)**, der Knoten- UND Kanten-Betweenness in einer
einzigen Breitensuche je Startknoten berechnet (O(n·m) statt exponentiell). Die Brücke zu Stück 2: die Kanten-Betweenness einer **Brücke**, die eine Komponente der Größe S in a und S-a teilt, ist exakt
**a·(S-a)** - ein Satz, kein Zufall.
"""
)
st.caption(
    "Kind der BFS-und-DFS-Demo UND der Brücken-Demo (sechstes Stück der Graphen-und-Netzwerke-Reihe); Nachfolger: Strukturkennzahlen, Robustheit, Kaskaden, kritische Knoten "
    "härten, Bandbreite. Die **Vitalität** eines Knotens (Rückgang der globalen Effizienz beim Entfernen) prüft, welches der vier Maße den Netzschaden am besten vorhersagt."
)

with st.expander("So funktionieren die vier Maße", expanded=True):
    st.markdown(
        """
1. **Grad:** Zahl der direkten Nachbarn - am einfachsten, aber blind für die Position im Netz.
2. **Closeness:** 1 / (Summe der Abstände zu allen erreichbaren Knoten), skaliert für unzusammenhängende Netze (Wasserman-Faust-Variante) - hoch für Knoten "in der Mitte" des Netzes.
3. **Betweenness:** Anteil aller kürzesten Wege, die über einen Knoten bzw. eine Kante laufen - unnormiert, sodass die Kanten-Betweenness einer Brücke direkt die Zahl der getrennten Knotenpaare ist.
   Naiv: alle kürzesten Wege eines Paares aufzählen und rekursiv zählen (nur für kleine Netze). **Brandes (2001):** eine Breitensuche je Startknoten, Abhängigkeit rückwärts akkumuliert - liefert Knoten-
   UND Kanten-Betweenness in einem Durchlauf, in O(n·m) statt exponentiell.
4. **PageRank:** Potenzmethode auf der Übergangsmatrix eines gedämpften Zufallslaufs (Brin und Page 1998) - ein Knoten ist wichtig, wenn wichtige Knoten auf ihn zeigen.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:4], preset_names[4:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                     help="Betriebsnetz: gestörtes Straßenraster (oder Zufallsgraph gleicher Kantenzahl). Barbell: zwei vollständige Graphen, durch eine einzige Brücke verbunden - Lehrbuchbeispiel, "
                     "in dem Grad und Betweenness maximal auseinanderfallen.")
    side, blocked, nettype, k_barbell = C.DEFAULT_SIDE, C.DEFAULT_BLOCKED, "grid", C.DEFAULT_BARBELL_K
    if kind == "city":
        side = st.slider("Seitenlänge des Rasters", *bounds("side_slider"), value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                          help="Die Instanz hat Seitenlänge² Kreuzungen.")
        nettype = st.radio("Netztyp", options=list(C.NETTYPES), format_func=lambda v: C.NETTYPE_LABELS[v], key="nettype_widget", on_change=store_from_widget, args=("nettype_select",),
                            index=list(C.NETTYPES).index(ss["nettype_select"]))
        if nettype == "grid":
            blocked = st.select_slider("Gesperrter Anteil der Straßen", options=list(C.BLOCKED_OPTIONS), value=float(ss["blocked_select"]), format_func=lambda v: f"{v * 100:.0f} %",
                                        key="blocked_widget", on_change=store_from_widget, args=("blocked_select",))
        else:
            blocked = float(ss["blocked_select"])
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        k_barbell = st.slider("Cliquengröße k (Barbell hat 2k Knoten)", *bounds("kbarbell_slider"), value=int(ss["kbarbell_slider"]), key="kbarbell_widget", on_change=store_from_widget,
                               args=("kbarbell_slider",))
        seed = int(ss["seed_input"])
    order = st.radio("Nachbarreihenfolge", options=list(C.ORDERS), format_func=lambda v: C.ORDER_LABELS[v], key="order_select",
                      help="Ändert nie ein Zentralitätsmaß - nur die Wiedergabe-Reihenfolge in Schritt 2.")

sync_query_params({"kind_select": kind, "side_slider": int(side) if kind == "city" else int(ss["side_slider"]), "blocked_select": float(blocked) if kind == "city" else float(ss["blocked_select"]),
                    "nettype_select": nettype if kind == "city" else ss["nettype_select"], "kbarbell_slider": int(k_barbell) if kind == "barbell" else int(ss["kbarbell_slider"]),
                    "seed_input": int(seed), "order_select": order, "cen_step": int(ss["cen_step"])})

settings = ev.Settings(kind, int(side) if kind == "city" else C.DEFAULT_SIDE, float(blocked) if kind == "city" else 0.0, nettype if kind == "city" else "grid",
                        int(k_barbell) if kind == "barbell" else C.DEFAULT_BARBELL_K, int(seed), order, float(ss.get("damping_slider", C.DEFAULT_DAMPING)))

step = st.select_slider("Schritt", options=list(C.STEPS), key="cen_step", format_func=lambda s: C.STEPS[s])
expected_n = settings.side ** 2 if settings.kind == "city" else 2 * settings.k_barbell
vitality_large = expected_n > C.VITALITY_MAX_N
need_vitality = step == 4 and (not vitality_large or ss.get("vitality_forced"))
if step == 4 and vitality_large and not ss.get("vitality_forced"):
    st.warning(f"Dieses Netz hat {_german(expected_n)} Knoten - die Vitalität (Aufwand ~ n² · (n+m)) wird hier nicht automatisch berechnet.")
    if st.button("Trotzdem berechnen (kann einen Moment dauern)", key="vitality_force_btn"):
        ss["vitality_forced"] = True
        need_vitality = True
with st.spinner("Rechne..."):
    inst, a = _analysis(settings, need_vitality)
adj = A.adjacency(inst.n, inst.edges, settings.order, settings.seed)

st.markdown("## 🎯 Das Netz und seine Zentralität")
n_comp = len(a.ll.comp_size)
st.markdown(f"**{a.n} Knoten, {_german(a.m)} Kanten**{' (' + C.KIND_LABELS[kind] + ')' if kind == 'city' else ''}, **{len(a.ll.bridges)} Brücken, {len(a.ll.articulation)} Artikulationspunkte**"
            f"{f', {n_comp} Komponenten' if n_comp > 1 else ''}.")

if step == 1:
    measure = st.radio("Zentralitätsmaß", options=list(C.MEASURES), format_func=lambda v: C.MEASURE_LABELS[v], horizontal=True, key="measure_select")
    values_map = {"degree": a.degree, "closeness": a.closeness, "betweenness": a.betweenness_node, "pagerank": a.pagerank}
    values = values_map[measure]
    if measure == "pagerank":
        damping = st.slider("Dämpfungsfaktor (PageRank)", *bounds("damping_slider"), value=float(ss["damping_slider"]), key="damping_widget", on_change=store_from_widget, args=("damping_slider",),
                             help="Wahrscheinlichkeit, einem Nachbarn zu folgen, statt zufällig irgendwohin zu springen.")
        if damping != settings.damping:
            settings = dataclasses.replace(settings, damping=damping)
            with st.spinner("Rechne..."):
                inst, a = _analysis(settings, need_vitality)
            values = a.pagerank
    st.plotly_chart(viz.build_measure_map(inst, values, C.MEASURE_LABELS[measure]), width="stretch", key=f"s1_map_{measure}")
    top = sorted(range(inst.n), key=lambda v: -values[v])[:3]
    st.caption(f"Höchste Werte bei Knoten {', '.join(str(v) for v in top)}.")
elif step == 2:
    src_max = max(0, inst.n - 1)
    default_src = a.betweenness_node.index(max(a.betweenness_node)) if a.betweenness_node else 0
    ss.setdefault("brandes_source", min(default_src, src_max))
    source = st.slider("Startknoten der Breitensuche", 0, src_max, key="brandes_source")
    run = A.brandes_source(adj, source)
    n_total = 2 * len(run.order)
    ss["brandes_step"] = n_total if "brandes_step" not in ss else min(max(1, int(ss["brandes_step"])), n_total)
    if n_total > 1:
        k = st.slider("Wiedergabe-Schritt", 1, n_total, key="brandes_step", help="1 bis n = Vorwärtsphase (BFS, sigma); danach die Rückwärtsphase (delta).")
    else:
        k = n_total
    st.plotly_chart(viz.build_brandes_map(inst, run, k), width="stretch", key=f"s2_map_{source}_{k}")
    phase = "Vorwärtsphase: Breitensuche, sigma = Zahl kürzester Wege von der Quelle" if k <= len(run.order) else "Rückwärtsphase: Abhängigkeit delta wird von den am weitesten entfernten Knoten " \
        "zurück akkumuliert"
    st.caption(phase)
    with st.expander("Tabelle: sigma und delta je Knoten"):
        st.dataframe(viz.brandes_table(run, k), width="stretch", hide_index=True)
elif step == 3:
    if a.ll.bridges:
        bridge_names = [f"{u}-{v}" for u, v in a.ll.bridges]
        ss.setdefault("bridge_select", bridge_names[0])
        if ss["bridge_select"] not in bridge_names:
            ss["bridge_select"] = bridge_names[0]
        chosen = st.selectbox("Brücke hervorheben", options=bridge_names, key="bridge_select")
        u, v = (int(x) for x in chosen.split("-"))
        st.plotly_chart(viz.build_bridge_map(inst, a.ll, a.betweenness_edge, highlight=(u, v)), width="stretch", key=f"s3_map_{chosen}")
        measured, formula = a.bridge_check[(u, v)]
        m1, m2 = st.columns(2)
        m1.metric("gemessene Kanten-Betweenness (Brandes)", f"{measured:.1f}")
        m2.metric("a · (S − a)", f"{formula:.0f}")
        st.success("Exakt gleich - kein Zufall: jedes der a·(S-a) getrennten Knotenpaare benutzt genau diese eine Brücke als einzigen kürzesten Weg." if abs(measured - formula) < 1e-6 else
                   "Weichen ab - das sollte nicht passieren (Fehler).")
    else:
        st.plotly_chart(viz.build_bridge_map(inst, a.ll, a.betweenness_edge), width="stretch", key="s3_map_none")
        st.caption("Dieses Netz hat keine Brücke (z. B. ein dichter Zufallsgraph oder ein ungesperrtes Raster mit Rundwegen).")
else:
    if a.vitality is not None:
        measures = {"Grad": a.degree, "Closeness": a.closeness, "Betweenness": a.betweenness_node, "PageRank": a.pagerank}
        corrs = {name: A.spearman(vals, a.vitality) for name, vals in measures.items()}
        st.plotly_chart(viz.build_vitality_scatter_grid(measures, a.vitality, corrs), width="stretch", key="s4_scatter")
        best = max(corrs, key=corrs.get)
        st.caption(f"**{best}** sagt die Vitalität auf dieser Instanz am besten vorher (Spearman = {corrs[best]:.2f}). Rangkorrelation, keine Kausalität - andere Netztypen können abweichen "
                   "(siehe Messreihe im README).")
    st.markdown("#### 🔬 Aufwand: naiv gegen Brandes über die Größe")
    if st.button("Über die Größe messen (kann einen Moment dauern)", key="cost_start"):
        ss["cost_done"] = True
    if ss.get("cost_done"):
        with st.spinner("Rechne..."):
            rows_cost = _cost_sweep()
        st.plotly_chart(viz.build_cost_sweep(rows_cost), width="stretch", key="s4_cost")
        st.caption(f"Median über {len(C.SWEEP_SEEDS)} feste Instanzen je Größe (Raster, {C.DEFAULT_BLOCKED * 100:.0f} % gesperrt).")
    st.markdown("#### 🔬 Rangkorrelation über Netztyp und Sperranteil (Vormessung)")
    if st.button("Über Netztyp und Sperranteil messen (kann einen Moment dauern)", key="corr_start"):
        ss["corr_done"] = True
    if ss.get("corr_done"):
        with st.spinner("Rechne..."):
            rows_corr = _correlation_sweep()
        st.dataframe(rows_corr, width="stretch", hide_index=True)
        st.caption("Median der Spearman-Rangkorrelation gegen Vitalität, über 5 feste Seeds je Zeile (12 × 12 = 144 Knoten).")

st.markdown("---")

st.markdown("## 🎯 Was das Netz verrät")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Knoten", _german(a.n), delta_color="off")
r2.metric("Kanten", _german(a.m), delta_color="off")
r3.metric("Brücken", _german(len(a.ll.bridges)), delta_color="off")
r4.metric("Artikulationspunkte", _german(len(a.ll.articulation)), delta_color="off")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ungerichtete Betweenness/PageRank reichen** | Gerichtete Netze (Einbahnstraßen, Zitationen) brauchen eigene Varianten - hier nicht umgesetzt. | - |
| **Vitalität über globale Effizienz genügt** | Andere Schadensmaße (z. B. größte Komponente, Umwegkosten) können ein anderes Maß bevorzugen. | - |
| **Elementarschritte zeigen den Aufwand** | Sie zählen Knoten- und Kantenbesuche, keine Rechenzeit oder Speicherbedarf. | - |
| **Ein Maß gewinnt immer** | Die Messreihe zeigt: welches Maß die Vitalität am besten vorhersagt, hängt vom Netztyp und Sperranteil ab (siehe README). | - |
| **Die naive Betweenness ist nur langsam** | Bei vielen gleich langen Wegen (z. B. ein reguläres Raster) wächst sie exponentiell, nicht nur polynomiell langsamer. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Grad.** $\deg(v) = |N(v)|$, die Zahl der Nachbarn.

**Closeness (Wasserman und Faust 1994, Bavelas 1950).** $C(v) = \frac{r(v)-1}{\sum_{u \in R(v)} d(v,u)} \cdot \frac{r(v)-1}{n-1}$, wobei $R(v)$ die von $v$ erreichbaren Knoten sind und $r(v)=|R(v)|$
(die zweite Bruchklammer verhindert, dass ein Knoten, der nur einen kleinen Teil des Netzes erreicht, künstlich hoch bewertet wird).

**Betweenness (Freeman 1977).** $C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$, wobei $\sigma_{st}$ die Zahl der kürzesten $s$-$t$-Wege ist und $\sigma_{st}(v)$ die davon über $v$.
Analog für eine Kante $e$. Hier UNNORMIERT (jedes Paar zählt einmal), damit die Kanten-Betweenness einer Brücke direkt die Zahl der getrennten Knotenpaare ist.

**Brandes (2001).** Statt für jedes Paar $(s,t)$ separat zu zählen: eine Breitensuche je Quelle $s$ liefert $\sigma_{sv}$ vorwärts; rückwärts (von den am weitesten entfernten Knoten zur Quelle) wird die
Abhängigkeit $\delta_s(v) = \sum_{w: v \in P_s(w)} \frac{\sigma_{sv}}{\sigma_{sw}}(1+\delta_s(w))$ akkumuliert ($P_s(w)$ = Vorgänger von $w$ auf einem kürzesten Weg von $s$). Die Kanten-Abhängigkeit
fällt als Nebenprodukt derselben Rückwärtsphase ab. Gesamtaufwand $O(n \cdot m)$ statt exponentiell bei expliziter Aufzählung.

**Brücken-Satz.** Trennt eine Brücke $(u,v)$ eine Komponente der Größe $S$ in Teile der Größe $a$ und $S-a$, ist ihre Kanten-Betweenness exakt $a \cdot (S-a)$: jedes der $a(S-a)$ Knotenpaare zwischen den
beiden Teilen hat genau EINEN kürzesten Weg, und der läuft zwangsläufig über die Brücke.

**PageRank (Brin und Page 1998).** $PR(v) = \frac{1-d}{n} + d \sum_{u \in N(v)} \frac{PR(u)}{\deg(u)}$, Potenzmethode bis zum Fixpunkt (Dämpfung $d$, hier 0.85).

**Globale Effizienz und Vitalität (Latora und Marchiori 2001).** $E(G) = \sum_{u<v} \frac{1}{d(u,v)}$ (unerreichbare Paare tragen 0 bei). Die Vitalität von $v$ ist $E(G) - E(G \setminus v)$ - nie negativ,
weil das Entfernen eines Knotens Abstände nur vergrößern oder gleich lassen kann.

**Literatur.** Freeman, L. C. (1977). *A set of measures of centrality based on betweenness.* Sociometry 40(1), 35–41. Brandes, U. (2001). *A faster algorithm for betweenness centrality.* Journal of
Mathematical Sociology 25(2), 163–177. Brin, S., & Page, L. (1998). *The anatomy of a large-scale hypertextual web search engine.* Computer Networks and ISDN Systems 30(1-7), 107–117. Latora, V., &
Marchiori, M. (2001). *Efficient behavior of small-world networks.* Physical Review Letters 87(19), 198701.

Implementiert in `cen_algorithm.py` (alle vier Maße, Brandes, PageRank, Effizienz/Vitalität), `cen_scenario.py` (Instanzen), `cen_evaluation.py` (Analyse, Sweeps).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Graphen und Netzwerke: BFS bis Cliquenbandbreite](https://sebastianhanisch.net/konzepte-graphen-netzwerke.html)."
)
