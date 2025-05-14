# crew.py
from crewai import Agent, Crew, Process, Task
from tools.custom_tool import ReconTool # Đảm bảo custom_tool.py đã được cập nhật như thảo luận
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import validators
import shutil
from typing import List

load_dotenv()

class ReconCrew:
    """Reconnaissance Crew for Security Analysis"""
    def __init__(self, domain: str): # Đổi tên target_url thành domain cho rõ ràng
        # `domain` ở đây nên là domain thuần túy, ví dụ: "example.com"
        # Việc chuẩn hóa từ URL đầy đủ sang domain nên được thực hiện ở main.py trước khi truyền vào đây
        if not domain or "." not in domain or " " in domain or "/" in domain or ":" in domain: # Kiểm tra domain đơn giản
             raise ValueError(f"Invalid domain format provided to ReconCrew: {domain}. Expected a bare domain like 'example.com'.")
        self.domain = domain # Lưu trữ domain thuần túy

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in .env file")

        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model="deepseek/deepseek-chat",
            temperature=0.2 # Giảm temperature hơn nữa để tăng tính tuân thủ
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
    # Các goal và description của tool sẽ nhấn mạnh việc sử dụng self.domain làm target cho tool
    # ReconTool của chúng ta cũng đã có logic để xử lý nếu agent có lỡ truyền https://

    def whois_agent(self) -> Agent:
        return Agent(
            role="WHOIS Information Specialist",
            goal=f"Gather comprehensive domain registration and ownership information for the domain '{self.domain}', and extract key entities (Registrant, Admin, Tech contacts).",
            backstory="Expert in domain registration analysis and WHOIS data interpretation, skilled at identifying crucial contact and organizational details.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WHOIS Lookup",
                    description=f"Fetches WHOIS information for a domain. The target should be the bare domain, like '{self.domain}'.",
                    command="whois {target}", # {target} sẽ là self.domain (được ReconTool xử lý)
                    tool_name="WHOIS Lookup"
                )
            ],
            allow_delegation=False
        )

    def dns_agent(self) -> Agent:
        return Agent(
            role="DNS Enumeration Specialist",
            goal=f"Discover and analyze DNS records (A, AAAA, MX, NS, TXT, CNAME, SOA) for the domain '{self.domain}' to map its network infrastructure.",
            backstory="Expert in DNS analysis and record enumeration, capable of identifying potential misconfigurations or interesting service endpoints.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="DNS Recon",
                    description=f"Enumerates DNS records for a domain. The target should be the bare domain, like '{self.domain}'. This tool may write output to a JSON file.",
                    command="dnsrecon -d {target} -a -s -j {output_file}", # dnsrecon dùng -j để chỉ định file JSON
                    tool_name="DNS Recon",
                    writes_to_file=True, # Đánh dấu tool này ghi ra file
                    output_file_template="dnsrecon_output_{target}.json" # Mẫu tên file
                )
            ],
            allow_delegation=False
        )

    def subdomain_agent(self) -> Agent:
        return Agent(
            role="Subdomain Discovery Specialist",
            goal=f"Find all active subdomains of the domain '{self.domain}' and verify their accessibility.",
            backstory="Expert in subdomain enumeration and discovery techniques, including brute-forcing and OSINT.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Subdomain Enumeration",
                    description=f"Discovers subdomains for a domain. The target should be the bare domain, like '{self.domain}'. This tool writes its output to a text file.",
                    command="sublist3r -d {target} -o {output_file}", # sublist3r dùng -o
                    tool_name="Subdomain Enumeration",
                    writes_to_file=True,
                    output_file_template="sublist3r_output_{target}.txt"
                )
            ],
            allow_delegation=False
        )

    def port_scan_agent(self) -> Agent:
        return Agent(
            role="Network Port Scanning Specialist",
            goal=f"Identify open TCP/UDP ports, running services, and their versions on the main IP address associated with the domain '{self.domain}'. If subdomains are known from context, mention if they warrant separate scans.",
            backstory="Expert in network scanning and service identification using Nmap, focusing on accuracy and thoroughness.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Nmap Scan",
                    description=f"Scans ports and services on a target. The target should be an IP address or a domain name like '{self.domain}'.",
                    command="nmap -sV -sC -T4 -Pn {target}",
                    tool_name="Nmap Scan"
                )
            ],
            allow_delegation=False
        )

    def directory_agent(self) -> Agent:
        return Agent(
            role="Web Directory Enumeration Specialist",
            goal=f"Discover hidden or common directories and files on web servers hosted at the domain '{self.domain}'. The tool will access it via 'https://{self.domain}'.",
            backstory="Expert in web directory enumeration, using wordlists and common patterns to find accessible paths.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Directory Enumeration",
                    description=f"Enumerates directories on a web server. "
                                f"CRITICAL: The 'target' argument for this tool MUST be the bare domain name (e.g., '{self.domain}'), not a full URL. "
                                f"The tool itself constructs the full URL (https://{self.domain}). This tool writes its output to a text file.",
                    command="dirsearch -u https://{target} -o {output_file} --force-extensions -e php,asp,aspx,jsp,html,js,txt,bak,config,yml,yaml -r -R 2", # Thêm -R 2 để theo redirect sâu hơn
                    tool_name="Directory Enumeration",
                    writes_to_file=True,
                    output_file_template="dirsearch_output_{target}.txt"
                )
            ],
            allow_delegation=False
        )

    def tech_stack_agent(self) -> Agent:
        return Agent(
            role="Technology Stack Analyst",
            goal=f"Identify web technologies, frameworks, CMS, server software, and programming languages used by the website at 'https://{self.domain}'.",
            backstory="Expert in web technology identification and analysis using tools like WhatWeb.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WhatWeb Scan",
                    description=f"Identifies technologies used by a website. The target should be the bare domain, like '{self.domain}'. The tool will access it via 'https://{self.domain}'.",
                    command="whatweb -a 3 https://{target}",
                    tool_name="WhatWeb Scan"
                )
            ],
            allow_delegation=False
        )

    def reporting_agent(self) -> Agent:
        return Agent(
            role="Lead Security Analyst and Report Synthesizer",
            goal=f"Compile, analyze, and synthesize all reconnaissance findings for the domain '{self.domain}' into a comprehensive, structured security report. Highlight key vulnerabilities, misconfigurations, and provide actionable recommendations.",
            backstory="An experienced security analyst skilled at interpreting diverse reconnaissance data (WHOIS, DNS, Subdomains, Ports, Directories, Tech Stack), correlating findings, and producing clear, actionable intelligence reports.",
            verbose=True,
            llm=self.llm,
            tools=[],
            allow_delegation=False
        )

    # --- TASKS ---
    def whois_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Execute a WHOIS lookup for the domain '{self.domain}'. Extract and list the registrant organization, admin contact, and tech contact if available. Summarize key findings.",
            agent=agent,
            expected_output=f"A summary of key WHOIS information for '{self.domain}', including registrant, admin, and tech contacts, and any notable registration details."
        )

    def dns_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Perform DNS enumeration for the domain '{self.domain}'. List all discovered A, AAAA, MX, NS, TXT, CNAME, and SOA records from the tool's output. Analyze for any unusual or potentially vulnerable configurations (e.g., missing SPF/DKIM/DMARC, exposed zone transfer).",
            agent=agent,
            expected_output=f"A comprehensive list and analysis of DNS records for '{self.domain}', highlighting potential security implications or interesting findings. Ensure the output is based on the tool's actual findings."
        )

    def subdomain_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Discover all publicly accessible subdomains for the domain '{self.domain}' using the provided tool. Provide a list of found subdomains. Verify their accessibility if possible from the tool output.",
            agent=agent,
            expected_output=f"A list of discovered subdomains for '{self.domain}' based on the tool's output. For each subdomain, note if it's accessible or any other relevant info from the tool.",
            context=[self.dns_task(self.dns_agent())]
        )

    def port_scan_task(self, agent: Agent) -> Task:
        # Port scan thường nhắm vào IP, agent cần hiểu điều này hoặc tool cần phân giải domain
        # Nmap tự phân giải domain, nên truyền domain là ổn
        return Task(
            description=f"Conduct a port scan on the domain '{self.domain}'. Identify open TCP ports, the services running on them, and their versions. Analyze for any outdated or vulnerable services based on version information from the tool's output. If the subdomain discovery task (from context) found many subdomains, focus this scan on the main domain '{self.domain}' unless specifically instructed otherwise by the overall goal.",
            agent=agent,
            expected_output=f"Detailed port scan results for '{self.domain}' (or its resolved IP), including open ports, service names, and versions. Highlight any services known for vulnerabilities or common misconfigurations based on the tool's output.",
            context=[self.subdomain_task(self.subdomain_agent())]
        )

    def tech_stack_task(self, agent: Agent) -> Task: # Chạy tech_stack trước directory
        return Task(
            description=f"Identify the technology stack (web server, backend languages, frameworks, CMS, JavaScript libraries, etc.) for the website at 'https://{self.domain}' using the provided tool. Correlate findings with common vulnerabilities associated with the identified technologies based on the tool's output.",
            agent=agent,
            expected_output=f"A detailed list of technologies, frameworks, and software versions used by 'https://{self.domain}', based on the tool's output. Include any known vulnerabilities or security considerations for the identified stack derived from the tool's findings."
        )

    def directory_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Enumerate web directories and files for the website at 'https://{self.domain}' using the 'Directory Enumeration' tool. "
                        f"The tool should be instructed to target the domain '{self.domain}'. "
                        f"Identify any interesting or potentially sensitive paths (e.g., admin panels, backup files, exposed configuration files, common framework paths like /wp-admin, .git) based on the tool's output.",
            agent=agent,
            expected_output=f"A list of discovered directories and files on 'https://{self.domain}' with their HTTP status codes, based on the tool's output. Highlight any paths that seem sensitive, are related to known frameworks, or might indicate information leakage, as reported by the tool.",
            context=[self.tech_stack_task(self.tech_stack_agent())]
        )


    def reporting_task(self, agent: Agent, all_recon_tasks: List[Task]) -> Task:
        return Task(
            description=f"""
Compile and synthesize ALL reconnaissance data gathered for the domain '{self.domain}'.
The data includes findings from:
- WHOIS Information
- DNS Records
- Discovered Subdomains
- Technology Stack
- Open Ports and Services
- Web Directories and Files

Analyze this consolidated information from the context of previous tasks to:
1.  Provide a concise executive summary of the reconnaissance.
2.  Identify potential attack vectors or key areas of security concern based *only* on the provided tool outputs.
3.  List any specific vulnerabilities or misconfigurations *explicitly suggested or found by the tools* (e.g., outdated software versions reported by Nmap or WhatWeb, exposed sensitive paths found by Dirsearch, weak DNS configurations from Dnsrecon). Do not invent vulnerabilities.
4.  Suggest actionable security recommendations *directly related* to the findings from the tools.
5.  Structure the final output in clear, well-organized Markdown format.
Ensure the report is factual and based SOLELY on the information provided in the context from the previous tasks.
            """,
            agent=agent,
            expected_output=f"A comprehensive and structured Markdown report detailing all reconnaissance findings for '{self.domain}', including an executive summary, identified potential vulnerabilities (as found by tools), and actionable security recommendations based on tool outputs. The report must be factual and directly derived from the provided context.",
            context=all_recon_tasks
        )

    def create_crew(self) -> Crew:
        _whois_agent = self.whois_agent()
        _dns_agent = self.dns_agent()
        _subdomain_agent = self.subdomain_agent()
        _tech_stack_agent = self.tech_stack_agent() # Di chuyển lên trước
        _port_scan_agent = self.port_scan_agent()
        _directory_agent = self.directory_agent()
        _reporting_agent = self.reporting_agent()

        task_whois = self.whois_task(_whois_agent)
        task_dns = self.dns_task(_dns_agent)
        task_subdomain = self.subdomain_task(_subdomain_agent)
        task_tech_stack = self.tech_stack_task(_tech_stack_agent) # Task tech_stack
        task_port_scan = self.port_scan_task(_port_scan_agent)
        task_directory = self.directory_task(_directory_agent)
        
        recon_tasks = [
            task_whois,
            task_dns,
            task_subdomain,
            task_tech_stack, # Chạy tech_stack trước port_scan và directory
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
                _tech_stack_agent, # Agent tech_stack
                _port_scan_agent,
                _directory_agent,
                _reporting_agent
            ],
            tasks=all_crew_tasks,
            process=Process.sequential,
            verbose=True, 
            llm=self.llm,
        )