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
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const repoSkillsDir = path.join(repoRoot, "skills");
const stateDir = process.env.OPENCLAW_STATE_DIR
    ? path.resolve(process.env.OPENCLAW_STATE_DIR)
    : path.join(stateRoot, "state-live");
const workspaceDir = path.join(stateRoot, "workspace");
const wifeEnglishWorkspaceDir = path.join(stateRoot, "workspace-wife-english");
const runtimeWorkspaceDir = path.join(stateDir, "workspace-main");
const requiredDeniedTools = ["browser", "canvas", "cron", "gateway", "nodes", "tts"];
const workspaceSyncTargets = [
    {
        targetDir: workspaceDir,
        templateDir: path.join(repoRoot, "assets", "openclaw-workspace"),
    },
    {
        targetDir: runtimeWorkspaceDir,
        templateDir: path.join(repoRoot, "assets", "openclaw-workspace"),
    },
    {
        targetDir: wifeEnglishWorkspaceDir,
        templateDir: path.join(repoRoot, "assets", "openclaw-workspace-wife-english"),
    },
];
const managedProviderId = "dashscope";
const managedPrimaryModel = "dashscope/qwen3.5-plus";
const wifeEnglishAgentId = "wife-english";
const wifeEnglishPrimaryModel = "dashscope/qwen3.5-plus";
const wifeEnglishFallbacks = ["dashscope/qwen3.5-flash"];
const homeDir = process.env.HOME ?? process.env.USERPROFILE ?? "";
const managedCommunityPluginPaths = [
    path.join(homeDir, ".openclaw", "extensions", "openclaw-weixin"),
];
const managedAllowedPlugins = ["qwen-portal-auth", "telegram"];
const managedProviderModels = [
    { id: "qwen-plus", name: "Qwen Plus" },
    { id: "qwen3.5-plus", name: "Qwen3.5 Plus" },
    { id: "qwen3.5-plus-2026-02-15", name: "Qwen3.5 Plus 2026-02-15" },
    { id: "qwen-max", name: "Qwen Max" },
    { id: "qwen3-max-2026-01-23", name: "Qwen3 Max 2026-01-23" },
    { id: "qwen-turbo", name: "Qwen Turbo" },
    { id: "qwen3.5-flash", name: "Qwen3.5 Flash" },
    { id: "qwen3.5-122b-a10b", name: "Qwen3.5 122B A10B" },
    { id: "qwen3.5-35b-a3b", name: "Qwen3.5 35B A3B" },
    { id: "qwen3.5-27b", name: "Qwen3.5 27B" },
    { id: "qwen3-coder-plus", name: "Qwen3 Coder Plus" },
    { id: "glm-5", name: "GLM 5" },
    { id: "tongyi-xiaomi-analysis-pro", name: "Tongyi Xiaomi Analysis Pro" },
    { id: "tongyi-xiaomi-analysis-flash", name: "Tongyi Xiaomi Analysis Flash" },
];
const managedAgentModels = {
    "dashscope/qwen-plus": { alias: "dashscope" },
    "dashscope/qwen3.5-plus": { alias: "dashscope" },
    "dashscope/qwen3.5-plus-2026-02-15": {},
    "dashscope/qwen-max": {},
    "dashscope/qwen3-max-2026-01-23": {},
    "dashscope/qwen-turbo": {},
    "dashscope/qwen3.5-flash": {},
    "dashscope/qwen3.5-122b-a10b": {},
    "dashscope/qwen3.5-35b-a3b": {},
    "dashscope/qwen3.5-27b": {},
    "dashscope/qwen3-coder-plus": {},
    "dashscope/glm-5": {},
    "dashscope/tongyi-xiaomi-analysis-pro": {},
    "dashscope/tongyi-xiaomi-analysis-flash": {},
};

const legacyManagedProviderId = "qwen";
const legacyManagedModelPrefix = `${legacyManagedProviderId}/`;
const managedModelIds = new Set(managedProviderModels.map((model) => model.id));

function remapManagedModelRef(modelRef) {
    if (typeof modelRef !== "string") return modelRef;
    if (!modelRef.startsWith(legacyManagedModelPrefix)) return modelRef;
    const modelId = modelRef.slice(legacyManagedModelPrefix.length);
    if (!managedModelIds.has(modelId)) return modelRef;
    return `${managedProviderId}/${modelId}`;
}

await fs.mkdir(path.dirname(configPath), { recursive: true });

async function existingPaths(paths) {
    const results = [];
    for (const candidate of paths) {
        try {
            await fs.access(candidate);
            results.push(candidate);
        } catch {
            // ignore missing optional plugin roots
        }
    }
    return results;
}

async function syncWorkspace(targetWorkspaceDir, templateDir) {
    const targetSkillsDir = path.join(targetWorkspaceDir, "skills");

    await fs.mkdir(targetWorkspaceDir, { recursive: true });
    await fs.mkdir(targetSkillsDir, { recursive: true });

    let repoSkillEntries = [];
    try {
        repoSkillEntries = await fs.readdir(repoSkillsDir, { withFileTypes: true });
    } catch (error) {
        console.error(`Failed to list skills under ${repoSkillsDir}: ${String(error)}`);
        process.exit(1);
    }

    for (const entry of repoSkillEntries) {
        if (!entry.isDirectory()) continue;

        const sourceSkillDir = path.join(repoSkillsDir, entry.name);
        const targetSkillDir = path.join(targetSkillsDir, entry.name);

        try {
            await fs.rm(targetSkillDir, { recursive: true, force: true });
            await fs.cp(sourceSkillDir, targetSkillDir, { recursive: true });
        } catch (error) {
            console.error(
                `Failed to sync workspace skill from ${sourceSkillDir} to ${targetSkillDir}: ${String(error)}`,
            );
            process.exit(1);
        }
    }

    for (const fileName of ["AGENTS.md", "BOOTSTRAP.md", "USER.md"]) {
        const sourcePath = path.join(templateDir, fileName);
        const targetPath = path.join(targetWorkspaceDir, fileName);

        try {
            await fs.copyFile(sourcePath, targetPath);
        } catch (error) {
            console.error(`Failed to sync workspace template ${sourcePath} to ${targetPath}: ${String(error)}`);
            process.exit(1);
        }
    }
}

for (const { targetDir, templateDir } of workspaceSyncTargets) {
    await syncWorkspace(targetDir, templateDir);
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

const denyList = Array.isArray(config.tools?.deny)
    ? config.tools.deny.filter((value) => typeof value === "string")
    : [];
const detectedCommunityPluginPaths = await existingPaths(managedCommunityPluginPaths);
const dynamicAllowedPlugins = [
    ...managedAllowedPlugins,
    ...detectedCommunityPluginPaths.map((candidate) => path.basename(candidate)),
];
const existingAllowedPlugins = Array.isArray(config.plugins?.allow)
    ? config.plugins.allow.filter((value) => typeof value === "string")
    : [];
const existingLoadPaths =
    Array.isArray(config.plugins?.load?.paths)
        ? config.plugins.load.paths.filter((value) => typeof value === "string")
        : [];
const nextAllowedPlugins = [...new Set([...existingAllowedPlugins, ...dynamicAllowedPlugins])];
const nextLoadPaths = [...new Set([...existingLoadPaths, ...detectedCommunityPluginPaths])];
const currentManagedProviderConfig =
    config.models?.providers?.[managedProviderId] ?? config.models?.providers?.[legacyManagedProviderId];
const existingProviderModels = Array.isArray(currentManagedProviderConfig?.models)
    ? currentManagedProviderConfig.models.filter(
          (model) => model && typeof model === "object" && typeof model.id === "string",
      )
    : [];
const mergedProviderModelMap = new Map(existingProviderModels.map((model) => [model.id, model]));

for (const model of managedProviderModels) {
    const existing = mergedProviderModelMap.get(model.id) ?? {};
    mergedProviderModelMap.set(model.id, { ...existing, ...model });
}

const preservedAgentModels = {};
for (const [key, value] of Object.entries(config.agents?.defaults?.models ?? {})) {
    if (typeof key !== "string") continue;
    if (key.startsWith(legacyManagedModelPrefix)) {
        const modelId = key.slice(legacyManagedModelPrefix.length);
        if (managedModelIds.has(modelId)) continue;
    }
    if (key === "qwen-portal/coder-model" && value && typeof value === "object" && value.alias === "qwen") {
        preservedAgentModels[key] = { ...value };
        delete preservedAgentModels[key].alias;
        continue;
    }
    preservedAgentModels[key] = value;
}
const mergedAgentModels = {
    ...preservedAgentModels,
    ...managedAgentModels,
};
const existingPrimaryModel = config.agents?.defaults?.model?.primary;
const nextPrimaryModel =
    typeof existingPrimaryModel === "string" && existingPrimaryModel !== `${legacyManagedProviderId}/qwen-max`
        ? remapManagedModelRef(existingPrimaryModel)
        : managedPrimaryModel;
const existingAgentList = Array.isArray(config.agents?.list)
    ? config.agents.list.filter((agent) => agent && typeof agent === "object" && typeof agent.id === "string")
    : [];
const preservedAgentList = existingAgentList.filter(
    (agent) => agent.id !== "local" && agent.id !== wifeEnglishAgentId,
);
const managedAgentList = [
    {
        id: "local",
        default: true,
        workspace: workspaceDir,
        identity: {
            name: "C3-PO",
            theme: "protocol droid",
            emoji: "🤖",
            ...(existingAgentList.find((agent) => agent.id === "local")?.identity ?? {}),
        },
    },
    {
        ...(existingAgentList.find((agent) => agent.id === wifeEnglishAgentId) ?? {}),
        id: wifeEnglishAgentId,
        default: false,
        workspace: wifeEnglishWorkspaceDir,
        model: {
            ...((existingAgentList.find((agent) => agent.id === wifeEnglishAgentId)?.model ?? {})),
            primary:
                remapManagedModelRef(existingAgentList.find((agent) => agent.id === wifeEnglishAgentId)?.model?.primary) ??
                wifeEnglishPrimaryModel,
            fallbacks: Array.isArray(existingAgentList.find((agent) => agent.id === wifeEnglishAgentId)?.model?.fallbacks)
                ? existingAgentList.find((agent) => agent.id === wifeEnglishAgentId).model.fallbacks.map(remapManagedModelRef)
                : wifeEnglishFallbacks,
        },
        identity: {
            ...(existingAgentList.find((agent) => agent.id === wifeEnglishAgentId)?.identity ?? {}),
            name: "Luna",
            theme: "language studio",
            emoji: "🌙",
        },
    },
];

for (const toolId of requiredDeniedTools) {
    if (!denyList.includes(toolId)) {
        denyList.push(toolId);
    }
}

const nextConfig = {
    ...config,
    models: {
        ...(config.models ?? {}),
        mode: config.models?.mode ?? "merge",
        providers: {
            ...Object.fromEntries(
                Object.entries(config.models?.providers ?? {}).filter(([key]) => key !== legacyManagedProviderId),
            ),
            [managedProviderId]: {
                ...(currentManagedProviderConfig ?? {}),
                baseUrl:
                    currentManagedProviderConfig?.baseUrl ??
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                apiKey:
                    currentManagedProviderConfig?.apiKey ?? {
                        source: "env",
                        provider: "default",
                        id: "DASHSCOPE_API_KEY",
                    },
                api: currentManagedProviderConfig?.api ?? "openai-completions",
                models: [...mergedProviderModelMap.values()],
            },
        },
    },
    agents: {
        ...(config.agents ?? {}),
        defaults: {
            ...(config.agents?.defaults ?? {}),
            model: {
                ...(config.agents?.defaults?.model ?? {}),
                primary: nextPrimaryModel,
            },
            models: mergedAgentModels,
            workspace: workspaceDir,
            skipBootstrap: true,
            compaction: {
                ...(config.agents?.defaults?.compaction ?? {}),
                mode: "safeguard",
            },
        },
        list: [
            ...managedAgentList,
            ...preservedAgentList,
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
    channels: {
        ...(config.channels ?? {}),
        telegram: {
            ...(config.channels?.telegram ?? {}),
            enabled: true,
            botToken: config.channels?.telegram?.botToken ?? {
                source: "env",
                provider: "default",
                id: "TELEGRAM_BOT_TOKEN",
            },
            dmPolicy: config.channels?.telegram?.dmPolicy ?? "pairing",
            groupPolicy: config.channels?.telegram?.groupPolicy ?? "disabled",
            streaming: config.channels?.telegram?.streaming ?? "partial",
        },
    },
    tools: {
        ...(config.tools ?? {}),
        deny: denyList,
    },
    plugins: {
        ...(config.plugins ?? {}),
        allow: nextAllowedPlugins,
        load: {
            ...(config.plugins?.load ?? {}),
            paths: nextLoadPaths,
        },
        entries: {
            ...(config.plugins?.entries ?? {}),
            "qwen-portal-auth": {
                ...(config.plugins?.entries?.["qwen-portal-auth"] ?? {}),
                enabled: true,
            },
            telegram: {
                ...(config.plugins?.entries?.telegram ?? {}),
                enabled: true,
            },
            ...(detectedCommunityPluginPaths.some((candidate) => path.basename(candidate) === "openclaw-weixin")
                ? {
                      "openclaw-weixin": {
                          ...(config.plugins?.entries?.["openclaw-weixin"] ?? {}),
                          enabled: true,
                      },
                  }
                : {}),
        },
    },
    meta: {
        ...(config.meta ?? {}),
        lastTouchedAt: new Date().toISOString(),
    },
};

await fs.writeFile(configPath, `${JSON.stringify(nextConfig, null, 2)}\n`, "utf8");
