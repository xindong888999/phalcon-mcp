# Phalcon MCP Server

一个用于执行 Phalcon 框架命令的 Model Context Protocol (MCP) 服务器。该服务器允许 AI 助手创建和管理 Phalcon 项目、控制器、模型等。

## 前置条件

- Phalcon Framework
- Cursor IDE
- Python 3.x

## 安装

### 快速安装

使用提供的安装脚本安装所有依赖：

```bash
python install.py
```

此脚本将安装：
- 基本的 MCP 服务器和依赖
- 必需的 Python 包

## 在 Cursor IDE 中使用

1. 打开 Cursor，导航到 Settings->Cursor Settings->MCP
2. 点击：Add new MCP server
3. 名称：Phalcon MCP；类型：Command
4. 命令：<完整路径>uv run --with mcp[cli] mcp run <完整路径>/phalcon_mcp_server.py

## 可用工具

- `phalcon_info` - 显示 Phalcon 版本和环境信息
- `phalcon_create_project` - 创建新的 Phalcon 项目
- `phalcon_create_module` - 创建新模块
- `phalcon_create_controller` - 创建新控制器
- `phalcon_create_model` - 创建新模型
- `phalcon_create_all_models` - 为所有数据库表创建模型
- `phalcon_create_migration` - 创建新的数据库迁移
- `phalcon_create_scaffold` - 创建完整的 CRUD 脚手架
- `phalcon_create_webtools` - 初始化 Phalcon Webtools
- `phalcon_serve` - 启动开发服务器
- `phalcon_list_commands` - 列出所有可用的 Phalcon 命令

## 工作原理

该服务器使用 MCP 协议与 Cursor IDE 集成，允许 AI 助手直接执行 Phalcon 命令行工具的各种功能。它通过标准输入输出（stdin/stdout）进行通信，不需要额外的网络端口。

## 注意事项
1. 确保系统中已正确安装 Phalcon Framework
2. 确保 PHP 环境变量配置正确
3. Windows 系统需要确保 `phalcon.bat` 在系统路径中

## 许可证

MIT