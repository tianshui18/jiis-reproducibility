# 独立证据退化风险识别 pilot 协议

冻结日期：2026-09-16。本协议在新的回答和 GLM judge 调用前冻结。

## 研究问题

在上一轮已证明候选集会因果改变答案的前提下，独立模型的 claim-evidence 诊断能否跨任务识别 `right -> wrong` 退化？显式建模退化风险的拒绝策略能否优于 always revise？

## 数据与干预

- 冻结上一轮 InfoSeek 20 题和 StrategyQA 20 题，每个 benchmark 的 base correct / wrong 各 10 题。
- 复用已缓存的七种候选集与 280 个回答，不重新抽样。
- 新增 `misleading_top`：将同一 foil 证据从文搜候选末尾移至首位，其余文本不变。
- 新增 `conflict_foil_first`：将 `explicit_conflict` 中 support / foil 的顺序反转，其余证据不变。
- 共 40 题 x 9 变体 = 360 个候选集；新增 80 次 Qwen 回答和 360 次独立 GLM 诊断。

顺序实验是成对反转而非只保留一个随机顺序，因此可以逐题估计位置效应。

## 独立诊断

- 回答模型：`Qwen/Qwen3-VL-8B-Instruct`。
- 风险 judge：`zai-org/GLM-4.5V`，禁用 thinking，temperature 0。
- judge 只看 question、initial answer 和 candidate evidence，不看 gold、回答后答案、变体名或结果标签。
- judge 对每条证据输出相对 initial answer 的 `support / contradict / unknown`、entity match、directness 和 source group，同时输出全局支持、反驳、实体一致、内部冲突与独立反驳分数。
- 结构特征仅由上述诊断、证据顺序、来源和文本重复度派生，不使用 gold。

## 冻结模型

1. `Qwen baseline`：上一轮 7 个全局诊断分数，仅在原七变体上评估。
2. `GLM compact`：GLM 全局分数加逐证据派生的 top-3 contradiction、顺序加权 contradiction、entity match、独立来源和重复度。这是主模型。

对每个迁移方向：

- `p_break` 只在 base-correct 行上拟合，标签为候选答案是否变错。
- 为评估接纳策略，`p_fix` 只在 base-wrong 行上拟合，标签为是否纠正。
- 线性 logistic 模型使用 L2 正则；不用 variant ID 和 benchmark ID。
- 风险加权分数为 `p_fix - 2 * p_break`。阈值只在训练 benchmark 选择：在保留至少 70% always-revise 纠错的候选中，最大化 `correction - 2 * regression`。
- 所有 bootstrap 以 sample ID 为簇，同题不拆分。

## 主终点与 gate

主终点是 base-correct 条件下的 regression AUROC、AUPRC lift、Brier 和 ECE。策略终点仍是 balanced net correction，不使用混合效用。

两个迁移方向均需同时满足：

- 锁定测试方向至少 30 个 regression 事件，且来自至少 10 个不同 sample ID；
- regression AUROC >= 0.70；
- regression AUPRC / prevalence >= 2.0；
- 风险策略 balanced net correction 严格高于 always revise；
- regression 不高于 always revise，且保留至少 70% 的 always-revise 纠错。

任一条件失败，本轮只能解释为机制 pilot，不得宣称风险接纳器可部署。
