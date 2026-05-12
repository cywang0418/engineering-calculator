# QSPICE CLI Validation

This folder contains the first technical validation package for the engineering calculator and QSPICE integration project.

## Known Windows Paths

The user has confirmed these paths on the Windows machine:

```text
C:\Program Files\QSPICE\QSPICE64.exe
C:\Program Files\QSPICE\QUX.exe
```

## Goal

Prove that QSPICE can be controlled from the command line before building the full desktop application.

This validation checks:

1. A `.cir` netlist can be launched by `QSPICE64.exe`.
2. A QSPICE-compatible PWL input file can drive a test circuit.
3. QSPICE produces `.qraw` and `.log` files.
4. The output waveform can later be exported through QUX or a QSPICE-supported CSV workflow.

## Test Circuit

The first case is an RC low-pass filter:

```text
PWL input -> 1 kOhm resistor -> output node -> 1 uF capacitor -> ground
```

Files:

```text
examples/rc-lowpass/input.pwl
examples/rc-lowpass/rc_lowpass.cir
examples/rc-lowpass/expected-files.txt
scripts/run-rc-lowpass.bat
```

## How To Run On Windows

Copy the `qspice-cli-validation` folder to the Windows machine, then open Command Prompt in that folder.

Run:

```bat
scripts\run-rc-lowpass.bat
```

Expected result:

```text
QSPICE exit code: 0
Found rc_lowpass.qraw
```

Some QSPICE versions or settings may not create `rc_lowpass.log` for a successful CLI run. Treat `rc_lowpass.qraw` plus exit code `0` as the pass condition for this first validation.

If QSPICE reports an error and creates a log file, inspect:

```text
examples\rc-lowpass\rc_lowpass.log
```

## Manual Command

If the batch file fails, run this manually:

```bat
cd /d path\to\qspice-cli-validation\examples\rc-lowpass
"C:\Program Files\QSPICE\QSPICE64.exe" "rc_lowpass.cir"
```

## What To Report Back

Please report:

```text
QSPICE exit code:
Was rc_lowpass.qraw created? yes/no
Was rc_lowpass.log created? yes/no, optional
Any error text from rc_lowpass.log:
```
