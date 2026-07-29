---
paths:
  - "**/*.java"
  - "**/pom.xml"
---

# Java 后端通用技术规范

本文件规定所有 Java 后端项目的**整体结构**、**技术选型**和**编码规范**。创建新项目、新模块、新文件必须严格遵循本文件约束，不得临时发挥。

遇到本规范覆盖不到的新场景时，**先停下来与用户讨论迭代规则本身**，禁止在项目里临时发挥。

**默认技术栈**：Java 21 + Spring Boot 3.x + Maven + MySQL + Redis

以上是新建 Java 后端项目的**默认选型**，不是硬性约束。项目可以偏离，条件是**在项目 spec 或项目 CLAUDE.md 中写明偏离项与理由**——偏离不需要事先请示，但必须留下书面依据，否则视为临时发挥。

典型的正当偏离理由：所选框架对运行时版本有硬性要求（如 Spring Authorization Server 自 7.0 起并入 Spring Security 7，只能配 Spring Boot 4.x）；开发机既有 JDK 版本已满足需求且升级会波及机器上其他项目；服务不需要缓存或消息中间件因而不引入 Redis。

**配套分片**：
- `java-backend-business-layer.md` — 业务层细则
- `java-backend-foundation-layer.md` — 基础层细则

---

## 1. 项目整体结构（强制）

所有 Java 后端项目统一使用两层结构：**业务层 `business_packages/` + 基础层 `foundation_packages/`**。

### 完整目录树

```
<project_root>/
├── pom.xml                                    # 父 POM（聚合 + 依赖管理 + Enforcer）
├── bootstrap/                                 # 启动工程
│   └── src/main/java/.../Application.java
│
├── business_packages/                         # ── 业务层（按 DDD 业务领域划分）
│   ├── <proj>-<domain-a>-api/                 # 领域 A 对内契约（接口 + DTO + 事件）
│   ├── <proj>-<domain-a>-core/                # 领域 A 实现
│   ├── <proj>-<domain-b>-api/
│   ├── <proj>-<domain-b>-core/
│   └── ...
│
└── foundation_packages/                       # ── 基础层（8 个包）
    ├── <proj>-common-error/                   # 异常 + 错误码（强制）
    ├── <proj>-common-web/                     # HTTP 响应封装（强制）
    ├── <proj>-common-auth/                    # 鉴权（强制）
    ├── <proj>-common-cache/                   # Redis 封装（强制）
    ├── <proj>-common-storage/                 # 对象存储（强制）
    ├── <proj>-common-util/                    # 通用工具（强制）
    ├── <proj>-common-test/                    # 测试基础（强制）
    └── <proj>-common-ws/                      # WebSocket（按需）
```

### 依赖方向（强制）

| 关系 | 允许 |
|------|------|
| `business_packages` → `foundation_packages` | ✅ |
| `foundation_packages` 之间 | ✅ 可互依（避免循环） |
| `business_packages` 之间 | ❌ **禁止直接 import** |
| `business_packages` → 其他业务的 `-api` | ✅ 通过契约调用 |
| `foundation_packages` → `business_packages` | ❌ **严禁** |

业务模块间通信只能走两种机制：

- **同步查询**：`@Autowired <Domain>Api`（依赖对方 `-api` 模块）
- **通知扩散**：Spring 领域事件（`ApplicationEventPublisher` + `@TransactionalEventListener`）

### 结构不变性声明

- 日常开发、新建模块、新建项目**严格按**此目录树组织
- 遇规则未覆盖场景**先更新规则再落地项目**
- 新业务领域**一律** `-api` + `-core` 双模块
- 新基础能力按 `java-backend-foundation-layer.md` 的清单命名

### 例外：单一职责基础设施服务可用单模块

双层结构是为**多业务域的业务系统**设计的。以下类型的服务**允许**采用单 Maven 模块 + 扁平包结构：

- 只有一个业务领域，且该领域不会随业务增长分裂出新领域
- 用不到基础层 8 个包中的多数能力
- 对外只提供一种协议入口

**判定标准**：如果套用双层结构会产出 3 个以上几乎为空的模块，即属于本例外。典型例子：统一认证中心、文件网关、短链服务、定时任务调度器。

**采用例外的条件**：

1. 在项目 spec 中写明「本项目不采用 `business_packages/` + `foundation_packages/` 结构」及具体理由；
2. 单模块内部**仍按职责分包**（如 `user/` `password/` `registration/` `config/` `web/`），一个包一个明确职责；
3. **依赖方向仍然单向**——领域包不得反向依赖 Web 层或配置层；
4. 一旦该服务长出第二个业务领域，就要重新评估是否升级为双层结构。

不满足上述条件而擅自用单模块，仍属违规。

---

## 2. 包命名规范（强制）

所有包**强制统一项目短名前缀** `<proj>-`。前缀值每个项目定，但同一项目内**必须一致**。

| 类别 | 模式 | 示例 |
|------|------|------|
| 业务领域契约模块 | `<proj>-<domain>-api` | `<proj>-user-api` |
| 业务领域实现模块 | `<proj>-<domain>-core` | `<proj>-user-core` |
| 基础能力模块 | `<proj>-common-<role>` | `<proj>-common-error` |
| Java 包根 | `com.<proj>.<domain>` / `com.<proj>.common.<role>` | `com.myapp.user` |
| 启动工程 | `<proj>-bootstrap` 或 `<proj>-server` | — |

---

## 3. 业务领域模块（`-api` + `-core` 双模块）

每个业务领域必须由 2 个 Maven 子模块构成。**细则见 `java-backend-business-layer.md`**。

**核心原则**：
- `-api` 模块：**只有接口 + DTO + 事件定义**，无实现
- `-core` 模块：实现层，对外暴露 HTTP 入口（Controller）+ Java 接口入口（ApiImpl）
- `-core` 内部分 4 个子包：`web/` + `internal/` + `api/` + `event/`
- **一个领域只有一个主 `<Domain>Api` 接口**（接口职责太多说明领域划分过粗）

---

## 4. 模块间边界守护（强制）

### 第一层：Maven Enforcer（POM 层）

在父 POM 配置 `maven-enforcer-plugin` 的 `banned-dependencies` 规则：

```xml
<rule implementation="org.apache.maven.enforcer.rules.dependency.BannedDependencies">
  <excludes>
    <exclude>com.<proj>:*-core</exclude>      <!-- 任何 -core 模块不允许依赖其他 -core -->
  </excludes>
  <includes>
    <include>com.<proj>:${project.artifactId}</include>  <!-- 自己的 -core 除外 -->
  </includes>
</rule>
```

违规时 `mvn validate` 阶段即失败。

### 第二层：ArchUnit（代码层 CI）

`common-test` 提供 ArchUnit 基类，CI 跑测试扫依赖图：

```java
@AnalyzeClasses(packages = "com.<proj>")
class ArchitectureTest {
    @ArchTest
    static final ArchRule business_core_modules_must_not_depend_on_each_other =
        noClasses().that().resideInAPackage("..<domain>.core..")
            .should().dependOnClassesThat().resideInAPackage("..<other-domain>.core..");
}
```

---

## 5. 业务异常设计（强制）

### 5.1 全项目唯一 `BusinessException`

**不拆子异常类**。所有业务失败都抛 `BusinessException`：

```java
public class BusinessException extends RuntimeException {
    @Getter private final ErrCode errCode;

    public BusinessException(ErrCode errCode) {
        super(errCode.getDefaultMessage());
        this.errCode = errCode;
    }

    public BusinessException(ErrCode errCode, String overrideMessage) {
        super(overrideMessage);
        this.errCode = errCode;
    }
}
```

### 5.2 `ErrCode` 接口 + 按模块拆 enum

```java
// common-error/ErrCode.java
public interface ErrCode {
    int getCode();
    String getDefaultMessage();
}

// common-error/CommonErrCode.java（400-499 通用码）
@Getter @AllArgsConstructor
public enum CommonErrCode implements ErrCode {
    TOKEN_EXPIRED(400, "登录态过期"),
    KICKED_OFFLINE(405, "账号被踢下线"),
    PARAM_INVALID(410, "参数错误"),
    FORBIDDEN(403, "无权限"),
    NOT_FOUND(404, "资源不存在"),
    ;
    private final int code;
    private final String defaultMessage;
}

// <proj>-user-core/internal/UserErrCode.java（1000-1999）
public enum UserErrCode implements ErrCode {
    PHONE_ALREADY_REGISTERED(1001, "手机号已注册"),
    AVATAR_INVALID_FORMAT(1002, "头像格式不支持"),
    ...;
}
```

### 5.3 code 区间约定

基础层 `common-error` 维护一张登记表（`README.md` 或 `ERROR_CODE_REGISTRY.md`）：

```
400-499    通用错误（CommonErrCode）
1000-1999  <domain-a>
2000-2999  <domain-b>
...
9000-9999  预留
```

**新模块申请 code 区间前必须更新登记表**。

### 5.4 启动时冲突扫描（硬约束）

`common-error` 提供 `ErrCodeConflictDetector`：启动时扫所有实现 `ErrCode` 的 enum，发现 code 冲突**直接启动失败**。

```java
@Component
@RequiredArgsConstructor
public class ErrCodeConflictDetector implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) {
        Map<Integer, String> seen = new HashMap<>();
        for (Class<? extends ErrCode> clazz : findAllErrCodeEnums()) {
            if (!clazz.isEnum()) continue;
            for (ErrCode code : clazz.getEnumConstants()) {
                String location = clazz.getSimpleName() + "." + ((Enum<?>) code).name();
                String existing = seen.put(code.getCode(), location);
                if (existing != null) {
                    throw new IllegalStateException(String.format(
                        "ErrCode 冲突：code=%d 被 %s 和 %s 同时定义",
                        code.getCode(), existing, location));
                }
            }
        }
    }
}
```

### 5.5 统一响应体 `BaseResp<T>`

由 `common-web` 提供：

```java
@Data
public class BaseResp<T> {
    public static final int SUCCESS_CODE = 0;
    public static final String SUCCESS_MESSAGE = "ok";

    private boolean success;    // 业务成败 —— app/web 端直接判断这个字段
    private int code;           // 失败时的错误类型区分（成功时固定为 0）
    private String message;     // 展示文案
    private T data;             // 业务数据

    public static <T> BaseResp<T> success(T data) {
        BaseResp<T> r = new BaseResp<>();
        r.setSuccess(true);
        r.setCode(SUCCESS_CODE);
        r.setMessage(SUCCESS_MESSAGE);
        r.setData(data);
        return r;
    }

    public static <T> BaseResp<T> failed(int code, String message) {
        BaseResp<T> r = new BaseResp<>();
        r.setSuccess(false);
        r.setCode(code);
        r.setMessage(message);
        return r;
    }
}
```

**字段语义**：
- `success`：**业务是否成功**，app / web 端直接判断，不必看 code。与 app 侧 `BaseResp.success` **同构**
- `code`：仅在**失败时区分错误类型**；成功固定为 `0`；任何 `ErrCode` 实现**不得**使用 `0`
- `message`：展示文案，失败时可直接 Toast
- `data`：业务数据，失败时为 `null`

### 5.6 全局异常处理器（common-web）

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(BusinessException.class)
    public BaseResp<Void> onBusinessException(BusinessException e) {
        return BaseResp.failed(e.getErrCode().getCode(), e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public BaseResp<Void> onValidation(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getAllErrors().get(0).getDefaultMessage();
        return BaseResp.failed(CommonErrCode.PARAM_INVALID.getCode(), msg);
    }

    @ExceptionHandler(Exception.class)
    public BaseResp<Void> onUnknown(Exception e) {
        log.error("unhandled exception", e);
        return BaseResp.failed(500, "服务器错误，请稍后重试");
    }
}
```

### 5.7 HTTP 响应契约

HTTP 层永远 200（除非通信层错），业务成败看 body `success`：

```json
// 成功
{ "success": true,  "code": 0,    "message": "ok",           "data": { ... } }

// 通用错误
{ "success": false, "code": 400,  "message": "登录态过期",    "data": null }

// 业务错误
{ "success": false, "code": 1001, "message": "手机号已注册",  "data": null }
```

---

## 6. 领域事件规范（强制）

- **事件类位置**：**发布方**的 `-api/event/`（作为对外契约的一部分，订阅方只需依赖发布方的 `-api` 即可订阅）
- **命名**：`<Domain><动作过去式>Event`（例：`UserRegisteredEvent`、`MessageSentEvent`）—— 表达"已发生的事实"
- **类型**：**Java 21 `record`**（不可变 + 简洁）
- **发布**：`@Autowired ApplicationEventPublisher`，Service 里直接 `events.publishEvent(new XxxEvent(...))`
- **订阅默认**：`@Async @TransactionalEventListener(phase = AFTER_COMMIT)`（**事务提交后异步触发**，避免"事件发了但事务回滚"的状态不一致）
- **同步订阅例外**：罕见场景（如审计必须在事务内落库）可用普通 `@EventListener`，但**必须在代码注释说明理由**

```java
// 事件定义（-api/event/）
public record UserRegisteredEvent(Long userId, String phone, Instant registeredAt) {}

// 订阅（-core/event/）
@Component
public class WelcomeMailListener {
    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onUserRegistered(UserRegisteredEvent event) {
        mailService.sendWelcome(event.userId());
    }
}
```

---

## 7. 测试规范（强制）

### 7.1 分层测试工具

| 测试对象 | 工具 | 文件后缀 | 速度 |
|---------|------|---------|------|
| Service / ApiImpl / Listener 业务逻辑 | 纯 **Mockito 单测** | `*Test` | ⚡⚡⚡ |
| Controller | `@WebMvcTest`（mock Service） | `*IT` | ⚡⚡ |
| Repository 自定义查询 | `@DataJpaTest`（H2） | `*IT` | ⚡⚡ |
| 端到端关键路径 | `@SpringBootTest`（完整上下文 + H2） | `*IT` | ⚡ |

### 7.2 Maven 插件分工

- `maven-surefire-plugin`：默认跑 `*Test`（每次 `mvn test` 都跑，快）
- `maven-failsafe-plugin`：默认跑 `*IT`（`mvn verify` / CI 跑，慢）

**不需要**聚合测试入口（Maven 自动发现，不像 Flutter 需要 `_suite.dart`）。

### 7.3 Mock 工具

**Mockito**（Spring Boot Test Starter 自带），不引入其他 mock 库。

### 7.4 端到端测试数据库

- **默认 H2 内存库**
- 关键路径（H2 不支持的语法/索引）补 **Testcontainers + 真实 MySQL**

### 7.5 Object Mother 强制

**Entity / Domain Object** 在测试中使用时**必须**通过对应的 `<Domain>TestFixtures` 类构造。**简单 DTO 不强制**。详见 `java-backend-business-layer.md`。

### 7.6 TDD 铁律

遵守全局 CLAUDE.md 的 **TDD 铁律**。有业务逻辑的代码必须先写失败测试 → 写最小实现 → 测试通过。

---

## 8. 通用命名规范汇总

### 8.1 类命名

| 类型 | 位置 | 模式 | 示例 |
|------|------|------|------|
| 对内 API 接口 | `-api/` 顶层 | `<Domain>Api` | `UserApi` |
| 对内 API 实现 | `-core/api/` | `<Domain>ApiImpl` | `UserApiImpl` |
| HTTP Controller | `-core/web/` | `<Domain>Controller` | `UserController` |
| 业务 Service | `-core/internal/` | `<Domain><Action>Service`（按动作拆） | `UserRegisterService` |
| Repository | `-core/internal/` | `<Domain>Repository` | `UserRepository` |
| JPA Entity | `-core/internal/` | `<Domain>Entity`（**带后缀**） | `UserEntity` |
| HTTP 请求 DTO | `-core/web/` | `<Action>Req` | `CreateUserReq` |
| HTTP 单接口响应 | `-core/web/`（与 Req 同文件） | `<Action>Data` | `LoginData` |
| HTTP 跨接口复用模型 | `-core/web/` | 业务描述名 | `UserProfile` |
| Java API DTO | `-api/dto/` | `<Domain>Dto` / `<Domain><描述>Dto` | `UserDto`, `UserSummaryDto` |
| 领域事件 | `-api/event/` | `<Domain><动作过去式>Event` (record) | `UserRegisteredEvent` |
| 事件监听器 | `-core/event/` | `<EventType>Listener` | `UserRegisteredListener` |
| 错误码 enum | `-core/internal/` 或 `common-error/` | `<Domain>ErrCode` | `UserErrCode` |
| 错误 enum 值 | 同上 | UPPER_SNAKE_CASE | `PHONE_ALREADY_REGISTERED` |

### 8.2 测试 / 工具 / 配置

| 类型 | 模式 | 示例 |
|------|------|------|
| 单元测试 | `<ClassUnderTest>Test` | `UserRegisterServiceTest` |
| 集成测试 | `<ClassUnderTest>IT` | `UserControllerIT` |
| Object Mother | `<Domain>TestFixtures` | `UserTestFixtures` |
| 工具类 | `<Role>Util`（单数） | `DateUtil`, `JsonUtil` |
| Spring 配置类 | `<Role>Config` | `RedisConfig` |
| 常量类 | `<Role>Constants` | `MessageConstants` |

---

## 9. 典型代码模板

### 9.1 Service（业务编排）

```java
@Service
@RequiredArgsConstructor
public class UserRegisterService {
    private final UserRepository repo;
    private final BCryptPasswordEncoder passwordEncoder;
    private final ApplicationEventPublisher events;

    @Transactional
    public Long register(String phone, String password, String nickname) {
        if (repo.existsByPhone(phone)) {
            throw new BusinessException(UserErrCode.PHONE_ALREADY_REGISTERED);
        }
        UserEntity user = new UserEntity();
        user.setPhone(phone);
        user.setNickname(nickname);
        user.setPasswordHash(passwordEncoder.encode(password));
        user.setCreatedAt(Instant.now());
        repo.save(user);

        events.publishEvent(new UserRegisteredEvent(user.getId(), phone, user.getCreatedAt()));
        return user.getId();
    }
}
```

### 9.2 ApiImpl（对内接口实现）

```java
@Service
@RequiredArgsConstructor
public class UserApiImpl implements UserApi {
    private final UserRepository repo;

    @Override
    public UserDto findById(Long userId) {
        return repo.findById(userId)
                .map(e -> new UserDto(e.getId(), e.getPhone(), e.getNickname(), e.getAvatarUrl()))
                .orElse(null);
    }

    @Override
    public boolean existsByPhone(String phone) {
        return repo.existsByPhone(phone);
    }
}
```

### 9.3 跨模块调用

```java
@Service
@RequiredArgsConstructor
public class MessageSendService {
    private final RelationApi relationApi;     // 来自 <proj>-relation-api
    private final UserApi userApi;             // 来自 <proj>-user-api
    private final MessageRepository repo;

    @Transactional
    public Long send(Long fromId, Long toId, String content) {
        if (!relationApi.isFriend(fromId, toId)) {
            throw new BusinessException(MessageErrCode.NOT_FRIEND);
        }
        // ...
    }
}
```

### 9.4 Mockito 单测

```java
@ExtendWith(MockitoExtension.class)
class UserRegisterServiceTest {
    @Mock UserRepository repo;
    @Mock BCryptPasswordEncoder passwordEncoder;
    @Mock ApplicationEventPublisher events;
    @InjectMocks UserRegisterService service;

    @Test
    void register_shouldFailIfPhoneAlreadyRegistered() {
        when(repo.existsByPhone("13800138000")).thenReturn(true);

        BusinessException ex = assertThrows(BusinessException.class,
            () -> service.register("13800138000", "pwd", "昵称"));

        assertEquals(UserErrCode.PHONE_ALREADY_REGISTERED, ex.getErrCode());
        verify(repo, never()).save(any());
        verify(events, never()).publishEvent(any());
    }
}
```
