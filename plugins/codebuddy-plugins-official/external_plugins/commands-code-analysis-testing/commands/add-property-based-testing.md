---
description: Implement property-based testing framework
category: code-analysis-testing
---

# Add Property-Based Testing

Implement property-based testing framework

## Instructions

1. **Property-Based Testing Analysis**
   - Analyze current codebase to identify functions suitable for property-based testing
   - Identify mathematical properties, invariants, and business rules to test
   - Assess existing testing infrastructure and integration requirements
   - Determine scope of property-based testing implementation
   - Plan integration with existing unit and integration tests

2. **Framework Selection and Installation**
   - Choose appropriate property-based testing framework:
     - **JavaScript/TypeScript**: fast-check, JSVerify
     - **Python**: Hypothesis, QuickCheck
     - **Java**: jqwik, QuickTheories
     - **C#**: FsCheck, CsCheck
     - **Rust**: proptest, quickcheck
     - **Go**: gopter, quick
   - Install framework and configure with existing test runner
   - Set up framework integration with build system

3. **Property Definition and Implementation**
   - Define mathematical properties and invariants for core functions
   - Implement property tests for data transformation functions
   - Create property tests for API contract validation
   - Set up property tests for business logic validation
   - Define properties for data structure consistency

4. **Test Data Generation**
   - Configure generators for primitive data types
   - Create custom generators for domain-specific objects
   - Set up composite generators for complex data structures
   - Configure generator constraints and boundaries
   - Implement shrinking strategies for minimal failing examples

5. **Property Test Categories**
   - **Roundtrip Properties**: Serialize/deserialize, encode/decode operations
   - **Invariant Properties**: Data structure consistency, business rule validation
   - **Metamorphic Properties**: Equivalent operations, transformation consistency
   - **Model-Based Properties**: State machine testing, system behavior validation
   - **Oracle Properties**: Comparison with reference implementations

6. **Integration with Existing Tests**
   - Integrate property-based tests with existing test suites
   - Configure test execution order and dependencies
   - Set up property test reporting and coverage tracking
   - Configure test timeout and resource management
   - Implement property test categorization and tagging

7. **Advanced Testing Strategies**
   - Set up stateful property testing for complex systems
   - Configure model-based testing for state machines
   - Implement targeted property testing for known issues
   - Set up regression property testing for bug prevention
   - Configure performance property testing for algorithmic validation

8. **Test Configuration and Tuning**
   - Configure test case generation limits and timeouts
   - Set up shrinking parameters and strategies
   - Configure random seed management for reproducibility
   - Set up test distribution and statistical analysis
   - Configure parallel test execution and resource management

9. **CI/CD Integration**
   - Configure property-based tests in continuous integration
   - Set up test result reporting and failure analysis
   - Configure test execution policies and resource limits
   - Set up automated property test maintenance
   - Configure property test performance monitoring

10. **Documentation and Team Training**
    - Create comprehensive property-based testing documentation
    - Document property definition patterns and best practices
    - Create examples and templates for common property patterns
    - Train team on property-based testing concepts and implementation
    - Set up property test maintenance and evolution guidelines
    - Document troubleshooting procedures for property test failures