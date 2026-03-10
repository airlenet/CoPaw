import { request } from "../request";
import type { AgentRequest, AgentsRunningConfig, SandboxConfig } from "../types";

// Agent API
export const agentApi = {
  agentRoot: () => request<unknown>("/agent/"),

  healthCheck: () => request<unknown>("/agent/health"),

  agentApi: (body: AgentRequest) =>
    request<unknown>("/agent/process", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getProcessStatus: () => request<unknown>("/agent/admin/status"),

  shutdownSimple: () =>
    request<void>("/agent/shutdown", {
      method: "POST",
    }),

  shutdown: () =>
    request<void>("/agent/admin/shutdown", {
      method: "POST",
    }),

  getAgentRunningConfig: () =>
    request<AgentsRunningConfig>("/agent/running-config"),

  updateAgentRunningConfig: (config: AgentsRunningConfig) =>
    request<AgentsRunningConfig>("/agent/running-config", {
      method: "PUT",
      body: JSON.stringify(config),
    }),

    getConfig: () => request<SandboxConfig>('/config/sandbox'),

    updateConfig: (config: { sandbox: SandboxConfig }) =>
        request<SandboxConfig>('/config/sandbox', {
            method: 'PUT',
            body: JSON.stringify(config.sandbox),
        }),

    execute_shell_command: (command: string) =>
        request<{ content: Array<{ type: string; text: string }> }>('/config/sandbox/start', {
            method: 'POST',
            body: JSON.stringify({ command }),
        }),

  getAgentLanguage: () => request<{ language: string }>("/agent/language"),

  updateAgentLanguage: (language: string) =>
    request<{ language: string; copied_files: string[] }>("/agent/language", {
      method: "PUT",
      body: JSON.stringify({ language }),
    }),
};
