# 03. 配置系统与 Qwen 接入

## 1. 当前项目的配置中心

当前仓库的主配置文件是：

- `.openclaw-dev/config.json`

这个文件定义了：

- provider
- model
- agent default
- workspace 路径
- gateway 监听模式
- 工具禁用策略
- 插件白名单

## 2. 先学会读当前配置

建议你先重点看这几块。

### `models.providers.qwen`

这部分定义模型供应商：

- `baseUrl` 指向 DashScope 兼容接口
- `apiKey` 来自环境变量 `DASHSCOPE_API_KEY`
- `api` 使用 `openai-completions`
- `models` 定义可见模型清单

这说明当前仓库不是走 Qwen OAuth，而是走 DashScope API key 模式。

### `agents.defaults.model.primary`

这决定默认主模型。

当前是：

- `qwen/qwen-max`

### `agents.defaults.workspace`

这决定 agent 从哪里注入本地 workspace 文件。

当前是：

- `.openclaw-dev/workspace`

### `gateway`

这部分决定 gateway 的运行方式。

当前关键点：

- `mode = local`
- `bind = loopback`
- Control UI 允许本地 origin
- `auth.mode = token`

### `tools`

这部分定义可用性边界。

当前项目中：

- 禁用了部分高风险工具
- `tools.elevated.enabled = false`
- 会话可见性限制为 `tree`

## 3. `.env.local` 在哪里起作用

当前项目的 `.env.local` 是本地私有配置入口。

最关键的变量是：

```sh
DASHSCOPE_API_KEY=你的真实Key
```

本地包装脚本会在启动时自动加载这个文件。

当前项目还专门做了一个重要修正：

- `.env.local` 中的值会覆盖同名旧环境变量

为什么这是必须的？

因为如果你宿主机 shell 里残留了一个旧的 `DASHSCOPE_API_KEY`，而脚本又优先吃宿主机旧值，就会出现：

- `curl` 可用
- 但 OpenClaw 仍然 401

## 4. Qwen 接入的三种常见模式

### 模式 1：Portal/OAuth

OpenClaw 官方文档里有 `qwen-portal-auth` 插件和 OAuth 流程。

特点：

- 适合走 Qwen Portal
- 依赖插件和 auth store
- 更接近 OpenClaw 官方示例

### 模式 2：DashScope 兼容 API

这就是你当前项目使用的方式。

特点：

- provider 自定义明确
- 用环境变量管理 key
- 对接路径清晰
- 更适合本地受控接入

### 模式 3：外层代理

例如 LiteLLM、兼容 OpenAI 的中间层。

特点：

- 适合多 provider 汇聚
- 更适合团队基础设施
- 学习成本更高

## 5. 为什么模型能“通”但仍然行为异常

这是 OpenClaw 新手最容易混淆的点。

模型链路正常，只说明：

- provider 可达
- key 可用
- model id 正确

它并不说明：

- 提示词正确
- 会话历史干净
- 工具路由正常
- UI 一定有回复

所以要把两个层次分开：

1. provider/model 是否可调用
2. agent 在当前上下文里是否会做出你期望的行为

## 6. 你当前项目里和 Qwen 相关的最佳实践

- 用 `.env.local` 保存 key，不把 key 写死进仓库
- 使用 `qwen-max` 作为默认模型，降低“弱模型钻提示词空子”的概率
- 保留多个白名单模型，便于切换验证
- 使用 repo-local config，不污染用户全局 OpenClaw 配置

## 7. 推荐的验证顺序

### 验证 provider/key

先验证 DashScope：

```bash
curl https://dashscope.aliyuncs.com/compatible-mode/v1/models \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY"
```

### 验证 OpenClaw 当前配置

```bash
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
openclaw config validate
```

### 验证 agent 端到端

```bash
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
openclaw agent --local --agent local --message "hi" --json
```

如果最后一步能稳定返回自然语言回复，而不是 `NO_REPLY` 或 `401`，说明当前配置链路是通的。

## 8. 本章要记住的结论

- 配置文件决定能力边界，`.env.local` 决定本地私密参数
- Qwen 接入成功，不等于 agent 行为正确
- provider 层和 agent 行为层必须分开诊断
- 在本项目里，`config + workspace + state-live + .env.local` 是一套完整闭环
