# 依赖说明

该 skill 的命令行脚本只依赖 Python 标准库；实际制作 PowerPoint 还需要 Agent Runtime 提供可编辑演示文稿生成能力。

## 检查命令

从 workspace 根目录运行：

```powershell
python skills/create-single-page-tech-report/verify_dependencies.py
```

## 必需与可选依赖

| 类型 | 依赖 | 缺失时的影响 |
| --- | --- | --- |
| 必需 | Python 3.10+ | 无法运行依赖自检和 PPTX 结构校验。 |
| 必需运行能力 | 可创建、编辑和渲染 `.pptx` 的 presentation 工具 | 无法生成并视觉检查可编辑 PowerPoint。 |
| 可选运行能力 | ImageGen | 来源缺少相关原图时不能生成定制位图；可降级为可编辑基础图形。 |

不需要额外 Python 包、Node.js、浏览器服务或外部网络服务才能运行 `verify_dependencies.py` 和 `validate_single_page_report.py`。

## 自检实际覆盖

`verify_dependencies.py` 会检查当前 Python 版本，并明确报告 Python 包依赖为零。它不会扫描仓库文件，也不会尝试创建 PPTX。

Agent Runtime 中的 presentation 和 ImageGen 工具不是稳定的命令行依赖，脚本无法可靠探测，因此只会输出说明。运行前应由 Agent 根据当前可用工具确认 presentation 能力；ImageGen 缺失只影响定制位图，不应被误报为依赖失败。

## 产物校验覆盖

`scripts/validate_single_page_report.py` 使用 Python 标准库读取 OOXML，检查：

- 文件是可读取的 PPTX ZIP 包。
- 必需的 PPTX 部件存在。
- 演示文稿声明且实际包含恰好 1 个 slide XML。
- slide 中不存在 PowerPoint `timing` 动画节点。

它不会判断标题语义、事实准确性、字体选择、正文是否小于等于 13 pt、图表是否清晰、页面是否溢出或遮挡。这些项目必须结合渲染预览人工复核。

## 修复方向

- Python 版本不足：安装 Python 3.10 或更高版本，并确保 `python` 指向该解释器。
- 缺少 presentation 能力：改用提供 PowerPoint 创建和渲染工具的 Agent Runtime。
- 缺少 ImageGen：使用原始来源图片或可编辑基础图形，并在交付说明中记录降级。
- 校验脚本报告页数或动画失败：删除额外页面或动画后重新导出 `.pptx` 并重跑校验。
