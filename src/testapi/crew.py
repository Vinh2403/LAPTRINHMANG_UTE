from crewai import Agent, Crew, Process, Task
from tools.custom_tool import ReconTool  # Import ReconTool from custom_tool.py
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
        # Validate URL
        if not validators.url(f"https://{target_url}") and not validators.url(f"http://{target_url}"):
            raise ValueError(f"Invalid URL: {target_url}")
        self.target_url = target_url.rstrip("/")

        # Check environment variable
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in .env file")

        # Initialize LLM (DeepSeek-specific configuration)
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model="deepseek/deepseek-chat",  # Prefix model with provider
            temperature=0.7
        )

        # Check required tools
        self.required_tools = ["whois", "dnsrecon", "sublist3r", "nmap", "dirsearch", "whatweb"]
        self.check_tools()

    def check_tools(self):
        """Check if required system tools are installed."""
        missing_tools = []
        for tool in self.required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        if missing_tools:
            raise EnvironmentError(f"Missing tools: {', '.join(missing_tools)}. Please install them.")

    def whois_agent(self) -> Agent:
        return Agent(
            role="WHOIS Information Specialist",
            goal="Gather domain registration and ownership information",
            backstory="Expert in domain registration analysis and WHOIS data interpretation",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WHOIS Lookup",
                    description="Fetches WHOIS information for a domain",
                    command="whois {target}",
                    tool_name="WHOIS Lookup"
                )
            ]
        )

    def dns_agent(self) -> Agent:
        return Agent(
            role="DNS Enumeration Specialist",
            goal="Discover DNS records and configurations",
            backstory="Expert in DNS analysis and record enumeration",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="DNS Recon",
                    description="Enumerates DNS records for a domain",
                    command="dnsrecon -d {target}",
                    tool_name="DNS Recon"
                )
            ]
        )

    def subdomain_agent(self) -> Agent:
        return Agent(
            role="Subdomain Discovery Specialist",
            goal="Find all possible subdomains of the target domain",
            backstory="Expert in subdomain enumeration and discovery",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Subdomain Enumeration",
                    description="Discovers subdomains for a domain",
                    command="sublist3r -d {target}",
                    tool_name="Subdomain Enumeration"
                )
            ]
        )

    def port_scan_agent(self) -> Agent:
        return Agent(
            role="Port Scanning Specialist",
            goal="Identify open ports and services",
            backstory="Expert in network scanning and service identification",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Nmap Scan",
                    description="Scans ports and services on a target",
                    command="nmap -sV -sC {target}",
                    tool_name="Nmap Scan"
                )
            ]
        )

    def directory_agent(self) -> Agent:
        return Agent(
            role="Directory Enumeration Specialist",
            goal="Discover hidden directories and files",
            backstory="Expert in web directory enumeration and discovery",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="Directory Enumeration",
                    description="Enumerates directories on a web server",
                    command="dirsearch -u https://{target} -w /app/wordlists/common.txt -e php,html,js,asp,aspx -i 200,301,302 -t 50 --format=plain --exclude-status=403,404 --exclude-text='Forbidden|Not Found' -o dirsearch_output.txt",
                    tool_name="Directory Enumeration"
                )
            ]
        )

    def tech_stack_agent(self) -> Agent:
        return Agent(
            role="Technology Stack Analyst",
            goal="Identify technologies and frameworks used",
            backstory="Expert in web technology identification and analysis",
            verbose=True,
            llm=self.llm,
            tools=[
                ReconTool(
                    name="WhatWeb Scan",
                    description="Identifies technologies used by a website",
                    command="whatweb https://{target}",
                    tool_name="WhatWeb Scan"
                )
            ]
        )

    def whois_task(self) -> Task:
        return Task(
            description=f"Gather WHOIS information for {self.target_url}",
            agent=self.whois_agent(),
            expected_output="Detailed WHOIS information including registration details, nameservers, and contact information"
        )

    def dns_task(self) -> Task:
        return Task(
            description=f"Perform DNS enumeration for {self.target_url}",
            agent=self.dns_agent(),
            expected_output="Complete list of DNS records including A, AAAA, MX, NS, and TXT records"
        )

    def subdomain_task(self) -> Task:
        return Task(
            description=f"Discover subdomains for {self.target_url}",
            agent=self.subdomain_agent(),
            expected_output="List of discovered subdomains with their status"
        )

    def port_scan_task(self) -> Task:
        return Task(
            description=f"Scan ports and services for {self.target_url}",
            agent=self.port_scan_agent(),
            expected_output="Detailed port scan results with service versions and potential vulnerabilities"
        )

    def directory_task(self) -> Task:
        return Task(
            description=f"Enumerate directories for {self.target_url}",
            agent=self.directory_agent(),
            expected_output="List of discovered directories and files with their status codes"
        )

    def tech_stack_task(self) -> Task:
        return Task(
            description=f"Identify technology stack for {self.target_url}",
            agent=self.tech_stack_agent(),
            expected_output="Detailed list of technologies, frameworks, and versions used"
        )

    def create_crew(self) -> Crew:
        """Creates the Reconnaissance crew"""
        return Crew(
            agents=[
                self.whois_agent(),
                self.dns_agent(),
                self.subdomain_agent(),
                self.port_scan_agent(),
                self.directory_agent(),
                self.tech_stack_agent()
            ],
            tasks=[
                self.whois_task(),
                self.dns_task(),
                self.subdomain_task(),
                self.port_scan_task(),
                self.directory_task(),
                self.tech_stack_task()
            ],
            process=Process.sequential,
            verbose=True,
            llm=self.llm
        )