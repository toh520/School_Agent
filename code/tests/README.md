# 跨服务测试目录

本目录保留给需要同时启动两个以上服务的契约、集成、安全和最终验收测试。

M01 当前的单服务测试分别靠近所属工程：

- Java：`code/services/core-service/src/test`
- Python：`code/services/agent-service/tests`
- Web 与真实健康链路：`code/apps/web/tests`

后续阶段不得把某一业务模块的普通单元测试集中堆放到本目录。
