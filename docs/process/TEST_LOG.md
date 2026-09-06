# 测试与验收记录

测试代码、报告和截图应保存在仓库中的稳定路径或 CI 构建产物中，本文件记录可复核的执行摘要。

## 2026-09-06｜M06 讲解与解析最终全量回归

- 范围：知识讲解、题目解析、错因诊断、追问纠错、三档学习目标、三档当前基础、无答案自测、附件/课程资料/AI 补充来源、资料冲突、失败降级、长对话和页面动态编号。
- 自动化：Agent Ruff 格式与规则检查通过，pytest 191/191；Web TypeScript/Prettier 检查和生产构建通过；全量隔离 Playwright 28/28。
- 真实模型：DeepSeek/SiliconFlow 完成数据结构层序遍历快速讲解和计算机网络 TCP 拥塞避免深入讲解；深入讲解最终返回 6 项前置知识、6 项核心概念、4 个步骤、例题、4 个易错点、记忆提示、自测题和 5 个课程资料来源，状态 `MATERIAL_SUPPORTED`。
- 真实页面：学生登录并进入讲解工作台后生成层序遍历讲义，页面按 `01` 至 `07` 连续展示一句话结论、前置知识、核心概念、推导步骤、例题、易错点和自测，未再出现跳号或重复编号。
- 本轮修复：可选栏目隐藏后使用可见栏目动态编号；诊断结果缺失时定向补全错因；隐藏内部审查字段；换例再讲必须更新例题结论；深入/考试复习目标缺少前置知识或例题时先定向补全再审查，补全失败才拦截。
- 环境边界：项目 `.venv` 启动器仍引用已删除的 Conda 基础解释器，本轮复用其中依赖并以 Codex Python 执行测试与 Agent；前端仍有既有的大于 500KB 分块警告。

## 2026-09-06｜M06 功能升级全量评审与边界回归

- 范围：学生考试只读总览、管理员考试维护、分层讲解/解题/诊断/纠错、资料与附件引用、错题本、个性化练习、复习计划版本及授权降级路径。
- 自动化：Ruff check/format 通过，pytest 191/191；Java Spotless/JUnit/package 34/34；Web TypeScript/Prettier 与生产构建通过；隔离 Playwright 28/28；真实考试管理 API 1/1。
- 考试题型参考：个性化练习检索为往年试卷、期末卷、样卷等考试资料保留优先名额，另保留教材/课件片段核对知识。真实“数据结构—二叉树遍历”索引返回 2 个考试题型片段和 3 个内容核对片段；对外仅保存“AI 生成（参考课程考试题型）”，不保存原题级来源。
- 真实模型：DeepSeek/SiliconFlow 完成长度17二分查找解析（5次）、错误作答4次的具体诊断、追问后改用长度8示例（4次）和无答案二叉树自测。最终自测 `steps=0`、`selfTestAnswer` 为空、不展示来源性结论。
- 修复：二分查找内部字段缺失误拦截、中文比较次数多种语序校验、可确定错因自动补齐、诊断去重与内部审查字段隐藏、附件重复/超长上下文、附件与课程资料来源混用、考试进行中文案、管理端删除失败反馈、源考试删除后计划过期判定及复习偏好文案误导。
- 真实全套 Playwright 当时为 7/9；两项失败分别来自共享数据库中学生授权状态与测试预期不一致、当时运行的 Core JAR 未包含最新校园知识字段；考试助手真实链路通过，这两项未作为 M06 功能失败隐藏。
- 已知边界：模型生成加独立审查在服务商繁忙时可接近 3 分钟；前端未设短超时，服务端模型失败时不写学习记录。Element Plus 仍有大于 500KB 的构建分块警告。

## 2026-09-06｜M06 讲解与解析分层及证据专项

- 范围：三种提问模式、学习目标/当前基础、分层讲义、提示渐进展开、最终答案隔离、RAG 来源索引、无资料降级、附件状态、资料冲突、纠错差异、自测防泄露、多轮上下文及原有考试助手回归。
- Agent：`ruff check .` 与 `ruff format --check .` 通过；pytest 172/172。新增验证模型上下文、有效/无效来源索引、无资料降级、附件来源约束、所有结构化答案字段清空、内部审查字段隐藏和步骤编号清理。
- Core：`mvn --batch-mode spotless:check test package` 通过；JUnit 34/34，JAR 打包成功。
- Web：`npm run check`、`npm run build` 通过；Playwright 全量 24/24，其中 `learning-explanation.spec.ts` 5/5。
- 真实页面：本地三端健康链路启动后，以学生账号进入考试助手；默认桌面宽度和 390×844 移动视口均可访问三种场景、课程、基础、目标、示例、附件和提交控件，浏览器控制台无 error/warning。
- 真实模型：通过学生页面两次请求“为什么二叉树层序遍历使用队列”，均返回 `MATERIAL_SUPPORTED`，关键结论定位到《数据结构 陈越 第2版》第124页等真实片段；第二次确认公开校验说明不再暴露内部字段且步骤序号不重复。
- 修复闭环：首次浏览器测试发现 Element Plus 组合控件定位方式不稳定，改为按可见控件容器和准确角色定位后复测通过；真实模型页面检查发现审查文字暴露内部字段、步骤序号重复，服务端收敛公开校验说明并清理列表前缀后新增测试通过。
- 已知边界：Playwright 使用可控模型响应验证协议和交互，不代表任意真实模型回答必然正确；构建保留既有大于 500KB 分块告警。

## 2026-09-06｜M06 考试助手完善回归

- 关联需求：FR-EXAM-002～003、FR-EXAM-005～009、FR-EXAM-013～020。
- 静态与单元测试：Ruff 修改模块检查通过；pytest 166/166；Java Spotless/JUnit/package 34/34；Vue TypeScript/Prettier 通过；前端生产构建通过。
- 浏览器测试：全部隔离 Playwright 19/19，其中 `tests/exam.spec.ts` 7/7；真实考试管理 Playwright 1/1。新增生成并保存可追溯复习计划场景，原考试查看、RAG 问答、纠错、错题历史和上下文边界继续通过。
- 数据迁移：首次增量打包残留已删除的旧 V20，Flyway 拒绝启动且未执行迁移；执行 Maven clean 后重建修复。最终 Flyway `20:enhance exam review plans:true`，`knowledge_mastery` 原有 2 条记录保留。
- 真实接口：SiliconFlow 请求 HTTP 200；计划生成得到 3 个阶段且阶段总时长为 150 分钟；重新生成后保留 v1/v2 两个版本且仅 v2 为当前版；标记错题已掌握后恢复原状态；两批临时计划均已删除。
- 已修复问题：旧 V20 破坏性删表与新功能冲突、Maven 资源缓存保留旧迁移、拆分后测试的数据库模拟路径失效。
- 已知警告：前端主分块仍大于 500KB，为既有 Element Plus 打包问题，不影响本次功能。

## 2026-09-04｜M06 特殊情况修复

- Python 182/182、Java 33/33、全量浏览器18/18；lint、格式、Web类型与构建通过。
- 修复缺失过程诊断、条件替换、自测、选择题、计划、评分、事务及历史回看等缺陷。
- 真实扩展测试继续发现校验元数据编造和程序样例错误，查阅GitHub后补充程序拥有的规则证据及样例参考算法。
- 真实测试、已知边界、原始证据路径及外部参考见 [M06特殊情况修复报告](M06_SPECIAL_CASE_FIXES.md)。未提交/推送。

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

## 2026-09-05｜管理员考试安排保存故障回归

- 关联范围：考试记录管理、管理员接口运行包一致性
- 根因：运行 JAR 不包含新增 `ExamAdminController`，且旧进程占用 JAR导致 Spring Boot 重新打包失败
- 测试命令：`mvn --batch-mode spotless:check test package`、`live-exam.spec.ts`、真实管理员 API 新增/查询/删除
- 结果：JUnit 34/34；真实考试管理链路 1/1；临时考试记录已清理
- 结论：新增考试安排接口已恢复；启动脚本会阻止过期 JAR 再次启动

## 2026-09-04｜M06 扩展回归及直接修复

- 自动化：Python139/139、Java33/33、全量Playwright17/17，Ruff lint、Web check/build通过。
- 真实测试：两轮各20个模型相关请求，随后对纯自测/选择/证明反复测试；发现问题即补回归和修复，不把响应成功当成内容通过。
- 修复重点：计划UUID序列化、输入及附件边界、评估布尔和百分制、完整练习集保存前校验、选择题完整性、证明完整性、题目/步骤/审查文本泄露、遍历参考算法、前端上下文竞态。
- 既有3项管理浏览器测试已更新至当前公共配置入口，保持CRUD/导入/分页断言；未改变旧页面方案。
- 报告与局限：`M06_EXTENDED_REGRESSION.md`。部分内容依然依赖概率模型和独立审查，不能声称覆盖所有题目或全部附件。

## 2026-09-04｜M06 闭环缺陷修复与复测

- 修复：有界多轮历史、最新诉求优先、纠错归因、完整上下文审查、一次修复后复审及失败拦截、二分查找确定性次数校验。
- 自动化：pytest 100/100；M06 Playwright 2/2；Ruff lint、Web check 和生产构建通过。构建仍有既有大于500KB分块告警。
- 真实模型：经用户授权调用 SiliconFlow DeepSeek-V4-Flash，最终三组8次学习请求完成；前序/中序对比及无答案自测、二分查找最坏5次、原子网广播地址 .127 均符合预期。
- 迭代发现：首次修复复测仍出现模型与审查共同接受错误比较次数，增加确定性规则后最终复测通过。
- 范围说明：没有重跑全量 Java 或全量浏览器测试；此前3项 M03 浏览器测试基线债务未改动。Python 全量格式检查还发现 office_convert.py、study_materials.py、test_study_materials.py 的既有格式差异，本轮仅格式化修改的闭环测试文件。
- 报告：`M06_LOOP_TEST.md`；资料不足的回答保持 PARTIAL，不声称教材支持或任意题目的普遍正确性。

## 2026-09-04｜M06 考试与学习助手开发者验证

- 版本/提交：`feature/m04-agent-platform` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda；OpenJDK 21；PostgreSQL 16 / pgvector 0.8.3；Node.js 24；SiliconFlow 配置保留
- 执行人：Codex（实现与自测）；非作者复现待完成
- 关联需求：FR-EXAM-001～020
- 测试命令：Maven Spotless/JUnit/package、Python Ruff/pytest、`npm run check`、`npm run build`、Playwright、真实本地 API 与资料扫描
- 自动化结果：JUnit 33/33；pytest 90/90；M06 + IAM 定向 Playwright 6/6；类型、格式、JAR 打包和生产构建通过
- 数据迁移：Flyway 在保留既有数据时从 V18 升至 V19；聚合健康链路 Core/Agent/PostgreSQL 全部 UP
- 真实接口：考试创建、列表、删除通过；第二学生更新第一学生考试返回 404；Agent 本机身份回查通过；短作答过程的诊断请求返回 422
- 资料索引：数据结构、算法设计与分析、计算机网络共 81/81 文件最终索引成功；修复 DOCX 图片 OCR、PDF NUL 清理和旧版 Office 隔离转换后定向重试 3/3；第二次扫描 `indexed=0, skipped=81`，耗时 0.4 秒
- 答案验证：单元测试覆盖资料证据状态、独立二次审查、步骤数量、程序题测试样例、精确计划分钟分配和模型失败降级边界
- 真实模型补测（2026-09-04）：用户明确授权检索片段外发后，使用现有 `deepseek-ai/DeepSeek-V4-Flash` 完成前序遍历教材问答；生成与独立审查两次请求均返回 HTTP 200，结论 A、B、C 正确，返回 5 个步骤、5 个来源定位，状态 MATERIAL_SUPPORTED。仅验证本次示例，不代表所有题目均能保证正确。
- 既有测试债务：全套 Playwright 中三个 M03 管理场景仍模拟 `CANTEEN`，但当前管理页已由前序 M05 改为 `DISH`；M06 未修改管理页，故单独记录而不计入 M06 缺陷
- 已知警告：既有 Element Plus 主包大于 500KB；不影响功能
- 结论：M06 模块开发者退出条件及真实模型补测满足，待非作者验收

## 2026-09-01｜S4/M04 通用 Agent 平台开发者验证

- 版本/提交：`feature/m04-agent-platform` 工作区（提交前）
- 环境：Windows 11；`school-agent` Conda；OpenJDK 21；PostgreSQL 16；Node.js 24；Qwen/Qwen3-8B
- 执行人：Codex（实现与自测）；非作者复现待完成
- 关联需求：FR-AGT-001～010、AT-06/14/16 的公共部分
- 测试命令：Python Ruff/pytest、`npm run check`、`npm run build`、Agent 隔离 Playwright、`live-agent.spec.ts`、真实模型安全边界请求
- 结果：JUnit 26/26；pytest 54/54；隔离 Playwright 11/11；真实完整链路 Playwright 8/8；类型、格式、Java 打包和生产构建通过
- 质量集：四类意图 20/20（100%）；测试桩工具 20/20（100%）；非法参数和错误角色均拒绝
- 真实链路：多轮必要追问、SSE、所有权 404、反馈、未确认记忆拒绝、授权后记忆 CRUD、工具契约和会话删除通过
- 模型验证：SiliconFlow Qwen/Qwen3-8B 返回 `COMPLETED`、`fallbackUsed=false`；输出边界检查通过，未生成无依据校园材料
- 已知问题：Element Plus 单包大于 500KB 的既有非阻断构建警告；领域结果必须等待 M05～M08 工具接入
- 结论：S4/M04 满足开发者退出条件，状态为“待验收”

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
