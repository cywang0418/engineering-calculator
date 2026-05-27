from __future__ import annotations

import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.qspice_tools.csv_reader import read_qspice_csv
from src.qspice_tools.pwg_lcr_workflow import run_pwg_lcr_workflow
from src.qspice_tools.waveform_report import _format_number


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = PROJECT_ROOT / "qspice-cli-validation" / "examples" / "pwg-lcr"
REPORTS_DIR = PROJECT_ROOT / "reports"
CSV_PATH = CASE_DIR / "pwg_lcr.csv"


class QspiceAppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send_html(render_app())
            return
        if parsed.path == "/api/status":
            self._send_json(build_status())
            return
        if parsed.path.startswith("/reports/"):
            self._send_report_file(parsed.path.removeprefix("/reports/"))
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run-pwg-lcr":
            self.send_error(404)
            return

        try:
            result = run_pwg_lcr_workflow(
                case_dir=CASE_DIR,
                reports_dir=REPORTS_DIR,
                run_qspice=True,
            )
            self._send_json(
                {
                    "ok": True,
                    "qspiceExitCode": result.qspice_exit_code,
                    "csvExportExitCode": result.csv_export_exit_code,
                    "status": build_status(),
                }
            )
        except Exception as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(limit=6),
                },
                status=500,
            )

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _send_html(self, text: str, status: int = 200) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_report_file(self, name: str) -> None:
        path = (REPORTS_DIR / name).resolve()
        if REPORTS_DIR.resolve() not in path.parents or not path.exists():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_status() -> dict:
    status = {
        "csvExists": CSV_PATH.exists(),
        "qrawExists": (CASE_DIR / "pwg_lcr.qraw").exists(),
        "reports": {
            "waveform": (REPORTS_DIR / "pwg_lcr_report.html").exists(),
            "comparison": (REPORTS_DIR / "pwg_lcr_comparison.html").exists(),
        },
        "sampleCount": 0,
        "traces": [],
        "stats": {},
    }
    if not CSV_PATH.exists():
        return status

    data = read_qspice_csv(CSV_PATH)
    status["sampleCount"] = data.sample_count
    status["traces"] = [column for column in data.columns if column != "Time"]
    status["timeStart"] = data.time[0] if data.time else None
    status["timeEnd"] = data.time[-1] if data.time else None
    for trace in status["traces"]:
        stats = data.stats(trace)
        status["stats"][trace] = {
            "minimum": stats.minimum,
            "maximum": stats.maximum,
            "average": stats.average,
            "rms": stats.rms,
        }
    return status


def render_app() -> str:
    status = build_status()
    cards = "\n".join(_render_trace_card(trace, values) for trace, values in status["stats"].items())
    workflow_state = "Ready" if status["csvExists"] and status["reports"]["comparison"] else "Needs Run"
    sample_count = status["sampleCount"]
    time_range = ""
    if status.get("timeStart") is not None and status.get("timeEnd") is not None:
        time_range = f'{_format_number(status["timeStart"])} s to {_format_number(status["timeEnd"])} s'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QSPICE Engineering Calculator</title>
  <style>
    :root {{
      --page: #eef3f8;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #5f6c7b;
      --line: #d2dbe8;
      --accent: #0f766e;
      --accent-dark: #0b5f59;
      --blue: #1d4ed8;
      --warn: #a15c07;
      --code: #101827;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--page);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }}
    header {{
      background: #172033;
      color: #fff;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: center;
    }}
    h1 {{
      margin: 0 0 5px;
      font-size: 24px;
      letter-spacing: 0;
    }}
    header p {{
      margin: 0;
      color: #cbd5e1;
      font-size: 13px;
    }}
    main {{
      max-width: 1220px;
      margin: 0 auto;
      padding: 18px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
      align-items: start;
    }}
    section, .metric, .trace {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    section {{
      margin-bottom: 16px;
      overflow: hidden;
    }}
    h2 {{
      margin: 0;
      padding: 13px 15px;
      border-bottom: 1px solid var(--line);
      font-size: 16px;
      letter-spacing: 0;
    }}
    .body {{ padding: 15px; }}
    .run-button {{
      width: 100%;
      border: 0;
      border-radius: 7px;
      background: var(--accent);
      color: #fff;
      padding: 12px 14px;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
    }}
    .run-button:hover {{ background: var(--accent-dark); }}
    .run-button:disabled {{ background: #90a4b8; cursor: wait; }}
    .status-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
    }}
    .metric {{
      padding: 11px;
      min-height: 70px;
    }}
    .metric span, .trace dt, .small {{
      color: var(--muted);
      font-size: 12px;
    }}
    .metric strong {{
      display: block;
      margin-top: 7px;
      font-size: 18px;
      font-variant-numeric: tabular-nums;
    }}
    .trace-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .trace {{
      padding: 12px;
      background: #fbfcfe;
    }}
    .trace h3 {{
      margin: 0 0 10px;
      font-size: 15px;
    }}
    dl {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 7px;
      margin: 0;
      font-size: 13px;
    }}
    dd {{
      margin: 0;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    .links {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    a.button {{
      display: block;
      text-align: center;
      color: #fff;
      background: var(--blue);
      text-decoration: none;
      padding: 10px;
      border-radius: 7px;
      font-weight: 700;
      font-size: 13px;
    }}
    pre {{
      margin: 0;
      background: var(--code);
      color: #e5edf7;
      border-radius: 7px;
      padding: 12px;
      white-space: pre-wrap;
      min-height: 112px;
      font-size: 12px;
      line-height: 1.45;
    }}
    .path {{
      overflow-wrap: anywhere;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    iframe {{
      width: 100%;
      height: 560px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
    }}
    @media (max-width: 900px) {{
      header, .layout {{ display: block; }}
      .trace-grid, .links {{ grid-template-columns: 1fr; }}
      iframe {{ height: 460px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>QSPICE Engineering Calculator</h1>
      <p>PWG sine input, local QSPICE simulation, QUX CSV export, and waveform reports.</p>
    </div>
    <div class="small">Workflow: <strong id="workflow-state">{workflow_state}</strong></div>
  </header>
  <main>
    <div class="layout">
      <aside>
        <section>
          <h2>Run</h2>
          <div class="body">
            <button class="run-button" id="run-button">Run PWG LCR</button>
            <div class="status-grid">
              <div class="metric"><span>Samples</span><strong id="sample-count">{sample_count}</strong></div>
              <div class="metric"><span>Traces</span><strong id="trace-count">{len(status["traces"])}</strong></div>
              <div class="metric"><span>QRAW</span><strong id="qraw-state">{_yes_no(status["qrawExists"])}</strong></div>
              <div class="metric"><span>CSV</span><strong id="csv-state">{_yes_no(status["csvExists"])}</strong></div>
            </div>
          </div>
        </section>

        <section>
          <h2>Case</h2>
          <div class="body">
            <p class="path">Circuit: {CASE_DIR / "pwg_lcr.cir"}</p>
            <p class="path">CSV: {CSV_PATH}</p>
            <p class="path">Time: <span id="time-range">{time_range}</span></p>
          </div>
        </section>

        <section>
          <h2>Log</h2>
          <div class="body"><pre id="log">Ready.</pre></div>
        </section>
      </aside>

      <div>
        <section>
          <h2>Trace Summary</h2>
          <div class="body trace-grid" id="trace-grid">
{cards}
          </div>
        </section>

        <section>
          <h2>Reports</h2>
          <div class="body links">
            <a class="button" href="/reports/pwg_lcr_comparison.html" target="_blank">Input Output Comparison</a>
            <a class="button" href="/reports/pwg_lcr_report.html" target="_blank">Waveform Report</a>
            <a class="button" href="/reports/pwg_display_panel_spec.html" target="_blank">Display Panel Spec</a>
          </div>
        </section>

        <section>
          <h2>Waveform</h2>
          <div class="body">
            <iframe id="waveform-frame" src="/reports/pwg_lcr_comparison.html" title="PWG input and QSPICE output waveform"></iframe>
          </div>
        </section>
      </div>
    </div>
  </main>

  <script>
    const runButton = document.getElementById('run-button');
    const logBox = document.getElementById('log');

    runButton.addEventListener('click', async () => {{
      runButton.disabled = true;
      logBox.textContent = 'Running QSPICE and QUX export...';
      try {{
        const response = await fetch('/api/run-pwg-lcr', {{ method: 'POST' }});
        const payload = await response.json();
        if (!payload.ok) {{
          throw new Error(payload.error || 'Workflow failed');
        }}
        updateStatus(payload.status);
        document.getElementById('waveform-frame').src =
          '/reports/pwg_lcr_comparison.html?ts=' + Date.now();
        logBox.textContent =
          'PWG LCR workflow complete\\n' +
          'QSPICE exit code: ' + payload.qspiceExitCode + '\\n' +
          'CSV export exit code: ' + payload.csvExportExitCode;
      }} catch (error) {{
        logBox.textContent = String(error);
      }} finally {{
        runButton.disabled = false;
      }}
    }});

    function updateStatus(status) {{
      document.getElementById('workflow-state').textContent = 'Ready';
      document.getElementById('sample-count').textContent = status.sampleCount;
      document.getElementById('trace-count').textContent = status.traces.length;
      document.getElementById('qraw-state').textContent = status.qrawExists ? 'Yes' : 'No';
      document.getElementById('csv-state').textContent = status.csvExists ? 'Yes' : 'No';
      document.getElementById('time-range').textContent =
        formatNumber(status.timeStart) + ' s to ' + formatNumber(status.timeEnd) + ' s';
      const grid = document.getElementById('trace-grid');
      grid.innerHTML = status.traces.map((trace) => renderTrace(trace, status.stats[trace])).join('');
    }}

    function renderTrace(trace, stats) {{
      return `<div class="trace"><h3>${{escapeHtml(trace)}}</h3><dl>
        <dt>Min</dt><dd>${{formatNumber(stats.minimum)}}</dd>
        <dt>Max</dt><dd>${{formatNumber(stats.maximum)}}</dd>
        <dt>Avg</dt><dd>${{formatNumber(stats.average)}}</dd>
        <dt>RMS</dt><dd>${{formatNumber(stats.rms)}}</dd>
      </dl></div>`;
    }}

    function formatNumber(value) {{
      if (value === null || value === undefined) return '';
      return Number(value).toPrecision(7).replace(/\\.0+$/, '');
    }}

    function escapeHtml(value) {{
      return value.replace(/[&<>"']/g, (char) => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }}[char]));
    }}
  </script>
</body>
</html>
"""


def _render_trace_card(trace: str, values: dict) -> str:
    return f"""            <div class="trace">
              <h3>{trace}</h3>
              <dl>
                <dt>Min</dt><dd>{_format_number(values["minimum"])}</dd>
                <dt>Max</dt><dd>{_format_number(values["maximum"])}</dd>
                <dt>Avg</dt><dd>{_format_number(values["average"])}</dd>
                <dt>RMS</dt><dd>{_format_number(values["rms"])}</dd>
              </dl>
            </div>"""


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def main(argv: list[str]) -> int:
    port = int(argv[1]) if len(argv) > 1 else 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), QspiceAppHandler)
    print(f"QSPICE Engineering Calculator UI: http://127.0.0.1:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
