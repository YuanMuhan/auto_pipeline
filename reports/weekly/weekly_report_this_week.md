# 本周总结（一句话）
- 完成 A/B/C/D 四条任务线的闭环：真实 LLM 成功/失败对比、IR 逻辑层口径澄清、Placement baseline 打通（IR→Placement→Bindings）、error-aware repair 离线复现，均有可复现证据与报告支撑（见 reports/cases、reports/repair、reports/weekly）。

# 任务线A：成功/失败 run 对比（诊断证据链）
- 差距：失败集中在 Bindings 结构缺失/必填字段缺失（典型为 component_bindings 缺失），而非 catalog 类型越界；成功样例多在 repair_on + normalizer/patch 后补齐结构。
- 样例选择：仅用真实 LLM（排除 mock），排除 E_CATALOG_COMPONENT，失败需有 IR/Bindings 文件；自动筛选并生成 bundles 与对比报告（reports/cases）。
- 启示：失败点可定位到具体字段/路径，为后续针对性修复或规则收敛提供依据，验证了静态 contracts 的诊断价值。

# 任务线B：IR 作为逻辑层中间产物（口径澄清）
- core vs full 分离：core 仅关注 Plan/IR/Placement/Bindings 的结构合法性与引用闭合，避免 codegen/compose 等执行层污染静态成功率；full 保留执行层验证。
- catalog open：未知组件类型仅记 warning/metrics，不再硬失败，承认开放世界生成的合理性，同时避免封闭库导致静态 PASS=0。
- 结论：core 口径更契合论文主线（LLM + contracts + repair 的分解闭环），full 口径留给后续执行/部署阶段。

# 任务线C：Placement baseline 落地（IR→Placement→Bindings 打通）
- Placement 位于 IR 之后、Bindings 之前，由启发式脚本生成（不调用 LLM），产物含 nodes/component_placements/rationale/transport_hint，并有 schema + checker。
- Bindings normalize 会回填 placement_node_id，与 placement_plan 对齐；metrics 增加节点/placement 计数。
- 结论：云/边/端切分已落为结构化产物，可在 core gate 下校验，为后续 codegen/runtime 预留接口与优化空间。

# 任务线D：error-aware repair + 离线 replay（修复闭环证据）
- 修复从盲重试升级为“利用错误信息增量修复”：deterministic patch + normalizer 先补齐结构，可选 LLM patch；repair_trace 记录策略/动作。
- 离线 replay 证明典型 schema 失败（E_SCHEMA_BIND 缺字段）可收敛为 core PASS 或错误迁移，并生成 before/after 报告与 debug json（reports/repair）。
- 结论：contracts-driven repair 让 LLM 输出可解释收敛，形成可复现的修复闭环，是当前技术路线的关键支撑。

# 风险与边界
- core PASS ≠ 可执行；full gate 才覆盖 codegen/runtime，当前 demo 默认 runtime_compose SKIP。
- Placement 为启发式 baseline，未做算力/延迟优化；后续可引入 LLM 建议或学习型策略对照。
- Plan 目前是 deterministic skeleton，后续可插入 LLM planner 做 ablation，对比对分解质量的影响。

# 可复现入口（命令）
- 选成功/失败并生成 bundles：`python -m tools.cases.pick_and_report --runs_glob "outputs_temp_*/**/run=*/" --out_dir reports/cases --min_repro 1 --require_real_llm true --require_ir_for_failure true --require_bindings_for_failure true --exclude_error_codes "E_CATALOG_COMPONENT"`
- 复现失败样例（openai，无修复，requires API key）：`python -m autopipeline run --case DEMO-MONITORING --llm-provider openai --model gpt-4o-mini --prompt-tier P0 --temperature 0 --output-root outputs_temp_fail --no-cache --no-repair`
- Repair 离线回放：`python -m tools.repair.replay_bindings_repair --run_dir outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890 --gate_mode core`
- Repair 前后报告：`python -m tools.repair.make_before_after_report --run_dir outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890 --out_subdir replay_repair --out_md reports/repair/bindings_repair_before_after.md --out_json reports/repair/bindings_repair_debug.json`
- Placement demo（mock，可换 openai）：`python -m autopipeline run --case DEMO-MONITORING --llm-provider mock --prompt-tier P0 --temperature 0 --output-root outputs_temp_place --no-cache`
- 单测：`python -m unittest discover -s tests -p "test*.py" -q`
