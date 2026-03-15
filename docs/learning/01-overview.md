# 01. OpenClaw 总览

## 1. OpenClaw 是什么

OpenClaw 可以理解为一个“以 Gateway 为中心的本地 AI 操作系统外壳”：

- 它把模型调用、聊天会话、工具执行、设备接入、状态存储、网页控制台统一到一个网关进程里
- 它不只是“一个聊天网页”
- 它也不只是“一个 CLI”
- 它更像“一个可编排的 agent runtime + 控制平面”

你当前项目里，OpenClaw 的实际使用方式是：

- `openclaw-gateway` 作为核心进程
- Control UI 作为浏览器前端
- Qwen 作为模型后端
- 仓库内 `.openclaw-dev/` 作为本地状态与配置根目录

## 2. OpenClaw 不是什么

- 不是单纯的模型 SDK 封装
- 不是只会聊天的前端页面
- 不是天然安全隔离的多租户平台
- 不是“只要配置上模型就一定稳定回复”的黑盒

这几点很重要。你之前遇到的 `NO_REPLY`、旧状态污染、service/foreground 停止方式差异，本质上都来自 OpenClaw 是一整套运行时，而不是一个简单 API 调用器。

## 3. 你应该如何理解它

建议把 OpenClaw 拆成 5 层来看：

1. 模型层
   例如 Qwen、OpenAI、Anthropic、Ollama。
2. Agent 层
   定义系统提示词、工具集合、会话策略、workspace 注入。
3. Gateway 层
   承担真正的运行、路由、状态维护、工具执行、前端服务。
4. UI/CLI 层
   例如 Control UI、dashboard、tui、CLI 子命令。
5. Host 层
   也就是你的 macOS、文件系统、网络、权限策略。

OpenClaw 的大多数问题，都可以定位到其中某一层。

## 4. 当前项目的最终运行模式

当前仓库已经收敛到下面这套模式：

- 运行模式：本地 macOS 宿主机直跑
- sandbox：关闭
- provider：Qwen（DashScope 兼容接口）
- 默认模型：`qwen/qwen-max`
- 默认 gateway 入口：`127.0.0.1:18789`
- 默认状态目录：`.openclaw-dev/state-live/`
- 默认 workspace：`.openclaw-dev/workspace/`
- 高风险工具：默认禁用部分能力，额外权限必须确认

这是一套适合个人本地学习、调试和受控实验的配置，不适合直接当作多人共享网关。

## 5. 学习 OpenClaw 时最常见的误区

### 误区 1：把“模型问题”和“运行时问题”混为一谈

例如：

- `401 Incorrect API key provided` 是 provider/auth 问题
- `NO_REPLY` 往往是提示词、会话历史、路由策略问题
- `gateway already running` 是进程/端口问题

### 误区 2：忽视状态目录

OpenClaw 的很多行为不是“只看当前消息”，而是受下面内容影响：

- 既有会话历史
- auth profile 缓存
- workspace 注入文件
- agent 默认配置

所以状态目录是理解 OpenClaw 的关键。

### 误区 3：误把 Gateway 当成 service-only 程序

你已经实际验证过：

- `make gui-gateway` 启动的是前台宿主机进程
- `openclaw gateway stop` 停的是 service 模式
- 两者不是同一个生命周期模型

## 6. 本章要记住的结论

- OpenClaw 是“模型 + agent + gateway + tool + state + UI”的统一运行时
- 问题定位时要先分层
- 状态目录和 workspace 提示词对行为影响非常大
- 你当前项目已经不是默认安装态，而是一个“带本地包装与安全收敛”的 OpenClaw 学习环境
