import gradio as gr
import os
from crewai import Agent, Task
from src.agents import AgentFactory
from src.crew import CrewFactory
from config.llm_config import get_llm
from utils.retry_utils import retry_on_exception

# Initialize variables for dynamic LLM configuration
llm = None
agent_factory = None
crew_factory = None

def initialize_llm(verbose=True):
    """Initialize the LLM, agent factory, and crew factory with GPT-4o."""
    global llm, agent_factory, crew_factory
    
    try:
        # Initialize GPT-4.1-nano LLM
        llm = get_llm(provider="openai", model_name="openai/gpt-4.1-nano", verbose=verbose)
        
        # Create agent factory
        agent_factory = AgentFactory(llm)
        
        # Create crew factory
        crew_factory = CrewFactory(agent_factory)
        
        return True, "LLM initialized successfully"
        
    except Exception as e:
        # Provide more detailed error information
        import traceback
        error_message = f"Error initializing LLM: {str(e)}"
        print(error_message)
        print("\nDetailed error information:")
        traceback.print_exc()
        return False, error_message

# Initialize with GPT-4o
initialize_llm()

@retry_on_exception(max_retries=5, initial_delay=5.0, backoff_factor=3.0)
def run_insight_facilitator_crew(media_title, media_type="book or movie", verbose=True):
    """Run an Insight Facilitator crew for a book or movie."""
    print(f"Starting analysis of {media_type}: {media_title}")
    
    # Create an Insight Facilitator crew with the specific media type
    insight_crew = crew_factory.create_insight_facilitator_crew(media_title, media_type=media_type, verbose=verbose)
    
    # Run the crew
    print("Insight Facilitator crew created, starting kickoff...")
    result = insight_crew.kickoff()
    print("Insight Facilitator analysis completed successfully")
    
    return result

# Create a simple theme with minimal customization
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="indigo",
    neutral_hue="slate",
    text_size="lg"
)

# Load external CSS file
css_path = os.path.join(os.path.dirname(__file__), "static", "styles.css")
with open(css_path, "r") as f:
    custom_css = f.read()

# Function to generate insights
def generate_insights(title, media_type):
    """Generate insights and discussion questions for the given title"""
    try:
        if not title or title.strip() == "":
            return "Please enter a book or movie title."
        
        # Strip emoji from media_type
        clean_media_type = "Book" if "Book" in media_type else "Movie"
            
        print(f"Starting analysis of {clean_media_type}: {title}")
        # Pass the specific media type to the crew factory
        result = run_insight_facilitator_crew(title, media_type=clean_media_type)
        
        return result
    except Exception as e:
        import traceback
        error_message = f"Error generating insights: {str(e)}"
        print(error_message)
        print("\nDetailed error information:")
        traceback.print_exc()
        # Provide more user-friendly error message
        error_msg = f"Error: {str(e)}. Please try again or try a different title."
        print(error_msg)
        return error_msg



# Create the main app UI
with gr.Blocks(title="Insight Facilitator", theme=theme, css=custom_css) as demo:
    # Header
    gr.Markdown("<div style='text-align: center;'><h1 class='title-text'>✨ Insight Facilitator</h1></div>")
    gr.Markdown("<div style='text-align: center;'><p class='subtitle-text'>Want to elevate your next book or film club conversation? Enter any title for 8 thought-provoking discussion questions.</p></div>")

    # Input section
    with gr.Group():
        media_title = gr.Textbox(
            label="",
            placeholder="What book or movie would you like to explore?",
            show_label=False,
            elem_classes="input-field",
            elem_id="search-bar",
            scale=3,
            container=False
        )
        
        media_type = gr.Radio(
            ["📖 Book", "🎬 Movie"], 
            label="", 
            value="📖 Book",
            show_label=False
        )
        
        insight_button = gr.Button(
            "Generate Insights & Discussion Questions", 
            variant="primary",
            size="lg"
        )

    # Results section
    with gr.Group():
        gr.Markdown("<h3 class='section-heading'>Results</h3>")
        insight_output = gr.Textbox(
            value="Insights and discussion questions will appear here in ~30 seconds after you click the button...", 
            lines=15, 
            show_label=False,
            container=False
        )
        


    # Footer
    gr.Markdown("""
    <div style='text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(128, 128, 128, 0.2);'>
        <p class='footer-text' style='margin-top: 1rem; font-size: 0.8em;'>Created by William Zhu | <a href='https://www.linkedin.com/in/william-wei-zhu/' target='_blank'>LinkedIn page</a> | <a href='https://william-wei-zhu.github.io/' target='_blank'>Personal Website</a></p>
        <p class='footer-text' style='font-size: 0.7em;'>All rights reserved.</p>
    </div>
    """)

    # Connect UI components to functions
    insight_button.click(
        fn=generate_insights,
        inputs=[media_title, media_type],
        outputs=[insight_output]
    )

# Launch the app
if __name__ == "__main__":
    import os
    # Check if running on Hugging Face Spaces
    if "SPACE_ID" in os.environ:
        demo.launch()
    else:
        # Running locally
        demo.launch(share=False)
