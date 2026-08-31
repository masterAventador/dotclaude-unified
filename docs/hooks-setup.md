# hooks/ 钩子脚本与各机器注册方式

`hooks/` 目录随 dotclaude-unified 同步，但钩子的**注册**在各机器本地的
`settings.json`（不入库）里，新机器拉取后需要手工注册一次。

## auto_approve_safe_rm.py — 自动放行"只删 scratchpad 临时文件"的 rm

- 作用：整条命令的每一段都是删除会话 scratchpad（`/private/tmp/claude-<uid>/…`）
  内文件的 rm 时自动放行；删除任何真实文件、含变量/管道/重定向/其他命令时仍走正常权限询问。
- 平台：**仅 macOS**（依赖 `os.getuid()` 与 `/private/tmp` 路径约定），Windows 机器不要注册。
- 测试：`python3 ~/.claude/hooks/test_auto_approve_safe_rm.py`（应输出 PASSED）。

### 注册（macOS，各 Mac 的 settings.json 中 hooks.PreToolUse 追加）

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "python3 ~/.claude/hooks/auto_approve_safe_rm.py"
    }
  ]
}
```

注册后新会话生效；当前会话内改动 hooks 配置可能需要重启会话或在 `/hooks` 里确认。
