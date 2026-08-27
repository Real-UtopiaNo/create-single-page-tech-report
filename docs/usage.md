# 使用方式

## 典型 Prompt

- `请使用 create-single-page-tech-report，把这篇论文整理成一页中文技术洞察 PPT，按问题、方法、效果组织，优先使用论文原图，并交付可编辑 PPTX、预览图和校验摘要。`
- `请把这份技术发布材料做成一页事件快报，标题直接总结事件，正文突出关键动作和量化结果，底部给出面向技术决策者的洞察启示。`
- `请修订这份单页技术汇报，保持一页和无动画，修复信息层级、溢出、遮挡及证据边界问题。`

## 输入

| 输入 | 说明 |
| --- | --- |
| 来源材料 | 论文 PDF、结构化解析结果、网页正文、Markdown、技术结果或新闻材料。 |
| 附带资产 | 原始图片、图表、表格、图注和来源定位。 |
| 目标读者 | 研究者、技术负责人或技术路径决策者。 |
| 输出路径 | 未明确指定时，使用 `.tmp/create-single-page-tech-report/<task-name>/`。 |

## 推荐流程

1. 阅读 `SKILL.md` 并盘点来源材料及附带资产。
2. 区分论文与事件快报，确定一句话标题和完整事件概览。
3. 选择两栏、三栏、四栏或纵向卡片布局。
4. 优先使用来源原图；没有相关原图时再使用 ImageGen 或可编辑基础图形。
5. 创建可编辑 `.pptx`，运行分组锁清理脚本，仅删除 slide 对象的活动 `noGrp` 锁。
6. 渲染预览并检查溢出、遮挡、对齐和可读性。
7. 运行结构校验并完成人工清单复核。

## 命令入口

以下命令从 workspace 根目录运行。

检查命令行依赖：

```powershell
python skills/create-single-page-tech-report/verify_dependencies.py
```

校验最终 PPTX：

```powershell
python skills/create-single-page-tech-report/scripts/normalize_groupability.py `
  .tmp/create-single-page-tech-report/<task-name>/report.pptx

python skills/create-single-page-tech-report/scripts/validate_single_page_report.py `
  .tmp/create-single-page-tech-report/<task-name>/report.pptx
```

`normalize_groupability.py` 默认原子更新输入文件，只删除 `noGrp=1/true`，保留 `noMove`、`noResize`、`noTextEdit` 和其他锁。需要保留原文件时使用 `--output <new-file.pptx>`。

## 输出

```text
.tmp/create-single-page-tech-report/<task-name>/
|-- report.pptx
|-- preview.png
`-- validation.txt
```

预览文件名可以随渲染工具变化，但最终结果必须包含可编辑 `.pptx`、至少一张页面预览和校验结果摘要。只有用户明确要求时，才把正式结果复制到指定的可追踪目录。

## 完成标准

- PPTX 严格为 1 页且无动画。
- 普通 slide 对象不存在活动 `noGrp` 锁，可在 PowerPoint 中组合。
- 标题直接总结事件，概览条可独立说明事实。
- 技术论文按问题、方法、效果组织并给出量化证据边界。
- 字体、字号、颜色和图表符合 `SKILL.md`；无溢出、遮挡或不自然换行。
- 底部洞察启示包含结论与建议，可选行动项。
- 自动校验通过，人工复核项已逐项确认。

本 skill 默认不要求子 Agent。材料复杂时可以让来源分析 Agent 整理事实，或让独立视觉 checker 检查预览；启用前应允许 Agent 启动相应协作角色，并要求它们只交接事实清单或视觉问题，不替代主 Agent 的最终责任。
