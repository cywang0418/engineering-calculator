# PWG LCR Windows CLI Validation Result

## Environment

Validated on the user's Windows QSPICE installation.

Previously confirmed paths:

```text
C:\Program Files\QSPICE\QSPICE64.exe
C:\Program Files\QSPICE\QUX.exe
```

## Case

```text
qspice-cli-validation/examples/pwg-lcr/pwg_lcr.cir
```

PWG input:

```text
qspice-cli-validation/examples/pwg-lcr/pwg_input.pwl
```

PWG settings:

```text
Waveform: Sinusoidal
Amplitude: Vp = 12 V
Bias: Vbias = 0 V
Frequency: 10k Hz
Duration: 5 cycles, 500 us
Samples: 1001
```

## Command

From the `qspice-cli-validation` folder on Windows:

```bat
scripts\run-qspice-circuit.bat examples\pwg-lcr\pwg_lcr.cir
```

## Result

```text
QSPICE exit code: 0
Found pwg_lcr.qraw: yes
Found pwg_lcr.log: no
```

## Interpretation

The PWG LCR CLI validation passes because QSPICE returned exit code `0` and produced `pwg_lcr.qraw`.

`pwg_lcr.log` is not required for this pass condition. This matches the earlier RC low-pass validation behavior where QSPICE also produced `.qraw` without `.log`.

## Next Step

Export these traces from `pwg_lcr.qraw` to CSV:

```text
Time
V(in)
V(out)
I(L1)
I(Ro)
```

Then import the CSV into this project to produce waveform and PWG input/output comparison reports.
