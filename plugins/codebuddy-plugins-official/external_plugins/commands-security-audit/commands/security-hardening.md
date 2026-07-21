---
description: Harden application security configuration
category: security-audit
---

# Security Hardening

Harden application security configuration

## Instructions

1. **Security Assessment and Baseline**
   - Conduct comprehensive security audit of current application
   - Identify potential vulnerabilities and attack vectors
   - Analyze authentication and authorization mechanisms
   - Review data handling and storage practices
   - Assess network security and communication protocols

2. **Authentication and Authorization Hardening**
   - Implement strong password policies and multi-factor authentication
   - Configure secure session management with proper timeouts
   - Set up role-based access control (RBAC) with least privilege principle
   - Implement JWT security best practices or secure session tokens
   - Configure account lockout and brute force protection

3. **Input Validation and Sanitization**
   - Implement comprehensive input validation for all user inputs
   - Set up SQL injection prevention with parameterized queries
   - Configure XSS protection with proper output encoding
   - Implement CSRF protection with tokens and SameSite cookies
   - Set up file upload security with type validation and sandboxing

4. **Secure Communication**
   - Configure HTTPS with strong TLS/SSL certificates
   - Implement HTTP Strict Transport Security (HSTS)
   - Set up secure API communication with proper authentication
   - Configure certificate pinning for mobile applications
   - Implement end-to-end encryption for sensitive data transmission

5. **Data Protection and Encryption**
   - Implement encryption at rest for sensitive data
   - Configure secure key management and rotation
   - Set up database encryption and access controls
   - Implement proper secrets management (avoid hardcoded secrets)
   - Configure secure backup and recovery procedures

6. **Security Headers and Policies**
   - Configure Content Security Policy (CSP) headers
   - Set up X-Frame-Options and X-Content-Type-Options headers
   - Implement Referrer Policy and Feature Policy headers
   - Configure CORS policies with proper origin validation
   - Set up security.txt file for responsible disclosure

7. **Dependency and Supply Chain Security**
   - Audit and update all dependencies to latest secure versions
   - Implement dependency vulnerability scanning
   - Configure automated security updates for critical dependencies
   - Set up software composition analysis (SCA) tools
   - Implement dependency pinning and integrity checks

8. **Infrastructure Security**
   - Configure firewall rules and network segmentation
   - Implement intrusion detection and prevention systems
   - Set up secure logging and monitoring
   - Configure secure container images and runtime security
   - Implement infrastructure as code security scanning

9. **Application Security Controls**
   - Implement rate limiting and DDoS protection
   - Set up web application firewall (WAF) rules
   - Configure secure error handling without information disclosure
   - Implement proper logging for security events
   - Set up security monitoring and alerting

10. **Security Testing and Validation**
    - Conduct penetration testing and vulnerability assessments
    - Implement automated security testing in CI/CD pipeline
    - Set up static application security testing (SAST)
    - Configure dynamic application security testing (DAST)
    - Create security incident response plan and procedures
    - Document security controls and compliance requirements