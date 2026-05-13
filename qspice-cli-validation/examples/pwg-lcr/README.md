# PWG LCR QSPICE Validation Case

This case matches the PWG Display Panel specification:

```text
Waveform: Sinusoidal
Amplitude: Vp = 12 V
Bias: Vbias = 0 V
Frequency: 10k Hz
```

The generated PWG source is:

```text
pwg_input.pwl
```

The QSPICE circuit is:

```text
pwg_lcr.cir
```

Run on Windows from the `qspice-cli-validation` folder:

```bat
scripts\run-qspice-circuit.bat examples\pwg-lcr\pwg_lcr.cir
```

Expected first pass result:

```text
QSPICE exit code: 0
Found pwg_lcr.qraw
```

After QSPICE simulation, export these traces to CSV:

```text
Time
V(in)
V(out)
I(L1)
I(Ro)
```

Then return the CSV to Codex for import, plotting, and comparison with the PWG input.
