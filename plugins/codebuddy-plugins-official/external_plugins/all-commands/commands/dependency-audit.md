---
description: Audit dependencies for security vulnerabilities
category: security-audit
---

# Dependency Audit Command

Audit dependencies for security vulnerabilities

## Instructions

Perform a comprehensive dependency audit following these steps:

1. **Dependency Discovery**
   - Identify all dependency management files (package.json, requirements.txt, Cargo.toml, pom.xml, etc.)
   - Map direct vs transitive dependencies
   - Check for lock files and version consistency
   - Review development vs production dependencies

2. **Version Analysis**
   - Check for outdated packages and available updates
   - Identify packages with major version updates available
   - Review semantic versioning compliance
   - Analyze version pinning strategies

3. **Security Vulnerability Scan**
   - Run security audits using appropriate tools:
     - `npm audit` for Node.js projects
     - `pip-audit` for Python projects
     - `cargo audit` for Rust projects
     - GitHub security advisories for all platforms
   - Identify critical, high, medium, and low severity vulnerabilities
   - Check for known exploits and CVE references

4. **License Compliance**
   - Review all dependency licenses for compatibility
   - Identify restrictive licenses (GPL, AGPL, etc.)
   - Check for license conflicts with project license
   - Document license obligations and requirements

5. **Dependency Health Assessment**
   - Check package maintenance status and activity
   - Review contributor count and community support
   - Analyze release frequency and stability
   - Identify abandoned or deprecated packages

6. **Size and Performance Impact**
   - Analyze bundle size impact of each dependency
   - Identify large dependencies that could be optimized
   - Check for duplicate functionality across dependencies
   - Review tree-shaking and dead code elimination effectiveness

7. **Alternative Analysis**
   - Identify dependencies with better alternatives
   - Check for lighter or more efficient replacements
   - Analyze feature overlap and consolidation opportunities
   - Review native alternatives (built-in functions vs libraries)

8. **Dependency Conflicts**
   - Check for version conflicts between dependencies
   - Identify peer dependency issues
   - Review dependency resolution strategies
   - Analyze potential breaking changes in updates

9. **Build and Development Impact**
   - Review dependencies that affect build times
   - Check for development-only dependencies in production
   - Analyze tooling dependencies and alternatives
   - Review optional dependencies and their necessity

10. **Supply Chain Security**
    - Check for typosquatting and malicious packages
    - Review package authenticity and signatures
    - Analyze dependency sources and registries
    - Check for suspicious or unusual dependencies

11. **Update Strategy Planning**
    - Create a prioritized update plan based on security and stability
    - Identify breaking changes and required code modifications
    - Plan for testing strategy during updates
    - Document rollback procedures for problematic updates

12. **Monitoring and Automation**
    - Set up automated dependency scanning
    - Configure security alerts and notifications
    - Review dependency update automation tools
    - Establish regular audit schedules

13. **Documentation and Reporting**
    - Create a comprehensive dependency inventory
    - Document all security findings with remediation steps
    - Provide update recommendations with priority levels
    - Generate executive summary for stakeholders

Use platform-specific tools and databases for the most accurate results. Focus on actionable recommendations with clear risk assessments.