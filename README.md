# Repo to Rules Automation

An end-to-end automation system that analyzes GitHub repositories and generates comprehensive rule directories for both Claude Code and Cursor, leveraging Claude Sonnet 4, LangGraph, and the GitHub API.

## Features

- 🔍 **Repository Analysis**: Deep analysis of project structure, dependencies, and patterns
- 🤖 **AI-Powered Processing**: Uses Claude Sonnet 4 for intelligent context extraction
- 📋 **Multi-Platform Rules**: Generates optimized rules for both Claude Code and Cursor
- 🔧 **MCP Integration**: Automatic MCP server configuration generation
- ⚡ **Slash Commands**: Custom slash commands for Claude Code
- 🎯 **Template System**: Jinja2-based templates for consistent output
- 🔄 **LangGraph Workflow**: Robust processing pipeline with error handling
- 📊 **Rich CLI**: Beautiful command-line interface with progress tracking

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd repo-to-rules
```

2. **Install dependencies:**
```bash
pip install poetry
poetry install
```

3. **Set up environment variables:**
```bash
cp .env.template .env
# Edit .env with your API keys
```

Required environment variables:
- `GITHUB_TOKEN`: GitHub personal access token
- `ANTHROPIC_API_KEY`: Claude API key
- `GITHUB_ORG`: Target GitHub organization (default: alldigitalrewards)

## Usage

### List Repositories
```bash
repo-to-rules list-repos --org alldigitalrewards --min-stars 5
```

### Process All Repositories
```bash
repo-to-rules process --max-concurrent 3 --output ./output
```

### Process Specific Repositories
```bash
repo-to-rules process repo1 repo2 repo3
```

### Validate Generated Rules
```bash
repo-to-rules validate repo-name
```

### Configuration Management
```bash
repo-to-rules config --show
```

## Output Structure

For each repository, the system generates:

```
output/
├── repo-name/
│   ├── .claude/
│   │   ├── CLAUDE.md              # Main rules file
│   │   ├── project-context.md     # Project context
│   │   ├── coding-conventions.md  # Code style rules
│   │   ├── testing-guide.md       # Testing guidelines
│   │   ├── architecture.md        # Architecture docs
│   │   ├── commands/               # Slash commands
│   │   │   ├── test               # /test command
│   │   │   ├── build              # /build command
│   │   │   ├── dev                # /dev command
│   │   │   ├── lint               # /lint command
│   │   │   └── setup              # /setup command
│   │   └── .mcp.json              # MCP configuration
│   ├── .cursor/
│   │   ├── .cursorrules           # Cursor rules
│   │   ├── cursor-context.md      # Project context
│   │   ├── snippets.json          # Code snippets
│   │   ├── tasks.json             # Task definitions
│   │   └── .mcp.json              # MCP configuration
│   └── context-summary.json       # Complete analysis
```

## Claude Code Integration

### Using Generated Rules
1. Copy the `.claude` directory to your project root
2. The `CLAUDE.md` file will be automatically recognized by Claude Code
3. Use slash commands for quick actions:
   - `/test` - Run project tests
   - `/build` - Build the project
   - `/dev` - Start development server
   - `/lint` - Run linters
   - `/setup` - Set up development environment

### MCP Servers
The generated `.mcp.json` includes relevant MCP servers based on your project:
- File system access
- Git operations
- Database connections (PostgreSQL, SQLite)
- Language-specific tools
- Cloud service integrations

## Cursor Integration

### Using Generated Rules
1. Copy the `.cursor` directory to your project root
2. Cursor will automatically use the `.cursorrules` file
3. Code snippets and tasks will be available in the IDE

### Features
- Project-specific coding conventions
- Custom code snippets
- Pre-configured tasks
- MCP server integration

## Architecture

The system uses a LangGraph workflow with the following nodes:

1. **GitHub Integration**: Fetches repository metadata and files
2. **Context Extraction**: Analyzes project structure and dependencies
3. **LLM Processing**: Enhances context using Claude Sonnet 4
4. **Rule Generation**: Creates platform-specific rules and configurations
5. **Output Generation**: Saves files using Jinja2 templates

## Supported Technologies

- **Languages**: JavaScript, TypeScript, Python, Java, Go, Rust, PHP, C#
- **Frameworks**: React, Next.js, Vue, Django, FastAPI, Express, Spring
- **Build Tools**: npm, Yarn, pnpm, Poetry, Maven, Gradle, Cargo
- **Testing**: Jest, Vitest, Cypress, Playwright, pytest, PHPUnit
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis, SQLite
- **Cloud**: AWS, GCP, Azure
- **DevOps**: Docker, Kubernetes, GitHub Actions, GitLab CI

## Configuration

The system can be configured via environment variables or the `.env` file:

```env
# GitHub Settings
GITHUB_TOKEN=your_token_here
GITHUB_ORG=alldigitalrewards

# Claude Settings
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Processing Settings
MAX_CONCURRENT_REPOS=5
RATE_LIMIT_DELAY=1.0
OUTPUT_DIR=output
OVERWRITE_EXISTING=false

# Repository Filtering
MIN_STARS=0
# INCLUDE_REPOS=repo1,repo2,repo3
# EXCLUDE_REPOS=archived-repo,test-repo
```

## Development

### Running Tests
```bash
poetry run pytest
```

### Code Quality
```bash
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy .
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## API Rate Limits

The system respects GitHub API rate limits:
- Uses authenticated requests for higher limits
- Implements exponential backoff
- Configurable delay between requests
- Concurrent processing with limits

## Error Handling

- Graceful handling of API failures
- Retry logic for transient errors
- Detailed error reporting
- Partial success handling

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/your-org/repo-to-rules/issues) page.