# Testapi Crew

Welcome to the Testapi Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/testapi/config/agents.yaml` to define your agents
- Modify `src/testapi/config/tasks.yaml` to define your tasks
- Modify `src/testapi/crew.py` to add your own logic, tools and specific args
- Modify `src/testapi/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the testapi Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The testapi Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the Testapi Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
----------------------
Flow trong chương trình:
Luồng hoạt động tổng quan:
Khởi chạy (main.py):
Người dùng chạy python3 main.py.
Chương trình yêu cầu nhập target URL/domain.
Input được chuẩn hóa thành một domain thuần túy (ví dụ: example.com hoặc grok.com).
Khởi tạo ReconCrew (crew.py):
Một instance của ReconCrew được tạo với domain đã chuẩn hóa.
Trong ReconCrew.__init__:
Kiểm tra biến môi trường DEEPSEEK_API_KEY.
Khởi tạo LLM (ChatOpenAI với DeepSeek).
Kiểm tra xem các tool hệ thống cần thiết (whois, dnsrecon, nmap, v.v.) có được cài đặt không.
Tạo Crew (ReconCrew.create_crew()):
Phương thức này được gọi để thiết lập toàn bộ "đội quân" agent và các nhiệm vụ của họ.
Định nghĩa Agents:
Từng agent chuyên biệt (WHOIS, DNS, Subdomain, Port Scan, Directory, Tech Stack, Reporting) được khởi tạo.
Mỗi agent có:
role: Vai trò.
goal: Mục tiêu cụ thể (thường liên quan đến self.target_url).
backstory: Mô tả kinh nghiệm.
llm: LLM đã khởi tạo.
tools: Danh sách các ReconTool (hoặc không có tool nào cho Reporting Agent).
Mỗi ReconTool có name, description, command (template), tool_name, và các cờ như writes_to_file.
Định nghĩa Tasks:
Từng task cụ thể được khởi tạo.
Mỗi task có:
description: Mô tả chi tiết nhiệm vụ, thường bao gồm yêu cầu phân tích và self.target_url.
agent: Agent được gán cho task này.
expected_output: Mô tả kết quả mong đợi.
context (tùy chọn): Danh sách các task trước đó mà output của chúng sẽ được cung cấp làm thông tin nền cho task hiện tại.
Thứ tự Task quan trọng: Các task được sắp xếp theo một trình tự logic (ví dụ: thu thập thông tin cơ bản trước, sau đó đến các thông tin chi tiết hơn, và cuối cùng là báo cáo). reporting_task nhận context từ tất cả các task trinh sát trước đó.
Khởi tạo Crew:
Một đối tượng Crew được tạo với danh sách các agents và tasks đã định nghĩa.
process=Process.sequential: Các task sẽ được thực hiện tuần tự.
verbose=True: Bật logging chi tiết.
Thực thi Crew (crew.kickoff()):
Đây là lúc "phép màu" xảy ra.
Crew bắt đầu thực hiện các task theo thứ tự đã định.
Với mỗi Task:
Agent được kích hoạt: Agent được gán cho task hiện tại sẽ bắt đầu làm việc.
Agent Suy nghĩ (Thought Process):
Dựa trên goal của mình, description của task, expected_output, và context (nếu có từ các task trước), agent sẽ sử dụng LLM để suy nghĩ về cách hoàn thành nhiệm vụ.
Nó sẽ quyết định xem có cần sử dụng tool nào không.
Sử dụng Tool (Nếu cần):
Nếu agent quyết định dùng tool (ví dụ: "WHOIS Lookup"), nó sẽ "gọi" tool đó.
Chuẩn bị Tool Input: Agent sẽ tạo input cho tool (ví dụ: {"target": "grok.com"}).
Thực thi ReconTool._run() (custom_tool.py):
Input target từ agent được nhận.
ReconTool chuẩn hóa target thành domain thuần túy (nếu cần, nhờ code sửa lỗi của chúng ta).
command template được format với target đã chuẩn hóa và output_file (nếu writes_to_file=True).
Lệnh subprocess.run() được gọi để thực thi tool dòng lệnh trên hệ thống.
Output (stdout, stderr) từ tool được thu thập.
Nếu writes_to_file=True, ReconTool đọc nội dung từ file output và gộp vào kết quả, sau đó xóa file.
Kết quả (chuỗi string) được trả về cho agent.
Agent Nhận Tool Output:
Agent nhận kết quả từ ReconTool.
Agent Tiếp tục Suy nghĩ/Phân tích:
Agent (với sự trợ giúp của LLM) xem xét output của tool.
Nó có thể quyết định:
Đã đủ thông tin, đưa ra "Final Answer" cho task.
Cần chạy lại tool với tham số khác (ít xảy ra nếu tool input được thiết kế tốt).
Cần thêm bước suy nghĩ hoặc sử dụng tool khác (nếu agent có nhiều tool).
Quá trình này lặp lại (Thought -> Action -> Observation) cho đến khi agent có "Final Answer".
Task Hoàn thành: Output của "Final Answer" từ agent được lưu lại như là kết quả của task.
Luân chuyển Task: Sau khi một task hoàn thành, Crew chuyển sang task tiếp theo trong danh sách. Output của task vừa hoàn thành sẽ có sẵn trong context cho các task sau (nếu được định nghĩa).
Reporting Task: Task cuối cùng, reporting_task, sẽ nhận context từ tất cả các task trinh sát trước đó. Reporting Agent sẽ sử dụng LLM để tổng hợp, phân tích toàn bộ thông tin này và tạo ra một báo cáo cuối cùng.
Trả về Kết quả (main.py):
Phương thức crew.kickoff() trả về kết quả của task cuối cùng trong chuỗi (trong trường hợp này là báo cáo từ Reporting Agent).
main.py nhận kết quả này.
Kết quả được ghi ra file Markdown (ví dụ: recon_results_grok_com_YYYYMMDD_HHMMSS.md).
Kết quả cũng được in ra console.
Luồng dữ liệu quan trọng:
target_url (domain): Truyền từ main.py -> ReconCrew -> được sử dụng trong description của các Task và goal của Agent.
Output của Task: Kết quả của một task được lưu trữ và có thể được sử dụng làm context cho các task sau.
Tool Input/Output: Agent tạo input -> ReconTool nhận input, thực thi lệnh -> ReconTool trả output về cho Agent.
Sự phối hợp giữa các Agents:
Tuần tự và Context: Do process=Process.sequential và việc sử dụng context, các agent làm việc nối tiếp nhau. Agent sau có thể "học hỏi" hoặc sử dụng kết quả của agent trước.
Reporting Agent là trung tâm: Agent này đóng vai trò tổng hợp công việc của tất cả các agent trinh sát khác để tạo ra một cái nhìn toàn diện.
