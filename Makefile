SHELL := /bin/bash

IMAGE_NAME ?= openclaw-test-env
CONTAINER_NAME ?= openclaw-test-shell
ENV_LOCAL_FILE ?= $(CURDIR)/.env.local
OPENCLAW_SRC_DIR ?= $(CURDIR)/src/openclaw-upstream
OPENCLAW_ASSET_DIR ?= $(CURDIR)/assets/game-data
OPENCLAW_BUILD_DIR ?= $(CURDIR)/.build/openclaw
OPENCLAW_CACHE_DIR ?= $(CURDIR)/.cache/openclaw
OPENCLAW_RUN_BIN ?=
OPENCLAW_NETWORK ?= none

GUI_ENV_RUN = set -a; if [ -f "$(ENV_LOCAL_FILE)" ]; then . "$(ENV_LOCAL_FILE)"; fi; set +a;
GCLOUD_FALLBACK_BIN = /opt/homebrew/share/google-cloud-sdk/bin/gcloud

DOCKER_RUN = docker run --rm -it \
	--name $(CONTAINER_NAME) \
	--network $(OPENCLAW_NETWORK) \
	-v $(CURDIR):/workspace \
	-v $(OPENCLAW_SRC_DIR):/workspace/src/openclaw-upstream:ro \
	-v $(OPENCLAW_ASSET_DIR):/workspace/assets/game-data:ro \
	-e OPENCLAW_SRC_DIR=/workspace/src/openclaw-upstream \
	-e OPENCLAW_ASSET_DIR=/workspace/assets/game-data \
	-e OPENCLAW_BUILD_DIR=/workspace/.build/openclaw \
	-e OPENCLAW_CACHE_DIR=/workspace/.cache/openclaw \
	-e OPENCLAW_RUN_BIN=$(OPENCLAW_RUN_BIN) \
	-w /workspace \
	$(IMAGE_NAME)

.PHONY: help prepare build-image build test run shell clean local-prepare gui-doctor gui-gateway gui-stop gui-dashboard gui-status gui-logs gui-tui gui-runtime-patch model-cheap model-balanced model-reasoning model-analysis gmail-config gmail-run gmail-check weixin-bind-wife tts-setup tts-start tts-stop tts-clean

help:
	@echo "make build-image  Build the Docker image"
	@echo "make build        Configure and build OpenClaw"
	@echo "make test         Run the test suite via CTest"
	@echo "make run          Run the built binary (set OPENCLAW_RUN_BIN)"
	@echo "make shell        Open an interactive shell in the container"
	@echo "make local-prepare Prepare local OpenClaw dev state"
	@echo "make gui-doctor   Run OpenClaw doctor with local state"
	@echo "make gui-gateway  Start local OpenClaw gateway"
	@echo "make gui-stop     Stop the local OpenClaw gateway on the configured port"
	@echo "make gui-dashboard Print or open the dashboard URL"
	@echo "make gui-status   Show repo-local gateway health, channels, and paired devices"
	@echo "make gui-logs     Show repo-local gateway logs"
	@echo "make gui-tui      Open the terminal UI"
	@echo "make gui-runtime-patch Reapply the local OpenClaw runtime patch for edit-tool alias compatibility"
	@echo "make model-cheap Set the default primary model to qwen/qwen3.5-flash"
	@echo "make model-balanced Set the default primary model to qwen/qwen3.5-plus"
	@echo "make model-reasoning Set the default primary model to qwen/qwen3-max-2026-01-23"
	@echo "make model-analysis Set the default primary model to qwen/tongyi-xiaomi-analysis-pro"
	@echo "make gmail-config Seed repo-local Gmail hook config and env placeholders"
	@echo "make gmail-run    Run the Gmail Pub/Sub watcher via OpenClaw webhooks"
	@echo "make gmail-check  Show whether gog, gcloud, and tailscale are installed"
	@echo "make weixin-bind-wife ACCOUNT_ID=<weixin-account-id>  Route a Weixin bot account to the wife-english agent"
	@echo "make tts-setup    Deploy the local TTS package under OPENCLAW_TTS_BASE_DIR (default: /Volumes/ExtendStorage/openclaw)"
	@echo "make tts-start    Start the local TTS gateway"
	@echo "make tts-stop     Stop the local TTS gateway"
	@echo "make tts-clean    Remove runtime TTS artifacts while keeping models"
	@echo "make clean        Remove local build and cache directories"

prepare:
	@mkdir -p $(OPENCLAW_BUILD_DIR) $(OPENCLAW_CACHE_DIR) $(dir $(OPENCLAW_SRC_DIR)) $(dir $(OPENCLAW_ASSET_DIR))
	@if [ ! -d "$(OPENCLAW_SRC_DIR)" ]; then echo "Missing source tree: $(OPENCLAW_SRC_DIR)"; echo "Clone the upstream OpenClaw source there or override OPENCLAW_SRC_DIR."; exit 1; fi
	@if [ ! -d "$(OPENCLAW_ASSET_DIR)" ]; then echo "Missing asset directory: $(OPENCLAW_ASSET_DIR)"; echo "Copy your legal game data there or override OPENCLAW_ASSET_DIR."; exit 1; fi

build-image:
	docker build -t $(IMAGE_NAME) .

build: prepare
	$(DOCKER_RUN) bash src/tools/openclaw_env.sh build

test: prepare
	$(DOCKER_RUN) bash src/tools/openclaw_env.sh test

run: prepare
	$(DOCKER_RUN) bash src/tools/openclaw_env.sh run

shell: prepare
	$(DOCKER_RUN) bash

local-prepare:
	@mkdir -p .openclaw-dev/state-live .openclaw-dev/logs

gui-doctor: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh doctor

gui-gateway: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh gateway

gui-stop:
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh stop

gui-dashboard: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh dashboard

gui-status: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh status

gui-logs: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh logs

gui-tui: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh tui

gui-runtime-patch:
	@bash scripts/patch-openclaw-runtime.sh

model-cheap:
	@python3 src/tools/openclaw_model_profile.py cheap

model-balanced:
	@python3 src/tools/openclaw_model_profile.py balanced

model-reasoning:
	@python3 src/tools/openclaw_model_profile.py reasoning

model-analysis:
	@python3 src/tools/openclaw_model_profile.py analysis

gmail-config:
	@$(GUI_ENV_RUN) python3 src/tools/openclaw_gmail_config.py

gmail-run:
	@$(GUI_ENV_RUN) bash -lc 'GOG_BIN="$$(command -v gog || true)"; GCLOUD_BIN="$$(command -v gcloud || true)"; if [ -z "$$GCLOUD_BIN" ] && [ -x "$(GCLOUD_FALLBACK_BIN)" ]; then GCLOUD_BIN="$(GCLOUD_FALLBACK_BIN)"; fi; if [ -z "$$GOG_BIN" ]; then echo "Missing dependency: gog"; exit 1; fi; if [ -z "$$GCLOUD_BIN" ]; then echo "Missing dependency: gcloud"; exit 1; fi; if [ -z "$${GMAIL_ACCOUNT:-}" ]; then echo "Missing GMAIL_ACCOUNT in .env.local or shell"; exit 1; fi; if [ -z "$${OPENCLAW_HOOK_TOKEN:-}" ]; then echo "Missing OPENCLAW_HOOK_TOKEN in .env.local or shell"; exit 1; fi; if [ -z "$${GMAIL_PUSH_TOKEN:-}" ]; then echo "Missing GMAIL_PUSH_TOKEN in .env.local or shell"; exit 1; fi; export PATH="$$(dirname "$$GCLOUD_BIN"):$${PATH}"; OPENCLAW_CONFIG_PATH="$(CURDIR)/.openclaw-dev/config.json" OPENCLAW_STATE_DIR="$(CURDIR)/.openclaw-dev/state-live" openclaw webhooks gmail run --account "$${GMAIL_ACCOUNT}" --label "$${GMAIL_LABEL:-INBOX}" --topic "$${GMAIL_PUBSUB_TOPIC}" --subscription "$${GMAIL_PUBSUB_SUBSCRIPTION:-gog-gmail-watch-push}" --hook-url "http://127.0.0.1:$${OPENCLAW_GATEWAY_PORT:-18789}/hooks/gmail" --hook-token "$${OPENCLAW_HOOK_TOKEN}" --push-token "$${GMAIL_PUSH_TOKEN}" --tailscale off'

gmail-check:
	@bash -lc 'GCLOUD_BIN="$$(command -v gcloud || true)"; if [ -z "$$GCLOUD_BIN" ] && [ -x "$(GCLOUD_FALLBACK_BIN)" ]; then GCLOUD_BIN="$(GCLOUD_FALLBACK_BIN)"; fi; printf "openclaw: "; command -v openclaw || true; printf "gog: "; command -v gog || true; printf "gcloud: %s\n" "$$GCLOUD_BIN"; printf "tailscale: "; command -v tailscale || true'

weixin-bind-wife:
	@if [ -z "$(ACCOUNT_ID)" ]; then echo "Missing ACCOUNT_ID"; exit 1; fi
	@python3 src/tools/openclaw_bind_weixin_agent.py --config .openclaw-dev/config.json --account-id "$(ACCOUNT_ID)" --agent-id wife-english

tts-setup:
	@bash scripts/setup.sh

tts-start:
	@bash scripts/start.sh

tts-stop:
	@bash scripts/stop.sh

tts-clean:
	@bash scripts/clean.sh

clean:
	rm -rf $(OPENCLAW_BUILD_DIR) $(OPENCLAW_CACHE_DIR)
