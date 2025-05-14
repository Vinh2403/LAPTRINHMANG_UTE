# crew.py
from crewai import Agent, Crew, Process, Task
from tools.custom_tool import ReconTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import validators
import shutil
from typing import List

load_dotenv()

class ReconCrew:
    """Reconnaissance Crew for Security Analysis"""
    def __init__(self, target_url: str):
        if not validators.url(f"https://{target_url}") and not validators.url(f"http://{target_url}"):
            # Sửa lỗi: nếu target_url đã có http/https, validators.url sẽ báo lỗi
            # Nên kiểm tra target_url trực tiếp hoặc chuẩn hóa trước khi kiểm tra
            test_url = target_url if target_url.startswith(("http://", "https://")) else f"http://{target_url}"
            if not validators.url(test_url):
                 raise ValueError(f"Invalid URL: {target_url}")
        self.target_url = target_url.rstrip("/") # target_url này là domain, ví dụ example.com

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in .env file")

        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model="deepseek/deepseek-chat",
            temperature=0.3 # Giảm temperature để output ổn định hơn cho việc phân tích
        )

        self.required_tools = ["whois", "dnsrecon", "sublist3r", "nmap", "dirsearch", "whatweb"]
        self.check_tools()

    def check_tools(self):
        missing_tools = []
        for tool in self.required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        if missing_tools:
            raise EnvironmentError(f"Missing tools: {', '.join(missing_tools)}. Please install them.")

    # --- AGENTS ---
    def whois_agent(self) -> Agent:
        return Agent(
            role="WHOIS Information Specialist",
            goal=f"Gather comprehensive domain registration and ownership information for {self.target_url}, and extract key entities (Registrant, Admin, Tech contacts).",
            backstory="Expert in domain registration analysis and WHOIS data interpretation, skilled at identifying crucial contact and organizational details.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WHOIS Lookup",
                    description=f"Fetches WHOIS information for a domain {self.target_url}.",
                    command="whois {target}", # {target} sẽ là self.target_url
                    tool_name="WHOIS Lookup"
                )
            ],
            allow_delegation=False
        )

    def dns_agent(self) -> Agent:
        return Agent(
            role="DNS Enumeration Specialist",
            goal=f"Discover and analyze DNS records (A, AAAA, MX, NS, TXT, CNAME, SOA) for {self.target_url} to map its network infrastructure.",
            backstory="Expert in DNS analysis and record enumeration, capable of identifying potential misconfigurations or interesting service endpoints.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="DNS Recon",
                    description=f"Enumerates DNS records for {self.target_url}.",
                    command="dnsrecon -d {target} -a -s -x --json", # Thêm --json để output có cấu trúc hơn nếu tool hỗ trợ
                    tool_name="DNS Recon"
                )
            ],
            allow_delegation=False
        )

    def subdomain_agent(self) -> Agent:
        return Agent(
            role="Subdomain Discovery Specialist",
            goal=f"Find all active subdomains of {self.target_url} and verify their accessibility.",
            backstory="Expert in subdomain enumeration and discovery techniques, including brute-forcing and OSINT.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Subdomain Enumeration",
                    description=f"Discovers subdomains for {self.target_url}.",
                    command="sublist3r -d {target} -o sublist3r_output_{target}.txt", # Ghi ra file để có thể đọc lại nếu cần
                    tool_name="Subdomain Enumeration",
                    writes_to_file=True, # Đánh dấu tool này ghi ra file
                    output_file_template="sublist3r_output_{target}.txt" # Mẫu tên file
                )
            ],
            allow_delegation=False
        )

    def port_scan_agent(self) -> Agent:
        return Agent(
            role="Network Port Scanning Specialist",
            goal=f"Identify open TCP/UDP ports, running services, and their versions on {self.target_url}. If subdomains are known, consider them for scanning if explicitly instructed.",
            backstory="Expert in network scanning and service identification using Nmap, focusing on accuracy and thoroughness.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Nmap Scan",
                    description=f"Scans ports and services on {self.target_url}. Can also scan specific subdomains if provided in the target.",
                    # Nmap có thể quét nhiều target, nhưng để đơn giản, ta vẫn truyền target chính.
                    # Việc quét subdomain sẽ được quyết định bởi logic của task/agent hoặc task tổng hợp.
                    command="nmap -sV -sC -T4 -Pn {target}", # -Pn để bỏ qua host discovery, -T4 để nhanh hơn
                    tool_name="Nmap Scan"
                )
            ],
            allow_delegation=False
        )

    def directory_agent(self) -> Agent:
        return Agent(
            role="Web Directory Enumeration Specialist",
            goal=f"Discover hidden or common directories and files on web servers hosted at https://{self.target_url}.",
            backstory="Expert in web directory enumeration, using wordlists and common patterns to find accessible paths.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Directory Enumeration",
                    description=f"Enumerates directories on a web server at https://{self.target_url}. Ensure the output file is specified in the command.",
                    # {output_file} sẽ được ReconTool thay thế
                    command="dirsearch -u https://{target} -o {output_file} --force-extensions -e php,asp,aspx,jsp,html,js,txt,bak,config,yml,yaml -r",
                    tool_name="Directory Enumeration",
                    writes_to_file=True, # Đánh dấu tool này ghi ra file
                    output_file_template="dirsearch_output_{target}.txt" # Mẫu tên file
                )
            ],
            allow_delegation=False
        )

    def tech_stack_agent(self) -> Agent:
        return Agent(
            role="Technology Stack Analyst",
            goal=f"Identify web technologies, frameworks, CMS, server software, and programming languages used by https://{self.target_url}.",
            backstory="Expert in web technology identification and analysis using tools like WhatWeb.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WhatWeb Scan",
                    description=f"Identifies technologies used by the website https://{self.target_url}.",
                    command="whatweb -a 3 https://{target}", # -a 3 for aggression level
                    tool_name="WhatWeb Scan"
                )
            ],
            allow_delegation=False
        )

    def reporting_agent(self) -> Agent: # AGENT MỚI
        return Agent(
            role="Lead Security Analyst and Report Synthesizer",
            goal=f"Compile, analyze, and synthesize all reconnaissance findings for {self.target_url} into a comprehensive, structured security report. Highlight key vulnerabilities, misconfigurations, and provide actionable recommendations.",
            backstory="An experienced security analyst skilled at interpreting diverse reconnaissance data (WHOIS, DNS, Subdomains, Ports, Directories, Tech Stack), correlating findings, and producing clear, actionable intelligence reports.",
            verbose=True,
            llm=self.llm,
            tools=[], # Agent này không dùng tool ngoài, chỉ dùng LLM để phân tích
            allow_delegation=False
        )

    # --- TASKS ---
    # Các task sẽ được thực thi tuần tự, output của task trước sẽ có trong context của task sau
    def whois_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Execute a WHOIS lookup for the domain '{self.target_url}'. Extract and list the registrant organization, admin contact, and tech contact if available. Summarize key findings.",
            agent=agent,
            expected_output=f"A summary of key WHOIS information for {self.target_url}, including registrant, admin, and tech contacts, and any notable registration details."
        )

    def dns_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Perform DNS enumeration for '{self.target_url}'. List all discovered A, AAAA, MX, NS, TXT, CNAME, and SOA records. Analyze for any unusual or potentially vulnerable configurations.",
            agent=agent,
            expected_output=f"A comprehensive list of DNS records for {self.target_url}, with analysis of potential security implications or interesting findings (e.g., SPF/DKIM/DMARC records, mail servers, nameservers)."
            # context=[self.whois_task] # Có thể thêm context nếu muốn, nhưng ở đây không quá cần thiết
        )

    def subdomain_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Discover all publicly accessible subdomains for the domain '{self.target_url}'. Provide a list of found subdomains. Verify their accessibility.",
            agent=agent,
            expected_output=f"A list of discovered subdomains for {self.target_url}. For each subdomain, note if it's accessible (e.g., resolves to an IP and responds to HTTP/HTTPS).",
            context=[self.dns_task(self.dns_agent())] # DNS task có thể cung cấp manh mối cho subdomains
        )

    def port_scan_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Conduct a port scan on the primary domain '{self.target_url}'. Identify open TCP ports, the services running on them, and their versions. Analyze for any outdated or vulnerable services based on version information. If the previous task (subdomain discovery) found critical subdomains, briefly mention if they should be considered for deeper scans later.",
            agent=agent,
            expected_output=f"Detailed port scan results for {self.target_url} (IP address resolved from the domain), including open ports, service names, and versions. Highlight any services known for vulnerabilities or common misconfigurations. Mention if subdomains data from context suggests further scanning targets.",
            context=[self.subdomain_task(self.subdomain_agent())] # Output của subdomain_task sẽ có trong context
        )

    def directory_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Enumerate web directories and files for 'https://{self.target_url}'. Identify any interesting or potentially sensitive paths (e.g., admin panels, backup files, exposed configuration files, common framework paths like /wp-admin, .git).",
            agent=agent,
            expected_output=f"A list of discovered directories and files on https://{self.target_url} with their HTTP status codes. Highlight any paths that seem sensitive, are related to known frameworks, or might indicate information leakage.",
            context=[self.tech_stack_task(self.tech_stack_agent())] # Tech stack có thể gợi ý các path đặc trưng
        )

    def tech_stack_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Identify the technology stack (web server, backend languages, frameworks, CMS, JavaScript libraries, etc.) for 'https://{self.target_url}'. Correlate findings with common vulnerabilities associated with the identified technologies.",
            agent=agent,
            expected_output=f"A detailed list of technologies, frameworks, and software versions used by https://{self.target_url}. Include any known vulnerabilities or security considerations for the identified stack.",
            # context=[self.port_scan_task(self.port_scan_agent())] # Port scan có thể tiết lộ server software
        )

    def reporting_task(self, agent: Agent, all_tasks: List[Task]) -> Task: # TASK MỚI
        return Task(
            description=f"""
Compile and synthesize all reconnaissance data gathered for '{self.target_url}'.
The data includes:
- WHOIS Information
- DNS Records
- Discovered Subdomains
- Open Ports and Services
- Web Directories and Files
- Technology Stack

Analyze this consolidated information to:
1.  Provide a concise executive summary of the reconnaissance.
2.  Identify potential attack vectors or key areas of security concern.
3.  List any specific vulnerabilities or misconfigurations suggested by the tool outputs (e.g., outdated software versions, exposed sensitive paths, weak DNS configurations).
4.  Suggest actionable security recommendations based on the findings.
5.  Structure the final output in clear, well-organized Markdown format.
Use the context from all previous tasks.
            """,
            agent=agent,
            expected_output=f"A comprehensive and structured Markdown report detailing all reconnaissance findings for {self.target_url}, including an executive summary, identified potential vulnerabilities, and actionable security recommendations. The report should be easy to read and understand.",
            context=all_tasks # Cung cấp context từ tất cả các task trước đó
        )

    def create_crew(self) -> Crew:
        """Creates the Reconnaissance crew"""
        # Khởi tạo agents
        _whois_agent = self.whois_agent()
        _dns_agent = self.dns_agent()
        _subdomain_agent = self.subdomain_agent()
        _port_scan_agent = self.port_scan_agent()
        _directory_agent = self.directory_agent()
        _tech_stack_agent = self.tech_stack_agent()
        _reporting_agent = self.reporting_agent()

        # Khởi tạo tasks
        # Lưu ý: khi task A cần context từ task B, task B phải được định nghĩa trước
        # và truyền vào context của task A.
        # Thứ tự trong list `tasks` của Crew sẽ quyết định thứ tự thực thi.

        task_whois = self.whois_task(_whois_agent)
        task_dns = self.dns_task(_dns_agent)
        task_subdomain = self.subdomain_task(_subdomain_agent)
        # Để tech_stack chạy trước directory, vì tech_stack có thể cung cấp thông tin hữu ích cho directory_task
        task_tech_stack = self.tech_stack_task(_tech_stack_agent)
        task_port_scan = self.port_scan_task(_port_scan_agent)
        task_directory = self.directory_task(_directory_agent)
        
        # Danh sách các task thu thập thông tin cho reporting_task
        recon_tasks = [
            task_whois,
            task_dns,
            task_subdomain,
            task_tech_stack, # Đã chạy trước port_scan và directory
            task_port_scan,
            task_directory
        ]
        
        task_report = self.reporting_task(_reporting_agent, recon_tasks)

        all_crew_tasks = recon_tasks + [task_report]

        return Crew(
            agents=[
                _whois_agent,
                _dns_agent,
                _subdomain_agent,
                _tech_stack_agent, # Cập nhật thứ tự agent nếu cần khớp với task
                _port_scan_agent,
                _directory_agent,
                _reporting_agent
            ],
            tasks=all_crew_tasks,
            process=Process.sequential,
            verbose=True, # verbose=2 để xem chi tiết hơn quá trình làm việc của agent
            llm=self.llm,
            # memory=True # Bật memory nếu bạn muốn crew ghi nhớ các tương tác dài hạn hơn qua nhiều lần kickoff (cẩn thận về token usage)
        )