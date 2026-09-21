# 证据依赖顺序效应：四数据集四模型确证协议

冻结计划：`data/order_confirmatory_v1.json`，SHA256：`08b5b69729a6801f09c310dab2a6f37c9268d540e664689d912f2907b35712d8`。计划包含 963 个唯一题目-模型-层单元和 3,852 个正式顺序条件。

本协议在正式顺序条件调用前冻结。筛选来自独立的 `order_confirmatory_screen_v1`，每个数据集、模型独立划分 `stable-correct` 与 `support-rescuable`，每个单元最多抽取 40 题，不跨数据集池化补足。

## 主假设与终点

主假设是：在 `support-rescuable` 题上，foil-first 会抑制 support 带来的净纠错。主终点为同一证据多重集下 support-first accuracy 减 foil-first accuracy，在 top 与 bottom 两个绝对位置取题内均值。`stable-correct` 是负对照；预期证据依赖交互 `support-rescuable - stable-correct` 为正。

## 操作化

- 四条件：`top_sf`、`top_fs`、`bottom_sf`、`bottom_fs`。
- 每对条件只交换 support 与 foil；三条中性填充证据、标题、总条数均固定。
- support 使用冻结金答案。support-rescuable 的 foil 优先采用该模型三次稳定错误回答的众数；无可用回答时，二元题用反答案，开放题使用同数据集冻结 donor。
- Reference A/B 中 support 身份按单元平衡，避免标签偏置。
- 每个条件只调用一次、temperature=0；调用失败按固定缓存键重试，不以其他调用替代。

## 缓解实验

在主层 `support-rescuable` 上，四排列回答做多数投票，2:2 冲突时拒答；与单次 `top_sf` 及相同四次预算的 `top_sf` self-consistency 多数投票比较。缓解分析在该层全部三个额外 canonical 重复成功后执行。
