# OVEN 真实候选顺序外测协议

冻结计划：`data/natural_order_oven_v1.json`，SHA256：`fb303f743550da5adc30d3dc5b5d171ff018660458a180e90ea18712c5a24057`。

该实验检验受控 support/foil 结论能否外推到自然候选。样本来自冻结筛选中的 100 个 OVEN-MTEB 问题；使用既有 fusion-v1 图搜证据生成、且未使用金答案的 conditioned entity candidates。纳入至少四个映射候选的全部样本，固定取原始前四名。

每个题目和模型运行原始顺序、完全逆序、两个固定 seed shuffle。四条件的候选多重集、ID、文本及图像完全相同，仅顺序不同。报告原始与逆序配对准确率差、四排列敏感率，以及四排列多数投票；2:2 冲突按拒答处理。
