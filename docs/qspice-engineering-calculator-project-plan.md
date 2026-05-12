# 工程計算機與 QSPICE 整合專案步驟書

## 1. 專案目標

建立一套可安裝於 Windows 的工程用計算機軟體，具備以下能力：

1. 工程計算機：科學計算、工程公式、單位換算。
2. 波形產生器：產生 sine、方波、PWM、任意公式或 CSV 波形。
3. QSPICE 輸入整合：將波形輸出成 QSPICE 可使用的 PWL 檔案。
4. QSPICE CLI 自動化：透過命令列呼叫 QSPICE/QUX 執行模擬與資料轉換。
5. QSPICE 輸出記錄：讀取 QSPICE 模擬結果，顯示並分析指定訊號。
6. Windows 安裝檔：提供一般使用者可安裝與解除安裝的版本。

## 2. 建議開發策略

採用分階段開發，先完成可用的最小版本，再逐步加上自動化與分析功能。

### 第 1 階段：需求確認與規格定義

目的：先定義清楚軟體要解決的工作流程。

工作項目：

1. 確認目標使用者：電源工程、類比電路、控制系統、機械振動或一般工程計算。
2. 確認第一版支援的計算功能：
   - 科學計算
   - 單位換算
   - 波形產生
   - QSPICE PWL 匯出
   - QSPICE CSV 匯入
3. 確認第一版不做的功能：
   - 即時硬體擷取
   - 複雜資料庫
   - 雲端同步
   - 多人協作
4. 決定主要工作流程：
   - 產生波形
   - 匯出 PWL
   - 呼叫 QSPICE 跑模擬
   - 匯出或讀取結果
   - 在本軟體內記錄與分析

產出物：

- 功能規格書
- 介面面板確認稿
- QSPICE CLI 可行性測試清單

預估時間：0.5 到 1 天

## 3. 第 2 階段：技術驗證

目的：先確認 QSPICE CLI 串接方式可行，再投入正式 UI 開發。

工作項目：

1. 在 Windows 測試機安裝 QSPICE。
2. 確認 QSPICE 執行檔位置，例如：

```text
C:\Program Files\QSPICE\QSPICE64.exe
C:\Program Files\QSPICE\QSPICE80.exe
C:\Program Files\QSPICE\QUX.exe
```

3. 準備一個最小測試電路，例如 RC filter 或 op amp buffer。
4. 用命令列執行 netlist：

```bat
"C:\Program Files\QSPICE\QSPICE64.exe" test.cir
```

5. 確認產生輸出檔：

```text
test.qraw
test.log
```

6. 測試用 QUX 匯出指定訊號成 CSV。
7. 確認可指定輸出訊號，例如：

```text
V(out)
V(gate)
I(L1)
I(Rload)
```

產出物：

- CLI 測試紀錄
- 可成功執行的範例 `.cir`
- 可成功讀取的範例 `.csv`
- QSPICE/QUX 參數筆記

預估時間：1 到 2 天

## 4. 第 3 階段：軟體架構設計

建議架構：

```text
使用者介面
  ↓
工程計算核心
  ↓
波形產生器
  ↓
QSPICE 檔案產生器
  ↓
CLI 執行器
  ↓
QSPICE / QUX
  ↓
結果讀取器
  ↓
波形顯示與工程分析
```

主要模組：

1. Calculator Core
   - 科學運算
   - 工程公式
   - 單位換算

2. Waveform Generator
   - sine
   - square
   - triangle
   - PWM
   - formula-based waveform
   - CSV-imported waveform

3. QSPICE Exporter
   - PWL 檔案輸出
   - SPICE source 語法產生
   - 節點名稱設定
   - 電壓源/電流源選擇

4. QSPICE CLI Runner
   - 找到 QSPICE 安裝路徑
   - 呼叫 QSPICE64.exe 或 QSPICE80.exe
   - 呼叫 QUX.exe
   - 記錄 stdout、stderr、log
   - 處理 timeout 與錯誤訊息

5. Result Recorder
   - 讀取 CSV
   - 記錄指定訊號
   - 計算 peak、RMS、average、frequency、rise time、fall time
   - 儲存每次模擬結果

6. Waveform Viewer
   - 顯示輸入波形
   - 顯示 QSPICE 輸出波形
   - 多訊號疊圖
   - 游標量測

預估時間：1 天

## 5. 第 4 階段：第一版 MVP 開發

目的：先做出可操作的最小版本。

第一版功能：

1. 工程計算機主面板。
2. 基本科學運算。
3. 常用工程單位換算。
4. 波形產生器：
   - sine
   - square
   - PWM
5. 波形預覽。
6. PWL 匯出。
7. 產生 QSPICE 可貼上的 source 語法。
8. 匯入 QSPICE 匯出的 CSV。
9. 顯示 CSV 波形與基本量測值。

第一版暫不做：

- 自動呼叫 QSPICE
- 自動從 `.qsch` 轉 `.cir`
- 直接讀 binary `.qraw`
- 複雜專案管理

預估時間：3 到 7 天

## 6. 第 5 階段：CLI 自動化整合

目的：讓使用者不必手動切換太多工具。

標準流程：

```text
1. 使用者在本軟體設定輸入波形
2. 本軟體輸出 input.pwl
3. 本軟體產生或修改 QSPICE netlist
4. 本軟體呼叫 QSPICE64.exe 執行模擬
5. QSPICE 產生 .qraw / .log
6. 本軟體呼叫 QUX.exe 匯出指定訊號 CSV
7. 本軟體讀取 CSV
8. 本軟體顯示與記錄輸出波形
```

需要設定的項目：

1. QSPICE 安裝路徑。
2. QUX.exe 路徑。
3. 工作資料夾。
4. 電路檔案路徑。
5. 要記錄的訊號名稱。
6. 模擬 timeout。
7. CSV 輸出位置。

預估時間：3 到 6 天

## 7. 第 6 階段：專案與資料記錄功能

目的：讓軟體成為真正的工程工作工具，而不是單次轉檔工具。

功能：

1. 儲存專案：

```text
project.json
input.pwl
simulation.cir
result.csv
analysis.json
```

2. 記錄每次模擬：

```text
Run 001
Run 002
Run 003
```

3. 比較多次結果。
4. 匯出報告。
5. 匯出新的 PWL，作為下一個電路的輸入。

預估時間：4 到 8 天

## 8. 第 7 階段：Windows 安裝檔

目的：提供可交付的一般 Windows 安裝程式。

工作項目：

1. 打包 Windows 桌面程式。
2. 建立安裝檔。
3. 建立桌面捷徑。
4. 建立開始選單捷徑。
5. 支援解除安裝。
6. 第一次啟動時偵測 QSPICE 安裝路徑。
7. 若找不到 QSPICE，提示使用者設定路徑。

預估時間：1 到 2 天

## 9. 建議技術選型

### 方案 A：Python + PySide6

優點：

- 工程計算與資料處理方便。
- CSV、波形、FFT、數值分析容易做。
- 打包 Windows 可行。

缺點：

- 安裝檔體積可能較大。
- UI 精緻度需要多花一些時間。

### 方案 B：Electron + React

優點：

- UI 好做，介面漂亮。
- 圖表與互動波形工具多。
- 打包安裝檔成熟。

缺點：

- 程式體積較大。
- 與本機 CLI、檔案權限整合要設計好。

### 建議

若重點是工程計算與 QSPICE 自動化，建議使用 Python + PySide6。
若重點是漂亮互動介面與波形視覺化，建議使用 Electron + React。

本專案較適合：

```text
Electron + React 前端
Node.js CLI 執行器
Python 小工具處理數值分析
```

這樣可以兼顧漂亮介面、本機 CLI 串接與工程分析能力。

## 10. 風險與注意事項

1. QSPICE CLI 參數必須在實機驗證。
2. 不同 QSPICE 版本可能有不同命令列行為。
3. `.qraw` 是主要模擬結果檔，但第一版建議先透過 CSV 交換資料。
4. 大型模擬結果可能非常大，必須限制輸出訊號與取樣密度。
5. 需要提供 timeout，避免 QSPICE 模擬卡住。
6. 需要保存 log，方便除錯。
7. 路徑中有空白時，CLI 指令必須正確加引號。

## 11. 測試計畫

### 單元測試

1. 工程計算結果正確性。
2. 單位換算正確性。
3. 波形取樣正確性。
4. PWL 檔案格式正確性。
5. CSV 讀取正確性。

### 整合測試

1. 匯出 PWL 給 QSPICE。
2. QSPICE 成功執行 `.cir`。
3. 產生 `.qraw` 與 `.log`。
4. QUX 匯出 CSV。
5. 本軟體讀回 CSV 並顯示波形。

### 使用者測試

1. 使用者能否在 5 分鐘內產生一個輸入波形。
2. 使用者能否將波形送進 QSPICE。
3. 使用者能否讀回指定輸出訊號。
4. 使用者能否匯出結果報告。

## 12. 建議總時程

```text
需求與規格：0.5 - 1 天
技術驗證：1 - 2 天
MVP 開發：3 - 7 天
CLI 自動化：3 - 6 天
資料記錄與分析：4 - 8 天
Windows 安裝檔：1 - 2 天
測試與修正：2 - 5 天
```

總計：

```text
可展示 MVP：約 1 週
可用整合版：約 2 到 3 週
較完整工程版：約 4 到 6 週
```

## 13. 建議第一個里程碑

第一個里程碑不要一次做完整系統，先完成以下成果：

1. 顯示工程計算機面板。
2. 產生 sine / square / PWM 波形。
3. 預覽波形。
4. 匯出 QSPICE PWL 檔案。
5. 匯入 QSPICE CSV 輸出。
6. 顯示輸入與輸出波形。

完成這個里程碑後，再進入 QSPICE CLI 自動化。

## 14. 最終完成樣貌

使用者可以在本軟體中完成以下流程：

```text
建立波形
  ↓
匯出成 QSPICE 輸入
  ↓
執行 QSPICE 模擬
  ↓
讀取 QSPICE 輸出
  ↓
分析結果
  ↓
儲存專案或匯出報告
```

這個方向會讓軟體成為：

```text
工程計算機 + 波形產生器 + QSPICE CLI 控制器 + 模擬結果記錄器
```
