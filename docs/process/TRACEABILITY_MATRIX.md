# 需求追踪矩阵

状态取值：`待设计`、`开发中`、`待验收`、`已验收`、`受阻`。本矩阵用于连接需求、设计、代码、测试和验收证据；功能开发开始后按需求编号逐项展开。

| 需求域 | 需求范围 | 设计/ADR | 代码模块 | 测试/验收 | 状态 |
|---|---|---|---|---|---|
| M01 | 工程基础、公共配置与可运行性 | 技术开发报告 M01、ADR-0001、M01 公共工程契约 | `code/apps/web`、`code/services/core-service`、`code/services/agent-service`、`code/deploy`、`code/tools` | `M01_ACCEPTANCE.md`、三端冒烟与真实链路测试 | 已验收 |
| IAM | FR-IAM-001～008 | 技术开发报告 M02、M02 身份用户与授权设计 | `core/identity`、`core/security`、Web 个人中心 | AT-01、AT-15、`M02_ACCEPTANCE.md` | 已验收 |
| AGT | FR-AGT-001～010 | 技术开发报告 M04、ADR-0001 | 待创建 | AT-06、AT-14、AT-16 | 待设计 |
| FOOD | FR-FOOD-001～015 | 技术开发报告 M05 | 待创建 | AT-02～04 | 待设计 |
| EXAM | FR-EXAM-001～013 | 技术开发报告 M06 | 待创建 | AT-05～09 | 待设计 |
| BOOK | FR-BOOK-001～012 | 技术开发报告 M07 | 待创建 | AT-10～12 | 待设计 |
| QA | FR-QA-001～010 | 技术开发报告 M08、ADR-0001 | 待创建 | AT-13、AT-14 | 待设计 |
| ADM | FR-ADM-001～008 | 技术开发报告 M03 | 待创建 | AT-16、AT-18 | 待设计 |
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

## 单项追踪模板

| 需求编号 | Issue/PR | 设计 | 实现位置 | 自动化测试 | 人工验收 | 负责人 | 状态 |
|---|---|---|---|---|---|---|---|
| FR-XXX-001 | # | ADR/设计文档 | 路径或服务 | 测试路径 | 证据路径 | 待分配 | 待设计 |
