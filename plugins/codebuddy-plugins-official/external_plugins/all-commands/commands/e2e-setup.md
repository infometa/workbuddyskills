---
description: Configure end-to-end testing suite
category: code-analysis-testing
argument-hint: 1. **Technology Stack Assessment**
allowed-tools: Bash(npm *)
---

# End-to-End Testing Setup Command

Configure end-to-end testing suite

## Instructions

Follow this systematic approach to implement E2E testing: **$ARGUMENTS**

1. **Technology Stack Assessment**
   - Identify the application type (web app, mobile app, API service)
   - Review existing testing infrastructure
   - Determine target browsers and devices
   - Assess current deployment and staging environments

2. **E2E Framework Selection**
   - Choose appropriate E2E testing framework based on stack:
     - **Playwright**: Modern, fast, supports multiple browsers
     - **Cypress**: Developer-friendly, great debugging tools
     - **Selenium WebDriver**: Cross-browser, mature ecosystem
     - **Puppeteer**: Chrome-focused, good for performance testing
     - **TestCafe**: No WebDriver needed, easy setup
   - Consider team expertise and project requirements

3. **Test Environment Setup**
   - Set up dedicated testing environments (staging, QA)
   - Configure test databases with sample data
   - Set up environment variables and configuration
   - Ensure environment isolation and reproducibility

4. **Framework Installation and Configuration**
   
   **For Playwright:**
   ```bash
   npm install -D @playwright/test
   npx playwright install
   npx playwright codegen # Record tests
   ```

   **For Cypress:**
   ```bash
   npm install -D cypress
   npx cypress open
   ```

   **For Selenium:**
   ```bash
   npm install -D selenium-webdriver
   # Install browser drivers
   ```

5. **Test Structure Organization**
   - Create logical test folder structure:
     ```
     e2e/
     ├── tests/
     │   ├── auth/
     │   ├── user-flows/
     │   └── api/
     ├── fixtures/
     ├── support/
     │   ├── commands/
     │   └── page-objects/
     └── config/
     ```
   - Organize tests by feature or user journey
   - Separate API tests from UI tests

6. **Page Object Model Implementation**
   - Create page object classes for better maintainability
   - Encapsulate element selectors and interactions
   - Implement reusable methods for common actions
   - Follow single responsibility principle for page objects

   **Example Page Object:**
   ```javascript
   class LoginPage {
     constructor(page) {
       this.page = page;
       this.emailInput = page.locator('#email');
       this.passwordInput = page.locator('#password');
       this.loginButton = page.locator('#login-btn');
     }

     async login(email, password) {
       await this.emailInput.fill(email);
       await this.passwordInput.fill(password);
       await this.loginButton.click();
     }
   }
   ```

7. **Test Data Management**
   - Create test fixtures and sample data
   - Implement data factories for dynamic test data
   - Set up database seeding for consistent test states
   - Use environment-specific test data
   - Implement test data cleanup strategies

8. **Core User Journey Testing**
   - Implement critical user flows:
     - User registration and authentication
     - Main application workflows
     - Payment and transaction flows
     - Search and filtering functionality
     - Form submissions and validations

9. **Cross-Browser Testing Setup**
   - Configure testing across multiple browsers
   - Set up browser-specific configurations
   - Implement responsive design testing
   - Test on different viewport sizes

   **Playwright Browser Configuration:**
   ```javascript
   module.exports = {
     projects: [
       { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
       { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
       { name: 'webkit', use: { ...devices['Desktop Safari'] } },
       { name: 'mobile', use: { ...devices['iPhone 12'] } },
     ],
   };
   ```

10. **API Testing Integration**
    - Test API endpoints alongside UI tests
    - Implement API request/response validation
    - Test authentication and authorization
    - Verify data consistency between API and UI

11. **Visual Testing Setup**
    - Implement screenshot comparison testing
    - Set up visual regression testing
    - Configure tolerance levels for visual changes
    - Organize visual baselines and updates

12. **Test Utilities and Helpers**
    - Create custom commands and utilities
    - Implement common assertion helpers
    - Set up authentication helpers
    - Create database and state management utilities

13. **Error Handling and Debugging**
    - Configure proper error reporting and screenshots
    - Set up video recording for failed tests
    - Implement retry mechanisms for flaky tests
    - Create debugging tools and helpers

14. **CI/CD Integration**
    - Configure E2E tests in CI/CD pipeline
    - Set up parallel test execution
    - Implement proper test reporting
    - Configure test environment provisioning

   **GitHub Actions Example:**
   ```yaml
   - name: Run Playwright tests
     run: npx playwright test
   - uses: actions/upload-artifact@v3
     if: always()
     with:
       name: playwright-report
       path: playwright-report/
   ```

15. **Performance Testing Integration**
    - Add performance assertions to E2E tests
    - Monitor page load times and metrics
    - Test under different network conditions
    - Implement lighthouse audits integration

16. **Accessibility Testing**
    - Integrate accessibility testing tools (axe-core)
    - Test keyboard navigation flows
    - Verify screen reader compatibility
    - Check color contrast and WCAG compliance

17. **Mobile Testing Setup**
    - Configure mobile device emulation
    - Test responsive design breakpoints
    - Implement touch gesture testing
    - Test mobile-specific features

18. **Reporting and Monitoring**
    - Set up comprehensive test reporting
    - Configure test result notifications
    - Implement test metrics and analytics
    - Create dashboards for test health monitoring

19. **Test Maintenance Strategy**
    - Implement test stability monitoring
    - Set up automatic test updates for UI changes
    - Create test review and update processes
    - Document test maintenance procedures

20. **Security Testing Integration**
    - Test authentication and authorization flows
    - Implement security headers validation
    - Test input sanitization and XSS prevention
    - Verify HTTPS and secure cookie handling

**Sample E2E Test:**
```javascript
test('user can complete purchase flow', async ({ page }) => {
  // Navigate and login
  await page.goto('/login');
  await page.fill('#email', 'test@example.com');
  await page.fill('#password', 'password');
  await page.click('#login-btn');

  // Add item to cart
  await page.goto('/products');
  await page.click('[data-testid="product-1"]');
  await page.click('#add-to-cart');

  // Complete checkout
  await page.goto('/checkout');
  await page.fill('#card-number', '4111111111111111');
  await page.click('#place-order');

  // Verify success
  await expect(page.locator('#order-confirmation')).toBeVisible();
});
```

Remember to start with critical user journeys and gradually expand coverage. Focus on stable, maintainable tests that provide real value.