---
description: Configure load and performance testing
category: code-analysis-testing
---

# Setup Load Testing

Configure load and performance testing

## Instructions

1. **Load Testing Strategy and Requirements**
   - Analyze application architecture and identify performance-critical components
   - Define load testing objectives (capacity planning, performance validation, bottleneck identification)
   - Determine testing scenarios (normal load, peak load, stress testing, spike testing)
   - Identify key performance metrics and acceptance criteria
   - Plan load testing environments and infrastructure requirements

2. **Load Testing Tool Selection**
   - Choose appropriate load testing tools based on requirements:
     - **k6**: Modern, developer-friendly with JavaScript scripting
     - **Artillery**: Simple, powerful, great for CI/CD integration
     - **JMeter**: Feature-rich GUI and command-line tool
     - **Gatling**: High-performance tool with detailed reporting
     - **Locust**: Python-based with web UI and distributed testing
     - **WebPageTest**: Web performance and real user monitoring
   - Consider factors: scripting language, reporting, CI integration, cost

3. **Test Environment Setup**
   - Set up dedicated load testing environment matching production
   - Configure test data and database setup for consistent testing
   - Set up network configuration and firewall rules
   - Configure monitoring and observability for test environment
   - Set up test isolation and cleanup procedures

4. **Load Test Script Development**
   - Create test scripts for critical user journeys and API endpoints
   - Implement realistic user behavior patterns and think times
   - Set up test data generation and management
   - Configure authentication and session management
   - Implement parameterization and data-driven testing

5. **Performance Scenarios Configuration**
   - **Load Testing**: Normal expected traffic patterns
   - **Stress Testing**: Beyond normal capacity to find breaking points
   - **Spike Testing**: Sudden traffic increases and decreases
   - **Volume Testing**: Large amounts of data processing
   - **Endurance Testing**: Extended periods under normal load
   - **Capacity Testing**: Maximum user load determination

6. **Monitoring and Metrics Collection**
   - Set up application performance monitoring during tests
   - Configure infrastructure metrics collection (CPU, memory, disk, network)
   - Set up database performance monitoring and query analysis
   - Configure real-time dashboards and alerting
   - Set up log aggregation and error tracking

7. **Test Execution and Automation**
   - Configure automated test execution and scheduling
   - Set up test result collection and analysis
   - Configure test environment provisioning and teardown
   - Set up parallel and distributed test execution
   - Configure test result storage and historical tracking

8. **Performance Analysis and Reporting**
   - Set up automated performance analysis and threshold checking
   - Configure performance trend analysis and regression detection
   - Set up detailed performance reporting and visualization
   - Configure performance alerts and notifications
   - Set up performance benchmark and baseline management

9. **CI/CD Integration**
   - Integrate load tests into continuous integration pipeline
   - Configure performance gates and deployment blocking
   - Set up automated performance regression detection
   - Configure test result integration with development workflow
   - Set up performance testing in staging and pre-production environments

10. **Optimization and Maintenance**
    - Document load testing procedures and maintenance guidelines
    - Set up load test script maintenance and version control
    - Configure test environment maintenance and updates
    - Create performance optimization recommendations workflow
    - Train team on load testing best practices and tool usage
    - Set up performance testing standards and conventions