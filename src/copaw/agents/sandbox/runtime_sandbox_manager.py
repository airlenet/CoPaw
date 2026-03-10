# -*- coding: utf-8 -*-
"""AgentScope Runtime Sandbox Manager"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from agentscope_runtime.sandbox import BaseSandboxAsync, FilesystemSandboxAsync


class AgentScopeRuntimeSandboxManager:
    """AgentScope Runtime沙箱管理器"""
    
    def __init__(self, config=None):
        """初始化沙箱管理器"""
        self.config = config or {}
        self.base_sandbox = None
        self.filesystem_sandbox = None
    
    async def get_base_sandbox(self):
        """获取基础沙箱实例"""
        if not self.base_sandbox:
            self.base_sandbox = BaseSandboxAsync()
            await self.base_sandbox.__aenter__()
        return self.base_sandbox
    
    async def get_filesystem_sandbox(self):
        """获取文件系统沙箱实例"""
        if not self.filesystem_sandbox:
            self.filesystem_sandbox = FilesystemSandboxAsync()
            await self.filesystem_sandbox.__aenter__()
        return self.filesystem_sandbox
    
    async def get_sandbox(self):
        """根据配置获取沙箱实例"""
        sandbox_type = self.config.get("type", "base")
        if sandbox_type == "filesystem":
            return await self.get_filesystem_sandbox()
        else:
            return await self.get_base_sandbox()
    
    async def execute_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """在沙箱中执行命令"""
        sandbox = await self.get_sandbox()
        result = await sandbox.run_shell_command(command=command)
        # 处理返回值格式
        if isinstance(result, dict):
            # 检查是否有content字段（与run_ipython_cell格式类似）
            if "content" in result:
                content = result.get("content", [])
                stdout = ""
                stderr = ""
                for item in content:
                    if item.get("type") == "text":
                        stdout += item.get("text", "")
                return {
                    "returncode": 0 if not result.get("isError", False) else 1,
                    "stdout": stdout,
                    "stderr": stderr
                }
            else:
                return {
                    "returncode": result.get("returncode", 0),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", "")
                }
        else:
            return {
                "returncode": 0,
                "stdout": str(result),
                "stderr": ""
            }
    
    async def run_python_code(self, code: str) -> Dict[str, Any]:
        """在沙箱中运行Python代码"""
        sandbox = await self.get_sandbox()
        result = await sandbox.run_ipython_cell(code=code)
        # 处理返回值格式
        if not result.get("isError", False):
            content = result.get("content", [])
            output = ""
            for item in content:
                if item.get("type") == "text":
                    output += item.get("text", "")
            return {
                "success": True,
                "output": output
            }
        else:
            return {
                "success": False,
                "error": "Python code execution failed"
            }
    
    async def read_file(self, file_path: str) -> str:
        """在沙箱中读取文件"""
        sandbox = await self.get_sandbox()
        try:
            # 使用绝对路径
            abs_path = f"/workspace/{file_path}" if not file_path.startswith('/') else file_path
            # 使用Python代码读取文件
            code = f"""
with open('{abs_path}', 'r', encoding='utf-8') as f:
    print(f.read())
"""
            result = await sandbox.run_ipython_cell(code=code)
            # 处理返回值格式
            if not result.get("isError", False):
                content = result.get("content", [])
                text = ""
                for item in content:
                    if item.get("type") == "text":
                        text += item.get("text", "")
                return text
            return ""
        except Exception as e:
            print(f"Read file error: {e}")
            return ""
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """在沙箱中写入文件"""
        sandbox = await self.get_sandbox()
        try:
            # 使用绝对路径
            abs_path = f"/workspace/{file_path}" if not file_path.startswith('/') else file_path
            # 使用Python代码写入文件
            code = f"""
import os
# 创建目录
os.makedirs(os.path.dirname('{abs_path}'), exist_ok=True)
# 写入文件
with open('{abs_path}', 'w', encoding='utf-8') as f:
    f.write('''{content}''')
# 验证文件是否存在
import os
if os.path.exists('{abs_path}'):
    print('File written successfully:', os.path.getsize('{abs_path}'), 'bytes')
else:
    print('File creation failed')
"""
            result = await sandbox.run_ipython_cell(code=code)
            
            # 检查命令是否成功执行
            if isinstance(result, dict):
                if "isError" in result:
                    return not result.get("isError", False)
            return True
        except Exception as e:
            print(f"Write file error: {e}")
            return False
    
    async def append_file(self, file_path: str, content: str) -> bool:
        """在沙箱中追加文件"""
        sandbox = await self.get_sandbox()
        try:
            # 使用绝对路径
            abs_path = f"/workspace/{file_path}" if not file_path.startswith('/') else file_path
            # 使用Python代码追加文件
            code = f"""
import os
# 创建目录
os.makedirs(os.path.dirname('{abs_path}'), exist_ok=True)
# 追加文件
with open('{abs_path}', 'a', encoding='utf-8') as f:
    f.write('''{content}''')
# 验证文件是否存在
import os
if os.path.exists('{abs_path}'):
    print('File appended successfully:', os.path.getsize('{abs_path}'), 'bytes')
else:
    print('File append failed')
"""
            result = await sandbox.run_ipython_cell(code=code)
            
            # 检查命令是否成功执行
            if isinstance(result, dict):
                if "isError" in result:
                    return not result.get("isError", False)
            return True
        except Exception as e:
            print(f"Append file error: {e}")
            return False
    
    async def delete_sandbox(self):
        """删除沙箱实例"""
        if self.base_sandbox:
            await self.base_sandbox.__aexit__(None, None, None)
            self.base_sandbox = None
        if self.filesystem_sandbox:
            await self.filesystem_sandbox.__aexit__(None, None, None)
            self.filesystem_sandbox = None
    
    async def __aenter__(self):
        """进入上下文管理器"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        await self.delete_sandbox()
