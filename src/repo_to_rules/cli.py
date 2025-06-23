"""Command-line interface for repo-to-rules automation."""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
import sys

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

from .config import Settings
from .langgraph_workflow import RepositoryWorkflow
from .github_client import GitHubClient

app = typer.Typer(name="repo-to-rules", help="Generate Claude Code and Cursor rules from GitHub repositories")
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


@app.command()
def list_repos(
    org: Optional[str] = typer.Option(None, "--org", "-o", help="GitHub organization name"),
    min_stars: int = typer.Option(0, "--min-stars", help="Minimum stars filter"),
    include_archived: bool = typer.Option(False, "--include-archived", help="Include archived repositories")
) -> None:
    """List repositories from the GitHub organization."""
    try:
        settings = Settings()
        if org:
            settings.github_org = org
        if min_stars:
            settings.min_stars = min_stars
        
        asyncio.run(_list_repositories(settings, include_archived))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def process(
    repos: Optional[List[str]] = typer.Argument(None, help="Specific repositories to process"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="GitHub organization name"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-d", help="Output directory"),
    max_concurrent: int = typer.Option(3, "--max-concurrent", "-c", help="Maximum concurrent repositories"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be processed without doing it")
) -> None:
    """Process repositories and generate rules."""
    try:
        settings = Settings()
        
        # Override settings with CLI arguments
        if org:
            settings.github_org = org
        if output_dir:
            settings.output_dir = output_dir
        if max_concurrent:
            settings.max_concurrent_repos = max_concurrent
        if overwrite:
            settings.overwrite_existing = overwrite
        if repos:
            settings.include_repos = repos
        
        asyncio.run(_process_repositories(settings, dry_run))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def validate(
    repo_name: str = typer.Argument(..., help="Repository name to validate"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="GitHub organization name")
) -> None:
    """Validate generated rules for a specific repository."""
    try:
        settings = Settings()
        if org:
            settings.github_org = org
        
        asyncio.run(_validate_repository(settings, repo_name))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration key"),
    value: Optional[str] = typer.Option(None, "--value", help="Configuration value")
) -> None:
    """Manage configuration settings."""
    try:
        if show:
            _show_config()
        elif set_key and value:
            _set_config(set_key, value)
        else:
            console.print("[yellow]Use --show to display config or --set with --value to modify[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


async def _list_repositories(settings: Settings, include_archived: bool) -> None:
    """List repositories from the organization."""
    console.print(f"[bold blue]Fetching repositories from {settings.github_org}...[/bold blue]")
    
    github_client = GitHubClient(settings)
    
    with console.status("[bold green]Loading repositories..."):
        repos = await github_client.get_repositories()
    
    if not include_archived:
        repos = [repo for repo in repos if not repo.archived]
    
    # Create table
    table = Table(title=f"Repositories in {settings.github_org}")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Language", style="magenta")
    table.add_column("Stars", justify="right", style="green")
    table.add_column("Description", style="white")
    table.add_column("Updated", style="blue")
    
    for repo in sorted(repos, key=lambda r: r.stars, reverse=True):
        table.add_row(
            repo.name,
            repo.language or "Unknown",
            str(repo.stars),
            (repo.description or "No description")[:50] + ("..." if len(repo.description or "") > 50 else ""),
            repo.updated_at.strftime("%Y-%m-%d") if repo.updated_at else "Unknown"
        )
    
    console.print(table)
    console.print(f"\n[bold]Total repositories: {len(repos)}[/bold]")


async def _process_repositories(settings: Settings, dry_run: bool) -> None:
    """Process repositories and generate rules."""
    console.print(f"[bold blue]Processing repositories from {settings.github_org}...[/bold blue]")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be generated[/yellow]")
    
    # Initialize workflow
    workflow = RepositoryWorkflow(settings)
    github_client = GitHubClient(settings)
    
    # Get repositories to process
    with console.status("[bold green]Fetching repository list..."):
        all_repos = await github_client.get_repositories()
    
    repos_to_process = []
    if settings.include_repos:
        repos_to_process = [repo for repo in all_repos if repo.name in settings.include_repos]
    else:
        repos_to_process = all_repos
    
    if not repos_to_process:
        console.print("[yellow]No repositories to process[/yellow]")
        return
    
    console.print(f"[bold]Processing {len(repos_to_process)} repositories...[/bold]")
    
    # Process repositories with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        main_task = progress.add_task("Processing repositories", total=len(repos_to_process))
        
        results = []
        semaphore = asyncio.Semaphore(settings.max_concurrent_repos)
        
        async def process_single_repo(repo):
            async with semaphore:
                progress.update(main_task, description=f"Processing {repo.name}")
                
                if dry_run:
                    # Simulate processing
                    await asyncio.sleep(1)
                    result = {"name": repo.name, "status": "success", "error": None}
                else:
                    try:
                        result_state = await workflow.process_repository(repo.name)
                        result = {
                            "name": repo.name,
                            "status": "success" if result_state.completed else "failed",
                            "error": result_state.error
                        }
                    except Exception as e:
                        result = {"name": repo.name, "status": "failed", "error": str(e)}
                
                progress.advance(main_task)
                return result
        
        # Process repositories concurrently
        tasks = [process_single_repo(repo) for repo in repos_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Display results
    _display_results(results, dry_run)


async def _validate_repository(settings: Settings, repo_name: str) -> None:
    """Validate generated rules for a repository."""
    console.print(f"[bold blue]Validating rules for {repo_name}...[/bold blue]")
    
    output_dir = Path(settings.output_dir) / repo_name
    
    if not output_dir.exists():
        console.print(f"[red]No output found for {repo_name} in {output_dir}[/red]")
        return
    
    # Check required files
    required_files = {
        "Claude Code": [
            ".claude/CLAUDE.md",
            ".claude/project-context.md",
            ".claude/coding-conventions.md",
            ".claude/testing-guide.md",
            ".claude/architecture.md",
            ".claude/.mcp.json"
        ],
        "Cursor": [
            ".cursor/.cursorrules",
            ".cursor/cursor-context.md",
            ".cursor/snippets.json",
            ".cursor/tasks.json",
            ".cursor/.mcp.json"
        ]
    }
    
    table = Table(title=f"Validation Results for {repo_name}")
    table.add_column("Tool", style="cyan")
    table.add_column("File", style="white")
    table.add_column("Status", style="green")
    table.add_column("Size", justify="right", style="blue")
    
    for tool, files in required_files.items():
        for file_path in files:
            full_path = output_dir / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                status = "✅ Exists"
                size_str = f"{size} bytes"
            else:
                status = "❌ Missing"
                size_str = "-"
            
            table.add_row(tool, file_path, status, size_str)
    
    console.print(table)
    
    # Check for slash commands
    commands_dir = output_dir / ".claude" / "commands"
    if commands_dir.exists():
        commands = list(commands_dir.iterdir())
        console.print(f"\n[bold green]Slash commands found: {len(commands)}[/bold green]")
        for cmd in commands:
            console.print(f"  - /{cmd.name}")


def _display_results(results: List, dry_run: bool) -> None:
    """Display processing results."""
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    failed_count = len(results) - success_count
    
    # Summary panel
    summary_text = f"[green]✅ Successful: {success_count}[/green]\n"
    summary_text += f"[red]❌ Failed: {failed_count}[/red]"
    
    if dry_run:
        summary_text += "\n[yellow]⚠️  DRY RUN - No files generated[/yellow]"
    
    console.print(Panel(summary_text, title="Processing Summary", border_style="blue"))
    
    # Failed repositories
    if failed_count > 0:
        console.print("\n[bold red]Failed Repositories:[/bold red]")
        for result in results:
            if isinstance(result, dict) and result.get("status") == "failed":
                console.print(f"  • {result['name']}: {result.get('error', 'Unknown error')}")


def _show_config() -> None:
    """Show current configuration."""
    try:
        settings = Settings()
        
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        config_items = [
            ("GitHub Organization", settings.github_org),
            ("Output Directory", settings.output_dir),
            ("Max Concurrent Repos", str(settings.max_concurrent_repos)),
            ("Rate Limit Delay", f"{settings.rate_limit_delay}s"),
            ("Min Stars", str(settings.min_stars)),
            ("Overwrite Existing", str(settings.overwrite_existing)),
        ]
        
        for key, value in config_items:
            table.add_row(key, value)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")


def _set_config(key: str, value: str) -> None:
    """Set configuration value."""
    console.print(f"[yellow]Setting {key} = {value}[/yellow]")
    console.print("[blue]Note: Configuration changes require environment variables or .env file updates[/blue]")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()