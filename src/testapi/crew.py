
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
            test_url = target_url if target_url.startswith(("http://", "https://")) else f"http://{target_url}"
            if not validators.url(test_url):
                raise ValueError(f"Invalid URL: {target_url}")
        self.target_url = target_url.rstrip("/")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in .env file")

        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model="deepseek/deepseek-chat",
            temperature=0.3
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
            goal=f"""
Analyze WHOIS data for {self.target_url} to extract registrant, admin, and tech contact details.
Include domain creation, update, and expiry dates, as well as nameservers.
Assess the risk of exposed contact information (e.g., personal emails or addresses indicate weak privacy, medium risk).
Include all raw WHOIS output.
If the lookup fails, suggest retrying with alternative WHOIS servers (e.g., whois.domaintools.com) or manual lookup for .vn TLDs.
""",
            backstory="Expert in domain registration analysis, skilled at extracting detailed WHOIS data and assessing security risks from exposed information.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WHOIS Lookup",
                    description=f"Fetches WHOIS information for a domain {self.target_url}.",
                    command="whois {target}",
                    tool_name="WHOIS Lookup"
                )
            ],
            allow_delegation=False
        )

    def dns_agent(self) -> Agent:
        return Agent(
            role="DNS Enumeration Specialist",
            goal=f"""
Enumerate DNS records for {self.target_url} using JSON output, including zone transfer attempts and SRV records.
Parse the JSON to list all records (A, AAAA, MX, NS, TXT, CNAME, SOA, SRV), including IPs, mail servers, nameservers, and TXT records (e.g., SPF, DKIM, DMARC).
Analyze for misconfigurations (e.g., missing SPF/DKIM/DMARC, successful zone transfers, unusual nameservers).
Assess risk (e.g., successful zone transfer = critical risk, missing DMARC = high risk for email spoofing).
Include raw JSON output.
If enumeration fails, suggest retries with longer timeouts, alternative DNS servers (e.g., 8.8.8.8), or tools like `dig`.
""",
            backstory="Expert in DNS analysis, proficient in parsing JSON outputs and identifying security risks from DNS misconfigurations and zone transfers.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="DNS Recon",
                    description=f"Enumerates DNS records for {self.target_url} in JSON format, including zone transfers.",
                    command="dnsrecon -d {target} -t std -s -j {output_file}",
                    tool_name="DNS Recon",
                    writes_to_file=True,
                    output_file_template="dnsrecon_output_{target}.json"
                )
            ],
            allow_delegation=False
        )

    def subdomain_agent(self) -> Agent:
        return Agent(
            role="Subdomain Discovery Specialist",
            goal=f"""
Discover all active subdomains of {self.target_url} and verify their accessibility (resolves to IP, responds to HTTP/HTTPS).
Identify sensitive subdomains (e.g., 'dev', 'admin', 'staging').
Assess their risk (e.g., exposed 'dev' may leak development data, high risk).
Include all discovered subdomains, their IPs, and HTTP/HTTPS response details.
Recommend further scans (e.g., port scans, directory enumeration) for critical subdomains.
Include raw tool output.
If enumeration fails, suggest retries with alternative tools (e.g., Amass, Fierce) or configurations (e.g., proxy settings).
""",
            backstory="Expert in subdomain enumeration and OSINT, skilled at identifying high-value targets and assessing their security implications.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Subdomain Enumeration",
                    description=f"Discovers subdomains for {self.target_url}.",
                    command="sublist3r -d {target} -o sublist3r_output_{target}.txt",
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
            goal=f"""
Identify open TCP ports, services, and versions on {self.target_url} for the top 100 ports.
Analyze each open port's service and version to identify potential vulnerabilities (e.g., outdated versions like Apache 2.4.29).
Check for known CVEs using tool outputs or well-known vulnerability data (e.g., CVE-2017-9798 for Apache 2.4.29).
Include all scan details (e.g., SSL certificate SANs, HTTP methods, robots.txt, OS detection).
Assess the risk of each finding (e.g., outdated service = high risk).
If subdomains are in context, recommend scanning critical ones (e.g., 'dev', 'admin').
Include raw Nmap output.
If the scan fails, suggest retries with slower scan speed (e.g., -T3) or additional scan types (e.g., -sU for UDP).
""",
            backstory="Expert in network scanning and vulnerability assessment, skilled at correlating service versions with known vulnerabilities and optimizing Nmap scans.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Nmap Scan",
                    description=f"Scans ports and services on {self.target_url}.",
                    command="nmap -sV -sC -T4 -Pn {target}",
                    tool_name="Nmap Scan"
                )
            ],
            allow_delegation=False
        )

    def directory_agent(self) -> Agent:
        return Agent(
            role="Web Directory Enumeration Specialist",
            goal=f"""
Enumerate directories and files on https://{self.target_url} to identify sensitive paths (e.g., admin panels, backup files, configuration files).
Include all discovered paths, their HTTP status codes, and response sizes.
Assess the risk of each finding (e.g., exposed /admin = critical risk).
Include raw tool output.
If enumeration fails, suggest retries with fewer threads (e.g., --threads=3), shorter delays (e.g., --delay=250), or limited recursion (e.g., --recursion-depth=1).
""",
            backstory="Expert in web directory enumeration, skilled at identifying high-risk paths and adjusting tool parameters to bypass rate-limiting.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Directory Enumeration",
                    description=f"Enumerates directories on a web server at https://{self.target_url}.",
                    command="dirsearch -u https://{target} -o {output_file} --force-extensions -e php,asp,aspx,jsp,html,js,txt,bak,config,yml,yaml -r",
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
            goal=f"""
Identify the technology stack (web server, frameworks, CMS, libraries) for https://{self.target_url} using customizable aggression levels.
Include all detected technologies, versions, and metadata (e.g., IP address, meta-author).
Correlate findings with known vulnerabilities (e.g., WordPress 5.8.1 has specific CVEs) using tool outputs or well-known vulnerability data.
Assess the risk of each technology (e.g., outdated CMS = high risk).
Include raw tool output.
If the scan fails, suggest retries with a lower aggression level (e.g., -a 1).
""",
            backstory="Expert in web technology identification, skilled at linking technologies to vulnerabilities and adjusting scan aggression for optimal results.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WhatWeb Scan",
                    description=f"Identifies technologies used by the website https://{self.target_url} with customizable aggression.",
                    command="whatweb -a {aggression} https://{target}",
                    tool_name="WhatWeb Scan"
                )
            ],
            allow_delegation=False
        )

    def reporting_agent(self) -> Agent:
        return Agent(
            role="Lead Security Analyst and Report Synthesizer",
            goal=f"""
Compile a comprehensive report for {self.target_url} synthesizing all reconnaissance findings from:
- WHOIS Information (e.g., registrant details, nameservers)
- DNS Records (e.g., A, MX, TXT, DMARC, SRV)
- Discovered Subdomains (e.g., dev, admin)
- Open Ports and Services (e.g., port 80, SSL details)
- Web Directories and Files (e.g., /admin, backups)
- Technology Stack (e.g., IIS, ASP.NET)
Perform the following:
- Provide a concise executive summary of key findings and risks.
- Include detailed findings for each task, preserving all raw tool outputs (e.g., Nmap SSL SANs, WhatWeb metadata, dnsrecon JSON) and agent analyses.
- Correlate data across tasks (e.g., if Subdomain Agent finds 'dev.{self.target_url}', recommend Port Scan and Directory scans).
- Identify vulnerabilities and misconfigurations, assigning risk levels (low, medium, high, critical) with justifications (e.g., exposed admin panel = critical).
- Review task failures (e.g., timeouts, errors) and suggest retries with adjusted parameters (e.g., Nmap -T3, dirsearch --threads=3).
- Provide actionable recommendations to mitigate risks (e.g., secure subdomains, patch software).
- Structure the report in clear Markdown format with sections for executive summary, detailed findings (including raw outputs), correlations, risk matrix, and recommendations.
Use context from all previous tasks to ensure completeness.
""",
            backstory="Expert security analyst skilled at correlating diverse reconnaissance data, preserving raw tool outputs, and producing detailed, actionable intelligence reports.",
            verbose=True,
            llm=self.llm,
            tools=[],
            allow_delegation=False
        )

    # --- TASKS ---
    def whois_task(self, agent: Agent) -> Task:
        return Task(
            description=f"""
Execute a WHOIS lookup for '{self.target_url}'.
Extract registrant, admin, tech contact details, domain creation/update/expiry dates, and nameservers.
Analyze for exposed sensitive information (e.g., personal emails, addresses).
Assess risk (e.g., exposed personal data = medium risk).
Include raw WHOIS output.
If the lookup fails, suggest retrying with alternative WHOIS servers or manual lookup for .vn TLDs.
""",
            agent=agent,
            expected_output=f"""
A detailed summary of WHOIS information for {self.target_url}, including:
- Registrant, admin, tech contacts
- Domain dates and nameservers
- Risk assessment of exposed data
- Raw tool output
- Retry suggestions for failures
"""
        )

    def dns_task(self, agent: Agent) -> Task:
        return Task(
            description=f"""
Enumerate DNS records for '{self.target_url}' using dnsrecon with JSON output, including zone transfer attempts and SRV records.
Parse the JSON to list all A, AAAA, MX, NS, TXT, CNAME, SOA, and SRV records, including IPs, mail servers, and TXT details (e.g., SPF, DMARC).
Analyze for misconfigurations (e.g., missing SPF/DKIM/DMARC, successful zone transfers, unusual nameservers).
Assess risk (e.g., successful zone transfer = critical risk, missing DMARC = high risk).
Include raw JSON output.
If enumeration fails, suggest retries with longer timeouts or alternative DNS servers.
""",
            agent=agent,
            expected_output=f"""
A detailed list of DNS records for {self.target_url} from JSON output, including:
- All record types (A, AAAA, MX, NS, TXT, CNAME, SOA, SRV)
- Analysis of misconfigurations
- Risk levels (low, medium, high, critical)
- Raw tool output
- Retry suggestions for failures
""",
            context=[self.whois_task(self.whois_agent())]
        )

    def subdomain_task(self, agent: Agent) -> Task:
        return Task(
            description=f"""
Discover all publicly accessible subdomains for '{self.target_url}'.
Verify accessibility (resolves to IP, responds to HTTP/HTTPS) and include IPs and response details.
Identify sensitive subdomains (e.g., 'dev', 'admin', 'staging').
Assess risk (e.g., exposed 'dev' = high risk).
Recommend further scans (e.g., port scans, directory enumeration) for critical subdomains.
Include raw tool output.
If enumeration fails, suggest retries with alternative tools or configurations.
""",
            agent=agent,
            expected_output=f"""
A comprehensive list of subdomains for {self.target_url}, including:
- IPs and accessibility details
- Sensitive subdomains with risk levels
- Recommendations for further scans
- Raw tool output
- Retry suggestions for failures
""",
            context=[self.dns_task(self.dns_agent())]
        )

    def port_scan_task(self, agent: Agent) -> Task:
        return Task(
            description=f"""
Conduct a port scan on '{self.target_url}' for the top 100 TCP ports.
Identify open ports, services, and versions.
Check for known CVEs using tool outputs or well-known vulnerability data (e.g., CVE-2017-9798 for Apache 2.4.29).
Include all scan details (e.g., SSL certificate SANs, HTTP methods, robots.txt, OS detection).
Assess the risk of each finding (e.g., outdated service = high risk).
If subdomains are in context, recommend scanning critical ones.
Include raw Nmap output.
If the scan fails, suggest retries with adjusted parameters (e.g., -T3).
""",
            agent=agent,
            expected_output=f"""
Comprehensive port scan results for {self.target_url}, including:
- Open ports, services, versions
- CVEs and SSL details
- HTTP methods and OS detection
- Risk levels
- Recommendations for subdomain scans
- Raw tool output
- Retry suggestions for failures
""",
            context=[self.subdomain_task(self.subdomain_agent())]
        )

    def directory_task(self, agent: Agent) -> Task:
        return Task(
            description=f"""
Enumerate directories and files for 'https://{self.target_url}' with limited recursion.
Identify sensitive paths (e.g., admin panels, backup files, configuration files).
Include HTTP status codes and response sizes.
Assess the risk of each finding (e.g., exposed /admin = critical risk).
Include raw tool output.
If enumeration fails, suggest retries with adjusted parameters (e.g., fewer threads, shorter delays).
""",
            agent=agent,
            expected_output=f"""
A detailed list of directories and files on https://{self.target_url}, including:
- HTTP status codes and response sizes
- Sensitive paths with risk levels
- Raw tool output
- Retry suggestions for failures
""",
            context=[self.tech_stack_task(self.tech_stack_agent())]
        )

    def tech_stack_task(self, agent: Agent) -> Task:
        return Task(
            description=f"""
Identify the technology stack for 'https://{self.target_url}' (web server, frameworks, CMS, libraries) using customizable aggression levels.
Include all detected technologies, versions, and metadata (e.g., IP address, meta-author).
Correlate findings with known vulnerabilities using tool outputs or well-known vulnerability data.
Assess the risk of each technology (e.g., outdated CMS = high risk).
Include raw tool output.
If the scan fails, suggest retries with a lower aggression level (e.g., -a 1).
""",
            agent=agent,
            expected_output=f"""
A comprehensive list of technologies and versions for https://{self.target_url}, including:
- Metadata
- Known vulnerabilities
- Risk levels
- Raw tool output
- Retry suggestions for failures
"""
        )

    def reporting_task(self, agent: Agent, all_tasks: List[Task]) -> Task:
        return Task(
            description=f"""
Compile a comprehensive report for '{self.target_url}' synthesizing all reconnaissance data from:
- WHOIS Information (e.g., registrant details, nameservers)
- DNS Records (e.g., A, MX, TXT, DMARC, SRV)
- Discovered Subdomains (e.g., dev, admin)
- Open Ports and Services (e.g., port 80, SSL details)
- Web Directories and Files (e.g., /admin, backups)
- Technology Stack (e.g., IIS, ASP.NET)
Perform the following:
- Provide an executive summary of key findings, highlighting critical risks (e.g., exposed subdomains, unpatched vulnerabilities).
- Include detailed findings for each task, preserving all raw tool outputs (e.g., Nmap SSL SANs, WhatWeb metadata, dnsrecon JSON) and agent analyses.
- Correlate data across tasks (e.g., match Subdomain Agent's 'dev.{self.target_url}' with Port Scan Agent's open ports).
- Identify vulnerabilities and misconfigurations, assigning risk levels (low, medium, high, critical) with detailed justifications.
- Review task failures and suggest retries with specific parameters (e.g., Nmap -T3, dirsearch --threads=3).
- Provide actionable recommendations to mitigate risks (e.g., secure subdomains, implement DMARC, patch software).
- Structure the report in Markdown with sections: Executive Summary, Detailed Findings (with raw outputs), Data Correlations, Risk Prioritization Matrix, Recommendations, and Retry Suggestions.
Use context from all previous tasks to ensure no data is omitted.
""",
            agent=agent,
            expected_output=f"""
A comprehensive Markdown report for {self.target_url}, including:
- Executive Summary: Key findings and critical risks
- Detailed Findings: Full agent analyses and raw tool outputs for each task
- Data Correlations: Cross-task insights (e.g., subdomain and port scan matches)
- Risk Prioritization Matrix: Vulnerabilities with risk levels and justifications
- Recommendations: Actionable mitigation steps
- Retry Suggestions: Parameters for failed tasks
""",
            context=all_tasks
        )

    def create_crew(self) -> Crew:
        """Creates the Reconnaissance crew"""
        _whois_agent = self.whois_agent()
        _dns_agent = self.dns_agent()
        _subdomain_agent = self.subdomain_agent()
        _port_scan_agent = self.port_scan_agent()
        _directory_agent = self.directory_agent()
        _tech_stack_agent = self.tech_stack_agent()
        _reporting_agent = self.reporting_agent()

        task_whois = self.whois_task(_whois_agent)
        task_dns = self.dns_task(_dns_agent)
        task_subdomain = self.subdomain_task(_subdomain_agent)
        task_tech_stack = self.tech_stack_task(_tech_stack_agent)
        task_port_scan = self.port_scan_task(_port_scan_agent)
        task_directory = self.directory_task(_directory_agent)

        recon_tasks = [
            task_whois,
            task_dns,
            task_subdomain,
            task_tech_stack,
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
                _tech_stack_agent,
                _port_scan_agent,
                _directory_agent,
                _reporting_agent
            ],
            tasks=all_crew_tasks,
            process=Process.sequential,
            verbose=True,
            llm=self.llm
        )
