# Weekly Figures

## Fig1 Static PASS Rate
![fig1_static_pass_rate__DEMO-MONITORING.png](fig1_static_pass_rate__DEMO-MONITORING.png)
![fig1_static_pass_rate__DEMO-SMARTHOME.png](fig1_static_pass_rate__DEMO-SMARTHOME.png)
- Static PASS 口径；bar=repair on/off；x=prompt_tier（每 case 各一张）

## Fig2 Attempts Distribution
![fig2_attempts_distribution__DEMO-MONITORING.png](fig2_attempts_distribution__DEMO-MONITORING.png)
![fig2_attempts_distribution__DEMO-SMARTHOME.png](fig2_attempts_distribution__DEMO-SMARTHOME.png)
- attempts_total 分布；样本少则均值柱状

## Fig4 Error Distribution
![fig4_error_distribution_topk.png](fig4_error_distribution_topk.png)
- TopK error codes（count），无 summary_by_error 时从 FAIL runs 的 error_code_top1 统计

## Fig5 Cost (tokens/time)
![fig5_cost_tokens.png](fig5_cost_tokens.png)
![fig5_cost_time_ms.png](fig5_cost_time_ms.png)
- tokens_total/total_duration_ms 分布（缺列则跳过）

## Summary (mean by prompt_tier x repair)
### pass_rate_static
repair_flag  off   on
prompt_tier          
P0           0.0  0.0
P1           0.0  0.0
P2           0.0  0.0

### attempts_mean
repair_flag  off   on
prompt_tier          
P0           3.0  5.0
P1           3.0  5.0
P2           3.0  5.0

### tokens_mean
repair_flag     off      on
prompt_tier                
P0           2653.0  8533.0
P1           2830.0  7870.0
P2           2909.5  8799.5

### semantic_warnings_mean
repair_flag  off   on
prompt_tier          
P0           0.0  0.0
P1           0.0  0.0
P2           0.0  0.0
