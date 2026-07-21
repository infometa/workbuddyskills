---
description: Implement secure user authentication system
category: security-audit
---

# Add Authentication System

Implement secure user authentication system

## Instructions

1. **Authentication Strategy Analysis**
   - Analyze application requirements and user types
   - Define authentication methods (password, OAuth, SSO, MFA)
   - Assess security requirements and compliance needs
   - Plan user management and role-based access control
   - Evaluate existing authentication infrastructure and integration points

2. **Authentication Method Selection**
   - Choose appropriate authentication strategies:
     - **Username/Password**: Traditional credential-based authentication
     - **OAuth 2.0/OpenID Connect**: Third-party authentication (Google, GitHub, etc.)
     - **SAML**: Enterprise single sign-on integration
     - **JWT**: Stateless token-based authentication
     - **Multi-Factor Authentication**: SMS, TOTP, hardware tokens
     - **Passwordless**: Magic links, WebAuthn, biometric authentication

3. **User Management System**
   - Set up user registration and account creation workflows
   - Configure user profile management and data storage
   - Implement password policies and security requirements
   - Set up account verification and email confirmation
   - Configure user deactivation and account deletion procedures

4. **Authentication Implementation**
   - Implement secure password hashing (bcrypt, Argon2, scrypt)
   - Set up session management and token generation
   - Configure secure cookie handling and CSRF protection
   - Implement authentication middleware and route protection
   - Set up authentication state management (client-side)

5. **Authorization and Access Control**
   - Implement role-based access control (RBAC) system
   - Set up permission-based authorization
   - Configure resource-level access controls
   - Implement dynamic authorization and policy engines
   - Set up API endpoint protection and authorization

6. **Multi-Factor Authentication (MFA)**
   - Configure TOTP-based authenticator app support
   - Set up SMS-based authentication codes
   - Implement backup codes and recovery mechanisms
   - Configure hardware token support (FIDO2/WebAuthn)
   - Set up MFA enforcement policies and user experience

7. **OAuth and Third-Party Integration**
   - Configure OAuth providers (Google, GitHub, Facebook, etc.)
   - Set up OpenID Connect for identity federation
   - Implement social login and account linking
   - Configure enterprise SSO integration (SAML, LDAP)
   - Set up API key management for external integrations

8. **Security Implementation**
   - Configure rate limiting and brute force protection
   - Set up account lockout and security monitoring
   - Implement security headers and session security
   - Configure audit logging and security event tracking
   - Set up vulnerability scanning and security testing

9. **User Experience and Frontend Integration**
   - Create responsive authentication UI components
   - Implement client-side authentication state management
   - Set up protected route handling and redirects
   - Configure authentication error handling and user feedback
   - Implement remember me and persistent login features

10. **Testing and Maintenance**
    - Set up comprehensive authentication testing
    - Configure security testing and penetration testing
    - Create authentication monitoring and alerting
    - Set up compliance reporting and audit trails
    - Train team on authentication security best practices
    - Create incident response procedures for security events