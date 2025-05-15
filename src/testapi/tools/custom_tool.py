from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import subprocess
from typing import Type, Any, Dict, Optional
import os
import re
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReconToolInput(BaseModel):
    target: str = Field(..., description="Target URL or domain.")
    custom_params: Optional[Dict[str, str]] = Field(default=None, description="Custom parameters for tool settings.")

class ReconTool(BaseTool):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    args_schema: Type[BaseModel] = ReconToolInput
    command: str = Field(..., description="Command template")
    tool_name: str = Field(..., description="Tool name for errors")
    writes_to_file: bool = Field(default=False, description="Whether tool writes to file.")
    output_file_template: str = Field(default="", description="Output file name template")
    max_retries: int = Field(default=1, description="Maximum retry attempts on failure")

    def __init__(self, **data):
        super().__init__(**data)

    def _run(self, target: str, custom_params: Optional[Dict[str, str]] = None) -> str:
        # Tool-specific timeouts
        timeouts = {
            "dnsrecon": 300,  
            "nmap": 300,      
            "dirsearch": 300, 
        }
        timeout = 30  # Default for unrecognized tools
        for tool, tool_timeout in timeouts.items():
            if tool in self.command:
                timeout = tool_timeout
                break
        if custom_params and "timeout" in custom_params:
            try:
                timeout = int(custom_params["timeout"])
            except ValueError:
                return f"Error: Invalid timeout '{custom_params['timeout']}' for {self.tool_name}"

        original_command = self.command
        start_time = time.time()
        clean_target = re.sub(r'^https?://', '', target).rstrip('/')
        logging.info(f"Starting {self.tool_name} on {clean_target} (Command: {original_command}, Timeout: {timeout}s, Retries: {self.max_retries})")

        attempt = 0
        while attempt <= self.max_retries:
            actual_output_file = None
            current_command = original_command
            try:
                if self.writes_to_file and self.output_file_template:
                    safe_target_name = clean_target.replace("/", "_")
                    actual_output_file = self.output_file_template.format(target=safe_target_name)
                    current_command = current_command.format(target=clean_target, output_file=actual_output_file)
                else:
                    current_command = current_command.format(target=clean_target)

                applied_params = {}
                if custom_params:
                    for key, value in custom_params.items():
                        value = str(value)
                        if key == "timeout":
                            applied_params[key] = value
                        elif key == "threads" and "dirsearch" in self.command:
                            current_command = re.sub(r'--threads=\d+', f'--threads={value}', current_command)
                            applied_params[key] = value
                        elif key == "delay" and "dirsearch" in self.command:
                            current_command = re.sub(r'--delay=\d+', f'--delay={value}', current_command)
                            applied_params[key] = value
                        else:
                            current_command = current_command.replace(f"--{key}", f"--{key}={value}")
                            applied_params[key] = value
                elif "dirsearch" in self.command:
                    current_command = re.sub(r'--threads=\d+', '--threads=5', current_command)
                    current_command = re.sub(r'--delay=\d+', '--delay=500', current_command)
                    applied_params = {"threads": "5", "delay": "500"}

                logging.info(f"Attempt {attempt + 1}/{self.max_retries + 1} for {self.tool_name} on {clean_target}")
                result = subprocess.run(
                    current_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                output_content = f"Applied parameters: {applied_params}\n"
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
                    elapsed_time = time.time() - start_time
                    logging.warning(f"{self.tool_name} failed after {elapsed_time:.2f} seconds on attempt {attempt + 1}")
                    if attempt < self.max_retries:
                        attempt += 1
                        continue
                    return f"Error executing {self.tool_name} after {self.max_retries + 1} attempts (Command: {current_command}):\n{output_content}"

                elapsed_time = time.time() - start_time
                logging.info(f"{self.tool_name} completed in {elapsed_time:.2f} seconds on attempt {attempt + 1}")
                return output_content or "No output"

            except subprocess.TimeoutExpired:
                elapsed_time = time.time() - start_time
                logging.warning(f"{self.tool_name} timed out after {elapsed_time:.2f} seconds with timeout {timeout}s on attempt {attempt + 1}")
                if attempt < self.max_retries:
                    attempt += 1
                    continue
                return f"Error: {self.tool_name} (Command: {current_command}) timed out after {timeout}s on {self.max_retries + 1} attempts"
            except Exception as e:
                elapsed_time = time.time() - start_time
                logging.error(f"{self.tool_name} failed after {elapsed_time:.2f} seconds on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    attempt += 1
                    continue
                return f"Error executing {self.tool_name} (Command: {current_command}) after {self.max_retries + 1} attempts: {str(e)}"
            finally:
                if self.writes_to_file and actual_output_file and os.path.exists(actual_output_file):
                    try:
                        os.remove(actual_output_file)
                    except OSError:
                        pass