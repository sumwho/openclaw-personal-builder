import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const [configPathArg, stateRootArg] = process.argv.slice(2);

if (!configPathArg || !stateRootArg) {
    console.error("Usage: node openclaw_seed_config.mjs <config-path> <state-root>");
    process.exit(1);
}

const configPath = path.resolve(configPathArg);
const stateRoot = path.resolve(stateRootArg);
const workspaceDir = path.join(stateRoot, "workspace");
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const repoSkillDir = path.join(repoRoot, "skills", "local-tts");
const workspaceSkillsDir = path.join(workspaceDir, "skills");
const workspaceSkillDir = path.join(workspaceSkillsDir, "local-tts");

await fs.mkdir(path.dirname(configPath), { recursive: true });
await fs.mkdir(workspaceDir, { recursive: true });
await fs.mkdir(workspaceSkillsDir, { recursive: true });

try {
    await fs.rm(workspaceSkillDir, { recursive: true, force: true });
    await fs.cp(repoSkillDir, workspaceSkillDir, { recursive: true });
} catch (error) {
    console.error(`Failed to sync workspace skill from ${repoSkillDir}: ${String(error)}`);
    process.exit(1);
}

let config = {};

try {
    const raw = await fs.readFile(configPath, "utf8");
    config = JSON.parse(raw);
} catch (error) {
    if (!error || typeof error !== "object" || !("code" in error) || error.code !== "ENOENT") {
        throw error;
    }
}

if (config.meta && typeof config.meta === "object") {
    delete config.meta.localManagedByRepo;
}

const token =
    config?.gateway?.auth?.token && typeof config.gateway.auth.token === "string"
        ? config.gateway.auth.token
        : crypto.randomBytes(24).toString("hex");

const nextConfig = {
    ...config,
    agents: {
        ...(config.agents ?? {}),
        defaults: {
            ...(config.agents?.defaults ?? {}),
            workspace: workspaceDir,
            skipBootstrap: true,
            compaction: {
                ...(config.agents?.defaults?.compaction ?? {}),
                mode: "safeguard",
            },
        },
        list: [
            {
                id: "local",
                default: true,
                workspace: workspaceDir,
                identity: {
                    name: "C3-PO",
                    theme: "protocol droid",
                    emoji: "🤖",
                    ...(config.agents?.list?.[0]?.identity ?? {}),
                },
            },
        ],
    },
    gateway: {
        ...(config.gateway ?? {}),
        mode: "local",
        bind: "loopback",
        auth: {
            ...(config.gateway?.auth ?? {}),
            mode: "token",
            token,
        },
    },
    meta: {
        ...(config.meta ?? {}),
        lastTouchedAt: new Date().toISOString(),
    },
};

await fs.writeFile(configPath, `${JSON.stringify(nextConfig, null, 2)}\n`, "utf8");
