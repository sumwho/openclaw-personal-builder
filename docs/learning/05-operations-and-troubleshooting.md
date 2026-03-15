# 05. 日常操作与排障

## 1. 你当前项目的标准操作

### 启动本地 Gateway

```bash
make gui-gateway
```

注意：

- 这是前台常驻进程
- 终端被占用是正常现象，不是卡住

### 打开控制台

```bash
make gui-dashboard
```

### 停止本地 Gateway

```bash
make gui-stop
```

这比 `openclaw gateway stop` 更符合你当前项目，因为它是针对 repo-local 前台实例设计的。

## 2. 验证链路时的推荐顺序

### 第一步：看 gateway 是否在监听

```bash
lsof -nP -iTCP:18789 -sTCP:LISTEN
```

### 第二步：看配置是否有效

```bash
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
openclaw config validate
```

### 第三步：看模型是否真能调用

```bash
curl https://dashscope.aliyuncs.com/compatible-mode/v1/models \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY"
```

### 第四步：看 agent 端到端是否能回复

```bash
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
openclaw agent --local --agent local --message "hi" --json
```

## 3. 常见问题分类

### 问题 1：`401 Incorrect API key provided`

优先检查：

- `.env.local` 里的 key 是否有效
- gateway 是否在修改 key 之后重启
- 是否还在吃宿主机旧环境变量

当前项目的包装脚本已经修正为：

- `.env.local` 覆盖同名旧环境变量

### 问题 2：消息没有回复

先区分两种情况。

#### 情况 A：真的没有跑起来

检查：

- gateway 是否监听端口
- dashboard 是否连到了本地正确地址

#### 情况 B：agent 返回了 `NO_REPLY`

检查：

- 是否仍在使用旧状态目录
- 当前 workspace 是否注入了本地覆盖提示词
- 是否不小心又回到了旧会话历史

### 问题 3：`gateway already running`

说明端口上已经有一个 gateway 进程。

处理方式：

```bash
make gui-stop
```

### 问题 4：`openclaw gateway stop` 停不掉实例

这通常说明：

- 当前运行的是前台宿主机实例
- 不是 LaunchAgent/service

所以应该使用：

- 原终端 `Ctrl+C`
- 或 `make gui-stop`

### 问题 5：切模型后反而报新错误

典型原因：

- 新模型用到了旧 auth profile
- 实际验证命令没有带正确的 `OPENCLAW_STATE_DIR`
- provider/key 问题和模型切换被混淆了

## 4. 为什么排障时一定要带 `OPENCLAW_STATE_DIR`

因为 OpenClaw 的很多运行信息是状态相关的。

如果你排障命令没有显式指定：

- 你以为自己在测“当前项目”
- 实际可能测的是另一个全局状态目录

这会造成非常典型的误判：

- UI 用的是新状态
- CLI 验证用的是旧状态
- 最后看起来像“同样配置，结果却矛盾”

## 5. 推荐的学习型排障习惯

### 习惯 1：先确认层级

先判断问题在哪层：

- 进程
- 配置
- 状态
- provider
- 提示词

### 习惯 2：每次只改一个变量

例如：

- 先只换状态目录
- 再只换模型
- 再只换 key

不要一次改三件事，不然很难知道到底哪一个起作用。

### 习惯 3：保留旧数据，但不要继续复用

这正是你当前项目里 `state` 和 `state-live` 的处理方式：

- 不暴力删历史
- 但用新目录建立干净运行面

这是比“全部重置”更成熟的工程做法。

## 6. 建议你自己练习的 5 个实验

1. 启动 `make gui-gateway`，然后用另一个终端执行 `make gui-stop`
2. 故意把 `.env.local` 改成错误 key，观察 `401`
3. 把 key 改回正确值并重启 gateway，观察恢复
4. 用 `openclaw agent --local ... --json` 做最小回复验证
5. 对比 `state-live` 和另一个临时状态目录的行为差异

## 7. 本章要记住的结论

- 排障最怕“层级混淆”
- 端口、配置、状态、provider、提示词必须分开看
- `state-live` 是你当前项目的真实运行面
- `make gui-stop` 是当前项目正确的停止方式
