"""Pure SVG publication figures with no plotting dependency."""

from __future__ import annotations

import html


def _svg(body: str, title: str, width: int = 800, height: int = 440) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img"><title>%s</title><style>text{font-family:Georgia,serif;fill:#17212b}.axis{stroke:#17212b}.grid{stroke:#d8d0c3}.bar{fill:#bb4d2e}.line{fill:none;stroke:#1d6b68;stroke-width:3}.point{fill:#bb4d2e}</style>%s</svg>'
        % (width, height, html.escape(title), body)
    )


def svg_waterfall_decomposition(
    p_greedy: float,
    p_sampled: float,
    p_mas: float,
    title: str = "PACE Accounting Decomposition",
) -> str:
    values = [p_greedy, p_sampled - p_greedy, p_sampled, p_mas - p_sampled]
    labels = [
        "Category A",
        "Compute Scaling Effect",
        "Category B",
        "Coordination Residual",
    ]
    body = '<line class="axis" x1="55" y1="380" x2="760" y2="380"/>'
    for i, (value, label) in enumerate(zip(values, labels)):
        x = 75 + i * 170
        y = 380 - abs(value) * 280
        h = abs(value) * 280
        body += (
            '<rect class="bar" x="%d" y="%.1f" width="100" height="%.1f"/><text x="%d" y="405" font-size="12">%s</text><text x="%d" y="%.1f" font-size="12">%.3f</text>'
            % (x, y, h, x, html.escape(label), x, y - 6, value)
        )
    return _svg(body, title)


def svg_phase_diagram(
    rho_grid: list[float] | None = None,
    k_team: int = 5,
    empirical_point: tuple[float, float] | None = None,
) -> str:
    rho_grid = rho_grid or [0, 0.25, 0.5, 0.75]
    body = '<line class="axis" x1="55" y1="190" x2="370" y2="190"/><line class="axis" x1="55" y1="30" x2="55" y2="190"/><line class="axis" x1="430" y1="190" x2="760" y2="190"/><line class="axis" x1="430" y1="30" x2="430" y2="190"/><text x="65" y="22">A: K_eff vs K</text><text x="440" y="22">B: beneficial phase boundary</text>'
    for index, rho in enumerate(rho_grid):
        points = []
        for k in range(1, k_team + 1):
            points.append(
                "%d,%.1f" % (55 + k * 55, 190 - (k / (1 + (k - 1) * rho)) * 25)
            )
        body += (
            '<polyline class="line" points="%s"/><text x="%d" y="210" font-size="11">rho=%.2f</text>'
            % (" ".join(points), 60 + index * 75, rho)
        )
    boundary = []
    for i in range(1, 10):
        kappa = i / 2
        boundary.append("%.1f,%.1f" % (430 + i * 30, 190 - (kappa / (1 + kappa)) * 150))
    body += '<polyline class="line" points="%s"/>' % " ".join(boundary)
    if empirical_point:
        body += '<circle class="point" cx="%.1f" cy="%.1f" r="6"/>' % (
            430 + empirical_point[0] * 30,
            190 - empirical_point[1] * 150,
        )
    return _svg(body, "PACE Phase Diagram")


def svg_frontier_curve(
    frontier_points: list[dict], mas_points: list[dict] | None = None
) -> str:
    body = '<line class="axis" x1="55" y1="380" x2="760" y2="380"/><line class="axis" x1="55" y1="30" x2="55" y2="380"/>'
    points = [
        "%.1f,%.1f"
        % (
            55
            + float(row["tokens"])
            / max(1, max(float(item["tokens"]) for item in frontier_points))
            * 680,
            380 - float(row["accuracy"]) * 330,
        )
        for row in frontier_points
    ]
    body += '<polyline class="line" points="%s"/>' % " ".join(points)
    for row in mas_points or []:
        body += (
            '<circle class="point" cx="%.1f" cy="%.1f" r="5"/><text x="%.1f" y="%.1f" font-size="12">%s</text>'
            % (
                55
                + float(row["tokens"])
                / max(1, max(float(item["tokens"]) for item in frontier_points))
                * 680,
                380 - float(row["accuracy"]) * 330,
                60
                + float(row["tokens"])
                / max(1, max(float(item["tokens"]) for item in frontier_points))
                * 680,
                375 - float(row["accuracy"]) * 330,
                html.escape(str(row.get("label", "MAS"))),
            )
        )
    return _svg(body, "PACE Frontier Curve")


def svg_influence_curves(
    by_correct_peers: dict, fit_result: dict, k_agents: int
) -> str:
    body = '<line class="axis" x1="55" y1="380" x2="760" y2="380"/><line class="axis" x1="55" y1="30" x2="55" y2="380"/>'
    for key, cell in by_correct_peers.items():
        own, peers = (
            key
            if isinstance(key, tuple)
            else (
                int(str(key).split("=")[1].split(",")[0]),
                int(str(key).split("=")[-1]),
            )
        )
        x = peers / max(1, k_agents - 1)
        y = cell.get("p_switch", cell.get("p_correct_next", 0))
        body += '<circle class="point" cx="%.1f" cy="%.1f" r="4"/>' % (
            55 + x * 680,
            380 - y * 330,
        )
    for name, model in fit_result.get("models", {}).items():
        power = 0 if name == "constant" else 1 if name == "linear_martingale" else 2
        points = [
            "%.1f,%.1f" % (55 + x * 680, 380 - min(1, model["a"] * x**power) * 330)
            for x in [i / 20 for i in range(21)]
        ]
        body += '<polyline class="line" points="%s"/>' % " ".join(points)
    return _svg(body, "PACE Peer Influence Curves")
