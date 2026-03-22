# 02. 架构与运行时

## 1. 核心组件图

可以把当前项目的实际链路理解成：

`Control UI -> Gateway -> Agent Runtime -> Model Provider(Qwen)`

同时 Gateway 还连接：

- 本地状态目录 `.openclaw-dev/state-live/`
- 本地 workspace `.openclaw-dev/workspace/`
- 本地配置 `.openclaw-dev/config.json`
- 工具执行宿主机 macOS

## 2. Gateway 是什么

Gateway 是 OpenClaw 的中枢：

- 提供 WebSocket 服务
- 持有会话状态
- 驱动 agent 运行
- 负责工具调用与事件流
- 为 Control UI / TUI / CLI 提供统一入口

在你的环境里，它监听：

- `ws://127.0.0.1:18789`
- `http://127.0.0.1:18789/`

## 3. Control UI 是什么

Control UI 是浏览器中的单页应用：

- 它不是“直接连模型”
- 它是“直接连 Gateway”
- 所有聊天、配置、调试动作，本质上都在通过 Gateway 完成

所以 UI 没回复，不一定是 UI 的问题，常见根因可能在：

- Gateway 没起来
- Gateway 连到了错误状态目录
- provider 鉴权失败
- agent 返回了 `NO_REPLY`

## 4. Agent Runtime 是什么

Agent Runtime 决定“这个助手如何思考和行动”：

- 使用哪个模型
- 注入哪些 workspace 文件
- 暴露哪些工具
- 如何处理会话历史
- 是否允许 sandbox / elevated / sessions 等能力

在当前项目中，Agent Runtime 主要受这几部分影响：

- `.openclaw-dev/config.json`
- `.openclaw-dev/workspace/AGENTS.md`
- `.openclaw-dev/workspace/USER.md`
- `.openclaw-dev/workspace/HEARTBEAT.md`
- `.openclaw-dev/workspace/BOOTSTRAP.md`

## 5. Workspace 为什么重要

Workspace 不是普通资料目录，它会被注入到系统提示词中。

这意味着：

- 你在 `AGENTS.md` 里写的规则，会直接影响模型行为
- `USER.md` 会改变 agent 对用户身份的理解
- `HEARTBEAT.md` 会影响 heartbeat 轮询
- `BOOTSTRAP.md` 会影响启动期行为

你之前的 `NO_REPLY` 问题，就是一个典型案例：

- 默认模板里带有“群聊可沉默”的策略
- 旧状态目录里的主会话历史持续强化了这种行为
- 只有在本地 workspace 中显式写出“单人直聊必须回复”后，模型行为才稳定纠正

## 6. State 目录为什么重要

状态目录可以理解为 Gateway 的运行数据库。

它里面通常会存：

- session transcript
- auth profile 缓存
- update check
- 设备信息
- 运行时派生状态

为什么 `state-live` 比 `state` 更关键？

- 旧 `state` 里累积了错误历史与异常会话
- 这些历史会持续影响主会话
- 切换到新的 `state-live`，相当于在不删除旧数据的前提下做了“干净切换”

这是一种比直接暴力删除更安全的工程策略。

## 7. 当前仓库里的两个关键脚本

### `src/tools/openclaw_local.sh`

这是本地运行包装层，负责：

- 读取 `.env.local`
- 设置 `OPENCLAW_STATE_DIR`
- 设置 `OPENCLAW_CONFIG_PATH`
- 注入 network shim
- 调用 `openclaw doctor/gateway/dashboard/tui`

### `src/tools/openclaw_seed_config.mjs`

这是配置种子脚本，负责：

- 确保配置文件存在
- 固定本地 workspace
- 固定 gateway 模式
- 生成或保留 gateway token
- 把仓库里的 `skills/local-tts/` 同步到 `.openclaw-dev/workspace/skills/local-tts/`

## 8. 学习架构时该怎么排问题

建议你以后都按这个顺序判断：

1. Gateway 是否启动并监听了端口
2. UI 是否连的是正确的 gateway
3. gateway 使用的是哪个 config / state 目录
4. 当前 agent 的 workspace 注入了什么文件
5. 当前 provider/model/auth 是否有效
6. 当前异常是模型行为问题还是进程/网络问题

## 9. 本章要记住的结论

- Gateway 是 OpenClaw 的控制平面
- Control UI 是 Gateway 的前端，不是模型直连端
- Workspace 决定 agent 行为，State 决定 agent 历史
- 学习 OpenClaw 时，一定要把“配置、workspace、state”当作一等公民
