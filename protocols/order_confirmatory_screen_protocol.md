# 证据依赖顺序效应：独立分层筛选协议

冻结日期：2026-09-17。本协议在四模型正式筛选回答前冻结。

冻结计划：`data/order_confirmatory_screen_v1.json`，SHA256：`57713aacd409e7ae7278a67a7d979b8c572bd3808893a1cfcdbed182e56365d4`。

## 目的

从顺序实验未使用的问题中，为每个回答模型独立建立 `stable-correct` 与 `support-rescuable` 分层。筛选答案不能用于调节后续顺序条件、提示词或判分规则。

## 数据

- StrategyQA：排除本项目所有已有逐题记录后，从剩余官方开发题中按固定 seed 抽取 100 题。
- BoolQ：从官方 SuperGLUE train 按固定 seed 抽取 100 题；原始 passage 只保留作后续自然 support，不进入无证据基线。
- InfoSeek：从与既有 pilot/independent 实体和图像均不重叠的 fusion development 中抽取 100 题。
- OVEN-MTEB：从冻结的 1,000 题检索测试中抽取 100 题。
- 固定 seed 为 `20260917`。四个数据集各 100 题。

## 模型

- `Qwen/Qwen3-VL-8B-Instruct`
- `Qwen/Qwen3.5-9B`
- `Pro/moonshotai/Kimi-K2.6`
- `zai-org/GLM-4.5V`

四个模型均在正式筛选前通过图片输入能力探针。每个模型独立分层，不共享其他模型的 base 标签。

烟测修订（正式全量调用前）：对 Qwen3.5、Kimi 与 GLM 显式关闭思考输出；瞬态超时、限流、服务端错误与解析失败最多重试 3 次。每个重复保存固定 `repeat` 编号，断点恢复只补缺失编号，禁止用已有缓存重复冒充独立调用。

## 筛选

1. 每个 sample-model 执行三次内容完全相同、但缓存盐不同的无检索回答。
2. 三次全对为 `stable-correct`，三次全错为 `stable-wrong`，其余为 `unstable`。
3. 只对 stable-wrong 调用一次中性标题的 controlled support-only。
4. stable-wrong 且 support-only 正确为 `support-rescuable`。

InfoSeek 与 OVEN 保留原图；StrategyQA 与 BoolQ 是 question-only 基线。数值型 InfoSeek 按官方 `range` 判定，其余使用归一化 exact match。

## Gate

理想确证规模为每个 dataset-model 至少 30 个 stable-correct 和 30 个 support-rescuable。筛选不足的单元不得通过跨数据集池化伪装为满足；应报告实际产率，并在顺序实验中使用冻结的可用数量和题级区间。
