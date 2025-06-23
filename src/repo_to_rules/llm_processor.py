"""LLM processor using Claude for context enhancement and analysis."""

import json
import logging
from typing import Dict, Any, List, Optional
import asyncio

from anthropic import AsyncAnthropic

from .models import RepositoryContext, CodePatterns, TestingInfo, BuildInfo
from .config import Settings

logger = logging.getLogger(__name__)


class LLMProcessor:
    """Process repository context using Claude LLM."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def enhance_context(self, context: RepositoryContext) -> RepositoryContext:
        """Enhance repository context with LLM analysis."""
        logger.info(f"Enhancing context for {context.metadata.name}")
        
        try:
            # Analyze in parallel for better performance
            tasks = [
                self._analyze_architecture(context),
                self._analyze_code_patterns(context),
                self._analyze_testing_strategy(context),
                self._analyze_build_deployment(context),
                self._generate_project_insights(context)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            architecture_analysis = results[0] if not isinstance(results[0], Exception) else {}
            code_patterns_analysis = results[1] if not isinstance(results[1], Exception) else {}
            testing_analysis = results[2] if not isinstance(results[2], Exception) else {}
            build_analysis = results[3] if not isinstance(results[3], Exception) else {}
            project_insights = results[4] if not isinstance(results[4], Exception) else {}
            
            # Enhance the context with LLM insights
            enhanced_context = self._merge_enhancements(
                context, 
                architecture_analysis,
                code_patterns_analysis,
                testing_analysis,
                build_analysis,
                project_insights
            )
            
            logger.info(f"Successfully enhanced context for {context.metadata.name}")
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Error enhancing context for {context.metadata.name}: {e}")
            return context  # Return original context if enhancement fails
    
    async def _analyze_architecture(self, context: RepositoryContext) -> Dict[str, Any]:
        """Analyze project architecture patterns."""
        prompt = f"""
        Analyze the architecture of this {context.metadata.language or 'software'} project:
        
        Project: {context.metadata.name}
        Description: {context.metadata.description or 'No description'}
        Main Language: {context.metadata.language}
        Tech Stack: {', '.join(context.structure.tech_stack)}
        Directories: {', '.join(context.structure.directories)}
        Dependencies: {list(context.dependencies.runtime.keys())[:10]}
        
        Key Files Analysis:
        {self._format_key_files(context.key_files)}
        
        Provide a structured analysis of:
        1. Overall architecture pattern (MVC, microservices, monolith, etc.)
        2. Layer separation and organization
        3. Design patterns used
        4. Scalability considerations
        5. Recommended architectural improvements
        
        Respond with JSON format:
        {{
            "architecture_type": "string",
            "patterns": ["pattern1", "pattern2"],
            "layers": ["layer1", "layer2"],
            "scalability": "assessment",
            "recommendations": ["rec1", "rec2"]
        }}
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_json_response(response.content[0].text)
        except Exception as e:
            logger.warning(f"Architecture analysis failed: {e}")
            return {}
    
    async def _analyze_code_patterns(self, context: RepositoryContext) -> Dict[str, Any]:
        """Analyze code patterns and conventions."""
        prompt = f"""
        Analyze the coding patterns and conventions for this project:
        
        Project: {context.metadata.name}
        Language: {context.metadata.language}
        Linting Rules: {json.dumps(context.code_patterns.linting_rules, indent=2)}
        Formatting Config: {json.dumps(context.code_patterns.formatting_config, indent=2)}
        
        Code Samples from Key Files:
        {self._format_code_samples(context.key_files)}
        
        Analyze and provide:
        1. Naming conventions (variables, functions, classes, files)
        2. Code organization patterns
        3. Error handling patterns
        4. Documentation standards
        5. Performance patterns
        6. Security patterns
        
        Respond with JSON format:
        {{
            "naming_conventions": {{
                "variables": "convention",
                "functions": "convention",
                "classes": "convention",
                "files": "convention"
            }},
            "organization_patterns": ["pattern1"],
            "error_handling": "approach",
            "documentation_style": "style",
            "performance_patterns": ["pattern1"],
            "security_patterns": ["pattern1"],
            "recommendations": ["rec1"]
        }}
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_json_response(response.content[0].text)
        except Exception as e:
            logger.warning(f"Code patterns analysis failed: {e}")
            return {}
    
    async def _analyze_testing_strategy(self, context: RepositoryContext) -> Dict[str, Any]:
        """Analyze testing strategy and patterns."""
        prompt = f"""
        Analyze the testing strategy for this project:
        
        Project: {context.metadata.name}
        Testing Frameworks: {', '.join(context.testing.frameworks)}
        Test Directories: {', '.join(context.testing.test_directories)}
        Mock Frameworks: {', '.join(context.testing.mock_frameworks)}
        
        Test Configuration:
        {json.dumps(context.testing.coverage_config or {}, indent=2)}
        
        Provide analysis of:
        1. Testing approach (unit, integration, e2e)
        2. Test organization and structure
        3. Coverage strategy
        4. Mocking patterns
        5. Test data management
        6. Recommended improvements
        
        Respond with JSON format:
        {{
            "testing_approach": ["unit", "integration", "e2e"],
            "test_structure": "description",
            "coverage_strategy": "strategy",
            "mocking_patterns": ["pattern1"],
            "data_management": "approach",
            "recommendations": ["rec1"]
        }}
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_json_response(response.content[0].text)
        except Exception as e:
            logger.warning(f"Testing analysis failed: {e}")
            return {}
    
    async def _analyze_build_deployment(self, context: RepositoryContext) -> Dict[str, Any]:
        """Analyze build and deployment processes."""
        prompt = f"""
        Analyze the build and deployment setup for this project:
        
        Project: {context.metadata.name}
        Build Tools: {', '.join(context.build.build_tools)}
        Scripts: {json.dumps(context.build.scripts, indent=2)}
        Docker Config: {json.dumps(context.build.docker_config or {}, indent=2)}
        CI/CD Config: {json.dumps(context.build.ci_cd_config or {}, indent=2)}
        
        Analyze:
        1. Build process and optimization
        2. Deployment strategy
        3. Environment management
        4. Performance optimizations
        5. Recommended improvements
        
        Respond with JSON format:
        {{
            "build_process": "description",
            "deployment_strategy": "strategy",
            "environment_management": "approach",
            "optimizations": ["opt1"],
            "recommendations": ["rec1"]
        }}
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_json_response(response.content[0].text)
        except Exception as e:
            logger.warning(f"Build/deployment analysis failed: {e}")
            return {}
    
    async def _generate_project_insights(self, context: RepositoryContext) -> Dict[str, Any]:
        """Generate overall project insights and recommendations."""
        prompt = f"""
        Generate comprehensive insights for this project:
        
        Project: {context.metadata.name}
        Description: {context.metadata.description}
        Language: {context.metadata.language}
        Stars: {context.metadata.stars}
        Size: {context.metadata.size}KB
        
        Tech Stack: {', '.join(context.structure.tech_stack)}
        Services: {', '.join(context.services.databases + context.services.cloud_services)}
        
        Generate insights about:
        1. Project maturity and quality
        2. Development workflow efficiency
        3. Maintainability concerns
        4. Scaling potential
        5. Technology choices assessment
        6. Key improvement areas
        
        Respond with JSON format:
        {{
            "maturity_level": "high|medium|low",
            "quality_score": "1-10",
            "workflow_efficiency": "assessment",
            "maintainability": "assessment",
            "scaling_potential": "assessment",
            "technology_assessment": "assessment",
            "key_strengths": ["strength1"],
            "improvement_areas": ["area1"],
            "recommendations": ["rec1"]
        }}
        """
        
        try:
            response = await self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_json_response(response.content[0].text)
        except Exception as e:
            logger.warning(f"Project insights generation failed: {e}")
            return {}
    
    def _format_key_files(self, key_files: List) -> str:
        """Format key files for LLM analysis."""
        formatted = []
        for file in key_files[:5]:  # Limit to top 5 files
            content_preview = file.content[:500] + "..." if len(file.content) > 500 else file.content
            formatted.append(f"File: {file.path}\n{content_preview}\n")
        return "\n".join(formatted)
    
    def _format_code_samples(self, key_files: List) -> str:
        """Format code samples for pattern analysis."""
        code_files = [f for f in key_files if any(f.path.endswith(ext) for ext in ['.js', '.ts', '.py', '.java', '.go', '.rs'])]
        
        formatted = []
        for file in code_files[:3]:  # Limit to 3 code files
            content_preview = file.content[:800] + "..." if len(file.content) > 800 else file.content
            formatted.append(f"File: {file.path}\n```\n{content_preview}\n```\n")
        return "\n".join(formatted)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from Claude."""
        try:
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in response")
                return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {}
    
    def _merge_enhancements(self, context: RepositoryContext, 
                           architecture: Dict[str, Any],
                           code_patterns: Dict[str, Any],
                           testing: Dict[str, Any],
                           build: Dict[str, Any],
                           insights: Dict[str, Any]) -> RepositoryContext:
        """Merge LLM enhancements into the context."""
        
        # Enhance code patterns
        if code_patterns:
            if 'naming_conventions' in code_patterns:
                context.code_patterns.naming_conventions.update(code_patterns['naming_conventions'])
            if 'organization_patterns' in code_patterns:
                context.code_patterns.architectural_patterns.extend(code_patterns['organization_patterns'])
        
        # Enhance testing info
        if testing:
            if 'testing_approach' in testing:
                context.testing.test_patterns.extend(testing['testing_approach'])
        
        # Add insights as metadata
        context.metadata.topics.extend(insights.get('key_strengths', []))
        
        return context