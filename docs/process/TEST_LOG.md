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

## 2026-08-31｜S3/M03 非作者验收

- 验收人：夫
- 关联范围：FR-ADM-001～008、AT-16、AT-18、M03 完整功能与数据边界
- 复核依据：`docs/process/M03_ACCEPTANCE.md`、完整自动化测试结果和实际页面/数据库检查
- 验证结果：Java 26/26；pytest 5/5；隔离 Playwright 9/9；真实 Playwright 7/7；数据库当前版本 V6
- 缺陷：无遗留 S1/S2 缺陷；Element Plus 单包体积警告为已记录的非阻断性能事项
- 结论：通过，S3/M03 标记为“已验收”，允许进入 S4/M04

## 2026-08-31｜M03 分页、停用筛选与操作日志回归

- 版本/提交：`feature/m03-information-management` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda；OpenJDK 21；PostgreSQL 16；Node.js 24
- 关联需求：FR-ADM-007、FR-ADM-008、AT-16
- 测试命令：`./code/tools/test-all.ps1`、`npm run test:e2e:live`、真实页面 DOM 与截图检查
- 结果：JUnit 26/26；pytest 5/5；隔离 Playwright 9/9；真实 Playwright 7/7；类型、格式、生产构建和 JAR 打包通过
- 新增覆盖：资料分页与总数、有效/已停用筛选、操作日志字段与分页、重复编码 HTTP 409、真实日志操作者账号和请求编号
- 页面验证：真实停用资料共 5 条可见；操作记录共 34 条并出现分页；管理员账号、作用对象和请求编号均正确显示
- 已知问题：仅保留既有 Element Plus 单包大于 500KB 的非阻断构建警告
- 结论：本次 M03 完善项通过开发者验证，等待非作者按更新后的验收步骤复核

## 2026-08-31｜校园公告简化与 RAG 数据契约回归

- 版本/提交：`feature/m03-information-management` 工作区（提交前）
- 关联需求：FR-ADM-006、FR-QA-001～010 的数据契约
- 测试命令：`./code/tools/test-all.ps1`、`npm run test:e2e:live`、Flyway 启动迁移、真实页面 DOM 检查
- 结果：JUnit 25/25；pytest 5/5；隔离 Playwright 7/7；真实 Playwright 7/7；构建与格式检查通过
- 数据验证：Flyway 从 V5 升级至 V6；校园公告 Schema 仅包含编码、标题、类别、关键词、正文和来源；关键词按列表持久化并可通过管理搜索命中
- 页面验证：导航显示“校园公告”，新增表单只显示六项字段，未残留版本、权限、有效期或附件字段
- 范围验证：未实现向量索引、检索器、RAG 或大模型回答
- 结论：校园公告简化满足变更后的 M03 数据契约

## 2026-08-31｜S3/M03 统一信息资料管理开发者验证

- 版本/提交：`feature/m03-information-management` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda；OpenJDK 21；PostgreSQL 16；Node.js 24
- 执行人：Codex（实现与自测）；非作者复现待完成
- 关联需求：FR-ADM-001～008、AT-16、AT-18
- 测试命令：`./code/tools/test-all.ps1`、`npm run test:e2e:live`、`./code/tools/start-dev.ps1`、浏览器桌面/390px 检查
- 结果：JUnit 25/25；pytest 5/5；隔离 Playwright 7/7；真实 Playwright 7/7；类型、格式、生产构建和 JAR 打包通过
- 真实场景：学生访问管理接口 403；管理员新增、搜索、更新、停用和停用状态核查；操作日志动作完整；CSV 负数错误定位至第 2 行具体字段；修正后预校验和确认入库成功
- 数据迁移：Flyway V5 在既有 V4 数据库成功应用，V6 完成校园公告字段收敛；八类资料和操作日志表可用
- 页面检查：桌面和 390px 无横向溢出；控制台无 warning/error；页面不含开发状态、基础服务状态或 Demo 字样
- 缺陷处理：首次真实测试发现 `INACTIVE` 检索受逻辑删除条件遮蔽，修复后完整复测通过；无遗留 S1/S2 缺陷
- 已知问题：Element Plus 单包大于 500KB 的构建警告不影响功能，留待性能阶段处理
- 结论：S3/M03 满足开发者退出条件，状态为“待验收”

## 2026-08-31｜S2/M02 非作者验收

- 验收人：夫
- 关联范围：FR-IAM-001～008、AT-01、AT-15、M02 数据库与前端页面
- 复核依据：`docs/process/M02_ACCEPTANCE.md`、本文件中的开发者测试批次和实际页面/数据库检查
- 验证结果：Java 15/15；pytest 5/5；隔离 Playwright 5/5；真实 Playwright 4/4；数据库当前版本 V4
- 缺陷：无遗留 S1/S2 缺陷
- 结论：通过，S2/M02 标记为“已验收”，允许进入 S3/M03

## 2026-08-31｜M02 学生注册与前端优化回归验证

- 版本/提交：`feature/m02-identity-access` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda；OpenJDK 21；PostgreSQL 16；Node.js 24
- 关联需求：FR-IAM-001～008、AT-01、AT-15
- 测试命令：`./code/tools/test-all.ps1`、`npm run test:e2e:live`、`./code/tools/start-dev.ps1`、`./code/tools/stop-dev.ps1`
- 结果：JUnit 15/15；pytest 5/5；隔离 Playwright 5/5；真实 Playwright 4/4；类型、格式和生产构建通过
- 注册场景：身份字段校验、密码确认、用户/偏好/四项授权原子创建、自动登录、身份资料回显、默认拒绝和注册审计均通过
- 数据迁移：Flyway V4 成功应用，学号/手机号/账号唯一性及学生字段约束由 PostgreSQL 兜底
- 页面检查：注册字段完整；新版标题与身份凭证布局生效；未显示开发阶段、基础服务状态及测试性页面字样
- 工程回归：样式文件均小于 500 行；停止脚本在启动器进程提前退出时可继续完成清理
- 已知问题：Element Plus 仍产生单包体积警告，不影响当前 M02 功能；留待性能阶段按路由拆包
- 结论：M02 学生注册、数据设计和前端优化通过开发者自测，状态保持“待验收”

## 2026-08-30｜S2/M02 身份、用户与授权验证

- 版本/提交：`feature/m02-identity-access` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda；OpenJDK 21；PostgreSQL 16；Node.js 24
- 执行人：Codex（实现与自测）；非作者复现待完成
- 关联需求：FR-IAM-001～008、AT-01、AT-15
- 测试命令：`mvn --batch-mode spotless:check test package`、`npm run check`、`npm run build`、`npm run test:e2e`、`npm run test:e2e:live`
- 结果：JUnit 12/12；隔离 Playwright 4/4；真实 Playwright 3/3；构建与格式检查通过
- 真实场景：登录、默认拒绝、刷新令牌旋转、退出立即失效、双用户越权 403、撤回授权与清理、学生/管理员审计边界、基础健康链路
- 数据迁移：Flyway 成功从 V1 升至 V3，身份与授权表、本地测试账号及中性显示名称创建成功
- 回归修复：方法级权限拒绝由 500 修正为稳定 403；停止脚本 PowerShell 字符串匹配兼容问题修复并验证
- 已知问题：无已知 S1/S2 缺陷；前端 Element Plus 单包体积有构建警告，不影响功能，后续可在性能阶段按路由拆包
- 结论：M02 实现满足退出条件的开发者自测部分，状态为“待验收”

## 2026-08-31｜M02 页面正式化回归验证

- 关联范围：M02 登录页、本地测试账号名称和健康链路展示边界
- 测试命令：`./code/tools/test-all.ps1`、`npm run test:e2e:live`、Flyway 启动校验、浏览器 DOM 检查
- 结果：JUnit 12/12；pytest 5/5；隔离 Playwright 4/4；真实 Playwright 3/3；前端构建通过
- 页面检查：不显示“演示/Demo”、开发阶段编号或基础服务运行状态；账号和密码没有预填
- 数据检查：Flyway 成功校验 4 条迁移，当前版本 V3；学生显示名称更新为中性名称
- 结论：正式化调整完成，无新增 S1/S2 缺陷

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
