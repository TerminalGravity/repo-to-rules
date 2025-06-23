"""Tests for MCP generator."""

import pytest

from src.repo_to_rules.mcp_generator import MCPGenerator
from src.repo_to_rules.models import (
    RepoMetadata, RepositoryContext, ProjectStructure, 
    Dependencies, ServicesInfo
)


class TestMCPGenerator:
    
    def setup_method(self):
        self.generator = MCPGenerator()
    
    def test_generate_claude_mcp_config_basic(self):
        """Test basic Claude MCP configuration generation."""
        context = self._create_test_context()
        
        config = self.generator.generate_claude_mcp_config(context)
        
        assert "mcpServers" in config
        assert "filesystem" in config["mcpServers"]
        assert "git" in config["mcpServers"]
        assert "memory" in config["mcpServers"]
        assert config["version"] == "1.0.0"
    
    def test_generate_cursor_mcp_config_basic(self):
        """Test basic Cursor MCP configuration generation."""
        context = self._create_test_context()
        
        config = self.generator.generate_cursor_mcp_config(context)
        
        assert "mcpServers" in config
        assert "filesystem" in config["mcpServers"]
        assert "git" in config["mcpServers"]
    
    def test_database_specific_servers(self):
        """Test database-specific MCP servers."""
        context = self._create_test_context()
        context.services.databases = ["postgresql", "sqlite"]
        
        config = self.generator.generate_claude_mcp_config(context)
        
        assert "postgres" in config["mcpServers"]
        assert "sqlite" in config["mcpServers"]
    
    def test_python_specific_servers(self):
        """Test Python-specific MCP servers."""
        context = self._create_test_context()
        context.metadata.language = "Python"
        context.structure.tech_stack = ["python"]
        context.structure.package_managers = ["poetry"]
        context.dependencies.runtime = {"fastapi": "0.68.0", "Django": "4.0.0"}
        
        python_servers = self.generator._get_python_mcp_servers(context)
        
        assert "poetry" in python_servers
        assert "fastapi" in python_servers
        assert "django" in python_servers
    
    def test_javascript_specific_servers(self):
        """Test JavaScript-specific MCP servers."""
        context = self._create_test_context()
        context.metadata.language = "JavaScript"
        context.structure.tech_stack = ["javascript"]
        context.structure.package_managers = ["npm"]
        context.dependencies.runtime = {"react": "18.0.0", "next": "12.0.0"}
        
        js_servers = self.generator._get_javascript_mcp_servers(context)
        
        assert "npm" in js_servers
        assert "react-dev" in js_servers
        assert "nextjs" in js_servers
    
    def test_docker_servers(self):
        """Test Docker-specific MCP servers."""
        context = self._create_test_context()
        context.build.docker_config = {"has_docker": True}
        
        docker_servers = self.generator._get_docker_mcp_servers(context)
        
        assert "docker" in docker_servers
    
    def test_cloud_service_detection(self):
        """Test cloud service MCP configuration."""
        context = self._create_test_context()
        context.services.cloud_services = ["aws", "gcp"]
        context.services.third_party_integrations = ["stripe"]
        
        config = self.generator.generate_project_specific_mcp_config(context)
        
        assert "aws-tools" in config
        assert "gcp-tools" in config
        assert "stripe" in config
        assert config["aws-tools"]["env"]["AWS_REGION"] == "us-east-1"
    
    def test_mcp_server_structure(self):
        """Test MCP server configuration structure."""
        context = self._create_test_context()
        
        config = self.generator.generate_claude_mcp_config(context)
        filesystem_config = config["mcpServers"]["filesystem"]
        
        assert "command" in filesystem_config
        assert "args" in filesystem_config
        assert "env" in filesystem_config
        assert filesystem_config["command"] == "npx"
        assert "-y" in filesystem_config["args"]
    
    def _create_test_context(self) -> RepositoryContext:
        """Create a test repository context."""
        metadata = RepoMetadata(
            name="test-repo",
            full_name="org/test-repo",
            language="JavaScript",
            description="Test repository"
        )
        
        structure = ProjectStructure(
            tech_stack=["javascript"],
            package_managers=["npm"],
            directories=["src", "tests"]
        )
        
        dependencies = Dependencies(
            runtime={"react": "18.0.0"},
            dev={"jest": "29.0.0"}
        )
        
        services = ServicesInfo(
            databases=[],
            cloud_services=[],
            third_party_integrations=[]
        )
        
        # Create context with mock objects for other fields
        from src.repo_to_rules.models import CodePatterns, TestingInfo, BuildInfo
        
        return RepositoryContext(
            metadata=metadata,
            structure=structure,
            dependencies=dependencies,
            code_patterns=CodePatterns(),
            testing=TestingInfo(),
            build=BuildInfo(),
            services=services,
            key_files=[]
        )