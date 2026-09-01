#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse hook：命令同时含整词 ssh 与 rm/rmdir 时强制人工审批（疑似远程删除）。

背景：本机 permissions.allow 里有裸 Bash（全放行）且 rm 已放行，
ssh 包着的远程删除不会命中任何 ask 规则，会被静默执行。本钩子把
"ssh + rm" 组合拉回人工审批；输出 ask 的优先级高于 allow 规则。

宁可误弹不可漏拦：ssh 命令里出现 rm 整词（如 grep rm、--rm）也会
多问一次，代价只是一次确认。其余命令不输出任何决定，走原有规则。

注册（各机器本地 settings.json，hooks.PreToolUse，matcher "Bash"）：
    { "type": "command", "command": "python3 ~/.claude/hooks/ask_remote_rm.py", "timeout": 10 }
"""
import json
import re
import sys

SSH_RE = re.compile(r"\bssh\b")
RM_RE = re.compile(r"\brm(dir)?\b")


def should_ask(command):
    """命令同时含整词 ssh 与 rm/rmdir 时要求人工审批。"""
    return bool(SSH_RE.search(command) and RM_RE.search(command))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if data.get("tool_name") != "Bash":
        return
    command = (data.get("tool_input") or {}).get("command") or ""
    if should_ask(command):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "命令同时含 ssh 与 rm：疑似远程删除，需人工确认",
            }
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
