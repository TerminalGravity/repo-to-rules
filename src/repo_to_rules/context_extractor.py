"""Context extraction from repository files and metadata."""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

from .models import (
    RepoMetadata, FileContent, ProjectStructure, Dependencies, 
    CodePatterns, TestingInfo, BuildInfo, ServicesInfo, RepositoryContext
)

logger = logging.getLogger(__name__)


class ContextExtractor:
    """Extract structured context from repository data."""
    
    def __init__(self):
        self.tech_stack_patterns = {
            'javascript': ['.js', '.jsx', '.ts', '.tsx', 'package.json'],
            'python': ['.py', 'requirements.txt', 'pyproject.toml', 'setup.py'],
            'java': ['.java', 'pom.xml', 'build.gradle'],
            'csharp': ['.cs', '.csproj', '.sln'],
            'go': ['.go', 'go.mod', 'go.sum'],
            'rust': ['.rs', 'Cargo.toml', 'Cargo.lock'],
            'php': ['.php', 'composer.json', 'composer.lock'],
            'ruby': ['.rb', 'Gemfile', 'Gemfile.lock'],
            'swift': ['.swift', 'Package.swift'],
            'kotlin': ['.kt', '.kts', 'build.gradle.kts'],
            'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'terraform': ['.tf', '.tfvars', 'terraform.tfvars'],
            'kubernetes': ['.yaml', '.yml', 'kustomization.yaml']
        }
        
        self.build_tool_patterns = {
            'npm': ['package.json', 'package-lock.json'],
            'yarn': ['yarn.lock', '.yarnrc'],
            'pnpm': ['pnpm-lock.yaml', '.pnpmrc'],
            'webpack': ['webpack.config.js', 'webpack.config.ts'],
            'vite': ['vite.config.js', 'vite.config.ts'],
            'rollup': ['rollup.config.js', 'rollup.config.ts'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle', 'gradle.properties'],
            'cargo': ['Cargo.toml'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml'],
            'pipenv': ['Pipfile'],
            'composer': ['composer.json'],
            'bundler': ['Gemfile'],
            'make': ['Makefile', 'makefile'],
            'cmake': ['CMakeLists.txt'],
            'bazel': ['BUILD', 'WORKSPACE']
        }
        
        self.test_framework_patterns = {
            'jest': ['jest.config.js', 'jest.config.ts', 'jest.config.json'],
            'vitest': ['vitest.config.js', 'vitest.config.ts'],
            'mocha': ['mocha.opts', '.mocharc.json'],
            'cypress': ['cypress.json', 'cypress.config.js'],
            'playwright': ['playwright.config.js', 'playwright.config.ts'],
            'pytest': ['pytest.ini', 'setup.cfg', 'pyproject.toml'],
            'unittest': ['test_*.py', '*_test.py'],
            'phpunit': ['phpunit.xml', 'phpunit.xml.dist'],
            'rspec': ['.rspec', 'spec_helper.rb'],
            'junit': ['junit.xml', 'TestCase.java'],
            'go-test': ['*_test.go'],
            'cargo-test': ['Cargo.toml']
        }
    
    def extract_context(self, metadata: RepoMetadata, files: List[FileContent], 
                       stats: Dict[str, Any]) -> RepositoryContext:
        """Extract complete repository context."""
        logger.info(f"Extracting context for {metadata.name}")
        
        # Extract different aspects
        structure = self._extract_project_structure(files)
        dependencies = self._extract_dependencies(files)
        code_patterns = self._extract_code_patterns(files)
        testing = self._extract_testing_info(files)
        build = self._extract_build_info(files)
        services = self._extract_services_info(files)
        
        # Get key files for LLM processing
        key_files = self._identify_key_files(files)
        
        return RepositoryContext(
            metadata=metadata,
            structure=structure,
            dependencies=dependencies,
            code_patterns=code_patterns,
            testing=testing,
            build=build,
            services=services,
            key_files=key_files
        )
    
    def _extract_project_structure(self, files: List[FileContent]) -> ProjectStructure:
        """Extract project structure information."""
        root_files = []
        directories = set()
        tech_stack = set()
        build_tools = set()
        testing_frameworks = set()
        package_managers = set()
        config_files = {}
        
        for file in files:
            path_parts = file.path.split('/')
            
            # Root files
            if len(path_parts) == 1:
                root_files.append(file.path)
            
            # Directories
            if len(path_parts) > 1:
                directories.add(path_parts[0])
            
            # Tech stack detection
            for tech, patterns in self.tech_stack_patterns.items():
                if any(file.path.endswith(pattern) or pattern in file.path for pattern in patterns):
                    tech_stack.add(tech)
            
            # Build tools
            for tool, patterns in self.build_tool_patterns.items():
                if any(file.path.endswith(pattern) or pattern in file.path for pattern in patterns):
                    build_tools.add(tool)
                    if tool in ['npm', 'yarn', 'pnpm']:
                        package_managers.add(tool)
                    elif tool in ['pip', 'poetry', 'pipenv']:
                        package_managers.add(tool)
                    elif tool in ['composer']:
                        package_managers.add(tool)
                    elif tool in ['bundler']:
                        package_managers.add(tool)
            
            # Testing frameworks
            for framework, patterns in self.test_framework_patterns.items():
                if any(file.path.endswith(pattern) or pattern in file.path for pattern in patterns):
                    testing_frameworks.add(framework)
            
            # Config files
            if any(file.path.endswith(ext) for ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']):
                config_files[file.path] = file.content[:500]  # First 500 chars
        
        return ProjectStructure(
            root_files=root_files,
            directories=list(directories),
            tech_stack=list(tech_stack),
            build_tools=list(build_tools),
            testing_frameworks=list(testing_frameworks),
            package_managers=list(package_managers),
            config_files=config_files
        )
    
    def _extract_dependencies(self, files: List[FileContent]) -> Dependencies:
        """Extract project dependencies."""
        runtime = {}
        dev = {}
        peer = {}
        optional = {}
        
        for file in files:
            if file.path == 'package.json':
                deps = self._parse_package_json_dependencies(file.content)
                runtime.update(deps.get('dependencies', {}))
                dev.update(deps.get('devDependencies', {}))
                peer.update(deps.get('peerDependencies', {}))
                optional.update(deps.get('optionalDependencies', {}))
            
            elif file.path == 'requirements.txt':
                deps = self._parse_requirements_txt(file.content)
                runtime.update(deps)
            
            elif file.path == 'pyproject.toml':
                deps = self._parse_pyproject_toml(file.content)
                runtime.update(deps.get('dependencies', {}))
                dev.update(deps.get('dev-dependencies', {}))
            
            elif file.path == 'Cargo.toml':
                deps = self._parse_cargo_toml(file.content)
                runtime.update(deps.get('dependencies', {}))
                dev.update(deps.get('dev-dependencies', {}))
            
            elif file.path == 'composer.json':
                deps = self._parse_composer_json(file.content)
                runtime.update(deps.get('require', {}))
                dev.update(deps.get('require-dev', {}))
        
        return Dependencies(
            runtime=runtime,
            dev=dev,
            peer=peer,
            optional=optional
        )
    
    def _extract_code_patterns(self, files: List[FileContent]) -> CodePatterns:
        """Extract code patterns and conventions."""
        style_guide = None
        linting_rules = {}
        formatting_config = {}
        common_patterns = []
        architectural_patterns = []
        naming_conventions = {}
        
        for file in files:
            # ESLint configuration
            if '.eslintrc' in file.path:
                try:
                    config = json.loads(file.content)
                    linting_rules['eslint'] = config
                except json.JSONDecodeError:
                    pass
            
            # Prettier configuration
            if '.prettierrc' in file.path:
                try:
                    config = json.loads(file.content)
                    formatting_config['prettier'] = config
                except json.JSONDecodeError:
                    pass
            
            # TypeScript configuration
            if 'tsconfig.json' in file.path:
                try:
                    config = json.loads(file.content)
                    linting_rules['typescript'] = config
                except json.JSONDecodeError:
                    pass
            
            # Detect architectural patterns
            if 'src' in file.path:
                if 'components' in file.path:
                    architectural_patterns.append('component-based')
                if 'services' in file.path:
                    architectural_patterns.append('service-layer')
                if 'models' in file.path:
                    architectural_patterns.append('model-layer')
                if 'controllers' in file.path:
                    architectural_patterns.append('mvc')
                if 'hooks' in file.path:
                    architectural_patterns.append('react-hooks')
                if 'store' in file.path or 'redux' in file.path:
                    architectural_patterns.append('state-management')
        
        return CodePatterns(
            style_guide=style_guide,
            linting_rules=linting_rules,
            formatting_config=formatting_config,
            common_patterns=list(set(common_patterns)),
            architectural_patterns=list(set(architectural_patterns)),
            naming_conventions=naming_conventions
        )
    
    def _extract_testing_info(self, files: List[FileContent]) -> TestingInfo:
        """Extract testing information."""
        frameworks = set()
        test_directories = set()
        coverage_config = None
        test_patterns = []
        mock_frameworks = set()
        
        for file in files:
            # Test directories
            if any(test_dir in file.path for test_dir in ['test', 'tests', '__tests__', 'spec', 'specs']):
                test_directories.add(file.path.split('/')[0])
            
            # Test frameworks
            for framework, patterns in self.test_framework_patterns.items():
                if any(pattern in file.path for pattern in patterns):
                    frameworks.add(framework)
            
            # Mock frameworks
            if 'mock' in file.content.lower():
                if 'jest.mock' in file.content:
                    mock_frameworks.add('jest')
                elif 'sinon' in file.content:
                    mock_frameworks.add('sinon')
                elif 'unittest.mock' in file.content:
                    mock_frameworks.add('unittest.mock')
            
            # Coverage configuration
            if 'jest.config' in file.path and 'coverage' in file.content:
                try:
                    # Extract coverage configuration
                    coverage_config = {'tool': 'jest', 'configured': True}
                except:
                    pass
        
        return TestingInfo(
            frameworks=list(frameworks),
            test_directories=list(test_directories),
            coverage_config=coverage_config,
            test_patterns=test_patterns,
            mock_frameworks=list(mock_frameworks)
        )
    
    def _extract_build_info(self, files: List[FileContent]) -> BuildInfo:
        """Extract build and deployment information."""
        build_tools = set()
        scripts = {}
        docker_config = None
        ci_cd_config = None
        deployment_targets = []
        
        for file in files:
            # Build tools
            for tool, patterns in self.build_tool_patterns.items():
                if any(pattern in file.path for pattern in patterns):
                    build_tools.add(tool)
            
            # Scripts from package.json
            if file.path == 'package.json':
                try:
                    package_data = json.loads(file.content)
                    scripts.update(package_data.get('scripts', {}))
                except json.JSONDecodeError:
                    pass
            
            # Docker configuration
            if 'Dockerfile' in file.path or 'docker-compose' in file.path:
                docker_config = {'has_docker': True, 'files': [file.path]}
            
            # CI/CD configuration
            if '.github/workflows' in file.path:
                ci_cd_config = {'platform': 'github-actions', 'files': [file.path]}
            elif '.gitlab-ci.yml' in file.path:
                ci_cd_config = {'platform': 'gitlab-ci', 'files': [file.path]}
            elif 'Jenkinsfile' in file.path:
                ci_cd_config = {'platform': 'jenkins', 'files': [file.path]}
        
        return BuildInfo(
            build_tools=list(build_tools),
            scripts=scripts,
            docker_config=docker_config,
            ci_cd_config=ci_cd_config,
            deployment_targets=deployment_targets
        )
    
    def _extract_services_info(self, files: List[FileContent]) -> ServicesInfo:
        """Extract external services and API information."""
        databases = set()
        apis = set()
        cloud_services = set()
        third_party_integrations = set()
        environment_variables = set()
        
        for file in files:
            content_lower = file.content.lower()
            
            # Database detection
            if any(db in content_lower for db in ['mongodb', 'mongoose']):
                databases.add('mongodb')
            if any(db in content_lower for db in ['postgresql', 'postgres', 'pg']):
                databases.add('postgresql')
            if any(db in content_lower for db in ['mysql', 'mariadb']):
                databases.add('mysql')
            if any(db in content_lower for db in ['redis']):
                databases.add('redis')
            if any(db in content_lower for db in ['sqlite']):
                databases.add('sqlite')
            
            # Cloud services
            if any(cloud in content_lower for cloud in ['aws', 'amazon']):
                cloud_services.add('aws')
            if any(cloud in content_lower for cloud in ['gcp', 'google cloud']):
                cloud_services.add('gcp')
            if any(cloud in content_lower for cloud in ['azure', 'microsoft']):
                cloud_services.add('azure')
            
            # Third-party integrations
            if 'stripe' in content_lower:
                third_party_integrations.add('stripe')
            if 'sendgrid' in content_lower:
                third_party_integrations.add('sendgrid')
            if 'twilio' in content_lower:
                third_party_integrations.add('twilio')
            
            # Environment variables
            if file.path.endswith('.env.example') or file.path.endswith('.env.template'):
                env_vars = re.findall(r'^([A-Z_][A-Z0-9_]*)', file.content, re.MULTILINE)
                environment_variables.update(env_vars)
        
        return ServicesInfo(
            databases=list(databases),
            apis=list(apis),
            cloud_services=list(cloud_services),
            third_party_integrations=list(third_party_integrations),
            environment_variables=list(environment_variables)
        )
    
    def _identify_key_files(self, files: List[FileContent]) -> List[FileContent]:
        """Identify key files for LLM processing."""
        key_files = []
        
        priority_patterns = [
            r'README\.(md|rst|txt)$',
            r'package\.json$',
            r'pyproject\.toml$',
            r'Cargo\.toml$',
            r'tsconfig\.json$',
            r'\.eslintrc\.(js|json)$',
            r'jest\.config\.(js|ts)$',
            r'Dockerfile$',
            r'docker-compose\.ya?ml$',
            r'\.github/workflows/.*\.ya?ml$'
        ]
        
        for file in files:
            if any(re.search(pattern, file.path, re.IGNORECASE) for pattern in priority_patterns):
                key_files.append(file)
        
        return key_files
    
    def _parse_package_json_dependencies(self, content: str) -> Dict[str, Dict[str, str]]:
        """Parse package.json dependencies."""
        try:
            data = json.loads(content)
            return {
                'dependencies': data.get('dependencies', {}),
                'devDependencies': data.get('devDependencies', {}),
                'peerDependencies': data.get('peerDependencies', {}),
                'optionalDependencies': data.get('optionalDependencies', {})
            }
        except json.JSONDecodeError:
            return {}
    
    def _parse_requirements_txt(self, content: str) -> Dict[str, str]:
        """Parse requirements.txt dependencies."""
        deps = {}
        for line in content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if '==' in line:
                    name, version = line.split('==', 1)
                    deps[name.strip()] = version.strip()
                elif '>=' in line:
                    name, version = line.split('>=', 1)
                    deps[name.strip()] = f">={version.strip()}"
                else:
                    deps[line] = "*"
        return deps
    
    def _parse_pyproject_toml(self, content: str) -> Dict[str, Dict[str, str]]:
        """Parse pyproject.toml dependencies."""
        # Simple parsing - in production, use tomllib
        deps = {'dependencies': {}, 'dev-dependencies': {}}
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('[tool.poetry.dependencies]'):
                current_section = 'dependencies'
            elif line.startswith('[tool.poetry.group.dev.dependencies]'):
                current_section = 'dev-dependencies'
            elif line.startswith('[') and current_section:
                current_section = None
            elif current_section and '=' in line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    version = parts[1].strip().strip('"\'')
                    deps[current_section][name] = version
        
        return deps
    
    def _parse_cargo_toml(self, content: str) -> Dict[str, Dict[str, str]]:
        """Parse Cargo.toml dependencies."""
        # Simple parsing - in production, use tomllib
        deps = {'dependencies': {}, 'dev-dependencies': {}}
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line == '[dependencies]':
                current_section = 'dependencies'
            elif line == '[dev-dependencies]':
                current_section = 'dev-dependencies'
            elif line.startswith('[') and current_section:
                current_section = None
            elif current_section and '=' in line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    version = parts[1].strip().strip('"\'')
                    deps[current_section][name] = version
        
        return deps
    
    def _parse_composer_json(self, content: str) -> Dict[str, Dict[str, str]]:
        """Parse composer.json dependencies."""
        try:
            data = json.loads(content)
            return {
                'require': data.get('require', {}),
                'require-dev': data.get('require-dev', {})
            }
        except json.JSONDecodeError:
            return {'require': {}, 'require-dev': {}}