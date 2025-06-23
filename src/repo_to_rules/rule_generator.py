"""Rule generator for Claude Code and Cursor formats."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from jinja2 import Environment, FileSystemLoader, Template
from anthropic import AsyncAnthropic

from .models import (
    RepositoryContext, ClaudeRules, CursorRules, 
    GeneratedOutput
)
from .config import Settings
from .mcp_generator import MCPGenerator

logger = logging.getLogger(__name__)


class RuleGenerator:
    """Generate rules and configurations for Claude Code and Cursor."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.output_dir = Path(settings.output_dir)
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.mcp_generator = MCPGenerator()
        
        # Setup Jinja2 environment for templates
        self.template_env = Environment(
            loader=FileSystemLoader(Path(__file__).parent.parent.parent / "templates"),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    async def generate_output(self, context: RepositoryContext) -> GeneratedOutput:
        """Generate complete output for a repository."""
        logger.info(f"Generating output for {context.metadata.name}")
        
        try:
            # Generate rules in parallel
            claude_task = self._generate_claude_rules(context)
            cursor_task = self._generate_cursor_rules(context)
            
            claude_rules, cursor_rules = await asyncio.gather(claude_task, cursor_task)
            
            output = GeneratedOutput(
                repo_name=context.metadata.name,
                claude_rules=claude_rules,
                cursor_rules=cursor_rules,
                context_summary=context
            )
            
            logger.info(f"Successfully generated output for {context.metadata.name}")
            return output
            
        except Exception as e:
            logger.error(f"Error generating output for {context.metadata.name}: {e}")
            raise
    
    async def _generate_claude_rules(self, context: RepositoryContext) -> ClaudeRules:
        """Generate Claude Code specific rules and configurations."""
        logger.info(f"Generating Claude rules for {context.metadata.name}")
        
        # Generate main CLAUDE.md content
        main_rules = await self._generate_claude_main_rules(context)
        
        # Generate modular rule files
        project_context = await self._generate_claude_project_context(context)
        coding_conventions = await self._generate_claude_coding_conventions(context)
        testing_guide = await self._generate_claude_testing_guide(context)
        architecture = await self._generate_claude_architecture(context)
        
        # Generate slash commands
        slash_commands = await self._generate_claude_slash_commands(context)
        
        # Generate MCP configuration
        mcp_config = self.mcp_generator.generate_claude_mcp_config(context)
        
        return ClaudeRules(
            main_rules=main_rules,
            project_context=project_context,
            coding_conventions=coding_conventions,
            testing_guide=testing_guide,
            architecture=architecture,
            slash_commands=slash_commands,
            mcp_config=mcp_config
        )
    
    async def _generate_cursor_rules(self, context: RepositoryContext) -> CursorRules:
        """Generate Cursor specific rules and configurations."""
        logger.info(f"Generating Cursor rules for {context.metadata.name}")
        
        # Generate .cursorrules content
        cursorrules = await self._generate_cursor_rules_content(context)
        
        # Generate context file
        cursor_context = await self._generate_cursor_context(context)
        
        # Generate snippets
        snippets = await self._generate_cursor_snippets(context)
        
        # Generate tasks
        tasks = await self._generate_cursor_tasks(context)
        
        # Generate MCP configuration
        mcp_config = self.mcp_generator.generate_cursor_mcp_config(context)
        
        return CursorRules(
            cursorrules=cursorrules,
            context=cursor_context,
            snippets=snippets,
            tasks=tasks,
            mcp_config=mcp_config
        )
    
    async def _generate_claude_main_rules(self, context: RepositoryContext) -> str:
        """Generate main CLAUDE.md rules file."""
        prompt = f"""
        Generate a comprehensive CLAUDE.md file for Claude Code for this project:
        
        Project: {context.metadata.name}
        Description: {context.metadata.description}
        Language: {context.metadata.language}
        Tech Stack: {', '.join(context.structure.tech_stack)}
        
        Key Information:
        - Main directories: {', '.join(context.structure.directories)}
        - Build tools: {', '.join(context.build.build_tools)}
        - Testing frameworks: {', '.join(context.testing.frameworks)}
        - Dependencies: {list(context.dependencies.runtime.keys())[:10]}
        
        Create a CLAUDE.md that includes:
        1. Project overview and purpose
        2. Development setup instructions
        3. Code style and conventions
        4. Project structure explanation
        5. Common workflows and commands
        6. Testing approach
        7. Deployment information
        8. Troubleshooting guide
        
        Format it as a proper markdown file optimized for Claude Code usage.
        Make it comprehensive but concise, focusing on actionable information.
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to generate Claude main rules: {e}")
            return self._generate_fallback_claude_rules(context)
    
    async def _generate_claude_project_context(self, context: RepositoryContext) -> str:
        """Generate project context file for Claude."""
        prompt = f"""
        Generate a project-context.md file for Claude Code that provides deep context about this project:
        
        Project: {context.metadata.name}
        Description: {context.metadata.description}
        
        Architecture: {', '.join(context.code_patterns.architectural_patterns)}
        Services: Databases: {', '.join(context.services.databases)}, Cloud: {', '.join(context.services.cloud_services)}
        
        Include:
        1. Business domain and purpose
        2. Key concepts and terminology
        3. Data models and relationships
        4. External integrations
        5. Security considerations
        6. Performance characteristics
        
        Make it detailed and informative for AI assistants to understand the project deeply.
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to generate Claude project context: {e}")
            return f"# Project Context\n\n## {context.metadata.name}\n\n{context.metadata.description or 'No description available'}"
    
    async def _generate_claude_coding_conventions(self, context: RepositoryContext) -> str:
        """Generate coding conventions file for Claude."""
        conventions = {
            'language': context.metadata.language,
            'naming': context.code_patterns.naming_conventions,
            'formatting': context.code_patterns.formatting_config,
            'linting': context.code_patterns.linting_rules
        }
        
        prompt = f"""
        Generate a coding-conventions.md file for this {context.metadata.language} project:
        
        Current conventions detected:
        {json.dumps(conventions, indent=2)}
        
        Include:
        1. Naming conventions for variables, functions, classes, files
        2. Code formatting standards
        3. Linting rules and enforcement
        4. Documentation standards
        5. Error handling patterns
        6. Import/export conventions
        7. Performance guidelines
        
        Make it actionable and specific to this project's patterns.
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to generate Claude coding conventions: {e}")
            return f"# Coding Conventions\n\n## {context.metadata.language} Project Standards\n\nProject uses {context.metadata.language} with standard conventions."
    
    async def _generate_claude_testing_guide(self, context: RepositoryContext) -> str:
        """Generate testing guide for Claude."""
        prompt = f"""
        Generate a testing-guide.md file for this project:
        
        Testing setup:
        - Frameworks: {', '.join(context.testing.frameworks)}
        - Test directories: {', '.join(context.testing.test_directories)}
        - Mock frameworks: {', '.join(context.testing.mock_frameworks)}
        
        Include:
        1. Testing strategy (unit, integration, e2e)
        2. How to run tests
        3. Writing new tests
        4. Test structure and organization
        5. Mocking patterns
        6. Coverage requirements
        7. Performance testing
        8. Common testing commands
        
        Make it practical and actionable for developers.
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to generate Claude testing guide: {e}")
            return f"# Testing Guide\n\n## Frameworks\n{', '.join(context.testing.frameworks)}\n\n## Test Directories\n{', '.join(context.testing.test_directories)}"
    
    async def _generate_claude_architecture(self, context: RepositoryContext) -> str:
        """Generate architecture documentation for Claude."""
        prompt = f"""
        Generate an architecture.md file for this project:
        
        Project structure:
        - Main directories: {', '.join(context.structure.directories)}
        - Tech stack: {', '.join(context.structure.tech_stack)}
        - Architectural patterns: {', '.join(context.code_patterns.architectural_patterns)}
        
        Include:
        1. Overall architecture overview
        2. Component relationships
        3. Data flow
        4. Key design decisions
        5. Scalability considerations
        6. Security architecture
        7. Performance considerations
        8. Integration points
        
        Make it comprehensive for understanding the system design.
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to generate Claude architecture: {e}")
            return f"# Architecture\n\n## Overview\n{context.metadata.description}\n\n## Tech Stack\n{', '.join(context.structure.tech_stack)}"
    
    async def _generate_claude_slash_commands(self, context: RepositoryContext) -> Dict[str, str]:
        """Generate slash commands for Claude Code."""
        commands = {}
        
        # Build commands based on available scripts
        if context.build.scripts:
            if 'test' in context.build.scripts:
                commands['test'] = f"Run tests using: {context.build.scripts['test']}"
            if 'build' in context.build.scripts:
                commands['build'] = f"Build project using: {context.build.scripts['build']}"
            if 'dev' in context.build.scripts or 'start' in context.build.scripts:
                dev_cmd = context.build.scripts.get('dev', context.build.scripts.get('start'))
                commands['dev'] = f"Start development server using: {dev_cmd}"
            if 'lint' in context.build.scripts:
                commands['lint'] = f"Run linter using: {context.build.scripts['lint']}"
        
        # Add deployment command if CI/CD is configured
        if context.build.ci_cd_config:
            commands['deploy'] = "Deploy using the configured CI/CD pipeline"
        
        # Add setup command
        if 'npm' in context.structure.package_managers:
            commands['setup'] = "Set up project with: npm install"
        elif 'pip' in context.structure.package_managers:
            commands['setup'] = "Set up project with: pip install -r requirements.txt"
        elif 'poetry' in context.structure.package_managers:
            commands['setup'] = "Set up project with: poetry install"
        
        return commands
    
    async def _generate_cursor_rules_content(self, context: RepositoryContext) -> str:
        """Generate .cursorrules content."""
        prompt = f"""
        Generate a .cursorrules file for Cursor IDE for this project:
        
        Project: {context.metadata.name}
        Language: {context.metadata.language}
        Tech Stack: {', '.join(context.structure.tech_stack)}
        
        Key patterns:
        - Architectural patterns: {', '.join(context.code_patterns.architectural_patterns)}
        - Naming conventions: {json.dumps(context.code_patterns.naming_conventions)}
        
        Create a .cursorrules file that includes:
        1. Code style preferences
        2. Language-specific rules
        3. Framework-specific guidelines
        4. File organization rules
        5. Import/export preferences
        6. Error handling patterns
        7. Performance guidelines
        8. Security considerations
        
        Format it according to Cursor's .cursorrules format and syntax.
        Make it comprehensive but focused on this project's specific needs.
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to generate Cursor rules: {e}")
            return self._generate_fallback_cursor_rules(context)
    
    async def _generate_cursor_context(self, context: RepositoryContext) -> str:
        """Generate Cursor context file."""
        return f"""# {context.metadata.name} - Cursor Context

## Project Overview
{context.metadata.description or 'No description available'}

## Tech Stack
{', '.join(context.structure.tech_stack)}

## Key Directories
{chr(10).join(f'- {dir}' for dir in context.structure.directories)}

## Dependencies
{chr(10).join(f'- {dep}: {version}' for dep, version in list(context.dependencies.runtime.items())[:10])}

## Build Tools
{', '.join(context.build.build_tools)}

## Testing
- Frameworks: {', '.join(context.testing.frameworks)}
- Test Directories: {', '.join(context.testing.test_directories)}
"""
    
    async def _generate_cursor_snippets(self, context: RepositoryContext) -> Dict[str, Any]:
        """Generate code snippets for Cursor."""
        snippets = {}
        
        # Generate language-specific snippets
        if context.metadata.language == 'JavaScript' or 'javascript' in context.structure.tech_stack:
            snippets.update({
                "component": {
                    "prefix": "comp",
                    "body": ["const ${1:ComponentName} = () => {", "  return (", "    <div>", "      ${2:content}", "    </div>", "  );", "};", "", "export default ${1:ComponentName};"],
                    "description": "React functional component"
                },
                "test": {
                    "prefix": "test",
                    "body": ["describe('${1:ComponentName}', () => {", "  it('${2:should}', () => {", "    ${3:// test code}", "  });", "});"],
                    "description": "Test block"
                }
            })
        
        elif context.metadata.language == 'Python' or 'python' in context.structure.tech_stack:
            snippets.update({
                "class": {
                    "prefix": "class",
                    "body": ["class ${1:ClassName}:", "    def __init__(self):", "        ${2:pass}", "", "    def ${3:method_name}(self):", "        ${4:pass}"],
                    "description": "Python class"
                },
                "test": {
                    "prefix": "test",
                    "body": ["def test_${1:function_name}():", "    ${2:# test code}", "    assert ${3:condition}"],
                    "description": "Python test function"
                }
            })
        
        return snippets
    
    async def _generate_cursor_tasks(self, context: RepositoryContext) -> Dict[str, Any]:
        """Generate tasks configuration for Cursor."""
        tasks = {"version": "2.0.0", "tasks": []}
        
        # Add tasks based on available scripts
        if context.build.scripts:
            for script_name, script_cmd in context.build.scripts.items():
                tasks["tasks"].append({
                    "label": f"Run {script_name}",
                    "type": "shell",
                    "command": script_cmd,
                    "group": "build" if script_name == "build" else "test" if script_name == "test" else "other"
                })
        
        return tasks
    
    async def save_output(self, repo_name: str, output: GeneratedOutput) -> None:
        """Save generated output to files."""
        logger.info(f"Saving output for {repo_name}")
        
        repo_dir = self.output_dir / repo_name
        claude_dir = repo_dir / ".claude"
        cursor_dir = repo_dir / ".cursor"
        commands_dir = claude_dir / "commands"
        
        # Create directories
        for dir_path in [repo_dir, claude_dir, cursor_dir, commands_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save Claude Code files
            await self._save_claude_files(claude_dir, commands_dir, output.claude_rules)
            
            # Save Cursor files
            await self._save_cursor_files(cursor_dir, output.cursor_rules)
            
            # Save context summary
            context_file = repo_dir / "context-summary.json"
            with open(context_file, 'w') as f:
                json.dump(output.context_summary.model_dump(), f, indent=2, default=str)
            
            logger.info(f"Successfully saved output for {repo_name}")
            
        except Exception as e:
            logger.error(f"Error saving output for {repo_name}: {e}")
            raise
    
    async def _save_claude_files(self, claude_dir: Path, commands_dir: Path, rules: ClaudeRules) -> None:
        """Save Claude Code specific files."""
        # Main CLAUDE.md
        with open(claude_dir / "CLAUDE.md", 'w') as f:
            f.write(rules.main_rules)
        
        # Modular rule files
        with open(claude_dir / "project-context.md", 'w') as f:
            f.write(rules.project_context)
        
        with open(claude_dir / "coding-conventions.md", 'w') as f:
            f.write(rules.coding_conventions)
        
        with open(claude_dir / "testing-guide.md", 'w') as f:
            f.write(rules.testing_guide)
        
        with open(claude_dir / "architecture.md", 'w') as f:
            f.write(rules.architecture)
        
        # Slash commands
        for cmd_name, cmd_content in rules.slash_commands.items():
            with open(commands_dir / cmd_name, 'w') as f:
                f.write(cmd_content)
        
        # MCP configuration
        with open(claude_dir / ".mcp.json", 'w') as f:
            json.dump(rules.mcp_config, f, indent=2)
    
    async def _save_cursor_files(self, cursor_dir: Path, rules: CursorRules) -> None:
        """Save Cursor specific files."""
        # .cursorrules
        with open(cursor_dir / ".cursorrules", 'w') as f:
            f.write(rules.cursorrules)
        
        # Context file
        with open(cursor_dir / "cursor-context.md", 'w') as f:
            f.write(rules.context)
        
        # Snippets
        with open(cursor_dir / "snippets.json", 'w') as f:
            json.dump(rules.snippets, f, indent=2)
        
        # Tasks
        with open(cursor_dir / "tasks.json", 'w') as f:
            json.dump(rules.tasks, f, indent=2)
        
        # MCP configuration
        with open(cursor_dir / ".mcp.json", 'w') as f:
            json.dump(rules.mcp_config, f, indent=2)
    
    def _generate_fallback_claude_rules(self, context: RepositoryContext) -> str:
        """Generate fallback Claude rules if LLM generation fails."""
        return f"""# {context.metadata.name}

## Project Overview
{context.metadata.description or 'No description available'}

## Tech Stack
{', '.join(context.structure.tech_stack)}

## Development Setup
1. Clone the repository
2. Install dependencies
3. Run the development server

## Project Structure
{chr(10).join(f'- {dir}/' for dir in context.structure.directories)}

## Available Scripts
{chr(10).join(f'- `{script}`: {cmd}' for script, cmd in context.build.scripts.items())}

## Testing
- Frameworks: {', '.join(context.testing.frameworks)}
- Test directories: {', '.join(context.testing.test_directories)}
"""
    
    def _generate_fallback_cursor_rules(self, context: RepositoryContext) -> str:
        """Generate fallback Cursor rules if LLM generation fails."""
        return f"""# {context.metadata.name} - Cursor Rules

## Language: {context.metadata.language}

## Code Style
- Follow standard {context.metadata.language} conventions
- Use consistent naming patterns
- Maintain clean code structure

## Project Structure
- Main directories: {', '.join(context.structure.directories)}
- Follow existing patterns

## Dependencies
- Runtime: {', '.join(list(context.dependencies.runtime.keys())[:5])}
- Dev: {', '.join(list(context.dependencies.dev.keys())[:5])}

## Testing
- Use {', '.join(context.testing.frameworks)} for testing
- Follow existing test patterns
"""