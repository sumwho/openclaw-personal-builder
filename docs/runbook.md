# OpenClaw 项目 Runbook（整理版）

## 1. 文档目标与范围

本 Runbook 面向本仓库当前形态：**容器化构建 OpenClaw 上游源码 + 本地 macOS 上直接运行 openclaw CLI**。  
它不包含 OpenClaw 上游源码本身，只定义“如何在本仓库内稳定执行构建、测试、运行与排障”。

---

## 2. 项目分类总览

### 2.1 仓库角色

- 构建与测试脚手架（Docker + CMake + Ninja + CTest）
- 本地调试入口（`openclaw` 的 `doctor/gateway/dashboard/tui`）
- 文档与流程规范承载

### 2.2 目录职责

- `src/tools/`：运行脚本与兼容层
- `docs/`：操作手册与排障说明
- `assets/game-data/`：本地游戏资源（忽略提交）
- `src/openclaw-upstream/`：上游源码目录（忽略提交）
- `.build/`：构建产物（忽略提交）
- `.cache/`：构建缓存（忽略提交）
- `.openclaw-dev/`：本地 CLI 配置、状态与日志（忽略提交）

---

## 3. 前置条件分类

### 3.1 系统依赖

- 已安装 Docker，并可执行 `docker` 命令
- 已安装 `openclaw` CLI（用于 `make gui-*` 流程）
- 本地以 macOS 宿主机模式运行，不启用 sandbox

### 3.2 必需输入

- 上游源码目录：`src/openclaw-upstream/`（必须包含 `CMakeLists.txt`）
- 合法游戏资源目录：`assets/game-data/`

### 3.3 配置项

可用变量（按需覆盖）：

- `IMAGE_NAME`
- `OPENCLAW_SRC_DIR`
- `OPENCLAW_ASSET_DIR`
- `OPENCLAW_BUILD_DIR`
- `OPENCLAW_CACHE_DIR`
- `OPENCLAW_RUN_BIN`
- `OPENCLAW_NETWORK`（默认 `none`）
- `OPENCLAW_GATEWAY_PORT`
- `OPENCLAW_DASHBOARD_NO_OPEN`

参考模板：`.env.example`

---

## 4. 标准操作 Runbook（按阶段）

### 4.1 阶段 A：初始化

1. 放置上游源码到 `src/openclaw-upstream/`
2. 放置游戏资源到 `assets/game-data/`
3. 构建镜像：

```sh
make build-image
```

### 4.2 阶段 B：构建与测试

1. 构建：

```sh
make build
```

2. 测试：

```sh
make test
```

说明：

- 构建与测试在容器中执行
- 默认源码与资源目录以只读挂载进入容器
- 产物写入 `.build/openclaw/`

### 4.3 阶段 C：运行二进制

```sh
make run OPENCLAW_RUN_BIN=./.build/openclaw/openclaw
```

若路径与实际产物不一致，替换为真实可执行文件路径。

### 4.4 阶段 D：本地 GUI/调试链路

1. 健康检查：

```sh
make gui-doctor
```

2. 启动 Gateway：

```sh
make gui-gateway
```

停止当前仓库启动的本地 Gateway：

```sh
make gui-stop
```

说明：

- `make gui-stop` 会优先停止 `launchd` 监管的 `ai.openclaw.gateway`
- 若端口上仍有残留监听，才会回退到进程级清理

3. 打开 Dashboard：

```sh
make gui-dashboard
```

仅打印地址，不自动打开浏览器：

```sh
OPENCLAW_DASHBOARD_NO_OPEN=1 make gui-dashboard
```

4. 启动终端 TUI：

```sh
make gui-tui
```

### 4.5 阶段 E：接入 Qwen API（DashScope）

本仓库当前已按本地配置路径 `.openclaw-dev/config.json` 接入 `qwen` provider：

- provider id：`qwen`
- base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- 默认模型：`qwen/qwen3.5-plus`
- 白名单模型：`qwen-plus`、`qwen3.5-plus`、`qwen3.5-plus-2026-02-15`、`qwen-max`、`qwen3-max-2026-01-23`、`qwen-turbo`、`qwen3.5-flash`、`qwen3.5-122b-a10b`、`qwen3.5-35b-a3b`、`qwen3.5-27b`、`qwen3-coder-plus`、`glm-5`、`tongyi-xiaomi-analysis-pro`、`tongyi-xiaomi-analysis-flash`
- API Key 来源：环境变量引用 `DASHSCOPE_API_KEY`

推荐使用策略：

- 日常简单对话：`qwen/qwen3.5-flash`
- 默认平衡档：`qwen/qwen3.5-plus`
- 复杂推理与高难任务：`qwen/qwen3-max-2026-01-23`
- 中文对话分析类任务：`qwen/tongyi-xiaomi-analysis-pro`

当前仓库没有原生“按问题复杂度自动路由到不同模型”的配置字段。现阶段更稳妥的做法是：

- 保持一个平衡档默认主模型
- 遇到高复杂度任务时手动切换模型
- 用以下命令快速切换默认主模型：

```sh
make model-cheap
make model-balanced
make model-reasoning
make model-analysis
```

切换后重启 gateway 使新默认配置生效：

```sh
make gui-stop
make gui-gateway
```

推荐在仓库根目录创建 `.env.local`：

```sh
DASHSCOPE_API_KEY=你的真实Key
```

`make gui-*` 会自动读取 `.env.local`。如果当前 shell 里已经显式设置了同名环境变量，则优先使用当前 shell 的值。
`make gui-*` 会自动读取 `.env.local`，并以 `.env.local` 中的值覆盖同名旧环境变量，避免宿主机残留旧 key 污染当前进程。

然后启动：

```sh
make gui-gateway
make gui-dashboard
```

说明：

- 当前项目默认是本地 loopback 绑定，仅监听 `127.0.0.1`
- 默认状态目录为 `.openclaw-dev/state-live/`
- 旧状态目录如果曾产生异常历史，不要继续复用，优先保留 `state-live`
- `make gui-gateway` 是前台常驻进程；若需要在另一个终端停止它，优先用 `make gui-stop`
- 如果看到 “another gateway instance is already listening”，先执行 `make gui-stop`；这会同时处理普通进程和 `launchd` 监管实例
- 如果 OpenClaw 升级后再次出现 `edit failed: Missing required parameter: oldText/newText` 之类报错，先执行 `make gui-runtime-patch`，然后重启 `make gui-gateway`

### 4.6 阶段 F：Gmail 整理与 Hook 自动化

仓库已提供 repo-local Gmail 组织入口：

- `skills/gmail-organizer/`
- `python3 skills/gmail-organizer/scripts/invoke_gmail.py ...`
- `make gmail-config`
- `make gmail-check`
- `make gmail-run`

初始化 Gmail 配置骨架：

```sh
make gmail-config
```

检查宿主依赖：

```sh
make gmail-check
```

即时读取 Gmail：

```sh
python3 skills/gmail-organizer/scripts/invoke_gmail.py status
python3 skills/gmail-organizer/scripts/invoke_gmail.py latest --limit 5 --unread-only
```

当前实现要求的宿主依赖：

- `gog`
- `gcloud`

填好 `.env.local` 之后，运行 Gmail watcher：

```sh
make gmail-run
```

默认 Gmail hook 策略：

- 低成本模型：`qwen/qwen3.5-flash`
- `thinking: off`
- `deliver: true`
- `channel: last`

这意味着 Gmail 事件会优先用便宜模型做常规 inbox triage，并把结果发回最近活动的聊天通道。

说明：

- 当前机器已经安装 `gog` / `gcloud`
- 如果 Homebrew 没把 `gcloud` 链到 `/opt/homebrew/bin`，`make gmail-run` 会自动回退到 `/opt/homebrew/share/google-cloud-sdk/bin/gcloud`
- `gcloud auth login` 只解决 GCP 登录，不会自动给 `gog` Gmail API 权限；`gog` 仍需要单独的 OAuth client credentials 和 `gog auth add`
- `make gmail-config` 会为 `OPENCLAW_HOOK_TOKEN` 和 `GMAIL_PUSH_TOKEN` 自动生成本地随机值
- Gmail Pub/Sub 的 topic / subscription 仍需你根据自己的 GCP 项目填写

---

## 5. 故障排查分类

### 5.1 输入缺失类

`Missing source tree`：

- 检查 `src/openclaw-upstream/` 是否存在
- 或覆盖 `OPENCLAW_SRC_DIR`

`Missing asset directory`：

- 检查 `assets/game-data/` 是否存在
- 或覆盖 `OPENCLAW_ASSET_DIR`

### 5.2 运行参数类

`OPENCLAW_RUN_BIN is not set`：

- 在 `make run` 时显式传入 `OPENCLAW_RUN_BIN`

`Run target is not executable`：

- 校验产物路径是否正确
- 校验目标文件是否具备可执行权限

### 5.3 本地网络/绑定类

`uv_interface_addresses returned Unknown system error 1`：

- 本仓库已通过 `src/tools/openclaw_network_shim.mjs` 提供回退

`gateway bind=loopback resolved to non-loopback host 0.0.0.0`：

- 若在受限环境里运行诊断命令，OpenClaw 的 loopback 自检可能被干扰
- 正常本地 macOS 运行时应直接绑定 `127.0.0.1`

`HTTP 401 Incorrect API key provided`：

- 检查 `.env.local` 中的 `DASHSCOPE_API_KEY` 是否为当前有效 key
- 重启 `make gui-gateway`，确保新进程重新加载 `.env.local`
- 若你曾在宿主机 shell 设置过旧 key，本仓库包装脚本会以 `.env.local` 覆盖它

`用户消息没有回复 / 返回 NO_REPLY`：

- 当前项目已通过本地 workspace 提示词禁止在一对一直聊里对普通消息返回 `NO_REPLY`
- 默认状态目录已切到 `.openclaw-dev/state-live/`，避免复用旧主会话历史
- 若 UI 仍异常，优先确认是否连到了新启动的 gateway

---

## 6. 日常维护分类

### 6.1 清理

```sh
make clean
```

作用：删除 `.build/openclaw` 和 `.cache/openclaw`。

### 6.2 日志与状态

- 日志目录：`.openclaw-dev/logs/`
- 状态目录：`.openclaw-dev/state-live/`
- 本地配置：`.openclaw-dev/config.json`

### 6.3 回归检查建议

- 执行 `make build`
- 执行 `make test`
- 执行 `make gui-doctor`
- 需要交互调试时再执行 `gui-gateway + gui-dashboard/tui`

---

## 7. 安全与合规分类

- 不提交商业资源与上游源码目录内容
- 默认使用 `OPENCLAW_NETWORK=none`，非必要不放开容器网络
- 本地状态保留在仓库内 `.openclaw-dev/`，避免污染用户全局目录
- 本地运行采用 macOS 宿主机模式，但高风险工具默认禁用，额外权限操作必须显式确认
- 二进制与缓存目录保持忽略提交

---

## 8. 快速命令索引

```sh
make help
make build-image
make build
make test
make run OPENCLAW_RUN_BIN=./.build/openclaw/openclaw
make gui-doctor
make gui-gateway
make gui-dashboard
make gui-tui
make clean
```
