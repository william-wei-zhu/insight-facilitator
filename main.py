from src.agents import AgentFactory
from src.crew import CrewFactory
from config.llm_config import get_llm
import argparse

def main():
    """Main function to run the Insight Facilitator application."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Insight Facilitator CLI")
    parser.add_argument("--title", type=str, default="To Kill a Mockingbird", help="Title of the book or movie to analyze")
    parser.add_argument("--type", type=str, default="Book", choices=["Book", "Movie"], help="Type of media (Book or Movie)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Get configured LLM from centralized config
    llm = get_llm(verbose=args.verbose)
    
    # Create agent factory
    agent_factory = AgentFactory(llm)
    
    # Create crew factory
    crew_factory = CrewFactory(agent_factory)
    
    print(f"Analyzing {args.type}: {args.title}")
    
    # Create the Insight Facilitator crew
    insight_crew = crew_factory.create_insight_facilitator_crew(args.title, verbose=args.verbose)
    
    # Run the crew
    result = insight_crew.kickoff()
    
    # Print the result
    print("\n\n=== INSIGHT FACILITATOR RESULT ===\n")
    print(result)

if __name__ == "__main__":
    main()
