# Evidence-set Adequacy 锁定协议

冻结日期：2026-09-16。在生成新 StrategyQA holdout 的动作结果之前冻结。

## 假设

工具动作的样本级价值由两个可迁移中介决定：

1. 检索前的实体锚点质量决定 anchored search 是否可能净纠错。
2. anchored 候选集的相关性、覆盖、独立性、冗余和冲突结构决定 rerank / verify 是否可能净纠错。

主标签不是混合效用，而是相对动作前状态的答案变化：`+1=wrong→right`、`0=不变`、`-1=right→wrong`。

## 数据隔离

- 训练：InfoSeek diagnostic 60 + entity-disjoint validation 100，共 160 条。旧锁定集在本轮视为开发数据。
- 开发审计：已经观察过的 StrategyQA 100 条仅用于代码和分布诊断，不用于拟合或阈值选择。
- 新锁定外测：官方 StrategyQA dev 按 seed `20260919` 打乱后的 `[100:200]`，与既有 `[0:100]` QID 零重叠。
- 新外测 gold decomposition 不进入冻结文件；gold facts 仅在动作回答完成后用于次要证据指标，不进入本轮特征或主标签。

## 特征可得性

检索前 anchor-quality：anchor 与问题/初始实体/基础实体的一致性、anchor 长度与信息量、泛化词比例、基础回答不确定性。只使用 anchored query 形成前可得的信息。

检索后 candidate-adequacy：anchored top-8 的问题/anchor/初始答案覆盖，embedding 相关性均值、最大值、离散度与低位候选增益，域名多样性、文档冗余、数字冲突、长度与空结果率。只使用 rerank / verify 前已经取得的 anchored 候选集。

排除：gold answer、gold entity、gold facts、question category、dataset split、provider raw score、rerank score、动作后的答案与引用。

## 模型与策略

- 每个动作分别拟合纠错分类器与退化分类器，净分数为 `P(correction)-P(regression)`。
- 比较 prior-only、legacy global-state、mechanism 三组特征。
- 固定 L2 正则，不在外测上校准；按训练样本 bootstrap 120 次，取净分数第 10 百分位作为 LCB。
- S0 仅在 anchored LCB > 0 时检索；执行 anchored 后，在 rerank / verify 中选择 LCB 最大且 > 0 的动作，否则停止。
- 主结果：相对 base 的净纠错、最终 accuracy、paired bootstrap CI、McNemar、policy regret；调用数为次要约束。

## 评价与门槛

- 每个动作分别报告 correction AUROC、regression AUROC、净分数与 `{-1,0,1}` 标签的 Spearman；禁止用 pooled AUROC 代替逐动作结果。
- 至少两个 benchmark 上 macro per-action correction AUROC 和 regression AUROC 均不低于 `0.60`。
- 新外测 LCB 策略的净纠错 95% CI 下界大于 0。
- 新外测 policy regret 低于最佳固定动作。
- 调用减少至少 20% 时，accuracy 相对最佳固定动作下降不超过 1 个百分点；或在不增加调用时 accuracy 提升至少 3 个百分点。
- 锚点错配、头部无关候选、单源复制、数值冲突四类干预中，预期方向响应率至少 80%。

任一主门槛失败，则不扩大数据规模，不训练复杂非线性路由器。

## 新外测前的开发期修订

首次开发回放发现绝对 anchor-question overlap 严重编码 benchmark：InfoSeek 均值 `0.049`，已观察 StrategyQA 均值 `0.927`。因此在创建 `[100:200]` 新 holdout 前冻结 v2：

- 新增 anchor 与两个独立实体假设的跨语言 embedding 一致性。
- 主模型改为 `mechanism_invariant`：候选侧只使用查询内相对量、来源多样性、冗余和冲突，不使用绝对 question/answer similarity 均值或最大值。
- v1 `mechanism` 保留为开发对照，不作为新外测主检验。
- 所有门槛、LCB 阈值和主标签不变。

v2 回放进一步发现 StrategyQA 的 anchor、initial entity、base entity 同源，三者相似度恒为 1。新 holdout 前再冻结 v3：锚点一致性只与独立闭卷视角比较。StrategyQA 使用已缓存的第二视角 anchors；InfoSeek 使用独立视觉模型实体与图搜 anchor。删除同源 base-entity agreement。其他特征和门槛不变。
