---
description: Generate comprehensive test cases automatically
category: code-analysis-testing
argument-hint: "Specify test case requirements"
---

# Generate Test Cases

Generate comprehensive test cases automatically

## Instructions

1. **Target Analysis and Scope Definition**
   - Parse target file or function from arguments: `$ARGUMENTS`
   - If no target specified, analyze current directory and prompt for specific target
   - Examine the target code structure, dependencies, and complexity
   - Identify function signatures, parameters, return types, and side effects
   - Determine testing scope (unit, integration, or both)

2. **Code Structure Analysis**
   - Analyze function logic, branching, and control flow
   - Identify input validation, error handling, and edge cases
   - Examine external dependencies, API calls, and database interactions
   - Review data transformations and business logic
   - Identify async operations and error scenarios

3. **Test Case Generation Strategy**
   - Generate positive test cases for normal operation flows
   - Create negative test cases for error conditions and invalid inputs
   - Generate edge cases for boundary conditions and limits
   - Create integration test cases for external dependencies
   - Generate performance test cases for complex operations

4. **Unit Test Implementation**
   - Create test file following project naming conventions
   - Set up test framework imports and configuration
   - Generate test suites organized by functionality
   - Create comprehensive test cases with descriptive names
   - Implement proper setup and teardown for each test

5. **Mock and Stub Generation**
   - Identify external dependencies requiring mocking
   - Generate mock implementations for APIs and services
   - Create stub data for database and file system operations
   - Set up spy functions for monitoring function calls
   - Configure mock return values and error scenarios

6. **Data-Driven Test Generation**
   - Create test data sets for various input scenarios
   - Generate parameterized tests for multiple input combinations
   - Create fixtures for complex data structures
   - Set up test data factories for consistent data generation
   - Generate property-based test cases for comprehensive coverage

7. **Integration Test Scenarios**
   - Generate tests for component interactions
   - Create end-to-end workflow test cases
   - Generate API integration test scenarios
   - Create database integration tests with real data
   - Generate cross-module integration test cases

8. **Error Handling and Exception Testing**
   - Generate tests for all error conditions and exceptions
   - Create tests for timeout and network failure scenarios
   - Generate tests for invalid input validation
   - Create tests for resource exhaustion and limits
   - Generate tests for concurrent access and race conditions

9. **Test Quality and Coverage**
   - Ensure comprehensive code coverage for target functions
   - Generate tests for all code branches and paths
   - Create tests for both success and failure scenarios
   - Validate test assertions are meaningful and specific
   - Ensure tests are isolated and independent

10. **Test Documentation and Maintenance**
    - Generate clear test descriptions and documentation
    - Create comments explaining complex test scenarios
    - Document test data requirements and setup procedures
    - Generate test maintenance guidelines and best practices
    - Create test execution and debugging instructions
    - Validate generated tests execute successfully and provide meaningful feedback