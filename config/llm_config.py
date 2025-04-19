"""
Centralized LLM configuration module.
This module provides a unified way to configure and access LLM instances across the application.
Supports both AWS Bedrock (Claude) and OpenAI (GPT) models.
"""

import os
from dotenv import load_dotenv
from crewai import LLM

# Load environment variables - only needs to happen once
load_dotenv()

def are_aws_credentials_valid():
    """Check if AWS credentials are properly configured."""
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region_name = os.getenv('AWS_REGION_NAME')
    
    # Check if credentials are set and not the placeholder values
    if (aws_access_key_id and aws_secret_access_key and aws_region_name and
        aws_access_key_id != 'your_access_key_id' and
        aws_secret_access_key != 'your_secret_access_key'):
        return True
    return False

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
        provider: The LLM provider to use. Options: "bedrock", "openai", or "auto".
                 If "auto", will try Bedrock first, then fall back to OpenAI if Bedrock credentials are invalid.
        model_name: Optional override for the model name.
                   If None, uses the default model based on the provider.
        verbose: Whether to print verbose information about the LLM configuration.
        
    Returns:
        A configured LLM instance.
    """
    # Default model names
    DEFAULT_BEDROCK_MODEL = "bedrock/anthropic.claude-3-haiku-20240307-v1:0"
    DEFAULT_OPENAI_MODEL = "openai/gpt-4o"
    
    # Handle auto provider selection
    if provider == "auto":
        if is_openai_api_key_valid():
            provider = "openai"
        elif are_aws_credentials_valid():
            provider = "bedrock"
        else:
            error_message = "No valid LLM configuration found. Please configure OpenAI or AWS Bedrock credentials in the .env file."
            if verbose:
                print(error_message)
            raise ValueError(error_message)
    
    # Configure LLM based on provider
    if provider == "bedrock":
        if not are_aws_credentials_valid():
            error_message = "AWS Bedrock credentials not properly configured. Please check your .env file."
            if verbose:
                print(error_message)
            raise ValueError(error_message)
            
        # Use the specified model or the default
        bedrock_model = model_name or DEFAULT_BEDROCK_MODEL
        
        if verbose:
            print(f"Using AWS Bedrock LLM with provided credentials ({bedrock_model})")
        
        return LLM(
            model=bedrock_model,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_region_name=os.getenv('AWS_REGION_NAME')
        )
    
    elif provider == "openai":
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
    
    else:
        error_message = f"Invalid provider: {provider}. Supported providers are 'bedrock', 'openai', or 'auto'."
        if verbose:
            print(error_message)
        raise ValueError(error_message)
