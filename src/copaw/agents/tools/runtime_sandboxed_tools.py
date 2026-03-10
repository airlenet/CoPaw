# -*- coding: utf-8 -*-
"""AgentScope Runtime Sandboxed Tools"""

import asyncio
from pathlib import Path
from typing import Optional

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

from copaw.constant import WORKING_DIR
from copaw.agents.sandbox.runtime_sandbox_manager import AgentScopeRuntimeSandboxManager

# 全局沙箱管理器实例
global_sandbox = None

async def get_sandbox():
    """获取全局沙箱实例"""
    global global_sandbox
    if not global_sandbox:
        # 从配置中读取沙箱设置
        from copaw.config import load_config
        config = load_config()
        sandbox_config = config.sandbox.model_dump()
        
        global_sandbox = AgentScopeRuntimeSandboxManager(sandbox_config)
        await global_sandbox.__aenter__()
    return global_sandbox


def _resolve_file_path(file_path: str) -> str:
    """Resolve file path: use absolute path as-is,
    resolve relative path from WORKING_DIR.

    Args:
        file_path: The input file path (absolute or relative).

    Returns:
        The resolved absolute file path as string.
    """
    path = Path(file_path)
    if path.is_absolute():
        # Convert Windows path to Linux path for sandbox
        return str(path).replace('\\', '/').replace('C:', '')
    else:
        # For sandbox, keep relative paths as-is to use /workspace
        return file_path


async def execute_shell_command(
    command: str,
    timeout: int = 60,
    cwd: Optional[Path] = None,
) -> ToolResponse:
    """在AgentScope Runtime沙箱中执行shell命令"""
    # 检查沙箱是否启用
    from copaw.config import load_config
    config = load_config()
    if not config.sandbox.enabled:
        # 直接执行命令（不使用沙箱）
        import subprocess
        import os
        
        working_dir = cwd if cwd is not None else WORKING_DIR
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                timeout=timeout,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                if result.stdout:
                    response_text = result.stdout
                else:
                    response_text = "Command executed successfully (no output)."
            else:
                response_parts = [f"Command failed with exit code {result.returncode}."]
                if result.stdout:
                    response_parts.append(f"\n[stdout]\n{result.stdout}")
                if result.stderr:
                    response_parts.append(f"\n[stderr]\n{result.stderr}")
                response_text = "".join(response_parts)
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=response_text,
                    ),
                ],
            )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Shell command execution failed due to \n{e}",
                    ),
                ],
            )
    
    try:
        sandbox = await get_sandbox()
        # 设置工作目录
        working_dir = cwd if cwd is not None else WORKING_DIR
        
        result = await sandbox.execute_command(
            command=command
        )
        
        # 格式化响应
        if result["returncode"] == 0:
            if result["stdout"]:
                response_text = result["stdout"]
            else:
                response_text = "Command executed successfully (no output)."
        else:
            response_parts = [f"Command failed with exit code {result['returncode']}."]
            if result["stdout"]:
                response_parts.append(f"\n[stdout]\n{result['stdout']}")
            if result["stderr"]:
                response_parts.append(f"\n[stderr]\n{result['stderr']}")
            response_text = "".join(response_parts)
        
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=response_text,
                ),
            ],
        )
        
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Shell command execution failed due to \n{e}",
                ),
            ],
        )


async def run_python_code_sandboxed(
    code: str,
) -> ToolResponse:
    """在AgentScope Runtime沙箱中运行Python代码"""
    # 检查沙箱是否启用
    from copaw.config import load_config
    config = load_config()
    if not config.sandbox.enabled:
        # 直接执行Python代码（不使用沙箱）
        import io
        import sys
        
        try:
            # 捕获标准输出
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            # 执行代码
            exec(code)
            
            # 获取输出
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            response_text = output if output else "Python code executed successfully (no output)."
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=response_text,
                    ),
                ],
            )
            
        except Exception as e:
            import traceback
            error_msg = f"Python code execution failed:\n{traceback.format_exc()}"
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=error_msg,
                    ),
                ],
            )
    
    try:
        sandbox = await get_sandbox()
        result = await sandbox.run_python_code(code=code)
        
        # 格式化响应
        if result.get("success", False):
            output = result.get("output", "")
            if output:
                response_text = output
            else:
                response_text = "Python code executed successfully (no output)."
        else:
            error = result.get("error", "")
            response_text = f"Python code execution failed:\n{error}"
        
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=response_text,
                ),
            ],
        )
        
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Python code execution failed due to \n{e}",
                ),
            ],
        )


async def read_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> ToolResponse:
    """在AgentScope Runtime沙箱中读取文件"""
    # 检查沙箱是否启用
    from copaw.config import load_config
    config = load_config()
    if not config.sandbox.enabled:
        # 直接读取文件（不使用沙箱）
        try:
            file_path = _resolve_file_path(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理行范围
            if start_line is not None or end_line is not None:
                lines = content.splitlines(keepends=True)
                total = len(lines)
                s = max(1, start_line if start_line is not None else 1)
                e = min(total, end_line if end_line is not None else total)
                
                if s > total:
                    return ToolResponse(
                        content=[
                            TextBlock(
                                type="text",
                                text=(f"Error: start_line {s} exceeds file length "
                                      f"({total} lines) in {file_path}."),
                            ),
                        ],
                    )
                
                if s > e:
                    return ToolResponse(
                        content=[
                            TextBlock(
                                type="text",
                                text=(f"Error: start_line ({s}) is greater than "
                                      f"end_line ({e}) in {file_path}."),
                            ),
                        ],
                    )
                
                selected = lines[s-1:e]
                content = "".join(selected)
                header = f"{file_path}  (lines {s}-{e} of {total})\n"
                content = header + content
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=content,
                    ),
                ],
            )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Read file failed due to \n{e}",
                    ),
                ],
            )
    
    try:
        sandbox = await get_sandbox()
        file_path = _resolve_file_path(file_path)
        
        content = await sandbox.read_file(file_path)
        
        # 处理行范围
        if start_line is not None or end_line is not None:
            lines = content.splitlines(keepends=True)
            total = len(lines)
            s = max(1, start_line if start_line is not None else 1)
            e = min(total, end_line if end_line is not None else total)
            
            if s > total:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=(f"Error: start_line {s} exceeds file length "
                                  f"({total} lines) in {file_path}."),
                        ),
                    ],
                )
            
            if s > e:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=(f"Error: start_line ({s}) is greater than "
                                  f"end_line ({e}) in {file_path}."),
                        ),
                    ],
                )
            
            selected = lines[s-1:e]
            content = "".join(selected)
            header = f"{file_path}  (lines {s}-{e} of {total})\n"
            content = header + content
        
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=content,
                ),
            ],
        )
        
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Read file failed due to \n{e}",
                ),
            ],
        )


async def write_file(
    file_path: str,
    content: str,
) -> ToolResponse:
    """在AgentScope Runtime沙箱中写入文件"""
    try:
        if not file_path:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: No `file_path` provided.",
                    ),
                ],
            )
        
        # 检查沙箱是否启用
        from copaw.config import load_config
        config = load_config()
        if not config.sandbox.enabled:
            # 直接写入文件（不使用沙箱）
            file_path = _resolve_file_path(file_path)
            
            import os
            # 创建目录
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Wrote {len(content)} bytes to {file_path}.",
                    ),
                ],
            )
        
        sandbox = await get_sandbox()
        file_path = _resolve_file_path(file_path)
        
        success = await sandbox.write_file(file_path, content)
        
        if success:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Wrote {len(content)} bytes to {file_path}.",
                    ),
                ],
            )
        else:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Failed to write to {file_path}.",
                    ),
                ],
            )
            
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Write file failed due to \n{e}",
                ),
            ],
        )


async def edit_file(
    file_path: str,
    old_text: str,
    new_text: str,
) -> ToolResponse:
    """在AgentScope Runtime沙箱中编辑文件"""
    try:
        # 检查沙箱是否启用
        from copaw.config import load_config
        config = load_config()
        if not config.sandbox.enabled:
            # 直接编辑文件（不使用沙箱）
            file_path = _resolve_file_path(file_path)
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_text not in content:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Error: The text to replace was not found in {file_path}.",
                        ),
                    ],
                )
            
            # 替换文本
            new_content = content.replace(old_text, new_text)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Successfully replaced text in {file_path}.",
                    ),
                ],
            )
        
        sandbox = await get_sandbox()
        file_path = _resolve_file_path(file_path)
        
        # 读取文件内容
        content = await sandbox.read_file(file_path)
        
        if old_text not in content:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: The text to replace was not found in {file_path}.",
                    ),
                ],
            )
        
        # 替换文本
        new_content = content.replace(old_text, new_text)
        
        # 写入文件
        success = await sandbox.write_file(file_path, new_content)
        
        if success:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Successfully replaced text in {file_path}.",
                    ),
                ],
            )
        else:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Failed to write to {file_path}.",
                    ),
                ],
            )
            
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Edit file failed due to \n{e}",
                ),
            ],
        )


async def append_file(
    file_path: str,
    content: str,
) -> ToolResponse:
    """在AgentScope Runtime沙箱中追加文件"""
    try:
        if not file_path:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: No `file_path` provided.",
                    ),
                ],
            )
        
        # 检查沙箱是否启用
        from copaw.config import load_config
        config = load_config()
        if not config.sandbox.enabled:
            # 直接追加文件（不使用沙箱）
            file_path = _resolve_file_path(file_path)
            
            import os
            # 创建目录
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 追加文件
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Appended {len(content)} bytes to {file_path}.",
                    ),
                ],
            )
        
        sandbox = await get_sandbox()
        file_path = _resolve_file_path(file_path)
        
        success = await sandbox.append_file(file_path, content)
        
        if success:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Appended {len(content)} bytes to {file_path}.",
                    ),
                ],
            )
        else:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Failed to append to {file_path}.",
                    ),
                ],
            )
            
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Append file failed due to \n{e}",
                ),
            ],
        )
