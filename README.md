# Phalcon MCP Server

一个用于执行 Phalcon 5.0.x 框架命令的 Model Context Protocol (MCP) 服务器。该服务器允许 AI 助手创建和管理 Phalcon 项目、控制器、模型等。

## 前置条件

- Phalcon Framework
- Cursor IDE
- Python 3.x
- Phalcon 5.0.x开发工具安装好   composer global require phalcon/devtools:"^5.0.x@dev" --dev

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
4. 命令：cmd /c uv run --with mcp[cli] mcp run \<完整路径\>/phalcon_mcp_server.py

```Json
    "phalcon-mcp": {
      "command": "cmd",
      "args": [
        "/c",
        "uv",
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "C:\\Users\\Administrator\\Desktop\\mcp\\phalcon-mcp\\phalcon_mcp_server.py"
      ]
    }
```

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

## 使用示例

### 查看 Phalcon 信息
```
命令：查看 Phalcon 版本和环境信息
结果：显示当前安装的 Phalcon 版本和系统环境信息
```

### 创建新项目
```
命令：创建一个名为 "my-app" 的新项目
参数：
- template: basic（默认）、micro 或 api
- directory: 项目创建位置
结果：创建一个新的 Phalcon 项目基础结构
```

### 创建模块
```
命令：创建一个名为 "admin" 的新模块
结果：在项目中创建一个新的模块结构
```

### 创建控制器
```
命令：创建一个名为 "Users" 的控制器
参数：
- base_class: 可选的基类
结果：创建一个新的控制器文件
```

### 创建模型
```
命令：创建一个名为 "Products" 的模型
参数：
- schema: 数据库 schema
- namespace: 命名空间
结果：创建一个新的模型文件
```

### 创建所有模型
```
命令：为数据库中的所有表创建模型
参数：
- schema: 数据库 schema
- namespace: 命名空间
结果：为所有数据库表创建对应的模型文件
```

### 创建迁移
```
命令：创建一个名为 "create_users_table" 的迁移
参数：
- table_name: 表名
- directory: 迁移文件位置
结果：创建一个新的数据库迁移文件
```

### 创建脚手架
```
命令：为 "products" 创建完整的 CRUD 界面
参数：
- schema: 数据库 schema
- template: 模板引擎
- force: 是否强制创建
结果：生成完整的 CRUD 接口
```

### 初始化 Webtools
```
命令：在项目中初始化 Phalcon Webtools
结果：设置 Phalcon 的 Web 开发工具
```

### 启动开发服务器
```
命令：启动开发服务器
参数：
- host: 主机地址（默认：localhost）
- port: 端口号（默认：8000）
结果：启动 PHP 开发服务器运行应用
```

## 工作原理

该服务器使用 MCP 协议与 Cursor IDE 集成，允许 AI 助手直接执行 Phalcon 命令行工具的各种功能。它通过标准输入输出（stdin/stdout）进行通信，不需要额外的网络端口。

## 注意事项
1. 确保系统中已正确安装 Phalcon Framework
2. 确保 PHP 环境变量配置正确
3. Windows 系统需要确保 `phalcon.bat` 在系统路径中

## 许可证

MIT