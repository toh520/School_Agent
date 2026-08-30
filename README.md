# School Agent｜智慧校园智能体系统

本仓库是“2026 软件工程专业实习计划 v2”的团队项目仓库，用于建设面向学生的智慧校园 AI 助手。项目按 M01～M10 单模块串行开发，S1/M01 工程基础已完成非作者验收，下一阶段为 S2/M02。

## 当前阶段

- 当前状态：S1/M01 工程基础与公共规范已验收；S2/M02 尚未开始
- 已完成：Vue、Spring Boot、FastAPI、PostgreSQL/pgvector 工程骨架及真实健康链路
- 明确未开展：登录、资料管理、Agent 对话、食堂、考试规划、图书推荐和校园问答
- 需求基线：V1.0（2026-08-27）
- 团队仓库：<https://github.com/toh520/School_Agent>

## M01 固定版本

| 层级 | 版本 |
|---|---|
| Node.js / npm | 24.19.0 / 11.17.0 |
| Vue / Vite | 3.5.22 / 7.3.6 |
| Java / Maven | OpenJDK 21 / Maven 3.9.x |
| Spring Boot | 3.5.7 |
| Python | 3.12.x |
| FastAPI / Uvicorn | 0.115.12 / 0.37.0 |
| PostgreSQL / pgvector | 16.x / 0.8.x |
| 测试 | JUnit 5、pytest 8.4.2、Playwright 1.55.1 |

前端完整依赖由 `package-lock.json` 锁定，Python 完整依赖由 `requirements.lock` 锁定，Java 依赖由 Maven POM、Spring Boot BOM 和插件版本共同锁定。

## 第一次启动

以下命令在仓库根目录的 PowerShell 中执行。

### 1. 激活开发环境

```powershell
conda activate school-agent
./code/tools/check-env.ps1
```

如果普通 PowerShell 不能识别 `conda`，先使用 Miniconda Prompt，或按[开发环境审查记录](docs/开发环境审查与安装记录.txt)重新初始化 PowerShell。

### 2. 创建本地配置

```powershell
Copy-Item deploy/.env.example deploy/.env.local
```

编辑 `deploy/.env.local`，至少替换 `SCHOOL_AGENT_DB_PASSWORD` 的占位值。该文件已被 Git 忽略，禁止提交真实密码、令牌或密钥。

### 3. 安装项目依赖

```powershell
./code/tools/install-dependencies.ps1
```

脚本会执行以下工作：

- 使用 `package-lock.json` 安装 Web 依赖并安装 Playwright Chromium；
- 在 `code/services/agent-service/.venv` 创建 Python 3.12 环境并按 `requirements.lock` 安装；
- 下载 Maven 构建依赖，不修改其他 Conda 环境。

### 4. 构建并测试

```powershell
./code/tools/test-all.ps1
```

该命令依次执行 Java Spotless/JUnit/打包、Python Ruff/pytest、Vue 类型/格式/构建和隔离 Playwright 冒烟测试。

### 5. 启动完整本地链路

```powershell
./code/tools/start-dev.ps1
```

首次启动会在仓库忽略目录 `tmp/postgres-data` 中初始化 PostgreSQL，并由 Spring Boot Flyway 自动执行：

- `V1__foundation.sql`：启用 pgvector 并创建基础元数据表；
- `R__sanitized_foundation_seed.sql`：写入不含账号和个人数据的基础种子标识。

启动成功后访问：

- Web 健康页：<http://127.0.0.1:5173>
- Java 聚合健康接口：<http://127.0.0.1:8080/api/v1/health/system>
- Java Actuator：<http://127.0.0.1:8080/actuator/health>
- Python 健康接口：<http://127.0.0.1:8000/health>

验证真实浏览器链路：

```powershell
Set-Location code/apps/web
npm run test:e2e:live
Set-Location ../..
```

### 6. 停止服务

```powershell
./code/tools/stop-dev.ps1
```

脚本只停止 `tmp/dev-processes.json` 记录的本项目进程和 `tmp/postgres-data` 对应的数据库实例。

## 公共约定

- 环境模板：`deploy/.env.example`
- 统一响应、错误码、分页、请求标识、时区和日志脱敏：[M01 公共工程契约](docs/design/M01-公共工程契约.md)
- 请求标识：`X-Request-ID`，在 Web、Java 和 Python 之间传播
- 项目时区：`Asia/Shanghai`
- 日志：不记录请求正文、密码、令牌、密钥和数据库连接值
- 配置：数据库及服务地址缺失或仍为占位符时快速失败

## 常见问题

### 端口被占用

默认端口为 5173、8000、8080 和 5432。先运行 `./code/tools/stop-dev.ps1`；若仍占用，应确认占用进程归属，不要直接终止未知进程。

### 服务启动失败

检查 `logs/` 下各服务的 `.out.log` 和 `.err.log`。日志属于本地运行产物，不进入 Git。

### 数据库需要重新初始化

先停止服务。`tmp/postgres-data` 是被 Git 忽略的本地测试数据，删除它会清空本机项目数据库；只有明确需要重建且已确认无需保留数据时才可删除，然后重新运行 `./code/tools/start-dev.ps1`。

## 目录结构

```text
School_Agent/
├─ code/                             # 所有开发代码、测试与工程脚本
│  ├─ apps/web/                      # Vue 3 健康页与 Playwright 测试
│  ├─ services/core-service/         # Spring Boot 公共契约、迁移和聚合健康接口
│  ├─ services/agent-service/        # FastAPI 配置、日志和数据库健康探针
│  ├─ tests/                         # 后续跨模块测试目录
│  └─ tools/                         # 环境、依赖、启动、停止和测试脚本
├─ deploy/.env.example               # 可提交的无密钥环境模板
├─ docs/                             # 需求、设计、决策和过程证据
├─ logs/                             # 被忽略的本地运行日志
└─ tmp/                              # 被忽略的本地运行数据
```

## 文档入口

- [需求分析报告 V1.0](docs/requirements/智慧校园智能体系统需求分析报告.md)
- [技术开发报告 V1.0](docs/design/智慧校园智能体系统技术开发报告.md)
- [M01 公共工程契约](docs/design/M01-公共工程契约.md)
- [M01 配置项与环境变量清单](docs/design/M01-配置项与环境变量清单.md)
- [M01 验收记录](docs/process/M01_ACCEPTANCE.md)
- [项目过程日志](docs/process/PROJECT_LOG.md)
- [需求追踪矩阵](docs/process/TRACEABILITY_MATRIX.md)
- [测试与验收记录](docs/process/TEST_LOG.md)
- [架构决策记录](docs/decisions/ADR-0001-technology-stack.md)
- [协作规范](CONTRIBUTING.md)
- [开发代码规范](AGENTS.md)

## 留痕原则

1. 每项开发工作必须关联需求编号、Issue、ADR 或项目日志。
2. `main` 只通过 Pull Request 合并，开发在约定分支完成。
3. 每次合并记录验证命令与结果；关键证据进入 `docs/process`。
4. 不提交口令、令牌、真实个人数据、依赖缓存、构建产物和运行日志。
