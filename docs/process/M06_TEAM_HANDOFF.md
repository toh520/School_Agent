# M06 队友接手与本地测试

分支：`feature/m04-agent-platform`。本交接包包含当前项目代码、迁移、测试、缺陷报告，以及已使用的三门课程资料。有效API密钥通过私密渠道单独交接，不能写入Git历史。

## 数据范围

- `学习资料/学习资料/数据结构`：29份；`算法设计与分析`：31份；`计算机网络`：21份，共81份，约356 MiB。其他课程不上传。
- `code/deploy/fixtures/m06-course-index.json.gz`：约9 MB，只导出三门课程的81条资料元数据和3335条向量索引，不是整个原数据库的备份。
- `code/deploy/fixtures/m06-demo.sql`：合成的3场考试、1道练习、2次作答、1条错题和1条学习活动，用于测试列表、评分展示和历史恢复。没有导出原用户作答或考试。
- 表结构与其他基础演示数据由现有Flyway迁移恢复；本交接不修改迁移历史，也不覆盖既有账号与授权。
- 不包含本地数据库目录、账号密码哈希、会话令牌、聊天记录、上传附件、日志、个人学习历史、JWT密钥或API密钥。

资料保持课程原文。文件名及已有索引文本已做初步检查：未匹配到API密钥或手机号模式；存在教师署名、课件教学联系方式及邮件协议教学示例，未把这些误当作本地账号数据。此检查不等于逐页人工隐私/版权审计，资料仅按项目协作授权提供；进一步分发前需确认相应权利。

## 第一次运行（Windows PowerShell）

先按根目录README准备相同开发环境：Python 3.12、Java/Maven、Node/npm和支持pgvector的PostgreSQL；激活 `school-agent`。不要将本地开发服务开放到公网。

```powershell
git clone --branch feature/m04-agent-platform https://github.com/toh520/School_Agent.git
cd School_Agent
conda activate school-agent
Copy-Item code/deploy/.env.example code/deploy/.env.local
```

编辑 `.env.local`，填入自己的数据库密码、至少32字符的随机JWT密钥，以及通过私密渠道获得的SiliconFlow API密钥。若暂不测试真实模型，可将模型密钥占位符替换为 `disabled-for-local-tests`：模型调用会失败，但可测试考试及历史功能。此值不是有效密钥。

```powershell
./code/tools/check-env.ps1
./code/tools/install-dependencies.ps1
./code/tools/test-all.ps1
./code/tools/start-dev.ps1
./code/tools/import-m06-demo.ps1
```

必须先启动一次，让Flyway完成迁移，再导入演示数据。**导入前不要在页面触发资料同步**：归档仅允许导入空索引，非空会拒绝且不会删表。如果已完成自己的索引同步，只导入合成练习数据：

```powershell
./code/tools/import-m06-demo.ps1 -SkipIndex
```

SQL样例按固定演示ID防重复插入，不覆盖用户原记录。默认学生账号及测试密码见README；仅限本地环境。登录后在授权页面开启考试和掌握度权限（EXAMS/MASTERY），再进入考试助手。

向量索引使用 `BAAI/bge-small-zh-v1.5`（512维），查询仍需同一嵌入模型；缓存不入库，队友首次使用时可能需要联网下载。文档解析依赖也需正常安装；旧版DOC/PPT转换需要可用的Office兼容环境，详见代码和环境说明。复制资料后文件时间戳可能不同，但增量同步会结合内容哈希判断，不必直接删除现有索引。

## 建议接手检查

1. 三场演示考试可见，练习记录中能展开两次合成作答。
2. 查询资料能定位到三门课；运行同步确认文件可访问。
3. 用真实模型验证“提问→追问→纠错→重新讲解”，勿把HTTP成功视为答案正确。
4. 回归 `M06_SPECIAL_CASE_FIXES.md` 与原始审计报告中的案例。`tmp/`内真实测试日志未上传（可能包含用户上下文），稳定测试代码和脱敏问题描述已上传。
5. 停止测试：`./code/tools/stop-dev.ps1`。

索引导入由单个事务执行，失败回滚；归档只允许固定表/列/课程。若需要重新导入，请另建本地测试数据库，不要清空他人的数据或强制覆盖。

## 本次交接验证（2026-09-04）

在独立临时数据库顺序执行V1～V19及R迁移，再恢复归档与演示SQL：81份文件SHA-256与归档一致；81条资料、3335条索引、3场考试、2次作答数量正确；会话及附件均为0。重复索引导入被拒绝、重复样例导入未产生重复记录。临时验证库已删除，原数据库未修改。
