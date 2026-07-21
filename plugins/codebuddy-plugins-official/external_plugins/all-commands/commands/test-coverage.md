---
description: Analyze and report test coverage
category: code-analysis-testing
argument-hint: 1. **Coverage Tool Setup**
allowed-tools: Bash(npm *), Write
---

# Test Coverage Command

Analyze and report test coverage

## Instructions

Follow this systematic approach to analyze and improve test coverage: **$ARGUMENTS**

1. **Coverage Tool Setup**
   - Identify and configure appropriate coverage tools:
     - JavaScript/Node.js: Jest, NYC, Istanbul
     - Python: Coverage.py, pytest-cov
     - Java: JaCoCo, Cobertura
     - C#: dotCover, OpenCover
     - Ruby: SimpleCov
   - Configure coverage reporting formats (HTML, XML, JSON)
   - Set up coverage thresholds and quality gates

2. **Baseline Coverage Analysis**
   - Run existing tests with coverage reporting
   - Generate comprehensive coverage reports
   - Document current coverage percentages:
     - Line coverage
     - Branch coverage
     - Function coverage
     - Statement coverage
   - Identify uncovered code areas

3. **Coverage Report Analysis**
   - Review detailed coverage reports by file and directory
   - Identify critical uncovered code paths
   - Analyze branch coverage for conditional logic
   - Find untested functions and methods
   - Examine coverage trends over time

4. **Critical Path Identification**
   - Identify business-critical code that lacks coverage
   - Prioritize high-risk, low-coverage areas
   - Focus on public APIs and interfaces
   - Target error handling and edge cases
   - Examine security-sensitive code paths

5. **Test Gap Analysis**
   - Categorize uncovered code:
     - Business logic requiring immediate testing
     - Error handling and exception paths
     - Configuration and setup code
     - Utility functions and helpers
     - Dead or obsolete code to remove

6. **Strategic Test Writing**
   - Write unit tests for uncovered business logic
   - Add integration tests for uncovered workflows
   - Create tests for error conditions and edge cases
   - Test configuration and environment-specific code
   - Add regression tests for bug-prone areas

7. **Branch Coverage Improvement**
   - Identify uncovered conditional branches
   - Test both true and false conditions
   - Cover all switch/case statements
   - Test exception handling paths
   - Verify loop conditions and iterations

8. **Edge Case Testing**
   - Test boundary conditions and limits
   - Test null, empty, and invalid inputs
   - Test timeout and network failure scenarios
   - Test resource exhaustion conditions
   - Test concurrent access and race conditions

9. **Mock and Stub Strategy**
   - Mock external dependencies for better isolation
   - Stub complex operations to focus on logic
   - Use dependency injection for testability
   - Create test doubles for external services
   - Implement proper cleanup for test resources

10. **Performance Impact Assessment**
    - Measure test execution time with new tests
    - Optimize slow tests without losing coverage
    - Parallelize test execution where possible
    - Balance coverage goals with execution speed
    - Consider test categorization (fast/slow, unit/integration)

11. **Coverage Quality Assessment**
    - Ensure tests actually verify behavior, not just execution
    - Check for meaningful assertions in tests
    - Avoid testing implementation details
    - Focus on testing contracts and interfaces
    - Review test quality alongside coverage metrics

12. **Framework-Specific Coverage Enhancement**
    
    **For Web Applications:**
    - Test API endpoints and HTTP status codes
    - Test form validation and user input handling
    - Test authentication and authorization flows
    - Test error pages and user feedback

    **For Mobile Applications:**
    - Test device-specific functionality
    - Test different screen sizes and orientations
    - Test offline and network connectivity scenarios
    - Test platform-specific features

    **For Backend Services:**
    - Test database operations and transactions
    - Test message queue processing
    - Test caching and performance optimizations
    - Test service integrations and API calls

13. **Continuous Coverage Monitoring**
    - Set up automated coverage reporting in CI/CD
    - Configure coverage thresholds to prevent regression
    - Generate coverage badges and reports
    - Monitor coverage trends and improvements
    - Alert on significant coverage decreases

14. **Coverage Exclusion Management**
    - Properly exclude auto-generated code
    - Exclude third-party libraries and dependencies
    - Document reasons for coverage exclusions
    - Regularly review and update exclusion rules
    - Avoid excluding code that should be tested

15. **Team Coverage Goals**
    - Set realistic coverage targets based on project needs
    - Establish minimum coverage requirements for new code
    - Create coverage improvement roadmap
    - Review coverage in code reviews
    - Celebrate coverage milestones and improvements

16. **Coverage Reporting and Communication**
    - Generate clear, actionable coverage reports
    - Create coverage dashboards for stakeholders
    - Document coverage improvement strategies
    - Share coverage results with development team
    - Integrate coverage into project health metrics

17. **Mutation Testing (Advanced)**
    - Implement mutation testing to validate test quality
    - Identify tests that don't catch actual bugs
    - Improve test assertions and edge case coverage
    - Use mutation testing tools specific to your language
    - Balance mutation testing cost with quality benefits

18. **Legacy Code Coverage Strategy**
    - Prioritize high-risk legacy code for testing
    - Use characterization tests for complex legacy systems
    - Refactor for testability where possible
    - Add tests before making changes to legacy code
    - Document known limitations and technical debt

**Sample Coverage Commands:**

```bash
# JavaScript with Jest
npm test -- --coverage --coverage-reporters=html,text,lcov

# Python with pytest
pytest --cov=src --cov-report=html --cov-report=term

# Java with Maven
mvn clean test jacoco:report

# .NET Core
dotnet test --collect:"XPlat Code Coverage"
```

Remember that 100% coverage is not always the goal - focus on meaningful coverage that actually improves code quality and catches bugs.