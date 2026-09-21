# 证据相对顺序机制干净复制协议

冻结日期：2026-09-16。本协议在新的 Qwen / GLM 回答调用前冻结。

## 研究问题

在问题、图像、证据文本多重集、来源、候选数和 token 上限不变时，仅交换 support 与 foil 的相对顺序，是否稳定改变答案正确性？该效应能否跨纯文本/多模态任务以及 Qwen/GLM 回答模型复现？

## 新样本

- 排除 `data/risk_identification_pilot_v1.json` 的全部 40 题。
- InfoSeek：剩余全部 7 个 base-correct，以及按 seed `20260923` 抽取的 13 个 base-wrong。
- StrategyQA：按同一 seed 抽取 20 个 base-correct 和 10 个 base-wrong。
- 共 50 个新问题。InfoSeek 的 gold entity 与上一轮完全不重叠。
- 本轮是干净复制 pilot；InfoSeek 只有 7 个可用 base-correct 问题，不足以单独支持普适结论。

## 候选构造

所有受控证据使用中性标题 `Reference A/B/C` 和中性来源 `reference-a/b/c`，不出现 support、foil、misleading、gold 或 controlled 等角色词。Reference A/B 与 support/foil 的映射在 benchmark 内等数随机对换，排除标题字母偏好。

每题构造 7 个条件：

1. `support_before_foil`：3 条自然候选 + support + foil。
2. `foil_before_support`：与 1 完全相同的文本多重集，只交换 support/foil。
3. `support_neutral_foil`：2 条自然候选 + support + neutral + foil。
4. `foil_neutral_support`：与 3 完全相同的文本多重集，只反转 support/foil。
5. `support_only`：4 条自然候选 + support。
6. `foil_only`：4 条自然候选 + foil。
7. `neutral_only`：4 条自然候选 + neutral。

InfoSeek 的图搜/OCR 上下文在全部条件中保持不变。所有条件的候选条数相同。support 和 foil 使用完全相同的句式，只替换答案值。

## 回答模型

- `Qwen/Qwen3-VL-8B-Instruct`
- `zai-org/GLM-4.5V`

两个模型使用同一回答 prompt、temperature 0 和 260 token 上限。InfoSeek 向两个模型提供同一图像。回答 prompt 不包含实验条件名和证据角色。

## 终点

主比较：`support_before_foil` 对 `foil_before_support`。

- 总体配对准确率差、paired bootstrap CI 和 McNemar。
- base-correct 分层的 order-induced regression：S-F 正确、F-S 错误。
- base-wrong 分层的 order-induced correction 差。
- 字面答案 flip rate。

次比较：`support_neutral_foil` 对 `foil_neutral_support`，检验加入间隔后的相对顺序效应。`support_only / foil_only / neutral_only` 是干预强度与方向操作检查。

所有 bootstrap 以 question/sample ID 为簇。不将两个回答模型的行当作相互独立的问题。

## 进入大样本复制的 gate

本 pilot 不直接宣称普适机制。只有同时满足以下条件，才进入按事件数停止的大样本复制：

- 两个 benchmark、两个模型的主比较均为 `Acc(S-F) > Acc(F-S)`；
- Qwen 和 GLM 各自的跨 benchmark 合并效应 95% CI 下界大于 0；
- 每个 benchmark-model 至少有 5 个不同 base-correct sample 发生 S-F 正确、F-S 错误；
- Reference A/B 角色对换后效应方向一致。

若通过，下一阶段以每个 benchmark/model 至少 50 个顺序诱发 regression、且来自至少 30 个问题为停止条件。

