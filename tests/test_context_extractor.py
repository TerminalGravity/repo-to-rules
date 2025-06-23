"""Tests for context extractor."""

import pytest
from unittest.mock import Mock

from src.repo_to_rules.context_extractor import ContextExtractor
from src.repo_to_rules.models import RepoMetadata, FileContent


class TestContextExtractor:
    
    def setup_method(self):
        self.extractor = ContextExtractor()
    
    def test_extract_context_basic(self):
        """Test basic context extraction."""
        metadata = RepoMetadata(
            name="test-repo",
            full_name="org/test-repo",
            language="JavaScript",
            description="Test repository"
        )
        
        files = [
            FileContent(
                path="package.json",
                content='{"name": "test-repo", "dependencies": {"react": "^18.0.0"}}',
                size=100,
                type="file"
            ),
            FileContent(
                path="src/index.js",
                content="import React from 'react';\nconsole.log('Hello');",
                size=50,
                type="file"
            )
        ]
        
        context = self.extractor.extract_context(metadata, files, {})
        
        assert context.metadata.name == "test-repo"
        assert "javascript" in context.structure.tech_stack
        assert "npm" in context.structure.build_tools
        assert "react" in context.dependencies.runtime
    
    def test_detect_tech_stack(self):
        """Test technology stack detection."""
        files = [
            FileContent(path="package.json", content="{}", size=10, type="file"),
            FileContent(path="requirements.txt", content="flask==2.0.0", size=20, type="file"),
            FileContent(path="Dockerfile", content="FROM node:16", size=30, type="file")
        ]
        
        metadata = RepoMetadata(name="test", full_name="org/test")
        context = self.extractor.extract_context(metadata, files, {})
        
        assert "javascript" in context.structure.tech_stack
        assert "python" in context.structure.tech_stack
        assert "docker" in context.structure.tech_stack
    
    def test_extract_dependencies_package_json(self):
        """Test package.json dependency extraction."""
        files = [
            FileContent(
                path="package.json",
                content='''{
                    "dependencies": {
                        "react": "^18.0.0",
                        "express": "^4.18.0"
                    },
                    "devDependencies": {
                        "jest": "^29.0.0",
                        "eslint": "^8.0.0"
                    }
                }''',
                size=200,
                type="file"
            )
        ]
        
        metadata = RepoMetadata(name="test", full_name="org/test")
        context = self.extractor.extract_context(metadata, files, {})
        
        assert context.dependencies.runtime["react"] == "^18.0.0"
        assert context.dependencies.runtime["express"] == "^4.18.0"
        assert context.dependencies.dev["jest"] == "^29.0.0"
        assert context.dependencies.dev["eslint"] == "^8.0.0"
    
    def test_extract_testing_info(self):
        """Test testing framework detection."""
        files = [
            FileContent(path="jest.config.js", content="module.exports = {};", size=20, type="file"),
            FileContent(path="tests/test_app.py", content="def test_something(): pass", size=30, type="file"),
            FileContent(path="cypress.json", content="{}", size=10, type="file")
        ]
        
        metadata = RepoMetadata(name="test", full_name="org/test")
        context = self.extractor.extract_context(metadata, files, {})
        
        assert "jest" in context.testing.frameworks
        assert "pytest" in context.testing.frameworks
        assert "cypress" in context.testing.frameworks
        assert "tests" in context.testing.test_directories
    
    def test_extract_build_info(self):
        """Test build information extraction."""
        files = [
            FileContent(
                path="package.json",
                content='''{
                    "scripts": {
                        "start": "node server.js",
                        "build": "webpack --mode production",
                        "test": "jest"
                    }
                }''',
                size=150,
                type="file"
            ),
            FileContent(path="Dockerfile", content="FROM node:16", size=20, type="file")
        ]
        
        metadata = RepoMetadata(name="test", full_name="org/test")
        context = self.extractor.extract_context(metadata, files, {})
        
        assert context.build.scripts["start"] == "node server.js"
        assert context.build.scripts["build"] == "webpack --mode production"
        assert context.build.docker_config is not None
        assert context.build.docker_config["has_docker"] is True
    
    def test_extract_services_info(self):
        """Test external services detection."""
        files = [
            FileContent(
                path="src/database.js",
                content="const mongoose = require('mongoose'); const redis = require('redis');",
                size=100,
                type="file"
            ),
            FileContent(
                path="config.py",
                content="STRIPE_SECRET_KEY = 'sk_test_...'; AWS_REGION = 'us-east-1'",
                size=80,
                type="file"
            ),
            FileContent(
                path=".env.example",
                content="DATABASE_URL=\nREDIS_URL=\nSTRIPE_KEY=\n",
                size=50,
                type="file"
            )
        ]
        
        metadata = RepoMetadata(name="test", full_name="org/test")
        context = self.extractor.extract_context(metadata, files, {})
        
        assert "mongodb" in context.services.databases
        assert "redis" in context.services.databases
        assert "stripe" in context.services.third_party_integrations
        assert "aws" in context.services.cloud_services
        assert "DATABASE_URL" in context.services.environment_variables
    
    def test_parse_requirements_txt(self):
        """Test requirements.txt parsing."""
        content = """
        flask==2.0.0
        requests>=2.25.0
        pytest
        # This is a comment
        django==4.0.0
        """
        
        deps = self.extractor._parse_requirements_txt(content)
        
        assert deps["flask"] == "2.0.0"
        assert deps["requests"] == ">=2.25.0"
        assert deps["pytest"] == "*"
        assert deps["django"] == "4.0.0"
        assert len(deps) == 4  # Comment should be ignored