# 需求追踪矩阵

状态取值：`待设计`、`开发中`、`待验收`、`已验收`、`受阻`。本矩阵用于连接需求、设计、代码、测试和验收证据；功能开发开始后按需求编号逐项展开。

| 需求域 | 需求范围 | 设计/ADR | 代码模块 | 测试/验收 | 状态 |
|---|---|---|---|---|---|
| M01 | 工程基础、公共配置与可运行性 | 技术开发报告 M01、ADR-0001、M01 公共工程契约 | `code/apps/web`、`code/services/core-service`、`code/services/agent-service`、`code/deploy`、`code/tools` | `M01_ACCEPTANCE.md`、三端冒烟与真实链路测试 | 已验收 |
| IAM | FR-IAM-001～008 | 技术开发报告 M02、M02 身份用户与授权设计 | `core/identity`、`core/security`、Web 个人中心 | AT-01、AT-15、`M02_ACCEPTANCE.md` | 已验收 |
| AGT | FR-AGT-001～010 | 技术开发报告 M04、M04 通用 Agent 平台设计、ADR-0001 | `agent-service` 工作流/模型/工具/持久化、Web 智能助手、Flyway V7 | `test_workflow.py`、`test_tools.py`、`agent.spec.ts`、`live-agent.spec.ts`、`M04_ACCEPTANCE.md` | 待验收 |
| FOOD | FR-FOOD-001～015 | 技术开发报告 M05 | 待创建 | AT-02～04 | 待设计 |
| EXAM | FR-EXAM-001～013 | 技术开发报告 M06 | 待创建 | AT-05～09 | 待设计 |
| BOOK | FR-BOOK-001～012 | 技术开发报告 M07 | 待创建 | AT-10～12 | 待设计 |
| QA | FR-QA-001～010 | 技术开发报告 M08、ADR-0001 | 待创建 | AT-13、AT-14 | 待设计 |
| ADM | FR-ADM-001～008 | 技术开发报告 M03、M03 统一信息资料管理设计 | `core/management`、Web 管理台、Flyway V5/V6、M03 CSV 模板 | AT-16、AT-18、`M03_ACCEPTANCE.md` | 已验收 |
| NFR-M01 | M01 范围内的可用性、安全与可维护性基础 | 技术开发报告 M01、ADR-0001、M01 公共工程契约 | 三端工程、配置预检、日志脱敏、测试与启停脚本 | `M01_ACCEPTANCE.md`、M01 基础证据 | 已验收 |
| NFR | 后续性能、安全、AI 质量与全局验收 | 技术开发报告 M09/M10、ADR-0001 | 待后续阶段实现 | AT-15～18 | 待设计 |

## M02 单项追踪

| 需求编号 | 设计 | 实现位置 | 自动化测试 | 人工验收 | 状态 |
|---|---|---|---|---|---|
| FR-IAM-001 | M02 设计 3.1、5.1 | `RegistrationService`、`AuthController`、`AuthService`、注册/登录页、V4 数据约束 | `RegistrationServiceTest`、`identity.spec.ts`、注册 live、AT-01 live | `M02_ACCEPTANCE.md`，夫验收通过 | 已验收 |
| FR-IAM-002 | M02 设计 3.2 | `TokenService`、`AuthSessionRepository`、会话校验过滤器 | AT-01 刷新旋转、旧令牌退出失效 | 同上 | 已验收 |
| FR-IAM-003 | M02 设计 4.1 | `UserService.profileById`、方法级角色校验 | `UserServiceTest`、AT-15 双用户越权 | 同上 | 已验收 |
| FR-IAM-004 | M02 设计 5.2 | 用户资料接口与个人中心 | `identity.spec.ts`、Java 构建 | 同上 | 已验收 |
| FR-IAM-005 | M02 设计 5.3 | 偏好接口、JSONB 持久化与表单 | `identity.spec.ts`、真实数据库迁移 | 同上 | 已验收 |
| FR-IAM-006 | M02 设计 4.2 | 四类 `data_authorization`、默认拒绝授权页 | `UserServiceTest`、隔离 E2E、AT-15 | 同上 | 已验收 |
| FR-IAM-007 | M02 设计 4.3 | 撤回授权、长期记忆删除、清理记录 | `UserServiceTest`、AT-15 | 同上 | 已验收 |
| FR-IAM-008 | M02 设计 4.4 | 独立事务审计、本人/管理员检索接口 | AT-15 审计检索与管理员边界 | 同上 | 已验收 |

## M03 单项追踪

| 需求编号 | 设计 | 实现位置 | 自动化测试 | 人工验收 | 状态 |
|---|---|---|---|---|---|
| FR-ADM-001 | M03 设计 1、3、6 | `AdminWorkspace.vue`、`ManagementController` | `management.spec.ts`、AT-16 live | `M03_ACCEPTANCE.md`，夫验收通过 | 已验收 |
| FR-ADM-002 | M03 设计 1、3、5 | `@PreAuthorize`、账号安全摘要接口 | AT-16 学生 403、既有权限回归 | 同上 | 已验收 |
| FR-ADM-003 | M03 设计 2、4 | `ResourceSchema`、`ResourceValidator`、完整度刻度 | `ResourceValidatorTest`、管理台 E2E | 同上 | 已验收 |
| FR-ADM-004 | M03 设计 2 | 食堂/窗口/食材/菜品表与动态表单 | Java 校验、隔离 E2E、真实 CRUD | 同上 | 已验收 |
| FR-ADM-005 | M03 设计 2 | 书目/馆藏表与动态表单 | Java 校验、模板及真实迁移 | 同上 | 已验收 |
| FR-ADM-006 | M03 设计 2、4 | 校园公告标题、类别、关键词、正文、来源及 V6 数据转换 | `ResourceValidatorTest`、CSV 模板及真实迁移 | 同上 | 已验收 |
| FR-ADM-007 | M03 设计 3、4 | 通用 CRUD、搜索、每页 20 条分页、有效/停用筛选、CSV 两阶段导入 | `management.spec.ts` 分页/筛选、`CsvTableParserTest`、AT-16、AT-18 | 同上 | 已验收 |
| FR-ADM-008 | M03 设计 2、5 | 统一审计字段与 `admin_operation_log`，展示操作者账号、作用对象和请求编号 | `ManagementServiceTest`、`management.spec.ts` 日志字段/分页、AT-16 操作记录 | 同上 | 已验收 |

## M04 单项追踪

| 需求编号 | 设计 | 实现位置 | 自动化测试 | 人工验收 | 状态 |
|---|---|---|---|---|---|
| FR-AGT-001 | M04 设计 2、3、4 | 会话/消息仓库、`AgentWorkspace.vue` | 多轮 live、会话所有权 | `M04_ACCEPTANCE.md` | 待验收 |
| FR-AGT-002 | M04 设计 3 | `IntentRouter`、LangGraph `StateGraph` | 20 条标准意图集 20/20 | 同上 | 待验收 |
| FR-AGT-003 | M04 设计 3 | 缺失字段节点、`follow_up_message` | 考试两轮必要追问 | 同上 | 待验收 |
| FR-AGT-004 | M04 设计 2、6 | `ToolRegistry`、`ToolExecutor`、身份解析 | 参数/角色拒绝、20 条工具成功集 | 同上 | 待验收 |
| FR-AGT-005 | M04 设计 3、5 | SSE 路由、状态/意图/工具/文本/完成事件 | 流式前端测试、失败后可重试 | 同上 | 待验收 |
| FR-AGT-006 | M04 设计 3 | `WorkflowResult` 的 basis、limitations、structuredResult | SSE/live 结构断言 | 同上 | 待验收 |
| FR-AGT-007 | M04 设计 6 | 系统约束、输出校验、安全降级 | 提示注入、无依据清单拒绝、真实模型联调 | 同上 | 待验收 |
| FR-AGT-008 | M04 设计 4、5 | 记忆 API、M02 授权复用、右侧偏好架 | 未确认拒绝、授权后 CRUD live | 同上 | 待验收 |
| FR-AGT-009 | M04 设计 6 | 模型超时/重试、降级结果和任务持久化 | 模型不可用、流失败恢复 | 同上 | 待验收 |
| FR-AGT-010 | M04 设计 4、5 | `agent_feedback`、四类反馈按钮 | 结果版本关联反馈 live | 同上 | 待验收 |

## 单项追踪模板

| 需求编号 | Issue/PR | 设计 | 实现位置 | 自动化测试 | 人工验收 | 负责人 | 状态 |
|---|---|---|---|---|---|---|---|
| FR-XXX-001 | # | ADR/设计文档 | 路径或服务 | 测试路径 | 证据路径 | 待分配 | 待设计 |
