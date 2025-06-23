"""MCP (Model Context Protocol) configuration generator."""

import logging
from typing import Dict, Any, List, Optional

from .models import RepositoryContext

logger = logging.getLogger(__name__)


class MCPGenerator:
    """Generate MCP server configurations for different tools."""
    
    def __init__(self):
        self.common_mcp_servers = {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "env": {"ALLOWED_DIRECTORIES": "."}
            },
            "git": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-git"],
                "env": {}
            },
            "sqlite": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sqlite"],
                "env": {}
            },
            "postgres": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
                "env": {}
            },
            "brave-search": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": ""}
            },
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""}
            },
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
                "env": {}
            }
        }
    
    def generate_claude_mcp_config(self, context: RepositoryContext) -> Dict[str, Any]:
        """Generate MCP configuration for Claude Code."""
        logger.info(f"Generating Claude MCP config for {context.metadata.name}")
        
        servers = {}
        
        # Always include filesystem and git
        servers["filesystem"] = self.common_mcp_servers["filesystem"].copy()
        servers["git"] = self.common_mcp_servers["git"].copy()
        
        # Add memory server for context retention
        servers["memory"] = self.common_mcp_servers["memory"].copy()
        
        # Database servers based on detected databases
        if "postgresql" in context.services.databases:
            servers["postgres"] = self.common_mcp_servers["postgres"].copy()
        
        if "sqlite" in context.services.databases:
            servers["sqlite"] = self.common_mcp_servers["sqlite"].copy()
        
        # GitHub server for repository operations
        servers["github"] = self.common_mcp_servers["github"].copy()
        
        # Search server for documentation and research
        servers["brave-search"] = self.common_mcp_servers["brave-search"].copy()
        
        # Language-specific servers
        if context.metadata.language == "Python" or "python" in context.structure.tech_stack:
            servers.update(self._get_python_mcp_servers(context))
        
        if context.metadata.language == "JavaScript" or "javascript" in context.structure.tech_stack:
            servers.update(self._get_javascript_mcp_servers(context))
        
        # Docker server if Docker is used
        if context.build.docker_config:
            servers.update(self._get_docker_mcp_servers(context))
        
        config = {
            "mcpServers": servers,
            "description": f"MCP configuration for {context.metadata.name}",
            "version": "1.0.0"
        }
        
        return config
    
    def generate_cursor_mcp_config(self, context: RepositoryContext) -> Dict[str, Any]:
        """Generate MCP configuration for Cursor."""
        logger.info(f"Generating Cursor MCP config for {context.metadata.name}")
        
        # Cursor MCP config is similar to Claude but may have different format
        servers = {}
        
        # Core servers
        servers["filesystem"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "env": {"ALLOWED_DIRECTORIES": "."}
        }
        
        servers["git"] = {
            "command": "npx", 
            "args": ["-y", "@modelcontextprotocol/server-git"],
            "env": {}
        }
        
        # Database servers
        for db in context.services.databases:
            if db == "postgresql":
                servers["postgres"] = self.common_mcp_servers["postgres"].copy()
            elif db == "sqlite":
                servers["sqlite"] = self.common_mcp_servers["sqlite"].copy()
        
        # Language-specific additions
        if "javascript" in context.structure.tech_stack or "typescript" in context.structure.tech_stack:
            servers.update(self._get_javascript_cursor_servers(context))
        
        if "python" in context.structure.tech_stack:
            servers.update(self._get_python_cursor_servers(context))
        
        config = {
            "mcpServers": servers,
            "description": f"Cursor MCP configuration for {context.metadata.name}",
            "version": "1.0.0"
        }
        
        return config
    
    def _get_python_mcp_servers(self, context: RepositoryContext) -> Dict[str, Any]:
        """Get Python-specific MCP servers."""
        servers = {}
        
        # Pytest server if pytest is used
        if "pytest" in context.testing.frameworks:
            servers["pytest"] = {
                "command": "python",
                "args": ["-m", "mcp_pytest_server"],
                "env": {}
            }
        
        # Django server if Django is detected
        if any(dep.startswith("Django") for dep in context.dependencies.runtime.keys()):
            servers["django"] = {
                "command": "python",
                "args": ["-m", "mcp_django_server"],
                "env": {}
            }
        
        # FastAPI server if FastAPI is detected
        if "fastapi" in context.dependencies.runtime:
            servers["fastapi"] = {
                "command": "python",
                "args": ["-m", "mcp_fastapi_server"],
                "env": {}
            }
        
        # Poetry server if poetry is used
        if "poetry" in context.structure.package_managers:
            servers["poetry"] = {
                "command": "python",
                "args": ["-m", "mcp_poetry_server"],
                "env": {}
            }
        
        return servers
    
    def _get_javascript_mcp_servers(self, context: RepositoryContext) -> Dict[str, Any]:
        """Get JavaScript-specific MCP servers."""
        servers = {}
        
        # NPM server if npm is used
        if "npm" in context.structure.package_managers:
            servers["npm"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-npm"],
                "env": {}
            }
        
        # React server if React is detected
        if "react" in context.dependencies.runtime:
            servers["react-dev"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-react"],
                "env": {}
            }
        
        # Next.js server if Next.js is detected
        if "next" in context.dependencies.runtime:
            servers["nextjs"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-nextjs"],
                "env": {}
            }
        
        # Jest server if Jest is used for testing
        if "jest" in context.testing.frameworks:
            servers["jest"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-jest"],
                "env": {}
            }
        
        # Webpack server if webpack is used
        if "webpack" in context.build.build_tools:
            servers["webpack"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-webpack"],
                "env": {}
            }
        
        return servers
    
    def _get_docker_mcp_servers(self, context: RepositoryContext) -> Dict[str, Any]:
        """Get Docker-specific MCP servers."""
        servers = {}
        
        if context.build.docker_config:
            servers["docker"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-docker"],
                "env": {}
            }
        
        return servers
    
    def _get_javascript_cursor_servers(self, context: RepositoryContext) -> Dict[str, Any]:
        """Get JavaScript-specific servers for Cursor."""
        servers = {}
        
        # TypeScript language server
        if "typescript" in context.structure.tech_stack:
            servers["typescript"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-typescript"],
                "env": {}
            }
        
        # ESLint server
        if "eslint" in context.code_patterns.linting_rules:
            servers["eslint"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-eslint"],
                "env": {}
            }
        
        return servers
    
    def _get_python_cursor_servers(self, context: RepositoryContext) -> Dict[str, Any]:
        """Get Python-specific servers for Cursor."""
        servers = {}
        
        # Python language server
        servers["python-lsp"] = {
            "command": "python",
            "args": ["-m", "mcp_python_lsp"],
            "env": {}
        }
        
        # Black formatter server
        if any("black" in str(config) for config in context.code_patterns.formatting_config.values()):
            servers["black"] = {
                "command": "python",
                "args": ["-m", "mcp_black_server"],
                "env": {}
            }
        
        return servers
    
    def generate_project_specific_mcp_config(self, context: RepositoryContext) -> Dict[str, Any]:
        """Generate project-specific MCP configuration based on detected patterns."""
        config = {}
        
        # Cloud service integrations
        if "aws" in context.services.cloud_services:
            config["aws-tools"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-aws"],
                "env": {
                    "AWS_ACCESS_KEY_ID": "",
                    "AWS_SECRET_ACCESS_KEY": "",
                    "AWS_REGION": "us-east-1"
                }
            }
        
        if "gcp" in context.services.cloud_services:
            config["gcp-tools"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-gcp"],
                "env": {
                    "GOOGLE_APPLICATION_CREDENTIALS": ""
                }
            }
        
        # API integrations
        if "stripe" in context.services.third_party_integrations:
            config["stripe"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-stripe"],
                "env": {
                    "STRIPE_SECRET_KEY": ""
                }
            }
        
        # Monitoring and logging
        if any(service in context.services.third_party_integrations for service in ["datadog", "newrelic", "sentry"]):
            config["monitoring"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-monitoring"],
                "env": {}
            }
        
        return config