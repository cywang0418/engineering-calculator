# RC Low-Pass Windows CLI Validation Result

## Environment

Validated on the user's Windows QSPICE installation.

Confirmed paths:

```text
C:\Program Files\QSPICE\QSPICE64.exe
C:\Program Files\QSPICE\QUX.exe
```

## Command

```bat
scripts\run-rc-lowpass.bat
```

## Result

```text
QSPICE exit code: 0
Found rc_lowpass.qraw
Missing rc_lowpass.log
```

## Interpretation

The first CLI validation passes because QSPICE returned exit code `0` and produced `rc_lowpass.qraw`.

`rc_lowpass.log` is not required for this validation result. It may depend on QSPICE version, runtime settings, circuit warnings, or whether QSPICE chooses to emit a diagnostic log for a successful run.

## Next Step

Validate export of one or more selected traces from `rc_lowpass.qraw` to CSV using QUX or QSPICE's supported export workflow.
