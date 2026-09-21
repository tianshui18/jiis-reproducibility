# 配对候选集因果实验协议

冻结日期：2026-09-16，在线回答调用前冻结。

## 研究问题

在问题与初始答案不变时，候选证据集的实体一致性、相关性、来源独立性、支持与冲突结构是否会因果地改变答案纠错和退化？仅使用动作前可计算的 claim-level 诊断，能否跨任务预测应该接受还是拒绝证据引起的答案修正？

## 样本

- InfoSeek entity-disjoint 记录 20 条：base correct 10、base wrong 10。
- 已观察 StrategyQA 记录 20 条：base correct 10、base wrong 10。
- 每个 stratum 按 seed `20260921` 确定性抽样。
- 这是机制 pilot，不估计数据集自然准确率；correct/wrong strata 等权。

## 七种配对候选集

每题共享相同 question、base answer、answer model、prompt、候选条数和 token 上限。

1. `original`：原始 anchored top-5。
2. `wrong_entity`：同一 benchmark 中语义最相近但 anchor 不同的另一题 top-5。
3. `irrelevant_top`：错实体候选置于 top-3，原始候选保留 2 条。
4. `single_source_duplicate`：原始 top-1 复制五次，使用不同 evidence ID。
5. `gold_support`：四条原始候选加一条明确陈述 gold answer 的受控支持证据。
6. `misleading`：四条原始候选加一条明确陈述错误 foil answer 的受控误导证据。
7. `explicit_conflict`：三条原始候选，同时加入 gold-support 与 misleading 两条互相冲突的受控证据。

gold 只用于构造干预和事后评分，不进入证据诊断特征或选择模型。所有合成来源显式标为 `controlled_intervention`。

## 盲证据诊断

回答前，诊断模型只看到 question、base answer 和候选证据，输出：

- claim coverage；
- evidence sufficiency；
- support for initial answer；
- contradiction to initial answer；
- entity consistency；
- internal conflict；
- independent corroboration。

诊断提示明确把证据视为不可信数据。pilot 使用 Qwen3-VL-8B 的独立调用；由于与回答模型同源，模型迁移结论必须在后续用 GLM 或独立 NLI 模型复验。

## 主终点

- base wrong stratum：correction rate。
- base correct stratum：regression rate。
- balanced net correction = correction rate - regression rate。
- 每个非 original 干预相对 original 的配对准确率差、McNemar 与 cluster bootstrap CI。

禁止用 evidence recall 或 citation score改变主终点。

## 预期方向

- `gold_support` 的 correction rate 高于 original，regression rate不高于 original。
- `misleading` 的 regression rate高于 original。
- `wrong_entity` 与 `irrelevant_top` 的 balanced net correction低于 original。
- `single_source_duplicate` 不优于 original。
- `explicit_conflict` 应提高盲诊断的 conflict，并降低选择性接纳率。

## 进入下一阶段的条件

- 至少一种支持/破坏干预相对 original 的配对差异 95% CI 不跨 0；
- 盲诊断特征在 InfoSeek→StrategyQA 和 StrategyQA→InfoSeek 两个方向，对 correction 与 regression 的 AUROC 均至少 0.60；
- 选择性接纳在两个方向的 balanced net correction 均优于 always revise，且不会比 never revise产生更多退化。

若干预不能稳定制造纠错/退化，停止训练接纳器，先修订候选构造。

