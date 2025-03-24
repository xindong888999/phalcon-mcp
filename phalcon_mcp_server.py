#!/usr/bin/env python3

import sys
import json
import subprocess
from typing import Dict, Any, List
from mcp import *

class PhalconMCPServer:
    def __init__(self):
        self.logger = logging.getLogger('phalcon-mcp')

    def phalcon_info(self) -> Dict[str, Any]:
        """显示 Phalcon 版本和环境信息"""
        try:
            result = subprocess.run(['phalcon', 'info'], capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_project(self, name: str, template: str = "basic", directory: str = None) -> Dict[str, Any]:
        """创建新的 Phalcon 项目"""
        cmd = ['phalcon', 'create-project', name]
        if template:
            cmd.extend(['--template', template])
        if directory:
            cmd.extend(['--directory', directory])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_module(self, name: str, project_path: str = None) -> Dict[str, Any]:
        """创建新模块"""
        cmd = ['phalcon', 'create-module', name]
        if project_path:
            cmd.extend(['--project-path', project_path])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_controller(self, name: str, base_class: str = None) -> Dict[str, Any]:
        """创建新控制器"""
        cmd = ['phalcon', 'create-controller', name]
        if base_class:
            cmd.extend(['--base-class', base_class])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_model(self, name: str, schema: str = None, namespace: str = None) -> Dict[str, Any]:
        """创建新模型"""
        cmd = ['phalcon', 'create-model', name]
        if schema:
            cmd.extend(['--schema', schema])
        if namespace:
            cmd.extend(['--namespace', namespace])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_all_models(self, schema: str = None, namespace: str = None) -> Dict[str, Any]:
        """为所有数据库表创建模型"""
        cmd = ['phalcon', 'create-all-models']
        if schema:
            cmd.extend(['--schema', schema])
        if namespace:
            cmd.extend(['--namespace', namespace])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_migration(self, name: str, table_name: str = None, directory: str = None) -> Dict[str, Any]:
        """创建新的数据库迁移"""
        cmd = ['phalcon', 'create-migration', name]
        if table_name:
            cmd.extend(['--table-name', table_name])
        if directory:
            cmd.extend(['--directory', directory])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_scaffold(self, name: str, schema: str = None, template: str = None, force: bool = False) -> Dict[str, Any]:
        """创建完整的 CRUD 脚手架"""
        cmd = ['phalcon', 'create-scaffold', name]
        if schema:
            cmd.extend(['--schema', schema])
        if template:
            cmd.extend(['--template', template])
        if force:
            cmd.append('--force')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_create_webtools(self) -> Dict[str, Any]:
        """初始化 Phalcon Webtools"""
        try:
            result = subprocess.run(['phalcon', 'create-webtools'], capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_serve(self, host: str = 'localhost', port: int = 8000) -> Dict[str, Any]:
        """启动开发服务器"""
        cmd = ['phalcon', 'serve']
        if host:
            cmd.extend(['--host', host])
        if port:
            cmd.extend(['--port', str(port)])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def phalcon_list_commands(self) -> Dict[str, Any]:
        """列出所有可用的 Phalcon 命令"""
        try:
            result = subprocess.run(['phalcon', 'list'], capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def phalcon_help() -> str:
    return """
    Phalcon MCP 工具提供以下功能：

    1. 项目管理
       - phalcon_create_project: 创建新的 Phalcon 项目
       - phalcon_create_module: 创建新模块
       - phalcon_serve: 启动开发服务器

    2. 代码生成
       - phalcon_create_controller: 创建新控制器
       - phalcon_create_model: 创建新模型
       - phalcon_create_all_models: 为所有数据库表创建模型
       - phalcon_create_migration: 创建新的数据库迁移
       - phalcon_create_scaffold: 创建完整的 CRUD 脚手架

    3. 开发工具
       - phalcon_info: 显示 Phalcon 版本和环境信息
       - phalcon_create_webtools: 初始化 Phalcon Webtools
       - phalcon_list_commands: 列出所有可用的 Phalcon 命令
    """

def main():
    server = PhalconMCPServer()
    mcp = MCP()

    @mcp.tool("显示 Phalcon 版本和环境信息")
    def phalcon_info() -> Dict[str, Any]:
        return server.phalcon_info()

    @mcp.tool("创建新的 Phalcon 项目")
    def phalcon_create_project(name: str, template: str = "basic", directory: str = None) -> Dict[str, Any]:
        return server.phalcon_create_project(name, template, directory)

    @mcp.tool("创建新模块")
    def phalcon_create_module(name: str, project_path: str = None) -> Dict[str, Any]:
        return server.phalcon_create_module(name, project_path)

    @mcp.tool("创建新控制器")
    def phalcon_create_controller(name: str, base_class: str = None) -> Dict[str, Any]:
        return server.phalcon_create_controller(name, base_class)

    @mcp.tool("创建新模型")
    def phalcon_create_model(name: str, schema: str = None, namespace: str = None) -> Dict[str, Any]:
        return server.phalcon_create_model(name, schema, namespace)

    @mcp.tool("为所有数据库表创建模型")
    def phalcon_create_all_models(schema: str = None, namespace: str = None) -> Dict[str, Any]:
        return server.phalcon_create_all_models(schema, namespace)

    @mcp.tool("创建新的数据库迁移")
    def phalcon_create_migration(name: str, table_name: str = None, directory: str = None) -> Dict[str, Any]:
        return server.phalcon_create_migration(name, table_name, directory)

    @mcp.tool("创建完整的 CRUD 脚手架")
    def phalcon_create_scaffold(name: str, schema: str = None, template: str = None, force: bool = False) -> Dict[str, Any]:
        return server.phalcon_create_scaffold(name, schema, template, force)

    @mcp.tool("初始化 Phalcon Webtools")
    def phalcon_create_webtools() -> Dict[str, Any]:
        return server.phalcon_create_webtools()

    @mcp.tool("启动开发服务器")
    def phalcon_serve(host: str = 'localhost', port: int = 8000) -> Dict[str, Any]:
        return server.phalcon_serve(host, port)

    @mcp.tool("列出所有可用的 Phalcon 命令")
    def phalcon_list_commands() -> Dict[str, Any]:
        return server.phalcon_list_commands()

    @mcp.prompt("获取 Phalcon MCP 工具帮助信息")
    def help() -> str:
        return phalcon_help()

    mcp.run()

if __name__ == "__main__":
    main()