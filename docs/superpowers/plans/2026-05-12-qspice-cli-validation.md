# QSPICE CLI Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small validation package that proves QSPICE can run from CLI, consume a PWL input, and produce simulation output files.

**Architecture:** Keep this as a standalone validation folder before building the main application. The package contains one minimal netlist, one PWL stimulus file, one Windows batch runner, and documentation for the user to execute on the Windows QSPICE machine.

**Tech Stack:** QSPICE `.cir` netlist, PWL text file, Windows batch script, Markdown documentation.

---

### Task 1: Create The RC Low-Pass CLI Validation Case

**Files:**
- Create: `qspice-cli-validation/examples/rc-lowpass/input.pwl`
- Create: `qspice-cli-validation/examples/rc-lowpass/rc_lowpass.cir`
- Create: `qspice-cli-validation/examples/rc-lowpass/expected-files.txt`
- Create: `qspice-cli-validation/scripts/run-rc-lowpass.bat`
- Create: `qspice-cli-validation/README.md`

- [x] **Step 1: Add the PWL input**

Create `input.pwl` with a 0 V to 5 V pulse-like waveform.

- [x] **Step 2: Add the RC netlist**

Create `rc_lowpass.cir` with a PWL voltage source, 1 kOhm resistor, 1 uF capacitor, transient simulation, and `.save` traces for `V(in)`, `V(out)`, and `I(R1)`.

- [x] **Step 3: Add the Windows batch runner**

Create `run-rc-lowpass.bat` using the confirmed QSPICE path:

```bat
C:\Program Files\QSPICE\QSPICE64.exe
```

- [x] **Step 4: Add user instructions**

Create `README.md` with the exact Windows commands and the expected output files.

### Task 2: Validate Repository Files

**Files:**
- Verify: `qspice-cli-validation/examples/rc-lowpass/input.pwl`
- Verify: `qspice-cli-validation/examples/rc-lowpass/rc_lowpass.cir`
- Verify: `qspice-cli-validation/scripts/run-rc-lowpass.bat`
- Verify: `qspice-cli-validation/README.md`

- [ ] **Step 1: Check all validation files exist**

Run:

```bash
find qspice-cli-validation -type f | sort
```

Expected files:

```text
qspice-cli-validation/README.md
qspice-cli-validation/examples/rc-lowpass/expected-files.txt
qspice-cli-validation/examples/rc-lowpass/input.pwl
qspice-cli-validation/examples/rc-lowpass/rc_lowpass.cir
qspice-cli-validation/scripts/run-rc-lowpass.bat
```

- [ ] **Step 2: Check QSPICE path appears in runner and README**

Run:

```bash
rg "C:\\\\Program Files\\\\QSPICE\\\\QSPICE64.exe|C:\\\\Program Files\\\\QSPICE\\\\QUX.exe" qspice-cli-validation
```

Expected: matches in `README.md` and `run-rc-lowpass.bat`.

- [ ] **Step 3: Commit the validation package**

Run:

```bash
git add qspice-cli-validation docs/superpowers/plans/2026-05-12-qspice-cli-validation.md
git commit -m "test: add qspice cli validation package"
```
