"""Configuration settings for the repo-to-rules application."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # GitHub settings
    github_token: str = Field(..., description="GitHub personal access token")
    github_org: str = Field(default="alldigitalrewards", description="GitHub organization name")
    
    # Claude settings
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model to use")
    
    # Processing settings
    max_concurrent_repos: int = Field(default=5, description="Maximum concurrent repository processing")
    rate_limit_delay: float = Field(default=1.0, description="Delay between API calls in seconds")
    
    # Output settings
    output_dir: str = Field(default="output", description="Output directory for generated rules")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing output")
    
    # Repository filtering
    include_repos: Optional[List[str]] = Field(default=None, description="Specific repos to include")
    exclude_repos: List[str] = Field(default_factory=list, description="Repos to exclude")
    min_stars: int = Field(default=0, description="Minimum stars for repository inclusion")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"