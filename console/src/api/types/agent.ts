export interface AgentRequest {
  input: unknown;
  session_id?: string | null;
  user_id?: string | null;
  channel?: string | null;
  [key: string]: unknown;
}

export interface AgentsRunningConfig {
  max_iters: number;
  max_input_length: number;
  memory_compact_ratio: number;
  memory_reserve_ratio: number;
  enable_tool_result_compact: boolean;
  tool_result_compact_keep_n: number;
}

export interface SandboxConfig {
  enabled: boolean;
  type: string;
  timeout: number;
  max_memory: number | null;
  max_cpu: number | null;
}

export interface ExecuteShellCommandRequest {
  command: string;
  timeout?: number;
}

export interface ExecuteShellCommandResponse {
  content: Array<{
    type: string;
    text: string;
  }>;
}
