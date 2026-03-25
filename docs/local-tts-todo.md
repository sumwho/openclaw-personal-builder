# Local TTS TODO

## Review Scope

This document captures the remaining gaps between the current implementation and the saved local requirements archive for the TTS integration work.

## Priority 0

- Harden MeloTTS installation on Apple Silicon.
  Current state: the gateway now has a working Melo adapter, an isolated Melo venv, a runtime patch that removes the Japanese import blocker, and a local English fallback path for common words and letter-spelled OOV tokens.
  Target state: finish a reproducible Melo install manifest, add a smoke test, and optionally package NLTK English data under the deployment base directory for better pronunciation on harder OOV cases.

- Make Kokoro English fully local.
  Current state: English requests with `engine=kokoro` fall back to Piper because the Kokoro English path triggers a spaCy compatibility lookup against `raw.githubusercontent.com` at runtime.
  Target state: preinstall the exact English spaCy model artifacts under the chosen deployment base directory and prevent any runtime network fetch.

- Materialize Kokoro assets under `models/kokoro/`.
  Current state: Kokoro is addressed by Hugging Face model id and is resolved through cache/runtime behavior.
  Target state: gateway config points to a local model directory or an explicit local manifest under `models/kokoro/` inside the deployment base directory.

- Replace best-effort background startup with a production macOS service path.
  Current state: `scripts/start.sh` uses `nohup` and a PID file.
  Target state: provide a `launchd` plist stored under the deployment base directory and use `launchctl` for stable process supervision.

- Define and enforce the host dependency boundary.
  Current state: Python 3.11-3.13 and ffmpeg are still host-managed and only partially re-exposed under the deployment base directory.
  Target state: either vendor these dependencies under the deployment base directory or explicitly document host-managed exceptions and cleanup steps.

## Priority 1

- Add integration tests for `/health`, `/voices`, and `/v1/audio/speech`.
- Add smoke tests for Kokoro Chinese success, Kokoro English fallback, and Piper success.
- Add a validation script that checks models, ffmpeg path, gateway config, and write permissions before startup.
- Remove incidental files such as `.DS_Store` from the deployment base directory.
- Clean setup-time temp artifacts immediately after install so `runtime/temp` is not left noisy after `setup.sh`.

## Priority 2

- Add a locked dependency manifest with hashes for the gateway venv.
- Add a version manifest under the deployment base directory that records deployed script version, config version, and model version.
- Add optional loudness normalization and output format regression tests.
- Add XTTS placeholder adapter scaffolding under `models/xtts` and `engines/`.
