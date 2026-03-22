# OpenClaw 本地图形界面与调试启动

## 适用对象

本文档适用于通过 `npm` 全局安装的 `openclaw` CLI，例如：

```sh
npm install -g openclaw
```

你当前安装的是这类版本，它提供的是：

- 浏览器控制台界面 `dashboard`
- 终端界面 `tui`
- 本地 Gateway 服务

它不是 SDL 游戏窗口程序，因此“图形界面”推荐走浏览器 Dashboard。

## 本仓库提供的本地启动包装

新增脚本：

- `src/tools/openclaw_local.sh`
- `src/tools/openclaw_network_shim.mjs`

作用：

- 将状态目录限制在仓库内的 `.openclaw-dev/`
- 固定 Gateway 绑定到 `127.0.0.1`
- 将 agent workspace 固定到仓库内 `.openclaw-dev/workspace/`
- 为当前环境提供网卡探测兜底，避免 `os.networkInterfaces()` 异常直接导致 CLI 退出
- 统一 Gateway、Dashboard、TUI 的启动参数
- 自动读取 `.env.local`，并以仓库内值覆盖同名旧环境变量

## 目录说明

- `.openclaw-dev/state-live/` — 当前生效的本地状态目录
- `.openclaw-dev/config.json` — 本地配置文件
- `.openclaw-dev/logs/` — 启动日志目录

这些内容已被 `.gitignore` 忽略。

## 推荐启动顺序

### 1. 基础体检

```sh
make gui-doctor
```

### 2. 启动 Gateway

```sh
make gui-gateway
```

默认行为：

- 使用 `127.0.0.1:18789`
- 使用仓库内本地状态目录
- 自动生成或修正仓库内本地配置文件
- 自动启用网络探测兼容层
- 使用 `gateway run --allow-unconfigured`，尽量降低首次启动门槛

### 3. 打开 Dashboard

```sh
make gui-dashboard
```

如果你只想打印地址而不自动打开浏览器：

```sh
OPENCLAW_DASHBOARD_NO_OPEN=1 make gui-dashboard
```

### 4. 启动终端界面

```sh
make gui-tui
```

### 5. 停止 Gateway

```sh
make gui-stop
```

当前实现会优先调用 `openclaw gateway stop` 停止被 `launchd` 监管的 Gateway 服务；如果端口上还有残留监听，再回退到 `launchctl bootout` 和进程级清理。

## 调试建议

- 若只验证服务可用性，优先用 `gui-doctor` 和 `gui-dashboard`
- 若要交互调试，先开 `gui-gateway`，再开 `gui-tui`
- `gui-gateway` 是前台常驻命令；如果不是在原终端里 `Ctrl+C`，可以直接执行 `make gui-stop`
- 若浏览器打不开，先使用 `OPENCLAW_DASHBOARD_NO_OPEN=1 make gui-dashboard` 确认 URL 是否正常输出

## 常见问题

### `uv_interface_addresses returned Unknown system error 1`

当前仓库里的启动包装会通过 `src/tools/openclaw_network_shim.mjs` 做兼容处理，优先尝试真实网卡，失败时回退到 loopback 信息。

### `gateway bind=loopback resolved to non-loopback host 0.0.0.0`

该问题通常只出现在受限诊断环境中。当前项目按宿主机本地模式运行时，应直接绑定 `127.0.0.1`。

### `make gui-stop` 之后 Gateway 立刻又起来

根因通常不是 `kill` 失败，而是进程由 `launchd` 监管。旧版 `gui-stop` 只会杀掉当前监听 pid，但 `launchd` 会马上拉起新的 `openclaw-gateway`。当前仓库版本的 `gui-stop` 已改为优先执行 `openclaw gateway stop`，必要时再 `launchctl bootout gui/$UID/ai.openclaw.gateway`。

### `NO_REPLY` 出现在直聊场景

当前仓库已经在 `.openclaw-dev/workspace/` 中加入本地覆盖提示词，要求一对一直聊必须正常回复。若仍出现此问题，优先确认是否还在使用旧状态目录或旧 gateway 进程。

### 想恢复 OpenClaw 默认状态目录

直接跳过包装脚本，自己运行原生命令即可，例如：

```sh
openclaw gateway run
```

但这样会把状态写入你的用户目录。
