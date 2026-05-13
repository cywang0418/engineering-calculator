from __future__ import annotations

import html
import sys
from pathlib import Path

from src.qspice_tools.csv_reader import QspiceCsvData, read_qspice_csv
from src.qspice_tools.waveform_report import (
    CHART_HEIGHT,
    CHART_WIDTH,
    PADDING_BOTTOM,
    PADDING_LEFT,
    PADDING_RIGHT,
    PADDING_TOP,
    _format_number,
    _grid_lines,
)


def generate_pwg_comparison_report(data: QspiceCsvData, output_path: Path) -> None:
    html_text = render_pwg_comparison_report(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")


def render_pwg_comparison_report(data: QspiceCsvData) -> str:
    vin = data.trace("V(in)")
    vout = data.trace("V(out)")
    times = data.time
    vin_stats = data.stats("V(in)")
    vout_stats = data.stats("V(out)")
    peak_gain = _peak_to_peak(vout) / _peak_to_peak(vin)
    rms_gain = vout_stats.rms / vin_stats.rms

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PWG Input Output Comparison</title>
  <style>
    :root {{
      --page: #f4f7fb;
      --panel: #ffffff;
      --ink: #182234;
      --muted: #667085;
      --line: #d8e0eb;
      --blue: #2563eb;
      --green: #0f766e;
      --dark: #172033;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--page);
      color: var(--ink);
    }}
    header {{
      background: var(--dark);
      color: #ffffff;
      padding: 20px 28px;
    }}
    header h1 {{
      margin: 0 0 6px;
      font-size: 24px;
      letter-spacing: 0;
    }}
    header p {{
      margin: 0;
      color: #cbd5e1;
      font-size: 14px;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }}
    section, .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-bottom: 18px;
      overflow: hidden;
    }}
    h2 {{
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      font-size: 17px;
      letter-spacing: 0;
    }}
    .body {{ padding: 16px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .metric {{
      padding: 12px;
      margin-bottom: 0;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .metric strong {{
      font-size: 20px;
      font-variant-numeric: tabular-nums;
    }}
    svg {{
      width: 100%;
      height: auto;
      display: block;
      border: 1px solid var(--line);
      background: #ffffff;
      border-radius: 6px;
    }}
    .axis-label {{
      fill: #667085;
      font-size: 12px;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .legend {{
      display: flex;
      gap: 16px;
      color: var(--muted);
      font-size: 13px;
      margin-top: 10px;
    }}
    .swatch {{
      display: inline-block;
      width: 22px;
      height: 3px;
      vertical-align: middle;
      margin-right: 6px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    th:first-child, td:first-child {{ text-align: left; }}
    th {{ background: #f8fafc; color: #475467; }}
    @media (max-width: 900px) {{
      .metrics {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>PWG Input Output Comparison</h1>
    <p>10k Hz sinusoidal PWG input compared with QSPICE LCR output.</p>
  </header>
  <main>
    <section>
      <h2>Comparison Metrics</h2>
      <div class="body metrics">
        <div class="metric"><span>Input Peak-to-Peak</span><strong>{_format_number(_peak_to_peak(vin))} V</strong></div>
        <div class="metric"><span>Output Peak-to-Peak</span><strong>{_format_number(_peak_to_peak(vout))} V</strong></div>
        <div class="metric"><span>Peak Gain</span><strong>{_format_number(peak_gain)}</strong></div>
        <div class="metric"><span>RMS Gain</span><strong>{_format_number(rms_gain)}</strong></div>
      </div>
    </section>

    <section>
      <h2>Overlay Waveform</h2>
      <div class="body">
        {_render_overlay_chart(times, vin, vout)}
        <div class="legend">
          <span><span class="swatch" style="background:#2563eb"></span>V(in)</span>
          <span><span class="swatch" style="background:#0f766e"></span>V(out)</span>
        </div>
      </div>
    </section>

    <section>
      <h2>Trace Statistics</h2>
      <div class="body">
        <table>
          <thead>
            <tr><th>Trace</th><th>Minimum</th><th>Maximum</th><th>Average</th><th>RMS</th></tr>
          </thead>
          <tbody>
            {_row("V(in)", vin_stats)}
            {_row("V(out)", vout_stats)}
          </tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>
"""


def _render_overlay_chart(times: list[float], vin: list[float], vout: list[float]) -> str:
    combined = vin + vout
    y_min, y_max = min(combined), max(combined)
    x_min, x_max = min(times), max(times)
    vin_points = _polyline_points_shared_scale(times, vin, y_min, y_max)
    vout_points = _polyline_points_shared_scale(times, vout, y_min, y_max)

    return f"""<svg viewBox="0 0 {CHART_WIDTH} {CHART_HEIGHT}" role="img" aria-label="V(in) and V(out) overlay">
          {_grid_lines()}
          <line x1="{PADDING_LEFT}" y1="{CHART_HEIGHT - PADDING_BOTTOM}" x2="{CHART_WIDTH - PADDING_RIGHT}" y2="{CHART_HEIGHT - PADDING_BOTTOM}" stroke="#98a2b3" />
          <line x1="{PADDING_LEFT}" y1="{PADDING_TOP}" x2="{PADDING_LEFT}" y2="{CHART_HEIGHT - PADDING_BOTTOM}" stroke="#98a2b3" />
          <text x="{PADDING_LEFT}" y="{CHART_HEIGHT - 16}" class="axis-label">t={_format_number(x_min)}s</text>
          <text x="{CHART_WIDTH - 150}" y="{CHART_HEIGHT - 16}" class="axis-label">t={_format_number(x_max)}s</text>
          <text x="12" y="{PADDING_TOP + 12}" class="axis-label">max {_format_number(y_max)} V</text>
          <text x="12" y="{CHART_HEIGHT - PADDING_BOTTOM}" class="axis-label">min {_format_number(y_min)} V</text>
          <polyline fill="none" stroke="#2563eb" stroke-width="2.4" points="{vin_points}" />
          <polyline fill="none" stroke="#0f766e" stroke-width="2.4" points="{vout_points}" />
        </svg>"""


def _polyline_points_shared_scale(
    times: list[float],
    values: list[float],
    y_min: float,
    y_max: float,
) -> str:
    x_min, x_max = min(times), max(times)
    x_span = x_max - x_min or 1.0
    y_span = y_max - y_min or 1.0
    plot_width = CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT
    plot_height = CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM

    points = []
    for time, value in zip(times, values):
        x = PADDING_LEFT + ((time - x_min) / x_span) * plot_width
        y = PADDING_TOP + (1 - ((value - y_min) / y_span)) * plot_height
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def _row(trace: str, stats) -> str:
    return f"""<tr>
              <td>{html.escape(trace)}</td>
              <td>{_format_number(stats.minimum)}</td>
              <td>{_format_number(stats.maximum)}</td>
              <td>{_format_number(stats.average)}</td>
              <td>{_format_number(stats.rms)}</td>
            </tr>"""


def _peak_to_peak(values: list[float]) -> float:
    return max(values) - min(values)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python -m src.qspice_tools.pwg_comparison_report <input.csv> <output.html>")
        return 2

    data = read_qspice_csv(Path(argv[1]))
    generate_pwg_comparison_report(data, Path(argv[2]))
    print(f"wrote {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
