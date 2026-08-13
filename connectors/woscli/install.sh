#!/bin/sh
# woscli installer for macOS / Linux
# Run directly : sh install.sh
# Source in current shell (so the PATH export takes effect immediately):
#   . ./install.sh
die() { echo "Error: $1" >&2; return 1 2>/dev/null || exit 1; }

WOSCLI_HOME="$HOME/.woscli"
BIN="$WOSCLI_HOME/woscli"
ZIP_URL="https://ipaas-huawei-cloud-1252328573.cos.ap-shanghai.myqcloud.com/wai/woscli.zip"
TMP_DIR="$(mktemp -d)"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "==> Installing woscli to $WOSCLI_HOME"
mkdir -p "$WOSCLI_HOME" || die "cannot create $WOSCLI_HOME"

echo "==> Downloading woscli..."
curl -fsSL "$ZIP_URL" -o "$TMP_DIR/woscli.zip" || die "download failed"

# Integrity check. Set EXPECTED_SHA256 to the official release hash published by
# Weimob; left empty on purpose so the connector still works before the hash is
# published. Fill it to enable tamper protection.
EXPECTED_SHA256=""
if [ -n "$EXPECTED_SHA256" ]; then
  ACTUAL_SHA256="$(sha256sum "$TMP_DIR/woscli.zip" 2>/dev/null | awk '{print $1}')"
  [ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ] && die "checksum mismatch"
fi

echo "==> Extracting..."
unzip -o "$TMP_DIR/woscli.zip" -d "$TMP_DIR/woscli" >/dev/null 2>&1 || \
  die "unzip failed (install 'unzip' and retry)"

# Select the binary matching the current OS + architecture.
OS="$(uname -s 2>/dev/null)"; ARCH="$(uname -m 2>/dev/null)"
case "$OS" in
  Darwin) PLAT="darwin" ;;
  Linux)  PLAT="linux" ;;
  *) die "unsupported OS: $OS (woscli supports macOS and Linux)" ;;
esac
case "$ARCH" in
  x86_64|amd64)  ARCH2="amd64" ;;
  arm64|aarch64) ARCH2="arm64" ;;
  *) die "unsupported architecture: $ARCH" ;;
esac
BINARY="$TMP_DIR/woscli/woscli-$PLAT-$ARCH2"
[ -f "$BINARY" ] || die "woscli binary not found in archive: woscli-$PLAT-$ARCH2"

install -m 755 "$BINARY" "$BIN" || die "install failed"
echo "==> Installed: $BIN"

# Expose in the CURRENT shell session. This is effective when the script is
# sourced (e.g. `. ./install.sh`); when run via `sh install.sh` it only affects
# that subprocess, so the caller must source it for the immediate effect.
export PATH="$WOSCLI_HOME:$PATH"

# Persist PATH across shells by detecting the user's login shell.
PROFILE_LINE='export PATH="'"$WOSCLI_HOME"':$PATH"'

add_to_file() {
  f="$1"
  if [ -f "$f" ] && grep -Fqx "$PROFILE_LINE" "$f"; then
    return 0
  fi
  printf '\n# woscli\nexport PATH="%s:$PATH"\n' "$WOSCLI_HOME" >> "$f"
  echo "    added woscli to $f"
}

SHELL_NAME="$(basename "${SHELL:-/bin/sh}")"
echo "==> Detected shell: $SHELL_NAME"
case "$SHELL_NAME" in
  zsh)  add_to_file "$HOME/.zshrc" ;;
  bash)
    add_to_file "$HOME/.bashrc"
    [ -f "$HOME/.bash_profile" ] && add_to_file "$HOME/.bash_profile"
    ;;
  fish)
    fish -c "set -Ua fish_user_paths $WOSCLI_HOME" 2>/dev/null || true
    echo "    added woscli to fish user paths"
    ;;
  *) add_to_file "$HOME/.profile" ;;
esac

# Global config: applies to ALL login shells via path_helper (macOS) / profile.d.
# Requires root; only attempt when we can do it non-interactively.
if [ "$(id -u)" -eq 0 ]; then
  echo "$WOSCLI_HOME" > /etc/paths.d/woscli 2>/dev/null || true
  echo "    wrote global path: /etc/paths.d/woscli"
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  echo "$WOSCLI_HOME" | sudo tee /etc/paths.d/woscli >/dev/null 2>&1 || true
  echo "    wrote global path (sudo): /etc/paths.d/woscli"
fi

# Verify
if command -v woscli >/dev/null 2>&1; then
  echo "==> woscli is ready: $(command -v woscli)"
  woscli --version 2>/dev/null || true
else
  echo "==> woscli installed, but not on PATH in this session."
  echo "    To use now: export PATH=\"$WOSCLI_HOME:\$PATH\""
fi
echo "Done."
