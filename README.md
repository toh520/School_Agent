# School Agent｜智慧校园智能体系统

本仓库是“2026 软件工程专业实习计划 v2”的团队项目仓库，用于建设面向学生的智慧校园 AI 助手。系统以统一登录为基础，提供智能食堂推荐、考试安排与 AI 学习规划、学校书籍查询推荐和校园知识问答四项核心服务。

## 项目状态

- 当前阶段：项目初始化与需求设计
- 需求基线：V1.0（Markdown）
- 基线日期：2026-08-27
- 团队仓库：<https://github.com/toh520/School_Agent>

## 技术栈

| 层级 | 技术选型 |
|---|---|
| Web 前端 | Vue 3、TypeScript、Vite、Element Plus、Tailwind CSS、Pinia、ECharts |
| 核心业务后端 | Java 21、Spring Boot 3.5、Spring Security、MyBatis-Plus |
| AI 与 Agent | Python 3.11/3.12、FastAPI、LangGraph、RAG |
| 数据存储 | PostgreSQL、pgvector、本地文件目录 |
| 本地运行 | Node.js、JDK、Python 虚拟环境，可选 Docker Compose |
| 可选部署 | Nginx、Docker Compose 或直接运行服务部署到个人云服务器 |
| 测试 | JUnit、pytest、Playwright |

## 文档入口

- [智慧校园智能体系统需求分析报告 V1.0](docs/requirements/智慧校园智能体系统需求分析报告.md)
- [项目过程日志](docs/process/PROJECT_LOG.md)
- [需求追踪矩阵](docs/process/TRACEABILITY_MATRIX.md)
- [测试与验收记录](docs/process/TEST_LOG.md)
- [会议纪要](docs/process/MEETING_NOTES.md)
- [架构决策记录](docs/decisions/ADR-0001-technology-stack.md)
- [协作规范](CONTRIBUTING.md)

## 留痕原则

1. 每项开发工作必须关联需求编号、Issue 或任务编号。
2. 重要技术取舍使用 ADR 记录背景、选择、影响和替代方案。
3. 每次合并必须记录验证命令与结果；关键验收证据进入 `docs/process`。
4. `main` 始终保持可演示、可测试；功能通过分支和 Pull Request 合并。
5. 不在仓库中提交口令、令牌、真实个人健康数据或其他敏感信息。

## 目录规划

```text
School_Agent/
├─ apps/                 # 前端应用与管理端（开发阶段创建）
├─ services/             # Java 业务服务和 Python Agent 服务
├─ deploy/               # 可选的本地容器和个人云服务器配置
├─ docs/                  # 项目、需求、决策与过程证据
├─ tests/                 # 端到端、性能和安全测试
└─ tools/                 # 构建、校验和辅助脚本（开发阶段创建）
```
