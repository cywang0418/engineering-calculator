# RC Low-Pass CSV Export Validation Result

## Evidence

The user provided a screenshot of the exported CSV opened in a spreadsheet/text viewer.

Visible CSV columns:

```text
Time
V(out)
V(in)
I(R1)
```

Visible rows show time-series numeric data beginning at `0`, `1e-005`, `2e-005`, and continuing in regular time steps.

## Result

CSV export is validated for the RC low-pass test case.

This confirms the project can support the workflow:

```text
QSPICE CLI simulation -> rc_lowpass.qraw -> CSV export -> engineering calculator import
```

## Next Step

Create a local CSV import parser that reads QSPICE-exported CSV data with columns such as `Time`, `V(out)`, `V(in)`, and `I(R1)`.
