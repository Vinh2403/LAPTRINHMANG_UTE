# tools/custom_tool.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import subprocess
from typing import Type, Any, Dict, Optional
import os

class ReconToolInput(BaseModel):
    """Input schema for ReconTool."""
    target: str = Field(..., description="The target URL or domain for the reconnaissance tool.")
    custom_params: Optional[Dict[str, str]] = Field(default=None, description="Custom parameters to override default tool settings.")

class ReconTool(BaseTool):
    """A custom tool for executing reconnaissance commands with retry logic."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    args_schema: Type[BaseModel] = ReconToolInput
    command: str = Field(..., description="The command template to execute")
    tool_name: str = Field(..., description="The name of the tool for error reporting")
    writes_to_file: bool = Field(default=False, description="Whether the tool writes its primary output to a file.")
    output_file_template: str = Field(default="", description="Template for the output file name, e.g., dirsearch_{target}.txt")
    max_retries: int = Field(default=2, description="Maximum number of retry attempts")
    retry_config: Dict[str, list] = Field(default_factory=dict, description="Tool-specific retry configurations")

    def __init__(self, **data):
        super().__init__(**data)
        # Define retry configurations for specific tools
        self.retry_config = {
            "Directory Enumeration": [
                {"threads": "10", "timeout": "700"},
                {"threads": "5", "timeout": "900"}
            ],
            "Nmap Scan": [
                {"flags": "-T3 -Pn"},
                {"flags": "-T2 -Pn"}
            ],
            "DNS Recon": [
                {"timeout": "700"},
                {"timeout": "900"}
            ]
        }

    def _run(self, target: str, custom_params: Optional[Dict[str, str]] = None) -> str:
        """Execute the reconnaissance command with retries on failure."""
        attempt = 0
        current_command = self.command
        timeout = 600  # Default timeout (10 minutes)

        while attempt <= self.max_retries:
            actual_output_file = None
            try:
                if self.writes_to_file and self.output_file_template:
                    safe_target_name = target.replace("http://", "").replace("https://", "").replace("/", "_")
                    actual_output_file = self.output_file_template.format(target=safe_target_name)
                    current_command = current_command.format(target=target, output_file=actual_output_file)
                else:
                    current_command = current_command.format(target=target)

                # Apply custom parameters or retry config
                if attempt > 0 and self.tool_name in self.retry_config:
                    retry_params = self.retry_config[self.tool_name][min(attempt - 1, len(self.retry_config[self.tool_name]) - 1)]
                    for key, value in retry_params.items():
                        if key == "threads" and "dirsearch" in current_command:
                            current_command = current_command.replace("--threads=10", f"--threads={value}")
                        elif key == "timeout":
                            timeout = int(value)
                        elif key == "flags" and "nmap" in current_command:
                            current_command = current_command.replace("-T4 -Pn", value)
                elif custom_params:
                    for key, value in custom_params.items():
                        current_command = current_command.replace(f"--{key}", f"--{key}={value}")

                result = subprocess.run(
                    current_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                output_content = ""
                if result.stdout:
                    output_content += f"STDOUT:\n{result.stdout}\n"
                if result.stderr and result.returncode != 0:
                    output_content += f"STDERR:\n{result.stderr}\n"

                if self.writes_to_file and actual_output_file and os.path.exists(actual_output_file):
                    with open(actual_output_file, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                    output_content += f"\n--- Content from {actual_output_file} ---\n{file_content}"
                    try:
                        os.remove(actual_output_file)
                    except OSError as e:
                        output_content += f"\nWarning: Could not remove {actual_output_file}: {e}"

                if result.returncode != 0:
                    if attempt < self.max_retries:
                        attempt += 1
                        output_content += f"\nRetrying {self.tool_name} (Attempt {attempt + 1}/{self.max_retries + 1})..."
                        continue
                    return f"Error executing {self.tool_name} after {self.max_retries + 1} attempts (Command: {current_command}):\n{output_content}"

                return output_content or "No output"

            except subprocess.TimeoutExpired:
                if attempt < self.max_retries:
                    attempt += 1
                    output_content = f"Timeout on attempt {attempt}/{self.max_retries + 1} for {self.tool_name}. Retrying..."
                    continue
                return f"Error: {self.tool_name} (Command: {current_command}) timed out after {self.max_retries + 1} attempts"
            except Exception as e:
                return f"Error executing {self.tool_name} (Command: {current_command}): {str(e)}"
            finally:
                if self.writes_to_file and actual_output_file and os.path.exists(actual_output_file):
                    try:
                        os.remove(actual_output_file)
                    except OSError:
                        pass

        return f"Failed to execute {self.tool_name} after {self.max_retries + 1} attempts"