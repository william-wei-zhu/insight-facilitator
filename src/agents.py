from crewai import Agent, LLM
from tools.web_scraping_tool import EnhancedScrapeWebsiteTool
from crewai_tools import SerperDevTool
from config.agent_config import (
    INFO_GATHERER_CONFIG, INSIGHT_ANALYST_CONFIG, DISCUSSION_FACILITATOR_CONFIG
)
import os

class AgentFactory:
    """Factory class for creating agents."""
    
    def __init__(self, llm):
        """
        Initialize the AgentFactory.
        
        Args:
            llm: The language model to use for the agents.
        """
        self.llm = llm
        
        # Initialize tools
        self.web_scraping_tool = EnhancedScrapeWebsiteTool()
        
        # Initialize SerperDevTool with API key from environment variable
        serper_api_key = os.getenv('SERPER_API_KEY')
        if serper_api_key:
            self.search_tool = SerperDevTool(api_key=serper_api_key)
        else:
            # If no API key, create a placeholder that will show an error message
            self.search_tool = None
    
    # Insight Facilitator agents
    def create_info_gatherer(self, verbose=False):
        """Create an information gatherer agent for books and movies."""
        # Prepare tools list, excluding None values
        tools = [tool for tool in [self.search_tool, self.web_scraping_tool] if tool is not None]
        
        # If no search tool is available, add a warning to the backstory
        backstory = INFO_GATHERER_CONFIG["backstory"]
        if self.search_tool is None:
            backstory += "\n\nNOTE: You do not have access to a search tool because no Serper API key was provided. "
            backstory += "You will need to rely on your existing knowledge and the web scraping tool."
        
        return Agent(
            role=INFO_GATHERER_CONFIG["role"],
            goal=INFO_GATHERER_CONFIG["goal"],
            backstory=backstory,
            verbose=verbose,
            llm=self.llm,
            tools=tools
        )
    
    def create_insight_analyst(self, verbose=False):
        """Create an insight analyst agent for books and movies."""
        # Use web scraping tool for verification if needed
        tools = [tool for tool in [self.web_scraping_tool] if tool is not None]
        
        return Agent(
            role=INSIGHT_ANALYST_CONFIG["role"],
            goal=INSIGHT_ANALYST_CONFIG["goal"],
            backstory=INSIGHT_ANALYST_CONFIG["backstory"],
            verbose=verbose,
            llm=self.llm,
            tools=tools
        )
    
    def create_discussion_facilitator(self, verbose=False):
        """Create a discussion facilitator agent for books and movies."""
        # This agent doesn't need any tools as it works with the output of other agents
        
        return Agent(
            role=DISCUSSION_FACILITATOR_CONFIG["role"],
            goal=DISCUSSION_FACILITATOR_CONFIG["goal"],
            backstory=DISCUSSION_FACILITATOR_CONFIG["backstory"],
            verbose=verbose,
            llm=self.llm
        )
