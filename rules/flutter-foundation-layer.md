---
paths:
  - "**/foundation_packages/**/*.dart"
---

# Flutter 基础层（`foundation_packages/`）架构规则

本文件规定 Flutter 项目**基础层**的包构成和每个包的内部规则。整体目录树和技术规范见 `~/.claude/rules/flutter.md`。

---

## 1. 基础层构成

```
foundation_packages/
├── <proj>_uikit/           # 公共 UI 组件（强制）
├── <proj>_network/         # 网络库（强制）
├── <proj>_routes/          # 路由名称表（强制）
├── <proj>_user/            # 用户中心（强制）
├── <proj>_bizkit/          # 公共业务组件（强制）
├── <proj>_util/            # 工具类（强制）
└── <proj>_test_helpers/    # 测试辅助（按需，dev-only 依赖，不进生产 APK）— 详见 §9
```

前 6 个**强制必有**，第 7 个 `_test_helpers` **可选**。遇到不在这些包职责范围内的场景，先停下来与用户讨论迭代规则本身。

**重要**：`_test_helpers` 跟前 6 个生产包性质不同——它是 dev-only 测试辅助包，消费方**必须**用 `dev_dependencies` 引用（详见 §9）。否则 mocktail 等测试库会进生产 APK。

---

## 2. 依赖方向（强制）

- `business_packages` → `foundation_packages` ✓
- `foundation_packages` 之间可以互相依赖 ✓
- `business_packages` 之间**禁止**互相依赖 ✗
- 业务模块需要共享代码时，**下沉到基础层**

---

## 3. `<proj>_uikit`

**职责**：项目内通用 UI 组件（Button / Input / Theme / Color / 各种基础 Widget）。

**组织**：
- 初始阶段文件**全部扁平**放在 `lib/src/` 下
- 同一类组件的文件超过 2~3 个时，再拆子目录（如 `button/primary_button.dart` + `button/ghost_button.dart`）
- 不要提前按类型建空文件夹

---

## 4. `<proj>_network`

**职责**：HTTP + WebSocket 网络封装 + 请求/响应基类。

**组织**：
```
lib/src/
├── http_client.dart       # HTTP get / post / put / delete 封装
├── base_req.dart          # 业务层请求基类
├── base_resp.dart         # 统一应答，data 走泛型
├── websocket_client.dart  # WebSocket 通用客户端（连接/心跳/重连）
└── ws_state.dart          # WsState enum
```

**HTTP 使用约束**：
- 业务层的请求类都继承 `BaseReq`
- 业务层**不用封装**自己的响应基类，直接用 `BaseResp<T>`，`T` 是业务层声明好的应答数据模型
- 业务层拿到 `BaseResp` 后先判断 `success`，true 就直接取 `resp.data`（泛型里已指定好类型）
- 请求参数一律走 `parameters` 方法返回，禁止用 `toJson`
- HTTP 调用复用统一 `HttpClient` 封装；纯转发入口可按项目惯例提供静态门面，持有配置、拦截器或会话状态的客户端按实例生命周期管理（见 CLAUDE.md「static 与实例设计」）。

**WebSocket 使用约束**：
- `WebSocketClient` 暴露原始字符串流 [messages]（`Stream<String>`），**不解析任何业务协议**
- 业务层在 `WebSocketClient` 之上加**协议适配器**（如 `ChatWsService`），适配器负责：
  - 订阅客户端的 `messages` 流
  - jsonDecode + 业务事件 parse（如 `ChatWsEvent.parse`）
  - 暴露业务级 typed Stream（如 `Stream<ChatWsEvent>`）
  - 业务方法（如 `send` / `ack`）调用客户端 `send` 时自己 jsonEncode
- `WebSocketClient` 的连接、心跳、重连和订阅状态按实例管理并明确关闭时机；不强制提升为 static 全局状态，客户端的获取方式遵循项目现有依赖管理。
- ping 帧格式硬编码在 `WebSocketClient` 内部（项目协议约定 `{"type":"ping"}`）；server 必须按这个 type 处理

---

## 5. `<proj>_routes`

**职责**：项目级**跨业务模块**的路由名称集中表。

**组织**：
```
lib/<proj>_routes.dart    # 单文件，全是静态字符串常量
```

**使用约束**：
- 文件内**只放 `static const String`**，不放其他任何东西
- **判定标准**：只有需要被其他业务模块跳转的页面才在这里声明路由名 + 注册到对应模块的 `_routes.dart` 中。模块内部跳转的页面**不声明**，保持路由表最少化
- 业务模块间跳转通过 `Get.toNamed(<Proj>Routes.xxx)`，路由名从本文件取
- 业务模块内部跳转**不需要**注册到本文件，直接 `Get.to(() => XxxPage())`
- 完整规则见 `~/.claude/rules/flutter-business-layer.md` 第 9 节

---

## 6. `<proj>_user`（用户中心）

**职责**：统一管理当前用户数据（token / 账号 / id / 登录态 / 用户信息），含本地缓存。

### 目录组织

```
lib/src/
├── api/
│   ├── <proj>_user_api.dart
│   ├── req/
│   │   ├── login_req.dart
│   │   └── ...
│   └── models/
├── models/                  # 业务数据模型
│   ├── user.dart
│   ├── profile.dart
│   └── setting.dart
├── local/
│   └── user_cache.dart      # 封装 GetStorage
└── user_center.dart         # 用户中心入口类
```

### UserCenter 关键设计（强制）

- **内存态 + 本地缓存双层**：内存态保证访问速度，本地缓存保证冷启动可用
- **冷启动必须同步读本地**：启动时从 GetStorage 同步读出 token / 用户信息装入内存，**立刻可用**，页面不阻塞
- **异步拉新**：冷启动同步读完后，异步请求服务端拉最新数据，拿到后**同时更新内存 + 本地缓存**
- **`user_cache.dart` 必须封装 GetStorage**，禁止直接暴露 GetStorage 实例给外部

---

## 7. `<proj>_bizkit`（公共业务组件）

**职责**：跨业务模块复用的**业务页面**（如名称模糊搜索、地址选择等）。

**组织**：整体结构**对齐业务模块**，**但无 routes 文件**。

```
<proj>_bizkit/
├── assets/images/
├── lib/
│   ├── <proj>_bizkit.dart   # barrel：直接 export 所有 page 类
│   └── src/
│       ├── api/             # 如有跨业务通用接口
│       ├── feature_a/       # 每个公共业务页面一个文件夹
│       │   ├── feature_a_page.dart
│       │   ├── feature_a_controller.dart
│       │   └── widgets/
│       └── widgets/         # 本包内跨页面共用
└── test/
    ├── <proj>_bizkit_suite.dart
    └── *_test.dart
```

### bizkit 特殊规则（强制）

1. **没有 `_routes.dart` 文件** —— bizkit 页面**不通过路由**使用
2. **`<proj>_bizkit.dart` 直接 export 所有 page 类**：
   ```dart
   // <proj>_bizkit.dart
   export 'src/name_search/name_search_page.dart';
   export 'src/address_picker/address_picker_page.dart';
   ```
   - **只 export page 类**，controller 是内部实现细节，**不 export**
3. 业务模块通过 `Get.to(() => NameSearchPage(...))` **直接传参**调用（类型安全，比 `Get.toNamed + arguments` 好）
4. bizkit 页面的 `Get.put` **强制带 `tag: UniqueKey().toString()`**，避免不同业务并发打开时 controller 实例互相替换。代码模板见 `~/.claude/rules/flutter.md` 第 5 节场景 ③

---

## 8. `<proj>_util`

**职责**：通用工具类（日期处理、字符串处理、加解密、格式校验、系统类扩展等）。

**组织**：
- 初始阶段文件**全部扁平**放在 `lib/src/` 下
- 同一维度工具超过 2~3 个文件时再拆子目录
- 不要提前按维度建空文件夹

---

## 9. `<proj>_test_helpers`（可选 / **dev-only**）

**TL;DR**：不是生产代码包。它的 `dependencies` 含 mocktail 等测试库，消费方**必须**用 `dev_dependencies` 引用，**禁止**写在 `dependencies`——否则测试库会被打进生产 APK。

**职责**：跨业务/基础包共享的测试辅助代码（mock / fake / fixture / 测试工具方法）。

**何时建**：当**多个**包的 `test/` 目录里出现**重复的 mock 类定义**（如 `MockDio`、`FakePathProvider`）时建。单包内部的测试 helper 留在该包的 `test/support/` 即可，不要进 `_test_helpers`。

**关键设计：dev-only 依赖**

`<proj>_test_helpers/lib/` 下的代码会 import `mocktail` / `path_provider_platform_interface` 等测试库——这些是 `_test_helpers` 自己的 `dependencies`（核心职责）。

但**消费方**（其他业务/基础包）必须用 `dev_dependencies` 引用本包：

```yaml
# 消费方 pubspec.yaml
dev_dependencies:
  <proj>_test_helpers:
    path: ../../foundation_packages/<proj>_test_helpers
```

**关键**：dev_dependencies 不会跨包传递到 release build，所以 mocktail 等测试库**只在测试时存在**，不会被打包进生产 APK。

**禁止**：把 `_test_helpers` 写在消费方的 `dependencies`（即便它能跑通），这样会把测试库带进生产。

**目录组织**：扁平放在 `lib/src/` 下，文件超过 2-3 个再拆子目录。
