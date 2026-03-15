# OpenClaw 本地测试环境搭建说明

## 目标

这套环境用于在本地安全地验证 OpenClaw 上游源码、资源加载和基本运行行为，同时尽量避免污染宿主机。

## 设计原则

- 源码目录默认只读挂载，避免容器意外改写上游代码
- 游戏资源目录默认只读挂载，避免测试过程破坏原始数据
- 构建产物和缓存单独写入 `.build/` 与 `.cache/`
- 容器内使用普通用户运行，不使用 root 执行构建或程序
- 默认关闭容器网络，减少测试时不必要的外部访问

## 前置要求

- 已安装 Docker
- 拥有合法的 OpenClaw 资源文件
- 上游源码支持 CMake 构建流程

## 目录准备

将上游源码放到：

- `src/openclaw-upstream/`

将本地游戏资源放到：

- `assets/game-data/`

这些目录默认已在 `.gitignore` 中忽略，不会被提交。

## 使用流程

### 1. 构建容器镜像

```sh
make build-image
```

### 2. 构建项目

```sh
make build
```

该步骤会：

- 检查源码与资源目录是否存在
- 在容器内执行 `cmake -S -B -G Ninja`
- 将产物输出到 `.build/openclaw/`

### 3. 运行测试

```sh
make test
```

该步骤会在容器内执行 `ctest --output-on-failure`。

### 4. 运行程序

首次运行前需要明确可执行文件路径：

```sh
make run OPENCLAW_RUN_BIN=./.build/openclaw/openclaw
```

`OPENCLAW_RUN_BIN` 应该是容器工作目录 `/workspace` 下可访问的路径，通常指向 `.build/openclaw/` 内的最终二进制。

## 可选参数

- `IMAGE_NAME` — 自定义镜像名
- `OPENCLAW_SRC_DIR` — 覆盖源码目录
- `OPENCLAW_ASSET_DIR` — 覆盖资源目录
- `OPENCLAW_BUILD_DIR` — 覆盖构建目录
- `OPENCLAW_RUN_BIN` — 指定运行的可执行文件
- `OPENCLAW_NETWORK` — 控制容器网络，默认 `none`

例如：

```sh
make build OPENCLAW_SRC_DIR=$HOME/code/OpenClaw OPENCLAW_ASSET_DIR=$HOME/games/claw-data
```

## 安全建议

- 不要把商业游戏资源提交到仓库
- 首次拉取上游源码后，优先审阅其构建脚本和第三方依赖
- 非必要不要给容器开启网络；确需联网时，按次开启
- 如果需要图形界面调试，优先先做无界面构建与测试，再单独放开显示相关权限

## 常见问题

### 缺少源码目录

确认 `src/openclaw-upstream/` 存在，或通过 `OPENCLAW_SRC_DIR` 指向你的本地源码树。

### 缺少资源目录

确认 `assets/game-data/` 存在，或通过 `OPENCLAW_ASSET_DIR` 指向你的本地资源目录。

### 无法运行图形界面

当前骨架优先面向安全构建和测试。若你需要 SDL 图形窗口、音频或调试器转发，可以在下一步补充平台专用的运行配置。

