---
description: Flutter + GetX 通用技术规范（结构 / Widget / Controller / 路由 / 网络 / 资源 / 鸿蒙）
paths:
  - "**/*.dart"
  - "**/pubspec.yaml"
---

# Flutter + GetX 通用技术规范

本文件规定所有 Flutter 项目的**整体结构**、**技术选型**和**编码规范**。创建新项目、新模块、新文件必须严格遵循本文件约束，不得临时发挥。

遇到本规范覆盖不到的新场景时，**先停下来与用户讨论迭代规则本身**，再落地到具体项目，禁止在项目里临时发挥。

---

## 1. 项目整体结构（强制）

所有 Flutter 项目统一使用两层结构：**业务层 `business_packages/` + 基础层 `foundation_packages/`**。

### 顶层目录树

本节只画**项目根 + 包级**结构，**不画**任何包的内部。包内部细节由对应分片规则规定（见下方索引）。

```
<project_root>/                              # Flutter 项目根目录
├── lib/
│   ├── main.dart                            # 启动入口（首行 await GetStorage.init()）
│   └── home_page.dart                       # 集成各业务模块暴露的 tab 首页
│
├── business_packages/                       # ── 业务层（按 app tab 划分模块）
│   ├── <proj>_home/                         # tab 1 业务模块
│   ├── <proj>_message/                      # tab 2 业务模块
│   ├── <proj>_profile/                      # tab 3 业务模块
│   └── <proj>_auth/                         # 非 tab 业务模块（登录/注册等）
│                                            # 包内结构 → flutter-business-layer.md
│
└── foundation_packages/                     # ── 基础层（6 个固定包）
    ├── <proj>_uikit/                        # 公共 UI 组件（Button/Input/Theme/Color）
    ├── <proj>_network/                      # 网络库
    ├── <proj>_routes/                       # 路由名称集中表
    ├── <proj>_user/                         # 用户中心
    ├── <proj>_bizkit/                       # 公共业务组件
    └── <proj>_util/                         # 工具类
                                             # 包内结构 → flutter-foundation-layer.md
```

### 结构不变性声明

- 日常开发、新建模块、新建项目，**严格按**此目录树组织代码
- 包内部结构按对应分片规则组织：
  - 业务层细则：`~/.claude/rules/flutter-business-layer.md`
  - 基础层细则：`~/.claude/rules/flutter-foundation-layer.md`
- 遇到此结构覆盖不到的新场景时，**停下来与用户讨论迭代规则本身**

---

## 2. 包命名规范（强制）

- **所有包强制使用统一的项目短名前缀** `<proj>_xxx`
- 前缀具体值由项目决定，但同一项目内**所有包必须统一前缀**
- 业务包：`<proj>_<tab_name>`（如 `<proj>_home`、`<proj>_message`、`<proj>_profile`、`<proj>_auth`）
- 基础包：`<proj>_<role>`（`<proj>_uikit` / `<proj>_network` / `<proj>_routes` / `<proj>_user` / `<proj>_bizkit` / `<proj>_util` 共 6 个，**固定**）

---

## 3. Widget 类型选择

优先使用 **StatelessWidget**，用 GetX 管理状态。

**必须使用 StatefulWidget 的场景：**
- 需要 `TickerProvider`（如 `TabController`、`AnimationController`）
- 需要管理 `TextEditingController` / `ScrollController` 等且不适合放在 Controller 中

---

## 4. Page 与 Controller 职责分离（强制）

- **Page**：**只写页面布局代码**，绑定 UI 事件（通过回调调用 controller 方法）
- **Controller**：数据管理、网络请求、页面跳转、所有业务逻辑
- **Page 类绝对禁止 `setState`**，也禁止写任何业务逻辑（包括简单跳转）
- 即使页面没有任何逻辑，**也必须创建对应 Controller 类**（空类也要写）

---

## 5. Controller 初始化三场景模板（强制）

所有 page 的 controller 属性**固定命名为 `c`**，`Get.put` **必须**在属性声明处或构造函数初始化列表完成。

**绝对禁止：**
- ❌ `late final c = Get.put(...)`（惰性初始化，controller 的 `onInit` 不会在页面打开时立即触发）
- ❌ 在 `build()` 方法里 `Get.put`

### 场景 ① 无参 controller

```dart
class ConversationListPage extends StatelessWidget {
  ConversationListPage({super.key});
  final c = Get.put(ConversationListController());

  @override
  Widget build(BuildContext context) { ... }
}
```

### 场景 ② 有参 controller（业务模块页面）

用构造函数**初始化列表**初始化 `c`：

```dart
class ChatDetailPage extends StatelessWidget {
  final String conversationId;
  final ChatDetailController c;

  ChatDetailPage({super.key, required this.conversationId})
      : c = Get.put(ChatDetailController(conversationId: conversationId));

  @override
  Widget build(BuildContext context) { ... }
}
```

### 场景 ③ bizkit 页面（有参 + 强制 `tag`）

bizkit 页面可能被不同业务并发打开，强制带 `tag: UniqueKey().toString()` 避免 controller 实例互相替换：

```dart
class NameSearchPage extends StatelessWidget {
  final String initialKeyword;
  final NameSearchController c;

  NameSearchPage({super.key, required this.initialKeyword})
      : c = Get.put(
          NameSearchController(initialKeyword: initialKeyword),
          tag: UniqueKey().toString(),
        );

  @override
  Widget build(BuildContext context) { ... }
}
```

`UniqueKey().toString()` 一次性字符串不需保存 —— 路由 pop 时 GetX 自动回收 controller。

**为什么不写在 `build()` 里:** 属性声明 / 初始化列表让 controller 的创建点与 Page 的属性列表并排，一眼能看出本页持有哪些 controller；Page 的 const 构造函数收益低（重建只在外部参数变化时触发），不值得为此把 `Get.put` 塞进 `build`。

---

## 6. Widget 交互事件处理

Widget 中的交互事件（点击、长按等）**不要直接处理业务逻辑**，通过**回调函数向上透传**给 Controller 处理：

```
Widget 接收回调参数 → 事件触发时调用回调 → Controller 处理业务逻辑
```

---

## 7. 页面参数传递

**创建时赋值**，不要在 `onInit` 里从 `Get.arguments` / `Get.parameters` 获取。

- ✅ 正确：调用方创建 Page 时直接传参 → Page 构造函数接收 → 传给 Controller 构造函数
- ❌ 错误：`Get.to()` 传 arguments → Controller 在 `onInit` 里从 `Get.arguments` 读取
- **唯一例外**：路由声明里的 `GetPage`（没有创建入口可以直接赋值，只能从 `Get.arguments` / `Get.parameters` 取）

---

## 8. 路由表 vs Get.to 直接跳转（强制）

**核心规则:** 页面跳转默认走 `Get.to(() => XxxPage(...))` 创建时传参，**只有跨业务模块跳转才在路由表注册**。非必要不加 page route。

**判断标准:**

| 场景 | 做法 |
|---|---|
| 同一业务模块内跳转（如模块 A 内部 home → detail） | `Get.to(() => DetailPage(...))`，**不**注册路由 |
| 跨业务模块跳转（如模块 A 跳到模块 B 的某个详情） | 注册到基础层路由包 `<proj>_routes`，用 `Get.toNamed(pageBDetail)` |
| 业务模块的主入口 Page（被 Tab 容器或壳工程直接 import 实例化） | 不需要路由，壳工程 `import` 直接拿 Page 类 |

**为什么:**
- `Get.to(() => ...)` 走构造函数传参 → 类型安全 + IDE 自动补全 + 重构友好；路由表 + `Get.arguments` 走 dynamic，容易漏字段
- 路由表的核心价值在 **"跨业务解耦"** —— 让业务模块之间不用互相 import 对方的 Page 类。模块内本来就在同一个 import 网内，加路由是浪费
- 路由表越精简，后续维护成本越低；无人引用的 PageName 只会变成噪音

**操作流程:**
1. 写新页面时**默认不注册路由**
2. 跳转点用 `Get.to(() => XxxPage(p1: v1, p2: v2))`
3. **当且仅当**其他业务模块也要跳到这个页面，才把它下沉到路由表
4. 重构时如果路由表里发现某个 PageName 已无人引用，直接删除（配合全局「重构后清理规范」）

**正确写法:**
```dart
// ✓ 模块内跳转直接 Get.to + 构造参数
Get.to(() => XxxPage(p1: v1));
```

**错误写法:**
```dart
// ❌ 模块内自己跳自己，没必要注册路由表
GetPage(name: pageXxx, page: () => XxxPage());
// ...
Get.toNamed(pageXxx, arguments: {'p1': v1});
```

---

## 9. Sheet / Dialog / Picker 快捷弹出封装（强制）

**核心规则:** 凡是用 `showModalBottomSheet` / `showDialog` / 自定义 picker 等方式弹出的 widget 类，**必须在类内提供 `static Future<T?> show(...)` 方法**，封装弹出方式 + Controller 生命周期管理。**外层调用方不允许直接调 `showModalBottomSheet` 自己封装。**

**封装内容（最少做到 5 条）:**
1. 调用 `showModalBottomSheet` / `showDialog` 等弹出方法本身
2. 配置项目通用的弹层参数（`barrierColor`、`backgroundColor: Colors.transparent`、`isScrollControlled: true` 等，具体遮罩 token 名以项目约定为准）
3. 创建 / 注入 Controller 实例（按第 5 节规则，用属性声明或构造函数初始化列表，**不要用 `late final`**）
4. **关闭后主动销毁 Controller**（如 `Get.delete<XxxController>()`），保证下次打开是新状态、不出现"再次打开还显示上次状态"的 bug
5. 返回 `Future<T?>`，T 是用户选择的结果类型（取消时 null）

**示例（bottom sheet 选择器）:**

```dart
class PriceZoneSelectSheet extends StatelessWidget {
  final String initial;
  final PriceZoneSelectController c;

  // 构造器私有，强制走 show 入口；c 在初始化列表创建（符合第 5 节场景 ②）
  PriceZoneSelectSheet._({super.key, required this.initial})
      : c = Get.put(PriceZoneSelectController(initial: initial));

  /// 弹出选择价区 sheet。
  /// 返回选中的价区名（点完成/确认）或 null（取消/点遮罩/系统返回）。
  static Future<String?> show({
    required BuildContext context,
    required String initial,
  }) async {
    final picked = await showModalBottomSheet<String?>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: AppColors.scrim,
      builder: (_) => PriceZoneSelectSheet._(initial: initial),
    );
    Get.delete<PriceZoneSelectController>();  // ← 关闭后销毁，下次打开重新创建
    return picked;
  }

  @override
  Widget build(BuildContext context) { ... }
}
```

**调用方写法（封装后调用方代码极简）:**

```dart
// ❌ 错误（外层自己重复封装 showModalBottomSheet）：
final picked = await showModalBottomSheet<String?>(
  context: ctx,
  isScrollControlled: true,
  backgroundColor: Colors.transparent,
  barrierColor: AppColors.scrim,
  builder: (_) => PriceZoneSelectSheet(initial: area.value),
);

// ✓ 正确（直接调封装好的 show 方法）：
final picked = await PriceZoneSelectSheet.show(
  context: ctx,
  initial: area.value,
);
```

**为什么:**
- **避免重复封装** —— 同一个 sheet 被多处入口调用时，每个入口都自己写 `showModalBottomSheet(...)` 是大量重复代码，且容易漏配置（如忘加 `barrierColor`）
- **强制 Controller 生命周期管理** —— `Get.put` 创建后若没人 `Get.delete` 销毁，下次打开同名 Controller 已存在，`selected` / 搜索关键字等状态会"残留"，导致再次打开看到的是上次状态
- **构造器私有强制走 show 入口** —— 用 `_` 前缀让构造器私有，外层无法 `new XxxSheet(...)` 直接构造，必须通过 `XxxSheet.show(...)` 入口，规则不会被绕过

**不适用场景:** 纯展示组件（如 `XxxCard` / `XxxButton` 等不弹出的 widget），不需要 show 方法。

---

## 10. 页面加载状态

- 首次加载显示 Loading 指示器，**刷新不显示**
- 判断条件：`if (c.isLoading.value && c.dataList.isEmpty)` 才显示 Loading
- `isLoading` 初始化为 `true.obs`，首次加载完成后设为 `false`
- 下拉刷新**不**修改 `isLoading`
- Loading 组件用项目自身已有的封装（具体类名以项目约定为准），不要每个页面各写一套

---

## 11. 刷新粒度分层（强制）

| 场景 | 方式 | 说明 |
|------|------|------|
| 单变量刷新 | `Obx` 包裹 `.obs` | **首选**，细粒度自动刷新 |
| 大块内容刷新 | `GetBuilder` + controller 调 `update()` | 手动触发整块刷新 |
| `setState` | 仅限**独立 widget 小组件 + 极简**场景 | **page 类绝对禁用** |

---

## 12. 页面安全区域 padding 规范

**核心规则:** 涉及"顶部 AppBar + 底部可滚动内容"的页面，**不要用 `SafeArea` 包整体 body**——会让背景在安全区下方裸露、滚动可视区被截短。**正确做法是让滚动 widget 全屏，由它的 `padding.bottom` 叠加系统底部安全区量**，让末项能滚到 home indicator 上方。

**正确写法:**

```dart
@override
Widget build(BuildContext context) {
  final bottomInset = MediaQuery.viewPaddingOf(context).bottom;
  return ListView(
    padding: EdgeInsets.fromLTRB(
      16,
      16,
      16,
      16 + bottomInset,  // 末项滚到 home indicator 上方
    ),
    children: [...],
  );
}
```

**错误写法（不要这么做）:**

```dart
// ❌ 整体 SafeArea 会让背景在安全区裸露 + 滚动可视区被截短
body: SafeArea(
  top: false,
  child: Column(
    children: [..., Expanded(child: ListView(...))],
  ),
),
```

**效果:**
- 背景色填满整个屏幕（含 home indicator 区域），视觉连续
- 滚动到底时末项能完整露出在 home indicator 上方，不被遮挡
- 滚动列表 viewport 占满全屏，可视面积最大化

**例外:** 纯静态页面（无可滚动内容，如登录页、设置项）用整体 `SafeArea` 是 OK 的；但只要页面有 `ListView` / `SingleChildScrollView` / `CustomScrollView` 等滚动 widget，就走上面的"滚动内 padding"做法。

**为什么:**
- `SafeArea` 给 child 加外 padding，会把整个内容区圈在安全区内 → 安全区下方是 Scaffold 背景色裸露，看着像"内容被截掉"
- 滚动列表的 viewport 被限制在安全区内 → 末项最低也只能贴到安全区顶部，浪费了 home indicator 区域的可视面积

---

## 13. 组件使用与 widget 参数优先

**核心规则:** 避免使用**过度封装**的组件——这类封装即使不使用某个属性也会套用对应 Widget 层级，造成 Widget 树加深、rebuild 代价变高。优先用原生组件 `Image` / `Container` / `Text` 等按需组合。

进项目前先扫一遍项目里的基础 UI 封装，评估是否有同类问题。项目特定的禁用组件清单见各项目的 `.claude/rules/`。

**优先用 widget 自身的参数，不要额外包一层 widget:**

很多 Flutter 内建 widget 已经有常用的属性参数（`padding` / `margin` / `alignment` / `decoration` 等），不要再外面套一个等效的 widget。

| 错误（外面套一层） | 正确（用自身参数） |
|---|---|
| `Padding(padding: ..., child: GridView.builder(...))` | `GridView.builder(padding: ..., ...)` |
| `Padding(padding: ..., child: ListView(...))` | `ListView(padding: ..., ...)` |
| `Padding(padding: ..., child: Container(...))` | `Container(padding: ..., ...)` |
| `Center(child: Container(alignment: ...))` | `Container(alignment: Alignment.center, ...)` |
| `Container(decoration: BoxDecoration(color: ...))` 单纯只为底色 | `ColoredBox(color: ...)` 或 `Container(color: ...)` |

**为什么:** 多套一层 widget 会让 Widget 树加深、rebuild 代价变高、layout 计算多走一遍；直接用参数语义清晰、性能更好。

**判断方法:** 写完想要包 `Padding` / `Center` / `Align` 等之前，先看子 widget 的构造器参数列表——通常已经有同名属性。

**Column / Row 子项之间的间距用自带的 `spacing` 参数，不要在 children 之间塞 `SizedBox`:**

Flutter 3.27 起 `Column` / `Row` / `Flex` 都有 `spacing` 参数（双精度像素值），自动给所有子项之间加同一个间距，不渲染额外的 widget 节点。

| 错误（中间塞 SizedBox） | 正确（用自身 spacing） |
|---|---|
| `Column(children: [A, SizedBox(height: 8), B, SizedBox(height: 8), C])` | `Column(spacing: 8, children: [A, B, C])` |
| `Row(children: [A, SizedBox(width: 12), B])` | `Row(spacing: 12, children: [A, B])` |

**为什么:**
- SizedBox 本身就是一个 RenderObject，n 个子项要塞 n-1 个 SizedBox，Widget 树多一倍节点；而 `spacing` 是 RenderFlex 内部直接计算偏移，零额外节点
- 间距需要统一调整时，改一个 `spacing` 数字就行；用 SizedBox 要逐个改，容易漏
- 看代码时 children list 一目了然，不被 SizedBox 噪音打断

**例外:**
- **每两项之间间距不一样**（例如：A↔B 间 8、B↔C 间 24）→ 这种"非均匀间距"还是用 SizedBox 显式插入
- **某项需要可变间距**（如条件出现/消失，spacer 也要跟着变）→ 用 SizedBox 或 Spacer
- **Row 里需要"挤开"两端**（一边靠左一边靠右）→ 用 `Spacer()` 或 `mainAxisAlignment: spaceBetween`，不是 `spacing`

---

## 14. 图标来源规范（铁律）

**核心规则:** **永远不要使用 Flutter/Material 系统自带的 icon**（如 `Icons.chevron_left`、`Icons.arrow_back`、`Icons.menu`、`Icons.close` 等），一律使用**用户/设计稿提供的图片资源**（SVG / PNG / WebP）。

**适用范围:** 所有页面 icon、TabBar icon、按钮内 icon、列表箭头、空态图、toast 图标等等。

**关于 AppBar 返回按钮:** 通常由项目主题（`ThemeData.actionIconTheme.backButtonIconBuilder`）全局接管为自家 SVG，业务代码**无需也不应介入**（详见第 15 节「AppBar 规范」）。

**没有图片资源时的处理:**
- **立即停下来问用户**，要求提供对应的设计资源
- **严禁擅自 fallback 到系统 icon**（包括"先用 Icons.xxx 占位、后面再换"这种临时做法，也不允许）
- 用户未给图就直接用系统 icon = 违规

**唯一例外:** 仅在 Dart 代码中为占位 widget 写测试样例时可用系统 icon，但不能出现在任何实际业务页面 / 通用组件 / 生产代码路径上。

**为什么:**
- 设计稿里的 icon 和 Material icon 视觉差异明显（粗细、圆角、尖端样式都不一样），擅自替换会让整个 App 看起来像半成品
- 过往踩过的坑：为了"省事"用了系统箭头，后续返工时所有页面都要改一遍

---

## 15. AppBar 规范（铁律）

**核心规则:** 业务页面**必须**使用 Flutter 系统 `AppBar`（`Scaffold(appBar: AppBar(...))`），**严禁**主动设置 `leading` / `automaticallyImplyLeading: false` 或用 `PreferredSize` 自己拼标题栏。业务代码只允许设置 `title`，以及（如有需要）`actions`（右侧操作按钮）。

**正确写法:**
```dart
Scaffold(
  appBar: AppBar(title: const Text('页面标题')),
  body: ...,
)
```

**错误写法:**
```dart
// ❌ 不要自己塞 leading
appBar: AppBar(leading: IconButton(...), title: ...)

// ❌ 不要禁掉自动 leading
appBar: AppBar(automaticallyImplyLeading: false, ...)

// ❌ 不要自己用 PreferredSize 重建标题栏
appBar: PreferredSize(preferredSize: Size.fromHeight(40), child: Container(...))
```

**为什么:** 项目通常会在主题层（`ThemeData.actionIconTheme.backButtonIconBuilder`）全局接管 AppBar 返回图标为自家 SVG，Flutter `AppBar` 的自动 leading 会读取这个 builder，所以**默认就显示自家图标**——业务代码不需要也不应该再介入。重复指定容易跑偏：用错图标、视觉不一致、漏掉个别页面、多出冗余资源。具体 builder 配置 / 图标资源路径见各项目 CLAUDE.md。

**特殊场景:**
- 右侧操作按钮（搜索、更多）→ 用 `AppBar.actions: [...]`，允许（不跟 leading 冲突）
- 全屏弹出页想用 "×" 代替返回箭头 → 改用全屏 dialog 或 `ModalBottomSheet`，不要在 `AppBar` 里自定义 leading
- 真有自定义 leading 的需求 → **停下来跟用户讨论**，不要擅自破例

---

## 16. 本地存储（强制）

**统一使用 `GetStorage`，禁止 `SharedPreferences`。**

- `main()` 首行必须 `await GetStorage.init();` 才能 `runApp`
- 按模块拆 container 避免 key 撞车：`GetStorage('user')` / `GetStorage('settings')` / `GetStorage()`（默认）
- 同一模块内部的 key 用字符串常量集中管理，禁止硬编码

---

## 17. 网络请求

### 响应处理
- 使用 `.then()` 处理响应，**不要用 try-catch**
- `resp.success` 为 false 时调用 `Toast.show(resp.message)` 显示错误提示（错误文案字段名以项目 `BaseResp` 定义为准，有的项目叫 `errMsg`）
- **接口请求失败必须给用户可见的提示**，不允许静默失败

### 请求参数
- 所有请求类型（GET/POST/PUT/DELETE）统一用 `parameters` 方法返回参数
- **禁止**使用 `toJson`（`toJson` 是响应数据类用的）

---

## 18. 接口请求与应答命名

### 请求类命名
- `XxxReq`（**不使用** `XxxResp` 这种命名习惯）

### 响应数据类分两类处理

**单接口专用响应**（该数据结构只被这一个接口使用）：
- 命名 `XxxData`
- **必须与 `XxxReq` 放在同一个文件**

**跨接口/跨模块复用的领域实体**（如 `User` / `Message` / `Conversation`，会被多个接口返回或被 WebSocket 事件等非 HTTP 路径使用）：
- 放独立的 `models/` 目录
- 保留业务命名，**不强制加 `Data` 后缀**

### 示例
- 单接口专用：`check_phone_exist_req.dart` 包含 `CheckPhoneExistReq` 和 `CheckPhoneExistData`
- 领域实体：`api/models/message.dart` 定义 `Message`（被 `ListMessagesReq` 返回，也被 WebSocket 推送事件复用）

---

## 19. 资源文件管理

### 格式选择（新项目默认规则）

- **图标类资源（icon / logo / 状态图 / 纯 UI 矢量）** → 优先用 **SVG + `flutter_svg`**
  - SVG 是矢量，任意屏幕密度都清晰，**一套文件适配 2x/3x 全部设备**，不用准备多套
  - 单色图标通过 `colorFilter` 参数动态着色（比如 nav bar 选中态切换主色），一个 SVG 管两种状态
  - 彩色/渐变图标直接显示原色
- **图片类资源（照片、插图、复杂装饰图、截图）** → 用 **WebP / PNG 的 2x/3x**

**判断依据:**
- 简单路径、少于 10 个颜色 → SVG
- 照片、复杂装饰、带多段渐变 → WebP/PNG

### SVG 图标着色规范

适用于 nav bar / tab / 按钮 icon 等可切换状态的图标：

- **选中态**：tint 成主色（如 `AppColors.primary`），用 `SvgPicture.asset(..., colorFilter: ColorFilter.mode(...))`
- **未选中态**：保持 SVG **自身的默认颜色**——如果 SVG 本身是灰色就显示灰色，如果是彩色就保持彩色，不要强行 tint 成灰
- **规则简化:** 只有当前选中项变色成主色，其他项保留 SVG 原本的颜色

### PNG / WebP 添加流程

- 只需要 2.0x 和 3.0x 版本（**不需要** 1x）
- 放到对应目录后**必须在 pubspec.yaml 中单独声明该图片**（如 `- assets/images/new_image.png`）
- 执行 `flutter pub get`

### 原生迁移规范

- 迁移原生已有功能到 Flutter 时，**必须使用与原生一致的图片资源**
- 从原生项目中找到对应图片，把 2.0x 和 3.0x 复制到 Flutter 项目
- 使用 `Image.asset` / `SvgPicture.asset` 加载，**不要用 `Icon` widget** 或 Material 图标替代（见第 14 节）

---

## 20. 日志打印

统一使用 `debugPrint`，不要用 `print` 或 `log()`。`debugPrint` 在 release build 自动被裁剪，不会泄露到生产环境。

---

## 21. 第三方库依赖鸿蒙适配规范

**核心规则:** 项目是鸿蒙 (OHOS) Flutter 项目时（`.fvmrc` 或 `.fvm/fvm_config.json` 版本号含 `-ohos-`），引入任何**带原生实现**的第三方 plugin（如 `path_provider` / `connectivity_plus` / `package_info_plus` / `device_info_plus` / `permission_handler` 等），**必须在主工程根 `pubspec.yaml` 的 `dependency_overrides:` 里把它指向 OpenHarmony-SIG 的 fork**。

**写法（以 `package_info_plus` 为例）:**

```yaml
dependencies:
  package_info_plus: ^8.1.2

dependency_overrides:
  package_info_plus:
    git:
      url: https://gitee.com/openharmony-sig/flutter_plus_plugins.git
      path: packages/package_info_plus/package_info_plus
```

**OpenHarmony-SIG 常用 plugin 仓库索引:**

| 包类型 | 仓库地址 |
|---|---|
| `path_provider` 等 packages 系 | `https://gitee.com/openharmony-sig/flutter_packages.git` |
| `connectivity_plus` / `device_info_plus` / `package_info_plus` 等 `_plus` 系 | `https://gitee.com/openharmony-sig/flutter_plus_plugins.git` |
| `permission_handler` | `https://gitee.com/openharmony-sig/flutter_permission_handler.git` |

**为什么:** pub.dev 上的官方 plugin 默认只支持 Android/iOS/Web/Desktop，没有 ohos 平台实现。OpenHarmony-SIG 的 fork 在 pubspec 里声明了 ohos 平台并附带 `_ohos` 实现，能让 plugin 在鸿蒙编译通过；不 override，鸿蒙编译会直接报"未实现"或丢失方法通道。

**不需要 override 的情况:** 纯 Dart 包（无原生代码）跨平台天然兼容，例如 `flutter_svg` / `intl` / `crypto` / `dio` / `get` / `get_storage` 等。判断方法：plugin 仓库里有 `android/` `ios/` 目录的就是带原生实现的，需要 override。

**子包写法:** business / foundation 子包的 `pubspec.yaml` **只写普通约束**（如 `package_info_plus: ^8.1.2`），**不需要重复 `dependency_overrides`**——pub 工具会让主工程的 override 作用于整个依赖图，包括 `path:` 依赖的子包。子包重复写反而会造成版本冲突。

**新增第三方依赖时的检查清单:**
1. 这个包带原生代码吗？（看仓库有没有 `android/` `ios/`）
2. 带 → OpenHarmony-SIG 是否有对应 fork？（先查上表，再去 gitee 搜）
3. 有 fork → 在主工程根 `pubspec.yaml` 加 `dependency_overrides`
4. 没 fork → 停下来跟用户讨论替代方案，不要硬上

---

## 22. fvm + 鸿蒙 Flutter SDK 命令执行规范

**核心规则:** 项目使用 `fvm` 管理 Flutter 版本、且 SDK 是鸿蒙 (OHOS) 版本时（如 `3.27.x-ohos-*`），**每次执行 `fvm flutter ...` 命令都必须在前面加 `yes |` 管道**，自动回答 OHOS SDK 弹出的 `Do you want to continue? · yes` 确认。

**错误写法（会无限卡死）:**
```bash
fvm flutter pub get           # ❌ 卡在确认提示
fvm flutter build             # ❌ 同样
fvm flutter test              # ❌ 同样
```

**正确写法:**
```bash
yes | fvm flutter pub get
yes | fvm flutter test
yes | fvm flutter build apk
yes | fvm flutter run
```

**判断项目是否使用鸿蒙 SDK:**
- 查 `.fvmrc` 或 `.fvm/fvm_config.json`，版本号含 `-ohos-` → 鸿蒙 SDK → 必须加 `yes |`
- 没有 `-ohos-` 或没用 fvm → 正常执行

**适用范围:** 所有 fvm 相关的 flutter/dart 命令（pub get、test、build、run、analyze 等）。

**原因:** 鸿蒙 Flutter SDK 每次调用都会弹一次兼容性确认，不提供自动确认参数。非交互环境（如 Claude Code 的 Bash 工具）stdin 被接到 /dev/null，确认提示永远等不到输入，进程就挂起了。

---

## 23. Flutter 测试栈

- **单元测试**：`package:test` + `flutter_test`（对工具函数、Controller 逻辑、API 数据清洗编写单元测试）
- **Widget 测试**：`flutter_test` 的 `testWidgets`
- **Mock**：`mocktail`（不推荐 `mockito`，注解生成太重）
- **E2E / 集成测试**：`integration_test`（官方包）
- **TDD 流程**：有业务逻辑的代码必须先写失败测试 → 写最小实现 → 测试通过
- **测试聚合入口**：每个含测试的 package 必须有 `test/<pkg_name>_suite.dart` 聚合本包测试，供顶层 E2E 调用（业务包细则见 `flutter-business-layer.md` 第 10 节，bizkit 见 `flutter-foundation-layer.md` 第 7 节）
