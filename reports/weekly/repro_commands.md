# 可复现命令清单

1) 选成功/失败并生成 bundles（真实 LLM，排除 catalog 错误）  
`python -m tools.cases.pick_and_report --runs_glob "outputs_temp_*/**/run=*/" --out_dir reports/cases --min_repro 1 --require_real_llm true --require_ir_for_failure true --require_bindings_for_failure true --exclude_error_codes "E_CATALOG_COMPONENT"`

2) 复现失败样例（openai，无修复，需 OPENAI_API_KEY）  
`python -m autopipeline run --case DEMO-MONITORING --llm-provider openai --model gpt-4o-mini --prompt-tier P0 --temperature 0 --output-root outputs_temp_fail --no-cache --no-repair`

3) Repair 离线回放（基于失败 run_dir）  
`python -m tools.repair.replay_bindings_repair --run_dir outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890 --gate_mode core`

4) Repair 前后报告  
`python -m tools.repair.make_before_after_report --run_dir outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890 --out_subdir replay_repair --out_md reports/repair/bindings_repair_before_after.md --out_json reports/repair/bindings_repair_debug.json`

5) Placement demo（mock，可换 openai）  
`python -m autopipeline run --case DEMO-MONITORING --llm-provider mock --prompt-tier P0 --temperature 0 --output-root outputs_temp_place --no-cache`

6) 单测  
`python -m unittest discover -s tests -p "test*.py" -q`
