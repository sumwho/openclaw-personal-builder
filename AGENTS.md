# Repository Guidelines

## Project Structure & Module Organization
This repository is currently minimal and has no committed source tree yet. Keep the root clean and group new work by purpose: application code in `src/`, automated tests in `tests/`, static assets in `assets/`, and supporting documentation in `docs/`. Mirror feature names across code and tests when possible, for example `src/physics/` and `tests/physics/`.

## Build, Test, and Development Commands
No build system, package manifest, or test runner is checked in yet. When adding one, expose a small set of predictable entry points and document them in `README.md`. Preferred command patterns are:
- `make build` — compile or package the project
- `make test` — run the full automated test suite
- `make run` — start the project locally
Use one canonical command per task so contributors do not need to guess which script is authoritative.

## Coding Style & Naming Conventions
Use 4-space indentation unless a language-specific formatter requires otherwise. Follow the dominant convention of the language you introduce: `PascalCase` for classes/types, `snake_case` or the language standard for functions and files, and descriptive directory names based on features. Keep modules small, avoid unrelated refactors, and run the repository formatter or linter before opening a pull request.

## Testing Guidelines
Add tests with every behavior change. Prefer fast, isolated unit tests first, then integration tests where behavior crosses module boundaries. Name tests after the feature under test, such as `tests/test_resource_loader.*` or `resource_loader.spec.*`. If you add a new test framework, include a single documented command to run it.

## Commit & Pull Request Guidelines
No local Git history is available in this checkout, so use concise, imperative commit subjects such as `Add asset manifest parser` or `Fix input mapping regression`. Keep commits focused on one change. Pull requests should explain the change, list validation steps, link related issues, and include screenshots or logs for UI or behavior changes.

## Configuration & Security Tips
Do not commit secrets, generated binaries, or personal editor settings. Store local-only values in ignored files such as `.env.local`, and provide safe example defaults when configuration is required.
