'use strict';

// Execution host and viewing client are independent: a PC can also use a cloud sandbox.
function resolveClientContext(env = process.env, platform = process.platform) {
  const explicit = String(env.WORKBUDDY_CLIENT_TYPE || '').trim().toLowerCase();
  const explicitDesktop = ['pc', 'desktop', 'mac', 'windows', 'linux'].includes(explicit);
  const cloud = Boolean(String(env.AGENTOS_RUNTIME_ID || '').trim())
    || env.WORKBUDDY_CLOUD_RUNTIME === '1'
    || ['cloud', 'cloud_agent', 'cloud-agent'].includes(explicit);
  const graphicalLinux = platform === 'linux'
    && Boolean(String(env.DISPLAY || '').trim() || String(env.WAYLAND_DISPLAY || '').trim());
  const headless = platform === 'linux' && !graphicalLinux;
  const browserCapableHost = platform === 'darwin' || platform === 'win32' || graphicalLinux;
  const runtime = cloud ? 'cloud' : headless ? 'headless' : 'desktop';
  let clientType;
  let surface;
  let surfaceSource = 'client';

  if (['miniprogram', 'mobile', 'ios', 'android'].includes(explicit)) {
    clientType = explicit === 'miniprogram' ? 'miniprogram' : 'mobile';
    surface = 'mobile';
  } else if (explicitDesktop) {
    clientType = ['pc', 'desktop'].includes(explicit)
      ? (platform === 'darwin' ? 'mac' : platform === 'win32' ? 'windows' : 'linux')
      : explicit;
    surface = 'desktop';
  } else if (['cloud', 'cloud_agent', 'cloud-agent'].includes(explicit)) {
    clientType = 'cloud';
    surface = 'mobile';
    surfaceSource = 'portable-fallback';
  } else if (platform === 'darwin' || platform === 'win32') {
    // WorkBuddy 桌面端可能同时注入云端运行标记，但脚本实际仍运行在
    // 用户电脑上。此时以可验证的本机平台能力为准，允许唤起默认浏览器。
    clientType = platform === 'darwin' ? 'mac' : 'windows';
    surface = 'desktop';
    surfaceSource = 'platform';
  } else if (cloud || headless) {
    clientType = runtime;
    // Conservative presentation fallback, not a claim that a Linux host is a phone.
    surface = 'mobile';
    surfaceSource = 'portable-fallback';
  } else {
    clientType = platform === 'darwin' ? 'mac' : platform === 'win32' ? 'windows' : 'linux';
    surface = 'desktop';
    surfaceSource = 'platform';
  }

  return {
    clientType,
    runtime,
    surface,
    surfaceSource,
    // 云端标记描述执行上下文，不应覆盖明确的 PC 查看端；真正无图形的
    // Linux 仍不会尝试打开浏览器。
    openBrowser: surface === 'desktop' && browserCapableHost
  };
}

module.exports = { resolveClientContext };
