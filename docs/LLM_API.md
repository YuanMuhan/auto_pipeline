# LLM_API 使用说明（v0.1）

## 目标与范围
- 仅覆盖 4 个调用点：`generate_ir` / `generate_bindings` / `repair_ir` / `repair_bindings`。
- Planner/CodeGen/Deploy 不调用 LLM。
- 输出必须为纯 YAML/JSON 字符串（无 markdown 代码块）。

## Provider 配置
- 支持 provider：
  - `mock`（默认）：离线读取 mock/gold 文件，不调用网络。
  - `anthropic`（示例真实 provider）：读取环境变量 `ANTHROPIC_API_KEY`；模型示例：`claude-3-haiku-20240307`（或根据实际可用模型调整）。
- 环境变量：
  - `ANTHROPIC_API_KEY`：真实 provider 所需；日志仅显示“已配置/未配置”，不打印密钥。
- CLI 参数（通过 `python -m autopipeline run ...`）：
  - `--llm-provider`：`mock` | `anthropic`
  - `--model`：模型名称（真实 provider 可选）
  - `--temperature`：默认 0
  - `--max-tokens`：可选
  - `--cache-dir`：默认 `.cache/llm/`
  - `--no-cache`：禁用缓存

## Mock 模式（CI 推荐）
- 查找顺序：`cases/<CASE_ID>/mock/` 下的对应文件：
  - `ir.yaml`、`bindings.yaml`、`repair_ir.yaml`、`repair_bindings.yaml`（缺失则尝试 `gold/` 同名文件）。
- 若 mock/gold 缺失：抛出清晰错误提示需补齐。
- 不调用网络、无 token 消耗。

## 真实 Provider 调用（以 anthropic 为例）
- 依赖 `ANTHROPIC_API_KEY`。
- 支持参数：`model`、`temperature`、`max_tokens`（可按需扩展 `top_p`）。
- 返回 usage（若可获），否则 usage=None。
- 网络/鉴权失败应抛出明确异常，runner 捕获后写入 run.log/eval。

## Prompt 与哈希
- prompt_loader 负责读取 `prompts/*.txt`，渲染模板并计算 `prompt_template_hash` / `rendered_prompt_hash`。
- 调用请求包含：rules_hash（IR_rules.md + bindings_rules.md）、schema_versions/hash、prompt_hash、inputs_hash、case_id、LLM 参数。

## 缓存策略
- 默认开启；cache key = SHA256(stage + provider + model + params + prompt_template_text_hash + rendered_prompt_hash + rules_hash + schema_versions + inputs_hash)。
- 缓存文件：`.cache/llm/<key>.json`，包含 request_meta、response_text、usage、created_at。
- 可通过 `--no-cache` 关闭，`--cache-dir` 指定路径。

## 调用点输入/输出契约
- 输入：`case_id`、`rules_ctx`(hash 集合)、`schema_versions`、`prompt_name`、`inputs_hash`、具体上下文（user_problem/device_info/ir_yaml/bindings_yaml/verifier_errors）。
- 输出：纯 YAML 字符串（无围栏），由调用者自行解析。

## CI/本地建议
- CI 使用 `--llm-provider mock` 保证可重复、无外网依赖。
- 本地调试真实模型前，先确认 `.env` 中设置 `ANTHROPIC_API_KEY`，并可指定 `--model`、`--temperature`。***
