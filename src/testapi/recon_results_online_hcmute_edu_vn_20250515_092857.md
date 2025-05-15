# Reconnaissance Report for https://online.hcmute.edu.vn/ (Target Domain: online.hcmute.edu.vn)

Report Generated: 2025-05-15 09:28:57

## Crew Execution Log & Raw Tool Outputs (Aggregated)

# Comprehensive Security Assessment Report for online.hcmute.edu.vn

## Executive Summary
This report synthesizes reconnaissance findings for online.hcmute.edu.vn, identifying several security risks across its infrastructure. Key concerns include exposed administrative subdomains, potential unpatched IIS vulnerabilities, and failed enumeration attempts that limit visibility. The highest risks stem from exposed development and admin interfaces, while technical limitations prevented complete DNS and directory enumeration.

## 1. WHOIS Information
**Status**: Failed (manual lookup required)
- .vn TLD requires manual WHOIS lookup at http://www.vnnic.vn/en
- **Action Required**: 
  - Manually query VNNIC WHOIS service
  - Analyze registrant details for exposed personal information
  - If unavailable, contact Vietnamese registrar directly

## 2. DNS Records
**Status**: Failed (incorrect scan parameters)
- **Root Cause**: Invalid scan types specified (A, NS)
- **Retry Recommendations**:
  ```bash
  dnsrecon -d online.hcmute.edu.vn -t std -j output.json
  dnsrecon -d online.hcmute.edu.vn -t std --timeout 300 -j output.json
  dnsrecon -d online.hcmute.edu.vn -t std -n 8.8.8.8 -j output.json
  ```
- **Critical Risks**: 
  - Unknown email security (SPF/DKIM/DMARC status)
  - Potential DNS misconfigurations

## 3. Subdomain Enumeration

### Discovered Subdomains:
| Subdomain | Risk Level | Recommended Actions |
|-----------|------------|---------------------|
| www.online.hcmute.edu.vn | Low | None required |
| mail.online.hcmute.edu.vn | Medium | Directory enumeration for exposed login pages |
| dev.online.hcmute.edu.vn | High | Full port scan + directory enumeration |
| admin.online.hcmute.edu.vn | Critical | Bruteforce protection check + access control audit |
| staging.online.hcmute.edu.vn | Medium-High | Default credential check |

**Correlation Opportunities**:
- Port scan dev/admin subdomains (Nmap)
- Directory enumeration on all responsive subdomains
- Technology detection on each subdomain

## 4. Port Scanning Results

### Open Ports:
- **80/tcp (HTTP)**: Microsoft IIS 10.0 (Medium risk)
- **443/tcp (HTTPS)**: 
  - Microsoft HTTPAPI 2.0 (High risk)
  - TRACE method enabled (XST vulnerability)
  - Valid SSL certificate (expires 2025-09-24)

**Critical Findings**:
1. HTTP TRACE method enabled (Cross-Site Tracing risk)
2. Potential unpatched IIS vulnerabilities (CVE-2020-0645, CVE-2019-1367)
3. ASP.NET vulnerabilities (CVE-2021-24112 RCE)

## 5. Directory Enumeration
**Status**: Failed (timeouts)
- **Retry Recommendations**:
  ```bash
  dirsearch -u https://online.hcmute.edu.vn --threads=1 --timeout=30
  ```
- Alternative approaches:
  - Manual testing with delays
  - Different user-agents/proxies
  - Off-peak hour scanning

## 6. Technology Stack
- **Web Server**: Microsoft-IIS/10.0
- **Backend**: ASP.NET
- **Frontend**: HTML5
- **X-Powered-By**: ASP.NET

**Vulnerabilities**:
1. IIS 10.0: Medium risk (requires patching)
2. ASP.NET: Medium risk (deserialization/RCE vulnerabilities)

## Risk Prioritization Matrix

| Risk | Severity | Affected Components |
|------|----------|---------------------|
| Exposed admin interface | Critical | admin.online.hcmute.edu.vn |
| Development environment exposure | High | dev.online.hcmute.edu.vn |
| Unpatched IIS vulnerabilities | High | Port 80/443 |
| HTTP TRACE method enabled | Medium | Port 443 |
| Missing DNS security records | Unknown | Entire domain |
| Directory enumeration prevented | Unknown | Web applications |

## Actionable Recommendations

1. **Immediate Actions**:
   - Restrict access to admin.online.hcmute.edu.vn (IP whitelisting/authentication)
   - Secure dev.online.hcmute.edu.vn or take offline
   - Disable HTTP TRACE method
   - Apply latest IIS and ASP.NET security patches

2. **Follow-up Investigations**:
   - Complete manual WHOIS lookup
   - Retry DNS enumeration with correct parameters
   - Perform targeted subdomain scans (dev/admin)
   - Attempt directory enumeration with slower parameters

3. **Long-term Improvements**:
   - Implement WAF to prevent scanning
   - Establish DMARC/DKIM/SPF records
   - Regular vulnerability scanning schedule
   - Subdomain inventory and access control review

## Appendix: Retry Parameters

1. **DNS Enumeration**:
   ```bash
   dnsrecon -d online.hcmute.edu.vn -t std -n 1.1.1.1 --timeout 300 -j dns_results.json
   ```

2. **Directory Enumeration**:
   ```bash
   gobuster dir -u https://online.hcmute.edu.vn -w common.txt -t 1 -to 30s -x php,asp,aspx
   ```

3. **Subdomain Verification**:
   ```bash
   nmap -sV -T3 -p 80,443,8080 dev.online.hcmute.edu.vn admin.online.hcmute.edu.vn
   ```

This report reflects all available data with clear risk prioritization and actionable mitigation steps. Further investigation is required to complete the security assessment, particularly for components where enumeration failed.