# Contributing Guide

Thank you for considering contributing to playwright-scraper-skill!

## 🐛 Reporting Issues

If you find a bug or have a feature suggestion:

1. Check [Issues](https://github.com/waisimon/playwright-scraper-skill/issues) to see if it already exists
2. If not, create a new Issue
3. Provide the following information:
   - Problem description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (Node.js version, OS)
   - Error messages (if any)

## 💡 Feature Requests

1. Create an Issue with `[Feature Request]` in the title
2. Explain:
   - The desired feature
   - Use cases
   - Why this feature would be useful

## 🔧 Submitting Code

### Setting Up Development Environment

```bash
# Fork the repo and clone
git clone https://github.com/YOUR_USERNAME/playwright-scraper-skill.git
cd playwright-scraper-skill

# Install dependencies
npm install
npx playwright install chromium

# Test
node scripts/playwright-simple.js https://example.com
```

### Contribution Workflow

1. Create a new branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Make your changes

3. Test your changes:
   ```bash
   npm test
   node scripts/playwright-stealth.js <test-URL>
   ```

4. Commit:
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

5. Push and create a Pull Request:
   ```bash
   git push origin feature/my-new-feature
   ```

### Commit Message Guidelines

Use clear commit messages:

- `Add: new feature`
- `Fix: issue description`
- `Update: existing feature`
- `Refactor: code refactoring`
- `Docs: documentation update`
- `Test: add or modify tests`

Example:
```
Fix: playwright-stealth.js screenshot timeout issue

- Increase timeout parameter to 10 seconds
- Add try-catch error handling
- Update documentation
```

## 📝 Documentation

If your changes affect usage:

- Update `SKILL.md` (full documentation)
- Update `README.md` (quick reference)
- Update `examples/README.md` (if adding new examples)
- Update `CHANGELOG.md` (record changes)

## ✅ Checklist

Before submitting a PR, confirm:

- [ ] Code runs properly
- [ ] Doesn't break existing functionality
- [ ] Updated relevant documentation
- [ ] Clear commit messages
- [ ] No sensitive information (API keys, personal paths, etc.)

## 🎯 Priority Areas

Currently welcoming contributions in:

1. **New anti-bot techniques** — Improve success rates
2. **Support more websites** — Test and share success cases
3. **Performance optimization** — Speed up scraping
4. **Error handling** — Better error messages and recovery
5. **Documentation improvements** — Clearer explanations and examples

## 🚫 Unaccepted Contributions

- Adding complex dependencies (keep it lightweight)
- Features violating privacy or laws
- Breaking existing API changes (unless well justified)

## 📞 Contact

Have questions? Feel free to:
- Create an Issue for discussion
- Ask in Pull Request comments

---

Thank you for your contribution! 🙏
