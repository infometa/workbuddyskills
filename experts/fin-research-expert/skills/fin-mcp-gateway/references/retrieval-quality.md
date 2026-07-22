# Retrieval And Evidence Quality

Load this reference for public-market research that needs identity resolution,
more than one evidence type, empty-result recovery, or evidence-gap wording. It
governs retrieval and answer semantics; it does not add tools or data rights.

## 1. Start From The User's Evidence Tasks

1. Identify the subject, market, time window, and explicitly requested evidence
   types.
2. For a named security or industry, confirm identity before detailed calls.
   Reuse resolver-returned codes and source IDs. If multiple candidates remain,
   ask the user to choose; never guess an internal ID.
3. Split a compound question into independently checkable tasks such as market,
   announcement, research, news, graph, or Tongzhou viewpoint evidence.
4. Make the original Connector business call directly. Do not run a local file,
   Shell, environment-variable, credential, API-Key, or `mcp-session-id`
   precheck.
5. A single-intent question stays single-domain. Do not call unrelated sources
   merely to make the answer look comprehensive.

## 2. Broad Recall, Narrow Conclusion

- For open research questions, cover each evidence type the user requested,
  then narrow the conclusion to what actually returned.
- In document retrieval, do not combine company name, ticker, document type,
  source, and a short time window in the first call unless every filter is
  required by the tool contract.
- After a broad result identifies the document or period, a narrower call may
  retrieve detail.
- Preserve successful evidence when another task is empty or fails. One source cannot silently stand in for a missing source type.

## 3. Evidence States

Every evidence task must have exactly one state:

| State | Meaning | User-facing wording |
|---|---|---|
| `found` | Target evidence and required fields returned | `截至 [日期]，[来源类型] 返回……` |
| `partial` | Some evidence returned but fields, dates, or source coverage are incomplete | `已命中 [部分]；当前缺少 [缺口]` |
| `empty` | The request succeeded but the disclosed range returned no record | `在 [时间/来源范围] 内当前未命中` |
| `unsupported` | The current capability does not cover the request | `当前数据源暂不覆盖 [范围]` |
| `error` | Parameter, timeout, service, or protocol failure prevented completion | `[来源类型] 本次请求未完成或暂时不可用` |
| `auth_required` | First authorization or reconnection is required | `需要先完成连接授权；授权后将重试本次请求一次` |

`empty`, `unsupported`, `error`, and `auth_required` are not company or market facts. Never turn them into `公司没有公告`, `公司没有研报`, `市场没有新闻`, or
an equivalent absence claim.

Treat a non-empty response as `partial` when a field required by the user's
question is missing. Report successful fields beside their own dates and units;
do not discard the whole response or fill missing fields from memory.

## 4. Recovery Budget

For one evidence task, perform at most two recovery attempts after an `empty`,
`partial`, or correctable parameter result. Use only a reasoned sequence:

1. `normalize_subject`: normalize the confirmed name, ticker, or market suffix.
2. `split_intent`: separate a compound request into single evidence types.
3. `relax_time` or `relax_source`: remove one demonstrably over-narrow filter.
4. `explicit_fallback`: use only a same-evidence fallback declared by the Layer
   1 contract or capability catalog.

Stop as soon as the requested evidence is sufficient. Do not restart the budget per synonym, source, or tool. Timeouts and service failures are `error`; preserve
other successful evidence and do not hide them behind repeated rewrites.

Authorization is separate from query recovery: after the user completes OAuth,
retry only the original business call once. Do not probe credentials or switch
to a local bridge.

## 5. Source Boundaries

| Evidence | Primary domain | Allowed supplement | Forbidden substitution |
|---|---|---|---|
| Market, financials, valuation, K line | Fin Data | resolved identity | a number quoted only by news |
| Announcement, research report, news | Doc Search | Tongzhou interpretation | news presented as an announcement or report |
| Industry or chain identity and relations | Fin Graph | returned public factors | model memory presented as graph evidence |
| Tongzhou article or viewpoint | Same Boat | its underlying public source | a login or portal page presented as article-level evidence |

Keep each returned source type, data date, reporting period, currency, and unit.
When dates conflict, show them separately. Do not label HKD or USD values as CNY
and do not imply an older period is real time.

## 6. Answer Contract

- Put key values next to their actual date, currency, unit, and source type.
- Separate returned facts, interpretation, conflicting evidence, and gaps.
- Keep a genuine article-level link when the tool returned one. Without an
  article-level link, name only the source type; no fake links, reconstructed
  URLs, login pages, or portal pages.
- Use Chinese market colors: up, positive return, bullish, or favorable is red;
  down, negative return, bearish, or unfavorable is green. Always include signs
  or text so color is not the only signal.
- Include the four-part boundary: AI generated, based on public information,
  not investment advice, and not an individual-stock recommendation.

Never expose Gateway, database, internal server or tool grants, internal IDs,
raw parameters, API-Key status, OAuth tokens, or `MCP session ID`. Never read
personal holdings or trade history, promise returns, or provide personalized
position and buy/sell instructions.
