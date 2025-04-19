import gradio as gr
import os
import hashlib
import time
import datetime
import base64
from crewai import Agent, Task
from src.agents import AgentFactory
from src.crew import CrewFactory
from config.llm_config import get_llm
from utils.retry_utils import retry_on_exception
from utils.database import record_feedback
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from utils.config import DB_PATH
from utils.tts_utils import text_to_speech

# Initialize variables for dynamic LLM configuration
llm = None
agent_factory = None
crew_factory = None

def initialize_llm(provider="openai", verbose=True):
    """Initialize the LLM, agent factory, and crew factory with the specified provider."""
    global llm, agent_factory, crew_factory
    
    try:
        # Get configured LLM
        if provider == "bedrock":
            llm = get_llm(provider="bedrock", model_name="bedrock/anthropic.claude-3-haiku-20240307-v1:0", verbose=verbose)
        elif provider == "openai":
            llm = get_llm(provider="openai", model_name="openai/gpt-4o", verbose=verbose)
        else:  # auto
            llm = get_llm(provider="auto", verbose=verbose)
        
        # Create agent factory
        agent_factory = AgentFactory(llm)
        
        # Create crew factory
        crew_factory = CrewFactory(agent_factory)
        
        return True, "LLM initialized successfully"
        
    except Exception as e:
        # Provide more detailed error information
        import traceback
        error_message = f"Error initializing LLM with provider '{provider}': {str(e)}"
        print(error_message)
        print("\nDetailed error information:")
        traceback.print_exc()
        return False, error_message

# Try to initialize with default provider
initialize_llm("openai")

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

# Function to switch provider
def switch_provider(provider):
    """Change the LLM provider"""
    # Map display names to actual provider values
    provider_map = {
        "OpenAI (GPT-4o)": "openai",
        "Claude 3.5 Haiku": "bedrock"
    }
    actual_provider = provider_map.get(provider, "openai")
    
    success, message = initialize_llm(actual_provider)
    if success:
        if actual_provider == "bedrock":
            status = "Using Claude 3.5 Haiku"
        elif actual_provider == "openai":
            status = "Using OpenAI (GPT-4o)"
        else:
            status = "Using Auto Provider Selection"
        return status
    else:
        return f"Error: {message}"

# Function to generate insights
def generate_insights(title, media_type):
    """Generate insights and discussion questions for the given title"""
    try:
        if not title or title.strip() == "":
            return "Please enter a book or movie title.", gr.update(visible=False), gr.update(visible=False)
        
        # Strip emoji from media_type
        clean_media_type = "Book" if "Book" in media_type else "Movie"
            
        print(f"Starting analysis of {clean_media_type}: {title}")
        # Pass the specific media type to the crew factory
        result = run_insight_facilitator_crew(title, media_type=clean_media_type, verbose=False)
        print("Insights generated successfully")
        
        # Show feedback options and audio button
        return result, gr.update(visible=True), gr.update(visible=True)
    except Exception as e:
        import traceback
        error_message = f"Error generating insights: {str(e)}"
        print(error_message)
        print("\nDetailed error information:")
        traceback.print_exc()
        # Provide more user-friendly error message
        error_msg = f"Error: {str(e)}. Please try again or try a different title."
        print(error_msg)
        return error_msg, gr.update(visible=False), gr.update(visible=False)

# Function to convert insights to speech
def insights_to_speech(insights):
    """Convert insights to speech"""
    try:
        # Add a loading indicator by returning an initial message
        gr.Info("Converting text to speech... This may take a moment.")
        
        # Check if insights is empty or too short
        if not insights or len(insights.strip()) < 10:
            gr.Warning("The text is too short or empty to convert to speech.")
            return None
        
        # Call the text-to-speech function
        speech_file = text_to_speech(insights, voice="echo", model="tts-1")
        
        # Show success message
        if speech_file:
            gr.Info("Speech generated successfully!")
        
        return speech_file
    except Exception as e:
        # Handle errors and show error message
        error_msg = f"Error generating speech: {str(e)}"
        print(error_msg)
        gr.Error(error_msg)
        return None

# Global state to track feedback
feedback_choices = gr.State({
    "is_positive": None,
    "title": "",
    "media_type": "",
    "result": ""
})

# Function to handle positive feedback
def record_positive(title, media_type, result):
    """Handle positive feedback button click"""
    if not title or not result:
        return "Please generate insights first", gr.update(visible=False), gr.update(visible=False)
    
    state = {
        "is_positive": True,
        "title": title,
        "media_type": "Book" if "Book" in media_type else "Movie",
        "result": result
    }
    
    return "Thanks! Any additional comments?", gr.update(visible=True), gr.update(visible=True)

# Function to handle negative feedback
def record_negative(title, media_type, result):
    """Handle negative feedback button click"""
    if not title or not result:
        return "Please generate insights first", gr.update(visible=False), gr.update(visible=False)
    
    state = {
        "is_positive": False,
        "title": title,
        "media_type": "Book" if "Book" in media_type else "Movie",
        "result": result
    }
    
    return "Thanks! Any additional comments?", gr.update(visible=True), gr.update(visible=True)

# Function to submit feedback with comment
def submit_feedback(title, media_type, result, is_positive, comment):
    """Submit feedback with optional comment"""
    try:
        if not title or not result:
            return "Error: Missing title or result."
        
        clean_media_type = "Book" if "Book" in media_type else "Movie"
        
        success = record_feedback(
            title=title,
            media_type=clean_media_type,
            result=result,
            positive=is_positive,
            comment=comment
        )
        
        return "✅ Thank you for your feedback!" if success else "❌ Error recording feedback."
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error: {str(e)}"

# Database functions for admin panel
def get_db_connection():
    """Get a connection to the SQLite database"""
    import os
    
    if not os.path.exists(DB_PATH):
        return None
    
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()

def get_feedback_statistics():
    """Get statistics about feedback"""
    session = get_db_connection()
    if not session:
        return "No feedback database found."
    
    try:
        # Get total count
        total_count = session.execute(text("SELECT COUNT(*) FROM feedback")).scalar()
        
        if total_count == 0:
            session.close()
            return "No feedback has been recorded yet."
        
        # Get positive count
        positive_count = session.execute(text("SELECT COUNT(*) FROM feedback WHERE positive = 1")).scalar()
        
        # Get negative count 
        negative_count = session.execute(text("SELECT COUNT(*) FROM feedback WHERE positive = 0")).scalar()
        
        # Get book vs movie breakdown
        book_count = session.execute(text("SELECT COUNT(*) FROM feedback WHERE media_type = 'Book'")).scalar()
        movie_count = session.execute(text("SELECT COUNT(*) FROM feedback WHERE media_type = 'Movie'")).scalar()
        
        # Calculate percentages
        positive_percentage = round((positive_count / total_count) * 100, 1) if total_count > 0 else 0
        
        # Format the results as HTML
        stats_html = f"""
        <div style="padding: 15px; background-color: #f5f5f5; border-radius: 10px; margin-bottom: 20px;">
            <h3>Feedback Statistics</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                <div style="background-color: #e9f7fe; padding: 10px; border-radius: 8px;">
                    <strong>Total Feedback:</strong> {total_count}
                </div>
                <div style="background-color: #e5f9e0; padding: 10px; border-radius: 8px;">
                    <strong>Positive Feedback:</strong> {positive_count} ({positive_percentage}%)
                </div>
                <div style="background-color: #feeae9; padding: 10px; border-radius: 8px;">
                    <strong>Negative Feedback:</strong> {negative_count} ({100 - positive_percentage}%)
                </div>
                <div style="background-color: #f0e6fa; padding: 10px; border-radius: 8px;">
                    <strong>Media Type:</strong> {book_count} Books, {movie_count} Movies
                </div>
            </div>
        </div>
        """
        
        session.close()
        return stats_html
    except Exception as e:
        if session:
            session.close()
        return f"Error retrieving statistics: {str(e)}"

def get_recent_feedback(count=10):
    """Get most recent feedback with comments"""
    session = get_db_connection()
    if not session:
        return "No feedback database found."
    
    try:
        # First check if the comment column exists in the table
        # This handles backwards compatibility with older database versions
        inspector = inspect(session.bind)
        columns = [col['name'] for col in inspector.get_columns('feedback')]
        has_comment_field = 'comment' in columns
        
        # Use dynamic SQL based on available columns
        if has_comment_field:
            query = f"""SELECT title, media_type, positive, comment, timestamp 
                    FROM feedback 
                    ORDER BY timestamp DESC 
                    LIMIT {count}"""
        else:
            # For older databases without comment field
            query = f"""SELECT title, media_type, positive, timestamp 
                    FROM feedback 
                    ORDER BY timestamp DESC 
                    LIMIT {count}"""
        
        results = session.execute(text(query)).fetchall()
        
        if not results:
            session.close()
            return "No feedback found."
        
        # Format the results as HTML
        feedback_html = '<div style="margin-top: 20px;"><h3>Recent Feedback</h3>'
        
        for item in results:
            if has_comment_field:
                title, media_type, positive, comment, timestamp = item
            else:
                title, media_type, positive, timestamp = item
                comment = None  # No comment column in older databases
                
            sentiment = "👍 Positive" if positive else "👎 Negative"
            comment_text = comment if comment else "No additional comments"
            
            # Format timestamp
            if isinstance(timestamp, str):
                # Parse timestamp if it's a string
                try:
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = timestamp
            else:
                # Format datetime object
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
            
            # Create card for each feedback
            feedback_html += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 8px; 
                        background-color: {"#f7fff7" if positive else "#fff7f7"}">
                <div><strong>{title}</strong> ({media_type}) - {sentiment}</div>
                <div style="margin-top: 8px; font-style: italic;">"{comment_text}"</div>
                <div style="margin-top: 5px; font-size: 0.8em; color: #666;">{formatted_time}</div>
            </div>
            """
        
        feedback_html += '</div>'
        session.close()
        return feedback_html
    
    except Exception as e:
        if session:
            session.close()
        return f"Error retrieving feedback: {str(e)}"

# Admin login function
def admin_login(password):
    """Verify admin password and load statistics if correct"""
    # Generate hash for comparison
    admin_password_hash = hashlib.sha256("insight_admin_2025".encode()).hexdigest()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != admin_password_hash:
        time.sleep(1)  # Small delay to prevent brute force
        return "❌ Incorrect password. Access denied.", gr.update(visible=False)
    
    # Password correct, show stats section
    return "✅ Access granted. Viewing feedback data.", gr.update(visible=True)

# Function to refresh statistics
def refresh_stats():
    """Get fresh statistics"""
    stats = get_feedback_statistics()
    comments = get_recent_feedback()
    return stats, comments

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
        
        # Audio player for text-to-speech - initially hidden
        with gr.Group(visible=False) as audio_group:
            audio_button = gr.Button("🔊 Listen to Insights", variant="secondary")
            audio_player = gr.Audio(label="", type="filepath", interactive=False)
        
        # Feedback controls - initially hidden
        with gr.Group(visible=False) as feedback_group:
            gr.Markdown("<h4 class='section-heading'>Was this helpful?</h4>")
            
            # Thumbs up/down buttons
            with gr.Row():
                thumbs_up = gr.Button("👍 Helpful", variant="secondary")
                thumbs_down = gr.Button("👎 Could be better", variant="secondary")
            
            # Feedback form (initially hidden)
            with gr.Group(visible=False) as comment_group:
                feedback_text = gr.Textbox(
                    label="Your comments",
                    placeholder="Please share any specific feedback (optional)",
                    lines=2
                )
                
                # Store whether feedback was positive or negative
                is_positive = gr.State(True)
                
                submit_button = gr.Button("Submit Feedback", variant="primary")
            
            feedback_status = gr.Markdown("")

    # Footer
    gr.Markdown("""
    <div style='text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(128, 128, 128, 0.2);'>
        <p class='footer-text' style='margin-top: 1rem; font-size: 0.8em;'>Created by William Zhu | <a href='https://www.linkedin.com/in/william-wei-zhu/' target='_blank'>LinkedIn page</a> | <a href='https://william-wei-zhu.github.io/' target='_blank'>Personal Website</a></p>
        <p class='footer-text' style='font-size: 0.7em;'>All rights reserved.</p>
    </div>
    """)
        
    # Settings section moved to footer as requested
    with gr.Accordion("Settings", open=False):
        with gr.Group():
            gr.Markdown("<h3 class='section-heading'>Select the AI engine to power your insights</h3>")
            
            with gr.Row():
                provider_dropdown = gr.Dropdown(
                    label="",
                    choices=["OpenAI (GPT-4o)", "Claude 3.5 Haiku"],
                    value="OpenAI (GPT-4o)"
                )
                provider_button = gr.Button("Switch Engine", size="sm")
            
            provider_status = gr.Markdown(value="Using OpenAI (GPT-4o)")

    # Connect UI components to functions
    insight_button.click(
        fn=generate_insights,
        inputs=[media_title, media_type],
        outputs=[insight_output, feedback_group, audio_group]
    )
    
    # Connect audio button to text-to-speech function
    audio_button.click(
        fn=insights_to_speech,
        inputs=[insight_output],
        outputs=[audio_player]
    )
    
    # Update state when thumbs up is clicked
    thumbs_up.click(
        fn=lambda: True,  # Set positive feedback flag to True
        outputs=[is_positive]
    ).then(
        fn=record_positive,
        inputs=[media_title, media_type, insight_output],
        outputs=[feedback_status, comment_group, feedback_text]
    )
    
    # Update state when thumbs down is clicked
    thumbs_down.click(
        fn=lambda: False,  # Set positive feedback flag to False
        outputs=[is_positive]
    ).then(
        fn=record_negative,
        inputs=[media_title, media_type, insight_output],
        outputs=[feedback_status, comment_group, feedback_text]
    )
    
    # Submit feedback with comment
    submit_button.click(
        fn=submit_feedback,
        inputs=[media_title, media_type, insight_output, is_positive, feedback_text],
        outputs=[feedback_status]
    )
    
    # Connect provider switch button
    provider_button.click(
        fn=switch_provider,
        inputs=[provider_dropdown],
        outputs=[provider_status]
    )

# Create admin panel interface
with gr.Blocks(title="Admin Panel", theme=theme, css=custom_css) as admin_panel:
    gr.Markdown("<h2>Admin Panel</h2>")
    
    # Login section
    with gr.Group():
        admin_password = gr.Textbox(
            type="password", 
            label="Password",
            placeholder="Enter admin password"
        )
        login_button = gr.Button("Login", variant="primary")
        login_message = gr.Markdown("")
    
    # Stats and feedback display (initially hidden)
    with gr.Group(visible=False) as stats_section:
        refresh_button = gr.Button("Refresh Data", variant="secondary")
        
        # Statistics display
        stats_display = gr.HTML(get_feedback_statistics())
        
        # Recent feedback display
        feedback_display = gr.HTML(get_recent_feedback())
    
    # Connect login button
    login_button.click(
        fn=admin_login,
        inputs=[admin_password],
        outputs=[login_message, stats_section]
    )
    
    # Connect refresh button
    refresh_button.click(
        fn=refresh_stats,
        outputs=[stats_display, feedback_display]
    )

# Combined interface
app = gr.TabbedInterface(
    [demo, admin_panel],
    ["Insight Facilitator", "Admin"],
    theme=theme,
    css=custom_css
)

# Launch the app
if __name__ == "__main__":
    import os
    # Check if running on Hugging Face Spaces
    if "SPACE_ID" in os.environ:
        app.launch()
    else:
        # Running locally
        app.launch(share=False)
