from __future__ import annotations

import html
import sys
from pathlib import Path

from src.qspice_tools.csv_reader import QspiceCsvData, read_qspice_csv
from src.qspice_tools.waveform_report import _format_number


def generate_project_dashboard(
    data: QspiceCsvData,
    output_path: Path,
    waveform_report_path: Path,
    circuit_path: Path,
    csv_path: Path,
) -> None:
    html_text = render_project_dashboard(
        data=data,
        waveform_report_path=waveform_report_path,
        circuit_path=circuit_path,
        csv_path=csv_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")


def render_project_dashboard(
    data: QspiceCsvData,
    waveform_report_path: Path,
    circuit_path: Path,
    csv_path: Path,
) -> str:
    traces = [column for column in data.columns if column != "Time"]
    stat_cards = "\n".join(_render_trace_card(data, trace) for trace in traces)
    report_href = html.escape(waveform_report_path.as_posix())
    circuit_display = html.escape(circuit_path.as_posix())
    csv_display = html.escape(csv_path.as_posix())
    runner_command = (
        "scripts\\run-qspice-circuit.bat "
        + str(circuit_path).replace("/", "\\")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QSPICE Engineering Calculator</title>
  <style>
    :root {{
      --page: #f4f7fb;
      --panel: #ffffff;
      --ink: #182234;
      --muted: #667085;
      --line: #d8e0eb;
      --dark: #172033;
      --green: #0f766e;
      --blue: #2563eb;
      --amber: #b45309;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--page);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }}
    header {{
      background: var(--dark);
      color: #ffffff;
      padding: 22px 28px;
    }}
    header h1 {{
      margin: 0 0 6px;
      font-size: 25px;
      letter-spacing: 0;
    }}
    header p {{
      margin: 0;
      color: #cbd5e1;
      font-size: 14px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.1fr .9fr;
      gap: 16px;
      align-items: start;
    }}
    section, .metric, .step {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    section {{ margin-bottom: 16px; }}
    h2 {{
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      font-size: 17px;
      letter-spacing: 0;
    }}
    .body {{ padding: 16px; }}
    .status {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }}
    .metric {{
      padding: 12px;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .metric strong {{
      display: block;
      font-size: 18px;
      letter-spacing: 0;
    }}
    .workflow {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .step {{
      padding: 12px;
      min-height: 118px;
    }}
    .step b {{
      display: block;
      font-size: 14px;
      margin-bottom: 8px;
    }}
    .step p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.45;
      font-size: 13px;
    }}
    .trace-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }}
    .trace {{
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 12px;
      background: #fbfcfe;
    }}
    .trace h3 {{
      margin: 0 0 10px;
      font-size: 15px;
      letter-spacing: 0;
    }}
    .trace dl {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin: 0;
      font-size: 13px;
    }}
    .trace dt {{ color: var(--muted); }}
    .trace dd {{
      margin: 0;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    code {{
      display: block;
      white-space: pre-wrap;
      background: #101827;
      color: #e5edf7;
      border-radius: 6px;
      padding: 12px;
      font-size: 13px;
      line-height: 1.5;
    }}
    a.button {{
      display: inline-block;
      background: var(--green);
      color: #ffffff;
      text-decoration: none;
      padding: 10px 12px;
      border-radius: 6px;
      font-weight: 700;
      margin-top: 10px;
    }}
    .fileline {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }}
    @media (max-width: 900px) {{
      .grid, .status, .workflow, .trace-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>QSPICE Engineering Calculator</h1>
    <p>Engineering calculator prototype with QSPICE CLI validation, CSV import, and waveform reporting.</p>
  </header>
  <main>
    <section>
      <h2>MVP Status</h2>
      <div class="body status">
        <div class="metric"><span>QSPICE CLI</span><strong>Validated</strong></div>
        <div class="metric"><span>CSV Import</span><strong>{data.sample_count} samples</strong></div>
        <div class="metric"><span>Traces</span><strong>{len(traces)}</strong></div>
        <div class="metric"><span>Waveform Report</span><strong>Ready</strong></div>
        <div class="metric"><span>PWG Display Panel</span><strong>Specified</strong></div>
      </div>
    </section>

    <section>
      <h2>Workflow</h2>
      <div class="body workflow">
        <div class="step"><b>1. Generate Input</b><p>Create PWL or circuit netlist files for QSPICE simulation.</p></div>
        <div class="step"><b>2. Run QSPICE CLI</b><p>Execute the Windows runner against the selected `.cir` file.</p></div>
        <div class="step"><b>3. Export CSV</b><p>Export selected QSPICE traces such as V(out), V(in), and I(R1).</p></div>
        <div class="step"><b>4. Analyze</b><p>Import CSV, compute engineering stats, and view waveform reports.</p></div>
      </div>
    </section>

    <div class="grid">
      <section>
        <h2>Trace Summary</h2>
        <div class="body trace-grid">
{stat_cards}
        </div>
      </section>

      <section>
        <h2>Run Command</h2>
        <div class="body">
          <code>{html.escape(runner_command)}</code>
          <p class="fileline">Circuit: {circuit_display}</p>
          <p class="fileline">CSV: {csv_display}</p>
          <a class="button" href="{report_href}">Open Waveform Report</a>
          <a class="button" href="pwg_display_panel_spec.html">Open PWG Display Panel Spec</a>
          <a class="button" href="pwg_lcr_report.html">Open PWG LCR Result Report</a>
          <a class="button" href="pwg_lcr_comparison.html">Open PWG Input Output Comparison</a>
          <p class="fileline">PWG LCR test: scripts\\run-qspice-circuit.bat examples\\pwg-lcr\\pwg_lcr.cir</p>
        </div>
      </section>
    </div>
  </main>
</body>
</html>
"""


def _render_trace_card(data: QspiceCsvData, trace: str) -> str:
    stats = data.stats(trace)
    return f"""          <div class="trace">
            <h3>{html.escape(trace)}</h3>
            <dl>
              <dt>Min</dt><dd>{_format_number(stats.minimum)}</dd>
              <dt>Max</dt><dd>{_format_number(stats.maximum)}</dd>
              <dt>Avg</dt><dd>{_format_number(stats.average)}</dd>
              <dt>RMS</dt><dd>{_format_number(stats.rms)}</dd>
            </dl>
          </div>"""


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(
            "Usage: python -m src.qspice_tools.project_dashboard "
            "<input.csv> <output.html> <waveform-report.html> <circuit.cir>"
        )
        return 2

    csv_path = Path(argv[1])
    output_path = Path(argv[2])
    waveform_report_path = Path(argv[3])
    circuit_path = Path(argv[4])
    data = read_qspice_csv(csv_path)

    generate_project_dashboard(
        data=data,
        output_path=output_path,
        waveform_report_path=waveform_report_path,
        circuit_path=circuit_path,
        csv_path=csv_path,
    )
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
