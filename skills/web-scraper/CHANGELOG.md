# Changelog — web-scraper

All notable changes to this skill will be documented in this file.

## [1.0.0] — 2025-02-23

### Added
- Initial release
- 5-stage extraction pipeline
- News/article detection with URL pattern and Schema.org analysis
- Multi-strategy cascade (static HTTP → Playwright → Scrapy)
- Boilerplate removal via trafilatura
- Structured metadata extraction with YAML config
- LLM entity extraction via OpenRouter (optional)
- Rate limiting with exponential backoff
- Incremental saving and checkpointing
- Paywall detection (hard/soft/none)
