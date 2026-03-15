import os from "node:os";

const originalNetworkInterfaces = os.networkInterfaces.bind(os);

os.networkInterfaces = function patchedNetworkInterfaces() {
    try {
        return originalNetworkInterfaces();
    } catch (error) {
        if (process.env.OPENCLAW_NETWORK_SHIM_STRICT === "1") {
            throw error;
        }

        process.emitWarning(
            `openclaw network shim fallback enabled: ${String(error)}`,
            {
                code: "OPENCLAW_NETWORK_SHIM_FALLBACK",
            },
        );

        return {
            lo0: [
                {
                    address: "127.0.0.1",
                    netmask: "255.0.0.0",
                    family: "IPv4",
                    mac: "00:00:00:00:00:00",
                    internal: true,
                    cidr: "127.0.0.1/8",
                },
            ],
        };
    }
};

