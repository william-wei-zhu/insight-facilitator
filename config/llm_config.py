"""
Centralized LLM configuration module.
This module provides a unified way to configure and access OpenAI GPT-4o across the application.
Optimized for Hugging Face Spaces deployment.
"""

import os
from dotenv import load_dotenv
from crewai import LLM

# Load environment variables - only needs to happen once
load_dotenv()



def is_openai_api_key_valid():
    """Check if OpenAI API key is properly configured."""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    # Check if API key is set and not a placeholder value
    if openai_api_key and openai_api_key != 'your_openai_api_key':
        return True
    return False

def get_llm(provider="openai", model_name=None, verbose=False):
    """
    Get a configured LLM instance.
    
    Args:
        provider: Currently only supports "openai".
        model_name: Optional override for the model name.
                   If None, uses the default model.
        verbose: Whether to print verbose information about the LLM configuration.
        
    Returns:
        A configured LLM instance.
    """
    # Default model for Hugging Face compatibility
    DEFAULT_OPENAI_MODEL = "openai/gpt-4.1-nano"
    
    # Handle provider selection
    if provider != "openai":
        provider = "openai"
        if verbose:
            print(f"Only OpenAI provider is supported. Using OpenAI.")
    
    # Configure OpenAI LLM
    if not is_openai_api_key_valid():
        error_message = "OpenAI API key not properly configured. Please check your .env file."
        if verbose:
            print(error_message)
        raise ValueError(error_message)
    
    # Use the specified model or the default
    openai_model = model_name or DEFAULT_OPENAI_MODEL
    
    if verbose:
        print(f"Using OpenAI LLM with provided API key ({openai_model})")
    
    # Set the OpenAI API key in the environment
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
    
    # Create the LLM with OpenAI provider
    try:
        # Set the OpenAI API key directly in the environment
        os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
        
        # Configure the LLM with OpenAI using the format from documentation
        # The model parameter should include the provider prefix: "openai/model-name"
        llm = LLM(
            model=openai_model,  # Already includes "openai/" prefix
            temperature=0.7,
            max_tokens=1000
        )
        
        if verbose:
            print("OpenAI LLM initialized successfully")
        return llm
    except Exception as e:
        error_message = f"Error initializing OpenAI LLM: {str(e)}"
        if verbose:
            print(error_message)
        raise ValueError(error_message)
