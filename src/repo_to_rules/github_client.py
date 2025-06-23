"""GitHub client for repository access and analysis."""

import asyncio
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from pathlib import Path
import base64

from github import Github, Repository, GithubException
from github.ContentFile import ContentFile

from .models import RepoMetadata, FileContent
from .config import Settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API client for repository operations."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.github = Github(settings.github_token)
        self.org = self.github.get_organization(settings.github_org)
    
    async def get_repositories(self) -> List[RepoMetadata]:
        """Get all repositories from the organization."""
        logger.info(f"Fetching repositories from {self.settings.github_org}")
        
        repos = []
        try:
            for repo in self.org.get_repos():
                # Apply filters
                if self._should_skip_repo(repo):
                    continue
                
                metadata = self._extract_repo_metadata(repo)
                repos.append(metadata)
                
            logger.info(f"Found {len(repos)} repositories to process")
            return repos
            
        except GithubException as e:
            logger.error(f"Error fetching repositories: {e}")
            raise
    
    def _should_skip_repo(self, repo: Repository.Repository) -> bool:
        """Check if repository should be skipped based on filters."""
        # Skip archived repos by default
        if repo.archived:
            return True
        
        # Check star count
        if repo.stargazers_count < self.settings.min_stars:
            return True
        
        # Check include/exclude lists
        if self.settings.include_repos:
            return repo.name not in self.settings.include_repos
        
        if repo.name in self.settings.exclude_repos:
            return True
        
        return False
    
    def _extract_repo_metadata(self, repo: Repository.Repository) -> RepoMetadata:
        """Extract metadata from GitHub repository."""
        # Get languages
        languages = {}
        try:
            languages = repo.get_languages()
        except GithubException:
            logger.warning(f"Could not fetch languages for {repo.name}")
        
        # Get topics
        topics = []
        try:
            topics = repo.get_topics()
        except GithubException:
            logger.warning(f"Could not fetch topics for {repo.name}")
        
        return RepoMetadata(
            name=repo.name,
            full_name=repo.full_name,
            description=repo.description,
            language=repo.language,
            languages=languages,
            stars=repo.stargazers_count,
            forks=repo.forks_count,
            topics=topics,
            default_branch=repo.default_branch,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            size=repo.size,
            archived=repo.archived,
            private=repo.private
        )
    
    async def get_repository_files(self, repo_name: str, max_files: int = 100) -> List[FileContent]:
        """Get key files from repository for analysis."""
        logger.info(f"Fetching files for repository: {repo_name}")
        
        try:
            repo = self.github.get_repo(f"{self.settings.github_org}/{repo_name}")
            files = []
            
            # Priority files to always include
            priority_files = [
                "README.md", "readme.md", "README.rst", "README.txt",
                "package.json", "package-lock.json", "yarn.lock",
                "requirements.txt", "requirements-dev.txt", "Pipfile", "pyproject.toml",
                "Cargo.toml", "Cargo.lock",
                "go.mod", "go.sum",
                "pom.xml", "build.gradle", "build.gradle.kts",
                "composer.json", "composer.lock",
                "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
                ".env.example", ".env.template",
                "tsconfig.json", "jsconfig.json",
                ".eslintrc.js", ".eslintrc.json", ".prettierrc",
                "jest.config.js", "vitest.config.js", "cypress.json",
                ".github/workflows/ci.yml", ".github/workflows/deploy.yml",
                "src/main.py", "src/index.js", "src/App.js", "main.go",
                "lib/index.js", "index.html"
            ]
            
            # Get priority files
            for file_path in priority_files:
                file_content = await self._get_file_content(repo, file_path)
                if file_content:
                    files.append(file_content)
            
            # Get directory structure
            try:
                contents = repo.get_contents("")
                await self._explore_directory(repo, contents, files, max_files - len(files))
            except GithubException as e:
                logger.warning(f"Could not get directory structure for {repo_name}: {e}")
            
            logger.info(f"Retrieved {len(files)} files from {repo_name}")
            return files[:max_files]
            
        except GithubException as e:
            logger.error(f"Error fetching files for {repo_name}: {e}")
            return []
    
    async def _get_file_content(self, repo: Repository.Repository, file_path: str) -> Optional[FileContent]:
        """Get content of a specific file."""
        try:
            content_file = repo.get_contents(file_path)
            
            if isinstance(content_file, list):
                return None  # It's a directory
            
            # Decode content
            content = ""
            encoding = content_file.encoding
            
            if encoding == "base64":
                try:
                    content = base64.b64decode(content_file.content).decode('utf-8')
                except UnicodeDecodeError:
                    logger.warning(f"Could not decode {file_path} as UTF-8")
                    return None
            else:
                content = content_file.content
            
            return FileContent(
                path=file_path,
                content=content,
                size=content_file.size,
                type="file",
                encoding=encoding
            )
            
        except GithubException:
            return None
    
    async def _explore_directory(self, repo: Repository.Repository, contents: List[ContentFile], 
                                files: List[FileContent], remaining_files: int, 
                                current_path: str = "", max_depth: int = 3) -> None:
        """Recursively explore directory structure."""
        if remaining_files <= 0 or max_depth <= 0:
            return
        
        for content in contents:
            if len(files) >= remaining_files:
                break
            
            full_path = f"{current_path}/{content.name}" if current_path else content.name
            
            if content.type == "file":
                # Skip large files and certain extensions
                if content.size > 100000:  # 100KB limit
                    continue
                
                if any(full_path.endswith(ext) for ext in [
                    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
                    '.pdf', '.zip', '.tar.gz', '.exe', '.dll',
                    '.min.js', '.min.css', '.map'
                ]):
                    continue
                
                file_content = await self._get_file_content(repo, full_path)
                if file_content:
                    files.append(file_content)
            
            elif content.type == "dir" and max_depth > 1:
                # Explore subdirectories
                if content.name not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv']:
                    try:
                        subcontents = repo.get_contents(full_path)
                        await self._explore_directory(repo, subcontents, files, 
                                                    remaining_files - len(files), 
                                                    full_path, max_depth - 1)
                    except GithubException:
                        continue
    
    async def get_repository_stats(self, repo_name: str) -> Dict[str, Any]:
        """Get repository statistics and metrics."""
        try:
            repo = self.github.get_repo(f"{self.settings.github_org}/{repo_name}")
            
            stats = {
                "commits_count": repo.get_commits().totalCount,
                "contributors_count": repo.get_contributors().totalCount,
                "issues_count": repo.get_issues(state="all").totalCount,
                "pulls_count": repo.get_pulls(state="all").totalCount,
                "releases_count": repo.get_releases().totalCount,
                "branches_count": repo.get_branches().totalCount,
                "has_wiki": repo.has_wiki,
                "has_pages": repo.has_pages,
                "has_projects": repo.has_projects,
                "has_issues": repo.has_issues,
                "license": repo.license.name if repo.license else None
            }
            
            return stats
            
        except GithubException as e:
            logger.warning(f"Could not get stats for {repo_name}: {e}")
            return {}