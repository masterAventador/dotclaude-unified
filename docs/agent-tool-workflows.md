# 工具专用约定（按需读取）

本文件只补充个人偏好，不替代当前安装版本的 skill。全局原则见 `../CLAUDE.md`。

## 代码审查工具

- Claude Code：需要独立代码质量审查时使用 `pr-review-toolkit:code-reviewer`；实现和独立 spec 审查按当前流程使用相应子代理。
- Codex：独立代码质量审查使用自带的 `codex review`，不安装或模拟 Claude 专用审查插件。按本机帮助选择 `--uncommitted`、`--base <分支>` 或 `--commit <SHA>`。
- 若 skill 当前流程采用合并的任务审查，按该流程提供 spec 与质量结论，不额外复制同一轮审查；需要独立质量审查或最终质量审查时，使用上述工具。
- 修复后的必要质量复审沿用对应工具；只核对 finding 是否处理的轻量检查不代替完整质量审查。
- 工具不可用时明确说明限制，使用当前环境支持的审查能力，不伪称已调用缺失工具。

## Monitor 收尾（Claude Code）

使用 Monitor 盯长任务时，收到结束标记即停止对应 monitor（当前工具支持时用 `TaskStop`），不等待超时制造通知。超时仅作兜底。
其他工具使用其对应的停止接口，不套用 Claude 的参数名。

## agent-browser 操作入口

- 先读当前安装的 agent-browser skill；如果它把正文交给 CLI，再运行 `agent-browser skills get core`，具体命令以当前帮助为准。
- 常见操作为打开页面 → 获取交互快照 → 使用快照里的 ref 点击或输入 → 页面变化后重新获取快照。
- 保持无头默认；结束时关闭本轮会话，并按主规则确认浏览器及子进程退出。

## 版本维护

Superpowers 的计划审查、任务审查轮次及执行检查点，以当前安装版本为准。
2026-09-18 精简时，本机 6.3.0 的 writing-plans 要求完成计划后自审，subagent-driven-development 采用任务审查同时给出 spec 与质量结论。
这段是调整旧规则的历史依据，不是把未来流程固定为 6.3.0；升级后重新读取相应 skill。
