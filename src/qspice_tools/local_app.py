from __future__ import annotations

import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.qspice_tools.csv_reader import read_qspice_csv
from src.qspice_tools.pwg_generator import (
    PwgConfig,
    SUPPORTED_WAVEFORMS,
    generate_pwl,
    parse_arbitrary_points,
    write_pwl,
)
from src.qspice_tools.pwg_lcr_workflow import run_pwg_lcr_workflow
from src.qspice_tools.waveform_report import _format_number


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = PROJECT_ROOT / "qspice-cli-validation" / "examples" / "pwg-lcr"
REPORTS_DIR = PROJECT_ROOT / "reports"
CSV_PATH = CASE_DIR / "pwg_lcr.csv"
DEFAULT_CONFIG = PwgConfig.default()
CHANNEL_COUNT = 4


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
            payload = self._read_json()
            channels = _channels_from_payload(payload)
            active_index, config = _active_channel_config(channels, payload.get("activeChannel"))
            _write_channel_pwl_files(channels)
            result = run_pwg_lcr_workflow(
                case_dir=CASE_DIR,
                reports_dir=REPORTS_DIR,
                pwg_config=config,
                run_qspice=True,
            )
            status = build_status()
            status["config"] = _config_payload(config)
            status["channels"] = [_channel_payload(channel) for channel in channels]
            status["activeChannel"] = active_index + 1
            self._send_json(
                {
                    "ok": True,
                    "qspiceExitCode": result.qspice_exit_code,
                    "csvExportExitCode": result.csv_export_exit_code,
                    "config": _config_payload(config),
                    "channels": [_channel_payload(channel) for channel in channels],
                    "activeChannel": active_index + 1,
                    "status": status,
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

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)


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
        "config": _config_payload(DEFAULT_CONFIG),
        "channels": [_channel_payload(channel) for channel in _default_channels()],
        "activeChannel": 1,
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


def _default_channels() -> list[dict]:
    waveforms = ("Sinusoidal", "Square", "Triangle", "Arbitrary")
    phases = (0.0, 90.0, 180.0, 270.0)
    return [
        {
            "enabled": True,
            "config": PwgConfig(
                waveform=waveforms[index],
                amplitude_v=DEFAULT_CONFIG.amplitude_v,
                bias_v=DEFAULT_CONFIG.bias_v,
                frequency_hz=DEFAULT_CONFIG.frequency_hz,
                cycles=DEFAULT_CONFIG.cycles,
                samples_per_cycle=DEFAULT_CONFIG.samples_per_cycle,
                duty_percent=DEFAULT_CONFIG.duty_percent,
                triangle_symmetry_percent=DEFAULT_CONFIG.triangle_symmetry_percent,
                arbitrary_points=DEFAULT_CONFIG.arbitrary_points,
                phase_deg=phases[index],
                output_load_ohms=DEFAULT_CONFIG.output_load_ohms,
            ),
        }
        for index in range(CHANNEL_COUNT)
    ]


def _pwg_config_from_payload(payload: dict) -> PwgConfig:
    return PwgConfig(
        waveform=_waveform(payload.get("waveform")),
        amplitude_v=_positive_float(payload.get("amplitudeV"), "amplitudeV"),
        bias_v=_float(payload.get("biasV"), "biasV"),
        frequency_hz=_positive_float(payload.get("frequencyHz"), "frequencyHz"),
        cycles=DEFAULT_CONFIG.cycles,
        samples_per_cycle=DEFAULT_CONFIG.samples_per_cycle,
        duty_percent=_duty_percent(payload.get("dutyPercent")),
        triangle_symmetry_percent=_triangle_symmetry_percent(payload.get("triangleSymmetryPercent")),
        arbitrary_points=parse_arbitrary_points(payload.get("arbitraryPoints")),
        phase_deg=_float(payload.get("phaseDeg"), "phaseDeg"),
        output_load_ohms=_positive_float(payload.get("outputLoadOhms"), "outputLoadOhms"),
    )


def _channels_from_payload(payload: dict) -> list[dict]:
    raw_channels = payload.get("channels")
    if not raw_channels:
        return [{"enabled": True, "config": _pwg_config_from_payload(payload)}]

    channels = []
    for index, raw_channel in enumerate(raw_channels[:CHANNEL_COUNT]):
        channel_payload = dict(raw_channel or {})
        channel_payload.setdefault("waveform", DEFAULT_CONFIG.waveform)
        channel_payload.setdefault("amplitudeV", DEFAULT_CONFIG.amplitude_v)
        channel_payload.setdefault("biasV", DEFAULT_CONFIG.bias_v)
        channel_payload.setdefault("frequencyHz", DEFAULT_CONFIG.frequency_hz)
        channel_payload.setdefault("dutyPercent", DEFAULT_CONFIG.duty_percent)
        channel_payload.setdefault("triangleSymmetryPercent", DEFAULT_CONFIG.triangle_symmetry_percent)
        channel_payload.setdefault("arbitraryPoints", DEFAULT_CONFIG.arbitrary_points)
        channel_payload.setdefault("phaseDeg", DEFAULT_CONFIG.phase_deg)
        channel_payload.setdefault("outputLoadOhms", DEFAULT_CONFIG.output_load_ohms)
        channels.append(
            {
                "enabled": bool(channel_payload.get("enabled", True)),
                "config": _pwg_config_from_payload(channel_payload),
            }
        )
    return channels


def _active_channel_config(channels: list[dict], active_channel=None) -> tuple[int, PwgConfig]:
    if active_channel not in (None, ""):
        try:
            index = int(active_channel) - 1
        except (TypeError, ValueError) as exc:
            raise ValueError("activeChannel must be a channel number") from exc
        if index < 0 or index >= len(channels):
            raise ValueError("activeChannel is out of range")
        if not channels[index]["enabled"]:
            raise ValueError("Selected active channel must be enabled")
        return index, channels[index]["config"]

    for index, channel in enumerate(channels):
        if channel["enabled"]:
            return index, channel["config"]
    raise ValueError("At least one channel must be enabled")


def _write_channel_pwl_files(channels: list[dict]) -> None:
    for index, channel in enumerate(channels, start=1):
        if not channel["enabled"]:
            continue
        path = CASE_DIR / f"pwg_ch{index}.pwl"
        write_pwl(generate_pwl(channel["config"]), path)


def _float(value, name: str) -> float:
    if value is None or value == "":
        return getattr(DEFAULT_CONFIG, _payload_name_to_config_attr(name))
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc


def _positive_float(value, name: str) -> float:
    number = _float(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def _duty_percent(value) -> float:
    number = _float(value, "dutyPercent")
    if not 0.0 < number < 100.0:
        raise ValueError("dutyPercent must be greater than zero and less than 100")
    return number


def _triangle_symmetry_percent(value) -> float:
    number = _float(value, "triangleSymmetryPercent")
    if not 0.0 < number < 100.0:
        raise ValueError("triangleSymmetryPercent must be greater than zero and less than 100")
    return number


def _payload_name_to_config_attr(name: str) -> str:
    return {
        "amplitudeV": "amplitude_v",
        "biasV": "bias_v",
        "frequencyHz": "frequency_hz",
        "dutyPercent": "duty_percent",
        "triangleSymmetryPercent": "triangle_symmetry_percent",
        "phaseDeg": "phase_deg",
        "outputLoadOhms": "output_load_ohms",
    }[name]


def _waveform(value) -> str:
    if value in (None, ""):
        return DEFAULT_CONFIG.waveform
    if value not in SUPPORTED_WAVEFORMS:
        raise ValueError(f"waveform must be one of: {', '.join(SUPPORTED_WAVEFORMS)}")
    return str(value)


def _config_payload(config: PwgConfig) -> dict:
    return {
        "waveform": config.waveform,
        "amplitudeV": config.amplitude_v,
        "biasV": config.bias_v,
        "frequencyHz": config.frequency_hz,
        "cycles": config.cycles,
        "samplesPerCycle": config.samples_per_cycle,
        "dutyPercent": config.duty_percent,
        "triangleSymmetryPercent": config.triangle_symmetry_percent,
        "arbitraryPoints": _format_arbitrary_points(config.arbitrary_points),
        "phaseDeg": config.phase_deg,
        "outputLoadOhms": config.output_load_ohms,
    }


def _channel_payload(channel: dict) -> dict:
    payload = _config_payload(channel["config"])
    payload["enabled"] = channel["enabled"]
    return payload


def _format_arbitrary_points(points: tuple[float, ...]) -> str:
    return ",".join(_format_number(point) for point in points)


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
      --page: #d9f5f7;
      --panel: #e9ffff;
      --panel-strong: #d7f7fa;
      --ink: #102535;
      --muted: #4e6d75;
      --line: #8ab5bd;
      --dark: #202728;
      --grid: #7e999b;
      --green: #1fd35f;
      --cyan: #0aa6d8;
      --amber: #f2b705;
      --red: #df1f2f;
      --blue: #1a68b5;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--page);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }}
    main {{
      max-width: 1460px;
      margin: 0 auto;
      padding: 10px 12px 18px;
    }}
    .instrument {{
      border: 2px solid #28515b;
      background: var(--panel);
      box-shadow: 0 14px 34px rgba(29, 77, 87, 0.24);
    }}
    .topbar {{
      display: grid;
      grid-template-columns: 320px 1fr 260px;
      gap: 18px;
      padding: 16px 18px;
      border-bottom: 2px solid #28515b;
      background: linear-gradient(#f0ffff, #daf8fb);
    }}
    .brand h1 {{
      margin: 0;
      color: #0086d8;
      font-size: 48px;
      line-height: 0.9;
      letter-spacing: 0;
    }}
    .brand span {{
      color: #14528b;
      font-size: 20px;
      font-weight: 700;
    }}
    .brand p, .status-line, .path, .small {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }}
    .device-strip {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      align-content: center;
    }}
    .meter {{
      border: 1px solid var(--line);
      background: #f6ffff;
      padding: 9px;
      min-height: 58px;
    }}
    .meter span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
    }}
    .meter strong {{
      display: block;
      margin-top: 8px;
      font-size: 18px;
      font-variant-numeric: tabular-nums;
    }}
    .run-stack {{
      display: grid;
      gap: 9px;
      align-content: center;
    }}
    .run-stack label {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    .run-button, a.button {{
      border: 1px solid #0f4450;
      border-radius: 3px;
      color: #fff;
      text-align: center;
      text-decoration: none;
      letter-spacing: 0;
      font-weight: 700;
      cursor: pointer;
    }}
    .run-button {{
      width: 100%;
      background: #11866f;
      padding: 12px;
      font-size: 15px;
    }}
    .run-button:hover {{ background: #0d6f5c; }}
    .run-button:disabled {{ background: #8fa6a8; cursor: wait; }}
    .stop-button {{
      background: var(--red);
      padding: 9px;
      font-size: 13px;
    }}
    .panel-layout {{
      display: grid;
      grid-template-columns: minmax(440px, 1.25fr) minmax(420px, 1fr);
      gap: 12px;
      padding: 12px;
    }}
    .panel {{
      border: 1px solid var(--line);
      background: #efffff;
    }}
    .panel-title {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 9px 11px;
      border-bottom: 1px solid var(--line);
      background: var(--panel-strong);
      font-size: 14px;
      font-weight: 700;
    }}
    .panel-body {{ padding: 12px; }}
    .scope {{
      background: #1e2323;
      border: 2px solid #566869;
      min-height: 360px;
      position: relative;
    }}
    .scope::before {{
      content: "";
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(to right, rgba(170, 220, 220, 0.55) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(170, 220, 220, 0.55) 1px, transparent 1px),
        linear-gradient(to right, rgba(170, 220, 220, 0.18) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(170, 220, 220, 0.18) 1px, transparent 1px);
      background-size: 10% 20%, 10% 20%, 2% 4%, 2% 4%;
    }}
    #preview-canvas {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
    }}
    .scope-readout {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-top: 10px;
    }}
    .readout-cell {{
      border: 1px solid var(--line);
      background: #f8ffff;
      padding: 8px;
      font-size: 12px;
    }}
    .readout-cell strong {{
      display: block;
      margin-top: 5px;
      font-size: 15px;
      font-variant-numeric: tabular-nums;
    }}
    .channel-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .channel {{
      border: 1px solid var(--line);
      border-left: 5px solid var(--cyan);
      padding: 9px;
      background: #fbfcfe;
    }}
    .channel[data-channel="2"] {{ border-left-color: var(--green); }}
    .channel[data-channel="3"] {{ border-left-color: var(--amber); }}
    .channel[data-channel="4"] {{ border-left-color: var(--red); }}
    .channel-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-size: 13px;
      font-weight: 700;
    }}
    .channel-head label {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 700;
    }}
    .channel-head input {{
      width: auto;
      padding: 0;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}
    label {{
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    input {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 2px;
      padding: 7px 8px;
      color: var(--ink);
      font-size: 13px;
      font-variant-numeric: tabular-nums;
      background: #f7ffff;
    }}
    textarea {{
      width: 100%;
      min-height: 44px;
      border: 1px solid var(--line);
      border-radius: 2px;
      padding: 7px 8px;
      color: var(--ink);
      font-size: 12px;
      font-family: Arial, Helvetica, sans-serif;
      background: #f7ffff;
      resize: vertical;
    }}
    select {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 2px;
      padding: 7px 8px;
      color: var(--ink);
      font-size: 13px;
      background: #f7ffff;
    }}
    .full-row {{
      grid-column: 1 / -1;
    }}
    .bottom-layout {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      padding: 0 12px 12px;
    }}
    .trace-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }}
    .trace {{
      border: 1px solid var(--line);
      background: #f8ffff;
      padding: 9px;
    }}
    .trace h3 {{
      margin: 0 0 8px;
      font-size: 14px;
    }}
    dl {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      margin: 0;
      font-size: 12px;
    }}
    dt {{
      color: var(--muted);
    }}
    dd {{
      margin: 0;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    .links {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }}
    a.button {{
      background: var(--blue);
      padding: 9px;
      font-size: 13px;
    }}
    pre {{
      margin: 0;
      background: #f7ffff;
      border: 1px solid var(--line);
      color: #e5edf7;
      color: var(--ink);
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
      height: 360px;
      border: 1px solid var(--line);
      background: #fff;
    }}
    @media (max-width: 940px) {{
      .panel-layout, .bottom-layout {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 860px) {{
      .topbar {{ grid-template-columns: 1fr; }}
      .brand h1 {{ font-size: 38px; }}
    }}
    @media (max-width: 720px) {{
      .channel-grid, .form-grid, .scope-readout, .trace-grid, .links, .device-strip {{
        grid-template-columns: 1fr;
      }}
      .scope {{ min-height: 320px; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="instrument">
      <div class="topbar">
        <div class="brand">
          <h1>QGEN</h1>
          <span>QSPICE Function Generator</span>
          <p>4-channel arbitrary source control with local and remote QSPICE execution.</p>
        </div>
        <div class="device-strip">
          <div class="meter"><span>Workflow</span><strong id="workflow-state">{workflow_state}</strong></div>
          <div class="meter"><span>Samples</span><strong id="sample-count">{sample_count}</strong></div>
          <div class="meter"><span>QRAW</span><strong id="qraw-state">{_yes_no(status["qrawExists"])}</strong></div>
          <div class="meter"><span>CSV</span><strong id="csv-state">{_yes_no(status["csvExists"])}</strong></div>
        </div>
        <div class="run-stack">
            <button class="run-button" id="run-button">Run Active Channel</button>
          <label>QSPICE Source CH
            <select id="active-channel">
{_render_active_channel_options()}
            </select>
          </label>
          <a class="button stop-button" href="/">Reset Panel</a>
          <div class="status-line">Selected source channel drives the QSPICE PWL input.</div>
        </div>
      </div>

      <div class="panel-layout">
        <section class="panel">
          <div class="panel-title">
            <span>Oscilloscope Preview</span>
            <span>Time: <span id="time-range">{time_range}</span></span>
          </div>
          <div class="panel-body">
            <div class="scope"><canvas id="preview-canvas"></canvas></div>
            <div class="scope-readout">
              <div class="readout-cell">Trace Count<strong id="trace-count">{len(status["traces"])}</strong></div>
              <div class="readout-cell">CH0 Frequency<strong id="freq-readout">10 kHz</strong></div>
              <div class="readout-cell">CH0 Vpp<strong id="vpp-readout">24 V</strong></div>
              <div class="readout-cell">Mode<strong>Simulation</strong></div>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-title">
            <span>Function Generator Channels</span>
            <span>AO 0 / AO 1 / AO 2 / AO 3</span>
          </div>
          <div class="panel-body">
            <div class="channel-grid" id="channel-grid">
{_render_channel_controls()}
            </div>
          </div>
        </section>
      </div>

      <div class="bottom-layout">
        <section class="panel">
          <div class="panel-title"><span>QSPICE Trace Summary</span><span>Generated Results</span></div>
          <div class="panel-body trace-grid" id="trace-grid">
{cards}
          </div>
        </section>

        <section class="panel">
          <div class="panel-title"><span>Run Log and Reports</span><span>Local Case</span></div>
          <div class="panel-body">
            <pre id="log">Ready.</pre>
            <p class="path">Circuit: {CASE_DIR / "pwg_lcr.cir"}</p>
            <p class="path">CSV: {CSV_PATH}</p>
            <div class="links">
            <a class="button" href="/reports/pwg_lcr_comparison.html" target="_blank">Input Output Comparison</a>
            <a class="button" href="/reports/pwg_lcr_report.html" target="_blank">Waveform Report</a>
            <a class="button" href="/reports/pwg_display_panel_spec.html" target="_blank">Display Panel Spec</a>
            </div>
          </div>
        </section>
      </div>

      <section class="panel" style="margin: 0 12px 12px;">
          <div class="panel-title"><span>QSPICE Waveform Report</span><span>Browser Preview</span></div>
          <div class="panel-body">
            <iframe id="waveform-frame" src="/reports/pwg_lcr_comparison.html" title="PWG input and QSPICE output waveform"></iframe>
          </div>
      </section>
    </div>
  </main>

  <script>
    const runButton = document.getElementById('run-button');
    const logBox = document.getElementById('log');
    const canvas = document.getElementById('preview-canvas');
    const context = canvas.getContext('2d');
    const traceColors = ['#21d4ff', '#39ff72', '#ffd43b', '#ff4d5f'];

    runButton.addEventListener('click', async () => {{
      runButton.disabled = true;
      logBox.textContent = 'Running QSPICE and QUX export...';
      try {{
        const config = readConfig();
        const response = await fetch('/api/run-pwg-lcr', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(config)
        }});
        const payload = await response.json();
        if (!payload.ok) {{
          throw new Error(payload.error || 'Workflow failed');
        }}
        updateStatus(payload.status);
        document.getElementById('waveform-frame').src =
          '/reports/pwg_lcr_comparison.html?ts=' + Date.now();
        logBox.textContent =
          'PWG LCR workflow complete\\n' +
          'Active channel: CH' + payload.activeChannel + '\\n' +
          'Waveform: ' + payload.config.waveform + '\\n' +
          'Amplitude Vp: ' + payload.config.amplitudeV + ' V\\n' +
          'Bias: ' + payload.config.biasV + ' V\\n' +
          'Frequency: ' + payload.config.frequencyHz + ' Hz\\n' +
          'Phase: ' + payload.config.phaseDeg + ' deg\\n' +
          'Load: ' + payload.config.outputLoadOhms + ' ohm\\n' +
          'Duty: ' + payload.config.dutyPercent + ' %\\n' +
          'Triangle symmetry: ' + payload.config.triangleSymmetryPercent + ' %\\n' +
          'AWG points: ' + payload.config.arbitraryPoints + '\\n' +
          'QSPICE exit code: ' + payload.qspiceExitCode + '\\n' +
          'CSV export exit code: ' + payload.csvExportExitCode;
      }} catch (error) {{
        logBox.textContent = String(error);
      }} finally {{
        runButton.disabled = false;
        drawPreview();
      }}
    }});

    document.querySelectorAll('.channel input, .channel select, .channel textarea').forEach((control) => {{
      control.addEventListener('input', drawPreview);
      control.addEventListener('change', drawPreview);
    }});
    window.addEventListener('resize', drawPreview);

    function readConfig() {{
      return {{
        activeChannel: Number(document.getElementById('active-channel').value),
        channels: Array.from(document.querySelectorAll('.channel')).map((channel) => ({{
          enabled: channel.querySelector('.channel-enabled').checked,
          waveform: channel.querySelector('.channel-waveform').value,
          amplitudeV: Number(channel.querySelector('.channel-amplitude').value),
          biasV: Number(channel.querySelector('.channel-bias').value),
          frequencyHz: Number(channel.querySelector('.channel-frequency').value),
          phaseDeg: Number(channel.querySelector('.channel-phase').value),
          outputLoadOhms: Number(channel.querySelector('.channel-load').value),
          dutyPercent: Number(channel.querySelector('.channel-duty').value),
          triangleSymmetryPercent: Number(channel.querySelector('.channel-triangle-symmetry').value),
          arbitraryPoints: channel.querySelector('.channel-awg').value
        }}))
      }};
    }}

    function updateStatus(status) {{
      document.getElementById('workflow-state').textContent = 'Ready';
      document.getElementById('sample-count').textContent = status.sampleCount;
      document.getElementById('trace-count').textContent = status.traces.length;
      document.getElementById('qraw-state').textContent = status.qrawExists ? 'Yes' : 'No';
      document.getElementById('csv-state').textContent = status.csvExists ? 'Yes' : 'No';
      document.getElementById('time-range').textContent =
        formatNumber(status.timeStart) + ' s to ' + formatNumber(status.timeEnd) + ' s';
      const firstEnabled = status.channels.find((channel) => channel.enabled) || status.channels[0];
      if (firstEnabled) {{
        document.getElementById('freq-readout').textContent = formatEngineering(firstEnabled.frequencyHz) + 'Hz';
        document.getElementById('vpp-readout').textContent = formatNumber(firstEnabled.amplitudeV * 2) + ' V';
      }}
      document.getElementById('active-channel').value = String(status.activeChannel || 1);
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

    function formatEngineering(value) {{
      const number = Number(value);
      if (number >= 1000) return formatNumber(number / 1000) + ' k';
      return formatNumber(number) + ' ';
    }}

    function escapeHtml(value) {{
      return value.replace(/[&<>"']/g, (char) => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }}[char]));
    }}

    function drawPreview() {{
      const rect = canvas.getBoundingClientRect();
      const scale = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * scale));
      canvas.height = Math.max(1, Math.floor(rect.height * scale));
      context.setTransform(scale, 0, 0, scale, 0, 0);
      context.clearRect(0, 0, rect.width, rect.height);
      const channels = readConfig().channels;
      const enabled = channels.filter((channel) => channel.enabled);
      const maxAmplitude = Math.max(1, ...enabled.map((channel) => Math.abs(channel.amplitudeV) + Math.abs(channel.biasV)));
      channels.forEach((channel, index) => {{
        if (!channel.enabled) return;
        drawWave(channel, index, rect.width, rect.height, maxAmplitude);
      }});
    }}

    function drawWave(channel, index, width, height, maxAmplitude) {{
      const yCenter = height * (0.2 + index * 0.2);
      const yScale = height * 0.075 / maxAmplitude;
      context.beginPath();
      context.lineWidth = 2;
      context.strokeStyle = traceColors[index % traceColors.length];
      for (let pixel = 0; pixel <= width; pixel += 2) {{
        const phase = normalizedPhase(pixel / width * 3 + channel.phaseDeg / 360);
        const unit = waveformUnit(
          channel.waveform,
          phase,
          channel.dutyPercent,
          channel.triangleSymmetryPercent,
          channel.arbitraryPoints
        );
        const y = yCenter - (channel.biasV + channel.amplitudeV * unit) * yScale;
        if (pixel === 0) context.moveTo(pixel, y);
        else context.lineTo(pixel, y);
      }}
      context.stroke();
      context.fillStyle = traceColors[index % traceColors.length];
      context.font = '12px Arial';
      const dutyLabel = channel.waveform === 'Square' ? ' ' + channel.dutyPercent + '%' : '';
      const symmetryLabel = channel.waveform === 'Triangle' ? ' ' + channel.triangleSymmetryPercent + '%' : '';
      context.fillText(
        'CH' + (index + 1) + ' ' + channel.waveform + dutyLabel + symmetryLabel + ' ' + channel.phaseDeg + 'deg',
        10,
        yCenter - 22
      );
    }}

    function normalizedPhase(value) {{
      return ((value % 1) + 1) % 1;
    }}

    function waveformUnit(waveform, phase, dutyPercent, triangleSymmetryPercent, arbitraryPoints) {{
      if (waveform === 'Square') return phase < dutyPercent / 100 ? 1 : -1;
      if (waveform === 'Triangle') {{
        return triangleUnit(phase, triangleSymmetryPercent);
      }}
      if (waveform === 'Arbitrary') return arbitraryUnit(phase, arbitraryPoints);
      return Math.sin(2 * Math.PI * phase);
    }}

    function triangleUnit(phase, symmetryPercent) {{
      const peakPhase = symmetryPercent / 200;
      const negativePeakPhase = 0.5 + peakPhase;
      if (phase < peakPhase) return phase / peakPhase;
      if (phase < 0.5) return 1 - (phase - peakPhase) / (0.5 - peakPhase);
      if (phase < negativePeakPhase) return -(phase - 0.5) / peakPhase;
      return -1 + (phase - negativePeakPhase) / (0.5 - peakPhase);
    }}

    function arbitraryUnit(phase, rawPoints) {{
      const points = parseArbitraryPoints(rawPoints);
      if (points.length < 2) return 0;
      const position = phase * (points.length - 1);
      const leftIndex = Math.min(Math.floor(position), points.length - 2);
      const fraction = position - leftIndex;
      return points[leftIndex] + (points[leftIndex + 1] - points[leftIndex]) * fraction;
    }}

    function parseArbitraryPoints(rawPoints) {{
      const parts = String(rawPoints)
        .replace(/[,;]/g, ' ')
        .split(/\\s+/)
        .filter(Boolean)
        .map((value) => Math.max(-1, Math.min(1, Number(value))));
      return parts.filter((value) => Number.isFinite(value));
    }}

    drawPreview();
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


def _render_waveform_options(selected: str) -> str:
    return "\n".join(
        f'                  <option value="{waveform}"{" selected" if waveform == selected else ""}>{waveform}</option>'
        for waveform in SUPPORTED_WAVEFORMS
    )


def _render_channel_controls() -> str:
    return "\n".join(
        _render_channel_control(index, channel)
        for index, channel in enumerate(_default_channels(), start=1)
    )


def _render_active_channel_options() -> str:
    return "\n".join(
        f'              <option value="{index}"{" selected" if index == 1 else ""}>CH{index}</option>'
        for index in range(1, CHANNEL_COUNT + 1)
    )


def _render_channel_control(index: int, channel: dict) -> str:
    config = channel["config"]
    checked = " checked" if channel["enabled"] else ""
    return f"""              <div class="channel" data-channel="{index}">
                <div class="channel-head">
                  <span>CH{index}</span>
                  <label><input class="channel-enabled" type="checkbox"{checked}> Enabled</label>
                </div>
                <div class="form-grid">
                  <label>Waveform
                    <select class="channel-waveform">
{_render_waveform_options(config.waveform)}
                    </select>
                  </label>
                  <label>Amplitude Vp
                    <input class="channel-amplitude" type="number" min="0.1" step="0.1" value="{config.amplitude_v}">
                  </label>
                  <label>Bias Voltage
                    <input class="channel-bias" type="number" step="0.1" value="{config.bias_v}">
                  </label>
                  <label>Frequency Hz
                    <input class="channel-frequency" type="number" min="1" step="100" value="{config.frequency_hz}">
                  </label>
                  <label>Phase deg
                    <input class="channel-phase" type="number" step="1" value="{config.phase_deg}">
                  </label>
                  <label>Load Ohm
                    <input class="channel-load" type="number" min="1" step="1" value="{config.output_load_ohms}">
                  </label>
                  <label>Duty % (Square)
                    <input class="channel-duty" type="number" min="1" max="99" step="1" value="{config.duty_percent}">
                  </label>
                  <label>Symmetry % (Triangle)
                    <input class="channel-triangle-symmetry" type="number" min="1" max="99" step="1" value="{config.triangle_symmetry_percent}">
                  </label>
                  <label class="full-row">AWG Points (-1..1)
                    <textarea class="channel-awg" rows="2">{_format_arbitrary_points(config.arbitrary_points)}</textarea>
                  </label>
                </div>
              </div>"""


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def main(argv: list[str]) -> int:
    host, port = _parse_host_port(argv)
    server = ThreadingHTTPServer((host, port), QspiceAppHandler)
    print(f"QSPICE Engineering Calculator UI: http://{host}:{port}")
    server.serve_forever()
    return 0


def _parse_host_port(argv: list[str]) -> tuple[str, int]:
    host = "127.0.0.1"
    port = 8765
    if len(argv) == 2:
        port = int(argv[1])
    elif len(argv) > 2:
        host = argv[1]
        port = int(argv[2])
    return host, port


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
