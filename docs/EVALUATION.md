# EVALUATION（对比实验模板）

本文件说明如何使用 Evaluation Pack 进行对比实验，并解读输出。

## 评估产物
- 单次运行（`python -m autopipeline run ...`）输出：`eval.json`、`report.md`、`run.log`（位于 `outputs/<case>/` 或自定义 `output_root`）。
- 批量运行（`python -m autopipeline bench ...`）额外输出：`outputs_bench/summary.csv`、`summary_by_error.csv`、`plots/`（若安装 matplotlib 则会生成 PNG）。

## 实验 1：Repair On/Off
- 目的：衡量 Repair 循环对通过率的影响。
- 命令示例：
  - On：`python -m autopipeline bench --case-ids DEMO-MONITORING,DEMO-SMARTHOME --llm-provider mock --out-root outputs_bench/repair_on`
  - Off：`python -m autopipeline bench --case-ids DEMO-MONITORING,DEMO-SMARTHOME --llm-provider mock --no-repair --out-root outputs_bench/repair_off`
- 解读：对比 `summary.csv` 中 `pass`、`ir_attempts`、`bindings_attempts`，以及 `summary_by_error.csv` 的错误码分布。

## 实验 2：Catalog On/Off
- 目的：评估 Catalog（组件/端点目录）约束对 LLM 输出合规性的影响。
- 命令示例：
  - On（默认）：`python -m autopipeline bench --case-ids DEMO-MONITORING,DEMO-SMARTHOME --llm-provider mock --out-root outputs_bench/catalog_on`
  - Off：`python -m autopipeline bench --case-ids DEMO-MONITORING,DEMO-SMARTHOME --llm-provider mock --no-catalog --out-root outputs_bench/catalog_off`
- 解读：查看 `fail_codes` 是否出现 `E_CATALOG_COMPONENT`/`E_ENDPOINT_TYPE` 等，Pass Rate 差异，报告中的 warnings（skip catalog）。

## 实验 3：Model/Prompt 对比
- 目的：对比不同 provider/model 的表现。
- 命令示例（真实 LLM 需配置 key）：
  - `python -m autopipeline bench --case-ids DEMO-MONITORING --llm-provider anthropic --model claude-3-5-sonnet-20240620 --repeat 3 --out-root outputs_bench/anthropic_sonnet`
  - `python -m autopipeline bench --case-ids DEMO-MONITORING --llm-provider mock --repeat 3 --out-root outputs_bench/mock_baseline`
- 解读：关注 `pass`、`fail_codes` 分布、`llm_calls/tokens`、`duration_ms_total`；若安装 matplotlib，查看 plots 中 Pass Rate / Failure Histogram。

## runtime_check（可选）
- 目的：最小运行时校验（`docker compose -f docker-compose.yml config`）。
- 命令：在 run 或 bench 中附加 `--runtime-check`。
- 输出：`validators.runtime_compose`，错误码 `E_RUNTIME_COMPOSE_CONFIG`。

## 输出字段提示
- `validators`：所有校验器（含 skip）结构化结果。
- `failures_flat`：扁平化错误记录（code/stage/checker/message）。
- `pipeline.stages`：各阶段耗时（ms）与尝试次数（含 repair）。
- `llm`：provider/model/缓存命中/调用次数/模板 hash 等。

## 建议的解读顺序
1. `summary.csv` Pass Rate、fail_codes（快速对比实验组）。
2. `summary_by_error.csv` 错误分布（定位瓶颈）。
3. 单 case `report.md` 细节（LLM 调用、产物存在性、规则 hash）。
4. `eval.json` 中的 validators / pipeline / llm 细节（需要更细粒度分析时）。
