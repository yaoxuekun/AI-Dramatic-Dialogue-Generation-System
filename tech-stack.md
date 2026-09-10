# AI漫剧生成系统 - 技术选型文档

## 1. 概述

本文档基于《AI漫剧生成对话系统设计文档》，详细列出各模块的技术选型、版本要求、选型理由、依赖关系及**本地命令行运行测试指南**。当前阶段暂不采用Docker容器化部署，各服务通过本地原生安装并直接启动运行。

---

## 2. 前端技术栈

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Vue** | 3.4+ | 响应式数据流，组件化开发，生态成熟；组合式API（Composition API）更适合复杂交互场景 |
| **TypeScript** | 5.3+ | 静态类型检查，提升代码可维护性，减少运行时错误；IDE智能提示增强开发效率 |
| **Pinia** | 2.1+ | Vue官方推荐的状态管理库，比Vuex更轻量，原生支持TypeScript |
| **Vue Router** | 4.3+ | Vue官方路由，支持懒加载、动态路由、导航守卫等特性 |
| **Axios** | 1.6+ | Promise HTTP客户端，支持拦截器、请求取消、自动转换JSON |
| **Element Plus** | 2.4+ | Vue 3 UI组件库，提供丰富的企业级组件，中文化支持良好 |
| **SockJS + STOMP.js** | 0.6+ / 1.2+ | WebSocket实时通信方案，实现AI消息推送 |
| **Vite** | 5.x | 极速构建工具，HMR热更新，替代Webpack作为开发服务器和打包工具 |

### 2.1 开发环境配置

```jsonc
// package.json 核心依赖
{
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "element-plus": "^2.4.0",
    "dayjs": "^1.11.0",
    "markdown-it": "^14.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "sass": "^1.69.0",
    "sockjs-client": "^1.6.1",
    "@stomp/stompjs": "^7.0.0"
  }
}
```

### 2.2 本地启动命令

```bash
cd frontend
npm install
npm run dev    # 启动开发服务器，默认访问 http://localhost:8080
```

### 2.3 选型说明

- **选择Vue 3而非React**：团队对Vue更熟悉，Vue的模板语法对中文化项目开发更友好
- **选择TypeScript**：复杂状态管理需要类型安全保障
- **选择Vite而非Webpack**：冷启动速度快10倍以上，更适合本地开发调试

---

## 3. 后端技术栈

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Java** | 17 LTS | Long-Term Support版本，稳定性高，性能优秀；Record、Sealed Classes等新特性提升开发效率 |
| **Spring Boot** | 3.2+ | 成熟的Java Web框架，自动配置减少样板代码，内置Tomcat简化本地启动 |
| **MyBatis-Plus** | 3.5+ | MyBatis增强工具，支持CRUD自动生成、分页插件、条件构造器等，大幅减少SQL编写工作量 |
| **Spring Security** | 6.2+ | 企业级安全框架，与Spring Boot深度集成，支持JWT/OAuth2等多种认证方式 |
| **JWT (jjwt)** | 0.12+ | JSON Web Token实现，无状态认证，适合前后端分离架构 |
| **Knife4j** | 4.4+ | Swagger增强UI，自动生成API文档，支持在线测试接口 |
| **Lombok** | 1.18+ | 简化Java POJO开发，通过注解自动生成Getter/Setter/ToString等方法 |

### 3.1 核心依赖配置

```xml
<!-- pom.xml 核心依赖 -->
<dependencies>
    <!-- Spring Boot核心 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>3.2.0</version>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
        <version>3.2.0</version>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-websocket</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- 数据库 -->
    <dependency>
        <groupId>com.mysql</groupId>
        <artifactId>mysql-connector-j</artifactId>
        <version>8.0.33</version>
    </dependency>
    <dependency>
        <groupId>com.baomidou</groupId>
        <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
        <version>3.5.5</version>
    </dependency>

    <!-- 安全与认证 -->
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-api</artifactId>
        <version>0.12.3</version>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-impl</artifactId>
        <version>0.12.3</version>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-jackson</artifactId>
        <version>0.12.3</version>
        <scope>runtime</scope>
    </dependency>

    <!-- 缓存 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-redis</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- 消息队列 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-amqp</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- API文档 -->
    <dependency>
        <groupId>com.github.xiaoymin</groupId>
        <artifactId>knife4j-openapi3-jakarta-spring-boot-starter</artifactId>
        <version>4.4.0</version>
    </dependency>

    <!-- 工具类 -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <version>1.18.30</version>
        <scope>provided</scope>
    </dependency>
    <dependency>
        <groupId>org.apache.commons</groupId>
        <artifactId>commons-lang3</artifactId>
        <version>3.14.0</version>
    </dependency>
</dependencies>
```

### 3.2 本地启动命令

```bash
cd backend
mvn spring-boot:run    # 启动Spring Boot，默认监听 http://localhost:8085
```

启动后可通过 Knife4j 查看API文档：`http://localhost:8085/doc.html`

### 3.3 选型说明

- **选择Java而非Go/Node.js**：企业级应用生态完善，人才储备充足
- **选择MyBatis-Plus而非JPA**：需要灵活控制SQL查询，特别是全文搜索和多表关联
- **选择Knife4j而非原生Swagger**：中文界面友好，文档展示更美观
- **选择RabbitMQ而非Kafka**：漫剧生成任务量中等，RabbitMQ更易运维且满足需求

---

## 4. AI引擎技术栈

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Python** | 3.11+ | AI/ML领域事实标准语言，拥有丰富的库和生态 |
| **LangChain** | 0.1+ | LLM应用开发框架，提供Agent/Chain/Memory等核心抽象，降低LLM集成复杂度 |
| **Pydantic** | 2.x | 数据验证库，用于结构化LLM输出，确保返回数据的类型安全 |
| **FastAPI** | 0.109+ | 异步Web框架，高性能且自动生成OpenAPI文档，适合作为AI引擎的HTTP服务层 |
| **langsmith** | 0.1+ | LangChain官方追踪平台，用于监控和优化Prompt效果 |
| **openai** | 1.x | OpenAI SDK，支持GPT-4/Claude等多模型调用 |
| **sentence-transformers** | 2.x | 文本嵌入模型，用于向量检索和语义相似度计算 |

### 4.1 核心依赖配置

```txt
# requirements.txt
fastapi==0.109.0
uvicorn==0.27.0
langchain==0.1.10
langchain-openai==0.0.8
pydantic==2.5.3
openai==1.12.0
langsmith==0.1.0
numpy==1.26.3
python-multipart==0.0.6
tiktoken==0.6.0
```

### 4.2 本地启动命令

```bash
cd ai_engine
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5000 --reload   # 启动AI引擎服务
```

启动后API文档地址：`http://localhost:5000/docs`

### 4.3 选型说明

- **选择FastAPI而非Flask**：原生支持异步，性能更好，自动生成API文档（Swagger UI）
- **选择LangChain**：社区活跃，文档完善，Agent/Chain抽象符合设计文档需求
- **选择Pydantic v2**：性能比v1提升显著，JSON Schema导出功能更强
- **使用 `--reload` 参数**：本地开发时文件变动自动重启，提高调试效率

---

## 5. 数据存储与中间件

> **注意**：以下所有服务均通过本地原生安装运行，不使用Docker容器。

### 5.1 MySQL 8.0

| 属性 | 值 |
|------|---|
| **角色** | 主数据存储（用户信息、会话记录、漫剧元数据） |
| **版本** | 8.0 |
| **端口** | 3306 |
| **字符集** | utf8mb4_unicode_ci |
| **存储引擎** | InnoDB |

**选型理由**：
- ACID事务保证数据一致性
- 完整的JSON字段支持，适合存储上下文数据
- 全文索引支持漫剧标题和摘要的模糊搜索
- 外键约束保证数据完整性

**本地安装方式（Windows）**：

```powershell
# 下载MySQL Community Server 8.0
# https://dev.mysql.com/downloads/installer/

# 初始化并启动MySQL服务
net start MySQL80

# 登录并创建数据库
mysql -u root -p
mysql> CREATE DATABASE aisay_manga CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql> CREATE USER 'aisay'@'localhost' IDENTIFIED BY 'aisay_pass';
mysql> GRANT ALL ON aisay_manga.* TO 'aisay'@'localhost';
mysql> FLUSH PRIVILEGES;
```

**后端连接配置** (`application.yml`)：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/aisay_manga?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai
    username: aisay
    password: aisay_pass
    driver-class-name: com.mysql.cj.jdbc.Driver
```

### 5.2 Redis 7

| 属性 | 值 |
|------|---|
| **角色** | 缓存层 + 会话记忆存储 |
| **版本** | 7.x |
| **端口** | 6379 |
| **持久化** | RDB快照 + AOF日志 |

**选型理由**：
- 内存数据结构存储，读写性能达百万QPS级别
- TTL自动过期机制天然适配会话记忆的生命周期管理
- 支持多种数据结构（String/List/Hash/Set），满足不同缓存场景

**本地安装方式（Windows）**：

```powershell
# 方式一：使用choco安装
choco install redis-64

# 方式二：从GitHub下载编译好的Redis for Windows
# https://github.com/microsoftarchive/redis/releases

# 后台启动Redis
redis-server.exe --service-install
redis-server.exe --service-start
```

**后端连接配置** (`application.yml`)：

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      password:
      database: 0
```

### 5.3 RabbitMQ 3.12+

| 属性 | 值 |
|------|---|
| **角色** | 漫剧生成异步任务队列 |
| **版本** | 3.12+ |
| **AMQP端口** | 5672 |
| **管理界面端口** | 15672 |

**选型理由**：
- 延迟低，路由灵活；漫剧生成任务以点对点为主，不需要Kafka的高吞吐能力
- Erlang编写，本身即可作为本地服务运行，无需额外容器

**本地安装方式（Windows）**：

```powershell
# 前提：先安装Erlang
choco install erlang

# 安装RabbitMQ
choco install rabbitmq

# 启用管理界面插件
rabbitmq-plugins enable rabbitmq_management

# 启动服务
net start RabbitMQ

# 登录管理界面：http://localhost:15672
# 默认账号密码: guest / guest
```

**后端连接配置** (`application.yml`)：

```yaml
spring:
  rabbitmq:
    host: localhost
    port: 5672
    username: guest
    password: guest
```

---

## 6. 文件存储方案

| 属性 | 值 |
|------|---|
| **方案** | 本地文件系统 |
| **根目录** | `./storage/` |
| **子目录** | uploads/, stories/, temp/, backups/, logs/ |
| **最大文件大小** | 10MB |
| **允许格式** | jpg/jpeg/png/gif/bmp/pdf/epub |
| **安全措施** | UUID重命名 + 路径遍历校验 + MIME类型检查 |

**选型理由**：
- 设计文档明确要求"本地化部署，无需云端依赖"
- 本地文件系统零运维成本，适合单机开发和测试场景
- 便于直接查看文件内容、调试和人工审核

---

## 7. 本地启动全流程

### 7.1 启动顺序

```
第1步 → 启动基础设施（MySQL、Redis、RabbitMQ）
第2步 → 启动后端（Spring Boot，依赖MySQL/Redis/RabbitMQ）
第3步 → 启动AI引擎（FastAPI，可选，不影响后端启动）
第4步 → 启动前端（Vite Dev Server，配置代理访问后端）
```

### 7.2 分窗口启动示例

在四个独立的命令行窗口中分别执行：

```bash
# 窗口1：确认MySQL已启动（通过系统服务或其他方式）
net start MySQL80

# 窗口2：启动Spring Boot后端
cd F:\ai\aisay\backend
mvn spring-boot:run

# 窗口3：启动Python AI引擎
cd F:\ai\aisay\ai_engine
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# 窗口4：启动Vue前端
cd F:\ai\aisay\frontend
npm install
npm run dev
```

### 7.3 端口分配汇总

| 服务 | 端口 | 用途 |
|------|------|------|
| Vue前端 | 8080 | 浏览器访问、开发热更新 |
| Spring Boot后端 | 8085 | REST API + WebSocket |
| Python AI引擎 | 5000 | AI对话与生成服务 |
| MySQL | 3306 | 主数据存储 |
| Redis | 6379 | 缓存与会话记忆 |
| RabbitMQ | 5672 | AMQP消息队列 |
| RabbitMQ管理 | 15672 | Web管理界面 |

### 7.4 前端代理配置

由于前后端端口不同，需通过Vite代理将API请求转发到后端：

```ts
// frontend/vite.config.ts
export default defineConfig({
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8085',
        ws: true,
      },
    },
  },
});
```

---

## 8. 版本汇总

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端** | Vue | 3.4+ |
| | TypeScript | 5.3+ |
| | Vite | 5.x |
| | Element Plus | 2.4+ |
| | Pinia | 2.1+ |
| | SockJS | 0.6+ |
| **后端** | Java | 17 LTS |
| | Spring Boot | 3.2+ |
| | MyBatis-Plus | 3.5+ |
| | Spring Security | 6.2+ |
| | JWT (jjwt) | 0.12+ |
| | Knife4j | 4.4+ |
| **AI引擎** | Python | 3.11+ |
| | FastAPI | 0.109+ |
| | LangChain | 0.1+ |
| | Pydantic | 2.5+ |
| | OpenAI SDK | 1.12+ |
| **数据存储** | MySQL | 8.0 |
| | Redis | 7.x |
| **消息队列** | RabbitMQ | 3.12+ |
| **构建工具** | Node/npm | 18+ / 9+ |
| | Maven | 3.9+ |
| | pip/poetry | 最新版 |

---

## 9. 技术风险与备选方案

| 风险 | 影响 | 备选方案 |
|------|------|----------|
| 本地文件存储容量有限 | 用户量增长后空间不足 | 切换到对象存储（MinIO） |
| Redis作为向量数据库 | 7.x不支持原生的向量检索 | 后续升级为ChromaDB或Milvus |
| 单台MySQL性能瓶颈 | 并发用户增多时查询变慢 | 引入读写分离或多级缓存 |
| RabbitMQ消息积压 | 漫剧生成高峰期处理不过来 | 升级为Kafka提升吞吐能力 |

---

## 10. 本地运行前置检查清单

- [ ] JDK 17 已安装（`java -version` >= 17）
- [ ] Node.js 18+ 已安装（`node -v` >= 18.0.0）
- [ ] Python 3.11+ 已安装（`python --version` >= 3.11）
- [ ] Maven 3.9+ 已安装（`mvn -version`）
- [ ] MySQL 8.0 已安装并运行（`net start MySQL80`）
- [ ] Redis 7 已安装并运行（`redis-cli ping` 返回 PONG）
- [ ] RabbitMQ 3.12+ 已安装并运行（`net start RabbitMQ`）
- [ ] Git 已安装
- [ ] 磁盘可用空间 >= 5GB

---

## 11. 附录

### 11.1 相关文档

| 文档 | 用途 |
|------|------|
| design-document.md | 系统总体设计文档 |
| tech-stack.md（本文档） | 技术选型详情 |
| API文档 | Knife4j自动生成，后端启动后访问 `/doc.html` |

### 11.2 参考链接

| 资源 | URL |
|------|-----|
| Vue 3 官方文档 | https://vuejs.org/ |
| Spring Boot 官方文档 | https://spring.io/projects/spring-boot |
| LangChain 官方文档 | https://python.langchain.com/ |
| FastAPI 官方文档 | https://fastapi.tiangolo.com/ |
| MySQL 8.0 参考手册 | https://dev.mysql.com/doc/refman/8.0/en/ |
| Redis 命令参考 | https://redis.io/commands/ |
| RabbitMQ 文档 | https://www.rabbitmq.com/documentation |
