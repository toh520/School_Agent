# M02 PostgreSQL 表格操作指南

项目使用 PostgreSQL 16。VS Code 已安装 Database Client 扩展，可像常见 MySQL 管理工具一样通过数据库树和数据网格查看、筛选及编辑表记录。

## 1. 建立本地连接

1. 先在仓库根目录执行 `./code/tools/start-dev.ps1`。
2. 点击 VS Code 左侧的 Database 图标，选择 `Create Connection`。
3. 数据库类型选择 `PostgreSQL`。
4. 填写以下字段：

| 字段 | 本地值 |
|---|---|
| Host | `127.0.0.1` |
| Port | `5432` |
| Database | `school_agent` |
| Username | `school_agent` |
| Password | 从被 Git 忽略的 `code/deploy/.env.local` 读取 |
| SSL | 本地环境关闭 |

连接名称建议填写 `School Agent Local`。不要把密码写入项目文件、截图或共享配置。

## 2. 使用表格操作

连接成功后依次展开 `school_agent → public → Tables`：

- 右键 `app_user`，选择打开表数据，可查看注册账号、学号、姓名、手机号、角色和状态；
- 使用数据网格顶部筛选、排序和分页；
- 双击普通单元格可修改本地测试数据，点击保存按钮后提交；
- 可在数据网格中新增或删除本地测试行，但涉及关联数据时优先通过系统接口操作。

## 3. 安全边界

- 表结构、约束和索引只能通过 Flyway 迁移修改，不要在图形界面手工改表结构；
- 不要编辑 `flyway_schema_history`；
- 不要查看、复制或手工设置 `password_hash`、刷新令牌摘要和 JWT 密钥；
- 用户、授权和清理操作优先使用系统页面或 API，以保留校验、事务和审计记录；
- 数据网格直接修改只适用于本机开发检查，不用于共享或正式数据库。

## 4. 常用表

| 表 | 用途 |
|---|---|
| `app_user` | 账号、学生身份、角色和状态 |
| `user_preference` | 饮食偏好 |
| `data_authorization` | 四类数据授权状态 |
| `auth_session` | 登录会话及撤销状态 |
| `data_cleanup_record` | 授权撤回和数据清理记录 |
| `audit_event` | 登录、注册、授权和敏感访问审计 |
