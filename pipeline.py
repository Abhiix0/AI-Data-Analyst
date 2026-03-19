"""Pipeline — orchestrates the multi-agent analysis workflow.

This module provides a clean, extensible pipeline for running agents in sequence.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import pandas as pd

from agents.base_agent import BaseAgent, AgentResult
from utils.logging_utils import setup_logger

logger = setup_logger(__name__)


class AnalysisPipeline:
    """Orchestrates the execution of multiple analysis agents."""
    
    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        """Initialize the pipeline.
        
        Args:
            agents: List of agents to run in sequence (optional)
        """
        self.agents: List[BaseAgent] = agents or []
        self.results: Dict[str, AgentResult] = {}
        self._df: Optional[pd.DataFrame] = None
    
    def add_agent(self, agent: BaseAgent) -> None:
        """Add an agent to the pipeline.
        
        Args:
            agent: Agent to add
        """
        self.agents.append(agent)
        logger.info(f"Added agent: {agent.name}")
    
    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the pipeline by name.
        
        Args:
            agent_name: Name of agent to remove
        """
        self.agents = [a for a in self.agents if a.name != agent_name]
        logger.info(f"Removed agent: {agent_name}")
    
    def run(
        self,
        df: pd.DataFrame,
        dataset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute all agents in the pipeline.
        
        Args:
            df: Input DataFrame to analyze
            dataset_name: Optional name for the dataset
            
        Returns:
            Combined results from all agents
        """
        self._df = df
        self.results.clear()
        
        logger.info("=" * 60)
        logger.info("  AI Data Analyst Pipeline")
        logger.info("=" * 60)
        logger.info(f"Dataset: {dataset_name or 'Unknown'}")
        logger.info(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        logger.info(f"Agents: {len([a for a in self.agents if a.is_enabled()])}")
        logger.info("=" * 60)
        
        combined_insights = []
        combined_metrics = {}
        
        for agent in self.agents:
            if not agent.is_enabled():
                logger.info(f"Skipping disabled agent: {agent.name}")
                continue
            
            try:
                logger.info(f"Running: {agent.name}")
                
                # Pass dataset_name to agents that need it
                kwargs = {}
                if dataset_name and "dataset_name" in agent.run.__code__.co_varnames:
                    kwargs["dataset_name"] = dataset_name
                
                # Pass previous results to agents that need context
                if "dataset_context" in agent.run.__code__.co_varnames:
                    kwargs["dataset_context"] = self.results.get("DatasetUnderstandingAgent")
                
                if "cleaning_result" in agent.run.__code__.co_varnames:
                    kwargs["cleaning_result"] = self.results.get("DataCleanerAgent")
                
                if "analysis_result" in agent.run.__code__.co_varnames:
                    kwargs["analysis_result"] = self.results.get("AnalysisAgent")
                
                result = agent.run(df, **kwargs)
                self.results[agent.name] = result
                
                # Collect insights and metrics
                combined_insights.extend(result.insights)
                combined_metrics[agent.name] = result.metrics
                
                logger.info(f"✓ {agent.name} complete: {len(result.insights)} insights")
                
            except Exception as e:
                logger.error(f"✗ {agent.name} failed: {e}")
                # Continue with other agents even if one fails
                continue
        
        # Build final report
        summary = (
            f"Completed analysis pipeline with {len(self.results)} agents. "
            f"Generated {len(combined_insights)} total insights."
        )
        
        final_report = {
            "summary": summary,
            "metrics": combined_metrics,
            "insights": combined_insights,
            "agent_results": {
                name: result.to_dict() 
                for name, result in self.results.items()
            }
        }
        
        logger.info("=" * 60)
        logger.info(f"Pipeline complete: {len(self.results)} agents executed")
        logger.info("=" * 60)
        
        return final_report
    
    def get_result(self, agent_name: str) -> Optional[AgentResult]:
        """Get result from a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AgentResult or None if not found
        """
        return self.results.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """Get list of agent names in the pipeline.
        
        Returns:
            List of agent names
        """
        return [agent.name for agent in self.agents]
    
    def __repr__(self) -> str:
        """String representation."""
        enabled = len([a for a in self.agents if a.is_enabled()])
        return f"AnalysisPipeline(agents={enabled}/{len(self.agents)})"
