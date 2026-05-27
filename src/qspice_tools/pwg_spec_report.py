from __future__ import annotations

import sys
from pathlib import Path


def generate_pwg_spec_report(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_pwg_spec_report(), encoding="utf-8")


def render_pwg_spec_report() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PWG Display Panel Specification</title>
  <style>
    :root {
      --page: #f7f9fc;
      --panel: #ffffff;
      --ink: #111827;
      --blue: #0037ff;
      --qblue: #0070c9;
      --pink: #ff74d4;
      --line: #d7e0ee;
      --muted: #667085;
      --red: #e10000;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--page);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }
    header {
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 18px 28px;
      text-align: center;
      position: relative;
    }
    .back-link {
      position: absolute;
      left: 22px;
      top: 18px;
      color: #ffffff;
      background: #0f766e;
      border-radius: 7px;
      padding: 8px 11px;
      text-decoration: none;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 13px;
      font-weight: 700;
    }
    h1 {
      color: var(--blue);
      font-family: Georgia, "Times New Roman", serif;
      font-size: 36px;
      line-height: 1.15;
      letter-spacing: 0;
      margin: 0;
      font-weight: 500;
    }
    main {
      max-width: 1240px;
      margin: 0 auto;
      padding: 22px;
    }
    .system {
      display: grid;
      grid-template-columns: 300px 112px minmax(440px, 1fr);
      gap: 16px;
      align-items: center;
      margin-bottom: 18px;
    }
    .box {
      background: var(--panel);
      border: 3px solid #111111;
      border-radius: 8px;
      padding: 14px;
      min-height: 450px;
    }
    .caption {
      color: var(--blue);
      font-size: 13px;
      text-align: center;
      margin-bottom: 8px;
    }
    .version {
      color: var(--pink);
      font-size: 13px;
      margin-bottom: 22px;
    }
    .pwg-title {
      color: var(--blue);
      font-size: 18px;
      line-height: 1.1;
      margin: 0 0 10px;
      text-align: center;
    }
    .device {
      display: flex;
      justify-content: center;
      margin: 4px 0 6px;
    }
    .display-label {
      color: var(--blue);
      text-align: center;
      font-size: 17px;
      margin: 4px 0;
    }
    .display-panel {
      border: 2px solid #1976d2;
      height: 146px;
      margin-top: 4px;
      background: #ffffff;
    }
    .cli {
      color: var(--blue);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      font-weight: 700;
    }
    .qspice-title {
      color: var(--qblue);
      font-size: 34px;
      text-align: center;
      margin-bottom: 8px;
    }
    .circuit {
      border: 2px solid #9bb9ef;
      padding: 8px;
      margin-bottom: 12px;
    }
    .tables {
      display: grid;
      grid-template-columns: 1.15fr .85fr;
      gap: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 13px;
      background: #ffffff;
    }
    caption {
      caption-side: top;
      color: #b00000;
      font-size: 11px;
      font-weight: 700;
      margin-bottom: 2px;
      text-align: left;
    }
    th, td {
      border: 1px solid #222222;
      padding: 4px 6px;
    }
    th {
      font-weight: 500;
      text-align: center;
      background: #fbfbfb;
    }
    .checklist {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
      margin-top: 18px;
    }
    .spec-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .spec-card h2 {
      margin: 0 0 10px;
      font-size: 17px;
      letter-spacing: 0;
    }
    ul {
      margin: 0;
      padding-left: 18px;
      color: #344054;
      line-height: 1.55;
      font-size: 14px;
    }
    code {
      background: #eef2f7;
      border-radius: 4px;
      padding: 1px 5px;
    }
    @media (max-width: 900px) {
      .system, .checklist, .tables {
        grid-template-columns: 1fr;
      }
      h1 { font-size: 28px; }
      .box { min-height: auto; }
      .back-link {
        position: static;
        display: inline-block;
        margin-bottom: 12px;
      }
    }
  </style>
</head>
<body>
  <header>
    <a class="back-link" href="/">Back to App</a>
    <h1>A Simulation Example for Testing of Open-CtrLab &amp; Qspice [2024-05-13]</h1>
  </header>
  <main>
    <div class="system">
      <section>
        <div class="caption">Man-Machine Interface and Optimization</div>
        <div class="box">
          <div class="version">Open-CtrLab V0.1</div>
          <h2 class="pwg-title">Programmable Waveform Generator (PWG)</h2>
          <div class="device">
            <svg width="180" height="140" viewBox="0 0 180 140" role="img" aria-label="PWG instrument">
              <rect x="14" y="12" width="150" height="108" rx="8" fill="none" stroke="#111" stroke-width="5"/>
              <rect x="32" y="28" width="72" height="42" fill="none" stroke="#111" stroke-width="5"/>
              <polyline points="38,50 48,50 54,36 64,64 74,36 84,64 94,50 102,50" fill="none" stroke="#111" stroke-width="5"/>
              <circle cx="134" cy="35" r="14" fill="none" stroke="#111" stroke-width="5"/>
              <circle cx="35" cy="92" r="8" fill="none" stroke="#111" stroke-width="5"/>
              <circle cx="60" cy="92" r="8" fill="none" stroke="#111" stroke-width="5"/>
              <rect x="82" y="84" width="22" height="16" fill="none" stroke="#111" stroke-width="5"/>
              <g stroke="#111" stroke-width="4">
                <line x1="119" y1="64" x2="128" y2="64"/><line x1="138" y1="64" x2="147" y2="64"/>
                <line x1="119" y1="78" x2="128" y2="78"/><line x1="138" y1="78" x2="147" y2="78"/>
                <line x1="119" y1="92" x2="128" y2="92"/><line x1="138" y1="92" x2="147" y2="92"/>
              </g>
              <path d="M50 120 v12 h78 v-12" fill="none" stroke="#111" stroke-width="5"/>
            </svg>
          </div>
          <div class="display-label">Display Panel</div>
          <div class="display-panel">
            <svg viewBox="0 0 260 140" width="100%" height="100%" role="img" aria-label="Display Panel showing vs and vo">
              <line x1="28" y1="102" x2="235" y2="102" stroke="#111" stroke-width="2"/>
              <line x1="28" y1="34" x2="235" y2="34" stroke="#111" stroke-width="2"/>
              <line x1="28" y1="14" x2="28" y2="62" stroke="#111" stroke-width="2"/>
              <line x1="28" y1="82" x2="28" y2="128" stroke="#111" stroke-width="2"/>
              <polygon points="235,34 228,30 228,38" fill="#111"/>
              <polygon points="235,102 228,98 228,106" fill="#111"/>
              <polygon points="28,14 24,22 32,22" fill="#111"/>
              <polygon points="28,82 24,90 32,90" fill="#111"/>
              <text x="7" y="22" font-size="14">v<tspan baseline-shift="sub">s</tspan></text>
              <text x="7" y="92" font-size="14">v<tspan baseline-shift="sub">o</tspan></text>
              <path d="M28 34 C52 0 78 0 104 34 S156 68 182 34 S218 0 235 26" fill="none" stroke="#0037ff" stroke-width="2.5"/>
            </svg>
          </div>
        </div>
      </section>

      <div class="cli">
        <svg width="112" height="70" viewBox="0 0 112 70" role="img" aria-label="CLI bidirectional link">
          <path d="M6 35 L34 12 V27 H78 V12 L106 35 L78 58 V43 H34 V58 Z" fill="#eef4ff" stroke="#0037ff" stroke-width="3"/>
          <text x="56" y="42" text-anchor="middle" font-size="21" fill="#0037ff" font-weight="700">CLI</text>
        </svg>
      </div>

      <section>
        <div class="caption">Digital Power Electronics Simulation</div>
        <div class="box">
          <div class="qspice-title">Qspice</div>
          <div class="circuit">
            <svg viewBox="0 0 620 200" width="100%" height="185" role="img" aria-label="Qspice LCR circuit">
              <defs>
                <marker id="arrow-red" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                  <path d="M0,0 L8,4 L0,8 Z" fill="#d00000"/>
                </marker>
                <marker id="arrow-blue" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                  <path d="M0,0 L8,4 L0,8 Z" fill="#0057d8"/>
                </marker>
                <g id="resistor-horizontal">
                  <polyline points="0,0 8,-12 20,12 32,-12 44,12 56,-12 68,12 80,0" fill="none" stroke="#111" stroke-width="3" stroke-linejoin="round"/>
                </g>
                <g id="resistor-vertical">
                  <polyline points="0,0 -12,8 12,20 -12,32 12,44 -12,56 12,68 0,80" fill="none" stroke="#111" stroke-width="3" stroke-linejoin="round"/>
                </g>
                <g id="inductor">
                  <path d="M0 0 H10 C10 -18 30 -18 30 0 C30 -18 50 -18 50 0 C50 -18 70 -18 70 0 C70 -18 90 -18 90 0 H100" fill="none" stroke="#111" stroke-width="3" stroke-linecap="round"/>
                </g>
              </defs>

              <rect x="14" y="8" width="592" height="174" rx="4" fill="#fff" stroke="#9bb9ef" stroke-width="2"/>

              <line x1="70" y1="145" x2="555" y2="145" stroke="#111" stroke-width="3"/>
              <line x1="70" y1="72" x2="112" y2="72" stroke="#111" stroke-width="3"/>

              <circle cx="70" cy="108" r="25" fill="#f8fff8" stroke="#111" stroke-width="3"/>
              <path d="M52 108 C58 92 66 92 72 108 S86 124 92 108" fill="none" stroke="#0a9b3f" stroke-width="3" stroke-linecap="round"/>
              <line x1="70" y1="72" x2="70" y2="83" stroke="#111" stroke-width="3"/>
              <line x1="70" y1="133" x2="70" y2="145" stroke="#111" stroke-width="3"/>
              <text x="45" y="66" font-size="18" font-weight="700">+</text>
              <text x="47" y="134" font-size="18" font-weight="700">-</text>
              <text x="31" y="111" font-size="17">v<tspan baseline-shift="sub">s</tspan></text>

              <use href="#inductor" x="112" y="72"/>
              <text x="152" y="45" font-size="18">L</text>
              <text x="122" y="104" font-size="13" fill="#475467">100 uH</text>

              <line x1="212" y1="72" x2="232" y2="72" stroke="#111" stroke-width="3"/>
              <use href="#resistor-horizontal" x="232" y="72"/>
              <text x="256" y="45" font-size="16">r<tspan baseline-shift="sub">L</tspan></text>
              <text x="238" y="104" font-size="13" fill="#475467">100 mΩ</text>
              <line x1="312" y1="72" x2="366" y2="72" stroke="#111" stroke-width="3"/>

              <circle cx="366" cy="72" r="4" fill="#111"/>
              <line x1="366" y1="72" x2="366" y2="145" stroke="#111" stroke-width="3"/>
              <line x1="337" y1="101" x2="395" y2="101" stroke="#111" stroke-width="3"/>
              <line x1="337" y1="116" x2="395" y2="116" stroke="#111" stroke-width="3"/>
              <text x="402" y="111" font-size="18">C<tspan baseline-shift="sub">out</tspan></text>
              <text x="398" y="132" font-size="13" fill="#475467">2.4 uF</text>

              <line x1="366" y1="72" x2="434" y2="72" stroke="#111" stroke-width="3"/>
              <use href="#resistor-horizontal" x="434" y="72"/>
              <text x="458" y="45" font-size="16">r<tspan baseline-shift="sub">C</tspan></text>
              <text x="440" y="104" font-size="13" fill="#475467">25 mΩ</text>

              <line x1="514" y1="72" x2="548" y2="72" stroke="#111" stroke-width="3"/>
              <circle cx="548" cy="72" r="4" fill="#111"/>
              <line x1="548" y1="72" x2="548" y2="82" stroke="#111" stroke-width="3"/>
              <use href="#resistor-vertical" x="548" y="82"/>
              <line x1="548" y1="162" x2="548" y2="145" stroke="#111" stroke-width="3"/>
              <text x="568" y="123" font-size="18">R<tspan baseline-shift="sub">o</tspan></text>
              <text x="568" y="141" font-size="13" fill="#475467">1.25 Ω</text>

              <line x1="506" y1="72" x2="506" y2="86" stroke="#111" stroke-width="3"/>
              <use href="#resistor-vertical" x="506" y="86"/>
              <line x1="506" y1="166" x2="506" y2="145" stroke="#111" stroke-width="3"/>
              <text x="463" y="133" font-size="17">R<tspan baseline-shift="sub">dy</tspan></text>
              <text x="460" y="151" font-size="13" fill="#475467">1 kΩ</text>

              <line x1="300" y1="52" x2="356" y2="52" stroke="#d00000" stroke-width="2.4" marker-end="url(#arrow-red)"/>
              <text x="317" y="44" fill="#d00000" font-size="13">i<tspan baseline-shift="sub">L</tspan></text>
              <line x1="366" y1="132" x2="366" y2="88" stroke="#0057d8" stroke-width="2.4" marker-end="url(#arrow-blue)"/>
              <text x="373" y="97" fill="#0057d8" font-size="13">v<tspan baseline-shift="sub">o</tspan></text>
              <line x1="548" y1="90" x2="548" y2="132" stroke="#d00000" stroke-width="2.4" marker-end="url(#arrow-red)"/>
              <text x="555" y="106" fill="#d00000" font-size="13">i<tspan baseline-shift="sub">o</tspan></text>

              <text x="74" y="33" font-size="13" fill="#475467">PWG source</text>
              <text x="201" y="33" font-size="13" fill="#475467">series L + ESR</text>
              <text x="370" y="33" font-size="13" fill="#475467">output filter and load</text>
            </svg>
          </div>
          <div class="tables">
            <table>
              <caption>Table 1 Parameters of the LCR Simulation Example</caption>
              <thead><tr><th colspan="2">LCR Circuit Parameters</th></tr></thead>
              <tbody>
                <tr><td>Inductor</td><td>L = 100 uH</td></tr>
                <tr><td>Inductor ESR</td><td>r<sub>L</sub> = 100 mΩ</td></tr>
                <tr><td>Output Capacitor</td><td>C<sub>out</sub> = 2.4 uF</td></tr>
                <tr><td>Capacitor ESR</td><td>r<sub>C</sub> = 25 mΩ</td></tr>
                <tr><td>Load Dummy Resistance</td><td>R<sub>dy</sub> = 1 kΩ</td></tr>
                <tr><td>Load Resistance</td><td>R<sub>o</sub> = 1.25 Ω</td></tr>
              </tbody>
            </table>
            <table>
              <caption>Table 2 Parameters of the PWG</caption>
              <thead><tr><th colspan="2">Input Voltage Source</th></tr></thead>
              <tbody>
                <tr><td>Waveform</td><td>Sinusoidal</td></tr>
                <tr><td>Amplitude</td><td>V<sub>p</sub> = 12 V</td></tr>
                <tr><td>Bias Voltage</td><td>V<sub>bias</sub> = 0 V</td></tr>
                <tr><td>Frequency</td><td>10k Hz</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>

    <div class="checklist">
      <section class="spec-card">
        <h2>PWG Functional Requirements</h2>
        <ul>
          <li>Generate a sinusoidal input voltage source for QSPICE.</li>
          <li>Expose waveform, amplitude, bias voltage, and frequency as editable parameters.</li>
          <li>Default parameters must match the diagram: <code>Sinusoidal</code>, <code>12 V</code>, <code>0 V</code>, <code>10k Hz</code>.</li>
          <li>Export the waveform to QSPICE through CLI-compatible files such as PWL or generated netlist input.</li>
        </ul>
      </section>
      <section class="spec-card">
        <h2>Display Panel Requirements</h2>
        <ul>
          <li>Show the input waveform <code>v_s</code> as a blue sinusoidal trace.</li>
          <li>Reserve an output waveform lane for <code>v_o</code> returned from QSPICE CSV export.</li>
          <li>Support PC1 local preview and PC1-to-PC2 CLI simulation workflow.</li>
          <li>Report QSPICE output traces after CSV import and compare them with the PWG input.</li>
        </ul>
      </section>
    </div>
  </main>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python -m src.qspice_tools.pwg_spec_report <output.html>")
        return 2

    generate_pwg_spec_report(Path(argv[1]))
    print(f"wrote {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
