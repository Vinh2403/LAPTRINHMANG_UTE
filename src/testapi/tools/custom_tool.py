# tools/custom_tool.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import subprocess
from typing import Type, Any
import os # Thêm os để xử lý file

class ReconToolInput(BaseModel):
    """Input schema for ReconTool."""
    target: str = Field(..., description="The target URL or domain for the reconnaissance tool.")
    # Tùy chọn: Thêm tham số cho file output nếu cần thiết cho các tool khác
    # output_filename: Optional[str] = Field(None, description="Optional filename for tool output.")

class ReconTool(BaseTool):
    """A custom tool for executing reconnaissance commands."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    args_schema: Type[BaseModel] = ReconToolInput
    command: str = Field(..., description="The command template to execute")
    tool_name: str = Field(..., description="The name of the tool for error reporting")
    # Thêm cờ để biết tool này có ghi ra file không, và tên file là gì
    writes_to_file: bool = Field(default=False, description="Whether the tool writes its primary output to a file.")
    output_file_template: str = Field(default="", description="Template for the output file name, e.g., dirsearch_{target}.txt")


    def _run(self, target: str) -> str:
        """Execute the reconnaissance command with the provided target."""
        actual_output_file = None
        formatted_command = self.command # Khởi tạo formatted_command
 # --- DEBUGGING LINES ---
        print(f"--- ReconTool DEBUG ---")
        print(f"Tool Name: {self.tool_name}")
        print(f"Received target input by agent: '{target}'")
        # --- END DEBUGGING LINES ---
        try:
            if self.writes_to_file and self.output_file_template:
                # Tạo tên file output duy nhất để tránh ghi đè nếu chạy nhiều lần hoặc song song
                # (Mặc dù ở đây là sequential, nhưng đây là good practice)
                safe_target_name = target.replace("http://", "").replace("https://", "").replace("/", "_")
                actual_output_file = self.output_file_template.format(target=safe_target_name)
                # Cập nhật command để sử dụng tên file này
                # Giả sử tool dùng -o hoặc --output để chỉ định file
                # Bạn cần đảm bảo placeholder {output_file} có trong command template của dirsearch
                formatted_command = self.command.format(target=target, output_file=actual_output_file)
            else:
                formatted_command = self.command.format(target=target)

            result = subprocess.run(
                formatted_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10-minute timeout
            )

            output_content = ""
            if result.stdout:
                output_content += f"STDOUT:\n{result.stdout}\n"
            if result.stderr and result.returncode != 0: # Chỉ thêm stderr nếu có lỗi
                 output_content += f"STDERR:\n{result.stderr}\n"


            if self.writes_to_file and actual_output_file:
                if os.path.exists(actual_output_file):
                    with open(actual_output_file, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                    output_content += f"\n--- Content from {actual_output_file} ---\n{file_content}"
                    try:
                        os.remove(actual_output_file) # Dọn dẹp file sau khi đọc
                    except OSError as e:
                        output_content += f"\nWarning: Could not remove {actual_output_file}: {e}"
                else:
                    output_content += f"\nWarning: Output file {actual_output_file} was expected but not found."


            if result.returncode != 0:
                return f"Error executing {self.tool_name} (Command: {formatted_command}):\n{output_content}"

            return output_content or "No output"

        except subprocess.TimeoutExpired:
            return f"Error: {self.tool_name} (Command: {formatted_command}) timed out after 10 minutes"
        except Exception as e:
            return f"Error executing {self.tool_name} (Command: {formatted_command}): {str(e)}"
        finally:
            # Đảm bảo dọn dẹp file nếu có lỗi xảy ra trước khi đọc và xóa file
            if self.writes_to_file and actual_output_file and os.path.exists(actual_output_file):
                try:
                    os.remove(actual_output_file)
                except OSError:
                    pass # Ghi đè lỗi nếu đã có thông báo