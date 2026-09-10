# AI漫剧生成系统 - 实现计划（前后端部分）

> **范围说明**：本计划仅覆盖前后端实现，AI引擎（LangChain/Python）部分暂不实现，聊天接口固定返回一串模拟字符串。
>
> **原则**：每一步小粒度、可独立验证，每步末尾附带测试/验证方法。

---

## Phase 1：项目脚手架与基础设施

### Step 1.1 — 创建后端 Maven 项目

- [ ] 在 `F:\ai\aisay\backend` 下用 Maven 初始化 Spring Boot 3.2 项目
- [ ] `pom.xml` 加入依赖：spring-boot-starter-web、spring-boot-starter-security、spring-boot-starter-websocket、mybatis-plus-spring-boot3-starter、mysql-connector-j、jjwt（api/impl/jackson）、spring-boot-starter-data-redis、spring-boot-starter-amqp、knife4j-openapi3-jakarta、lombok、commons-lang3
- [ ] 创建主启动类 `com.aisay.manga.AisayMangaApplication`
- [ ] 创建 `application.yml`：端口 8085，MySQL/Redis/RabbitMQ 连接信息，Knife4j 开关
- [ ] 创建包结构：controller / service / service.impl / repository / entity / dto.request / dto.response / config / utils

**验证**：`mvn compile` 成功，`mvn spring-boot:run` 启动无报错（中间件未就绪时允许 datasource 连接异常，确认启动日志出现即可）

---

### Step 1.2 — 创建前端 Vite + Vue 3 项目

- [ ] 在 `F:\ai\aisay\frontend` 下用 `npm create vite@latest` 初始化 Vue 3 + TypeScript 项目
- [ ] 安装依赖：vue-router、pinia、axios、element-plus、dayjs、markdown-it、sockjs-client、@stomp/stompjs
- [ ] 安装开发依赖：sass
- [ ] 配置 `vite.config.ts`：端口 8080，`/api` 代理到 `http://localhost:8085`，`/ws` 代理到 `ws://localhost:8085`
- [ ] 创建目录结构：views / components/chat / components/story / components/common / stores / api / router / types / styles
- [ ] 创建 `src/main.ts`：挂载 App，注册 Element Plus、Pinia、Vue Router
- [ ] 创建 `src/App.vue`：基础 `<router-view />` 布局
- [ ] 创建 `src/router/index.ts`：空路由表（后续逐步填充）

**验证**：`npm run dev` 启动成功，浏览器访问 `http://localhost:8080` 看到空白页面无报错

---

## Phase 2：数据库初始化

### Step 2.1 — 创建 MySQL 数据库与表结构

- [ ] 在 MySQL 中执行：`CREATE DATABASE aisay_manga CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`
- [ ] 创建用户并授权：`aisay` / `aisay_pass`
- [ ] 编写 `backend/src/main/resources/db/init.sql`，包含以下建表语句：
  - `users`（id, username, email, password_hash, avatar_path, preferences, created_at, updated_at）
  - `chat_sessions`（id, user_id FK, session_key, title, context_data JSON, current_stage, progress_percentage, status, started_at, last_active）
  - `messages`（id, session_id FK, role, content TEXT, metadata JSON, created_at）
  - `stories`（id, user_id FK, title, genre, style, synopsis, full_content LONGTEXT, cover_image_path, status, view_count, like_count, created_at, updated_at）
  - `characters`（id, story_id FK, name, role, description, personality, appearance JSON）
  - `scenes`（id, story_id FK, scene_number, setting, description, visual_elements JSON）
  - `dialogues`（id, scene_id FK, character_id FK, content, `order`）
- [ ] 执行 init.sql 创建所有表

**验证**：连接 MySQL 执行 `SHOW TABLES FROM aisay_manga;` 确认 7 张表全部存在

---

### Step 2.2 — 配置 MyBatis-Plus 连接

- [ ] 在 `application.yml` 中配置 mybatis-plus：mapper-locations、type-aliases-package、全局逻辑删除等
- [ ] 创建 `com.aisay.manga.config.MyBatisPlusConfig`：分页插件、乐观锁插件
- [ ] 创建 `com.aisay.manga.config.RedisConfig`：RedisTemplate 序列化配置

**验证**：启动后端，日志中出现 MyBatis-Plus 和 Redis 连接成功信息

---

## Phase 3：后端 — 实体与数据访问层

### Step 3.1 — 创建所有 Entity 类

- [ ] `User.java`：`@TableName("users")`，字段 id/username/email/passwordHash/avatarPath/preferences/createdAt/updatedAt，使用 `@TableId(type=IdType.AUTO)`
- [ ] `ChatSession.java`：对应 chat_sessions 表，`contextData` 字段用 `@TableField(typeHandler=JacksonTypeHandler.class)`
- [ ] `Message.java`：对应 messages 表
- [ ] `Story.java`：对应 stories 表
- [ ] `Character.java`：对应 characters 表
- [ ] `Scene.java`：对应 scenes 表
- [ ] `Dialogue.java`：对应 dialogues 表
- [ ] 所有 Entity 使用 Lombok `@Data` + `@NoArgsConstructor` + `@AllArgsConstructor`

**验证**：`mvn compile` 通过

---

### Step 3.2 — 创建 Mapper 接口

- [ ] `UserMapper.java`：继承 `BaseMapper<User>`
- [ ] `ChatSessionMapper.java`：继承 `BaseMapper<ChatSession>`，添加 `@Select` 按 userId + status 查询
- [ ] `MessageMapper.java`：继承 `BaseMapper<Message>`，添加按 sessionId + 时间排序查询
- [ ] `StoryMapper.java`：继承 `BaseMapper<Story>`，添加按 userId 分页查询
- [ ] `CharacterMapper.java`：继承 `BaseMapper<Character>`
- [ ] `SceneMapper.java`：继承 `BaseMapper<Scene>`
- [ ] `DialogueMapper.java`：继承 `BaseMapper<Dialogue>`
- [ ] 在主启动类加 `@MapperScan("com.aisay.manga.repository")`

**验证**：编写一个简单的 `UserMapperTest`（使用 `@SpringBootTest` + H2 内存库 或 MySQL），执行 insert + select 通过

---

## Phase 4：后端 — DTO 层

### Step 4.1 — 创建请求 DTO

- [ ] `dto/request/RegisterRequest.java`：username、email、password（带 `@NotBlank` / `@Email` 校验）
- [ ] `dto/request/LoginRequest.java`：username、password
- [ ] `dto/request/ChatStartRequest.java`：title（可选）
- [ ] `dto/request/SendMessageRequest.java`：sessionId、content
- [ ] `dto/request/StoryGenerateRequest.java`：sessionId
- [ ] `dto/request/StoryUpdateRequest.java`：title、genre、style、synopsis（均为可选字段）
- [ ] `dto/request/UserUpdateRequest.java`：username、email、avatarPath（可选）

**验证**：`mvn compile` 通过

---

### Step 4.2 — 创建响应 DTO

- [ ] `dto/response/ApiResponse<T>.java`：统一响应体 code/message/data/timestamp
- [ ] `dto/response/LoginResponse.java`：token、userId、username
- [ ] `dto/response/ChatSessionResponse.java`：id、sessionKey、title、status、startedAt、lastActive
- [ ] `dto/response/MessageResponse.java`：id、sessionId、role、content、createdAt
- [ ] `dto/response/StoryResponse.java`：id、title、genre、style、synopsis、status、coverImagePath、createdAt
- [ ] `dto/response/StoryDetailResponse.java`：继承 StoryResponse + characters[] + scenes[] + fullContent
- [ ] `dto/response/UserProfileResponse.java`：id、username、email、avatarPath、createdAt

**验证**：`mvn compile` 通过

---

## Phase 5：后端 — 安全与认证

### Step 5.1 — JWT 工具类

- [ ] `utils/JwtUtil.java`：
  - `generateToken(Long userId, String username)`：签发 JWT，有效期 24h，密钥从配置读取
  - `validateToken(String token)`：返回 boolean
  - `getUserIdFromToken(String token)`：解析 userId
  - `getUsernameFromToken(String token)`：解析 username
- [ ] 在 `application.yml` 配置 `jwt.secret` 和 `jwt.expiration`

**验证**：编写 `JwtUtilTest`：生成 token → 验证通过 → 解析出正确 userId

---

### Step 5.2 — Spring Security 配置

- [ ] `config/SecurityConfig.java`：
  - 放行 `/api/auth/**`、`/doc.html`、`/v3/api-docs/**`、`/webjars/**`、`/ws/**`
  - 其余请求需认证
  - 禁用 CSRF、启用 CORS
  - 添加 JWT 过滤器
- [ ] `config/JwtAuthenticationFilter.java`：从 `Authorization: Bearer xxx` 头提取 token，验证并设置 SecurityContext
- [ ] `config/CorsConfig.java`：允许 `http://localhost:8080` 跨域

**验证**：启动后端，不带 token 访问 `/api/user/profile` 返回 401；带有效 token 返回 200（接口后续实现）

---

### Step 5.3 — 用户注册与登录

- [ ] `service/UserService.java` 接口：
  - `register(RegisterRequest req)` → `UserProfileResponse`
  - `login(LoginRequest req)` → `LoginResponse`
  - `getProfile(Long userId)` → `UserProfileResponse`
  - `updateProfile(Long userId, UserUpdateRequest req)` → `UserProfileResponse`
- [ ] `service/impl/UserServiceImpl.java`：
  - 注册：校验 username/email 唯一性 → BCrypt 加密密码 → 保存 → 返回 profile
  - 登录：按 username 查用户 → BCrypt 验密 → 生成 JWT → 返回 LoginResponse
  - 获取/更新 profile
- [ ] `controller/UserController.java`：
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/user/profile`（需认证）
  - `PUT /api/user/profile`（需认证）

**验证**：用 curl 或 Knife4j `POST /api/auth/register` 注册用户 → `POST /api/auth/login` 获取 token → 带 token 调 `GET /api/user/profile` 返回用户信息

```bash
# 注册
curl -X POST http://localhost:8085/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"123456"}'

# 登录（获取 token）
curl -X POST http://localhost:8085/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# 获取 profile（用上面返回的 token）
curl http://localhost:8085/api/user/profile \
  -H "Authorization: Bearer <token>"
```

---

## Phase 6：后端 — 聊天服务（核心）

### Step 6.1 — 聊天会话管理

- [ ] `service/ChatService.java` 接口：
  - `startSession(Long userId, ChatStartRequest req)` → `ChatSessionResponse`
  - `getHistory(Long sessionId, Long userId)` → `List<MessageResponse>`
  - `deleteSession(Long sessionId, Long userId)`
  - `getUserSessions(Long userId)` → `List<ChatSessionResponse>`
- [ ] `service/impl/ChatServiceImpl.java`：
  - startSession：生成 UUID sessionKey → 保存 ChatSession（status=active, current_stage=INITIAL）→ 返回
  - getHistory：校验会话归属 → 按 created_at 升序返回消息列表
  - deleteSession：校验归属 → 软删除或状态改为 deleted
  - getUserSessions：按 userId + last_active 降序返回

**验证**：编写 `ChatServiceTest`（或通过 Knife4j 手动测试）：
- startSession → 返回 sessionKey
- 再次调用 getUserSessions → 列表中包含刚创建的会话

---

### Step 6.2 — 消息发送与模拟 AI 回复

- [ ] 扩展 `ChatService` 接口：`sendMessage(Long userId, SendMessageRequest req)` → `MessageResponse`
- [ ] `service/impl/ChatServiceImpl.java` 中的 sendMessage 逻辑：
  1. 校验 session 归属用户
  2. 保存用户消息（role=user）
  3. **模拟 AI 回复**：生成固定字符串 `"你好！我是AI漫剧创作助手。关于漫剧创作的功能正在开发中，敬请期待！"`，保存为 role=ai 的消息
  4. 更新 session 的 last_active 时间
  5. 返回 AI 消息的 MessageResponse
- [ ] `controller/ChatController.java`：
  - `POST /api/chat/start`
  - `POST /api/chat/message`
  - `GET /api/chat/history/{sessionId}`
  - `DELETE /api/chat/session/{sessionId}`
  - `GET /api/chat/sessions`

**验证**：用 curl 测试完整对话流：
```bash
# 1. 开始会话
curl -X POST http://localhost:8085/api/chat/start \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"测试会话"}'

# 2. 发送消息
curl -X POST http://localhost:8085/api/chat/message \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":1,"content":"你好"}'
# 返回 AI 固定回复

# 3. 查看历史
curl http://localhost:8085/api/chat/history/1 \
  -H "Authorization: Bearer <token>"
# 返回两条消息（用户 + AI）
```

---

### Step 6.3 — WebSocket 实时消息推送

- [ ] `config/WebSocketConfig.java`：配置 STOMP 端点 `/ws/chat`，broker `/topic`，应用前缀 `/app`
- [ ] `controller/ChatWebSocketController.java`：
  - `@MessageMapping("/chat.send")`：接收 WebSocket 消息 → 调用 ChatService.sendMessage → 通过 `SimpMessagingTemplate` 推送到 `/topic/chat/{sessionId}`
- [ ] 修改发送消息流程：HTTP 和 WebSocket 共用 ChatService

**验证**：使用浏览器控制台或简单 HTML 页面连接 WebSocket，发送消息后收到 AI 回复推送

---

## Phase 7：后端 — 漫剧服务

### Step 7.1 — 漫剧 CRUD

- [ ] `service/StoryService.java` 接口：
  - `getStoryDetail(Long storyId, Long userId)` → `StoryDetailResponse`
  - `getUserStories(Long userId, int page, int size)` → `Page<StoryResponse>`
  - `updateStory(Long storyId, Long userId, StoryUpdateRequest req)` → `StoryResponse`
  - `deleteStory(Long storyId, Long userId)`
- [ ] `service/impl/StoryServiceImpl.java`：
  - getStoryDetail：查询 story + characters + scenes → 组装 StoryDetailResponse
  - getUserStories：分页查询 + 按 updated_at 降序
  - updateStory：校验归属 → 更新字段 → 保存
  - deleteStory：校验归属 → 删除（级联删除关联 characters/scenes/dialogues）
- [ ] `controller/StoryController.java`：
  - `GET /api/story/{id}`
  - `GET /api/story/list?page=1&size=10`
  - `PUT /api/story/{id}`
  - `DELETE /api/story/{id}`

**验证**：用 curl 测试 CRUD：
```bash
# 创建（模拟，可直接 insert 数据库）
# 查询列表
curl "http://localhost:8085/api/story/list?page=1&size=10" \
  -H "Authorization: Bearer <token>"
```

---

### Step 7.2 — 模拟漫剧生成接口

- [ ] 扩展 `StoryService`：`generateStory(Long userId, StoryGenerateRequest req)` → `StoryResponse`
- [ ] `service/impl/StoryServiceImpl.java`：
  - 查询 session 的 context_data
  - 生成模拟数据：title="示例漫剧"、genre="科幻"、style="日漫"、synopsis="这是一部由AI助手生成的示例漫剧..."
  - 创建 Story、创建 2 个默认 Character、创建 2 个默认 Scene
  - 保存并返回 StoryResponse
- [ ] `controller/StoryController.java`：`POST /api/story/generate`

**验证**：
```bash
curl -X POST http://localhost:8085/api/story/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":1}'
# 返回一条模拟的漫剧数据
```

---

## Phase 8：后端 — 文件存储与全局异常处理

### Step 8.1 — 本地文件存储工具

- [ ] `utils/LocalFileStorageUtil.java`：
  - `saveFile(MultipartFile file, String category)` → 文件相对路径
  - `loadFile(String filePath)` → `Resource`
  - `deleteFile(String filePath)` → boolean
  - `getFileUrl(String filePath)` → URL 字符串
  - 文件名校验（UUID 重命名、路径遍历检查、类型白名单、大小限制 10MB）
- [ ] `config/StorageConfig.java`：配置 root-path、max-file-size
- [ ] `controller/FileController.java`：
  - `POST /api/files/upload`
  - `GET /api/files/{category}/{date}/{filename}`
  - `DELETE /api/files/{category}/{date}/{filename}`

**验证**：上传一张测试图片 → 返回 URL → 浏览器访问 URL 显示图片

---

### Step 8.2 — 全局异常处理

- [ ] `config/GlobalExceptionHandler.java`（或放在 utils 包）：
  - `@ExceptionHandler(MethodArgumentNotValidException.class)` → 400 + 校验错误详情
  - `@ExceptionHandler(IllegalArgumentException.class)` → 400
  - `@ExceptionHandler(AccessDeniedException.class)` → 403
  - `@ExceptionHandler(NoSuchElementException.class)` → 404
  - `@ExceptionHandler(Exception.class)` → 500 + 通用错误信息
- [ ] 所有异常返回统一 `ApiResponse` 格式

**验证**：调一个不存在的 API 路径或传递非法参数，确认返回 JSON 格式错误信息而非 HTML/堆栈

---

## Phase 9：前端 — 路由与布局

### Step 9.1 — Vue Router 路由配置

- [ ] `router/index.ts`：
  - `/` → 重定向到 `/chat`
  - `/chat` → `ChatView.vue`（懒加载）
  - `/chat/:sessionId` → `ChatView.vue`（带会话参数）
  - `/stories` → `StoryList.vue`（懒加载）
  - `/story/:id` → `StoryDetailView.vue`（懒加载）
  - `/user` → `UserCenter.vue`（懒加载，需认证）
  - `/login` → `LoginView.vue`
  - `/register` → `RegisterView.vue`
- [ ] 路由守卫：除 `/login`、`/register` 外，未登录跳转 `/login`

**验证**：`npm run dev` 后手动访问各路径，确认页面切换正常。访问 `/chat` 自动跳转 `/login`

---

### Step 9.2 — 基础布局组件

- [ ] `components/common/AppLayout.vue`：顶部导航栏（Logo + 导航链接 + 用户头像下拉）+ `<router-view />` 内容区
- [ ] 导航链接：对话、漫剧列表（登录后可见）
- [ ] 用户头像下拉：个人中心、退出登录

**验证**：登录后页面顶部显示导航栏，点击各链接切换页面

---

## Phase 10：前端 — 认证模块

### Step 10.1 — API 层与 Axios 封装

- [ ] `api/index.ts`：创建 Axios 实例，baseURL 为空（走 Vite 代理），超时 15s
- [ ] 请求拦截器：从 localStorage 取 token 加到 `Authorization: Bearer xxx`
- [ ] 响应拦截器：401 → 清除 token → 跳转 `/login`；其他错误 → 统一 toast 提示

**验证**：在浏览器 DevTools Network 面板中看到请求头带 Authorization

---

### Step 10.2 — Auth API 与 User Store

- [ ] `api/authApi.ts`：`register(data)` / `login(data)` / `getProfile()` / `updateProfile(data)`
- [ ] `stores/userStore.ts`（Pinia）：
  - state：token、userInfo（id/username/email/avatarPath）、isLoggedIn
  - actions：`login(username, password)`、`register(username, email, password)`、`fetchProfile()`、`logout()`
  - persist：token 存 localStorage

**验证**：调用 `userStore.login()` → token 持久化到 localStorage → `isLoggedIn` 变为 true

---

### Step 10.3 — 登录/注册页面

- [ ] `views/LoginView.vue`：用户名 + 密码表单，Element Plus `el-form`，调用 userStore.login，成功后跳转 `/chat`
- [ ] `views/RegisterView.vue`：用户名 + 邮箱 + 密码 + 确认密码，调用 userStore.register，成功后跳转 `/login`
- [ ] 表单校验：用户名必填（3-20字符）、邮箱格式、密码必填（6+字符）、确认密码一致

**验证**：页面操作完整流程 — 注册 → 登录 → 跳转到 `/chat`

---

## Phase 11：前端 — 聊天核心功能

### Step 11.1 — Chat API 与 Chat Store

- [ ] `api/chatApi.ts`：`startSession(title?)` / `sendMessage(sessionId, content)` / `getHistory(sessionId)` / `getSessions()` / `deleteSession(sessionId)`
- [ ] `stores/chatStore.ts`（Pinia）：
  - state：currentSessionId、sessions[]、messages[]、isLoading
  - actions：`startNewSession()`、`switchSession(sessionId)`、`sendMessage(content)`、`loadHistory(sessionId)`、`loadSessions()`、`deleteSession(sessionId)`
  - sendMessage 调用 API 后将 user 消息和 ai 回复追加到 messages[]

**验证**：在浏览器控制台调用 `chatStore.startNewSession()` → `chatStore.sendMessage("你好")` → messages 数组包含 2 条消息

---

### Step 11.2 — 消息气泡组件

- [ ] `components/chat/MessageBubble.vue`：
  - props：role（user/ai）、content、timestamp
  - user 消息：右对齐、蓝色背景
  - ai 消息：左对齐、灰色背景 + 机器人头像图标
  - 时间格式化（dayjs）
  - 支持 markdown 渲染（markdown-it）

**验证**：在父组件传入不同 props，确认渲染样式正确

---

### Step 11.3 — 输入区域组件

- [ ] `components/chat/InputArea.vue`：
  - `el-input` textarea + 发送按钮
  - Enter 发送、Shift+Enter 换行
  - 发送中显示 loading 状态、按钮 disabled
  - emit：`send` 事件，传递文本内容
  - 发送后清空输入框

**验证**：输入文字 → 点击发送 → 触发 send 事件 → 输入框清空 → 输入文字 → Ctrl+Enter 发送

---

### Step 11.4 — 会话列表组件

- [ ] `components/chat/SessionList.vue`：
  - 左侧列表显示所有会话（标题 + 时间）
  - "新建对话"按钮
  - 当前会话高亮
  - 右键/更多按钮删除会话
  - emit：`select`、`delete`、`create`

**验证**：创建多个会话 → 列表中显示 → 点击切换 → 高亮变化 → 删除一个 → 列表刷新

---

### Step 11.5 — 对话主页面 ChatView

- [ ] `views/ChatView.vue`：
  - 左侧：SessionList（宽度 ~280px，可折叠）
  - 右侧：消息列表（MessageBubble 列表，自动滚到底部）+ InputArea
  - 路由参数 `sessionId` 存在时自动切换到该会话
  - 无会话时显示欢迎页（Logo + "开始新对话"引导）
  - 加载消息历史时显示骨架屏

**验证**：完整操作流程 — 进入页面 → 新建对话 → 发送 "你好" → 收到固定回复 → 切换会话 → 查看历史消息

---

### Step 11.6 — WebSocket 集成（前端）

- [ ] 在 `chatStore` 中集成 WebSocket（SockJS + STOMP）：
  - startNewSession / switchSession 时建立 STOMP 连接，订阅 `/topic/chat/{sessionId}`
  - 收到消息时追加到 messages[]（仅追加非当前用户发送的消息）
  - 组件卸载时断开连接
- [ ] 备选方案：如果 WebSocket 复杂，先用 HTTP 轮询方式（发送消息后轮询一次 history），不影响功能

**验证**：打开两个浏览器标签页，同一会话中 A 发送消息，B 实时收到推送（或至少 HTTP 方式能正确获取）

---

## Phase 12：前端 — 漫剧模块

### Step 12.1 — Story API 与 Story Store

- [ ] `api/storyApi.ts`：`getStories(page, size)` / `getStoryDetail(id)` / `generateStory(sessionId)` / `updateStory(id, data)` / `deleteStory(id)`
- [ ] `stores/storyStore.ts`：
  - state：stories[]、currentStory（含 detail）、pagination、isLoading
  - actions：`fetchStories()`、`fetchStoryDetail(id)`、`generateStory(sessionId)`、`updateStory(id, data)`、`deleteStory(id)`

**验证**：调用 `fetchStories()` → stories 数组填充数据

---

### Step 12.2 — 漫剧列表页

- [ ] `views/StoryList.vue`：
  - 卡片网格展示漫剧列表（封面图、标题、类型标签、状态、更新时间）
  - 分页组件（Element Plus `el-pagination`）
  - 搜索/筛选（按类型、状态）
  - 点击卡片跳转 `/story/:id`
  - 删除按钮 + 确认弹窗

**验证**：进入页面 → 显示漫剧卡片列表 → 翻页 → 点击进入详情

---

### Step 12.3 — 漫剧详情页

- [ ] `views/StoryDetailView.vue`：
  - 顶部：标题 + 类型/风格标签 + 状态 + 操作按钮（编辑/删除/生成封面）
  - 内容区：摘要 + 角色卡片列表（CharacterCard）+ 场景列表
  - 角色卡片展示名称、角色定位、外观描述、性格
- [ ] `components/story/CharacterCard.vue`：头像占位 + 名称 + 角色标签 + 描述

**验证**：访问 `/story/1` → 详情信息完整展示 → 角色卡片渲染正确

---

### Step 12.4 — 对话中触发漫剧生成

- [ ] 在 `ChatView.vue` 消息区域上方添加"生成漫剧"按钮
- [ ] 点击 → 调用 `storyStore.generateStory(currentSessionId)` → 提示"生成成功" → 可跳转到详情页
- [ ] 生成成功后 AI 自动发送一条消息告知用户

**验证**：对话中点击生成 → 等待 → 收到成功提示 → 漫剧列表出现新漫剧

---

## Phase 13：前端 — 用户中心

### Step 13.1 — 用户中心页面

- [ ] `views/UserCenter.vue`：
  - 头像展示（Element Plus `el-avatar`）
  - 用户信息展示：用户名、邮箱、注册时间
  - 编辑入口：修改用户名/邮箱的表单（`el-dialog` 弹窗）
  - 漫剧数量统计卡片
  - 对话数量统计卡片
- [ ] 上传头像功能：`el-upload` + 调用文件上传 API

**验证**：进入 `/user` → 显示用户信息 → 点击编辑 → 弹窗修改 → 保存成功

---

## Phase 14：集成测试与收尾

### Step 14.1 — 前端-后端联调测试

- [ ] 启动 MySQL + Redis + RabbitMQ
- [ ] 启动后端（8085）
- [ ] 启动前端（8080）
- [ ] 完整用户流程测试：
  1. 注册账号 → 登录
  2. 新建对话 → 发送 3 条消息 → 收到 AI 固定回复
  3. 切换/删除会话
  4. 点击生成漫剧 → 查看漫剧详情
  5. 查看漫剧列表 → 翻页
  6. 进入用户中心 → 修改信息
  7. 退出登录 → 重新登录

**验证**：完整流程无报错，各页面功能正常

---

### Step 14.2 — 后端单元测试覆盖

- [ ] UserService 测试：注册 + 登录 + 获取 profile
- [ ] ChatService 测试：创建会话 + 发送消息 + 获取历史 + 删除会话
- [ ] StoryService 测试：生成漫剧 + 查询列表 + 查询详情 + 更新 + 删除
- [ ] JwtUtil 测试：生成 + 验证 + 解析

**验证**：`mvn test` 全部通过

---

## 实现顺序依赖图

```
Phase 1  (脚手架)
  ├── 1.1 后端项目
  └── 1.2 前端项目
        ↓
Phase 2  (数据库)
  ├── 2.1 建表
  └── 2.2 MyBatis-Plus 配置
        ↓
Phase 3  (Entity + Mapper) ──→ Phase 4 (DTO)
        ↓
Phase 5  (安全认证)
  ├── 5.1 JWT
  ├── 5.2 Security 配置
  └── 5.3 注册登录
        ↓
Phase 6  (聊天服务) ─────────→ Phase 9  (前端路由)
  ├── 6.1 会话管理                ↓
  ├── 6.2 消息发送           Phase 10 (前端认证)
  └── 6.3 WebSocket               ↓
        ↓                    Phase 11 (前端聊天)
Phase 7  (漫剧服务)               ↓
  ├── 7.1 CRUD               Phase 12 (前端漫剧)
  └── 7.2 模拟生成                ↓
        ↓                    Phase 13 (用户中心)
Phase 8  (文件存储 + 异常)         ↓
                             Phase 14 (集成测试)
```

箭头表示依赖关系，前后端各 Phase 可部分并行开发（后端 Phase 5-7 完成后前端 Phase 10-12 可开始）。

---

**文档版本**: v1.0  
**创建日期**: 2026-05-16  
**适用范围**: MVP 前后端部分（AI 引擎用固定字符串模拟）