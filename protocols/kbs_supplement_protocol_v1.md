# KBS 补充实验冻结协议 v1

冻结日期：2026-09-17

本协议实现 `docs/26_KBS投稿补充实验计划.md` 的可自动执行部分。除显式标记为人工盲审的步骤外，样本、条件、模型和停止规则均在回答实验前冻结。

## 独立模型

- 模型 ID：`gemini-3.8-flash`
- 接口：OpenAI Chat Completions 兼容网关
- temperature：0
- max_tokens：1024
- response_format：`json_object`
- 系统提示：无
- 图像输入：data URL，JPEG
- 冻结受控样本：`data/order_confirmatory_screen_v1.json` 中的 400 题
- baseline 重复：3
- support-only：仅 stable-wrong 题
- 确证条件：`top_sf`、`top_fs`、`bottom_sf`、`bottom_fs`

网关密钥只从运行环境或现有示例读取，不复制到协议、日志或结果文件。

## 图像迁移

旧计划中的图像路径指向原 Linux 实验环境，本机不可直接读取。恢复源固定为：

- InfoSeek：`LuciusLan/InfoSeek_val_full` 的官方 Arrow 快照；
- OVEN-MTEB：`mteb/mbeir_oven_task6` 的 query parquet。

恢复脚本先核对原始图像 SHA256，再按旧流水线保持原尺寸、转 RGB、JPEG quality=95，并核对处理后 SHA256。只有两级哈希均匹配才写入恢复清单。

## 自然检索

- 完整自然总体：StrategyQA 200 题、InfoSeek 200 题；
- 条件机制补充池：每数据集额外最多 300 题；
- top-k：6；
- StrategyQA 查询：官方 `term + question`；
- InfoSeek 查询：冻结的 Gemini 图像实体锚点生成一次固定 query；
- 排列：original、reverse、shuffle seed 2026091701、shuffle seed 2026091702；
- 无证据 baseline：每题每模型一次，用于 correction/degradation/net correction；
- support/foil 严格配对：自动初标同时存在 support 和 foil 时，仅交换两者相对位置；
- 回答模型看不到候选标签或金答案。

自动候选标签只作为初标。全部自然冲突对和确定性抽取的 20% 其他候选进入双人盲审包；人工列在真人完成前保持空白。

## 机制稳健性

从既有四模型每个 dataset-model 的 support-rescuable 层固定抽 10 题，不跨 cell 补足。比较原始措辞、两套等义模板、token 数匹配证据对，以及 0/2/4 条 neutral distractor。自动检查答案字符串保留、句数一致和长度差不超过 10%；人工抽检状态独立记录。

## 统计

主对比固定为 support-rescuable 与 stable-correct 的 `support-first - foil-first` 差中差。首先报告以 question 为单位的 10,000 次 bootstrap；分层二项模型若混合效应随机斜率实现不可用或不收敛，则按计划使用 exchangeable within-question GEE。模型/数据集次级检验使用 Holm 校正。

## 人工边界

本自动执行不能冒充两名独立人类标注者。答案审计和自然候选审计均生成盲审 CSV、单独解盲映射与裁决列；完成状态必须保持 `pending`，直到真人填写并运行汇总。
