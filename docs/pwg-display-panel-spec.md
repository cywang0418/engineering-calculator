# PWG Display Panel Specification

Reference: `【20260513】Testing of Open-CtrLab & Qspice.png`

## Target Architecture

The software PWG must match the reference diagram workflow:

```text
PC1 / Open-CtrLab V0.1 PWG + Display Panel
  <-> CLI
PC2 / Qspice Digital Power Electronics Simulation
```

A same-PC combined layout is also acceptable for early development, as long as the software boundaries remain the same: PWG input generation, CLI handoff, QSPICE simulation, CSV result import, and display-panel comparison.

## PWG Requirements

- Product label: `Open-CtrLab V0.1`.
- Module name: `Programmable Waveform Generator (PWG)`.
- Domain label: `Man-Machine Interface and Optimization`.
- Output target: QSPICE input voltage source.
- CLI integration: bidirectional handoff between PWG and QSPICE workflow.

## Default PWG Parameters

| Parameter | Required value |
|---|---:|
| Waveform | Sinusoidal |
| Amplitude | Vp = 12 V |
| Bias Voltage | Vbias = 0 V |
| Frequency | 10k Hz |

## Display Panel Requirements

- Show `v_s` as the PWG input waveform.
- Reserve a second lane for `v_o`, the output returned from QSPICE simulation.
- Use a waveform-style display panel, not only numeric fields.
- Support future comparison of `v_s` and `v_o` after CSV import.

## QSPICE Reference Circuit Requirements

The reference QSPICE example is an LCR circuit for digital power electronics simulation.

| LCR parameter | Required value |
|---|---:|
| Inductor | L = 100 uH |
| Inductor ESR | rL = 100 mΩ |
| Output Capacitor | Cout = 2.4 uF |
| Capacitor ESR | rC = 25 mΩ |
| Load Dummy Resistance | Rdy = 1 kΩ |
| Load Resistance | Ro = 1.25 Ω |

## Compliance Check

- [x] PWG name and Open-CtrLab label captured.
- [x] Display Panel includes `v_s` and `v_o` lanes.
- [x] CLI handoff between PWG and QSPICE captured.
- [x] QSPICE side is represented as digital power electronics simulation.
- [x] PWG table values match the reference image.
- [x] LCR parameter values match the reference image.

## Generated Artifacts

- `reports/pwg_display_panel_spec.html`: visual PWG/QSPICE specification page.
- `src/qspice_tools/pwg_spec_report.py`: generator for the visual spec page.
- `tests/test_pwg_spec_report.py`: regression test that checks key reference terms and parameter values.
