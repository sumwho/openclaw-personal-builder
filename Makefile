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

.PHONY: help prepare build-image build test run shell clean local-prepare gui-doctor gui-gateway gui-stop gui-dashboard gui-tui tts-setup tts-start tts-stop tts-clean

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
	@echo "make gui-tui      Open the terminal UI"
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
	@PORT="$${OPENCLAW_GATEWAY_PORT:-18789}"; \
	PIDS="$$(lsof -tiTCP:$$PORT -sTCP:LISTEN 2>/dev/null || true)"; \
	if [ -z "$$PIDS" ]; then \
		echo "No local OpenClaw gateway is listening on port $$PORT."; \
		exit 0; \
	fi; \
	echo "Stopping local OpenClaw gateway on port $$PORT (pid: $$PIDS)"; \
	kill -TERM $$PIDS; \
	sleep 1; \
	REMAINING="$$(lsof -tiTCP:$$PORT -sTCP:LISTEN 2>/dev/null || true)"; \
	if [ -n "$$REMAINING" ]; then \
		echo "Gateway still running after SIGTERM, forcing stop (pid: $$REMAINING)"; \
		kill -KILL $$REMAINING; \
	fi

gui-dashboard: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh dashboard

gui-tui: local-prepare
	@$(GUI_ENV_RUN) bash src/tools/openclaw_local.sh tui

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
