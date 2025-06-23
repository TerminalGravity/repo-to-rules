"""Data models for the repo-to-rules application."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RepoMetadata(BaseModel):
    """Repository metadata."""
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)
    stars: int = 0
    forks: int = 0
    topics: List[str] = Field(default_factory=list)
    default_branch: str = "main"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    size: int = 0
    archived: bool = False
    private: bool = False


class FileContent(BaseModel):
    """File content with metadata."""
    path: str
    content: str
    size: int
    type: str  # 'file' or 'dir'
    encoding: Optional[str] = None


class ProjectStructure(BaseModel):
    """Project structure analysis."""
    root_files: List[str] = Field(default_factory=list)
    directories: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    build_tools: List[str] = Field(default_factory=list)
    testing_frameworks: List[str] = Field(default_factory=list)
    package_managers: List[str] = Field(default_factory=list)
    config_files: Dict[str, str] = Field(default_factory=dict)


class Dependencies(BaseModel):
    """Project dependencies."""
    runtime: Dict[str, str] = Field(default_factory=dict)
    dev: Dict[str, str] = Field(default_factory=dict)
    peer: Dict[str, str] = Field(default_factory=dict)
    optional: Dict[str, str] = Field(default_factory=dict)


class CodePatterns(BaseModel):
    """Code patterns and conventions."""
    style_guide: Optional[str] = None
    linting_rules: Dict[str, Any] = Field(default_factory=dict)
    formatting_config: Dict[str, Any] = Field(default_factory=dict)
    common_patterns: List[str] = Field(default_factory=list)
    architectural_patterns: List[str] = Field(default_factory=list)
    naming_conventions: Dict[str, str] = Field(default_factory=dict)


class TestingInfo(BaseModel):
    """Testing information."""
    frameworks: List[str] = Field(default_factory=list)
    test_directories: List[str] = Field(default_factory=list)
    coverage_config: Optional[Dict[str, Any]] = None
    test_patterns: List[str] = Field(default_factory=list)
    mock_frameworks: List[str] = Field(default_factory=list)


class BuildInfo(BaseModel):
    """Build and deployment information."""
    build_tools: List[str] = Field(default_factory=list)
    scripts: Dict[str, str] = Field(default_factory=dict)
    docker_config: Optional[Dict[str, Any]] = None
    ci_cd_config: Optional[Dict[str, Any]] = None
    deployment_targets: List[str] = Field(default_factory=list)


class ServicesInfo(BaseModel):
    """External services and APIs."""
    databases: List[str] = Field(default_factory=list)
    apis: List[str] = Field(default_factory=list)
    cloud_services: List[str] = Field(default_factory=list)
    third_party_integrations: List[str] = Field(default_factory=list)
    environment_variables: List[str] = Field(default_factory=list)


class RepositoryContext(BaseModel):
    """Complete repository context."""
    metadata: RepoMetadata
    structure: ProjectStructure
    dependencies: Dependencies
    code_patterns: CodePatterns
    testing: TestingInfo
    build: BuildInfo
    services: ServicesInfo
    key_files: List[FileContent] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.now)


class ClaudeRules(BaseModel):
    """Claude Code rules and configuration."""
    main_rules: str
    project_context: str
    coding_conventions: str
    testing_guide: str
    architecture: str
    slash_commands: Dict[str, str] = Field(default_factory=dict)
    mcp_config: Dict[str, Any] = Field(default_factory=dict)


class CursorRules(BaseModel):
    """Cursor rules and configuration."""
    cursorrules: str
    context: str
    snippets: Dict[str, Any] = Field(default_factory=dict)
    tasks: Dict[str, Any] = Field(default_factory=dict)
    mcp_config: Dict[str, Any] = Field(default_factory=dict)


class GeneratedOutput(BaseModel):
    """Generated output for a repository."""
    repo_name: str
    claude_rules: ClaudeRules
    cursor_rules: CursorRules
    context_summary: RepositoryContext
    generation_timestamp: datetime = Field(default_factory=datetime.now)