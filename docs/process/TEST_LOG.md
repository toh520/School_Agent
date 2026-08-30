# 测试与验收记录

测试代码、报告和截图应保存在仓库中的稳定路径或 CI 构建产物中，本文件记录可复核的执行摘要。

## 执行记录模板

### YYYY-MM-DD｜测试批次名称

- 版本/提交：
- 环境：
- 执行人：
- 关联需求：
- 测试命令：
- 结果：通过 0 / 失败 0 / 跳过 0
- 报告与截图：
- 已知问题：
- 结论：

## 验收基线

- V1.0 Markdown 需求分析报告定义 AT-01～AT-18 为当前端到端验收场景。
- S1、S2 缺陷必须为 0；S3 必须有确认后的修复计划；S4 不得影响验收。
- 课设阶段重点验证本地启动、核心流程、数据保存、错误处理和课堂演示稳定性。

## 2026-08-30｜S1/M01 工程基础验证

- 版本/提交：`chore/m01-project-foundation` 工作区（提交前）
- 环境：Windows 11；Node.js 24.19.0；OpenJDK 21.0.10；Python 3.12.13；PostgreSQL 16.14；pgvector 0.8.3
- 执行人：Codex（实现与自测）；非作者复现待完成
- 关联范围：技术开发报告 S1/M01；NFR 运行可靠性、可维护性与基础安全
- 测试命令：
  - `./code/tools/check-env.ps1`
  - `./code/tools/test-all.ps1`
  - `./code/tools/start-dev.ps1`
  - `npm run test:e2e:live`
  - `npm audit --audit-level=high`
  - PostgreSQL 查询 `flyway_schema_history`、`pg_extension` 和 `schema_metadata`
  - 缺失环境变量启动 JAR；运行日志本地测试密码精确扫描；停止后端口扫描
- 结果：自动化通过 15 / 失败 0 / 跳过 0；迁移通过 2 / 失败 0；npm 漏洞 0
- 明细：JUnit 7/7；pytest 5/5；隔离 Playwright 2/2；真实链路 Playwright 1/1
- 报告与截图：`docs/process/M01_ACCEPTANCE.md`；Surefire、Playwright 本地产物为忽略的构建产物
- 已知问题：无 S1/S2 缺陷；仍需非作者按 README 复现并评审
- 结论：M01 实现和自测满足退出条件，状态为“待验收”

## 2026-08-30｜代码目录归并回归验证

- 版本/提交：`chore/m01-project-foundation` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda 环境
- 执行人：Codex
- 关联范围：S1/M01 目录结构与开发入口调整
- 调整内容：将 `apps`、`services`、`tests`、`tools` 归并至仓库根目录的 `code/`，同步修正脚本和文档路径
- 测试命令：
  - `./code/tools/check-env.ps1`
  - `./code/tools/test-all.ps1`
  - `./code/tools/start-dev.ps1`
  - `npm run test:e2e:live`
  - `./code/tools/stop-dev.ps1`
- 结果：JUnit 7/7；pytest 5/5；隔离 Playwright 2/2；真实链路 Playwright 1/1
- 结论：目录归并后环境检查、构建、三端测试、真实健康链路和启停流程全部通过

## 2026-08-30｜启动健康检查竞态修复验证

- 版本/提交：`chore/m01-project-foundation` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda 环境
- 执行人：Codex
- 问题：Java 已返回健康响应但 Python Agent 尚未就绪时，启动脚本未等待便立即重试，30 次检查可能在一秒内耗尽
- 修复：每次未达到整体 `UP` 后统一等待 1 秒，保留完整的 30 秒重试窗口
- 测试命令：`./code/tools/start-dev.ps1`、`npm run test:e2e:live`、`./code/tools/stop-dev.ps1`
- 结果：完整健康链路达到 `UP`；真实链路 Playwright 1/1；停止后项目服务正常退出
- 结论：启动竞态已修复，人工验收可重新执行启动步骤

## 2026-08-30｜S1/M01 非作者验收

- 版本/提交：`chore/m01-project-foundation` 工作区（提交前）
- 环境：Windows 11；VS Code；`school-agent` Conda 环境
- 执行人：夫（非作者验收）
- 关联范围：S1/M01；M01 范围内的 NFR 基础
- 审查内容：开发环境、目录结构、本地配置、三端测试、真实健康链路、数据库迁移、pgvector、依赖安全、日志与硬编码、阶段范围和启停恢复
- 问题处理：首次人工启动暴露健康检查重试竞态；修复后重新执行完整启动和真实链路验证通过
- 结果：JUnit 7/7；pytest 5/5；隔离 Playwright 2/2；真实链路 Playwright 1/1；Flyway 2/2；npm 高危漏洞 0
- 缺陷：验收发现的启动竞态已修复并回归通过；无遗留 S1/S2 缺陷
- 结论：通过，S1/M01 标记“已验收”，允许进入 S2/M02

## 2026-08-30｜部署配置目录迁移回归验证

- 版本/提交：`chore/m01-project-foundation` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda 环境
- 执行人：Codex
- 调整内容：将 `deploy` 从仓库根目录迁移到 `code/deploy`，同步脚本默认配置路径和全部项目文档
- 安全检查：`code/deploy/.env.local` 继续被 Git 忽略，真实配置未进入版本控制
- 测试命令：
  - `./code/tools/check-env.ps1`
  - `./code/tools/test-all.ps1`
  - `./code/tools/start-dev.ps1`
  - `npm run test:e2e:live`
  - `./code/tools/stop-dev.ps1`
- 结果：JUnit 7/7；pytest 5/5；隔离 Playwright 2/2；真实链路 Playwright 1/1；前端构建成功
- 结论：配置迁移后编译、测试、真实启动、配置读取和停止流程全部通过
