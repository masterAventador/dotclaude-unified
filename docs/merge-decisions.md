# 三份全局规则的融合记录

2026-07-25 把三台机器各自维护的全局规则合并成本仓库这一份，此后三台机器共用同一份规则。

## 来源

| 原仓库 | 机器 | 融合前的 CLAUDE.md |
|---|---|---|
| `masterAventador/dotclaude` | 公司 Mac | 393 行 |
| `masterAventador/dotclaude-windows` | Windows 台式机 | 637 行 |
| `masterAventador/dotclaude-personal` | 家用 Mac | 692 行 |

三个原仓库保留不动作为归档。被删掉的机器专属信息（服务器 IP 与别名、bjx 项目源码路径、E 盘安装位置等）仍可在这三个仓库的历史里查到。

## 冲突裁决

| 冲突点 | 三份原写法 | 裁决 |
|---|---|---|
| Git 提交时机 | 家用 Mac：Task 完成即自动提交推送 / Windows：从不主动提交，等指令 / 公司 Mac：未表态 | **一律自动提交推送**：成块工作完成且验证通过就主动 commit + push，不等指令；只有用户说"只提交不推送""暂不提交"才停 |
| E2E 工具 | 家用 Mac：Playwright 管 E2E，agent-browser 不算测试覆盖 / 公司 Mac + Windows：E2E 直接用 agent-browser | **分工**：正式 E2E 与回归用例一律 Playwright（进仓库、可重复、接 CI）；agent-browser 只做 AI 临时操作浏览器，不计入自动化测试覆盖 |
| 子代理模型 | Windows：一律显式 opus，覆盖 skill 默认 / 另两台：无此条 | **不写死模型**，按任务难度和所在 skill 约定挑；需要高质量审查时不为省 token 降级 |
| 子代理派遣模式 | 公司 Mac + Windows：必须 `run_in_background` / 家用 Mac：无此条 | **收录**：一律后台派遣，禁止前台阻塞对话 |
| 机器专属内容 | 三份各写自己机器的服务器、盘符、路径、自检命令 | **全部删除**。本文件只写跨机器通用规则，机器事实需要时现场向用户确认 |
| 任务计划规范 | 公司 Mac：绑定 TaskCreate、编号用工具内部 taskId / 家用 Mac：工具中立、`[T1]` 自行分配 | 取**家用 Mac 版**（工具中立，不依赖特定产品的参数与依赖语法） |
| 规则管理说明 | 家用 Mac + 公司 Mac：三分路由（全局 / 技术栈分片 / 项目） / Windows：只说加进全局文件 | 取**三分路由版**，并补充"机器专属内容不进本文件"的例外条款 |
| 分支命名 | 家用 Mac + 公司 Mac：跟随团队既有规范 / Windows：不加 `feature/` 前缀 | 合并为：**跟随团队既有规范**；个人项目或无既有规范时用简短分支名不加前缀 |

## 删除清单

| 删除内容 | 原属 | 原因 |
|---|---|---|
| 本机与设备说明（Windows） | Windows | 机器专属 |
| 软件安装位置规范（一律装 E 盘） | Windows | 机器专属 |
| 服务器操作规范 | 家用 Mac（new / old）、Windows（beastify） | 机器专属，且两份内容互相矛盾 |
| 项目路径导航规则（招聘项目 / 学社项目路径） | 家用 Mac、公司 Mac | 机器专属 |
| 末尾的英文 Browser Automation 段 | Windows | 与「浏览器工具分工规范」重复 |
| Tasklist 使用规范 | 公司 Mac | 被「多步骤任务计划与状态更新规范」取代 |
| cliproxyapi 常驻例外 | 家用 Mac | 该工具已于 2026-07-25 卸载，例外不再需要 |
| agent-browser 复用系统 Chrome 的本机路径说明 | 家用 Mac | 机器专属 |

## 中性化改写

规则本身通用、但原文举的例子是某台机器专属的，保留规则、去掉机器细节：

- **本地开发服务管理规范**：保留"按需启动、用完就关、禁止开机自启"原则和理由；删掉 `brew services` / PowerShell 的具体自检命令，改成"用本机的服务管理器和进程列表自检"
- **可复用开发工具安装规范**：从"用 Homebrew 装"改成"用本机系统包管理器装（macOS 用 Homebrew，Windows 用 winget / scoop）"
- **UI 开发临时文件清理规范 / 富文本文档读取规范**：`/tmp/` 改为"临时目录"

## 新增与加强

- **全技术栈测试静默运行规范**提为独立章节并加硬：自我验证默认无头、默认后台，**禁止自检过程中弹出任何浏览器 / Electron / Tauri / 模拟器窗口打断用户**；只有用户本次明确要求有头，或底层工具确实不支持静默（必须提前说明）才例外
- **真实验收规范**（原仅公司 Mac 有，用户特别要求不能丢）原样保留，并补一句与 E2E 裁决的衔接：验收可用 agent-browser 走真实用户路径，但沉淀进回归集的正式用例一律 Playwright
- **Claude 配置文件同步规范**改为三台机器统一推 `dotclaude-unified`，白名单为 `CLAUDE.md` + `rules/` + `docs/` + `.gitignore`；明确排除 `settings.json`（含机器本地路径与插件开关）和 `memory/`（机器本地事实）

## rules/flutter.md 的合并

公司 Mac 那份 429 行、家用 Mac 那份 248 行，两份结构完全不同。以**家用 Mac 的编号结构为骨架**，把公司版 9 个独有章节按主题插入，合并后 23 节。

**从公司版并入的章节:** 路由表 vs Get.to 直接跳转（第 8 节）、Sheet/Dialog/Picker 快捷弹出封装（第 9 节）、页面安全区域 padding 规范（第 12 节）、组件使用与 widget 参数优先（第 13 节）、图标来源规范（第 14 节）、AppBar 规范（第 15 节）、日志打印（第 20 节）、第三方库依赖鸿蒙适配（第 21 节）、fvm + 鸿蒙 SDK 命令（第 22 节）。

**同主题冲突的处理:**

| 章节 | 冲突 | 处理 |
|---|---|---|
| Controller 初始化 | 家用版给了三场景模板并明确禁止 `late final c = Get.put(...)` 和 `build()` 内 `Get.put`；公司版只要求"属性声明方式" | 取家用版（更严格更具体），并把公司版解释"为什么不写在 build 里"的理由并入 |
| Sheet 封装示例代码 | 公司版示例用了 `late final PriceZoneSelectController c = Get.put(...)`，**违反**家用版的禁令 | 示例改写为构造函数初始化列表 `PriceZoneSelectSheet._({...}) : c = Get.put(...)`，两条规则不再打架 |
| 网络请求失败提示 | 家用版 `Toast.show(resp.message)`，公司版 `Toast.show(resp.errMsg)` | 字段名是项目差异不是规则差异，写成"以项目 `BaseResp` 定义为准（有的项目叫 `errMsg`）"，并补"必须给用户可见提示，不允许静默失败" |
| 接口应答命名 | 家用版区分单接口专用 `XxxData`（同文件）与跨接口领域实体（放 `models/`，不强制后缀）；公司版只要求同文件 | 取家用版（是公司版的超集） |
| 页面加载状态 | 内容一致，公司版多一条"Loading 用项目已有封装" | 取家用版 + 并入这一条 |
| 资源文件管理 | 公司版有 SVG 格式选择与着色规范；家用版有原生迁移规范 | 两边合并成一节：格式选择 → SVG 着色 → PNG/WebP 流程 → 原生迁移 |
| 路由表章节里的路由包名 | 公司版写 `app_routes` | 改为本规范第 1 节定义的 `<proj>_routes`，与项目结构对齐 |

## 待办

- **公司 Mac、Windows 两台还需手动切到本仓库**，切之前它们本地仍是旧规则。切换命令：
  ```bash
  cd ~/.claude
  git remote set-url origin git@github.com:masterAventador/dotclaude-unified.git
  git fetch origin
  git reset --hard origin/main      # 会覆盖本地规则，切前先确认本地没有想保留的改动
  ```
- 公司 Mac 切换前应确认它 `rules/flutter.md` 里没有本次没并进来的新内容（本次已按 2026-07-25 的 `dotclaude` 仓库状态合并）
- 公司 Mac 原仓库里的 `scripts/sim_control.py`（iOS 模拟器滚动/点击脚本）和 `memory/MEMORY.md` 未纳管，仍留在 `dotclaude` 仓库
