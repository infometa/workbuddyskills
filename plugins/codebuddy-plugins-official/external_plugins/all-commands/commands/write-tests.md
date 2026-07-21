---
description: Write unit and integration tests
category: code-analysis-testing
argument-hint: 1. **Test Framework Detection**
allowed-tools: Write
---

# Write Tests Command

Write unit and integration tests

## Instructions

Follow this systematic approach to write effective tests: **$ARGUMENTS**

1. **Test Framework Detection**
   - Identify the testing framework in use (Jest, Mocha, PyTest, RSpec, etc.)
   - Review existing test structure and conventions
   - Check test configuration files and setup
   - Understand project-specific testing patterns

2. **Code Analysis for Testing**
   - Analyze the code that needs testing
   - Identify public interfaces and critical business logic
   - Map out dependencies and external interactions
   - Understand error conditions and edge cases

3. **Test Strategy Planning**
   - Determine test levels needed:
     - Unit tests for individual functions/methods
     - Integration tests for component interactions
     - End-to-end tests for user workflows
   - Plan test coverage goals and priorities
   - Identify mock and stub requirements

4. **Unit Test Implementation**
   - Test individual functions and methods in isolation
   - Cover happy path scenarios first
   - Test edge cases and boundary conditions
   - Test error conditions and exception handling
   - Use proper assertions and expectations

5. **Test Structure and Organization**
   - Follow the AAA pattern (Arrange, Act, Assert)
   - Use descriptive test names that explain the scenario
   - Group related tests using test suites/describe blocks
   - Keep tests focused and atomic

6. **Mocking and Stubbing**
   - Mock external dependencies and services
   - Stub complex operations for unit tests
   - Use proper isolation for reliable tests
   - Avoid over-mocking that makes tests brittle

7. **Data Setup and Teardown**
   - Create test fixtures and sample data
   - Set up and tear down test environments cleanly
   - Use factories or builders for complex test data
   - Ensure tests don't interfere with each other

8. **Integration Test Writing**
   - Test component interactions and data flow
   - Test API endpoints with various scenarios
   - Test database operations and transactions
   - Test external service integrations

9. **Error and Exception Testing**
   - Test all error conditions and exception paths
   - Verify proper error messages and codes
   - Test error recovery and fallback mechanisms
   - Test validation and security scenarios

10. **Performance and Load Testing**
    - Add performance tests for critical operations
    - Test under different load conditions
    - Verify memory usage and resource cleanup
    - Test timeout and rate limiting scenarios

11. **Security Testing**
    - Test authentication and authorization
    - Test input validation and sanitization
    - Test for common security vulnerabilities
    - Test access control and permissions

12. **Accessibility Testing (for UI)**
    - Test keyboard navigation and screen readers
    - Test color contrast and visual accessibility
    - Test ARIA attributes and semantic markup
    - Test with assistive technology simulations

13. **Cross-Platform Testing**
    - Test on different operating systems
    - Test on different browsers (for web apps)
    - Test on different device sizes and resolutions
    - Test with different versions of dependencies

14. **Test Utilities and Helpers**
    - Create reusable test utilities and helpers
    - Build test data factories and builders
    - Create custom matchers and assertions
    - Set up common test setup and teardown functions

15. **Snapshot and Visual Testing**
    - Use snapshot testing for UI components
    - Implement visual regression testing
    - Test rendered output and markup
    - Version control snapshots properly

16. **Async Testing**
    - Test asynchronous operations properly
    - Use appropriate async testing patterns
    - Test promise resolution and rejection
    - Test callback and event-driven code

17. **Test Documentation**
    - Document complex test scenarios and reasoning
    - Add comments for non-obvious test logic
    - Create test documentation for team reference
    - Document test data requirements and setup

18. **Test Maintenance**
    - Keep tests up to date with code changes
    - Refactor tests when code is refactored
    - Remove obsolete tests and update assertions
    - Monitor and fix flaky tests

**Framework-Specific Guidelines:**

**Jest/JavaScript:**
```javascript
describe('ComponentName', () => {
  beforeEach(() => {
    // Setup
  });

  it('should handle valid input correctly', () => {
    // Arrange
    const input = 'test';
    // Act
    const result = functionToTest(input);
    // Assert
    expect(result).toBe(expectedValue);
  });
});
```

**PyTest/Python:**
```python
class TestClassName:
    def setup_method(self):
        # Setup
        pass

    def test_should_handle_valid_input(self):
        # Arrange
        input_data = "test"
        # Act
        result = function_to_test(input_data)
        # Assert
        assert result == expected_value
```

**RSpec/Ruby:**
```ruby
RSpec.describe ClassName do
  describe '#method_name' do
    it 'handles valid input correctly' do
      # Arrange
      input = 'test'
      # Act
      result = subject.method_name(input)
      # Assert
      expect(result).to eq(expected_value)
    end
  end
end
```

Remember to prioritize testing critical business logic and user-facing functionality first, then expand coverage to supporting code.