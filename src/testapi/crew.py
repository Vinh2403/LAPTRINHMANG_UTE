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
            goal=f"Analyze WHOIS data for {self.target_url} to extract registrant, admin, and tech contact details. Assess the risk of exposed contact information (e.g., personal emails may indicate weak privacy measures). If the lookup fails, suggest retrying with alternative WHOIS servers.",
            backstory="Expert in domain registration analysis, skilled at evaluating WHOIS data for security implications and troubleshooting lookup issues.",
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
            goal=f"Enumerate DNS records (A, AAAA, MX, NS, TXT, CNAME, SOA) for {self.target_url} and parse JSON output to identify misconfigurations (e.g., missing SPF/DKIM/DMARC, unusual nameservers). Assess the risk of each finding (e.g., missing DMARC may allow email spoofing, high risk). If enumeration fails, suggest retrying with a longer timeout or alternative DNS servers.",
            backstory="Expert in DNS analysis, adept at parsing structured outputs and assessing security risks from misconfigurations.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="DNS Recon",
                    description=f"Enumerates DNS records for {self.target_url} in JSON format.",
                    command="dnsrecon -d {target} -a -s -j {output_file}",
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
            goal=f"Discover all active subdomains of {self.target_url} and verify their accessibility. Identify sensitive subdomains (e.g., 'dev', 'admin', 'staging') and assess their risk (e.g., exposed 'dev' may leak development data, high risk). Recommend further scans (e.g., port scans, directory enumeration) for critical subdomains. If enumeration fails, suggest retrying with alternative tools or configurations.",
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
            goal=f"Identify open TCP/UDP ports, services, and versions on {self.target_url}. For each open port, analyze the service and version to identify potential vulnerabilities (e.g., outdated versions like Apache 2.4.29). Check for known CVEs associated with specific versions, using only tool outputs or well-known vulnerability data (e.g., Apache 2.4.29 has CVE-2017-9798). Assess the risk of each finding (e.g., outdated service = high risk). If subdomains are in context, recommend scanning critical ones (e.g., 'dev.{self.target_url}'). If the scan fails, suggest retrying with slower scan speed (e.g., -T3).",
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
            goal=f"Enumerate directories and files on https://{self.target_url} to identify sensitive paths (e.g., admin panels, backup files, configuration files). Assess the risk of each finding (e.g., exposed /admin = critical risk). If enumeration fails, suggest retrying with fewer threads (e.g., --threads=5) or a longer timeout.",
            backstory="Expert in web directory enumeration, skilled at identifying high-risk paths and adjusting tool parameters to bypass rate-limiting.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Directory Enumeration",
                    description=f"Enumerates directories on a web server at https://{self.target_url}.",
                    command="dirsearch -u https://{target} -o {output_file} --force-extensions -e php,asp,aspx,jsp,html,js,txt,bak,config,yml,yaml -r --threads=10",
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
            goal=f"Identify the technology stack (web server, frameworks, CMS, libraries) for https://{self.target_url}. Correlate findings with known vulnerabilities (e.g., WordPress 5.8.1 has specific CVEs). Assess the risk of each technology (e.g., outdated CMS = high risk). If the scan fails, suggest retrying with a different aggression level (e.g., -a 1).",
            backstory="Expert in web technology identification, skilled at linking technologies to vulnerabilities and assessing their security impact.",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WhatWeb Scan",
                    description=f"Identifies technologies used by the website https://{self.target_url}.",
                    command="whatweb -a 3 https://{target}",
                    tool_name="WhatWeb Scan"
                )
            ],
            allow_delegation=False
        )

    def reporting_agent(self) -> Agent:
        return Agent(
            role="Lead Security Analyst and Report Synthesizer",
            goal=f"Compile and synthesize all reconnaissance findings for {self.target_url} into a comprehensive report. Correlate data across tasks (e.g., if Subdomain Agent finds 'dev.{self.target_url}', suggest Port Scan Agent and Directory Agent scan it further). Identify vulnerabilities and misconfigurations, assigning risk levels (low, medium, high). Review task failures and suggest retries with adjusted parameters (e.g., Nmap -T3, dirsearch --threads=5). Provide actionable recommendations to mitigate identified risks.",
            backstory="Expert security analyst skilled at correlating diverse reconnaissance data, assessing risks, and producing actionable intelligence reports.",
            verbose=True,
            llm=self.llm,
            tools=[],
            allow_delegation=False
        )

    # --- TASKS ---
    def whois_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Execute a WHOIS lookup for '{self.target_url}'. Extract registrant, admin, and tech contact details. Analyze for exposed sensitive information (e.g., personal emails, physical addresses) and assess risk (e.g., exposed personal data = medium risk). If the lookup fails, suggest retrying with alternative WHOIS servers.",
            agent=agent,
            expected_output=f"A summary of WHOIS information for {self.target_url}, including registrant, admin, and tech contacts, with risk assessment of exposed data and retry suggestions for failures."
        )

    def dns_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Enumerate DNS records for '{self.target_url}' using dnsrecon with JSON output. Parse the JSON to list A, AAAA, MX, NS, TXT, CNAME, and SOA records. Analyze for misconfigurations (e.g., missing SPF/DKIM/DMARC, unusual nameservers) and assess risk (e.g., missing DMARC = high risk for email spoofing). If enumeration fails, suggest retrying with a longer timeout or alternative DNS servers.",
            agent=agent,
            expected_output=f"A detailed list of DNS records for {self.target_url} from JSON output, with analysis of misconfigurations, risk levels (low, medium, high), and retry suggestions for failures.",
            context=[self.whois_task(self.whois_agent())]
        )

    def subdomain_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Discover all publicly accessible subdomains for '{self.target_url}'. Verify accessibility (resolves to IP, responds to HTTP/HTTPS). Identify sensitive subdomains (e.g., 'dev', 'admin', 'staging') and assess risk (e.g., exposed 'dev' = high risk). Recommend further scans (e.g., port scans, directory enumeration) for critical subdomains. If enumeration fails, suggest retrying with alternative tools or configurations.",
            agent=agent,
            expected_output=f"A list of subdomains for {self.target_url}, noting accessibility, highlighting sensitive ones with risk levels, recommending further scans, and including retry suggestions for failures.",
            context=[self.dns_task(self.dns_agent())]
        )

    def port_scan_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Conduct a port scan on '{self.target_url}'. Identify open TCP ports, services, and versions. For each service with a specific version (e.g., Apache 2.4.29), check for known CVEs using tool outputs or well-known vulnerability data (e.g., CVE-2017-9798 for Apache 2.4.29). Assess the risk of each finding (e.g., outdated service = high risk). If subdomains are in context, recommend scanning critical ones (e.g., 'dev', 'admin'). If the scan fails, suggest retrying with adjusted parameters (e.g., -T3).",
            agent=agent,
            expected_output=f"Detailed port scan results for {self.target_url}, including open ports, services, versions, known CVEs, and risk levels. Recommend scanning critical subdomains from context. Include retry suggestions for failures.",
            context=[self.subdomain_task(self.subdomain_agent())]
        )

    def directory_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Enumerate directories and files for 'https://{self.target_url}'. Identify sensitive paths (e.g., admin panels, backup files, configuration files) and assess risk (e.g., exposed /admin = critical risk). If enumeration fails, suggest retrying with fewer threads (e.g., --threads=5) or a longer timeout.",
            agent=agent,
            expected_output=f"A list of directories and files on https://{self.target_url} with HTTP status codes, highlighting sensitive paths with risk levels and potential information leakage. Include retry suggestions for failures.",
            context=[self.tech_stack_task(self.tech_stack_agent())]
        )

    def tech_stack_task(self, agent: Agent) -> Task:
        return Task(
            description=f"Identify the technology stack for 'https://{self.target_url}' (web server, frameworks, CMS, libraries). Correlate findings with known vulnerabilities (e.g., WordPress 5.8.1 has specific CVEs) using tool outputs or well-known vulnerability data. Assess risk (e.g., outdated CMS = high risk). If the scan fails, suggest retrying with a different aggression level (e.g., -a 1).",
            agent=agent,
            expected_output=f"A detailed list of technologies and versions for https://{self.target_url}, with known vulnerabilities, risk levels, and retry suggestions for failures."
        )

    def reporting_task(self, agent: Agent, all_tasks: List[Task]) -> Task:
        return Task(
            description=f"""
Compile and synthesize all reconnaissance data for '{self.target_url}' from:
- WHOIS Information
- DNS Records
- Discovered Subdomains
- Open Ports and Services
- Web Directories and Files
- Technology Stack
Analyze the data to:
1. Provide a concise executive summary of findings.
2. Correlate data across tasks (e.g., if Subdomain Agent finds 'dev.{self.target_url}', suggest Port Scan Agent and Directory Agent scan it further).
3. Identify vulnerabilities and misconfigurations, assigning risk levels (low, medium, high) based on findings (e.g., exposed admin panel = critical, missing DMARC = high).
4. Review task failures (e.g., timeouts, errors) and suggest retries with adjusted parameters (e.g., Nmap -T3, dirsearch --threads=5).
5. Provide actionable recommendations to mitigate risks (e.g., update outdated software, secure exposed subdomains).
6. Structure the output in clear Markdown format with sections for each task, correlations, risks, and recommendations.
Use context from all previous tasks.
            """,
            agent=agent,
            expected_output=f"A comprehensive Markdown report for {self.target_url}, including an executive summary, correlated findings, vulnerabilities with risk levels, task failure analysis with retry suggestions, and actionable recommendations.",
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