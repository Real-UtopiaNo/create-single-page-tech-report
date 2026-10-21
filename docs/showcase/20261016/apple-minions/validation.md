# Apple Minions：校验摘要

[可编辑 PPTX](./report.pptx) · [最终预览](/skill-static/create-single-page-tech-report/showcase/20261016/apple-minions/preview.png) · [来源与边界](./source.md)

校验日期：2026-10-16。本页针对展示目录中的当前 `report.pptx`，没有修改源报告或为通过检查重写内容。

## 当前文件结构校验

从工作区根目录运行：

```powershell
python skills/create-single-page-tech-report/scripts/validate_single_page_report.py skills/create-single-page-tech-report/docs/showcase/20261016/apple-minions/report.pptx
```

结果：**PASS，退出码 0**。脚本确认必需 PPTX 部件、严格单页、标准宽屏 `12192000 × 6858000 EMU`、无动画 timing 节点、无阻碍常规编辑的活动锁、无与段落默认显式 RGB 色重复的 run 颜色覆盖，以及可检测多行文本的显式 `150%` 行距。

| 文件 | SHA256 |
| --- | --- |
| report.pptx | `ad56cca53434a085917d105ddff493fd6c16b1556f486cc82ec1739d0efb932b` |
| preview.png | `cbc7e32a141982be25793cd1e6fe1b3fc7d55282bca1c8a49e302349e7fcaea9` |

PPTX 内含 26 个原生形状对象和 1 个独立图片对象，字体记录为 Microsoft YaHei 与 Arial；正文保留原生文字。原始图像仍是可单独选择、移动和缩放的图片对象，未把整页扁平化为截图。

## 预览与人工检查

本轮将当前 PPTX 重新导入 Artifact Tool 并渲染为 `1920 × 1080` PNG，渲染结果与展示预览的 SHA256 完全一致；因此预览对应此处下载的 PPTX。审查者实际查看了该预览，并阅读了 PPTX 文字与来源说明。

论文 Figure 1 在方法区清晰呈现，问题与效果文字分列；标题、两行事件概览、来源及洞察没有可见截断、溢出或非预期遮挡。“超过10小时到数分钟”限定为部分内部作业排队等待，成本与性能外推边界已明示。

本文件 SHA256 与真实运行的最终归档回执一致。较早的通用 finalizer 回执记录的是另一文件哈希，因此本摘要以当前文件重新校验与重新导入渲染为依据，不把旧回执当作当前字节的认证。

## 检查边界

以上记录不是原生 Microsoft PowerPoint 的打开或操作验证。结构脚本不会判断技术事实、完整 OOXML 兼容性、视觉可读性或所有编辑体验，也不能自动判断文本最终是否因宽度而换行。事实与图像来源见来源页；本页的人工检查限于所见预览和可读取的 PPTX 结构，不代替独立基准复现或现场项目验收。

