# M01 工程基础与公共规范验收记录

- 阶段：S1
- 模块：M01 工程基础与公共规范
- 执行日期：2026-08-30
- 验收人：夫（非作者评审）
- 当前结论：已验收，可以进入 S2/M02
- 分支：`chore/m01-project-foundation`

## 1. 范围核对

已实现：

- Vue 3、Spring Boot 3.5、FastAPI 三端工程；
- PostgreSQL 16、pgvector、Flyway 迁移与脱敏基础种子；
- 环境变量预检、统一响应、错误码、请求标识、时区、分页和日志脱敏；
- JUnit、pytest、Playwright、Spotless、Ruff、Prettier、类型检查和构建脚本；
- 环境检查、依赖安装、启动、停止、全量测试和真实链路验证命令。

未实现且本阶段禁止实现：登录、用户授权、管理后台、Agent 对话、食堂推荐、考试规划、图书推荐和校园知识问答。

## 2. 退出条件证据

| 退出条件 | 证据 | 结果 |
|---|---|---|
| 新环境可按 README 启动 | `README.md`、`code/tools/check-env.ps1`、`code/tools/install-dependencies.ps1`、`code/tools/start-dev.ps1` | 通过自测及非作者复现 |
| 三端冒烟测试通过 | JUnit 7、pytest 5、Playwright 隔离场景 2 | 通过 |
| 浏览器—Java—Python—数据库链路通过 | `npm run test:e2e:live`，页面显示三项依赖 `UP` | 通过，1/1 |
| 数据库迁移通过 | Flyway `foundation` 与 `sanitized foundation seed` 两条记录成功 | 通过，2/2 |
| pgvector 可用 | 健康接口返回 pgvector 0.8.3；迁移启用扩展 | 通过 |
| 配置缺失快速失败 | Java 启动前预检测试 2；Python Pydantic 配置测试 1；JAR 人工进程验证 | 通过 |
| 仓库及日志无真实密钥 | `.env.local` 被忽略；运行日志按本地测试密码精确扫描 | 通过 |
| 启停可恢复 | 最终停止后 5173、8000、8080、5432 均无监听 | 通过 |

## 3. 验证摘要

```text
Java:      7 passed, 0 failed
Python:    5 passed, 0 failed
Web E2E:   2 passed, 0 failed
Live E2E:  1 passed, 0 failed
npm audit: 0 vulnerabilities
Flyway:    2 successful migrations
```

完整命令与环境见 `docs/process/TEST_LOG.md`。

## 4. 数据、接口和安全影响

- 数据：只创建 `schema_metadata` 和 Flyway 历史表，不创建任何学生、账号或业务数据。
- 接口：新增 `/api/v1/health/system`、`/actuator/health` 和 Python `/health`。
- 权限：M02 尚未开始，健康接口不接收或返回个人信息。
- 日志：基础结构化日志会屏蔽常见凭据赋值，不记录请求体和环境变量值。
- 兼容性：后续模块应复用 `docs/design/M01-公共工程契约.md`；不兼容变更需单独评审 M01。
- 配置约束：数据库和服务地址统一登记在 `docs/design/M01-配置项与环境变量清单.md`，后续模块不得硬编码环境相关值。

## 5. 非作者验收确认

- [x] 验收人夫仅按 README 在 VS Code 新终端复现环境检查、启动、健康链路、数据库检查和停止流程。
- [x] 验收人夫检查数据、接口、日志、安全、配置硬编码和阶段范围边界。
- [x] 启动健康检查竞态修复后重新验证，完整链路与真实浏览器测试通过。
- [x] M01 与 M01 范围内的 NFR 基础状态已更新为“已验收”，允许进入 S2。
