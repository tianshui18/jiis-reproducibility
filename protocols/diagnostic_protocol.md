# Action-Level 机制诊断协议

日期：2026-09-16。目标是诊断上一轮 H1 失败，而不是扩大一个尚未成立的 DGMS 主实验。

## 冻结设计

- InfoSeek validation 60 题，按问题类型和 seen/unseen split 确定性分层抽样；不新增人工标签。
- 基础模型：`Qwen/Qwen3-VL-8B-Instruct`，temperature=0。
- 第一轮固定观测：基础视觉回答、百度图搜、OCR 提示。
- 同一状态枚举五个动作：generic text、anchored text、rewritten text、rerank、双查询 verify。
- 每个动作独立回答，不允许看到其他动作的回答或 gold。
- 效用：`correct + 0.3*evidence_recall + 0.2*citation_support - 0.05*action_cost`。
- 主检验：动作专属预测分数与实际 `delta utility` 的 Spearman 和正收益 AUROC。
- M2 门槛：开发集存在可解释的 feature-action 对达到 `rho >= 0.2`；通过后必须在未见实体锁定集复验。

## OCR 接口预检

在自然建筑图上实测 `PaddlePaddle/PaddleOCR-VL-1.5`，返回重复数字且未形成 JSON；`deepseek-ai/DeepSeek-OCR` 重复输出“不可辨认”并未遵循 JSON。两者都不进入正式动作池。正式诊断沿用 Qwen OCR 提示作为观测，并把缺少独立 OCR 后端列为限制。

## 受控干预

- OCR 字符替换和删除；
- 逐步用错误实体替换图搜候选；
- 注入相互冲突的年份主张；
- 复制同 URL 来源。

这些干预检验特征响应是否单调，不直接代替动作收益实验。
