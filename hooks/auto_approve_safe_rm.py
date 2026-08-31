#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse hook:自动放行"整条命令只删会话 scratchpad 内文件"的 rm。

放行条件(全部满足才放行,否则不输出决定、走正常询问流程):
- 整条命令按 && / || / ; / 换行 拆段后,每一段都必须是合法的 rm 段
  (混入任何其他命令、管道、后台符、重定向都不放行,因为 hook 放行的是整条命令);
- 段内不允许 $ 变量、` 命令替换、反斜杠转义,目标必须是字面绝对路径;
- rm 的每个目标都以安全前缀开头,且不含 .. / ~;
- 只接受 -r/-R/-f/-v 组合与 --,其他选项(-i、--no-preserve-root 等)不放行。
"""
import json
import os
import re
import shlex
import sys

FLAG_RE = re.compile(r"^-[rRfv]+$")


def _safe_prefixes():
    """按当前用户 uid 推导 scratchpad 根目录(跨 Mac 可移植)。"""
    uid = os.getuid()
    return (
        f"/private/tmp/claude-{uid}/",
        f"/tmp/claude-{uid}/",
    )


def _segment_ok(seg, safe_prefixes):
    # 段内禁止管道/后台/重定向/子 shell/变量/命令替换/转义
    if any(c in seg for c in ("|", "&", ">", "<", "(", ")", "$", "`", "\\")):
        return False
    try:
        tokens = shlex.split(seg)
    except ValueError:
        return False
    if not tokens or tokens[0] != "rm":
        return False
    paths = []
    for t in tokens[1:]:
        if t == "--":
            continue
        if t.startswith("--"):
            return False
        if t.startswith("-"):
            if FLAG_RE.match(t):
                continue
            return False
        paths.append(t)
    if not paths:
        return False
    for p in paths:
        if "~" in p or ".." in p:
            return False
        if not p.startswith(safe_prefixes):
            return False
    return True


def decide(command):
    """整条命令的每一段都是安全 rm 段时返回 True;任何异常都按"不放行"处理。"""
    try:
        safe_prefixes = _safe_prefixes()
    except Exception:
        return False
    segments = [s.strip() for s in re.split(r"&&|\|\||;|\n", command)]
    segments = [s for s in segments if s]
    if not segments:
        return False
    return all(_segment_ok(s, safe_prefixes) for s in segments)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if data.get("tool_name") != "Bash":
        return
    command = (data.get("tool_input") or {}).get("command") or ""
    if decide(command):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "rm 仅作用于会话 scratchpad 临时目录,自动放行",
            }
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
