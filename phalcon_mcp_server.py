import os
import json
import sqlite3
import platform
import re
from pathlib import Path
import argparse
import logging
from typing import Dict, List, Optional, Any, Union, AsyncIterator
from contextlib import asynccontextmanager
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp-server.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('phalcon-mcp')

# Import MCP libraries
try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError as e:
    logger.error(f"Failed to import MCP libraries: {str(e)}. Make sure they are installed.")
    sys.exit(1)

# Global DB manager instance
db_manager = None

class CursorDBManager:
    def __init__(self, cursor_path=None, project_dirs=None):
        """
        Initialize the CursorDBManager with a Cursor main directory and/or list of project directories.
        
        Args:
            cursor_path (str): Path to main Cursor directory (e.g. ~/Library/Application Support/Cursor/User/)
            project_dirs (list): List of paths to Cursor project directories containing state.vscdb files
        """
        if cursor_path:
            self.cursor_path = Path(cursor_path).expanduser().resolve()
        else:
            # Try to get the default cursor path
            self.cursor_path = self.get_default_cursor_path()
            
        self.project_dirs = project_dirs or []
        self.db_paths = {}
        self.projects_info = {}
        self.global_db_path = None
        self.refresh_db_paths()
    
    def get_default_cursor_path(self):
        """Return the default Cursor path based on the operating system"""
        system = platform.system()
        home = Path.home()
        
        default_path = None
        if system == "Darwin":  # macOS
            default_path = home / "Library/Application Support/Cursor/User"
        elif system == "Windows":
            default_path = home / "AppData/Roaming/Cursor/User"
        elif system == "Linux":
            default_path = home / ".config/Cursor/User"
        else:
            logger.warning(f"Unknown operating system: {system}. Cannot determine default Cursor path.")
            return None
        
        logger.info(f"Detected default Cursor path for {system}: {default_path}")
        return default_path
    
    def detect_cursor_projects(self):
        """Detect Cursor projects by scanning the workspaceStorage directory"""
        if not self.cursor_path:
            logger.error("No Cursor path available")
            return []
            
        # Check if the path exists
        if not self.cursor_path.exists():
            logger.error(f"Cursor path does not exist: {self.cursor_path}")
            return []
                
        workspace_storage = self.cursor_path / "workspaceStorage"
        if not workspace_storage.exists():
            logger.warning(f"Workspace storage directory not found: {workspace_storage}")
            return []
            
        logger.info(f"Found workspace storage directory: {workspace_storage}")
        
        projects = []
        
        # Scan all subdirectories in workspaceStorage
        for workspace_dir in workspace_storage.iterdir():
            if not workspace_dir.is_dir():
                continue
                
            workspace_json = workspace_dir / "workspace.json"
            state_db = workspace_dir / "state.vscdb"
            
            if workspace_json.exists() and state_db.exists():
                try:
                    with open(workspace_json, 'r') as f:
                        workspace_data = json.load(f)
                        
                    folder_uri = workspace_data.get("folder")
                    if folder_uri:
                        # Extract the project name from the URI
                        # For "file:///Users/johndamask/code/cursor-chat-browser", get "cursor-chat-browser"
                        project_name = folder_uri.rstrip('/').split('/')[-1]
                        
                        projects.append({
                            "name": project_name,
                            "db_path": str(state_db),
                            "workspace_dir": str(workspace_dir),
                            "folder_uri": folder_uri
                        })
                        logger.info(f"Found project: {project_name} at {state_db}")
                except Exception as e:
                    logger.error(f"Error processing workspace: {workspace_dir}: {e}")
        
        return projects
        
    def refresh_db_paths(self):
        """Scan project directories and identify all state.vscdb files"""
        self.db_paths = {}
        self.projects_info = {}
        
        # First, detect projects from the Cursor directory
        if self.cursor_path:
            cursor_projects = self.detect_cursor_projects()
            for project in cursor_projects:
                project_name = project["name"]
                self.db_paths[project_name] = project["db_path"]
                self.projects_info[project_name] = project
            
            # Set the global storage database path
            global_storage_path = self.cursor_path / "globalStorage" / "state.vscdb"
            if global_storage_path.exists():
                self.global_db_path = str(global_storage_path)
                logger.info(f"Found global storage database at {self.global_db_path}")
            else:
                logger.warning(f"Global storage database not found at {global_storage_path}")
        
        # Then add explicitly specified project directories
        for project_dir in self.project_dirs:
            project_path = Path(project_dir).expanduser().resolve()
            db_path = project_path / "state.vscdb"
            
            if db_path.exists():
                project_name = project_path.name
                self.db_paths[project_name] = str(db_path)
                self.projects_info[project_name] = {
                    "name": project_name,
                    "db_path": str(db_path),
                    "workspace_dir": None,
                    "folder_uri": None
                }
                logger.info(f"Found database: {project_name} at {db_path}")
            else:
                logger.warning(f"No state.vscdb found in {project_path}")
    
    def list_projects(self, detailed=False):
        """
        Return list of available projects
        
        Args:
            detailed (bool): Whether to return detailed project information
            
        Returns:
            dict: Project information (either just DB paths or full details)
        """
        if detailed:
            return self.projects_info
        return self.db_paths
    
    def execute_query(self, project_name, table_name, query_type, key=None, limit=100):
        """
        Execute a query against a specific project's database
        
        Args:
            project_name (str): Name of the project (key in db_paths)
            table_name (str): Either 'ItemTable' or 'cursorDiskKV'
            query_type (str): Type of query ('get_all', 'get_by_key', 'search_keys')
            key (str, optional): Key to search for when using 'get_by_key' or 'search_keys'
            limit (int): Maximum number of results to return
            
        Returns:
            list: Query results
        """
        if project_name not in self.db_paths:
            raise ValueError(f"Project '{project_name}' not found")
            
        if table_name not in ["ItemTable", "cursorDiskKV"]:
            raise ValueError("Table name must be either 'ItemTable' or 'cursorDiskKV'")
        
        db_path = self.db_paths[project_name]
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if query_type == "get_all":
                cursor.execute(f"SELECT key, value FROM {table_name} LIMIT ?", (limit,))
            elif query_type == "get_by_key" and key:
                cursor.execute(f"SELECT key, value FROM {table_name} WHERE key = ?", (key,))
            elif query_type == "search_keys" and key:
                search_term = f"%{key}%"
                cursor.execute(f"SELECT key, value FROM {table_name} WHERE key LIKE ? LIMIT ?", 
                              (search_term, limit))
            else:
                raise ValueError("Invalid query type or missing key parameter")
                
            results = []
            for row in cursor.fetchall():
                key, value = row
                try:
                    # Try to parse JSON value
                    parsed_value = json.loads(value)
                    results.append({"key": key, "value": parsed_value})
                except json.JSONDecodeError:
                    # If not valid JSON, return as string
                    results.append({"key": key, "value": value})
            
            conn.close()
            return results
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise
    
    def get_chat_data(self, project_name):
        """
        Retrieve AI chat data from a project
        
        Args:
            project_name (str): Name of the project
            
        Returns:
            dict: Chat data from the project
        """
        if project_name not in self.db_paths:
            raise ValueError(f"Project '{project_name}' not found")
        
        try:
            results = self.execute_query(
                project_name, 
                "ItemTable", 
                "get_by_key", 
                "workbench.panel.aichat.view.aichat.chatdata"
            )
            
            if results and len(results) > 0:
                return results[0]["value"]
            else:
                return {"error": "No chat data found for this project"}
                
        except Exception as e:
            logger.error(f"Error retrieving chat data: {e}")
            raise
    
    def get_composer_ids(self, project_name):
        """
        Retrieve composer IDs from a project
        
        Args:
            project_name (str): Name of the project
            
        Returns:
            list: List of composer IDs
        """
        if project_name not in self.db_paths:
            raise ValueError(f"Project '{project_name}' not found")
        
        try:
            results = self.execute_query(
                project_name, 
                "ItemTable", 
                "get_by_key", 
                "composer.composerData"
            )
            
            if results and len(results) > 0:
                composer_data = results[0]["value"]
                # Extract composer IDs from the data
                composer_ids = []
                if "allComposers" in composer_data:
                    for composer in composer_data["allComposers"]:
                        if "composerId" in composer:
                            composer_ids.append(composer["composerId"])
                return {
                    "composer_ids": composer_ids,
                    "full_data": composer_data
                }
            else:
                return {"error": "No composer data found for this project"}
                
        except Exception as e:
            logger.error(f"Error retrieving composer IDs: {e}")
            raise
    
    def get_composer_data(self, composer_id):
        """
        Retrieve composer data from global storage
        
        Args:
            composer_id (str): Composer ID
            
        Returns:
            dict: Composer data
        """
        if not self.global_db_path:
            raise ValueError("Global storage database not found")
        
        try:
            conn = sqlite3.connect(self.global_db_path)
            cursor = conn.cursor()
            
            key = f"composerData:{composer_id}"
            cursor.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (key,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                try:
                    return {"composer_id": composer_id, "data": json.loads(row[0])}
                except json.JSONDecodeError:
                    return {"composer_id": composer_id, "data": row[0]}
            else:
                return {"error": f"No data found for composer ID: {composer_id}"}
                
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise

# Create an MCP server with lifespan support
@asynccontextmanager
async def app_lifespan(app: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle with context"""
    try:
        # Initialize the DB manager on startup
        global db_manager
        db_manager = CursorDBManager()
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Cursor IDE SQLite Database MCP Server')
        parser.add_argument('--cursor-path', help='Path to Cursor User directory (e.g. ~/Library/Application Support/Cursor/User/)')
        parser.add_argument('--project-dirs', nargs='+', help='List of additional Cursor project directories to scan')
        
        # Parse known args only, to avoid conflicts with MCP's own args
        args, _ = parser.parse_known_args()
        
        # Configure the DB manager with the Cursor path
        if args.cursor_path:
            db_manager.cursor_path = Path(args.cursor_path).expanduser().resolve()
        
        # Add explicitly specified project directories
        if args.project_dirs:
            for project_dir in args.project_dirs:
                db_manager.add_project_dir(project_dir)
        
        # Log detected Cursor path
        if db_manager.cursor_path:
            logger.info(f"Using Cursor path: {db_manager.cursor_path}")
        else:
            logger.warning("No Cursor path specified or detected")
        
        logger.info(f"Available projects: {list(db_manager.list_projects().keys())}")
        
        # Yield empty context - we're using global db_manager instead
        yield {}
    finally:
        # Cleanup on shutdown (if needed)
        logger.info("Shutting down Cursor DB MCP server")

# Create the MCP server with lifespan
mcp = FastMCP("Phalcon CLI Manager", lifespan=app_lifespan)

# MCP Resources
@mcp.resource("cursor://projects")
def list_all_projects() -> Dict[str, str]:
    """List all available Cursor projects and their database paths"""
    global db_manager
    return db_manager.list_projects(detailed=False)

@mcp.resource("cursor://projects/detailed")
def list_detailed_projects() -> Dict[str, Dict[str, Any]]:
    """List all available Cursor projects with detailed information"""
    global db_manager
    return db_manager.list_projects(detailed=True)

@mcp.resource("cursor://projects/{project_name}/chat")
def get_project_chat_data(project_name: str) -> Dict[str, Any]:
    """Retrieve AI chat data from a specific Cursor project"""
    global db_manager
    try:
        return db_manager.get_chat_data(project_name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Error retrieving chat data: {str(e)}"}

@mcp.resource("cursor://projects/{project_name}/composers")
def get_project_composer_ids(project_name: str) -> Dict[str, Any]:
    """Retrieve composer IDs from a specific Cursor project"""
    global db_manager
    try:
        return db_manager.get_composer_ids(project_name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Error retrieving composer data: {str(e)}"}

@mcp.resource("cursor://composers/{composer_id}")
def get_composer_data_resource(composer_id: str) -> Dict[str, Any]:
    """Retrieve composer data from global storage"""
    global db_manager
    try:
        return db_manager.get_composer_data(composer_id)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Error retrieving composer data: {str(e)}"}

# MCP Tools
@mcp.tool()
def query_table(project_name: str, table_name: str, query_type: str, key: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Query a specific table in a project's database
    
    Args:
        project_name: Name of the project
        table_name: Either 'ItemTable' or 'cursorDiskKV'
        query_type: Type of query ('get_all', 'get_by_key', 'search_keys')
        key: Key to search for when using 'get_by_key' or 'search_keys'
        limit: Maximum number of results to return
    
    Returns:
        List of query results
    """
    global db_manager
    try:
        return db_manager.execute_query(project_name, table_name, query_type, key, limit)
    except ValueError as e:
        return [{"error": str(e)}]
    except sqlite3.Error as e:
        return [{"error": f"Database error: {str(e)}"}]

@mcp.tool()
def refresh_databases() -> Dict[str, Any]:
    """Refresh the list of database paths"""
    global db_manager
    db_manager.refresh_db_paths()
    return {
        "message": "Database paths refreshed",
        "projects": db_manager.list_projects()
    }

@mcp.tool()
def phalcon_info() -> Dict[str, Any]:
    """
    Show Phalcon version and environment information
    
    Returns:
        Result of the operation
    """
    try:
        cmd = "phalcon info"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error getting info: {str(e)}"}

@mcp.tool()
def phalcon_create_project(project_name: str, template: str = "basic", directory: str = None) -> Dict[str, Any]:
    """
    Create a new Phalcon project
    
    Args:
        project_name: Name of the project
        template: Project template type (basic, micro, api, etc.)
        directory: Directory where to create the project
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"phalcon create-project {project_name}"
        if template:
            cmd += f" --template-engine={template}"
        if directory:
            cmd += f" --directory={directory}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating project: {str(e)}"}

@mcp.tool()
def phalcon_create_module(module_name: str, project_path: str = ".") -> Dict[str, Any]:
    """
    Create a new module
    
    Args:
        module_name: Name of the module
        project_path: Path to the Phalcon project
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon create-module {module_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating module: {str(e)}"}

@mcp.tool()
def phalcon_create_controller(controller_name: str, project_path: str = ".", base_class: str = None) -> Dict[str, Any]:
    """
    Create a new controller
    
    Args:
        controller_name: Name of the controller
        project_path: Path to the Phalcon project
        base_class: Base class to extend from
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon create-controller {controller_name}"
        if base_class:
            cmd += f" --base-class={base_class}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating controller: {str(e)}"}

@mcp.tool()
def phalcon_create_model(model_name: str, project_path: str = ".", schema: str = None, namespace: str = None) -> Dict[str, Any]:
    """
    Create a new model
    
    Args:
        model_name: Name of the model
        project_path: Path to the Phalcon project
        schema: Database schema name
        namespace: Namespace for the model
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon create-model {model_name}"
        if schema:
            cmd += f" --schema={schema}"
        if namespace:
            cmd += f" --namespace={namespace}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating model: {str(e)}"}

@mcp.tool()
def phalcon_create_all_models(project_path: str = ".", schema: str = None, namespace: str = None) -> Dict[str, Any]:
    """
    Create models for all tables in the database
    
    Args:
        project_path: Path to the Phalcon project
        schema: Database schema name
        namespace: Namespace for the models
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon create-all-models"
        if schema:
            cmd += f" --schema={schema}"
        if namespace:
            cmd += f" --namespace={namespace}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating all models: {str(e)}"}

@mcp.tool()
def phalcon_create_migration(migration_name: str, project_path: str = ".", table_name: str = None, directory: str = None) -> Dict[str, Any]:
    """
    Create a new migration
    
    Args:
        migration_name: Name of the migration
        project_path: Path to the Phalcon project
        table_name: Name of the table for the migration
        directory: Directory where to create the migration
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon create-migration {migration_name}"
        if table_name:
            cmd += f" --table-name={table_name}"
        if directory:
            cmd += f" --directory={directory}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating migration: {str(e)}"}

@mcp.tool()
def phalcon_create_scaffold(name: str, project_path: str = ".", schema: str = None, template: str = None, force: bool = False) -> Dict[str, Any]:
    """
    Create a full CRUD scaffold
    
    Args:
        name: Name of the scaffold
        project_path: Path to the Phalcon project
        schema: Database schema name
        template: Template to use for scaffold
        force: Force creation even if files exist
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon scaffold {name}"
        if schema:
            cmd += f" --schema={schema}"
        if template:
            cmd += f" --template-engine={template}"
        if force:
            cmd += " --force"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating scaffold: {str(e)}"}

@mcp.tool()
def phalcon_create_webtools(project_path: str = ".") -> Dict[str, Any]:
    """
    Initialize Phalcon Webtools
    
    Args:
        project_path: Path to the Phalcon project
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon webtools"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error creating webtools: {str(e)}"}

@mcp.tool()
def phalcon_serve(project_path: str = ".", host: str = "localhost", port: int = 8000) -> Dict[str, Any]:
    """
    Serve the application
    
    Args:
        project_path: Path to the Phalcon project
        host: Host to serve on
        port: Port to serve on
    
    Returns:
        Result of the operation
    """
    try:
        cmd = f"cd {project_path} && phalcon serve --host={host} --port={port}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error starting server: {str(e)}"}

@mcp.tool()
def phalcon_list_commands() -> Dict[str, Any]:
    """
    List all available Phalcon commands
    
    Returns:
        List of available commands and their descriptions
    """
    try:
        cmd = "phalcon commands"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {"error": f"Error listing commands: {str(e)}"}

# MCP Prompts
@mcp.prompt()
def phalcon_help() -> str:
    """Create a prompt to help with Phalcon commands"""
    return """
    我可以帮助你使用 Phalcon 框架的命令。以下是我可以做的事情：
    
    1. 项目管理：
       - 创建新的 Phalcon 项目
       - 创建新模块
       - 启动开发服务器
    
    2. 代码生成：
       - 创建控制器
       - 创建模型（单个或所有表）
       - 创建数据库迁移
       - 生成完整的 CRUD 脚手架
    
    3. 开发工具：
       - 初始化 Phalcon Webtools
       - 查看系统信息
       - 列出所有可用命令
    
    你想执行哪个操作？
    """

@mcp.prompt()
def explore_cursor_projects() -> str:
    """Create a prompt to explore Cursor projects"""
    return """
    I can help you explore your Cursor projects and their data. 
    
    Here are some things I can do:
    1. List all your Cursor projects
    2. Show AI chat history from a project
    3. Find composer data
    4. Query specific tables in the Cursor database
    
    What would you like to explore?
    """

@mcp.prompt()
def analyze_chat_data(project_name: str) -> str:
    """Create a prompt to analyze chat data from a specific project"""
    return f"""
    I'll analyze the AI chat data from your '{project_name}' project.
    
    I can help you understand:
    - The conversation history
    - Code snippets shared in the chat
    - Common themes or questions
    
    Would you like me to focus on any specific aspect of the chat data?
    """