# 模型清单与分层建议

本文整理的是你在 2026-03-22 提供的截图里“当前仍有免费额度”的模型，并说明它们已经如何接入本仓库的 OpenClaw 本地配置。

## 1. 当前已加入 `.openclaw-dev/config.json` 的模型

以下模型已加入 `models.providers.qwen.models` 与 `agents.defaults.models`：

- `qwen3.5-plus`
- `qwen3.5-plus-2026-02-15`
- `qwen3.5-flash`
- `qwen3-max-2026-01-23`
- `qwen3.5-122b-a10b`
- `qwen3.5-35b-a3b`
- `qwen3.5-27b`
- `glm-5`
- `tongyi-xiaomi-analysis-pro`
- `tongyi-xiaomi-analysis-flash`

兼容保留的既有模型：

- `qwen-plus`
- `qwen-max`
- `qwen-turbo`
- `qwen3-coder-plus`

说明：

- 当前 provider id 仍命名为 `qwen`
- 这是历史兼容命名，不代表只能挂千问模型
- 这些模型仍走同一个百炼兼容入口：`https://dashscope.aliyuncs.com/compatible-mode/v1`

## 2. 截图中的免费额度信息

以下日期来自你在 2026-03-22 提供的截图，本仓库仅做记录，不把这些日期作为程序逻辑。

| 模型 | 截图显示剩余额度 | 截图显示到期时间 |
| --- | --- | --- |
| `tongyi-xiaomi-analysis-pro` | `1,000,000 / 1,000,000` | `2026-04-28` |
| `qwen3.5-122b-a10b` | `1,000,000 / 1,000,000` | `2026-05-25` |
| `qwen3.5-flash` | `1,000,000 / 1,000,000` | `2026-05-25` |
| `qwen3.5-35b-a3b` | `1,000,000 / 1,000,000` | `2026-05-25` |
| `qwen3.5-plus` | `1,000,000 / 1,000,000` | `2026-05-18` |
| `qwen3.5-plus-2026-02-15` | `1,000,000 / 1,000,000` | `2026-05-18` |
| `glm-5` | `1,000,000 / 1,000,000` | `2026-05-18` |
| `qwen3-max-2026-01-23` | `1,000,000 / 1,000,000` | `2026-04-27` |
| `qwen3.5-27b` | `1,000,000 / 1,000,000` | `2026-05-25` |
| `tongyi-xiaomi-analysis-flash` | `1,000,000 / 1,000,000` | `2026-04-28` |

## 3. 建议分层

以下分层综合了模型命名、百炼官方接入建议和当前 OpenClaw 使用场景。

### 低成本档

- `qwen/qwen3.5-flash`
- `qwen/tongyi-xiaomi-analysis-flash`

适用：

- 普通闲聊
- 简单问答
- 短文本改写
- 轻量工具调用

### 平衡档

- `qwen/qwen3.5-plus`
- `qwen/glm-5`

适用：

- 大多数日常 OpenClaw 对话
- 需要一定推理但不想直接上最高成本模型
- 一般性的 agent 工作流

### 高性能推理档

- `qwen/qwen3-max-2026-01-23`
- `qwen/qwen3.5-122b-a10b`
- `qwen/tongyi-xiaomi-analysis-pro`

适用：

- 复杂推理
- 架构设计
- 高要求分析
- 复杂中文对话分析

## 4. 当前仓库能否自动按复杂度切换模型

当前结论是：还不能靠现有 OpenClaw 配置实现“真正自动路由”。

当前仓库里已经确认的能力只有：

- 设置一个默认主模型
- 暴露多个可选模型
- 在会话中手动切换模型
- 在配置里整体切换默认主模型

当前没有证据表明 `.openclaw-dev/config.json` 支持：

- 按 prompt 长度自动选模型
- 按是否需要推理自动选模型
- 按工具调用复杂度自动选模型

所以本仓库采用的现实策略是：

1. 默认主模型设为 `qwen/qwen3.5-plus`
2. 简单对话时切到 `qwen/qwen3.5-flash`
3. 复杂推理时切到 `qwen/qwen3-max-2026-01-23`

## 5. 一键切换命令

```sh
make model-cheap
make model-balanced
make model-reasoning
make model-analysis
```

切换后重启 gateway：

```sh
make gui-stop
make gui-gateway
```
