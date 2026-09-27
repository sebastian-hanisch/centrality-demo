"""Plotly-Figuren: Karte mit einem wählbaren Zentralitätsmaß, Brandes-Wiedergabe (Vorwärts- und Rückwärtsphase), Brücken-Karte mit Kanten-Betweenness, Vitalitäts-Streudiagramme (2x2), Aufwandskurve.
Alle Achsen fest (fixedrange); Karten mit gleichem Maßstab nutzen `scaleanchor` mit autorange und zwei unsichtbaren Eckpunkten (wie in den Geschwistern)."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

TEAL, ORANGE, BLUE, RED, PURPLE, GREY, LIGHT = "#2F6B65", "#f58518", "#4c78a8", "#e45756", "#7b3fbf", "#b7bec7", "#e8ebee"


def _lines(xy, pairs):
    xs, ys = [], []
    for u, v in pairs:
        xs += [xy[u][0], xy[v][0], None]
        ys += [xy[u][1], xy[v][1], None]
    return xs, ys


def _base_layout(fig, height=430, title=None):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=36 if title else 10, b=10), showlegend=False, title=dict(text=title, x=0.01, font=dict(size=14)) if title else None,
                       plot_bgcolor="white")
    fig.update_xaxes(visible=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, fixedrange=True)
    return fig


def _corners(fig, xy):
    pad = 0.4
    fig.add_trace(go.Scatter(x=[xy[:, 0].min() - pad, xy[:, 0].max() + pad], y=[xy[:, 1].min() - pad, xy[:, 1].max() + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip"))


def _pairs(inst):
    return [(u, v) for u, v, _ in inst.edges]


# --- 1 · Vier Maße auf einer Karte ------------------------------------------------------------------------------------------------------------------


def build_measure_map(inst, values, measure_label, size_range=(6, 26)):
    """Knotengröße UND -farbe nach `values` (ein Zentralitätsmaß); Farbskala oben mit ~4 Ticks."""
    xy = inst.xy
    fig = go.Figure()
    ex, ey = _lines(xy, _pairs(inst))
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#dfe3e8", width=1.2), hoverinfo="skip"))
    lo, hi = min(values), max(values)
    span = hi - lo if hi > lo else 1.0
    sizes = [size_range[0] + (size_range[1] - size_range[0]) * (v - lo) / span for v in values]
    fig.add_trace(go.Scatter(x=xy[:, 0], y=xy[:, 1], mode="markers", marker=dict(size=sizes, color=values, colorscale="Viridis", showscale=True,
                              colorbar=dict(title=measure_label, orientation="h", y=1.08, len=0.6, thickness=14, tickmode="linear", tick0=lo, dtick=max(span / 3, 1e-9)),
                              line=dict(color="white", width=1)),
                              hovertext=[f"Knoten {v}: {measure_label} = {values[v]:.4g}" for v in range(inst.n)], hoverinfo="text"))
    _corners(fig, xy)
    return _base_layout(fig, 440)


# --- 2 · Brandes in Aktion ---------------------------------------------------------------------------------------------------------------------------


def build_brandes_map(inst, run, k):
    """Zustand nach k Schritten der Wiedergabe: erst die Vorwärtsphase (BFS-Entdeckung, Farbe = sigma), dann die Rückwärtsphase (Farbe wechselt auf delta, in umgekehrter Entdeckungsreihenfolge -
    zum Zeitpunkt, an dem ein Knoten rückwärts verarbeitet wird, ist sein delta bereits sein Endwert, weil alle Nachkommen zuvor verarbeitet wurden)."""
    xy = inst.xy
    order = run.order
    n_fwd = len(order)
    k = max(0, min(k, 2 * n_fwd))
    forward_done = order[:min(k, n_fwd)]
    backward_done = list(reversed(order))[:max(0, k - n_fwd)]
    phase = "Vorwärts (BFS, sigma)" if k <= n_fwd else "Rückwärts (Abhängigkeit delta)"
    cur = None
    if k > 0:
        cur = forward_done[-1] if k <= n_fwd else backward_done[-1]

    fig = go.Figure()
    ex, ey = _lines(xy, _pairs(inst))
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#dfe3e8", width=1.2), hoverinfo="skip"))
    # Baumkanten (Vorgänger) für alle bisher entdeckten Knoten
    tree_edges = [(run.preds[v][0], v) for v in forward_done if run.preds[v]]
    if tree_edges:
        tx, ty = _lines(xy, tree_edges)
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color=TEAL, width=2.6), hoverinfo="skip"))
    rest = [v for v in range(inst.n) if v not in set(forward_done)]
    if rest:
        fig.add_trace(go.Scatter(x=xy[rest, 0], y=xy[rest, 1], mode="markers", marker=dict(size=7, color="#cfd4da"), hoverinfo="skip"))
    if k <= n_fwd:
        shown = forward_done
        colorvals = [run.sigma[v] for v in shown]
        hover = [f"Knoten {v}: sigma = {run.sigma[v]}" for v in shown]
        cbar_title = "sigma"
    else:
        shown = forward_done                                 # alle vorwärts entdeckten Knoten bleiben sichtbar
        done_set = set(backward_done)
        colorvals = [run.delta[v] if v in done_set else 0.0 for v in shown]
        hover = [f"Knoten {v}: delta = {run.delta[v]:.3f}" if v in done_set else f"Knoten {v}: noch nicht rückwärts verarbeitet" for v in shown]
        cbar_title = "delta"
    if shown:
        fig.add_trace(go.Scatter(x=xy[shown, 0], y=xy[shown, 1], mode="markers", marker=dict(size=15, color=colorvals, colorscale="Viridis", showscale=True,
                                  colorbar=dict(title=cbar_title, orientation="h", y=1.08, len=0.5, thickness=12)), hovertext=hover, hoverinfo="text"))
    if cur is not None:
        fig.add_trace(go.Scatter(x=[xy[cur, 0]], y=[xy[cur, 1]], mode="markers", marker=dict(size=24, color="rgba(0,0,0,0)", line=dict(color=ORANGE, width=3)), hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 440, title=f"Quelle {run.source} - {phase}")


def brandes_table(run, k):
    """Zeilen (Knoten, sigma, delta, Status) der bisher wiedergegebenen Knoten."""
    order = run.order
    n_fwd = len(order)
    k = max(0, min(k, 2 * n_fwd))
    forward_done = order[:min(k, n_fwd)]
    backward_done = set(list(reversed(order))[:max(0, k - n_fwd)])
    rows = []
    for v in forward_done:
        rows.append({"Knoten": v, "sigma": run.sigma[v], "delta": round(run.delta[v], 4) if v in backward_done else "-",
                     "Status": "delta bestimmt" if v in backward_done else "nur entdeckt"})
    return rows


# --- 3 · Struktur gegen Zahl (Brücken und Kanten-Betweenness) ------------------------------------------------------------------------------------------


def build_bridge_map(inst, ll, edge_between, highlight=None):
    """Alle Kanten, Breite/Farbe der BRÜCKEN nach ihrer Kanten-Betweenness (die Formel a*(S-a) steht als Annotation an der auffälligsten Brücke); Artikulationspunkte als blaue Rauten."""
    xy = inst.xy
    fig = go.Figure()
    non_bridges = [(u, v) for u, v, _ in inst.edges if (u, v) not in set(ll.bridges)]
    nx_, ny_ = _lines(xy, non_bridges)
    fig.add_trace(go.Scatter(x=nx_, y=ny_, mode="lines", line=dict(color="#dfe3e8", width=1.4), hoverinfo="skip"))
    if ll.bridges:
        max_b = max(edge_between.get((u, v), 0.0) for u, v in ll.bridges) or 1.0
        for u, v in ll.bridges:
            val = edge_between.get((u, v), 0.0)
            width = 2.5 + 7.5 * (val / max_b)
            bx, by = _lines(xy, [(u, v)])
            fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=RED, width=width), hoverinfo="text", hovertext=f"Brücke {u}-{v}: Kanten-Betweenness = {val:.1f}"))
        best = max(ll.bridges, key=lambda e: edge_between.get(e, 0.0))
        u, v = best
        mx, my = (xy[u][0] + xy[v][0]) / 2, (xy[u][1] + xy[v][1]) / 2
        fig.add_annotation(x=mx, y=my, text=f"a·(S−a) = {edge_between.get(best, 0.0):.0f}", showarrow=True, arrowhead=2, bgcolor="white", bordercolor=RED, font=dict(size=12), ax=30, ay=-30)
    others = [v for v in range(inst.n) if v not in ll.articulation]
    fig.add_trace(go.Scatter(x=xy[others, 0], y=xy[others, 1], mode="markers", marker=dict(size=8, color="#9aa3ad"), hoverinfo="skip"))
    a = sorted(ll.articulation)
    if a:
        fig.add_trace(go.Scatter(x=xy[a, 0], y=xy[a, 1], mode="markers", marker=dict(size=14, color=BLUE, symbol="diamond", line=dict(color="white", width=1)),
                                  hovertext=[f"Artikulationspunkt {v}" for v in a], hoverinfo="text"))
    if highlight is not None:
        u, v = highlight
        hx, hy = _lines(xy, [(u, v)])
        fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", line=dict(color="black", width=10), opacity=0.3, hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 440)


# --- 4 · Welches Maß sagt den Schaden vorher? ------------------------------------------------------------------------------------------------------------


def build_vitality_scatter_grid(measures, vitality, corrs):
    """2x2-Streudiagramme: jedes Maß gegen Vitalität, Rangkorrelation im Subplot-Titel."""
    names = list(measures)
    fig = make_subplots(rows=2, cols=2, subplot_titles=[f"{name} (Spearman = {corrs[name]:.2f})" for name in names])
    colors = {names[0]: TEAL, names[1]: ORANGE, names[2]: RED, names[3]: BLUE} if len(names) == 4 else {n: TEAL for n in names}
    for i, name in enumerate(names):
        r, c = divmod(i, 2)
        fig.add_trace(go.Scatter(x=measures[name], y=vitality, mode="markers", marker=dict(size=6, color=colors.get(name, TEAL), opacity=0.65), hoverinfo="skip"), row=r + 1, col=c + 1)
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=50, b=10), showlegend=False, plot_bgcolor="white")
    fig.update_xaxes(fixedrange=True, gridcolor=LIGHT)
    fig.update_yaxes(fixedrange=True, gridcolor=LIGHT, title="Vitalität")
    return fig


def build_cost_sweep(rows):
    ns = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[r["naive"] for r in rows], mode="lines+markers", line=dict(color=RED, width=2.6), name="naive Betweenness (alle Wege aufzählen)"))
    fig.add_trace(go.Scatter(x=ns, y=[r["brandes"] for r in rows], mode="lines+markers", line=dict(color=TEAL, width=2.6), name="Brandes (eine BFS je Startknoten)"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.14), plot_bgcolor="white")
    fig.update_xaxes(title="Knotenzahl n", fixedrange=True)
    fig.update_yaxes(title="Elementarschritte", type="log", fixedrange=True)
    return fig
