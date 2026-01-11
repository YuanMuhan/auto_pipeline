# 周报总结（2026-01-11）  

## 本周完成（对应 A/B/C/D）
- A 成功/失败样例：自动筛选真实 LLM 成功 & 失败，生成对比报告与打包产物（reports/cases/*，bundles 含 plan/ir/bindings/eval）。失败缺字段表明确指向 E_SCHEMA_BIND 的 component_bindings 缺失。
- B IR 逻辑层定位：保留 catalog open（未知类型仅告警），core/full gate 区分，文档与说明补充 gate_mode_explainer/catalog_open_note。
- C Placement baseline：新增 placement_plan.yaml（heuristic，无 LLM），通过 schema+checker 校验，并在 bindings_norm 回填 placement_node_id；示例 run 见 outputs_temp_place。
- D Error-aware repair：bindings raw/norm/patched 落盘，deterministic_patch + 回放工具，生成 before/after 报告与 debug json（reports/repair/*）。

## 关键证据
- 成功/失败对比：`reports/cases/case_success.md`, `reports/cases/case_failure.md`, `reports/cases/case_compare.md`
- Repair 前后：`reports/repair/bindings_repair_before_after.md`, `reports/repair/bindings_repair_debug.json`
- Placement 示例：`outputs_temp_place/DEMO-MONITORING/run=20260111_223006_99346c/placement_plan.yaml`, `reports/weekly/placement_onepager.md`
- 核心说明：`reports/weekly/gate_mode_explainer.md`, `reports/weekly/catalog_open_note.md`

## 可复现命令（完整列表见 reports/weekly/repro_commands.md）
1) 选成功/失败并生成 bundles：`python -m tools.cases.pick_and_report --runs_glob "outputs_temp_*/**/run=*/" --out_dir reports/cases --min_repro 1 --require_real_llm true --require_ir_for_failure true --require_bindings_for_failure true --exclude_error_codes "E_CATALOG_COMPONENT"`
2) 复现失败样例（openai，无修复）：`python -m autopipeline run --case DEMO-MONITORING --llm-provider openai --model gpt-4o-mini --prompt-tier P0 --temperature 0 --output-root outputs_temp_fail --no-cache --no-repair` （需 OPENAI_API_KEY）
3) Repair 离线回放：`python -m tools.repair.replay_bindings_repair --run_dir outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890 --gate_mode core`
4) Repair 前后报告：`python -m tools.repair.make_before_after_report --run_dir outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890 --out_subdir replay_repair --out_md reports/repair/bindings_repair_before_after.md --out_json reports/repair/bindings_repair_debug.json`
5) Placement demo（mock）：`python -m autopipeline run --case DEMO-MONITORING --llm-provider mock --prompt-tier P0 --temperature 0 --output-root outputs_temp_place --no-cache`
6) 单测：`python -m unittest discover -s tests -p "test*.py" -q`

## 关键结论
- core/full 分离后，静态 PASS 不再被 codegen/compose 污染；未知组件类型默认告警统计，未再阻断。
+- bindings schema 失败可通过 deterministic_patch + 回放修复，E_SCHEMA_BIND 可迁移/消除，修复轨迹可审计。
- Placement 基线已打通，bindings_norm 可回填 placement_node_id，后续可在此基础上改进 heuristics/transport 选择。

## 风险与边界
- core PASS ≠ full PASS：runtime/compose 仍在 full gate，当前 demo 默认 SKIP。
- placement 为 heuristic baseline，未做算力/延迟优化；仅用于链路打通与可解释性。
- plan/placement 为 deterministic 基线，真实语义质量受 IR/Bindings LLM 输出与规则限制。

## 下周计划（聚焦 GPIoT/微调前置）
1) 明确微调切分：UserProblem+DeviceInfo→IR、IR+Placement→Bindings；设计样本导出脚本。
2) 定义评测口径与基准：core pass rate、错误码分布、修复成本；准备数据对齐脚本。
3) 小模型接入方案草案：训练数据格式、替换点（IR/Bindings agent）、对比实验设计。 
