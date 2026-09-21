# 证据相对顺序机制定位实验协议

冻结日期：2026-09-16。协议和计划在本轮新回答调用前冻结。

冻结计划：`data/order_mechanism_localization_v1.json`，SHA256：`1a6aa21bff534a1aba22b75e9a023bcce107ecdaf376baf64d10e967eb16ff8e`。

## 定位目标

本轮是开发集机制定位，不是新的外部复制。研究问题是：模型自身无检索答案的稳定性、冲突证据对的绝对位置和间隔，分别如何调节 support-first 相对 foil-first 的净答案退化。

## 样本和模型

- 复用干净复制中的 50 题：InfoSeek 20、StrategyQA 30。
- 复用是为了在已观察到信号的开发集上定位机制；本轮结果不得表述为独立泛化证据。
- 回答模型为 `Qwen/Qwen3-VL-8B-Instruct` 和 `zai-org/GLM-4.5V`。
- 每个模型独立建立三次无检索基线。InfoSeek 的 native 基线保留原图但不提供检索证据，并增加三次不提供图像的 text-only 基线；StrategyQA 的 native 基线是 question-only。
- 三次基线使用完全相同的 API 请求内容，但采用不同缓存盐，确保实际独立调用。

## 2×2×2 配对干预

每题保持三条自然证据、support、foil 及 InfoSeek 固定图搜/OCR 前缀完全相同。只改变五条可排序候选的位置：

- 位置：top / bottom；
- 间隔：adjacent / spaced（中间隔一条自然证据）；
- 相对顺序：support-first / foil-first。

这产生 8 个条件。每个 support-first 条件都有证据文本多重集、自然证据顺序和绝对槽位完全相同的 foil-first 配对条件。此外运行一个 `support_only` 操作检查，用于识别 native 稳定错误但可被正确证据纠正的题。

## 终点

模型自身三次 native 基线全部正确定义为 `stable_correct`，全部错误为 `stable_wrong`，其余为 `unstable`。

主终点仅在每个模型自身的 stable-correct 题上计算：四个布局中 `Acc(support-first) - Acc(foil-first)` 的题级均值。正值表示 foil-first 造成净退化。bootstrap 以题为簇，不能将四个布局或两个模型当作独立样本。

两个机制调节量为：

1. `bottom - top order effect`：正值表示冲突对靠后时顺序效应更强；
2. `spaced - adjacent order effect`：正值表示隔开后顺序效应更强。

次终点包括四个位置的独立配对效应、答案 flip、至少一个配对发生退化的独立题数、反向事件、baseline stable-wrong 和 support-rescuable 分层，以及 InfoSeek 的图像增益。

## 决策规则

相对顺序机制定位成功要求两个模型各自同时满足：至少 10 个 stable-correct 问题、合并四布局的主效应为正、至少 5 个不同问题出现顺序诱发退化。

特定调节机制定位成功要求两个模型的调节量方向相同且非零，并且至少一个模型的题级 bootstrap 95% CI 不跨 0。只有相对顺序机制和至少一个特定调节机制都定位成功，才进入针对该调节量的新样本复制。

无论 gate 是否通过，都完整报告四个 task-model 单元、精确事件数和反向事件，不以跨任务合并结果替代任务异质性。
