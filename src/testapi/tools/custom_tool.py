from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import subprocess
from typing import Type, Any

class ReconToolInput(BaseModel):
    """Input schema for ReconTool."""
    target: str = Field(..., description="The target URL or domain for the reconnaissance tool.")

class ReconTool(BaseTool):
    """A custom tool for executing reconnaissance commands."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    args_schema: Type[BaseModel] = ReconToolInput
    command: str = Field(..., description="The command template to execute")
    tool_name: str = Field(..., description="The name of the tool for error reporting")

    def _run(self, target: str) -> str:
        """Execute the reconnaissance command with the provided target."""
        try:
            # Format the command with the target
            formatted_command = self.command.format(target=target)
            result = subprocess.run(
                formatted_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10-minute timeout
            )
            if result.returncode != 0:
                return f"Error executing {self.tool_name}: {result.stderr}"
            return result.stdout or "No output"
        except subprocess.TimeoutExpired:
            return f"Error: {self.tool_name} timed out after 10 minutes"
        except Exception as e:
            return f"Error executing {self.tool_name}: {str(e)}"