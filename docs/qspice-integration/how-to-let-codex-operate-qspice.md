# 如何讓 Codex 操作 QSPICE

## 目前限制

Codex 目前在 macOS 工作區中操作專案檔案；QSPICE 安裝在你的 Windows 電腦上。

所以我不能直接點擊你的 Windows QSPICE 視窗，但可以透過檔案與 CLI 流程來控制 QSPICE：

```text
Codex 產生 .cir / .pwl / runner 腳本
  ↓
Windows 執行 QSPICE CLI
  ↓
QSPICE 產生 .qraw / CSV
  ↓
Codex 讀取 CSV、分析、畫圖、產生下一步檔案
```

## 方案 A：手動交接，目前已可用

這是現在最穩的方式。

1. 我在專案中產生 `.cir`、`.pwl`、`.bat`。
2. 你在 Windows 執行：

```bat
scripts\run-rc-lowpass.bat
```

3. 你把產生的 `.qraw` 或 `.csv` 放回專案或拖給我。
4. 我解析 CSV、產生報表或下一個 QSPICE input。

優點：

- 不需要開遠端權限。
- 不需要設定網路。
- 目前已經驗證成功。

缺點：

- 每次模擬需要你手動跑一次指令。

## 方案 B：共享資料夾，自動化程度中等

適合你的 Windows 和 macOS 都能看到同一個資料夾，例如外接硬碟、NAS、同步資料夾。

流程：

```text
Codex 寫入共享資料夾
Windows 在共享資料夾執行 .bat
QSPICE 結果回到同一個資料夾
Codex 讀取結果
```

建議共享資料夾結構：

```text
qspice-cli-validation/
  examples/
  scripts/
  results/
```

你只要在 Windows 執行：

```bat
scripts\run-qspice-circuit.bat examples\rc-lowpass\rc_lowpass.cir
```

之後我就可以讀取共享資料夾裡的 CSV 或結果檔。

## 方案 C：遠端 CLI，由 Codex 直接觸發

這是最接近「讓我直接操作 QSPICE」的方式。

可選做法：

1. Windows 啟用 OpenSSH Server。
2. Windows 設定一個專用使用者帳號。
3. 用 SSH key 登入，不要傳密碼。
4. 讓 Codex 透過 `ssh` 執行 Windows 命令，例如：

```bash
ssh user@windows-host "cd C:\path\to\qspice-cli-validation && scripts\run-rc-lowpass.bat"
```

優點：

- 我可以直接觸發 QSPICE CLI。
- 適合未來做自動化測試。

缺點：

- 需要設定 Windows 遠端登入。
- 需要網路、防火牆、權限設定。
- 不建議一開始就做，除非你熟悉 Windows 遠端管理。

## 我建議的路線

先採用方案 A 或 B。

目前已驗證：

```text
QSPICE64.exe 可以從 CLI 執行 .cir
QSPICE 可以產生 .qraw
QSPICE/QUX 可以匯出 CSV
Codex 可以讀取 CSV 並計算統計值
```

下一步應該做：

```text
Codex 產生波形 HTML 報表
  ↓
確認畫面
  ↓
再把同樣能力包進 Windows 桌面程式
```

## 已新增的通用 runner

我已加入：

```text
qspice-cli-validation/scripts/run-qspice-circuit.bat
```

使用方式：

```bat
scripts\run-qspice-circuit.bat examples\rc-lowpass\rc_lowpass.cir
```

如果 QSPICE 不在預設路徑，可以先設定：

```bat
set QSPICE_EXE=C:\Program Files\QSPICE\QSPICE64.exe
scripts\run-qspice-circuit.bat examples\rc-lowpass\rc_lowpass.cir
```
