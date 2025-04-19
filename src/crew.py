from crewai import Crew, Process, Task
from src.agents import AgentFactory
from config.agent_config import TASK_CONFIGS
from typing import List, Dict, Any

class CrewFactory:
    """Factory class for creating crews."""
    
    def __init__(self, agent_factory):
        """
        Initialize the CrewFactory.
        
        Args:
            agent_factory: The agent factory to use for creating agents.
        """
        self.agent_factory = agent_factory
    

    
    # Custom validation handling will be implemented in the task descriptions
    
    def create_insight_facilitator_crew(self, media_title, media_type="Book", verbose=False):
        """
        Create an Insight Facilitator crew for book/movie analysis.
        
        Args:
            media_title: The title of the book or movie to analyze.
            media_type: The type of media (Book or Movie).
            verbose: Whether to enable verbose output.
            
        Returns:
            A configured Crew object.
        """
        # Create agents
        info_gatherer = self.agent_factory.create_info_gatherer(verbose=verbose)
        insight_analyst = self.agent_factory.create_insight_analyst(verbose=verbose)
        discussion_facilitator = self.agent_factory.create_discussion_facilitator(verbose=verbose)
        
        # Create tasks with media_type-specific descriptions
        research_task = Task(
            description=f"{TASK_CONFIGS['research_media']['description']} Title: {media_title}, Type: {media_type}",
            expected_output=TASK_CONFIGS['research_media']['expected_output'],
            agent=info_gatherer
        )
        
        insights_task = Task(
            description=f"FIRST: Check if the research output contains 'VALIDATION_FAILED'. If it does, respond with exactly the same message and do not perform any analysis. SECOND (only if validation passed): {TASK_CONFIGS['analyze_insights']['description']} This is a {media_type} titled: {media_title}",
            expected_output=TASK_CONFIGS['analyze_insights']['expected_output'],
            agent=insight_analyst,
            context=[research_task]
        )
        
        questions_task = Task(
            description=f"FIRST: Check if the research output or insights output contains 'VALIDATION_FAILED'. If it does, respond with exactly the same message and do not create any questions. SECOND (only if validation passed): {TASK_CONFIGS['create_questions']['description']} This is a {media_type} titled: {media_title}",
            expected_output=TASK_CONFIGS['create_questions']['expected_output'],
            agent=discussion_facilitator,
            context=[research_task, insights_task]
        )
        
        # Create crew
        crew = Crew(
            agents=[info_gatherer, insight_analyst, discussion_facilitator],
            tasks=[research_task, insights_task, questions_task],
            verbose=verbose,
            process=Process.sequential,
            # Add significant delay between agent actions to avoid rate limits
            # agent_execution_delay=10  # 10 seconds delay between agent actions (commented out for speed)
        )
        
        return crew
