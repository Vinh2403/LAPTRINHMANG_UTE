# Reconnaissance Report for https://fpt.com (Target Domain: fpt.com)

Report Generated: 2025-05-14 16:06:48

## Crew Execution Log & Raw Tool Outputs (Aggregated)

# Comprehensive Security Reconnaissance Report for fpt.com  

## Executive Summary  
This report synthesizes reconnaissance findings for fpt.com, covering WHOIS, DNS, subdomains, technology stack, open ports, and attempted directory enumeration. Key observations include:  
- **Domain Protection**: Registered via GoDaddy with privacy protection, using Cloudflare DNS with DNSSEC  
- **Email Vulnerabilities**: Missing SPF/DKIM records despite DMARC implementation  
- **Subdomain Exposure**: 150+ subdomains discovered, including development (dev), testing (staging), and sensitive systems (econtract, einvoice)  
- **Infrastructure**: Cloudflare-protected web services with proper HTTPS enforcement  
- **Port Exposure**: Only Cloudflare-fronted HTTP/HTTPS services detected (ports 80, 443, 8080)  

---  

## 1. WHOIS Analysis  
**Key Findings**:  
- **Registration**: Domain registered since 1995 (expires 2032) with GoDaddy  
- **Privacy**: Registrant details hidden via Domains By Proxy  
- **Lock Status**: Client transfer/update/renew/delete prohibitions enabled  
- **Name Servers**: Cloudflare-managed (aspen.ns.cloudflare.com, toby.ns.cloudflare.com)  

**Security Implications**:  
✅ Domain hijacking mitigated by registrar locks  
⚠️ Privacy protection obscures ownership details for abuse reporting  

---  

## 2. DNS Security Assessment  
### A. Record Analysis  
- **A/AAAA**: 104.18.24.29/104.18.25.29 (Cloudflare) with IPv6 support  
- **MX**: Microsoft Outlook protection services  
- **TXT**: DMARC configured with quarantine policy (`v=DMARC1; p=quarantine`)  
- **SRV**: SIP federation service pointing to Microsoft Lync (52.113.102.64)  

### B. Vulnerabilities  
🔴 **Critical**:  
- Missing SPF record (email spoofing risk)  
- No DKIM record (email authentication gap)  

✅ **Strengths**:  
- DNSSEC properly configured (ECDSAP256SHA256)  
- DNS zone transfers prevented  

---  

## 3. Subdomain Exposure  
**Discovered Subdomains**: 150+ entries, including:  
- **Sensitive Systems**:  
  - `econtract.fpt.com`, `einvoice.fpt.com` (contract/e-invoicing)  
  - `epayment.fpt.com`, `etax.fpt.com` (financial services)  
- **Development/Testing**:  
  - `dev.apps.prod01.fis-cloud.fpt.com`  
  - `staging.apps.prod01.fis-cloud.fpt.com`  
- **API Endpoints**:  
  - `api.fpt.com`, `api.digital-accounting.fpt.com`  

**Security Implications**:  
⚠️ Development subdomains exposed to public indexing  
⚠️ API endpoints increase attack surface  

---  

## 4. Technology Stack  
**Identified Components**:  
- **Frontend**: HTML5, jQuery 3.7.1  
- **Backend**: ASP.NET (evidenced by `ASP.NET_SessionId`, `__RequestVerificationToken`)  
- **Infrastructure**: Cloudflare CDN/WAF  
- **Security Headers**:  
  - HSTS with preload (`max-age=2592000; includeSubDomains`)  
  - X-Frame-Options: SAMEORIGIN  

**Vulnerability Status**:  
✅ No outdated library versions detected  
⚠️ ASP.NET requires patch management for known vulnerabilities  

---  

## 5. Port Scanning Results  
**Open Ports**:  
| Port  | Service   | Details                          |  
|-------|-----------|----------------------------------|  
| 80    | HTTP      | Redirects to HTTPS               |  
| 443   | HTTPS     | Valid cert (2025-07-08 expiry)   |  
| 8080  | HTTP-Proxy| Redirects to HTTPS               |  

**Findings**:  
- All services behind Cloudflare protection  
- Robots.txt blocks 6 paths (search/newsletter-related)  
- No vulnerable service versions detected  

---  

## 6. Directory Enumeration  
**Outcome**: Scan timed out - Potential causes:  
- Cloudflare anti-bot protections  
- Server-side rate limiting  
- Network connectivity issues  

---  

## Actionable Recommendations  
### 🔴 Critical  
1. **Email Security**:  
   - Deploy SPF record: `v=spf1 include:spf.protection.outlook.com -all`  
   - Implement DKIM for all email-sending domains  

### 🟠 High Priority  
2. **Subdomain Management**:  
   - Restrict public access to `dev.*` and `staging.*` subdomains  
   - Audit API endpoints (`api.fpt.com`, `api.digital-accounting.fpt.com`) for authentication flaws  

3. **ASP.NET Hardening**:  
   - Validate all forms use `__RequestVerificationToken`  
   - Apply patches for ASP.NET request validation bypass (CVE-2023-33170)  

### 🟢 General Improvements  
4. **Monitoring**:  
   - Set certificate expiry alerts (current SSL cert expires 2025-07-08)  
   - Monitor DNS for unauthorized changes  

5. **Scanning Adjustments**:  
   - Use authenticated scans to bypass Cloudflare protections for internal testing  
   - Schedule scans during maintenance windows to avoid timeout issues  

---  

## Conclusion  
fpt.com demonstrates strong foundational security with Cloudflare protection, DNSSEC, and HSTS. Primary risks stem from email configuration gaps (SPF/DKIM) and exposed subdomains. Immediate action on email authentication and subdomain access controls is recommended.