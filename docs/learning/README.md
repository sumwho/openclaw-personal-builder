# OpenClaw 学习资料

这套资料面向当前仓库的最终运行方式：

- 本地 macOS 宿主机运行 OpenClaw
- 通过 `make gui-gateway` / `make gui-dashboard` 使用 Control UI
- 模型提供方使用 Qwen（DashScope 兼容接口）
- 默认状态目录使用 `.openclaw-dev/state-live/`
- 安全策略采用“默认保守、额外权限必须确认”

## 建议学习顺序

1. [01-overview.md](./01-overview.md)
   先建立整体心智模型，理解 OpenClaw 到底是什么，不是什么。
2. [02-architecture.md](./02-architecture.md)
   理解 Gateway、Control UI、Agent、Workspace、State 之间的关系。
3. [03-configuration-and-qwen.md](./03-configuration-and-qwen.md)
   学会读懂当前项目配置，并理解 Qwen 接入链路。
4. [04-tools-and-approvals.md](./04-tools-and-approvals.md)
   理解工具系统、权限边界、审批策略、为什么要严格控制宿主机执行。
5. [05-operations-and-troubleshooting.md](./05-operations-and-troubleshooting.md)
   把知识落到日常启动、停止、验证、排障。
6. [06-security-review.md](./06-security-review.md)
   从安全视角复盘 OpenClaw，建立长期正确的操作习惯。

## 学习目标

读完这套资料后，你应该能回答这些问题：

- OpenClaw 的核心运行单元是什么？
- Gateway 与 Control UI 分别负责什么？
- 为什么同一个模型能“可用”但仍然出现 `NO_REPLY`？
- 为什么状态目录会影响行为？
- OpenClaw 的工具权限与宿主机安全是如何关联的？
- 为什么 `openclaw gateway stop` 停不掉 `make gui-gateway` 启动的进程？
- Qwen 接入时，`apiKey`、provider、model、auth profile 分别处在什么层？

## 本项目中的关键路径

- 配置文件：`/.openclaw-dev/config.json`
- 本地 workspace：`/.openclaw-dev/workspace/`
- 当前状态目录：`/.openclaw-dev/state-live/`
- 本地启动脚本：`/src/tools/openclaw_local.sh`
- 配置种子脚本：`/src/tools/openclaw_seed_config.mjs`
- 运维手册：`/docs/runbook.md`

## 建议学习方法

- 先读 `overview` 和 `architecture`，不要一上来陷入命令细节
- 再对照当前仓库的 `.openclaw-dev/config.json` 一项项看
- 然后实际执行 `make gui-gateway`、`make gui-dashboard`、`make gui-stop`
- 最后阅读 `security-review`，建立长期操作边界
