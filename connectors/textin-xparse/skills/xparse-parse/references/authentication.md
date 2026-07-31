# Authentication

`xparse-cli` supports three explicit authentication paths while preserving the
legacy AppKey workflow. In an interactive terminal, bare `xparse-cli auth`
opens a menu for OAuth, AppKey, status, and logout. With piped/non-terminal
input it keeps the legacy AppKey prompt contract.

## WorkBuddy

WorkBuddy v5 uses the Connector's native Device Code Flow:

```bash
xparse-cli --profile workbuddy auth device --open-browser=always --output=jsonl
```

The CLI opens `verification_uri_complete` automatically when a desktop browser
is available. WorkBuddy also extracts `verification_uri_complete` and
`user_code`, presents its Device Code Modal as a fallback, and leaves the CLI
process running while the CLI polls the token endpoint. The CLI saves
credentials only after authorization succeeds.

The `workbuddy` profile stores credentials under
`~/.xparse-cli/profiles/workbuddy/`. Login and logout in WorkBuddy therefore do
not affect standalone credentials directly under `~/.xparse-cli`.

WorkBuddy task shells do not inherit Connector lifecycle environment variables.
Every CLI command issued by the installed Skill must therefore include
`--profile workbuddy`. This profile also marks API requests with
`X-From: workbuddy`.

The Skill must not:

- request, store, or repeat an Access Token, Refresh Token, Secret Code, or
  private `device_code`;
- implement its own callback listener, token polling, or HTTP client;
- start browser PKCE as an automatic fallback from Device OAuth;
- open a separate browser PKCE flow while Device OAuth is in progress.

If Connector status is disconnected, ask the user to reconnect it in
WorkBuddy. Do not collect AppKey credentials in the conversation.

## Standalone Device OAuth

Use this in terminals and on servers without a callback listener. Inside the
interactive TTY auth menu, choosing OAuth selects Device OAuth for SSH or a
Linux session without `DISPLAY`/`WAYLAND_DISPLAY`. Non-TTY and CI automation
must call the explicit Device command; bare `auth` intentionally remains the
legacy AppKey input flow:

```bash
# Print URL/code and do not try to open a browser
xparse-cli auth device --open-browser=never

# Open verification_uri_complete when a desktop browser is available
xparse-cli auth device --open-browser=auto
```

`auto` and `never` run the same Device flow. Automatic browser opening is only a
convenience; authorization state remains on the server and the CLI continues
polling.

Client ID resolution is:

1. `--client-id`
2. `XPARSE_OAUTH_CLIENT_ID`
3. `config.yaml` `oauth.client_id`
4. the shipped public xParse client `cli_textin_xparse`

The default client ID is public application identity, not a client secret. A
private deployment may override it with any of the first three options.

Scope resolution is flag, `XPARSE_OAUTH_SCOPE`, YAML, then `ocr:*`.

## Standalone Browser PKCE

Bare `xparse-cli auth` automatically chooses browser PKCE when a local GUI and
platform opener are available. Explicit commands always override detection:

```bash
xparse-cli auth browser
xparse-cli auth browser --prompt=consent
```

It opens Authorization Code + PKCE and listens only on the configured
`http://127.0.0.1` loopback callback. The default redirect uses port `0`, so
the operating system chooses an available ephemeral port; an explicitly
configured fixed port is still honored. `--prompt=consent` forces a fresh
authorization confirmation instead of reusing remembered consent.

Explicit `auth browser` fails fast in SSH/CI/headless mode and recommends
Device OAuth. `--open-browser=never` remains available for advanced explicit
port-forwarding setups.

## Standalone AppKey

The explicit legacy command remains compatible:

```bash
xparse-cli auth app-key
```

Bare `xparse-cli auth` only keeps the direct AppKey behavior for non-terminal
input; in a terminal it opens the authentication menu.

For automation, callers may provide a complete pair through
`XPARSE_APP_ID` and `XPARSE_SECRET_CODE`. Never print or copy the Secret into
agent output.

## Status and logout

```bash
xparse-cli auth status --output=json
xparse-cli auth logout --method oauth
xparse-cli auth logout --method app-key
xparse-cli auth logout --method all
```

Status is local and does not make a network request. An expired access token
with a still-usable refresh token remains logged in; the next paid OAuth parse
refreshes it. Logout attempts RFC 7009 remote revocation first (Refresh Token
preferred) and then removes the local token. A remote failure is a stderr
warning and does not prevent local logout. Logout does not delete remembered
consent; use the next browser login with `--prompt=consent` when a fresh
confirmation is required.

Omitting `--api` and using `--api auto` or `--api free` always selects the
anonymous free endpoint, whether credentials exist or not. A successful login
records the preferred authentication method only for an explicit
`--api paid` request. In paid mode, old configuration files remain AppKey-first
when both AppKey and OAuth exist, and `--auth-method` temporarily overrides
that paid-mode preference.
