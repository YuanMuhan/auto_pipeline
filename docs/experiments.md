# Experiments & Matrices

## 24-run (2 providers x 2 cases)

配置：`experiments/matrix_24_2providers.yaml`

运行命令：
```bash
python -m autopipeline.bench.run_matrix --config experiments/matrix_24_2providers.yaml --out-root outputs_matrix_24 --no-cache
```

生成周报图：
```bash
python -m autopipeline.bench.weekly_plots --matrix-root outputs_matrix_24 --out-dir outputs_matrix_24/weekly_plots
```

## 60-run 模板（预留）

配置：`experiments/matrix_60_template.yaml`（CASE3/CASE4/CASE5 为占位，跑之前需在 cases/<CASE_ID>/ 下补齐 user_problem.json 和 device_info.json）

## 提醒
- 运行真实 LLM 时需要设置 API Key：
  - DEEPSEEK_API_KEY
  - OPENAI_API_KEY（可选 OPENAI_API_BASE）
- 如需避免并发限流，建议保持 max-workers=1（若 run_matrix 支持该参数）。
