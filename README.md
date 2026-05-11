# Nemotron3 Test Workspace

This folder is organized for Ollama `nemotron3:33b` testing.

## 中文說明

這個資料夾是用來測試 Ollama `nemotron3:33b` 的工作區，所有腳本、測試輸入、報告與結果都集中在這裡。

### 資料夾結構（中文）

- `scripts/`：測試腳本
  - `run_nemotron3_tests.py`（文字/程式/安全測試）
  - `run_nemotron3_multimodal_tests.py`（多模態測試：圖片 + 音訊嘗試）
- `inputs/`：測試輸入
  - `prompts.json`
- `reports/`：Markdown 測試報告
- `results/`：機器可讀結果（`.json`、`.csv`）
- `results/raw/`：除錯用原始回應
- `assets/multimodal_assets/`：多模態測試素材（生成或下載）
- `refs/`：測試時使用的參考檔案
- `cache/`：Python 編譯快取

### 快速指令（中文）

執行文字測試：

```bash
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_tests.py
```

執行文字測試（切換 think 模式）：

```bash
REPORT_PREFIX=nemotron3_test_think_true OLLAMA_THINK=true \
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_tests.py

REPORT_PREFIX=nemotron3_test_think_false OLLAMA_THINK=false \
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_tests.py
```

執行多模態測試：

```bash
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_multimodal_tests.py
```

### 主要輸出（中文）

- 最新多模態報告：
  - `/Users/tycg/Desktop/nemotron3-test-workspace/reports/nemotron3_multimodal_report.md`
- 最新文字測試報告：
  - `/Users/tycg/Desktop/nemotron3-test-workspace/reports/nemotron3_test_think_true_report.md`
  - `/Users/tycg/Desktop/nemotron3-test-workspace/reports/nemotron3_test_think_false_report.md`

### 備註（中文）

- 所有作業與輸出都放在 `/Users/tycg/Desktop/nemotron3-test-workspace`。
- 本工作區主要測試模型為 `nemotron3:33b`（透過 Ollama）。

## Folder layout

- `scripts/`: test scripts
  - `run_nemotron3_tests.py` (text/coding/safety benchmark)
  - `run_nemotron3_multimodal_tests.py` (vision + audio attempt)
- `inputs/`: test inputs
  - `prompts.json`
- `reports/`: markdown reports
- `results/`: machine-readable outputs (`.json`, `.csv`)
- `results/raw/`: raw debug responses
- `assets/multimodal_assets/`: generated/downloaded multimodal assets
- `refs/`: references used during testing
- `cache/`: Python bytecode cache

## Quick commands

Run text test:

```bash
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_tests.py
```

Run text test with think mode on/off:

```bash
REPORT_PREFIX=nemotron3_test_think_true OLLAMA_THINK=true \
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_tests.py

REPORT_PREFIX=nemotron3_test_think_false OLLAMA_THINK=false \
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_tests.py
```

Run multimodal test:

```bash
python3 /Users/tycg/Desktop/nemotron3-test-workspace/scripts/run_nemotron3_multimodal_tests.py
```

## Key outputs

- Latest multimodal report:
  - `/Users/tycg/Desktop/nemotron3-test-workspace/reports/nemotron3_multimodal_report.md`
- Latest text reports:
  - `/Users/tycg/Desktop/nemotron3-test-workspace/reports/nemotron3_test_think_true_report.md`
  - `/Users/tycg/Desktop/nemotron3-test-workspace/reports/nemotron3_test_think_false_report.md`

## Notes

- All work and outputs stay inside `/Users/tycg/Desktop/nemotron3-test-workspace`.
- Model tested: `nemotron3:33b` via Ollama.
