from __future__ import annotations

import html
import sys
from pathlib import Path

from src.qspice_tools.csv_reader import QspiceCsvData, read_qspice_csv


CHART_WIDTH = 980
CHART_HEIGHT = 360
PADDING_LEFT = 64
PADDING_RIGHT = 24
PADDING_TOP = 28
PADDING_BOTTOM = 48

TRACE_COLORS = {
    "V(out)": "#0f766e",
    "V(in)": "#2563eb",
    "I(R1)": "#b45309",
}


def generate_waveform_report(
    data: QspiceCsvData,
    output_path: Path,
    title: str = "QSPICE Waveform Report",
) -> None:
    html_text = render_waveform_report(data, title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")


def render_waveform_report(data: QspiceCsvData, title: str) -> str:
    traces = [column for column in data.columns if column != "Time"]
    escaped_title = html.escape(title)

    stat_rows = "\n".join(_render_stat_row(data, trace) for trace in traces)
    trace_sections = "\n".join(_render_trace_chart(data, trace) for trace in traces)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #182234;
      --muted: #667085;
      --line: #d9e0ea;
      --panel: #ffffff;
      --page: #f3f6fa;
      --grid: #e6ebf2;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--page);
      color: var(--ink);
    }}
    header {{
      background: #172033;
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
    section {{
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
    .section-body {{ padding: 16px; }}
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
    th {{
      color: #475467;
      font-weight: 700;
      background: #f8fafc;
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
    .trace-label {{
      font-size: 13px;
      font-weight: 700;
      font-family: Arial, Helvetica, sans-serif;
    }}
  </style>
</head>
<body>
  <header>
    <h1>QSPICE Waveform Report</h1>
    <p>{escaped_title} - samples: {data.sample_count}, traces: {len(traces)}</p>
  </header>
  <main>
    <section>
      <h2>Trace Statistics</h2>
      <div class="section-body">
        <table>
          <thead>
            <tr>
              <th>Trace</th>
              <th>Minimum</th>
              <th>Maximum</th>
              <th>Average</th>
              <th>RMS</th>
            </tr>
          </thead>
          <tbody>
{stat_rows}
          </tbody>
        </table>
      </div>
    </section>
{trace_sections}
  </main>
</body>
</html>
"""


def _render_stat_row(data: QspiceCsvData, trace: str) -> str:
    stats = data.stats(trace)
    return f"""            <tr>
              <td>{html.escape(trace)}</td>
              <td>{_format_number(stats.minimum)}</td>
              <td>{_format_number(stats.maximum)}</td>
              <td>{_format_number(stats.average)}</td>
              <td>{_format_number(stats.rms)}</td>
            </tr>"""


def _render_trace_chart(data: QspiceCsvData, trace: str) -> str:
    values = data.trace(trace)
    times = data.time
    color = TRACE_COLORS.get(trace, "#4f46e5")
    points = _polyline_points(times, values)
    y_min, y_max = min(values), max(values)
    x_min, x_max = min(times), max(times)
    escaped_trace = html.escape(trace)

    return f"""    <section>
      <h2>{escaped_trace}</h2>
      <div class="section-body">
        <svg viewBox="0 0 {CHART_WIDTH} {CHART_HEIGHT}" role="img" aria-label="{escaped_trace} waveform">
          {_grid_lines()}
          <line x1="{PADDING_LEFT}" y1="{CHART_HEIGHT - PADDING_BOTTOM}" x2="{CHART_WIDTH - PADDING_RIGHT}" y2="{CHART_HEIGHT - PADDING_BOTTOM}" stroke="#98a2b3" />
          <line x1="{PADDING_LEFT}" y1="{PADDING_TOP}" x2="{PADDING_LEFT}" y2="{CHART_HEIGHT - PADDING_BOTTOM}" stroke="#98a2b3" />
          <text x="{PADDING_LEFT}" y="{CHART_HEIGHT - 16}" class="axis-label">t={_format_number(x_min)}s</text>
          <text x="{CHART_WIDTH - 150}" y="{CHART_HEIGHT - 16}" class="axis-label">t={_format_number(x_max)}s</text>
          <text x="12" y="{PADDING_TOP + 12}" class="axis-label">max {_format_number(y_max)}</text>
          <text x="12" y="{CHART_HEIGHT - PADDING_BOTTOM}" class="axis-label">min {_format_number(y_min)}</text>
          <text x="{PADDING_LEFT}" y="20" fill="{color}" class="trace-label">{escaped_trace}</text>
          <polyline fill="none" stroke="{color}" stroke-width="2.4" points="{points}" />
        </svg>
      </div>
    </section>"""


def _grid_lines() -> str:
    lines: list[str] = []
    plot_width = CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT
    plot_height = CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM

    for index in range(6):
        x = PADDING_LEFT + plot_width * index / 5
        lines.append(
            f'<line x1="{x:.2f}" y1="{PADDING_TOP}" x2="{x:.2f}" '
            f'y2="{CHART_HEIGHT - PADDING_BOTTOM}" stroke="#e6ebf2" />'
        )

    for index in range(5):
        y = PADDING_TOP + plot_height * index / 4
        lines.append(
            f'<line x1="{PADDING_LEFT}" y1="{y:.2f}" '
            f'x2="{CHART_WIDTH - PADDING_RIGHT}" y2="{y:.2f}" stroke="#e6ebf2" />'
        )

    return "\n          ".join(lines)


def _polyline_points(times: list[float], values: list[float]) -> str:
    if len(times) != len(values):
        raise ValueError("Time and trace sample counts do not match")

    x_min, x_max = min(times), max(times)
    y_min, y_max = min(values), max(values)

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


def _format_number(value: float) -> str:
    return f"{value:.9g}"


def main(argv: list[str]) -> int:
    if len(argv) not in (3, 4):
        print("Usage: python -m src.qspice_tools.waveform_report <input.csv> <output.html> [title]")
        return 2

    input_path = Path(argv[1])
    output_path = Path(argv[2])
    title = argv[3] if len(argv) == 4 else "QSPICE Waveform Report"

    data = read_qspice_csv(input_path)
    generate_waveform_report(data, output_path, title=title)
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
