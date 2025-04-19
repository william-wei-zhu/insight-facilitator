import subprocess
import json
from typing import Dict, List, Optional, Any
from crewai.tools import BaseTool

class AWSCLITool(BaseTool):
    """Tool for interacting with AWS CLI."""
    
    name: str = "AWS CLI Tool"
    description: str = "Execute AWS CLI commands to interact with AWS services."
    
    def _run(self, command: str) -> str:
        """
        Execute an AWS CLI command.
        
        Args:
            command: The AWS CLI command to execute (without the 'aws' prefix).
            
        Returns:
            The output of the command as a string.
        """
        try:
            # Add 'aws' prefix to the command
            full_command = f"aws {command}"
            
            # Execute the command
            result = subprocess.run(
                full_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing AWS CLI command: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
