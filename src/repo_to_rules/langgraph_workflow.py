"""LangGraph workflow for repository processing."""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage

from .models import RepoMetadata, RepositoryContext, GeneratedOutput
from .github_client import GitHubClient
from .context_extractor import ContextExtractor
from .llm_processor import LLMProcessor
from .rule_generator import RuleGenerator
from .config import Settings

logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """State for the LangGraph workflow."""
    repo_name: str
    metadata: RepoMetadata = None
    files: List = None
    stats: Dict[str, Any] = None
    context: RepositoryContext = None
    generated_output: GeneratedOutput = None
    error: str = None
    completed: bool = False


class RepositoryWorkflow:
    """LangGraph workflow for processing repositories."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.github_client = GitHubClient(settings)
        self.context_extractor = ContextExtractor()
        self.llm_processor = LLMProcessor(settings)
        self.rule_generator = RuleGenerator(settings)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("fetch_metadata", self._fetch_metadata)
        workflow.add_node("fetch_files", self._fetch_files)
        workflow.add_node("fetch_stats", self._fetch_stats)
        workflow.add_node("extract_context", self._extract_context)
        workflow.add_node("process_with_llm", self._process_with_llm)
        workflow.add_node("generate_rules", self._generate_rules)
        workflow.add_node("save_output", self._save_output)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("fetch_metadata")
        
        # Add edges
        workflow.add_conditional_edges(
            "fetch_metadata",
            self._should_continue_after_metadata,
            {
                "continue": "fetch_files",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "fetch_files",
            self._should_continue_after_files,
            {
                "continue": "fetch_stats",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "fetch_stats",
            self._should_continue_after_stats,
            {
                "continue": "extract_context",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "extract_context",
            self._should_continue_after_context,
            {
                "continue": "process_with_llm",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "process_with_llm",
            self._should_continue_after_llm,
            {
                "continue": "generate_rules",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_rules",
            self._should_continue_after_generation,
            {
                "continue": "save_output",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("save_output", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def process_repository(self, repo_name: str) -> WorkflowState:
        """Process a single repository through the workflow."""
        logger.info(f"Starting workflow for repository: {repo_name}")
        
        initial_state = WorkflowState(repo_name=repo_name)
        
        try:
            result = await self.workflow.ainvoke(initial_state)
            return result
        except Exception as e:
            logger.error(f"Workflow failed for {repo_name}: {e}")
            return WorkflowState(
                repo_name=repo_name,
                error=str(e),
                completed=False
            )
    
    async def _fetch_metadata(self, state: WorkflowState) -> WorkflowState:
        """Fetch repository metadata."""
        try:
            logger.info(f"Fetching metadata for {state.repo_name}")
            
            # Get all repositories and find the target one
            repos = await self.github_client.get_repositories()
            target_repo = next((repo for repo in repos if repo.name == state.repo_name), None)
            
            if not target_repo:
                state.error = f"Repository {state.repo_name} not found"
                return state
            
            state.metadata = target_repo
            logger.info(f"Successfully fetched metadata for {state.repo_name}")
            return state
            
        except Exception as e:
            state.error = f"Failed to fetch metadata: {str(e)}"
            logger.error(f"Error fetching metadata for {state.repo_name}: {e}")
            return state
    
    async def _fetch_files(self, state: WorkflowState) -> WorkflowState:
        """Fetch repository files."""
        try:
            logger.info(f"Fetching files for {state.repo_name}")
            
            files = await self.github_client.get_repository_files(state.repo_name)
            state.files = files
            
            logger.info(f"Successfully fetched {len(files)} files for {state.repo_name}")
            return state
            
        except Exception as e:
            state.error = f"Failed to fetch files: {str(e)}"
            logger.error(f"Error fetching files for {state.repo_name}: {e}")
            return state
    
    async def _fetch_stats(self, state: WorkflowState) -> WorkflowState:
        """Fetch repository statistics."""
        try:
            logger.info(f"Fetching stats for {state.repo_name}")
            
            stats = await self.github_client.get_repository_stats(state.repo_name)
            state.stats = stats
            
            logger.info(f"Successfully fetched stats for {state.repo_name}")
            return state
            
        except Exception as e:
            state.error = f"Failed to fetch stats: {str(e)}"
            logger.error(f"Error fetching stats for {state.repo_name}: {e}")
            return state
    
    async def _extract_context(self, state: WorkflowState) -> WorkflowState:
        """Extract repository context."""
        try:
            logger.info(f"Extracting context for {state.repo_name}")
            
            context = self.context_extractor.extract_context(
                state.metadata, 
                state.files, 
                state.stats or {}
            )
            state.context = context
            
            logger.info(f"Successfully extracted context for {state.repo_name}")
            return state
            
        except Exception as e:
            state.error = f"Failed to extract context: {str(e)}"
            logger.error(f"Error extracting context for {state.repo_name}: {e}")
            return state
    
    async def _process_with_llm(self, state: WorkflowState) -> WorkflowState:
        """Process context with LLM."""
        try:
            logger.info(f"Processing with LLM for {state.repo_name}")
            
            # Enhance context with LLM analysis
            enhanced_context = await self.llm_processor.enhance_context(state.context)
            state.context = enhanced_context
            
            logger.info(f"Successfully processed with LLM for {state.repo_name}")
            return state
            
        except Exception as e:
            state.error = f"Failed to process with LLM: {str(e)}"
            logger.error(f"Error processing with LLM for {state.repo_name}: {e}")
            return state
    
    async def _generate_rules(self, state: WorkflowState) -> WorkflowState:
        """Generate rules and configurations."""
        try:
            logger.info(f"Generating rules for {state.repo_name}")
            
            output = await self.rule_generator.generate_output(state.context)
            state.generated_output = output
            
            logger.info(f"Successfully generated rules for {state.repo_name}")
            return state
            
        except Exception as e:
            state.error = f"Failed to generate rules: {str(e)}"
            logger.error(f"Error generating rules for {state.repo_name}: {e}")
            return state
    
    async def _save_output(self, state: WorkflowState) -> WorkflowState:
        """Save generated output to files."""
        try:
            logger.info(f"Saving output for {state.repo_name}")
            
            await self.rule_generator.save_output(
                state.repo_name, 
                state.generated_output
            )
            
            state.completed = True
            logger.info(f"Successfully saved output for {state.repo_name}")
            return state
            
        except Exception as e:
            state.error = f"Failed to save output: {str(e)}"
            logger.error(f"Error saving output for {state.repo_name}: {e}")
            return state
    
    async def _handle_error(self, state: WorkflowState) -> WorkflowState:
        """Handle workflow errors."""
        logger.error(f"Handling error for {state.repo_name}: {state.error}")
        state.completed = False
        return state
    
    def _should_continue_after_metadata(self, state: WorkflowState) -> str:
        """Decide whether to continue after metadata fetch."""
        return "error" if state.error else "continue"
    
    def _should_continue_after_files(self, state: WorkflowState) -> str:
        """Decide whether to continue after files fetch."""
        return "error" if state.error else "continue"
    
    def _should_continue_after_stats(self, state: WorkflowState) -> str:
        """Decide whether to continue after stats fetch."""
        return "error" if state.error else "continue"
    
    def _should_continue_after_context(self, state: WorkflowState) -> str:
        """Decide whether to continue after context extraction."""
        return "error" if state.error else "continue"
    
    def _should_continue_after_llm(self, state: WorkflowState) -> str:
        """Decide whether to continue after LLM processing."""
        return "error" if state.error else "continue"
    
    def _should_continue_after_generation(self, state: WorkflowState) -> str:
        """Decide whether to continue after rule generation."""
        return "error" if state.error else "continue"