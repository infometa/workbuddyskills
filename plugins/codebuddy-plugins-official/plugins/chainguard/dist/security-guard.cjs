#!/usr/bin/env node
/**
 * Security Guard - MCP Hook Client (CJS Bundle)
 * 
 * 供应链安全防? Hook，拦截依赖安装操作进行安全审?
 * 
 * 生成时间: 2026-10-21T10:19:46.693Z
 * 源文件数: 45
 * 格式: CommonJS
 * 
 * 使用方式:
 *   echo '{"tool_name": "Write", ...}' | node hook.cjs
 * 
 * 此文件由 scripts/bundle-cjs.js 自动生成，请勿手动编?
 */

'use strict';



const child_process = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const https = require('https');
const os = require('os');
const path = require('path');
const url = require('url');


// ============================================================================
// Fail-Open 安全? - 任何未捕获异常都放行
// ============================================================================
const __fs__ = require('fs');

// 最早的错误日志函数（用于解析阶段之后的错误?
function __logError__(type, err) {
  try {
    const timestamp = new Date().toISOString();
    const msg = `[${timestamp}] [${type}] ${err.stack || err}\n`;
    __fs__.appendFileSync('/tmp/security-guard.log', msg);
  } catch {}
}

const __FAIL_OPEN_RESPONSE__ = JSON.stringify({
  suppressOutput: true,
  hookSpecificOutput: {
    hookEventName: 'PreToolUse',
    permissionDecision: 'allow',
    permissionDecisionReason: 'uncaught_exception_fail_open'
  }
});

process.on('uncaughtException', (err) => {
  __logError__('CRASH', err);
  process.stdout.write(__FAIL_OPEN_RESPONSE__);
  process.exit(0);
});

process.on('unhandledRejection', (reason) => {
  __logError__('UNHANDLED', reason);
  process.stdout.write(__FAIL_OPEN_RESPONSE__);
  process.exit(0);
});



const __ui__ = {};
const __filters_privacy__ = {};
const __version__ = {};
const __risk_policy__ = {};
const __parsers_manifests_package_json__ = {};
const __parsers_manifests_package_lock_json__ = {};
const __parsers_manifests_requirements__ = {};
const __parsers_manifests_go_mod__ = {};
const __parsers_manifests_cargo_toml__ = {};
const __parsers_manifests_pom_xml__ = {};
const __parsers_manifests_gemfile__ = {};
const __parsers_manifests_composer_json__ = {};
const __parsers_manifests_pipfile__ = {};
const __parsers_manifests_pyproject_toml__ = {};
const __parsers_manifests_index__ = {};
const __parsers_commands_name_only__ = {};
const __parsers_commands_npm__ = {};
const __parsers_commands_pip__ = {};
const __parsers_commands_go__ = {};
const __parsers_commands_cargo__ = {};
const __parsers_commands_gem__ = {};
const __parsers_commands_composer__ = {};
const __parsers_commands_mvn__ = {};
const __parsers_commands_index__ = {};
const __parsers_lockfiles_resolve_installed__ = {};
const __parsers_repl__ = {};
const __parsers_input__ = {};
const __auth_token_manager__ = {};
const __auth_session_reader__ = {};
const __tls__ = {};
const __repo__ = {};
const __local_audit_adapter__ = {};
const __local_audit_npm_audit__ = {};
const __client__ = {};
const __autofix_manifest_adapter_npm__ = {};
const __response__ = {};
const __operation_router__ = {};
const __redactor__ = {};
const __audit_log__ = {};
const __rollout__ = {};
const __telemetry__ = {};
const __dedup__ = {};
const __build_info__ = {};
const __adoption__ = {};
const __index__ = {};


// ============================================================================
// Module: ui
// ============================================================================

(function() {
  /**
   * UI Reporter
   * 
   * 调试信息写入日志文件，不输出到 stdout/stderr
   * 确保 Hook 输出只有纯 JSON
   */
  
  const { appendFileSync, statSync, renameSync, unlinkSync } = require('fs');
  
  const LOG_FILE = '/tmp/security-guard.log';
  const LOG_FILE_OLD = '/tmp/security-guard.log.1';
  const MAX_LOG_SIZE = 5 * 1024 * 1024; // 5MB
  
  // 全局 debug 标志，由 main() 初始化时设置
  let globalDebugMode = false;
  
  /**
   * 简单日志轮转：超过 MAX_LOG_SIZE 时将当前文件重命名为 .1，只保留一个备份
   * 每 50 次写入检查一次大小，避免频繁 stat
   */
  let writeCount = 0;
  function rotateIfNeeded() {
    if (++writeCount % 50 !== 0) return;
    try {
      const stat = statSync(LOG_FILE);
      if (stat.size >= MAX_LOG_SIZE) {
        try { unlinkSync(LOG_FILE_OLD); } catch { /* ignore */ }
        renameSync(LOG_FILE, LOG_FILE_OLD);
      }
    } catch {
      // 文件不存在或无法 stat，无需轮转
    }
  }
  
  /**
   * 设置全局 debug 模式
   */
  function setGlobalDebugMode(enabled) {
    globalDebugMode = enabled;
  }
  
  /**
   * 返回本地时间戳字符串，格式: 2026-03-03T10:52:49.576+08:00
   */
  function localTimestamp() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    const ms = String(d.getMilliseconds()).padStart(3, '0');
    const offset = -d.getTimezoneOffset();
    const sign = offset >= 0 ? '+' : '-';
    const oh = pad(Math.floor(Math.abs(offset) / 60));
    const om = pad(Math.abs(offset) % 60);
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${ms}${sign}${oh}:${om}`;
  }
  
  /**
   * UI 输出类
   * 
   * 所有输出写入日志文件，不污染 stdout/stderr
   */
  class UI {
    constructor(debugMode = false) {
      this.debugMode = debugMode;
    }
    
    /**
     * 写入日志文件（静默失败）
     * 
     * security-guard.log 默认关闭，仅在 debug 模式下记录
     */
    static log(message) {
      try {
        if (!globalDebugMode) {
          return;
        }
  
        const timestamp = localTimestamp();
        rotateIfNeeded();
        appendFileSync(LOG_FILE, `${timestamp} ${message}\n`);
      } catch {
        // 静默忽略日志写入失败
      }
    }
    
    /**
     * 输出调试信息到日志文件
     */
    debug(...args) {
      if (!this.debugMode) return;
      
      const message = args.map(arg => {
        if (typeof arg === 'object') {
          return JSON.stringify(arg, null, 2);
        }
        return String(arg);
      }).join(' ');
      
      UI.log(`[DEBUG] ${message}`);
    }
    
    /**
     * 记录性能/耗时信息到日志文件
     * 性能日志始终记录，不受debug模式限制
     */
    performance(message) {
      UI.log(`[PERFORMANCE] ${message}`);
    }
  }
  
  __ui__.default = UI;
  
  
  // Module exports
  __ui__.setGlobalDebugMode = setGlobalDebugMode;
  __ui__.localTimestamp = localTimestamp;
  __ui__.UI = UI;
})();


// ============================================================================
// Module: filters_privacy
// ============================================================================

(function() {
  /**
   * Privacy Filter
   * 
   * 本地隐私过滤器，防止敏感信息泄露到公网 Server
   * 
   * 过滤规则：
   * 1. 私有 scope 包（@internal/, @company/, @private/ 等）
   * 2. 本地路径包（file:, link:, workspace:）
   * 3. 带 Token/凭证的 URL
   * 4. 内网域名包
   * 5. 用户自定义的私有前缀
   */
  
  // ============================================================================
  // 默认配置
  // ============================================================================
  
  /**
   * 默认私有 scope 前缀
   * 这些前缀的包不会发送到公网 Server
   */
  const DEFAULT_PRIVATE_SCOPES = [
    '@internal/',
    '@private/',
    '@corp/',
    '@company/',
    '@enterprise/',
    '@local/',
    '@dev/',
    '@test/',
  ];
  
  /**
   * 默认需要过滤的包名模式
   */
  const DEFAULT_FILTER_PATTERNS = [
    // 本地引用
    /^file:/i,
    /^link:/i,
    /^workspace:/i,
    /^portal:/i,
    
    // 本地路径
    /^\.\.?\//,           // ./ 或 ../
    /^\/[^@]/,            // /absolute/path (排除 /@scope)
    /\.tgz$/i,            // 本地 tarball
    /\.tar\.gz$/i,
    
    // Git URL（可能包含 Token）
    /^git(\+https?|\+ssh)?:/i,
    /^github:/i,
    /^gitlab:/i,
    /^bitbucket:/i,
    
    // HTTP URL（可能包含凭证）
    /^https?:\/\//i,
    
    // 带凭证的 URL 模式
    /[:@].*@/,            // user:pass@host 或 token@host
    /\?.*token=/i,        // ?token=xxx
    /\?.*auth=/i,         // ?auth=xxx
    /\?.*key=/i,          // ?key=xxx
  ];
  
  /**
   * 默认内网域名模式
   */
  const DEFAULT_INTERNAL_DOMAINS = [
    /\.internal\./i,
    /\.local$/i,
    /\.corp\./i,
    /\.intranet\./i,
    /localhost/i,
    /127\.0\.0\.1/,
    /192\.168\./,
    /10\.\d+\./,
    /172\.(1[6-9]|2\d|3[01])\./,
  ];
  
  // ============================================================================
  // 过滤函数
  // ============================================================================
  
  /**
   * 检查包名是否为私有 scope
   * 
   * @param {string} name - 包名
   * @param {string[]} privateScopes - 私有 scope 列表
   * @returns {boolean} 是否为私有包
   */
  function isPrivateScope(name, privateScopes) {
    if (!name || typeof name !== 'string') {
      return false;
    }
    
    const lowerName = name.toLowerCase();
    
    for (const scope of privateScopes) {
      if (lowerName.startsWith(scope.toLowerCase())) {
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * 检查包名是否匹配过滤模式
   * 
   * @param {string} name - 包名
   * @param {RegExp[]} patterns - 过滤模式列表
   * @returns {boolean} 是否应过滤
   */
  function matchesFilterPattern(name, patterns) {
    if (!name || typeof name !== 'string') {
      return false;
    }
    
    for (const pattern of patterns) {
      if (pattern.test(name)) {
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * 检查版本字符串是否包含敏感信息
   * 
   * @param {string} version - 版本字符串
   * @param {RegExp[]} patterns - 过滤模式列表
   * @returns {boolean} 是否包含敏感信息
   */
  function versionContainsSensitive(version, patterns) {
    if (!version || typeof version !== 'string') {
      return false;
    }
    
    // 检查版本字符串是否为 URL 或路径
    for (const pattern of patterns) {
      if (pattern.test(version)) {
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * 检查是否包含内网域名
   * 
   * @param {string} str - 字符串
   * @param {RegExp[]} internalDomains - 内网域名模式
   * @returns {boolean} 是否包含内网域名
   */
  function containsInternalDomain(str, internalDomains) {
    if (!str || typeof str !== 'string') {
      return false;
    }
    
    for (const pattern of internalDomains) {
      if (pattern.test(str)) {
        return true;
      }
    }
    
    return false;
  }
  
  // ============================================================================
  // 主过滤函数
  // ============================================================================
  
  /**
   * 过滤私有包和敏感信息
   * 
   * @param {Array<{n: string, v: string}>} packages - 包列表
   * @param {Object} options - 配置选项
   * @param {string[]} options.privateScopes - 额外的私有 scope
   * @param {RegExp[]} options.filterPatterns - 额外的过滤模式
   * @param {string[]} options.allowList - 白名单（这些包总是允许）
   * @param {boolean} options.debug - 是否输出调试信息
   * @returns {Object} { filtered: [{n, v}], removed: [{n, v, reason}] }
   */
  function filterPrivatePackages(packages, options = {}) {
    const {
      privateScopes = [],
      filterPatterns = [],
      internalDomains = [],
      allowList = [],
      debug = false
    } = options;
    
    // 合并默认配置和用户配置
    const allPrivateScopes = [...DEFAULT_PRIVATE_SCOPES, ...privateScopes];
    const allFilterPatterns = [...DEFAULT_FILTER_PATTERNS, ...filterPatterns];
    const allInternalDomains = [...DEFAULT_INTERNAL_DOMAINS, ...internalDomains];
    
    // 白名单 Set（用于快速查找）
    const allowSet = new Set(allowList.map(p => p.toLowerCase()));
    
    const filtered = [];
    const removed = [];
    
    for (const pkg of packages) {
      const { n: name, v: version } = pkg;
      
      // 白名单检查
      if (allowSet.has(name?.toLowerCase())) {
        filtered.push(pkg);
        continue;
      }
      
      // 1. 检查私有 scope
      if (isPrivateScope(name, allPrivateScopes)) {
        removed.push({ ...pkg, reason: 'private_scope' });
        continue;
      }
      
      // 2. 检查包名模式
      if (matchesFilterPattern(name, allFilterPatterns)) {
        removed.push({ ...pkg, reason: 'filter_pattern_name' });
        continue;
      }
      
      // 3. 检查版本字符串
      if (versionContainsSensitive(version, allFilterPatterns)) {
        removed.push({ ...pkg, reason: 'filter_pattern_version' });
        continue;
      }
      
      // 4. 检查内网域名
      if (containsInternalDomain(name, allInternalDomains) || 
          containsInternalDomain(version, allInternalDomains)) {
        removed.push({ ...pkg, reason: 'internal_domain' });
        continue;
      }
      
      // 通过所有检查，保留
      filtered.push(pkg);
    }
    
    // 不输出任何调试信息到 stdout/stderr，只返回结果
    return {
      filtered,
      removed,
      stats: {
        total: packages.length,
        kept: filtered.length,
        removed: removed.length
      }
    };
  }
  
  /**
   * 创建自定义过滤器
   * 
   * @param {Object} config - 过滤器配置
   * @returns {Function} 过滤函数
   */
  function createPrivacyFilter(config = {}) {
    return (packages) => filterPrivatePackages(packages, config);
  }
  
  const VALID_MODES = new Set(['smooth', 'audit', 'strict']);
  
  /**
   * O1-13：解析产品模式（mode）。
   *
   * 三种模式：
   * - smooth: 默认。安全结果静默 allow，可修复时自动修改输入，只对不可自动处理
   *   的高风险问题 deny。服务降级默认 allow。
   * - audit: 不修改原工具输入（disableAutofix=true），不因普通 CVE/License 阻断
   *   开发（BLOCK→allow+记录），但仍然 deny PACKAGE_NOT_FOUND（幻觉风险）和 fatal
   *   （熔断）。记录完整结构化结果。极端恶意 deny 由企业策略配置（本切片中
   *   PACKAGE_NOT_FOUND + fatal 作为默认 deny 保留）。
   * - strict: 高风险 deny，coverage degraded 可按企业策略 fail-closed。
   *
   * 遗留变量 SECURITY_GUARD_DISABLE_AUTOFIX 仍然被读取，作为 mode 未显式
   * 设置时的历史输入源。
   *
   * @returns {{mode: 'smooth'|'audit'|'strict', source: 'explicit'|'legacy_env'|'default'|'invalid_fallback'}}
   */
  function resolveMode() {
    const rawMode = (process.env.SECURITY_GUARD_MODE || '').trim().toLowerCase();
  
    if (rawMode && VALID_MODES.has(rawMode)) {
      return { mode: rawMode, source: 'explicit' };
    }
  
    // 遗留变量归一化：未设置合法 mode 时，用 SECURITY_GUARD_DISABLE_AUTOFIX
    // 推断——保持与改动前完全一致的默认行为（未设置任何变量时 disableAutofix
    // 默认为 true，对应 strict）
    const legacyDisableAutofixEnv = process.env.SECURITY_GUARD_DISABLE_AUTOFIX;
    const inferredMode = legacyDisableAutofixEnv !== 'false' ? 'strict' : 'smooth';
  
    if (rawMode && !VALID_MODES.has(rawMode)) {
      // 显式请求了一个不支持的模式——诚实回退，不静默接受
      return { mode: inferredMode, source: 'invalid_fallback' };
    }
  
    if (legacyDisableAutofixEnv !== undefined) {
      return { mode: inferredMode, source: 'legacy_env' };
    }
  
    return { mode: inferredMode, source: 'default' };
  }
  
  /**
   * 从环境变量加载私有 scope 配置
   * 
   * 环境变量：
   * - SECURITY_GUARD_PRIVATE_SCOPES: 逗号分隔的私有 scope 列表
   * - SECURITY_GUARD_ALLOW_LIST: 逗号分隔的白名单包列表
   * - CODEBUDDY_DEBUG / MCP_DEBUG: 设为 '1' 启用调试模式
   * - SECURITY_GUARD_HIGH_THRESHOLD: 高危 CVSS 阈值（默认 9.0）
   * - SECURITY_GUARD_MEDIUM_THRESHOLD: 中危 CVSS 阈值（默认 4.0）
   * - SECURITY_GUARD_AUDIT_LOG: 审计日志路径（默认 null，使用 DEFAULT_AUDIT_LOG）
   * - SECURITY_GUARD_MODE: 'smooth' | 'strict'（O1-13，见 resolveMode()）
   * - SECURITY_GUARD_DISABLE_AUTOFIX: 遗留变量，未设置 SECURITY_GUARD_MODE 时
   *   作为 mode 的历史输入源（设为 'false' 归一化为 smooth，其余归一化为 strict）
   * - SECURITY_GUARD_ALLOW_MAJOR_AUTOFIX: risk-policy 维度（设为 'true' 开启）
   *
   * 关于 SECURITY_GUARD_ALLOW_MAJOR_AUTOFIX 的 v1 范围说明：
   *   Mode（strict↔smooth）只决定交互摩擦量；risk-policy 决定机器授权边界，两者
   *   正交——smooth=true 绝不等于"可以做高爆炸半径修改"。本变量只是把 risk-policy
   *   的取值读出来并贯穿 context/审计，**v1 尚未开放自动跨 Major 行为**：即使为
   *   true，跨 Major 仍然进入人工 checkpoint，只在审计标记里记录 opted_in_pending，
   *   用于先观测真实诉求量再决定是否解锁行为。
   * 
   * @returns {Object} 配置对象
   */
  function loadConfigFromEnv() {
    const { mode, source: modeSource } = resolveMode();
  
    const config = {
      privateScopes: [],
      allowList: [],
      debug: process.env.CODEBUDDY_DEBUG === '1' || process.env.MCP_DEBUG === '1',
      // 分级审查配置
      highThreshold:   parseFloat(process.env.SECURITY_GUARD_HIGH_THRESHOLD)   || 9.0,
      mediumThreshold: parseFloat(process.env.SECURITY_GUARD_MEDIUM_THRESHOLD) || 4.0,
      mode,
      modeSource,
      // audit 模式不修改原工具输入（disableAutofix=true），且在 response.js 中
      // BLOCK 决策会被降级为 allow+记录（除 PACKAGE_NOT_FOUND 和 fatal 外）
      disableAutofix:  mode === 'strict' || mode === 'audit',
      auditMode:       mode === 'audit',
      auditLog:        process.env.SECURITY_GUARD_AUDIT_LOG || null,
      // risk-policy 维度：机器授权边界（safe-only ↔ major-autofix-enabled）。
      // v1 只铺字段、不解锁行为——见上方 JSDoc 的范围说明。
      majorAutofix:    process.env.SECURITY_GUARD_ALLOW_MAJOR_AUTOFIX === 'true',
    };
  
    // 解析私有 scope（原有逻辑，保持不变）
    const scopesEnv = process.env.SECURITY_GUARD_PRIVATE_SCOPES;
    if (scopesEnv) {
      config.privateScopes = scopesEnv
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
    }
  
    // 解析白名单（原有逻辑，保持不变）
    const allowEnv = process.env.SECURITY_GUARD_ALLOW_LIST;
    if (allowEnv) {
      config.allowList = allowEnv
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
    }
  
    return config;
  }
  
  __filters_privacy__.default = filterPrivatePackages;
  
  
  // Module exports
  __filters_privacy__.filterPrivatePackages = filterPrivatePackages;
  __filters_privacy__.createPrivacyFilter = createPrivacyFilter;
  __filters_privacy__.resolveMode = resolveMode;
  __filters_privacy__.loadConfigFromEnv = loadConfigFromEnv;
})();


// ============================================================================
// Module: version
// ============================================================================

(function() {
  /**
   * Version Scheme Policy（客户端侧）
   *
   * 只回答一个问题：这次修复是否跨 Major（高爆炸半径）。
   *
   * 设计约束（与服务端 P0-1 的分工）：
   * - 服务端 `find_safe_version_ex` 已经保证 `fixed_content` 是同 Major 版本，
   *   跨 Major 只走 `recommended_fix`。本模块是**纵深防御**：面对旧版服务端、
   *   local-audit 或其他来源给出的变更时，客户端仍能自己判定、不静默跨 Major。
   * - 判定不确定时一律返回 false（非跨 Major）。原因：本模块的产出只会触发
   *   "人工 checkpoint"，而误触发会把常规升级全变成硬拦，代价远大于漏判——
   *   漏判时还有服务端契约兜底，误判则直接杀死 smooth 模式的无感率。
   * - calver / 非 semver（如 2023.10 → 2024.1）不判为跨 Major：这类生态的
   *   主版本段是年份，常规升级就会变，判为跨 Major 会误伤（见 P1 #7）。
   */
  
  const CALVER_MIN_YEAR = 1900;
  const CALVER_MAX_YEAR = 2100;
  
  /**
   * 从各种变更表达里抽出裸版本号。
   *
   * 支持：'Django==4.2.7'、'Django>=4.2.30'、'a@1.0.0'、'@scope/pkg@1.2.3'、
   * '4.2.7'、'^4.2'。抽不出数字版本时返回 null（不猜测）。
   *
   * @param {string} spec - 形如 `${name}@${version}` 或带操作符的约束
   * @returns {string|null} 裸版本号，如 '4.2.7'
   */
  function extractVersion(spec) {
    if (typeof spec !== 'string' || spec.trim() === '') return null;
  
    let s = spec.trim();
  
    // 去掉包名：取最后一个 '@' 之后的部分（兼容 '@scope/pkg@1.2.3'）
    const at = s.lastIndexOf('@');
    if (at > 0) s = s.slice(at + 1);
  
    // 去掉比较/范围操作符与空白（'^4.2'、'>= 4.2.30'、'==4.2.7'）
    s = s.replace(/^[^\d]*/, '');
  
    const match = s.match(/^(\d+(?:\.\d+)*)/);
    return match ? match[1] : null;
  }
  
  /**
   * 是否 calver（版本号首段是年份，如 2023.10）。
   *
   * @param {string} version - 裸版本号
   * @returns {boolean}
   */
  function isCalverVersion(version) {
    if (typeof version !== 'string') return false;
    const first = version.split('.')[0];
    if (!/^\d{4}$/.test(first)) return false;
    const year = parseInt(first, 10);
    return year >= CALVER_MIN_YEAR && year <= CALVER_MAX_YEAR;
  }
  
  /**
   * 是否跨 Major（高爆炸半径）。
   *
   * 保守判定：任一版本解析不出、或任一为 calver → 返回 false（不触发 checkpoint）。
   *
   * @param {string} fromSpec - 变更前表达（如 'Django==4.2.7'）
   * @param {string} toSpec   - 变更后表达（如 'Django>=5.0.1'）
   * @returns {boolean}
   */
  function isCrossMajor(fromSpec, toSpec) {
    const from = extractVersion(fromSpec);
    const to = extractVersion(toSpec);
    if (from === null || to === null) return false;
    if (isCalverVersion(from) || isCalverVersion(to)) return false;
  
    const fromMajor = parseInt(from.split('.')[0], 10);
    const toMajor = parseInt(to.split('.')[0], 10);
    if (Number.isNaN(fromMajor) || Number.isNaN(toMajor)) return false;
  
    return fromMajor !== toMajor;
  }
  
  /**
   * 从变更列表中筛出跨 Major 的条目。
   *
   * @param {Array<{from?: string, to?: string}>} changes - 变更列表
   * @returns {Array} 跨 Major 的变更条目
   */
  function findCrossMajorChanges(changes = []) {
    if (!Array.isArray(changes)) return [];
    return changes.filter(c => isCrossMajor(c?.from, c?.to));
  }
  
  /**
   * 比较两个版本号的大小（语义化比较）。
   *
   * @param {string} specA - 版本号或带约束规格
   * @param {string} specB - 版本号或带约束规格
   * @returns {number|null} 1: A > B; 0: A == B; -1: A < B; null: 无法比较
   */
  function compareVersions(specA, specB) {
    if (specA === specB) return 0;
    const vA = extractVersion(specA);
    const vB = extractVersion(specB);
    if (vA === null || vB === null) {
      if (typeof specA === 'string' && typeof specB === 'string') {
        return specA === specB ? 0 : null;
      }
      return null;
    }
    const partsA = vA.split('.').map(n => parseInt(n, 10));
    const partsB = vB.split('.').map(n => parseInt(n, 10));
    const maxLen = Math.max(partsA.length, partsB.length);
    for (let i = 0; i < maxLen; i++) {
      const numA = Number.isNaN(partsA[i]) ? 0 : (partsA[i] ?? 0);
      const numB = Number.isNaN(partsB[i]) ? 0 : (partsB[i] ?? 0);
      if (numA > numB) return 1;
      if (numA < numB) return -1;
    }
    return 0;
  }
  
  
  // Module exports
  __version__.extractVersion = extractVersion;
  __version__.isCalverVersion = isCalverVersion;
  __version__.isCrossMajor = isCrossMajor;
  __version__.findCrossMajorChanges = findCrossMajorChanges;
  __version__.compareVersions = compareVersions;
})();


// ============================================================================
// Module: risk_policy
// ============================================================================

(function() {
  /**
   * Risk Policy
   *
   * 根据漏洞 CVSS 分数对变更列表进行分级判断。
   *
   * 分级：
   *   high   - maxCvss >= highThreshold (默认 9.0)
   *   medium - maxCvss >= mediumThreshold (默认 4.0)
   *   low    - maxCvss > 0
   *   none   - 无变更或 cvss 均为 0/缺失
   */
  
  const DEFAULT_HIGH_THRESHOLD    = 9.0;
  const DEFAULT_MEDIUM_THRESHOLD  = 4.0;
  const DEFAULT_CVSS_WHEN_MISSING = 4.0; // 宁可误报不可漏报
  
  function maxCvss(changes) {
    if (!changes || changes.length === 0) return 0;
    let max = 0;
    for (const c of changes) {
      const score = typeof c.cvss === 'number' ? c.cvss : DEFAULT_CVSS_WHEN_MISSING;
      if (score > max) max = score;
    }
    return max;
  }
  
  function getRiskLevel(changes, config = {}) {
    if (!changes || changes.length === 0) return 'none';
  
    const highThreshold   = config.highThreshold   ?? DEFAULT_HIGH_THRESHOLD;
    const mediumThreshold = config.mediumThreshold ?? DEFAULT_MEDIUM_THRESHOLD;
  
    const score = maxCvss(changes);
    if (score === 0) return 'none';
    if (score >= highThreshold)   return 'high';
    if (score >= mediumThreshold) return 'medium';
    return 'low';
  }
  
  function getMaxCvss(changes) {
    return maxCvss(changes);
  }
  
  
  // Module exports
  __risk_policy__.getRiskLevel = getRiskLevel;
  __risk_policy__.getMaxCvss = getMaxCvss;
})();


// ============================================================================
// Module: parsers_manifests_package_json
// ============================================================================

(function() {
  /**
   * package.json Parser
   * 
   * 解析 npm package.json 文件中的依赖
   */
  
  /**
   * 标准化版本号
   * 
   * 移除版本前缀 (^, ~, >=, >, <, <=, =) 和范围操作符
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 标准化后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
    
    // 跳过特殊版本
    if (
      version.startsWith('git') ||
      version.startsWith('http') ||
      version.startsWith('file:') ||
      version.startsWith('link:') ||
      version.startsWith('workspace:') ||
      version === '*' ||
      version === 'latest' ||
      version === 'next'
    ) {
      return '';
    }
    
    // 处理 npm: 别名
    if (version.startsWith('npm:')) {
      // npm:package@version -> 提取 version
      const match = version.match(/npm:[^@]+@(.+)$/);
      if (match) {
        return normalizeVersion(match[1]);
      }
      return '';
    }
    
    // 移除前缀
    let cleaned = version
      .replace(/^[\^~>=<]+/, '')  // 移除 ^, ~, >=, >, <, <=
      .replace(/^\s*v/, '')       // 移除 v 前缀
      .trim();
    
    // F-05 修复：处理逗号分隔的范围: ">=4.17.1,<5.0.0" -> "4.17.1"
    // (之前逗号分隔的范围会残留 ",<5.0.0" 产生非法版本号)
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[\^~>=<]+/, '').trim();
    }
    
    // 处理范围: ">=1.0.0 <2.0.0" -> "1.0.0"
    if (cleaned.includes(' ')) {
      cleaned = cleaned.split(' ')[0].replace(/^[\^~>=<]+/, '');
    }
    
    // 处理 || 范围: "^1.0.0 || ^2.0.0" -> "1.0.0"
    if (cleaned.includes('||')) {
      cleaned = cleaned.split('||')[0].trim().replace(/^[\^~>=<]+/, '');
    }
    
    // 验证是否为有效版本号 (简单检查)
    if (!/^\d/.test(cleaned)) {
      return '';
    }
    
    return cleaned;
  }
  
  /**
   * 解析 package.json 内容
   * 
   * @param {string} content - package.json 文件内容
   * @returns {Object} 解析结果 { ecosystem: 'npm', packages: [{n, v, section}] }
   */
  function parsePackageJson(content) {
    const result = {
      ecosystem: 'npm',
      packages: []
    };
    
    if (!content || typeof content !== 'string') {
      return result;
    }
    
    let pkg;
    try {
      pkg = JSON.parse(content);
    } catch (error) {
      // JSON 解析失败
      return result;
    }
    
    // 要扫描的依赖块
    const sections = [
      'dependencies',
      'devDependencies',
      'peerDependencies',
      'optionalDependencies'
    ];
    
    for (const section of sections) {
      if (pkg[section] && typeof pkg[section] === 'object') {
        for (const [name, version] of Object.entries(pkg[section])) {
          const normalizedVersion = normalizeVersion(version);
  
          // F-05: Determine resolution_state from original declared spec
          const declaredSpec = typeof version === 'string' ? version : '';
          let resolutionState = 'EXACT';
          if (!declaredSpec || declaredSpec === '*' || declaredSpec === 'latest' || declaredSpec === 'next') {
            resolutionState = 'NAME_ONLY';
          } else if (/[\^~>=<]/.test(declaredSpec) || declaredSpec.includes('||') || declaredSpec.includes(' ')) {
            resolutionState = 'RANGE';
          }
  
          // Skip packages with no parseable version at all
          if (!normalizedVersion && resolutionState !== 'NAME_ONLY') {
            continue;
          }
  
          result.packages.push({
            n: name,
            v: normalizedVersion || '',
            declared_spec: declaredSpec,
            resolution_state: resolutionState,
            section: section
          });
        }
      }
    }
    
    return result;
  }
  
  __parsers_manifests_package_json__.default = parsePackageJson;
  
  
  // Module exports
  __parsers_manifests_package_json__.normalizeVersion = normalizeVersion;
  __parsers_manifests_package_json__.parsePackageJson = parsePackageJson;
})();


// ============================================================================
// Module: parsers_manifests_package_lock_json
// ============================================================================

(function() {
  const normalizeVersion = __parsers_manifests_package_json__.normalizeVersion;
  const parsePackageJson = __parsers_manifests_package_json__.parsePackageJson;
  
  /**
   * npm package-lock.json (v2/v3) Parser —— O1-10（最小切片）
   *
   * 只提取"顶层直接依赖的 resolved exact version"，用于纠正 package.json
   * 里被 normalizeVersion() 剥离成范围下界的近似版本号（如 "^4.17.20" ->
   * "4.17.21"）。这个近似值不是真实
   * resolved version，可能导致 CVE 判断误报或漏报（见
   * fix_update/optimizations/10_Lockfile_Resolved_and_Transitive_Audit.md）。
   *
   * 不读取传递依赖（node_modules/<parent>/node_modules/<name> 这类嵌套
   * 路径），不支持 v1 格式（无 packages 扁平字段的旧版 lockfile）——这些
   * 场景返回空 Map，调用方据此回退到 manifest 声明的版本范围，不阻塞、
   * 不报错、不伪造。
   */
  
  /**
   * 解析 package-lock.json，提取顶层直接依赖的 resolved exact version。
   *
   * @param {string} content - package-lock.json 文件内容
   * @returns {Map<string, string>} 包名 -> resolved exact version
   */
  function parseNpmLockfile(content) {
    const result = new Map();
    if (!content || typeof content !== 'string') return result;
  
    let lock;
    try {
      lock = JSON.parse(content);
    } catch {
      return result;
    }
  
    // 只支持 v2/v3（扁平 packages 字段）；v1（嵌套 dependencies 树）不支持，
    // 静默返回空 Map，调用方回退到 manifest 声明的版本范围
    if (!lock.packages || typeof lock.packages !== 'object') return result;
  
    for (const [pkgPath, meta] of Object.entries(lock.packages)) {
      if (!pkgPath || !meta || typeof meta !== 'object') continue;
      if (!meta.version || typeof meta.version !== 'string') continue;
  
      // 只取顶层 node_modules/<name> 或 node_modules/@scope/<name>（scoped
      // package 路径含一个额外的 "/" 分隔 scope 和包名），排除更深嵌套路径
      // （node_modules/<parent>/node_modules/<name> 这类传递依赖，本次不
      // 读取——文档里"传递依赖可见性"是独立的、需要两层数据模型才能承载的
      // 更大范围，本次只纠正已经在 manifest 里声明的直接依赖版本）
      const match = pkgPath.match(/^node_modules\/((?:@[^/]+\/)?[^/]+)$/);
      if (!match) continue;
  
      result.set(match[1], meta.version);
    }
  
    return result;
  }
  
  /**
   * 将 packages 列表转换为 Map<name, version>
   *
   * @param {Array<{n: string, v: string}>} packages
   * @returns {Map<string, string>}
   */
  function lockfilePackagesToMap(packages) {
    const map = new Map();
    if (!Array.isArray(packages)) return map;
    for (const pkg of packages) {
      if (pkg && pkg.n && pkg.v) {
        map.set(pkg.n, pkg.v);
      }
    }
    return map;
  }
  
  /**
   * 解析 package-lock.json 文件的全部依赖组件
   *
   * @param {string} content - package-lock.json 文件内容
   * @returns {Object} { ecosystem: 'npm', packages: [{n, v}] }
   */
  function parsePackageLockJson(content) {
    const result = {
      ecosystem: 'npm',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    let lock;
    try {
      lock = JSON.parse(content);
    } catch {
      return result;
    }
  
    const seen = new Set();
  
    // 1. v2/v3 lockfile (packages 字段)
    if (lock.packages && typeof lock.packages === 'object') {
      for (const [pkgPath, meta] of Object.entries(lock.packages)) {
        if (!pkgPath || !meta || typeof meta !== 'object') continue;
        if (!meta.version || typeof meta.version !== 'string') continue;
  
        const match = pkgPath.match(/(?:^|\/)node_modules\/((?:@[^/]+\/)?[^/]+)$/);
        if (match) {
          const name = match[1];
          const version = normalizeVersion(meta.version);
          if (name && version) {
            const key = `${name}@${version}`;
            if (!seen.has(key)) {
              seen.add(key);
              result.packages.push({ n: name, v: version });
            }
          }
        }
      }
    }
  
    // 2. v1 lockfile (dependencies 嵌套树) 兜底
    if (result.packages.length === 0 && lock.dependencies && typeof lock.dependencies === 'object') {
      function walkDependencies(deps) {
        for (const [name, meta] of Object.entries(deps)) {
          if (!meta || typeof meta !== 'object') continue;
          if (meta.version && typeof meta.version === 'string') {
            const version = normalizeVersion(meta.version);
            if (name && version) {
              const key = `${name}@${version}`;
              if (!seen.has(key)) {
                seen.add(key);
                result.packages.push({ n: name, v: version });
              }
            }
          }
          if (meta.dependencies && typeof meta.dependencies === 'object') {
            walkDependencies(meta.dependencies);
          }
        }
      }
      walkDependencies(lock.dependencies);
    }
  
    return result;
  }
  
  /**
   * 解析 pnpm-lock.yaml 依赖文件
   *
   * @param {string} content - pnpm-lock.yaml 文件内容
   * @returns {Object} { ecosystem: 'npm', packages: [{n, v}] }
   */
  function parsePnpmLockfile(content) {
    const result = {
      ecosystem: 'npm',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const seen = new Set();
  
    // 1. 匹配 packages: 块下的条目 (/lodash@4.17.21:, '@babel/core@7.24.0':, /@babel/core@7.24.0(foo@1.0): 等)
    const pkgKeyRegex = /^\s*['"]?(?:\/)?((?:@[a-zA-Z0-9._-]+\/)?[a-zA-Z0-9._-]+)@([0-9][a-zA-Z0-9._+-]*?)(?:[(_].*)?['"]?:\s*$/gm;
    let m;
    while ((m = pkgKeyRegex.exec(content)) !== null) {
      const name = m[1].trim();
      const ver = normalizeVersion(m[2]);
      if (name && ver) {
        const key = `${name}@${ver}`;
        if (!seen.has(key)) {
          seen.add(key);
          result.packages.push({ n: name, v: ver });
        }
      }
    }
  
    // 2. 匹配 dependencies / devDependencies 块下的 specifier/version 声明
    const depBlockRegex = /^\s{2,4}['"]?((?:@[a-zA-Z0-9._-]+\/)?[a-zA-Z0-9._-]+)['"]?:\s*\n(?:\s+specifier:[^\n]*\n)?\s+version:\s*['"]?([0-9][a-zA-Z0-9._+-]*?)(?:[(_].*)?['"]?\s*$/gm;
    while ((m = depBlockRegex.exec(content)) !== null) {
      const name = m[1].trim();
      const ver = normalizeVersion(m[2]);
      if (name && ver) {
        const key = `${name}@${ver}`;
        if (!seen.has(key)) {
          seen.add(key);
          result.packages.push({ n: name, v: ver });
        }
      }
    }
  
    return result;
  }
  
  /**
   * 解析 yarn.lock 文件（兼容 v1 与 Berry v2/v3/v4）
   *
   * @param {string} content - yarn.lock 文件内容
   * @returns {Object} { ecosystem: 'npm', packages: [{n, v}] }
   */
  function parseYarnLockfile(content) {
    const result = {
      ecosystem: 'npm',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const seen = new Set();
    const blocks = content.split(/\n(?=[^\s#])/);
  
    for (const block of blocks) {
      const trimmed = block.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
  
      const firstLine = trimmed.split('\n')[0];
      const nameMatch = firstLine.match(/^["']?((?:@[a-zA-Z0-9._-]+\/)?[a-zA-Z0-9._-]+)@/);
      const verMatch = trimmed.match(/^\s*version[:\s]+["']?([0-9][a-zA-Z0-9._+-]*)["']?/m);
  
      if (nameMatch && verMatch) {
        const name = nameMatch[1].trim();
        const version = normalizeVersion(verMatch[1]);
        if (name && version) {
          const key = `${name}@${version}`;
          if (!seen.has(key)) {
            seen.add(key);
            result.packages.push({ n: name, v: version });
          }
        }
      }
    }
  
    return result;
  }
  
  /**
   * npm 生态统一解析器（支持 package.json, package-lock.json, pnpm-lock.yaml, yarn.lock）
   *
   * @param {string} content - 文件内容
   * @param {string} [filePath] - 文件路径
   * @returns {Object} { ecosystem: 'npm', packages: [{n, v}] }
   */
  function parseNpmManifest(content, filePath = '') {
    if (filePath) {
      if (/pnpm-lock\.yaml$/.test(filePath)) {
        return parsePnpmLockfile(content);
      }
      if (/yarn\.lock$/.test(filePath)) {
        return parseYarnLockfile(content);
      }
      if (/package-lock\.json$/.test(filePath)) {
        return parsePackageLockJson(content);
      }
    }
    return parsePackageJson(content);
  }
  
  __parsers_manifests_package_lock_json__.default = parseNpmLockfile;
  
  
  
  // Module exports
  __parsers_manifests_package_lock_json__.parseNpmLockfile = parseNpmLockfile;
  __parsers_manifests_package_lock_json__.lockfilePackagesToMap = lockfilePackagesToMap;
  __parsers_manifests_package_lock_json__.parsePackageLockJson = parsePackageLockJson;
  __parsers_manifests_package_lock_json__.parsePnpmLockfile = parsePnpmLockfile;
  __parsers_manifests_package_lock_json__.parseYarnLockfile = parseYarnLockfile;
  __parsers_manifests_package_lock_json__.parseNpmManifest = parseNpmManifest;
})();


// ============================================================================
// Module: parsers_manifests_requirements
// ============================================================================

(function() {
  /**
   * requirements.txt Parser
   * 
   * 解析 Python requirements.txt 文件中的依赖
   */
  
  /**
   * 标准化 pip 版本号
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 标准化后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
    
    let cleaned = version.trim();
    
    // 移除操作符前缀
    cleaned = cleaned.replace(/^[=<>~!]+/, '');
    
    // 处理范围: ">=1.0,<2.0" -> "1.0"
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[=<>~!]+/, '');
    }
    
    // 验证是否为有效版本号
    if (!/^\d/.test(cleaned)) {
      return '';
    }
    
    return cleaned;
  }
  
  /**
   * 解析单行 requirements.txt
   * 
   * 支持格式:
   * - package==1.0.0
   * - package>=1.0.0
   * - package~=1.0.0
   * - package[extra]==1.0.0
   * - package>=1.0.0,<2.0.0
   * - package==1.0.0; python_version>="3.8"
   * 
   * @param {string} line - 单行内容
   * @returns {Object|null} 解析结果 {n, v} 或 null
   */
  function parseLine(line) {
    if (!line || typeof line !== 'string') {
      return null;
    }
    
    // 去除首尾空白
    let trimmed = line.trim();
    
    // 跳过空行
    if (!trimmed) {
      return null;
    }
    
    // 跳过注释行
    if (trimmed[0] === '#') {
      return null;
    }
    
    // 跳过选项行 (-r, -e, -i, --index-url, etc)
    if (trimmed[0] === '-') {
      return null;
    }
    
    // 查找注释和环境标记
    let lineEnd = trimmed.length;
    let hasComment = false;
    let hasMarker = false;
    
    // 一次遍历找到注释和环境标记位置
    for (let i = 0; i < trimmed.length; i++) {
      const char = trimmed[i];
      if (char === '#') {
        lineEnd = i;
        hasComment = true;
        break;
      }
      if (char === ';') {
        lineEnd = i;
        hasMarker = true;
        break;
      }
    }
    
    // 提取有效部分并去除末尾空白
    const content = trimmed.substring(0, lineEnd);
    let validContent = content;
    
    // 去除末尾空白（更高效的方式）
    let end = validContent.length;
    while (end > 0 && (validContent[end - 1] === ' ' || validContent[end - 1] === '\t')) {
      end--;
    }
    if (end < validContent.length) {
      validContent = validContent.substring(0, end);
    }
    
    if (!validContent) {
      return null;
    }
    
    // 解析包名和版本
    // 匹配: package[extras]==version 或 package==version
    const match = validContent.match(/^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?\s*(==|>=|<=|~=|>|<|!=)?\s*(.*)$/);
    
    if (!match) {
      return null;
    }
    
    const name = match[1];
    const operator = match[2] || '';
    const versionPart = match[3] || '';
    
    // 如果没有版本信息，跳过
    if (!versionPart) {
      return null;
    }
    
    const version = normalizeVersion(versionPart);
    
    if (!version) {
      return null;
    }
    
    return {
      n: name,
      v: version
    };
  }
  
  /**
   * 解析 requirements.txt 内容
   * 
   * @param {string} content - requirements.txt 文件内容
   * @returns {Object} 解析结果 { ecosystem: 'pypi', packages: [{n, v}] }
   */
  function parseRequirements(content) {
    const result = {
      ecosystem: 'pypi',
      packages: []
    };
    
    if (!content || typeof content !== 'string') {
      return result;
    }
    
    const lines = content.split('\n');
    
    for (const line of lines) {
      const pkg = parseLine(line);
      
      if (pkg) {
        result.packages.push(pkg);
      }
    }
    
    return result;
  }
  
  __parsers_manifests_requirements__.default = parseRequirements;
  
  
  // Module exports
  __parsers_manifests_requirements__.normalizeVersion = normalizeVersion;
  __parsers_manifests_requirements__.parseLine = parseLine;
  __parsers_manifests_requirements__.parseRequirements = parseRequirements;
})();


// ============================================================================
// Module: parsers_manifests_go_mod
// ============================================================================

(function() {
  /**
   * go.mod Parser
   * 
   * 解析 Go go.mod 文件中的依赖
   */
  
  /**
   * 标准化 Go 模块版本号
   * 
   * @param {string} version - 原始版本字符串 (如 "v1.2.3", "v0.0.0-20231215...")
   * @returns {string} 标准化后的版本号（去掉 v 前缀）
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 去掉 v 前缀
    cleaned = cleaned.replace(/^v/, '');
  
    // 去掉 // indirect 注释
    if (cleaned.includes('//')) {
      cleaned = cleaned.split('//')[0].trim();
    }
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 解析 go.mod 文件内容
   * 
   * 解析 require 块中的依赖：
   * - require golang.org/x/crypto v0.17.0
   * - require (
   *     golang.org/x/crypto v0.17.0
   *     github.com/gin-gonic/gin v1.9.1 // indirect
   *   )
   * 
   * @param {string} content - go.mod 文件内容
   * @returns {Object} { ecosystem: 'go', packages: [{n, v}] }
   */
  function parseGoMod(content) {
    const result = {
      ecosystem: 'go',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const lines = content.split('\n');
  
    let inRequireBlock = false;
  
    for (const line of lines) {
      const trimmed = line.trim();
  
      // 跳过空行和注释
      if (!trimmed || trimmed.startsWith('//')) {
        continue;
      }
  
      // 检查 require 块开始
      if (trimmed.startsWith('require')) {
        // 单行 require: require golang.org/x/crypto v0.17.0
        if (trimmed.includes('(')) {
          inRequireBlock = true;
          continue;
        }
  
        // 单行 require（无括号）
        const singleMatch = trimmed.match(/^require\s+(\S+)\s+(\S+)/);
        if (singleMatch) {
          const name = singleMatch[1];
          const version = normalizeVersion(singleMatch[2]);
  
          if (name && version && name.includes('/') && name.includes('.')) {
            result.packages.push({ n: name, v: version });
          }
        }
        continue;
      }
  
      // require 块结束
      if (inRequireBlock && trimmed === ')') {
        inRequireBlock = false;
        continue;
      }
  
      // require 块内的依赖行
      if (inRequireBlock) {
        // 格式: module/path v1.2.3 [// indirect]
        const match = trimmed.match(/^(\S+)\s+(\S+)/);
  
        if (match) {
          const name = match[1];
          const version = normalizeVersion(match[2]);
  
          // 验证模块路径格式（含域名和路径）
          if (name && version && name.includes('/') && name.includes('.')) {
            result.packages.push({ n: name, v: version });
          }
        }
      }
    }
  
    return result;
  }
  
  __parsers_manifests_go_mod__.default = parseGoMod;
  
  
  // Module exports
  __parsers_manifests_go_mod__.normalizeVersion = normalizeVersion;
  __parsers_manifests_go_mod__.parseGoMod = parseGoMod;
})();


// ============================================================================
// Module: parsers_manifests_cargo_toml
// ============================================================================

(function() {
  /**
   * Cargo.toml Parser
   * 
   * 解析 Rust Cargo.toml 文件中的依赖
   * 使用正则解析，不依赖外部 TOML 库
   */
  
  /**
   * 标准化版本号
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 清理后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 去掉引号
    cleaned = cleaned.replace(/^["']|["']$/g, '');
  
    // 去掉前缀操作符（^, ~, >=, <=, >, <, =）
    cleaned = cleaned.replace(/^[>=<~^]+/, '').trim();
  
    // 处理逗号范围: ">=1.0, <2.0" -> "1.0"
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[>=<~^]+/, '').trim();
    }
  
    // 跳过通配符
    if (cleaned === '*') {
      return '';
    }
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 解析 Cargo.toml 文件内容
   * 
   * 支持:
   * - [dependencies] 段
   * - [dev-dependencies] 段
   * - [build-dependencies] 段
   * - 简单格式: serde = "1.0"
   * - 表格式: serde = { version = "1.0", features = ["derive"] }
   * - 工作区引用: serde = { workspace = true } （跳过）
   * - 路径引用: foo = { path = "../foo" } （跳过）
   * - Git 引用: bar = { git = "..." } （跳过）
   * 
   * @param {string} content - Cargo.toml 文件内容
   * @returns {Object} { ecosystem: 'cargo', packages: [{n, v, section}] }
   */
  function parseCargoToml(content) {
    const result = {
      ecosystem: 'cargo',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const lines = content.split('\n');
  
    // 依赖段名
    const depSections = new Set([
      'dependencies',
      'dev-dependencies',
      'build-dependencies',
    ]);
  
    let currentSection = null;
    // 跟踪 [dependencies.foo] 形式的表依赖
    let currentTableDep = null;
    let currentTableSection = null;
  
    for (const line of lines) {
      const trimmed = line.trim();
  
      // 跳过空行和注释
      if (!trimmed || trimmed.startsWith('#')) {
        continue;
      }
  
      // 检测段头 [xxx]
      const sectionMatch = trimmed.match(/^\[([^\]]+)\]$/);
      if (sectionMatch) {
        const sectionName = sectionMatch[1].trim();
  
        // 检查是否为 [dependencies.foo] 形式
        const dotMatch = sectionName.match(/^(dependencies|dev-dependencies|build-dependencies)\.(.+)$/);
        if (dotMatch) {
          currentSection = null;
          currentTableDep = dotMatch[2];
          currentTableSection = dotMatch[1];
          continue;
        }
  
        // 是否为依赖段
        if (depSections.has(sectionName)) {
          currentSection = sectionName;
        } else {
          currentSection = null;
        }
        currentTableDep = null;
        currentTableSection = null;
        continue;
      }
  
      // 在 [dependencies.foo] 段内，查找 version = "x.y"
      if (currentTableDep && currentTableSection) {
        const versionMatch = trimmed.match(/^version\s*=\s*"([^"]+)"/);
        if (versionMatch) {
          // 跳过有 path 或 git 的依赖（通过检查整个段来判断不可行，简化处理：如果有 version 就录入）
          const version = normalizeVersion(versionMatch[1]);
          if (version) {
            result.packages.push({
              n: currentTableDep,
              v: version,
              section: currentTableSection
            });
          }
          // version 找到后不清除 currentTableDep，因为同一段可能还有其他键
        }
        continue;
      }
  
      // 在依赖段内解析每行
      if (currentSection) {
        // 简单格式: name = "version"
        const simpleMatch = trimmed.match(/^([a-zA-Z][a-zA-Z0-9_-]*)\s*=\s*"([^"]+)"$/);
        if (simpleMatch) {
          const name = simpleMatch[1];
          const version = normalizeVersion(simpleMatch[2]);
          if (version) {
            result.packages.push({ n: name, v: version, section: currentSection });
          }
          continue;
        }
  
        // 表格式: name = { version = "1.0", ... }
        const tableMatch = trimmed.match(/^([a-zA-Z][a-zA-Z0-9_-]*)\s*=\s*\{(.+)\}$/);
        if (tableMatch) {
          const name = tableMatch[1];
          const inner = tableMatch[2];
  
          // 跳过 workspace = true
          if (/workspace\s*=\s*true/.test(inner)) {
            continue;
          }
  
          // 跳过纯 path 或 git 引用（无 version）
          const versionInner = inner.match(/version\s*=\s*"([^"]+)"/);
          if (versionInner) {
            const version = normalizeVersion(versionInner[1]);
            if (version) {
              result.packages.push({ n: name, v: version, section: currentSection });
            }
          }
          continue;
        }
      }
    }
  
    return result;
  }
  
  /**
   * 解析 Cargo.lock 文件中的所有包及其锁定版本
   *
   * @param {string} content - Cargo.lock 文件内容
   * @returns {Object} { ecosystem: 'cargo', packages: [{n, v}] }
   */
  function parseCargoLockfile(content) {
    const result = {
      ecosystem: 'cargo',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const seen = new Set();
    const blocks = content.split('[[package]]');
  
    for (let i = 1; i < blocks.length; i++) {
      const block = blocks[i];
      const nameMatch = block.match(/name\s*=\s*"([^"]+)"/);
      const versionMatch = block.match(/version\s*=\s*"([^"]+)"/);
      if (nameMatch && versionMatch) {
        const name = nameMatch[1].trim();
        const version = normalizeVersion(versionMatch[1]);
        if (name && version) {
          const key = `${name}@${version}`;
          if (!seen.has(key)) {
            seen.add(key);
            result.packages.push({ n: name, v: version });
          }
        }
      }
    }
  
    return result;
  }
  
  /**
   * Cargo 生态统一解析器（支持 Cargo.toml 和 Cargo.lock）
   *
   * @param {string} content - 文件内容
   * @param {string} [filePath] - 文件路径
   * @returns {Object} { ecosystem: 'cargo', packages: [{n, v}] }
   */
  function parseCargoManifest(content, filePath = '') {
    if (filePath && /Cargo\.lock$/.test(filePath)) {
      return parseCargoLockfile(content);
    }
    return parseCargoToml(content);
  }
  
  __parsers_manifests_cargo_toml__.default = parseCargoToml;
  
  
  
  // Module exports
  __parsers_manifests_cargo_toml__.normalizeVersion = normalizeVersion;
  __parsers_manifests_cargo_toml__.parseCargoToml = parseCargoToml;
  __parsers_manifests_cargo_toml__.parseCargoLockfile = parseCargoLockfile;
  __parsers_manifests_cargo_toml__.parseCargoManifest = parseCargoManifest;
})();


// ============================================================================
// Module: parsers_manifests_pom_xml
// ============================================================================

(function() {
  /**
   * pom.xml / build.gradle Parser
   * 
   * 解析 Maven pom.xml 和 Gradle build.gradle 文件中的依赖
   * 使用正则解析，不依赖外部 XML/Gradle 库
   */
  
  /**
   * 标准化版本号
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 清理后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 跳过属性引用: ${project.version}
    if (cleaned.startsWith('${') || cleaned.startsWith('[') || cleaned.startsWith('(')) {
      return '';
    }
  
    // 跳过 SNAPSHOT / LATEST / RELEASE
    if (/SNAPSHOT$/.test(cleaned) || cleaned === 'LATEST' || cleaned === 'RELEASE') {
      return '';
    }
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 提取 pom.xml 中的 <properties> 键值对
   * 
   * @param {string} content - pom.xml 文件内容
   * @returns {Record<string, string>} 属性键值映射
   */
  function extractPomProperties(content) {
    const properties = {};
    if (!content || typeof content !== 'string') {
      return properties;
    }
  
    const propsMatch = content.match(/<properties>([\s\S]*?)<\/properties>/i);
    if (!propsMatch) {
      return properties;
    }
  
    const propRegex = /<([a-zA-Z0-9._-]+)>\s*([^<]*?)\s*<\/\1>/g;
    let match;
    while ((match = propRegex.exec(propsMatch[1])) !== null) {
      properties[match[1]] = match[2].trim();
    }
  
    return properties;
  }
  
  /**
   * 解析 pom.xml 文件内容
   * 
   * 提取 <dependency> 块中的:
   * - <groupId>xxx</groupId>
   * - <artifactId>yyy</artifactId>
   * - <version>zzz</version>
   * 
   * 包名格式: groupId:artifactId
   * 
   * @param {string} content - pom.xml 文件内容
   * @returns {Object} { ecosystem: 'maven', packages: [{n, v}] }
   */
  function parsePomXml(content) {
    const result = {
      ecosystem: 'maven',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const properties = extractPomProperties(content);
  
    // 匹配所有 <dependency>...</dependency> 块
    const depBlockRegex = /<dependency>\s*([\s\S]*?)\s*<\/dependency>/gi;
    let blockMatch;
  
    while ((blockMatch = depBlockRegex.exec(content)) !== null) {
      const block = blockMatch[1];
  
      const groupIdMatch = block.match(/<groupId>\s*([^<]+?)\s*<\/groupId>/);
      const artifactIdMatch = block.match(/<artifactId>\s*([^<]+?)\s*<\/artifactId>/);
      const versionMatch = block.match(/<version>\s*([^<]+?)\s*<\/version>/);
  
      if (groupIdMatch && artifactIdMatch) {
        const groupId = groupIdMatch[1].trim();
        const artifactId = artifactIdMatch[1].trim();
        let rawVersion = versionMatch ? versionMatch[1].trim() : '';
  
        // 解析 ${property.name} 引用
        if (rawVersion.startsWith('${') && rawVersion.endsWith('}')) {
          const propName = rawVersion.slice(2, -1).trim();
          if (properties[propName]) {
            rawVersion = properties[propName];
          }
        }
  
        const version = normalizeVersion(rawVersion);
  
        // 跳过无版本号的（可能由 parent/BOM 管理）
        if (!version) {
          continue;
        }
  
        result.packages.push({
          n: `${groupId}:${artifactId}`,
          v: version
        });
      }
    }
  
    return result;
  }
  
  /**
   * 提取 Gradle 脚本中的属性/变量键值对
   * 
   * 支持:
   * - ext { key = 'value' } 或 extra { ... }
   * - def/val/var/ext.prop = 'value'
   * - extra["key"] = "value" (Kotlin DSL)
   * 
   * @param {string} content - build.gradle / build.gradle.kts 文件内容
   * @returns {Record<string, string>} 属性键值映射
   */
  function extractGradleProperties(content) {
    const properties = {};
    if (!content || typeof content !== 'string') {
      return properties;
    }
  
    // 1. ext { key = 'value' } 或 extra { ... } 块
    const extBlockMatch = content.match(/(?:ext|extra)\s*\{([\s\S]*?)\}/);
    if (extBlockMatch) {
      const blockContent = extBlockMatch[1];
      const kvRegex = /([a-zA-Z0-9_.-]+)\s*=\s*['"]([^'"]+)['"]/g;
      let m;
      while ((m = kvRegex.exec(blockContent)) !== null) {
        properties[m[1]] = m[2].trim();
      }
    }
  
    // 2. 单行定义: def/val/var/ext.prop = 'value'
    const lineDefRegex = /(?:def|val|var|ext\.([a-zA-Z0-9_.-]+))\s+([a-zA-Z0-9_.-]+)?\s*=\s*['"]([^'"]+)['"]/g;
    let m;
    while ((m = lineDefRegex.exec(content)) !== null) {
      const key = m[1] || m[2];
      const val = m[3];
      if (key && val) {
        properties[key] = val.trim();
      }
    }
  
    // 3. extra["key"] = "value" (Kotlin DSL)
    const extraMapRegex = /extra\[['"]([a-zA-Z0-9_.-]+)['"]\]\s*=\s*['"]([^'"]+)['"]/g;
    while ((m = extraMapRegex.exec(content)) !== null) {
      properties[m[1]] = m[2].trim();
    }
  
    return properties;
  }
  
  /**
   * 解析并插值 Gradle 版本字符串中的变量
   * 
   * @param {string} rawVersion - 原始版本字符串（如 "$springVersion" 或 "${springVersion}"）
   * @param {Record<string, string>} properties - 提取到的属性字典
   * @returns {string} 标准化后的版本号
   */
  function resolveGradleVersion(rawVersion, properties) {
    if (!rawVersion || typeof rawVersion !== 'string') {
      return '';
    }
    let v = rawVersion.trim();
    // 替换 ${varName}
    v = v.replace(/\$\{([a-zA-Z0-9_.-]+)\}/g, (match, varName) => {
      return properties && properties[varName] !== undefined ? properties[varName] : match;
    });
    // 替换 $varName
    v = v.replace(/\$([a-zA-Z0-9_]+)/g, (match, varName) => {
      return properties && properties[varName] !== undefined ? properties[varName] : match;
    });
    return normalizeVersion(v);
  }
  
  /**
   * 解析 build.gradle / build.gradle.kts 文件内容
   * 
   * 支持格式:
   * - 字符串表示法: implementation 'group:artifact:version', implementation("group:artifact:version")
   * - 平台依赖: implementation platform('group:artifact:version')
   * - Map 表示法 (Groovy DSL): implementation group: 'group', name: 'artifact', version: 'version'
   * - 命名参数表示法 (Kotlin DSL): implementation(group = "group", name = "artifact", version = "version")
   * - 变量引用与属性插值: implementation "group:artifact:${springVersion}"
   * 
   * @param {string} content - build.gradle 文件内容
   * @returns {Object} { ecosystem: 'maven', packages: [{n, v}] }
   */
  function parseBuildGradle(content) {
    const result = {
      ecosystem: 'maven',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const properties = extractGradleProperties(content);
  
    // Gradle 配置名
    const configs = '(?:implementation|api|compile|compileOnly|runtimeOnly|testImplementation|testCompileOnly|testRuntimeOnly|annotationProcessor|kapt|ksp|classpath)';
  
    // 1. 冒号坐标表示法: implementation 'group:artifact:version' / implementation("...") / platform(...)
    const colonRegex = new RegExp(
      configs + '\\s*\\(?\\s*(?:(?:platform|enforcedPlatform)\\s*\\(?\\s*)?[\'"]([a-zA-Z0-9._-]+):([a-zA-Z0-9._-]+):([^\'"\\s)]+)',
      'g'
    );
  
    let match;
    while ((match = colonRegex.exec(content)) !== null) {
      const groupId = match[1].trim();
      const artifactId = match[2].trim();
      const rawVersion = match[3].trim();
      const version = resolveGradleVersion(rawVersion, properties);
  
      if (!version) {
        continue;
      }
  
      result.packages.push({
        n: `${groupId}:${artifactId}`,
        v: version
      });
    }
  
    // 2. Map / 命名参数表示法: group(:|=) '...', name(:|=) '...', version(:|=) '...'
    const mapDepRegex = new RegExp(
      configs + '\\s*\\(?\\s*([^\\n)]+)',
      'g'
    );
  
    while ((match = mapDepRegex.exec(content)) !== null) {
      const line = match[1];
      const gMatch = line.match(/\bgroup\s*[:=]\s*['"]([^'"\s)]+)['"]/);
      const aMatch = line.match(/\bname\s*[:=]\s*['"]([^'"\s)]+)['"]/);
      const vMatch = line.match(/\bversion\s*[:=]\s*['"]([^'"\s)]+)['"]/);
  
      if (gMatch && aMatch && vMatch) {
        const groupId = gMatch[1].trim();
        const artifactId = aMatch[1].trim();
        const rawVersion = vMatch[1].trim();
        const version = resolveGradleVersion(rawVersion, properties);
  
        if (!version) {
          continue;
        }
  
        result.packages.push({
          n: `${groupId}:${artifactId}`,
          v: version
        });
      }
    }
  
    return result;
  }
  
  /**
   * 解析 gradle.lockfile 文件内容
   * 
   * 格式:
   * groupId:artifactId:version=compileClasspath,runtimeClasspath
   * 
   * @param {string} content - gradle.lockfile 文件内容
   * @returns {Object} { ecosystem: 'maven', packages: [{n, v}] }
   */
  function parseGradleLockfile(content) {
    const result = {
      ecosystem: 'maven',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const lines = content.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('empty=')) {
        continue;
      }
  
      const match = trimmed.match(/^([a-zA-Z0-9._-]+):([a-zA-Z0-9._-]+):([^=:\s]+)=/);
      if (match) {
        const groupId = match[1].trim();
        const artifactId = match[2].trim();
        const version = normalizeVersion(match[3].trim());
  
        if (version) {
          result.packages.push({
            n: `${groupId}:${artifactId}`,
            v: version
          });
        }
      }
    }
  
    return result;
  }
  
  /**
   * 根据内容与路径判断是 pom.xml、build.gradle 还是 gradle.lockfile 并调用相应解析器
   * 
   * @param {string} content - 文件内容
   * @param {string} filePath - 文件路径（用于区分）
   * @returns {Object} { ecosystem: 'maven', packages: [{n, v}] }
   */
  function parseMavenManifest(content, filePath) {
    if (!content || typeof content !== 'string') {
      return { ecosystem: 'maven', packages: [] };
    }
  
    // 通过文件路径判断
    if (filePath) {
      if (/(?:^|\/)gradle\.lockfile$/.test(filePath) || /\.lockfile$/.test(filePath)) {
        return parseGradleLockfile(content);
      }
      if (/build\.gradle/.test(filePath)) {
        return parseBuildGradle(content);
      }
    }
  
    // 通过内容判断：如果包含 XML 声明或 <project>，按 pom.xml 解析
    if (content.includes('<project') || content.includes('<dependency>')) {
      return parsePomXml(content);
    }
  
    // 如果包含 lockfile 格式 (形如 ...=classpath)，尝试 lockfile 解析
    if (/^[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+:[^=:\s]+=.*$/m.test(content)) {
      return parseGradleLockfile(content);
    }
  
    // 默认尝试 Gradle 格式
    if (content.includes('implementation') || content.includes('dependencies')) {
      return parseBuildGradle(content);
    }
  
    return { ecosystem: 'maven', packages: [] };
  }
  
  __parsers_manifests_pom_xml__.default = parseMavenManifest;
  
  
  // Module exports
  __parsers_manifests_pom_xml__.normalizeVersion = normalizeVersion;
  __parsers_manifests_pom_xml__.extractPomProperties = extractPomProperties;
  __parsers_manifests_pom_xml__.parsePomXml = parsePomXml;
  __parsers_manifests_pom_xml__.extractGradleProperties = extractGradleProperties;
  __parsers_manifests_pom_xml__.resolveGradleVersion = resolveGradleVersion;
  __parsers_manifests_pom_xml__.parseBuildGradle = parseBuildGradle;
  __parsers_manifests_pom_xml__.parseGradleLockfile = parseGradleLockfile;
  __parsers_manifests_pom_xml__.parseMavenManifest = parseMavenManifest;
})();


// ============================================================================
// Module: parsers_manifests_gemfile
// ============================================================================

(function() {
  /**
   * Gemfile Parser
   * 
   * 解析 Ruby Gemfile 和 .gemspec 文件中的依赖
   */
  
  /**
   * 标准化版本号
   * 
   * @param {string} version - 原始版本字符串 (如 "~> 5.0", ">= 1.0, < 2.0")
   * @returns {string} 清理后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 去掉引号
    cleaned = cleaned.replace(/^["']|["']$/g, '');
  
    // 去掉前缀操作符（~>, >=, <=, >, <, =, !=）
    cleaned = cleaned.replace(/^[~><=!]+\s*/, '').trim();
  
    // 处理范围: ">=1.0, <2.0" -> "1.0"
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[~><=!]+\s*/, '').trim();
    }
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 解析 Gemfile 文件内容
   * 
   * 支持格式:
   * - gem 'rails'
   * - gem 'rails', '~> 7.0'
   * - gem "rails", ">= 7.0.0", "< 8.0"
   * - gem 'puma', '~> 5.0', require: false
   * - gem 'pg', group: :production
   * 
   * @param {string} content - Gemfile 文件内容
   * @returns {Object} { ecosystem: 'rubygems', packages: [{n, v}] }
   */
  function parseGemfile(content) {
    const result = {
      ecosystem: 'rubygems',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const lines = content.split('\n');
  
    for (const line of lines) {
      const trimmed = line.trim();
  
      // 跳过空行和注释
      if (!trimmed || trimmed.startsWith('#')) {
        continue;
      }
  
      // 匹配 gem 'name' 或 gem "name" 以及可选版本
      // gem 'name'[, 'version_constraint'][, 'version_constraint'][, key: value ...]
      const gemMatch = trimmed.match(/^gem\s+(['"])([^'"]+)\1/);
  
      if (!gemMatch) {
        continue;
      }
  
      const name = gemMatch[2];
  
      // 验证 gem 名称
      if (!name || !/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(name)) {
        continue;
      }
  
      // 提取版本约束（gem 名后面的逗号分隔参数，直到遇到 key: value 形式）
      // 先获取 gem 名之后的剩余内容
      const afterName = trimmed.substring(gemMatch[0].length);
  
      let version = '';
  
      // 查找第一个版本字符串: , 'version' 或 , "version"
      const versionMatch = afterName.match(/,\s*(['"])([^'"]+)\1/);
      if (versionMatch) {
        version = normalizeVersion(versionMatch[2]);
      }
  
      result.packages.push({ n: name, v: version });
    }
  
    return result;
  }
  
  /**
   * 解析 .gemspec 文件内容
   * 
   * 支持:
   * - spec.add_dependency 'name', '~> 1.0'
   * - spec.add_runtime_dependency 'name', '>= 1.0'
   * - spec.add_development_dependency 'name', '~> 2.0'
   * - s.add_dependency 'name'
   * 
   * @param {string} content - .gemspec 文件内容
   * @returns {Object} { ecosystem: 'rubygems', packages: [{n, v}] }
   */
  function parseGemspec(content) {
    const result = {
      ecosystem: 'rubygems',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const lines = content.split('\n');
  
    for (const line of lines) {
      const trimmed = line.trim();
  
      // 跳过空行和注释
      if (!trimmed || trimmed.startsWith('#')) {
        continue;
      }
  
      // 匹配 add_dependency / add_runtime_dependency / add_development_dependency
      const depMatch = trimmed.match(
        /\.add_(?:runtime_|development_)?dependency\s*\(?\s*(['"])([^'"]+)\1(?:\s*,\s*(['"])([^'"]+)\3)?/
      );
  
      if (!depMatch) {
        continue;
      }
  
      const name = depMatch[2];
      const rawVersion = depMatch[4] || '';
  
      if (!name || !/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(name)) {
        continue;
      }
  
      const version = normalizeVersion(rawVersion);
  
      result.packages.push({ n: name, v: version });
    }
  
    return result;
  }
  
  /**
   * 根据文件路径选择合适的解析器
   * 
   * @param {string} content - 文件内容
   * @param {string} filePath - 文件路径
   * @returns {Object} { ecosystem: 'rubygems', packages: [{n, v}] }
   */
  function parseRubyManifest(content, filePath) {
    if (!content || typeof content !== 'string') {
      return { ecosystem: 'rubygems', packages: [] };
    }
  
    if (filePath && /\.gemspec$/.test(filePath)) {
      return parseGemspec(content);
    }
  
    return parseGemfile(content);
  }
  
  __parsers_manifests_gemfile__.default = parseRubyManifest;
  
  
  // Module exports
  __parsers_manifests_gemfile__.normalizeVersion = normalizeVersion;
  __parsers_manifests_gemfile__.parseGemfile = parseGemfile;
  __parsers_manifests_gemfile__.parseGemspec = parseGemspec;
  __parsers_manifests_gemfile__.parseRubyManifest = parseRubyManifest;
})();


// ============================================================================
// Module: parsers_manifests_composer_json
// ============================================================================

(function() {
  /**
   * composer.json Parser
   * 
   * 解析 PHP Composer composer.json 文件中的依赖
   */
  
  /**
   * 标准化版本号
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 清理后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 去掉前缀操作符（^, ~, >=, <=, >, <, !=, =）
    cleaned = cleaned.replace(/^[>=<~^!=]+/, '').trim();
  
    // 去掉 v 前缀
    cleaned = cleaned.replace(/^v/, '');
  
    // 处理 || 范围: "^1.0 || ^2.0" -> "1.0"
    if (cleaned.includes('||')) {
      cleaned = cleaned.split('||')[0].trim().replace(/^[>=<~^!=]+/, '');
    }
  
    // 处理空格范围: ">=1.0 <2.0" -> "1.0"
    if (cleaned.includes(' ')) {
      cleaned = cleaned.split(' ')[0].replace(/^[>=<~^!=]+/, '');
    }
  
    // 跳过通配符和特殊值
    if (cleaned === '*' || cleaned.startsWith('dev-') || cleaned.startsWith('@')) {
      return '';
    }
  
    // 处理通配符版本: "1.0.*" -> "1.0"
    cleaned = cleaned.replace(/\.\*$/, '');
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 解析 composer.json 文件内容
   * 
   * 扫描 require 和 require-dev 段
   * 
   * @param {string} content - composer.json 文件内容
   * @returns {Object} { ecosystem: 'packagist', packages: [{n, v, section}] }
   */
  function parseComposerJson(content) {
    const result = {
      ecosystem: 'packagist',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    let pkg;
    try {
      pkg = JSON.parse(content);
    } catch (error) {
      return result;
    }
  
    const sections = ['require', 'require-dev'];
  
    for (const section of sections) {
      if (pkg[section] && typeof pkg[section] === 'object') {
        for (const [name, version] of Object.entries(pkg[section])) {
          // 跳过 PHP 平台包（php, ext-xxx）
          if (name === 'php' || name.startsWith('ext-') || name.startsWith('lib-')) {
            continue;
          }
  
          // Composer 包名必须是 vendor/package 格式
          if (!name.includes('/')) {
            continue;
          }
  
          const normalizedVersion = normalizeVersion(version);
  
          result.packages.push({
            n: name,
            v: normalizedVersion,
            section: section
          });
        }
      }
    }
  
    return result;
  }
  
  __parsers_manifests_composer_json__.default = parseComposerJson;
  
  
  // Module exports
  __parsers_manifests_composer_json__.normalizeVersion = normalizeVersion;
  __parsers_manifests_composer_json__.parseComposerJson = parseComposerJson;
})();


// ============================================================================
// Module: parsers_manifests_pipfile
// ============================================================================

(function() {
  /**
   * Pipfile Parser
   *
   * 解析 Python Pipfile（TOML 格式）中的依赖，覆盖 [packages] 和 [dev-packages] 段。
   * 使用正则逐行解析，不依赖外部 TOML 库（与 cargo-toml.js 的解析风格一致），
   * 因为这里只需要提取"包名 + 版本约束"这一薄语义层，完整 TOML AST 不是必需的。
   *
   * 修复背景（D1-09 Parser 路由空洞）：此前 `isDependencyManifest`/`detectEcosystem`
   * 已识别 Pipfile 为依赖清单，但 `parseManifest` 对 Pipfile 始终返回空 packages 数组，
   * 造成"看起来正常放行，实际零组件审计"的静默覆盖空洞。
   */
  
  /**
   * 标准化 Pipfile 版本约束
   *
   * Pipfile 版本语法示例:
   * - "==2.28.0"  -> "2.28.0"
   * - ">=4.0"     -> "4.0"
   * - "*"         -> ""（无约束，视为未指定版本）
   * - "~=1.4.2"   -> "1.4.2"
   *
   * @param {string} version - 原始版本字符串
   * @returns {string} 清理后的版本号，无法提取精确版本时返回空字符串
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim().replace(/^["']|["']$/g, '');
  
    if (cleaned === '*' || cleaned === '') {
      return '';
    }
  
    // 去掉前缀操作符（==, >=, <=, ~=, >, <, !=）
    cleaned = cleaned.replace(/^[=<>~!]+\s*/, '').trim();
  
    // 处理逗号范围: ">=1.0,<2.0" -> "1.0"
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[=<>~!]+\s*/, '').trim();
    }
  
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 从表格式依赖行中提取 version 字段
   *
   * 支持: numpy = {version = ">=1.20", extras = ["test"]}
   *
   * @param {string} tableContent - 花括号内的内容
   * @returns {string} 提取到的版本约束（未标准化），无 version 字段时返回空字符串
   */
  function extractVersionFromTable(tableContent) {
    const versionMatch = tableContent.match(/version\s*=\s*["']([^"']*)["']/);
    return versionMatch ? versionMatch[1] : '';
  }
  
  /**
   * 解析 Pipfile 文件内容
   *
   * @param {string} content - Pipfile 文件内容
   * @returns {Object} { ecosystem: 'pypi', packages: [{n, v, section}] }
   */
  function parsePipfile(content) {
    const result = {
      ecosystem: 'pypi',
      packages: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const lines = content.split('\n');
    const depSections = new Set(['packages', 'dev-packages']);
    let currentSection = null;
  
    for (const line of lines) {
      const trimmed = line.trim();
  
      if (!trimmed || trimmed.startsWith('#')) {
        continue;
      }
  
      // 检测段头 [xxx] 或 [[xxx]]（source 段用双括号，跳过）
      const sectionMatch = trimmed.match(/^\[([^\]]+)\]$/);
      if (sectionMatch) {
        const sectionName = sectionMatch[1].trim();
        currentSection = depSections.has(sectionName) ? sectionName : null;
        continue;
      }
      if (/^\[\[.+\]\]$/.test(trimmed)) {
        currentSection = null;
        continue;
      }
  
      if (!currentSection) {
        continue;
      }
  
      // 简单格式: name = "==1.0.0" / name = "*"
      const simpleMatch = trimmed.match(/^([a-zA-Z0-9_.-]+)\s*=\s*["']([^"']*)["']\s*$/);
      if (simpleMatch) {
        const version = normalizeVersion(simpleMatch[2]);
        result.packages.push({ n: simpleMatch[1], v: version, section: currentSection });
        continue;
      }
  
      // 表格式: name = {version = "...", extras = [...]}
      const tableMatch = trimmed.match(/^([a-zA-Z0-9_.-]+)\s*=\s*\{(.+)\}\s*$/);
      if (tableMatch) {
        const rawVersion = extractVersionFromTable(tableMatch[2]);
        const version = normalizeVersion(rawVersion);
        result.packages.push({ n: tableMatch[1], v: version, section: currentSection });
        continue;
      }
    }
  
    return result;
  }
  
  __parsers_manifests_pipfile__.default = parsePipfile;
  
  
  // Module exports
  __parsers_manifests_pipfile__.normalizeVersion = normalizeVersion;
  __parsers_manifests_pipfile__.parsePipfile = parsePipfile;
})();


// ============================================================================
// Module: parsers_manifests_pyproject_toml
// ============================================================================

(function() {
  /**
   * pyproject.toml Parser
   *
   * pyproject.toml 承载了至少三种事实上不兼容的依赖声明规范，必须分别识别，
   * 不能用同一段正则假装全部兼容（这正是 D1-09 文档明确警告的反模式）：
   *
   * 1. PEP 621 标准（[project] dependencies = ["requests>=2.28.0", ...]）
   * 2. Poetry（[tool.poetry.dependencies] requests = "^2.28.0"）
   * 3. PDM / uv 的 dev 依赖分组（[dependency-groups] dev = [...] 或
   *    [tool.pdm.dev-dependencies]）
   *
   * 本 Parser 同时支持以上三种，缺失/不认识的 section 会被记录到
   * `unsupported_sections`（而不是静默忽略），以匹配文档要求的
   * "unsupported 状态必须显式返回覆盖空洞，不能与 no_dependencies 等价"。
   */
  
  /**
   * 标准化 PEP 508 依赖字符串中的版本约束
   *
   * PEP 508 格式示例: "requests>=2.28.0", "django==4.0.*", "flask"
   *
   * @param {string} spec - PEP 508 依赖声明（不含引号）
   * @returns {{name: string, version: string}|null}
   */
  function parsePep508(spec) {
    if (!spec || typeof spec !== 'string') return null;
    const trimmed = spec.trim();
    if (!trimmed) return null;
  
    // 去掉 extras（如 requests[security]）和环境标记（; python_version>="3.8"）
    const withoutMarker = trimmed.split(';')[0].trim();
    const match = withoutMarker.match(/^([a-zA-Z0-9_.-]+)(?:\[[^\]]*\])?\s*(==|>=|<=|~=|!=|>|<)?\s*(.*)$/);
    if (!match) return null;
  
    const name = match[1];
    const rawVersion = (match[3] || '').trim();
    const version = rawVersion && /^\d/.test(rawVersion) ? rawVersion.split(',')[0].trim() : '';
  
    return { name, version };
  }
  
  /**
   * 标准化 Poetry 风格版本约束（^1.0.0, ~1.0.0, >=1.0.0 等）
   *
   * @param {string} version - 原始版本字符串
   * @returns {string} 标准化后的版本号
   */
  function normalizePoetryVersion(version) {
    if (!version || typeof version !== 'string') return '';
    let cleaned = version.trim().replace(/^["']|["']$/g, '');
    if (cleaned === '*' || cleaned === '') return '';
    cleaned = cleaned.replace(/^[\^~><=!]+\s*/, '').trim();
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[\^~><=!]+\s*/, '').trim();
    }
    return /^\d/.test(cleaned) ? cleaned : '';
  }
  
  /**
   * 从 TOML 数组内容中提取所有字符串字面量（正确处理单引号/双引号混用）
   *
   * TOML 允许同一个文件里字符串用双引号或单引号，PEP 508 依赖声明本身也常见
   * 环境标记里嵌套另一种引号（如 'django==4.0.1; python_version>="3.8"'）。
   * 用同一个字符类同时当左右引号（`["']...["']`）会在这种混用场景下把定界符
   * 错误配对，必须让 "..." 和 '...' 分别独立匹配。
   *
   * @param {string} arrayContent - 数组方括号内的原始文本
   * @returns {string[]} 提取到的字符串字面量内容（不含引号）
   */
  function extractStringLiterals(arrayContent) {
    const results = [];
    const re = /"([^"]*)"|'([^']*)'/g;
    let match;
    while ((match = re.exec(arrayContent)) !== null) {
      results.push(match[1] !== undefined ? match[1] : match[2]);
    }
    return results;
  }
  
  /**
   * 计算 TOML 数组文本中、字符串引号之外的方括号净深度
   *
   * 引号内的 `[`/`]`（如 PEP 508 extras 语法 "requests[security]"）不计入深度，
   * 只统计真正属于数组结构的方括号。
   *
   * @param {string} text - 待扫描的文本
   * @returns {number} 净深度（`[` 计 +1，`]` 计 -1，忽略引号内的字符）
   */
  function bracketDepthOutsideQuotes(text) {
    let depth = 0;
    let inSingle = false;
    let inDouble = false;
    for (let k = 0; k < text.length; k++) {
      const ch = text[k];
      if (ch === "'" && !inDouble) inSingle = !inSingle;
      else if (ch === '"' && !inSingle) inDouble = !inDouble;
      else if (!inSingle && !inDouble) {
        if (ch === '[') depth++;
        else if (ch === ']') depth--;
      }
    }
    return depth;
  }
  
  /**
   * 判断截至目前累积的数组文本是否已经闭合（净深度回到 <= 0，即最外层的
   * `[` 已经被对应的 `]` 闭合）。传入的 arrayContent 是 `dependencies = [`
   * 之后的部分，因此起始深度视为已经处于第一层内部（还差一个 `]` 才闭合）。
   *
   * @param {string} arrayContent - 目前累积的数组内容
   * @returns {boolean}
   */
  function isArrayClosed(arrayContent) {
    return bracketDepthOutsideQuotes(arrayContent) < 0;
  }
  
  /**
   * 找到数组真正闭合的 `]` 在文本中的位置（跳过引号内的方括号）
   *
   * @param {string} arrayContent - 累积的数组内容
   * @returns {number} 闭合括号的下标，未找到时返回 -1
   */
  function findArrayCloseIndex(arrayContent) {
    let depth = 0;
    let inSingle = false;
    let inDouble = false;
    for (let k = 0; k < arrayContent.length; k++) {
      const ch = arrayContent[k];
      if (ch === "'" && !inDouble) inSingle = !inSingle;
      else if (ch === '"' && !inSingle) inDouble = !inDouble;
      else if (!inSingle && !inDouble) {
        if (ch === '[') depth++;
        else if (ch === ']') {
          if (depth === 0) return k;
          depth--;
        }
      }
    }
    return -1;
  }
  
  /**
   * 解析 PEP 621 [project] 段的 dependencies 数组（含跨行数组）
   *
   * @param {string[]} lines - 全文件按行拆分
   * @returns {{packages: Array, consumedLineIndexes: Set<number>}}
   */
  function parsePep621Dependencies(lines) {
    const packages = [];
    const consumed = new Set();
  
    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      const arrayStart = trimmed.match(/^dependencies\s*=\s*\[(.*)$/);
      if (!arrayStart) continue;
  
      consumed.add(i);
      let arrayContent = arrayStart[1];
      let j = i;
      // 跨行数组：持续读取直到遇到闭合的 ]。不能简单判断"是否包含 ]"，因为
      // PEP 508 extras 语法（如 "requests[security]>=2.28.0"）本身就含有
      // 方括号，会被误判为数组已闭合，导致后续行被截断丢失。这里改为统计
      // 未被引号包裹的方括号深度，只有深度回到 0 才认为数组真正闭合。
      while (!isArrayClosed(arrayContent) && j + 1 < lines.length) {
        j++;
        arrayContent += '\n' + lines[j];
        consumed.add(j);
      }
      const closeIdx = findArrayCloseIndex(arrayContent);
      arrayContent = closeIdx >= 0 ? arrayContent.slice(0, closeIdx) : arrayContent;
  
      const specs = extractStringLiterals(arrayContent);
      for (const spec of specs) {
        const parsed = parsePep508(spec);
        if (parsed) {
          packages.push({ n: parsed.name, v: parsed.version, section: 'project.dependencies' });
        }
      }
    }
  
    return { packages, consumedLineIndexes: consumed };
  }
  
  /**
   * 解析 dependency-groups（PEP 735 / uv 标准）：
   *   [dependency-groups]
   *   dev = ["pytest>=7.0"]
   *
   * F-06 修复：支持多行数组格式：
   *   [dependency-groups]
   *   dev = [
   *     "pytest>=8",
   *     "ruff>=0.5"
   *   ]
   *
   * @param {string[]} lines
   * @returns {Array}
   */
  function parseDependencyGroups(lines) {
    const packages = [];
    let inSection = false;
  
    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      const sectionMatch = trimmed.match(/^\[([^\]]+)\]$/);
      if (sectionMatch) {
        inSection = sectionMatch[1].trim() === 'dependency-groups';
        continue;
      }
      if (!inSection) continue;
  
      // F-06: 支持多行数组——先尝试匹配单行，再尝试多行
      const singleLineMatch = trimmed.match(/^([a-zA-Z0-9_-]+)\s*=\s*\[(.*)\]\s*$/);
      if (singleLineMatch) {
        // 单行格式: dev = ["pytest>=7.0"]
        const groupName = singleLineMatch[1];
        const specs = extractStringLiterals(singleLineMatch[2]);
        for (const spec of specs) {
          const parsed = parsePep508(spec);
          if (parsed) {
            packages.push({ n: parsed.name, v: parsed.version, section: `dependency-groups.${groupName}` });
          }
        }
        continue;
      }
  
      // F-06: 多行数组格式: dev = [
      //   "pytest>=8",
      //   "ruff>=0.5"
      // ]
      const multiLineStart = trimmed.match(/^([a-zA-Z0-9_-]+)\s*=\s*\[(.*)$/);
      if (multiLineStart) {
        const groupName = multiLineStart[1];
        let arrayContent = multiLineStart[2];
        let j = i;
        // 跨行读取直到数组闭合
        while (!isArrayClosed(arrayContent) && j + 1 < lines.length) {
          j++;
          arrayContent += '\n' + lines[j];
        }
        const closeIdx = findArrayCloseIndex(arrayContent);
        arrayContent = closeIdx >= 0 ? arrayContent.slice(0, closeIdx) : arrayContent;
  
        const specs = extractStringLiterals(arrayContent);
        for (const spec of specs) {
          const parsed = parsePep508(spec);
          if (parsed) {
            packages.push({ n: parsed.name, v: parsed.version, section: `dependency-groups.${groupName}` });
          }
        }
        i = j; // 跳过已消费的行
      }
    }
  
    return packages;
  }
  
  /**
   * 解析 Poetry 段：[tool.poetry.dependencies] / [tool.poetry.dev-dependencies] /
   * [tool.poetry.group.<name>.dependencies]
   *
   * @param {string[]} lines
   * @returns {Array}
   */
  function parsePoetrySections(lines) {
    const packages = [];
    let currentSection = null; // null 表示不在 poetry 依赖段内
  
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
  
      const sectionMatch = trimmed.match(/^\[([^\]]+)\]$/);
      if (sectionMatch) {
        const name = sectionMatch[1].trim();
        if (
          name === 'tool.poetry.dependencies' ||
          name === 'tool.poetry.dev-dependencies'
        ) {
          currentSection = name;
        } else if (/^tool\.poetry\.group\.[^.]+\.dependencies$/.test(name)) {
          currentSection = name;
        } else {
          currentSection = null;
        }
        continue;
      }
  
      if (!currentSection) continue;
  
      // python 版本约束不是真正的依赖包，跳过
      const simpleMatch = trimmed.match(/^([a-zA-Z0-9_.-]+)\s*=\s*["']([^"']*)["']\s*$/);
      if (simpleMatch) {
        if (simpleMatch[1].toLowerCase() === 'python') continue;
        const version = normalizePoetryVersion(simpleMatch[2]);
        packages.push({ n: simpleMatch[1], v: version, section: currentSection });
        continue;
      }
  
      const tableMatch = trimmed.match(/^([a-zA-Z0-9_.-]+)\s*=\s*\{(.+)\}\s*$/);
      if (tableMatch) {
        if (tableMatch[1].toLowerCase() === 'python') continue;
        const versionMatch = tableMatch[2].match(/version\s*=\s*["']([^"']*)["']/);
        const version = versionMatch ? normalizePoetryVersion(versionMatch[1]) : '';
        packages.push({ n: tableMatch[1], v: version, section: currentSection });
      }
    }
  
    return packages;
  }
  
  /**
   * 解析 PDM dev 依赖段：[tool.pdm.dev-dependencies] test = ["pytest>=7.0"]
   *
   * @param {string[]} lines
   * @returns {Array}
   */
  function parsePdmDevDependencies(lines) {
    const packages = [];
    let inSection = false;
  
    for (const line of lines) {
      const trimmed = line.trim();
      const sectionMatch = trimmed.match(/^\[([^\]]+)\]$/);
      if (sectionMatch) {
        inSection = sectionMatch[1].trim() === 'tool.pdm.dev-dependencies';
        continue;
      }
      if (!inSection) continue;
  
      const groupMatch = trimmed.match(/^([a-zA-Z0-9_-]+)\s*=\s*\[(.*)\]\s*$/);
      if (groupMatch) {
        const specs = extractStringLiterals(groupMatch[2]);
        for (const spec of specs) {
          const parsed = parsePep508(spec);
          if (parsed) {
            packages.push({ n: parsed.name, v: parsed.version, section: `tool.pdm.dev-dependencies.${groupMatch[1]}` });
          }
        }
      }
    }
  
    return packages;
  }
  
  /**
   * 检测文件中出现过、但当前 Parser 未处理的依赖相关 section 名称
   * （避免"识别了却没有解析，还静默当成无依赖"这一 D1-09 核心问题）
   *
   * @param {string[]} lines
   * @returns {string[]} 未被处理的 section 名称列表
   */
  function detectUnsupportedSections(lines) {
    const knownPrefixes = [
      'project',
      'dependency-groups',
      'tool.poetry',
      'tool.pdm.dev-dependencies',
    ];
    const unsupported = [];
  
    for (const line of lines) {
      const trimmed = line.trim();
      const sectionMatch = trimmed.match(/^\[([^\]]+)\]$/);
      if (!sectionMatch) continue;
      const name = sectionMatch[1].trim();
  
      // project.optional-dependencies 是已知但当前不解析的可选依赖段（PEP 621 extras）
      const isKnown = knownPrefixes.some(prefix => name === prefix || name.startsWith(`${prefix}.`));
      if (!isKnown) continue;
      if (name === 'project.optional-dependencies' || name.startsWith('project.optional-dependencies.')) {
        unsupported.push(name);
      }
    }
  
    return unsupported;
  }
  
  /**
   * 解析 pyproject.toml 文件内容
   *
   * @param {string} content - pyproject.toml 文件内容
   * @returns {Object} { ecosystem: 'pypi', packages: [{n, v, section}], unsupported_sections: string[] }
   */
  function parsePyprojectToml(content) {
    const result = {
      ecosystem: 'pypi',
      packages: [],
      unsupported_sections: []
    };
  
    if (!content || typeof content !== 'string') {
      return result;
    }
  
    const lines = content.split('\n');
  
    const { packages: pep621Packages } = parsePep621Dependencies(lines);
    const dependencyGroupPackages = parseDependencyGroups(lines);
    const poetryPackages = parsePoetrySections(lines);
    const pdmDevPackages = parsePdmDevDependencies(lines);
  
    result.packages = [
      ...pep621Packages,
      ...dependencyGroupPackages,
      ...poetryPackages,
      ...pdmDevPackages,
    ];
    result.unsupported_sections = detectUnsupportedSections(lines);
  
    return result;
  }
  
  __parsers_manifests_pyproject_toml__.default = parsePyprojectToml;
  
  
  // Module exports
  __parsers_manifests_pyproject_toml__.parsePyprojectToml = parsePyprojectToml;
})();


// ============================================================================
// Module: parsers_manifests_index
// ============================================================================

(function() {
  /**
   * Manifest Parser Router
   * 
   * 根据文件路径自动选择合适的解析器
   */
  
  const parsePackageJson = __parsers_manifests_package_json__.parsePackageJson;
  const parseNpmManifest = __parsers_manifests_package_lock_json__.parseNpmManifest;
  const parseRequirements = __parsers_manifests_requirements__.parseRequirements;
  const parseGoMod = __parsers_manifests_go_mod__.parseGoMod;
  const parseCargoToml = __parsers_manifests_cargo_toml__.parseCargoToml;
  const parseCargoManifest = __parsers_manifests_cargo_toml__.parseCargoManifest;
  const parseMavenManifest = __parsers_manifests_pom_xml__.parseMavenManifest;
  const parseRubyManifest = __parsers_manifests_gemfile__.parseRubyManifest;
  const parseComposerJson = __parsers_manifests_composer_json__.parseComposerJson;
  const parsePipfile = __parsers_manifests_pipfile__.parsePipfile;
  const parsePyprojectToml = __parsers_manifests_pyproject_toml__.parsePyprojectToml;
  
  /**
   * 根据文件路径判断生态系统类型
   * 
   * @param {string} filePath - 文件路径
   * @returns {string|null} 生态系统类型或 null
   */
  function detectEcosystem(filePath) {
    if (!filePath) return null;
    
    // npm (package.json 及 package-lock.json, pnpm-lock.yaml, yarn.lock)
    if (/(?:^|[\\/])package\.json$/.test(filePath) ||
        /(?:^|[\\/])package-lock\.json$/.test(filePath) ||
        /(?:^|[\\/])pnpm-lock\.yaml$/.test(filePath) ||
        /(?:^|[\\/])yarn\.lock$/.test(filePath)) {
      return 'npm';
    }
    
    // pypi
    if (/(?:^|[\\/])requirements(?:[-_.].*)?\.txt$/.test(filePath) || 
        /(?:^|[\\/])Pipfile$/.test(filePath) ||
        /(?:^|[\\/])pyproject\.toml$/.test(filePath)) {
      return 'pypi';
    }
    
    // go
    if (/(?:^|[\\/])go\.mod$/.test(filePath)) {
      return 'go';
    }
    
    // cargo (rust: Cargo.toml 及 Cargo.lock)
    if (/(?:^|[\\/])Cargo\.(toml|lock)$/.test(filePath)) {
      return 'cargo';
    }
    
    // maven
    if (/(?:^|[\\/])pom\.xml$/.test(filePath) || 
        /(?:^|[\\/])build\.gradle(\.kts)?$/.test(filePath) ||
        /(?:^|[\\/])gradle\.lockfile$/.test(filePath) ||
        /(?:^|[\\/])dependency-locks[\\/].*\.lockfile$/.test(filePath)) {
      return 'maven';
    }
    
    // rubygems
    if (/(?:^|[\\/])Gemfile$/.test(filePath) || 
        /\.gemspec$/.test(filePath)) {
      return 'rubygems';
    }
    
    // packagist (php)
    if (/(?:^|[\\/])composer\.json$/.test(filePath)) {
      return 'packagist';
    }
    
    return null;
  }
  
  /**
   * 解析依赖清单文件
   * 
   * @param {string} filePath - 文件路径
   * @param {string} content - 文件内容
   * @returns {Object|null} 解析结果 { ecosystem, packages: [{n, v}] } 或 null
   */
  function parseManifest(filePath, content) {
    const ecosystem = detectEcosystem(filePath);
    
    if (!ecosystem) {
      return null;
    }
    
    switch (ecosystem) {
      case 'npm':
        return parseNpmManifest(content, filePath);
        
      case 'pypi':
        // D1-09 修复：Pipfile 和 pyproject.toml 此前被识别为 pypi manifest，
        // 但一直返回空 packages（"看起来正常放行，实际零组件审计"的覆盖空洞）
        if (/(?:^|[\\/])requirements(?:[-_.].*)?\.txt$/.test(filePath)) {
          return parseRequirements(content);
        }
        if (/(?:^|[\\/])Pipfile$/.test(filePath)) {
          return parsePipfile(content);
        }
        if (/(?:^|[\\/])pyproject\.toml$/.test(filePath)) {
          return parsePyprojectToml(content);
        }
        return { ecosystem: 'pypi', packages: [] };
        
      case 'go':
        return parseGoMod(content);
        
      case 'cargo':
        return parseCargoManifest(content, filePath);
        
      case 'maven':
        return parseMavenManifest(content, filePath);
        
      case 'rubygems':
        return parseRubyManifest(content, filePath);
        
      case 'packagist':
        return parseComposerJson(content);
        
      default:
        return null;
    }
  }
  
  __parsers_manifests_index__.default = parseManifest;
  
  
  // Module exports
  __parsers_manifests_index__.detectEcosystem = detectEcosystem;
  __parsers_manifests_index__.parseManifest = parseManifest;
})();


// ============================================================================
// Module: parsers_commands_name_only
// ============================================================================

(function() {
  /**
   * D4-FIX: 构造“裸包名 install”解析结果。
   *
   * 裸包名（无版本）在 PreToolUse 阶段永远拿不到 resolved version，
   * 必须显式标记 resolution_state='NAME_ONLY'，让 Server 短路（不返回全量 CVE 命中），
   * 待 PostToolUse 阶段用对应生态探测命令拿真实版本后再二次审计。
   *
   * 为什么单独成文件：此前它定义在 commands/index.js 里，而 index.js 又要 import
   * pip/npm/... 这些解析器 —— 解析器再回过头 import index.js 就形成了循环依赖。
   * ESM 下这个环在运行时侥幸能跑（函数调用被延后），但 CJS bundle 是按值捕获
   * 导入绑定的（`const makeNameOnly = ns.makeNameOnly`），环会让解析器在
   * index.js 执行完之前就捕获到 undefined，最终 `makeNameOnly is not a function`
   * 崩掉整个 hook（fail-open 前就抛异常）。放到叶子模块，环即消失。
   *
   * @param {string} name - 包名
   * @returns {Object} { n, v: '', resolution_state: 'NAME_ONLY' }
   */
  function makeNameOnly(name) {
    return { n: name, v: '', resolution_state: 'NAME_ONLY' };
  }
  
  __parsers_commands_name_only__.default = makeNameOnly;
  
  
  // Module exports
  __parsers_commands_name_only__.makeNameOnly = makeNameOnly;
})();


// ============================================================================
// Module: parsers_commands_npm
// ============================================================================

(function() {
  /**
   * npm/yarn/pnpm/bun Command Parser
   * 
   * 解析 npm 系列包管理器的安装命令
   */
  
  /**
   * 将命令参数字符串按空白拆分，正确处理引号包裹的内容（单引号/双引号）
   * 例: `id3-writer@">=1.0.0 <2.0.0" lodash` -> ["id3-writer@>=1.0.0 <2.0.0", "lodash"]
   *
   * @param {string} args - 参数字符串
   * @returns {string[]} token 列表（引号已剥离）
   */
  function splitArgs(args) {
    const tokens = [];
    let current = '';
    let inQuote = null; // 当前引号字符 ' 或 "
  
    for (let i = 0; i < args.length; i++) {
      const ch = args[i];
  
      if (inQuote) {
        if (ch === inQuote) {
          // 引号结束，不将引号字符加入 token
          inQuote = null;
        } else {
          current += ch;
        }
      } else if (ch === '"' || ch === "'") {
        // 引号开始，不将引号字符加入 token
        inQuote = ch;
      } else if (/\s/.test(ch)) {
        if (current) {
          tokens.push(current);
          current = '';
        }
      } else {
        current += ch;
      }
    }
  
    if (current) tokens.push(current);
    return tokens;
  }
  
  /**
   * 解析包字符串
   * 
   * 支持格式:
   * - package
   * - package@version
   * - @scope/package
   * - @scope/package@version
   * 
   * @param {string} pkgStr - 包字符串
   * @returns {Object|null} {n, v} 或 null
   */
  function parsePackageString(pkgStr) {
    if (!pkgStr || typeof pkgStr !== 'string') {
      return null;
    }
    
    const trimmed = pkgStr.trim();
    
    // 跳过 flags
    if (trimmed.startsWith('-')) {
      return null;
    }
    
    // 跳过 URL
    if (trimmed.startsWith('http') || trimmed.startsWith('git')) {
      return null;
    }
    
    // 跳过本地路径
    if (trimmed.startsWith('.') || trimmed.startsWith('/') || trimmed.startsWith('file:')) {
      return null;
    }
    
    // 跳过 shell 重定向 token（2>&1、>/dev/null 等）
    if (/^\d*>/.test(trimmed) || /^&/.test(trimmed)) {
      return null;
    }
    
    // 解析 @scope/package@version 格式
    // 需要特殊处理因为 @ 既用于 scope 也用于版本
    let name, version;
    
    if (trimmed.startsWith('@')) {
      // scoped package: @scope/package 或 @scope/package@version
      const lastAtIndex = trimmed.lastIndexOf('@');
      
      if (lastAtIndex > 0 && lastAtIndex !== trimmed.indexOf('@')) {
        // 有版本号: @scope/package@version
        name = trimmed.substring(0, lastAtIndex);
        version = trimmed.substring(lastAtIndex + 1);
      } else {
        // 无版本号: @scope/package
        name = trimmed;
        version = '';
      }
    } else {
      // 非 scoped package
      const atIndex = trimmed.indexOf('@');
      
      if (atIndex > 0) {
        name = trimmed.substring(0, atIndex);
        version = trimmed.substring(atIndex + 1);
      } else {
        name = trimmed;
        version = '';
      }
    }
    
    // 验证包名
    if (!name || !/^(@[a-zA-Z0-9_-]+\/)?[a-zA-Z0-9_-]/.test(name)) {
      return null;
    }
    
    // 提取版本：支持范围表达式（>=1.0.0 <2.0.0、^1.0.0、~1.0.0 等）
    // 从范围中提取第一个精确版本数字部分，发给 Server 做查询
    const cleanVersion = extractVersion(version);
    
    // D4-FIX: 裸包名（npm install foo，无 @version）标记 NAME_ONLY
    return cleanVersion ? { n: name, v: cleanVersion } : makeNameOnly(name);
  }
  
  /**
   * 从版本字符串中提取可用于查询的版本号
   * 
   * 支持：
   * - 精确版本: "1.0.0" -> "1.0.0"
   * - 范围: ">=1.0.0 <2.0.0" -> "1.0.0"（取第一个数字版本）
   * - 前缀: "^1.0.0", "~1.0.0" -> "1.0.0"
   * - 空字符串（无版本）: "" -> ""
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 提取出的版本号，无法提取时返回空字符串
   */
  function extractVersion(version) {
    if (!version) return '';
    
    // 已经是精确版本（以数字开头）
    if (/^\d/.test(version)) return version;
    
    // 去掉前缀操作符（^、~、>=、<=、>、<、!=、=）后取第一段
    const match = version.match(/(?:^|[\s,|])(?:[><=!~^]*)\s*(\d[\w.-]*)/);
    if (match) return match[1];
    
    return '';
  }
  
  /**
   * 检查是否为 npm 系列命令
   * 
   * @param {string} command - 命令字符串
   * @returns {boolean}
   */
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  function isNpmCommand(command) {
    if (!command) return false;
    
    return /^(npm|yarn|pnpm|bun)\s+(install|add|i)\s/.test(command);
  }
  
  /**
   * 解析 npm 系列安装命令
   * 
   * 支持:
   * - npm install package@version
   * - npm i package@version
   * - npm add package@version
   * - yarn add package@version
   * - pnpm add package@version
   * - pnpm install package@version
   * - bun add package@version
   * - bun install package@version
   * 
   * @param {string} command - 命令字符串
   * @returns {Object} { ecosystem: 'npm', packages: [{n, v}] }
   */
  function parseNpmCommand(command) {
    const result = {
      ecosystem: 'npm',
      packages: []
    };
    
    if (!command || typeof command !== 'string') {
      return result;
    }
    
    // 提取命令后的参数部分，截断 shell 重定向（> 或 2>）之前的内容
    const match = command.match(/^(?:npm|yarn|pnpm|bun)\s+(?:install|add|i)\s+(.+)$/);
    
    if (!match) {
      return result;
    }
    
    // 截断 shell 重定向部分（在引号外的 > 或 2> 才算重定向）
    // 先用 splitArgs 分割，再丢弃重定向 token 及其之后的内容
    const rawParts = splitArgs(match[1]);
    const parts = [];
    for (const p of rawParts) {
      // 遇到重定向 token 停止（\d*> 开头，且不是包名/版本的一部分）
      if (/^\d*>/.test(p) || p === '&') break;
      parts.push(p);
    }
    
    for (const part of parts) {
      const pkg = parsePackageString(part);
      
      if (pkg) {
        result.packages.push(pkg);
      }
    }
    
    return result;
  }
  
  __parsers_commands_npm__.default = parseNpmCommand;
  
  
  // Module exports
  __parsers_commands_npm__.parsePackageString = parsePackageString;
  __parsers_commands_npm__.isNpmCommand = isNpmCommand;
  __parsers_commands_npm__.parseNpmCommand = parseNpmCommand;
})();


// ============================================================================
// Module: parsers_commands_pip
// ============================================================================

(function() {
  /**
   * pip Command Parser
   * 
   * 解析 pip 安装命令
   */
  
  /**
   * 将命令参数字符串按空白拆分，正确处理引号包裹的内容（单引号/双引号）
   * 例: `"requests>=2.25.0,<3.0.0" flask` -> ["requests>=2.25.0,<3.0.0", "flask"]
   *
   * @param {string} args - 参数字符串
   * @returns {string[]} token 列表（引号已剥离）
   */
  function splitArgs(args) {
    const tokens = [];
    let current = '';
    let inQuote = null;
  
    for (let i = 0; i < args.length; i++) {
      const ch = args[i];
  
      if (inQuote) {
        if (ch === inQuote) {
          inQuote = null;
        } else {
          current += ch;
        }
      } else if (ch === '"' || ch === "'") {
        inQuote = ch;
      } else if (/\s/.test(ch)) {
        if (current) {
          tokens.push(current);
          current = '';
        }
      } else {
        current += ch;
      }
    }
  
    if (current) tokens.push(current);
    return tokens;
  }
  
  /**
   * 解析包字符串
   * 
   * 支持格式:
   * - package==version
   * - package>=version
   * - package~=version
   * - package[extra]==version
   * 
   * @param {string} pkgStr - 包字符串
   * @returns {Object|null} {n, v} 或 null
   */
  function parsePackageString(pkgStr) {
    if (!pkgStr || typeof pkgStr !== 'string') {
      return null;
    }
    
    const trimmed = pkgStr.trim();
    
    // 跳过 flags
    if (trimmed.startsWith('-')) {
      return null;
    }
    
    // 跳过 URL
    if (trimmed.startsWith('http') || trimmed.startsWith('git')) {
      return null;
    }
    
    // 跳过本地路径
    if (trimmed.startsWith('.') || trimmed.startsWith('/')) {
      return null;
    }
    
    // 跳过 shell 重定向 token（2>&1、>/dev/null 等）
    if (/^\d*>/.test(trimmed) || /^&/.test(trimmed)) {
      return null;
    }
    
    // 解析 package[extras]==version 格式（有版本约束）
    const matchWithVersion = trimmed.match(/^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)(?:\[[^\]]+\])?\s*(==|>=|<=|~=|>|<|!=)\s*(.+)$/);
    
    if (matchWithVersion) {
      const name = matchWithVersion[1];
      const version = matchWithVersion[4].trim();
      
      if (!version || !/^\d/.test(version)) {
        return null;
      }
      
      // 处理范围版本（取第一个版本）
      const cleanVersion = version.split(',')[0].replace(/^[=<>~!]+/, '').trim();
      
      if (!cleanVersion || !/^\d/.test(cleanVersion)) {
        return null;
      }
      
      return { n: name, v: cleanVersion };
    }
    
    // 支持 package[extras]@version 格式（Poetry 风格）
    const matchAtVersion = trimmed.match(/^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)(?:\[[^\]]+\])?@[\^~=]?\s*(.+)$/);
    if (matchAtVersion) {
      const name = matchAtVersion[1];
      const rawVer = matchAtVersion[3].trim();
      if (rawVer === 'latest') {
        return makeNameOnly(name);
      }
      const cleanVersion = rawVer.split(',')[0].replace(/^[=<>~!^]+/, '').trim();
      if (cleanVersion && /^\d/.test(cleanVersion)) {
        return { n: name, v: cleanVersion };
      }
      return makeNameOnly(name);
    }
  
    // 无版本号：仅包名，version 用空字符串表示（Server 侧按包名查询）
    const matchNameOnly = trimmed.match(/^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)(?:\[[^\]]+\])?$/);
    
    if (matchNameOnly) {
      return makeNameOnly(matchNameOnly[1]);
    }
    
    return null;
  }
  
  /**
   * Python 包管理命令中带参数值的 flags
   */
  const FLAGS_WITH_VALUE = new Set([
    '-r', '--requirement',
    '-c', '--constraint',
    '-i', '--index-url',
    '--extra-index-url',
    '-t', '--target',
    '-e', '--editable',
    '--group', '-G',
    '--source',
    '--python',
  ]);
  
  /**
   * 检查是否为 pip / poetry / pipenv / pdm / uv 安装命令
   * 
   * @param {string} command - 命令字符串
   * @returns {boolean}
   */
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  function isPipCommand(command) {
    if (!command) return false;
    
    return /^(pip3?|python3?\s+-m\s+pip|uv\s+pip|pipenv)\s+install\s/.test(command) ||
           /^(poetry|pdm|uv)\s+add\s/.test(command);
  }
  
  /**
   * 解析 pip / poetry / pipenv / pdm / uv 安装命令
   * 
   * 支持:
   * - pip install package==version
   * - pip3 install package==version
   * - python -m pip install package==version
   * - uv pip install package==version
   * - poetry add package@^version
   * - pipenv install package==version
   * - pdm add package
   * - uv add package
   * 
   * @param {string} command - 命令字符串
   * @returns {Object} { ecosystem: 'pypi', packages: [{n, v}] }
   */
  function parsePipCommand(command) {
    const result = {
      ecosystem: 'pypi',
      packages: []
    };
    
    if (!command || typeof command !== 'string') {
      return result;
    }
    
    // 提取命令后的参数部分，截断 shell 重定向（> 或 2>）之前的内容
    const match = command.match(/^(?:(?:pip3?|python3?\s+-m\s+pip|uv\s+pip|pipenv)\s+install|(?:poetry|pdm|uv)\s+add)\s+(.+)$/);
    
    if (!match) {
      return result;
    }
    
    // 截断 shell 重定向部分，使用引号感知分割
    const rawParts = splitArgs(match[1]);
    const parts = [];
    for (const p of rawParts) {
      if (/^\d*>/.test(p) || p === '&') break;
      parts.push(p);
    }
    
    let skipNext = false;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (skipNext) {
        skipNext = false;
        continue;
      }
  
      if (FLAGS_WITH_VALUE.has(part)) {
        skipNext = true;
        continue;
      }
  
      if (part.startsWith('--') && part.includes('=')) {
        continue;
      }
  
      const pkg = parsePackageString(part);
      if (pkg) {
        result.packages.push(pkg);
      }
    }
    
    return result;
  }
  
  __parsers_commands_pip__.default = parsePipCommand;
  
  
  // Module exports
  __parsers_commands_pip__.parsePackageString = parsePackageString;
  __parsers_commands_pip__.isPipCommand = isPipCommand;
  __parsers_commands_pip__.parsePipCommand = parsePipCommand;
})();


// ============================================================================
// Module: parsers_commands_go
// ============================================================================

(function() {
  /**
   * Go Command Parser
   * 
   * 解析 go get / go install 命令
   */
  
  /**
   * 解析 Go 模块路径字符串
   * 
   * 支持格式:
   * - golang.org/x/crypto
   * - golang.org/x/crypto@v1.2.3
   * - github.com/foo/bar@latest
   * - github.com/foo/bar/v2@v2.1.0
   * 
   * @param {string} pkgStr - 模块路径字符串
   * @returns {Object|null} {n, v} 或 null
   */
  function parsePackageString(pkgStr) {
    if (!pkgStr || typeof pkgStr !== 'string') {
      return null;
    }
  
    const trimmed = pkgStr.trim();
  
    // 跳过 flags
    if (trimmed.startsWith('-')) {
      return null;
    }
  
    // 跳过 shell 重定向
    if (/^\d*>/.test(trimmed) || /^&/.test(trimmed)) {
      return null;
    }
  
    // Go 模块路径必须包含 '.'（域名部分）
    // 例: golang.org/x/crypto, github.com/foo/bar
    // 排除简单单词（如 ./local）
    if (!trimmed.includes('.') || trimmed.startsWith('.') || trimmed.startsWith('/')) {
      return null;
    }
  
    let name, version;
  
    const atIndex = trimmed.indexOf('@');
    if (atIndex > 0) {
      name = trimmed.substring(0, atIndex);
      const rawVersion = trimmed.substring(atIndex + 1);
  
      // 跳过 latest / upgrade / patch 等伪版本
      if (rawVersion === 'latest' || rawVersion === 'upgrade' || rawVersion === 'patch') {
        version = '';
      } else {
        // 去掉 v 前缀
        version = rawVersion.replace(/^v/, '');
      }
    } else {
      name = trimmed;
      version = '';
    }
  
    // 验证模块路径格式：至少有一个 '/' 和域名（含 '.'）
    if (!name || !name.includes('/') || !name.includes('.')) {
      return null;
    }
  
    // 基本域名格式校验
    if (!/^[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}\//.test(name)) {
      return null;
    }
  
    // D4-FIX: 裸模块路径（go get pkg，无 @version）标记 NAME_ONLY
    return version ? { n: name, v: version } : makeNameOnly(name);
  }
  
  /**
   * 检查是否为 go get / go install 命令
   * 
   * @param {string} command - 命令字符串
   * @returns {boolean}
   */
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  function isGoCommand(command) {
    if (!command) return false;
  
    return /^go\s+(get|install)\s/.test(command);
  }
  
  /**
   * 解析 go get / go install 命令
   * 
   * 支持:
   * - go get golang.org/x/crypto@v1.2.3
   * - go get -u golang.org/x/crypto
   * - go install github.com/foo/bar@v1.0.0
   * 
   * @param {string} command - 命令字符串
   * @returns {Object} { ecosystem: 'go', packages: [{n, v}] }
   */
  function parseGoCommand(command) {
    const result = {
      ecosystem: 'go',
      packages: []
    };
  
    if (!command || typeof command !== 'string') {
      return result;
    }
  
    const match = command.match(/^go\s+(?:get|install)\s+(.+)$/);
  
    if (!match) {
      return result;
    }
  
    // 按空格分割参数
    const parts = match[1].trim().split(/\s+/);
  
    for (const part of parts) {
      // 跳过 flags（-u, -d, -t, -v 等）
      if (part.startsWith('-')) {
        continue;
      }
  
      // 跳过 shell 重定向
      if (/^\d*>/.test(part) || part === '&') {
        break;
      }
  
      const pkg = parsePackageString(part);
  
      if (pkg) {
        result.packages.push(pkg);
      }
    }
  
    return result;
  }
  
  __parsers_commands_go__.default = parseGoCommand;
  
  
  // Module exports
  __parsers_commands_go__.parsePackageString = parsePackageString;
  __parsers_commands_go__.isGoCommand = isGoCommand;
  __parsers_commands_go__.parseGoCommand = parseGoCommand;
})();


// ============================================================================
// Module: parsers_commands_cargo
// ============================================================================

(function() {
  /**
   * Cargo Command Parser
   * 
   * 解析 cargo add / cargo install 命令
   */
  
  /**
   * 解析 Cargo 包字符串
   * 
   * 支持格式:
   * - serde
   * - serde@1.0.0
   * - tokio@1.35.0
   * 
   * @param {string} pkgStr - 包字符串
   * @returns {Object|null} {n, v} 或 null
   */
  function parsePackageString(pkgStr) {
    if (!pkgStr || typeof pkgStr !== 'string') {
      return null;
    }
  
    const trimmed = pkgStr.trim();
  
    // 跳过 flags
    if (trimmed.startsWith('-')) {
      return null;
    }
  
    // 跳过 URL
    if (trimmed.startsWith('http') || trimmed.startsWith('git')) {
      return null;
    }
  
    // 跳过本地路径
    if (trimmed.startsWith('.') || trimmed.startsWith('/')) {
      return null;
    }
  
    // 跳过 shell 重定向
    if (/^\d*>/.test(trimmed) || /^&/.test(trimmed)) {
      return null;
    }
  
    let name, version;
  
    const atIndex = trimmed.indexOf('@');
    if (atIndex > 0) {
      name = trimmed.substring(0, atIndex);
      version = trimmed.substring(atIndex + 1);
    } else {
      name = trimmed;
      version = '';
    }
  
    // Cargo 包名：字母、数字、连字符、下划线
    if (!name || !/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(name)) {
      return null;
    }
  
    // 清理版本号
    const cleanVersion = normalizeVersion(version);
  
    // D4-FIX: 裸包名（cargo add foo，无 @version）标记 NAME_ONLY
    return cleanVersion ? { n: name, v: cleanVersion } : makeNameOnly(name);
  }
  
  /**
   * 标准化版本号
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 清理后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 去掉前缀操作符（^, ~, >=, <=, >, <, =）
    cleaned = cleaned.replace(/^[>=<~^]+/, '').trim();
  
    // 处理范围: ">=1.0, <2.0" -> "1.0"
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[>=<~^]+/, '').trim();
    }
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 需要跳过值的 cargo 参数 flags
   */
  const FLAGS_WITH_VALUE = new Set([
    '--features', '-F',
    '--version', 
    '--git', '--branch', '--tag', '--rev',
    '--path', '--registry',
    '--rename',
    '--target', '--target-dir',
    '--jobs', '-j',
    '--color',
    '--config',
  ]);
  
  /**
   * 检查是否为 cargo add / cargo install 命令
   * 
   * @param {string} command - 命令字符串
   * @returns {boolean}
   */
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  function isCargoCommand(command) {
    if (!command) return false;
  
    return /^cargo\s+(add|install)\s/.test(command);
  }
  
  /**
   * 解析 cargo add / cargo install 命令
   * 
   * 支持:
   * - cargo add serde@1.0.0
   * - cargo add serde tokio@1.35
   * - cargo install ripgrep
   * - cargo add serde --features derive
   * 
   * @param {string} command - 命令字符串
   * @returns {Object} { ecosystem: 'cargo', packages: [{n, v}] }
   */
  function parseCargoCommand(command) {
    const result = {
      ecosystem: 'cargo',
      packages: []
    };
  
    if (!command || typeof command !== 'string') {
      return result;
    }
  
    const match = command.match(/^cargo\s+(?:add|install)\s+(.+)$/);
  
    if (!match) {
      return result;
    }
  
    const parts = match[1].trim().split(/\s+/);
  
    let skipNext = false;
    for (const part of parts) {
      // 上一个 token 是带值 flag，跳过这个 token（它是 flag 的值）
      if (skipNext) {
        skipNext = false;
        continue;
      }
  
      // 跳过 shell 重定向
      if (/^\d*>/.test(part) || part === '&') {
        break;
      }
  
      // 检查是否为带值的 flag（--features derive）
      if (part.startsWith('-')) {
        // 处理 --flag=value 形式（不需要跳过下一个）
        if (part.includes('=')) {
          continue;
        }
        // 检查是否需要消耗下一个参数
        if (FLAGS_WITH_VALUE.has(part)) {
          skipNext = true;
        }
        continue;
      }
  
      const pkg = parsePackageString(part);
  
      if (pkg) {
        result.packages.push(pkg);
      }
    }
  
    return result;
  }
  
  __parsers_commands_cargo__.default = parseCargoCommand;
  
  
  // Module exports
  __parsers_commands_cargo__.parsePackageString = parsePackageString;
  __parsers_commands_cargo__.normalizeVersion = normalizeVersion;
  __parsers_commands_cargo__.isCargoCommand = isCargoCommand;
  __parsers_commands_cargo__.parseCargoCommand = parseCargoCommand;
})();


// ============================================================================
// Module: parsers_commands_gem
// ============================================================================

(function() {
  /**
   * RubyGems Command Parser
   * 
   * 解析 gem install / bundle add 命令
   */
  
  /**
   * 将命令参数字符串按空白拆分，正确处理引号包裹的内容（单引号/双引号）
   * 例: `-v "~> 7.0" rails` -> ["-v", "~> 7.0", "rails"]
   *
   * @param {string} args - 参数字符串
   * @returns {string[]} token 列表（引号已剥离）
   */
  function splitArgs(args) {
    const tokens = [];
    let current = '';
    let inQuote = null;
  
    for (let i = 0; i < args.length; i++) {
      const ch = args[i];
  
      if (inQuote) {
        if (ch === inQuote) {
          inQuote = null;
        } else {
          current += ch;
        }
      } else if (ch === '"' || ch === "'") {
        inQuote = ch;
      } else if (/\s/.test(ch)) {
        if (current) {
          tokens.push(current);
          current = '';
        }
      } else {
        current += ch;
      }
    }
  
    if (current) tokens.push(current);
    return tokens;
  }
  
  /**
   * 标准化版本号
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 清理后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 去掉引号
    cleaned = cleaned.replace(/^["']|["']$/g, '');
  
    // 去掉前缀操作符（~>, >=, <=, >, <, =, !=）
    cleaned = cleaned.replace(/^[~><=!]+\s*/, '').trim();
  
    // 处理范围: ">=1.0, <2.0" -> "1.0"
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].replace(/^[~><=!]+\s*/, '').trim();
    }
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 解析包名字符串
   * 
   * @param {string} pkgStr - 包名
   * @returns {Object|null} {n, v} 或 null（仅包名，版本从 flag 中获取）
   */
  function parsePackageString(pkgStr) {
    if (!pkgStr || typeof pkgStr !== 'string') {
      return null;
    }
  
    const trimmed = pkgStr.trim();
  
    // 跳过 flags
    if (trimmed.startsWith('-')) {
      return null;
    }
  
    // 跳过 URL
    if (trimmed.startsWith('http') || trimmed.startsWith('git')) {
      return null;
    }
  
    // 跳过本地路径
    if (trimmed.startsWith('.') || trimmed.startsWith('/')) {
      return null;
    }
  
    // 跳过 shell 重定向
    if (/^\d*>/.test(trimmed) || /^&/.test(trimmed)) {
      return null;
    }
  
    // RubyGems 包名：字母开头，字母/数字/连字符/下划线
    if (!/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(trimmed)) {
      return null;
    }
  
    return makeNameOnly(trimmed);
  }
  
  /**
   * 检查是否为 gem / bundle 命令
   * 
   * @param {string} command - 命令字符串
   * @returns {boolean}
   */
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  function isGemCommand(command) {
    if (!command) return false;
  
    return /^gem\s+install\s/.test(command) || /^bundle\s+(add|install)\s/.test(command);
  }
  
  /**
   * gem install 中需要跳过值的 flags
   */
  const GEM_FLAGS_WITH_VALUE = new Set([
    '-v', '--version',
    '-i', '--install-dir',
    '--platform',
    '--source',
    '--http-proxy',
    '-n', '--bindir',
    '--document',
    '-g', '--file',
  ]);
  
  /**
   * bundle add 中需要跳过值的 flags
   */
  const BUNDLE_FLAGS_WITH_VALUE = new Set([
    '--version',
    '--source',
    '--git', '--branch', '--ref',
    '--path',
    '--group',
  ]);
  
  /**
   * 解析 gem install / bundle add 命令
   * 
   * 支持:
   * - gem install rails
   * - gem install rails -v 7.0.0
   * - gem install rails --version "~> 7.0"
   * - gem install nokogiri puma
   * - bundle add puma
   * - bundle add puma --version="~> 5.0"
   * 
   * @param {string} command - 命令字符串
   * @returns {Object} { ecosystem: 'rubygems', packages: [{n, v}] }
   */
  function parseGemCommand(command) {
    const result = {
      ecosystem: 'rubygems',
      packages: []
    };
  
    if (!command || typeof command !== 'string') {
      return result;
    }
  
    // 匹配 gem install 或 bundle add/install
    const match = command.match(/^(?:gem\s+install|bundle\s+(?:add|install))\s+(.+)$/);
  
    if (!match) {
      return result;
    }
  
    const isBundle = command.startsWith('bundle');
    const flagsWithValue = isBundle ? BUNDLE_FLAGS_WITH_VALUE : GEM_FLAGS_WITH_VALUE;
  
    const parts = splitArgs(match[1].trim());
  
    // 第一遍：收集包名和版本关联
    const packages = [];
    let skipNext = false;
    let lastPkgIndex = -1;
  
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
  
      if (skipNext) {
        skipNext = false;
        continue;
      }
  
      // 跳过 shell 重定向
      if (/^\d*>/.test(part) || part === '&') {
        break;
      }
  
      // 处理 -v / --version flag
      if (part === '-v' || part === '--version') {
        if (i + 1 < parts.length && lastPkgIndex >= 0) {
          const verStr = parts[i + 1];
          packages[lastPkgIndex].v = normalizeVersion(verStr);
          skipNext = true;
        }
        continue;
      }
  
      // 处理 --version="~> 5.0" 形式
      if (part.startsWith('--version=')) {
        const verStr = part.substring('--version='.length);
        if (lastPkgIndex >= 0) {
          packages[lastPkgIndex].v = normalizeVersion(verStr);
        }
        continue;
      }
  
      // 处理 -v"7.0.0" 形式（无空格）
      if (/^-v["']?[\d~><=]/.test(part)) {
        const verStr = part.substring(2);
        if (lastPkgIndex >= 0) {
          packages[lastPkgIndex].v = normalizeVersion(verStr);
        }
        continue;
      }
  
      // 处理其他带值 flags
      if (part.startsWith('-')) {
        if (part.includes('=')) {
          continue;
        }
        if (flagsWithValue.has(part)) {
          skipNext = true;
        }
        continue;
      }
  
      // 包名
      const pkg = parsePackageString(part);
      if (pkg) {
        packages.push(pkg);
        lastPkgIndex = packages.length - 1;
      }
    }
  
    result.packages = packages;
    return result;
  }
  
  __parsers_commands_gem__.default = parseGemCommand;
  
  
  // Module exports
  __parsers_commands_gem__.normalizeVersion = normalizeVersion;
  __parsers_commands_gem__.parsePackageString = parsePackageString;
  __parsers_commands_gem__.isGemCommand = isGemCommand;
  __parsers_commands_gem__.parseGemCommand = parseGemCommand;
})();


// ============================================================================
// Module: parsers_commands_composer
// ============================================================================

(function() {
  /**
   * Composer Command Parser
   * 
   * 解析 composer require 命令
   */
  
  /**
   * 标准化版本号
   * 
   * @param {string} version - 原始版本字符串
   * @returns {string} 清理后的版本号
   */
  function normalizeVersion(version) {
    if (!version || typeof version !== 'string') {
      return '';
    }
  
    let cleaned = version.trim();
  
    // 去掉前缀操作符（^, ~, >=, <=, >, <, !=, =）
    cleaned = cleaned.replace(/^[>=<~^!=]+/, '').trim();
  
    // 去掉 v 前缀
    cleaned = cleaned.replace(/^v/, '');
  
    // 处理 || 范围: "^1.0 || ^2.0" -> "1.0"
    if (cleaned.includes('||')) {
      cleaned = cleaned.split('||')[0].trim().replace(/^[>=<~^!=]+/, '');
    }
  
    // 处理空格范围: ">=1.0 <2.0" -> "1.0"
    if (cleaned.includes(' ')) {
      cleaned = cleaned.split(' ')[0].replace(/^[>=<~^!=]+/, '');
    }
  
    // 跳过通配符
    if (cleaned === '*' || cleaned === 'dev-master' || cleaned === 'dev-main' ||
        cleaned.startsWith('dev-') || cleaned.startsWith('@')) {
      return '';
    }
  
    // 验证以数字开头
    if (!/^\d/.test(cleaned)) {
      return '';
    }
  
    return cleaned;
  }
  
  /**
   * 解析 Composer 包字符串
   * 
   * 支持格式:
   * - vendor/package
   * - vendor/package:^2.0
   * - vendor/package:2.0.0
   * 
   * @param {string} pkgStr - 包字符串
   * @returns {Object|null} {n, v} 或 null
   */
  function parsePackageString(pkgStr) {
    if (!pkgStr || typeof pkgStr !== 'string') {
      return null;
    }
  
    const trimmed = pkgStr.trim();
  
    // 跳过 flags
    if (trimmed.startsWith('-')) {
      return null;
    }
  
    // 跳过 shell 重定向
    if (/^\d*>/.test(trimmed) || /^&/.test(trimmed)) {
      return null;
    }
  
    let name, version;
  
    // Composer 版本用 ':' 分隔（不是 '@'）
    const colonIndex = trimmed.indexOf(':');
    if (colonIndex > 0) {
      name = trimmed.substring(0, colonIndex);
      version = trimmed.substring(colonIndex + 1);
    } else {
      name = trimmed;
      version = '';
    }
  
    // Composer 包名必须是 vendor/package 格式
    if (!name || !/^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?\/[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$/.test(name)) {
      return null;
    }
  
    const cleanVersion = normalizeVersion(version);
  
    // D4-FIX: 裸包名（composer require vendor/pkg，无 :version）标记 NAME_ONLY
    return cleanVersion ? { n: name, v: cleanVersion } : makeNameOnly(name);
  }
  
  /**
   * 检查是否为 composer require 命令
   * 
   * @param {string} command - 命令字符串
   * @returns {boolean}
   */
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  function isComposerCommand(command) {
    if (!command) return false;
  
    return /^composer\s+(require|install)\s/.test(command);
  }
  
  /**
   * composer require 中需要跳过值的 flags
   */
  const FLAGS_WITH_VALUE = new Set([
    '--working-dir', '-d',
    '--prefer-install',
    '--repository',
    '--repository-url',
  ]);
  
  /**
   * 解析 composer require 命令
   * 
   * 支持:
   * - composer require vendor/package
   * - composer require vendor/package:^2.0
   * - composer require vendor/package vendor/other:1.0
   * - composer require --dev vendor/package
   * 
   * @param {string} command - 命令字符串
   * @returns {Object} { ecosystem: 'packagist', packages: [{n, v}] }
   */
  function parseComposerCommand(command) {
    const result = {
      ecosystem: 'packagist',
      packages: []
    };
  
    if (!command || typeof command !== 'string') {
      return result;
    }
  
    const match = command.match(/^composer\s+(?:require|install)\s+(.+)$/);
  
    if (!match) {
      return result;
    }
  
    const parts = match[1].trim().split(/\s+/);
  
    let skipNext = false;
    for (const part of parts) {
      if (skipNext) {
        skipNext = false;
        continue;
      }
  
      // 跳过 shell 重定向
      if (/^\d*>/.test(part) || part === '&') {
        break;
      }
  
      // 处理 flags
      if (part.startsWith('-')) {
        if (part.includes('=')) {
          continue;
        }
        if (FLAGS_WITH_VALUE.has(part)) {
          skipNext = true;
        }
        continue;
      }
  
      const pkg = parsePackageString(part);
  
      if (pkg) {
        result.packages.push(pkg);
      }
    }
  
    return result;
  }
  
  __parsers_commands_composer__.default = parseComposerCommand;
  
  
  // Module exports
  __parsers_commands_composer__.normalizeVersion = normalizeVersion;
  __parsers_commands_composer__.parsePackageString = parsePackageString;
  __parsers_commands_composer__.isComposerCommand = isComposerCommand;
  __parsers_commands_composer__.parseComposerCommand = parseComposerCommand;
})();


// ============================================================================
// Module: parsers_commands_mvn
// ============================================================================

(function() {
  /**
   * Maven Command Parser
   * 
   * 解析 mvn / mvnw 依赖命令（如 dependency:get, install:install-file 等）
   */
  
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  /**
   * 检查是否为 Maven 相关依赖命令
   * 
   * @param {string} command - 命令行字符串
   * @returns {boolean}
   */
  function isMavenCommand(command) {
    if (!command || typeof command !== 'string') {
      return false;
    }
  
    const trimmed = command.trim();
  
    // 必须以 mvn、mvnw 或 ./mvnw 开头
    if (!/^(?:mvn|mvnw|\.\/mvnw)\s+/.test(trimmed)) {
      return false;
    }
  
    // 匹配常见的依赖下载/处理插件命令，或带有 -Dartifact= / -DgroupId=
    return (
      /\bdependency:(?:get|copy|unpack|purge-local-repository)\b/.test(trimmed) ||
      /\binstall:install-file\b/.test(trimmed) ||
      /-Dartifact=/.test(trimmed) ||
      (/-DgroupId=/.test(trimmed) && /-DartifactId=/.test(trimmed))
    );
  }
  
  /**
   * 解析 Maven 依赖命令中的组件坐标
   * 
   * 支持格式:
   * - mvn dependency:get -Dartifact=org.springframework:spring-core:5.3.20
   * - mvn dependency:get -Dartifact="org.apache.logging.log4j:log4j-core:2.14.1"
   * - mvn dependency:get -DgroupId=junit -DartifactId=junit -Dversion=4.13.2
   * 
   * @param {string} command - 命令行字符串
   * @returns {Object} { ecosystem: 'maven', packages: [{n, v}] }
   */
  function parseMavenCommand(command) {
    const result = {
      ecosystem: 'maven',
      packages: []
    };
  
    if (!command || typeof command !== 'string') {
      return result;
    }
  
    // 1. 尝试匹配 -Dartifact=groupId:artifactId:version[:packaging[:classifier]]
    const artifactMatch = command.match(/-Dartifact=(["']?)([^"'\s]+)\1/);
    if (artifactMatch) {
      const coordsStr = artifactMatch[2].trim();
      const parts = coordsStr.split(':');
  
      if (parts.length >= 2) {
        const groupId = parts[0].trim();
        const artifactId = parts[1].trim();
        const version = parts.length >= 3 ? parts[2].trim() : '';
  
        if (groupId && artifactId) {
          const pkgName = `${groupId}:${artifactId}`;
          if (version && /^\d/.test(version)) {
            result.packages.push({ n: pkgName, v: version });
          } else {
            result.packages.push(makeNameOnly(pkgName));
          }
        }
      }
      return result;
    }
  
    // 2. 尝试匹配 -DgroupId=... -DartifactId=... [-Dversion=...]
    const gMatch = command.match(/-DgroupId=(["']?)([^"'\s]+)\1/);
    const aMatch = command.match(/-DartifactId=(["']?)([^"'\s]+)\1/);
    const vMatch = command.match(/-Dversion=(["']?)([^"'\s]+)\1/);
  
    if (gMatch && aMatch) {
      const groupId = gMatch[2].trim();
      const artifactId = aMatch[2].trim();
      const version = vMatch ? vMatch[2].trim() : '';
  
      if (groupId && artifactId) {
        const pkgName = `${groupId}:${artifactId}`;
        if (version && /^\d/.test(version)) {
          result.packages.push({ n: pkgName, v: version });
        } else {
          result.packages.push(makeNameOnly(pkgName));
        }
      }
      return result;
    }
  
    return result;
  }
  
  __parsers_commands_mvn__.default = parseMavenCommand;
  
  
  // Module exports
  __parsers_commands_mvn__.isMavenCommand = isMavenCommand;
  __parsers_commands_mvn__.parseMavenCommand = parseMavenCommand;
})();


// ============================================================================
// Module: parsers_commands_index
// ============================================================================

(function() {
  /**
   * Command Parser Router
   * 
   * 根据命令自动选择合适的解析器
   */
  
  const parseNpmCommand = __parsers_commands_npm__.parseNpmCommand;
  const isNpmCommand = __parsers_commands_npm__.isNpmCommand;
  const parsePipCommand = __parsers_commands_pip__.parsePipCommand;
  const isPipCommand = __parsers_commands_pip__.isPipCommand;
  const parseGoCommand = __parsers_commands_go__.parseGoCommand;
  const isGoCommand = __parsers_commands_go__.isGoCommand;
  const parseCargoCommand = __parsers_commands_cargo__.parseCargoCommand;
  const isCargoCommand = __parsers_commands_cargo__.isCargoCommand;
  const parseGemCommand = __parsers_commands_gem__.parseGemCommand;
  const isGemCommand = __parsers_commands_gem__.isGemCommand;
  const parseComposerCommand = __parsers_commands_composer__.parseComposerCommand;
  const isComposerCommand = __parsers_commands_composer__.isComposerCommand;
  const parseMavenCommand = __parsers_commands_mvn__.parseMavenCommand;
  const isMavenCommand = __parsers_commands_mvn__.isMavenCommand;
  
  // D4: makeNameOnly 已迁到 ./name-only.js（叶子模块），这里 re-export 保持公共 API 不变。
  // 不要把它搬回本文件 —— 会重新引入 index.js <-> 解析器的循环依赖，见 name-only.js 说明。
  const makeNameOnly = __parsers_commands_name_only__.makeNameOnly;
  
  
  
  /**
   * 检测命令类型
   * 
   * @param {string} command - 命令字符串
   * @returns {string|null} 生态系统类型或 null
   */
  function detectCommandType(command) {
    if (!command) return null;
    
    if (isNpmCommand(command)) {
      return 'npm';
    }
    
    if (isPipCommand(command)) {
      return 'pypi';
    }
    
    if (isGoCommand(command)) {
      return 'go';
    }
    
    if (isCargoCommand(command)) {
      return 'cargo';
    }
    
    if (isGemCommand(command)) {
      return 'rubygems';
    }
    
    if (isComposerCommand(command)) {
      return 'packagist';
    }
  
    if (isMavenCommand(command)) {
      return 'maven';
    }
  
    return null;
  }
  
  /**
   * 解析命令
   * 
   * @param {string} command - 命令字符串
   * @returns {Object|null} { ecosystem, packages: [{n, v}] } 或 null
   */
  function parseCommand(command) {
    const type = detectCommandType(command);
    
    if (!type) {
      return null;
    }
    
    switch (type) {
      case 'npm':
        return parseNpmCommand(command);
        
      case 'pypi':
        return parsePipCommand(command);
        
      case 'go':
        return parseGoCommand(command);
        
      case 'cargo':
        return parseCargoCommand(command);
        
      case 'rubygems':
        return parseGemCommand(command);
        
      case 'packagist':
        return parseComposerCommand(command);
  
      case 'maven':
        return parseMavenCommand(command);
        
      default:
        return null;
    }
  }
  
  __parsers_commands_index__.default = parseCommand;
  
  
  // Module exports
  __parsers_commands_index__.detectCommandType = detectCommandType;
  __parsers_commands_index__.parseCommand = parseCommand;
  __parsers_commands_index__.makeNameOnly = makeNameOnly;
})();


// ============================================================================
// Module: parsers_lockfiles_resolve_installed
// ============================================================================

(function() {
  /**
   * resolve-installed.js — D4-FIX (B 侧): PostToolUse 解析裸包名 install 的真实版本
   * =================================================================================
   *
   * 裸包名 install（如 `pip install flask`）在 PreToolUse 阶段没有版本，client 解析出
   * `{ n, v: '', resolution_state: 'NAME_ONLY' }`。装完后（PostToolUse）才可用对应生态的
   * 探测命令拿到 resolved version，用于二次精确 CVE 审计。
   *
   * 注意：CodeBuddy/Claude Code 的 PostToolUse `tool_response` **没有 stdout 字段**（已在
   * `PENDING_ISSUES.md` §1 用真实会话 + CLI bundle 双验证），所以不能依赖命令输出，必须
   * 在本 hook 内再跑一次探测子进程 / 读 lockfile 兜底。
   *
   * 安全执行（沿用 LocalAuditAdapter 规则，见 `local-audit/adapter.js`）：
   * - 用 execFile + 参数数组，不拼接 shell 字符串。
   * - 固定超时（RESOLVE_TIMEOUT_MS），超时/失败 → 返回 null（fail-open，不阻塞主流程）。
   * - stdout 截断到字节上限，防超大输出占满内存。
   */
  
  const { execFile } = require('child_process');
  
  const RESOLVE_TIMEOUT_MS = 3000;
  const MAX_STDOUT_BYTES = 64 * 1024;
  
  /**
   * 安全执行探测命令，返回截断后的 stdout 字符串；任何失败返回 null。
   * @param {string} cmd
   * @param {string[]} args
   * @returns {Promise<string|null>}
   */
  function safeProbe(cmd, args) {
    return new Promise((resolve) => {
      try {
        execFile(cmd, args, { timeout: RESOLVE_TIMEOUT_MS, maxBuffer: MAX_STDOUT_BYTES }, (err, stdout, stderr) => {
          if (err) {
            // 超时 / 命令不存在 / 非零退出都按"无法解析"处理（fail-open）
            resolve(null);
            return;
          }
          resolve(typeof stdout === 'string' ? stdout : '');
        });
      } catch (e) {
        resolve(null);
      }
    });
  }
  
  /**
   * npm: 从 package-lock.json 解析（已有路径，这里提供统一入口兜底）。
   * @param {string} lockfileContent
   * @param {string} name
   * @returns {string|null}
   */
  function resolveFromNpmLockfile(lockfileContent, name) {
    if (!lockfileContent) return null;
    try {
      const lock = JSON.parse(lockfileContent);
      const pkgs = lock.packages || {};
      // npm v2/v3 lockfile：键为 "node_modules/<name>" 或 "" 根
      const direct = pkgs[`node_modules/${name}`];
      if (direct && direct.version) return direct.version;
      // 旧格式 dependencies 树
      const deps = lock.dependencies || {};
      if (deps[name] && deps[name].version) return deps[name].version;
      return null;
    } catch (e) {
      return null;
    }
  }
  
  /**
   * pip: `pip show <pkg>` → 取 Version: 行
   */
  async function resolvePip(name) {
    const out = await safeProbe(process.execPath === process.execPath ? 'pip' : 'pip', ['show', name]);
    if (!out) {
      // 部分环境用 python -m pip
      const out2 = await safeProbe(process.execPath, ['-m', 'pip', 'show', name]);
      if (!out2) return null;
      return extractPipVersion(out2);
    }
    return extractPipVersion(out);
  }
  
  function extractPipVersion(out) {
    const m = out.match(/^Version:\s*(.+)$/m);
    return m ? m[1].trim() : null;
  }
  
  /**
   * cargo: 读 Cargo.lock 中的 package 版本（name 匹配）
   */
  function resolveCargo(lockfileContent, name) {
    if (!lockfileContent) return null;
    // Cargo.lock TOML：[[package]] name = "x" version = "y"
    const re = /\[\[package\]\][\s\S]*?name\s*=\s*"([^"]+)"[\s\S]*?version\s*=\s*"([^"]+)"/g;
    let m;
    while ((m = re.exec(lockfileContent)) !== null) {
      if (m[1] === name) return m[2];
    }
    return null;
  }
  
  /**
   * gem: `gem list ^<pkg>$` → 取 "name (version)" 第一行
   */
  async function resolveGem(name) {
    const out = await safeProbe('gem', ['list', `^${name}$`]);
    if (!out) return null;
    const m = out.match(/^[^(\s]+\s*\(([^)]+)\)/m);
    return m ? m[1].split(',')[0].trim() : null;
  }
  
  /**
   * go: `go list -m <pkg>` → 输出 "module v1.2.3"
   */
  async function resolveGo(name) {
    const out = await safeProbe('go', ['list', '-m', name]);
    if (!out) return null;
    const m = out.match(/^(\S+)\s+(v?[\d][\w.\-]*)/m);
    return m && m[2] ? m[2] : null;
  }
  
  /**
   * composer: `composer show <pkg>` → 取 versions 第一行，或 `composer show -f json` 更稳定。
   * 这里用 `composer show <pkg> --latest` 的回退：优先简单解析 "versions : * x.y.z"。
   */
  async function resolveComposer(name) {
    const out = await safeProbe('composer', ['show', name]);
    if (!out) return null;
    const m = out.match(/versions\s*:?\s*\*?\s*([\d][\w.\-]*)/i);
    return m ? m[1].trim() : null;
  }
  
  /**
   * 解析裸包名 install 装完后的真实版本（PostToolUse 二次审计用）。
   *
   * @param {string} ecosystem - npm / pypi / cargo / go / rubygems / packagist
   * @param {string} name - 包名
   * @param {Object} [opts] - { lockfileContent } 供读 lockfile 的生态（npm/cargo）使用
   * @returns {Promise<string|null>} resolved version，或 null（fail-open）
   */
  async function resolveInstalledVersion(ecosystem, name, opts = {}) {
    if (!name) return null;
    try {
      switch (ecosystem) {
        case 'npm':
          return resolveFromNpmLockfile(opts.lockfileContent, name);
        case 'pypi':
          return await resolvePip(name);
        case 'cargo':
          return resolveCargo(opts.lockfileContent, name);
        case 'rubygems':
          return await resolveGem(name);
        case 'go':
          return await resolveGo(name);
        case 'packagist':
          return await resolveComposer(name);
        default:
          return null;
      }
    } catch (e) {
      return null;
    }
  }
  
  __parsers_lockfiles_resolve_installed__.default = resolveInstalledVersion;
  
  
  // Module exports
  __parsers_lockfiles_resolve_installed__.resolveInstalledVersion = resolveInstalledVersion;
})();


// ============================================================================
// Module: parsers_repl
// ============================================================================

(function() {
  /**
   * REPL Script Parser for PTC (Program-The-Conversation) Agent Mode
   *
   * Extracts tool calls executed inside REPL code snippets, such as:
   * - await Write({ path: '...', content: '...' })
   * - await Edit({ path: '...', old_string: '...', new_string: '...' })
   * - await Bash({ command: '...' })
   */
  
  /**
   * Unescape basic JavaScript string escape sequences
   * @param {string} str
   * @returns {string}
   */
  function unescapeJsString(str) {
    if (!str) return str;
    return str.replace(/\\([nrt\\'"\`])/g, (_, c) => {
      if (c === 'n') return '\n';
      if (c === 'r') return '\r';
      if (c === 't') return '\t';
      return c;
    });
  }
  
  /**
   * Extract simple string variable assignments in code:
   * const varName = "value";
   * let varName = 'value';
   * var varName = `value`;
   * 
   * @param {string} code
   * @returns {Map<string, string>}
   */
  function extractStringVariables(code) {
    const vars = new Map();
    if (!code || typeof code !== 'string') return vars;
  
    const varRegex = /(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:(["'])([\s\S]*?[^\\]|)\2|`([\s\S]*?[^\\]|)`)/g;
    for (const match of code.matchAll(varRegex)) {
      const name = match[1];
      const val = match[3] !== undefined ? match[3] : match[4];
      vars.set(name, unescapeJsString(val));
    }
    return vars;
  }
  
  /**
   * Extracts a property string value from an object literal string,
   * supporting string literals, variables, and ES6 shorthand.
   * 
   * @param {string} objStr
   * @param {string[]} propKeys
   * @param {Map<string, string>} vars
   * @returns {string|null}
   */
  function extractPropValue(objStr, propKeys, vars = new Map()) {
    for (const k of propKeys) {
      // 1. Literal string: { key: "val" } or { 'key': 'val' } or { key: `val` }
      const literalRe = new RegExp(`(?:["']?${k}["']?\\s*:\\s*)(?:(["'])([\\s\\S]*?[^\\\\]|)\\1|\`([\\s\\S]*?[^\\\\]|)\`)`, 's');
      const lm = objStr.match(literalRe);
      if (lm) {
        const raw = lm[2] !== undefined ? lm[2] : lm[3];
        return unescapeJsString(raw);
      }
  
      // 2. Variable identifier: { key: myVar }
      const identRe = new RegExp(`(?:["']?${k}["']?\\s*:\\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)`);
      const im = objStr.match(identRe);
      if (im && vars && vars.has(im[1])) {
        return vars.get(im[1]);
      }
    }
  
    // 3. ES6 Shorthand: { path, content }
    const shorthandRe = new RegExp(`(?:^|[,{])\\s*(${propKeys.join('|')})\\s*(?:$|[,}])`);
    const sm = objStr.match(shorthandRe);
    if (sm && vars && vars.has(sm[1])) {
      return vars.get(sm[1]);
    }
  
    return null;
  }
  
  /**
   * Extracts function call arguments with balanced parentheses.
   * 
   * @param {string} code
   * @param {string[]} fnNames
   * @returns {Array<{fnName: string, argsStr: string}>}
   */
  function extractFunctionCalls(code, fnNames) {
    const pattern = new RegExp(`\\b(${fnNames.join('|')})\\s*\\(`, 'g');
    const calls = [];
    let match;
    while ((match = pattern.exec(code)) !== null) {
      const fnName = match[1];
      let depth = 1;
      let idx = match.index + match[0].length;
      const start = idx;
      while (idx < code.length && depth > 0) {
        const char = code[idx];
        if (char === '(') depth++;
        else if (char === ')') depth--;
        idx++;
      }
      if (depth === 0) {
        const argsStr = code.slice(start, idx - 1).trim();
        calls.push({ fnName, argsStr });
      }
    }
    return calls;
  }
  
  /**
   * Parse a REPL script and extract dependency operations.
   *
   * @param {string} code - The JavaScript code passed to REPL
   * @returns {Array<{type: 'Write'|'Edit'|'Bash', filePath?: string, content?: string, oldString?: string, newString?: string, command?: string}>}
   */
  function parseReplOperations(code) {
    if (!code || typeof code !== 'string') return [];
  
    const vars = extractStringVariables(code);
    const calls = extractFunctionCalls(code, [
      'Write', 'write_to_file',
      'Edit', 'replace_in_file',
      'Bash', 'execute_command'
    ]);
  
    const operations = [];
  
    for (const { fnName, argsStr } of calls) {
      if (fnName === 'Write' || fnName === 'write_to_file') {
        const filePath = extractPropValue(argsStr, ['file_path', 'filePath', 'path'], vars);
        const content = extractPropValue(argsStr, ['content'], vars);
        if (filePath) {
          operations.push({
            type: 'Write',
            filePath,
            content: content || ''
          });
        }
      } else if (fnName === 'Edit' || fnName === 'replace_in_file') {
        const filePath = extractPropValue(argsStr, ['file_path', 'filePath', 'path'], vars);
        const oldString = extractPropValue(argsStr, ['old_string', 'oldString'], vars);
        const newString = extractPropValue(argsStr, ['new_string', 'newString'], vars);
        if (filePath) {
          operations.push({
            type: 'Edit',
            filePath,
            oldString: oldString || '',
            newString: newString || ''
          });
        }
      } else if (fnName === 'Bash' || fnName === 'execute_command') {
        let command = extractPropValue(argsStr, ['command'], vars);
        if (!command) {
          const directStringMatch = argsStr.match(/^(?:(["'])([\s\S]*?[^\\]|)\1|`([\s\S]*?[^\\]|)`)$/s);
          if (directStringMatch) {
            command = unescapeJsString(directStringMatch[2] !== undefined ? directStringMatch[2] : directStringMatch[3]);
          }
        }
        if (command) {
          operations.push({
            type: 'Bash',
            command
          });
        }
      }
    }
  
    return operations;
  }
  
  
  // Module exports
  __parsers_repl__.unescapeJsString = unescapeJsString;
  __parsers_repl__.extractStringVariables = extractStringVariables;
  __parsers_repl__.extractPropValue = extractPropValue;
  __parsers_repl__.extractFunctionCalls = extractFunctionCalls;
  __parsers_repl__.parseReplOperations = parseReplOperations;
})();


// ============================================================================
// Module: parsers_input
// ============================================================================

(function() {
  /**
   * Hook Input Parser
   * 
   * 解析 CodeBuddy Hook 传入的 JSON 输入
   */
  
  /**
   * IDE (Craft Agent) 工具名 → CLI 工具名映射
   * 
   * IDE 和 CLI 使用不同的工具名称，统一规范化为 CLI 名称
   */
  const IDE_TOOL_NAME_MAP = {
    'execute_command': 'Bash',
    'write_to_file':   'Write',
    'replace_in_file': 'Edit',
    'read_file':       'Read',
    'search_file':     'Glob',
    'search_content':  'Grep',
    'list_dir':        'LS',
    'web_fetch':       'WebFetch',
    'web_search':      'WebSearch',
    'task':            'Task',
    'Code':            'REPL',
  };
  
  /**
   * 规范化工具名：将 IDE 工具名映射为 CLI 工具名
   * 
   * @param {string} toolName - 原始工具名
   * @returns {string} 规范化后的工具名
   */
  function normalizeToolName(toolName) {
    return IDE_TOOL_NAME_MAP[toolName] ?? toolName;
  }
  
  /**
   * 判断客户端是否为 IDE 环境（VSCode / CodeBuddyIDE / JetBrains 等）
   * 
   * @param {string|undefined} client - 客户端标识
   * @param {string|undefined} [toolName] - 原始工具名（可选）
   * @returns {boolean}
   */
  function isIdeClient(client, toolName = null) {
    if (typeof client === 'string') {
      const c = client.toLowerCase();
      if (c === 'codebuddyide' || c === 'vscode' || c === 'jetbrains' || c === 'ide' || c === 'vim' || c === 'xcode') {
        return true;
      }
    }
    if (typeof toolName === 'string') {
      if (['write_to_file', 'replace_in_file', 'execute_command', 'read_file', 'list_dir', 'search_file', 'search_content'].includes(toolName)) {
        return true;
      }
    }
    return false;
  }
  
  /**
   * 获取规范化客户端类型（IDE / CLI）
   * 
   * @param {string|undefined} client
   * @param {string|undefined} [toolName]
   * @returns {'IDE'|'CLI'}
   */
  function getClientType(client, toolName = null) {
    return isIdeClient(client, toolName) ? 'IDE' : 'CLI';
  }
  
  /**
   * 规范化工具输入参数键名：将 IDE camelCase 参数名映射为 CLI snake_case 参数名
   * 
   * IDE 环境传入 filePath（camelCase），CLI 环境传入 file_path（snake_case）
   * 统一规范化为 snake_case，保证后续逻辑只需处理一种格式
   * 
   * @param {Object} toolInput - 原始工具输入
   * @returns {Object} 规范化后的工具输入
   */
  function normalizeToolInput(toolInput) {
    if (!toolInput || typeof toolInput !== 'object') return toolInput;
  
    const normalized = { ...toolInput };
  
    // filePath / path → file_path
    if (normalized.filePath !== undefined && normalized.file_path === undefined) {
      normalized.file_path = normalized.filePath;
    }
    if (normalized.path !== undefined && normalized.file_path === undefined) {
      normalized.file_path = normalized.path;
    }
  
    // oldString / search → old_string
    if (normalized.oldString !== undefined && normalized.old_string === undefined) {
      normalized.old_string = normalized.oldString;
    }
    if (normalized.search !== undefined && normalized.old_string === undefined) {
      normalized.old_string = normalized.search;
    }
  
    // newString / replace → new_string
    if (normalized.newString !== undefined && normalized.new_string === undefined) {
      normalized.new_string = normalized.newString;
    }
    if (normalized.replace !== undefined && normalized.new_string === undefined) {
      normalized.new_string = normalized.replace;
    }
  
    // script / input → code (for REPL)
    if (normalized.script !== undefined && normalized.code === undefined) {
      normalized.code = normalized.script;
    }
  
    return normalized;
  }
  
  /**
   * 解析 Hook 输入 JSON
   * 
   * @param {string} rawInput - 原始 JSON 字符串
   * @returns {Object|null} 解析后的输入对象，无效输入返回 null
   */
  function parseInput(rawInput) {
    if (!rawInput || typeof rawInput !== 'string') {
      return null;
    }
    
    try {
      const input = JSON.parse(rawInput);
      
      // 验证必要字段
      if (!input.tool_name || !input.tool_input) {
        return null;
      }
      
      return {
        toolName: normalizeToolName(input.tool_name),
        toolInput: normalizeToolInput(input.tool_input),
        // 保留原始输入用于后续处理
        raw: input
      };
      
    } catch (error) {
      // JSON 解析失败
      return null;
    }
  }
  
  /**
   * 容错行匹配与替换辅助函数
   * 
   * 处理 CRLF vs LF 差异以及行尾空白（trailing spaces/tabs）差异
   */
  function tolerantMatchAndReplace(originalContent, oldString, newString, replaceAll = false) {
    const origHasCrlf = originalContent.includes('\r\n');
    
    // 规范化两端的换行符为 \n 进行比对
    const origNormLf = originalContent.replace(/\r\n/g, '\n');
    const oldNormLf = oldString.replace(/\r\n/g, '\n');
    const newNormLf = (newString || '').replace(/\r\n/g, '\n');
    
    // 1. 换行符统一后直接包含
    if (origNormLf.includes(oldNormLf)) {
      const replaced = replaceAll
        ? origNormLf.split(oldNormLf).join(newNormLf)
        : origNormLf.replace(oldNormLf, newNormLf);
      return origHasCrlf ? replaced.replace(/\n/g, '\r\n') : replaced;
    }
  
    // 2. 逐行去除行尾空白后的多行容错匹配
    const origLines = origNormLf.split('\n');
    const oldLines = oldNormLf.split('\n');
    const newLines = newNormLf.split('\n');
  
    if (oldLines.length === 0 || (oldLines.length === 1 && !oldLines[0].trim())) {
      return originalContent;
    }
  
    const matchedIndices = [];
    const k = oldLines.length;
  
    for (let i = 0; i <= origLines.length - k; i++) {
      let match = true;
      for (let j = 0; j < k; j++) {
        if (origLines[i + j].trimEnd() !== oldLines[j].trimEnd()) {
          match = false;
          break;
        }
      }
      if (match) {
        matchedIndices.push(i);
        if (!replaceAll) break;
        i += (k - 1);
      }
    }
  
    if (matchedIndices.length === 0) {
      return originalContent;
    }
  
    // 执行行级替换（从后往前替换以保持前面的行索引有效）
    const resultLines = [...origLines];
    for (let idx = matchedIndices.length - 1; idx >= 0; idx--) {
      const startIdx = matchedIndices[idx];
      resultLines.splice(startIdx, k, ...newLines);
    }
  
    const resultNorm = resultLines.join('\n');
    return origHasCrlf ? resultNorm.replace(/\n/g, '\r\n') : resultNorm;
  }
  
  /**
   * 从 Edit 工具输入计算最终文件内容
   * 
   * P1-1 改进：添加换行符与空白容错匹配
   * - 第一层：原内容严格包含 old_string，直接替换
   * - 第二层：针对 CRLF vs LF 或行尾多余空格等情况做容错行级替换
   * - 若完全不匹配，返回原内容（与 Claude Edit 工具行为一致）
   * 
   * @param {string} originalContent - 原始文件内容
   * @param {string} oldString - 要替换的字符串
   * @param {string} newString - 替换后的字符串
   * @param {boolean} replaceAll - 是否替换所有匹配
   * @returns {string} 计算后的最终内容
   */
  function computeEditResult(originalContent, oldString, newString, replaceAll = false) {
    // 如果原内容为空，直接返回 newString（创建新文件场景）
    if (!originalContent) {
      return newString || '';
    }
    
    // 如果 oldString 为空，返回 newString 或原内容
    if (!oldString) {
      return newString || originalContent;
    }
    
    // 第一层：精确匹配
    if (originalContent.includes(oldString)) {
      if (replaceAll) {
        return originalContent.split(oldString).join(newString);
      }
      return originalContent.replace(oldString, newString);
    }
    
    // 第二层：容错替换
    return tolerantMatchAndReplace(originalContent, oldString, newString, replaceAll);
  }
  
  /**
   * 校验 Edit 操作是否可以成功执行
   * 
   * @param {string} originalContent - 原始文件内容
   * @param {string} oldString - 要替换的字符串
   * @returns {boolean} 是否可以执行
   */
  function validateEditOperation(originalContent, oldString) {
    // 创建新文件场景
    if (!originalContent && !oldString) {
      return true;
    }
    
    // 无 old_string，视为追加操作
    if (!oldString) {
      return true;
    }
    
    if (!originalContent) {
      return false;
    }
    
    // 第一层：精确匹配
    if (originalContent.includes(oldString)) {
      return true;
    }
    
    // 第二层：换行符与去除行尾空白后的容错检查
    const origNormLf = originalContent.replace(/\r\n/g, '\n');
    const oldNormLf = oldString.replace(/\r\n/g, '\n');
    if (origNormLf.includes(oldNormLf)) {
      return true;
    }
  
    const origLines = origNormLf.split('\n');
    const oldLines = oldNormLf.split('\n');
    const k = oldLines.length;
  
    for (let i = 0; i <= origLines.length - k; i++) {
      let match = true;
      for (let j = 0; j < k; j++) {
        if (origLines[i + j].trimEnd() !== oldLines[j].trimEnd()) {
          match = false;
          break;
        }
      }
      if (match) return true;
    }
  
    return false;
  }
  
  /**
   * 从 MultiEdit 工具输入计算最终文件内容
   * 
   * @param {string} originalContent - 原始文件内容
   * @param {Array} edits - 编辑操作数组 [{old_string, new_string, replace_all}]
   * @returns {string} 计算后的最终内容
   */
  function computeMultiEditResult(originalContent, edits) {
    if (!edits || !Array.isArray(edits)) {
      return originalContent;
    }
    
    let content = originalContent || '';
    
    for (const edit of edits) {
      content = computeEditResult(
        content,
        edit.old_string,
        edit.new_string,
        edit.replace_all
      );
    }
    
    return content;
  }
  
  /**
   * 提取工具输入中的文件内容
   * 
   * 根据不同工具类型提取最终的文件内容:
   * - Write: 直接使用 content
   * - Edit: 需要读取原文件并应用修改 (这里简化处理，使用 new_string)
   * - MultiEdit: 需要读取原文件并应用所有修改
   * 
   * @param {string} toolName - 工具名称
   * @param {Object} toolInput - 工具输入
   * @param {string|undefined} diskContent - 磁盘上的原文件内容 (undefined 表示未传入)
   * @returns {string} 文件内容
   */
  function extractFileContent(toolName, toolInput, diskContent) {
    // 判断是否显式传入了 diskContent 参数
    // 注意：空字符串 '' 是有效的磁盘内容（表示文件存在但为空）
    const hasDiskContent = diskContent !== undefined;
    // 规范化工具名，兼容 IDE 工具名
    const normalizedName = normalizeToolName(toolName);
    
    switch (normalizedName) {
      case 'Write':
        return toolInput.content || '';
        
      case 'Edit':
        // 如果显式传入了磁盘内容（包括空字符串），计算编辑结果
        if (hasDiskContent) {
          return computeEditResult(
            diskContent,
            toolInput.old_string,
            toolInput.new_string,
            toolInput.replace_all
          );
        }
        // 未传入磁盘内容，回退到 new_string
        return toolInput.new_string || '';
        
      case 'MultiEdit':
        // 如果显式传入了磁盘内容（包括空字符串），计算编辑结果
        if (hasDiskContent && toolInput.edits) {
          return computeMultiEditResult(diskContent, toolInput.edits);
        }
        // 如果没有磁盘内容，尝试从最后一个 edit 获取
        if (toolInput.edits && toolInput.edits.length > 0) {
          return toolInput.edits[toolInput.edits.length - 1].new_string || '';
        }
        return '';
        
      default:
        return '';
    }
  }
  
  
  // Module exports
  __parsers_input__.normalizeToolName = normalizeToolName;
  __parsers_input__.isIdeClient = isIdeClient;
  __parsers_input__.getClientType = getClientType;
  __parsers_input__.normalizeToolInput = normalizeToolInput;
  __parsers_input__.parseInput = parseInput;
  __parsers_input__.computeEditResult = computeEditResult;
  __parsers_input__.validateEditOperation = validateEditOperation;
  __parsers_input__.computeMultiEditResult = computeMultiEditResult;
  __parsers_input__.extractFileContent = extractFileContent;
})();


// ============================================================================
// Module: auth_token_manager
// ============================================================================

(function() {
  /**
   * JWT Token 管理器
   *
   * 职责:
   * - 存储和读取 JWT Token
   * - 检查 Token 是否即将过期（提前5分钟视为过期）
   * - 从 JWT payload 解析过期时间
   */
  
  class TokenManager {
    constructor() {
      this._token = null;
      this._expiresAt = null; // ms 时间戳
    }
  
    /**
     * 从 JWT token 字符串解析过期时间
     * @param {string} token
     * @returns {number|null} 过期时间戳 (ms)，解析失败返回 null
     */
    _parseExpiry(token) {
      try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        // base64url decode payload
        const payload = JSON.parse(
          Buffer.from(parts[1], 'base64url').toString('utf8')
        );
        return payload.exp ? payload.exp * 1000 : null;
      } catch {
        return null;
      }
    }
  
    /**
     * 设置 Token
     * @param {string} token JWT Token 字符串
     */
    setToken(token) {
      if (!token || typeof token !== 'string') return;
      this._token = token;
      this._expiresAt = this._parseExpiry(token);
    }
  
    /**
     * 获取有效 Token（已过期或即将过期返回 null）
     * @returns {string|null}
     */
    getToken() {
      if (!this._token) return null;
      // 提前 5 分钟视为过期
      if (this._expiresAt && Date.now() > this._expiresAt - 5 * 60 * 1000) {
        return null;
      }
      return this._token;
    }
  
    /**
     * 从环境变量加载 Token
     * @returns {string|null}
     */
    loadFromEnv() {
      const token = process.env.CODEBUDDY_SECURITY_JWT_TOKEN || null;
      if (token) this.setToken(token);
      return this.getToken();
    }
  
    /**
     * 检查 Token 是否有效
     */
    isValid() {
      return this.getToken() !== null;
    }
  
    /**
     * 清除 Token
     */
    clear() {
      this._token = null;
      this._expiresAt = null;
    }
  }
  
  // 单例
  const tokenManager = new TokenManager();
  
  
  // Module exports
  __auth_token_manager__.tokenManager = tokenManager;
  __auth_token_manager__.TokenManager = TokenManager;
})();


// ============================================================================
// Module: auth_session_reader
// ============================================================================

(function() {
  /**
   * CodeBuddy Session Reader
   *
   * 从 CodeBuddy 本地 auth 文件读取当前登录 session，
   * 提供 accessToken / refreshToken / domain / userId / enterpriseId 等字段，
   * 用于在 hook client 发起请求时携带与 codebuddy 主程序完全一致的身份头部。
   *
   * 逆向来源：
   *   codebuddy-code/dist/codebuddy.js
   *     - FileAuthenticationStorage.getAuthSavePath()   → auth 文件路径
   *     - enterpriseHeaders(auth)                        → X-Domain
   *     - OpenTelemetrySpan.requestHeaders               → X-Request-ID / b3 / X-B3-*
   *     - AuthenticationHttpInterceptor (axios 拦截器)   → Authorization / X-User-Id 等
   *   codebuddy-code/product.json
   *     - authentication.id                              → auth 文件名
   *     - authentication.attributes.prefixPath           → URL 前缀
   *     - endpoint                                       → 服务端地址
   */
  
  const { readFileSync, existsSync } = require('fs');
  const { join } = require('path');
  const { homedir, platform } = require('os');
  const UI = __ui__.UI;
  
  // ── auth 文件路径解析 ──────────────────────────────────────────────────────────
  
  /**
   * 定位 product.json（在 codebuddy-code 安装目录下）。
   * 运行时路径：security-guard-js/src/auth/session_reader.js
   * → 上溯 4 级到工作区根，再进入 codebuddy-code/product.json
   *
   * 若找不到，则回退到内置默认值。
   */
  function loadProductConfig() {
    const defaults = {
      authId:   'Tencent-Cloud.coding-copilot',
      endpoint: 'https://www.codebuddy.ai',
      prefix:   '/plugin',
    };
  
    // 常见安装位置：与 security-guard-js 同级的 codebuddy-code 目录
    // 用运行时入口文件路径（process.argv[1]）推算工作区根，兼容 ESM / CJS bundle
    const entryFile = process.argv[1] || '';
  
    const candidates = [
      // bundle 部署模式：dist/hook.cjs → ../../ → security-guard-js → ../codebuddy-code
      join(entryFile, '..', '..', 'codebuddy-code', 'product.json'),
      // workspace 源码模式：security-guard-js/src/auth/ 上溯4级
      join(entryFile, '..', '..', '..', '..', 'codebuddy-code', 'product.json'),
      // npm global install / cbc 二进制
      join(homedir(), '.codebuddy', 'product.json'),
    ];
  
    for (const candidate of candidates) {
      try {
        if (existsSync(candidate)) {
          const prod = JSON.parse(readFileSync(candidate, 'utf8'));
          return {
            authId:   prod?.authentication?.id   ?? defaults.authId,
            endpoint: prod?.endpoint             ?? defaults.endpoint,
            prefix:   prod?.authentication?.attributes?.prefixPath ?? defaults.prefix,
          };
        }
      } catch {
        // 静默跳过
      }
    }
  
    return defaults;
  }
  
  /**
   * 返回 auth 文件的完整路径。
   * macOS:   ~/Library/Application Support/CodeBuddyExtension/Data/Public/auth/{id}.info
   * Linux:   ~/.local/share/CodeBuddyExtension/Data/Public/auth/{id}.info
   * Windows: %APPDATA%\CodeBuddyExtension\Data\Public\auth\{id}.info
   */
  function getAuthFilePath(authId) {
    const os = platform();
    let base;
    if (os === 'darwin') {
      base = join(homedir(), 'Library', 'Application Support',
        'CodeBuddyExtension', 'Data', 'Public');
    } else if (os === 'win32') {
      base = join(process.env.APPDATA || homedir(),
        'CodeBuddyExtension', 'Data', 'Public');
    } else {
      base = join(homedir(), '.local', 'share',
        'CodeBuddyExtension', 'Data', 'Public');
    }
    return join(base, 'auth', `${authId}.info`);
  }
  
  // ── trace header 生成（还原 OpenTelemetrySpan.requestHeaders）───────────────
  
  /**
   * 生成符合 OpenTelemetry B3 格式的 trace 请求头。
   *
   * 原始实现：
   *   get requestHeaders() {
   *     const { traceId, spanId, traceFlags } = this.span.spanContext();
   *     return {
   *       [REQUEST_ID_HEADER]: traceId,
   *       b3: `${traceId}-${spanId}-${traceFlags}-${parentSpanId}`,
   *       "X-B3-TraceId": traceId, ...
   *     };
   *   }
   *
   * Node.js 18+ 内置 crypto.randomUUID()，格式与 OTel traceId 等价（去掉连字符）。
   */
  function generateTraceHeaders() {
    // crypto 在 Node.js 18+ 为全局对象，无需 require
    const traceId    = crypto.randomUUID().replace(/-/g, '');  // 32 hex chars
    const spanId     = crypto.randomUUID().replace(/-/g, '').slice(0, 16); // 16 hex chars
    const traceFlags = '1'; // sampled
  
    return {
      'X-Request-ID':      traceId,
      'b3':                `${traceId}-${spanId}-${traceFlags}-`,
      'X-B3-TraceId':      traceId,
      'X-B3-SpanId':       spanId,
      'X-B3-ParentSpanId': '',
      'X-B3-Sampled':      traceFlags,
    };
  }
  
  // ── Session 读取 ───────────────────────────────────────────────────────────────
  
  /**
   * 读取本地 codebuddy auth 文件，返回 session 对象。
   * 失败时静默返回 null（fail-open）。
   *
   * @returns {{ auth: object, account: object } | null}
   */
  function readSession() {
    try {
      const { authId } = loadProductConfig();
      const filePath = getAuthFilePath(authId);
  
      if (!existsSync(filePath)) {
        UI.log(`[SESSION] auth file not found: ${filePath}`);
        return null;
      }
  
      const raw = readFileSync(filePath, 'utf8');
      const session = JSON.parse(raw);
  
      if (!session?.auth?.accessToken) {
        UI.log('[SESSION] auth file missing accessToken');
        return null;
      }
  
      UI.log(`[SESSION] loaded session for uid=${session.account?.uid}`);
      return session;
    } catch (err) {
      UI.log(`[SESSION] readSession error: ${err.message}`);
      return null;
    }
  }
  
  // ── 对外接口 ──────────────────────────────────────────────────────────────────
  
  /**
   * 构建发往 MCP Security Server 的完整身份请求头。
   *
   * 还原逻辑（按 JS 源码层次）：
   *
   *   Layer 1 – enterpriseHeaders(auth)：
   *     X-Domain = auth.domain（服务路由标识）
   *
   *   Layer 2 – axios 全局 AuthenticationHttpInterceptor：
   *     Authorization      = Bearer {accessToken}
   *     X-Refresh-Token    = auth.refreshToken（若存在）
   *     X-User-Id          = account.uid
   *     X-Enterprise-Id    = account.enterpriseId
   *     X-Tenant-Id        = account.enterpriseId
   *     X-Department-Info  = account.departmentFullName（若存在）
   *
   *   Layer 3 – OpenTelemetrySpan.requestHeaders：
   *     X-Request-ID / b3 / X-B3-*（每次请求随机生成）
   *
   * @returns {object} 请求头键值对，可直接 spread 进 fetch headers
   */
  function buildSessionHeaders() {
    const session = readSession();
    const headers = {};
  
    if (!session) {
      // 未登录或文件不可读，注入 trace headers；尝试从环境变量提取用户信息
      UI.log('[SESSION] no session, checking env for auth headers');
      const headers = generateTraceHeaders();
      const envUser = process.env.CODEBUDDY_USER_NAME || process.env.CODEBUDDY_RTX || process.env.USER || process.env.LOGNAME;
      if (envUser) {
        headers['X-User-Name'] = envUser;
        headers['X-RTX-Name']  = envUser;
      }
      return headers;
    }
  
    const { auth, account } = session;
  
    // Layer 1: X-Domain（来自 enterpriseHeaders(auth)）
    if (auth.domain) {
      headers['X-Domain'] = auth.domain;
    }
  
    // Layer 2: 身份认证（来自 axios Auth Interceptor）
    if (auth.accessToken) {
      headers['Authorization'] = `Bearer ${auth.accessToken}`;
    }
    if (auth.refreshToken) {
      headers['X-Refresh-Token'] = auth.refreshToken;
    }
    if (account?.uid) {
      headers['X-User-Id'] = account.uid;
    }
    const rtxName = account?.enterpriseUserName || account?.nickname || process.env.CODEBUDDY_USER_NAME || process.env.CODEBUDDY_RTX || process.env.USER || process.env.LOGNAME;
    if (rtxName) {
      headers['X-User-Name'] = String(rtxName);
      headers['X-RTX-Name']  = String(rtxName);
    }
    if (account?.displayName) {
      try {
        headers['X-User-Display-Name'] = encodeURIComponent(account.displayName);
      } catch {
        // ignore
      }
    }
    if (account?.enterpriseId) {
      headers['X-Enterprise-Id'] = account.enterpriseId;
      headers['X-Tenant-Id']     = account.enterpriseId;
    }
    if (account?.departmentFullName) {
      headers['X-Department-Info'] = account.departmentFullName;
    }
  
    // Layer 3: trace 上下文（每次调用随机生成）
    Object.assign(headers, generateTraceHeaders());
  
    UI.log(`[SESSION] built headers: uid=${account?.uid} rtx=${rtxName} enterprise=${account?.enterpriseId} domain=${auth.domain} hasRefreshToken=${!!auth.refreshToken}`);
    return headers;
  }
  
  /**
   * 仅返回 trace 相关 headers（不携带身份信息，用于匿名请求）。
   */
  function buildTraceHeaders() {
    return generateTraceHeaders();
  }
  
  /**
   * 返回当前登录用户的 uid，供 resolveUserId 直接使用。
   * 找不到时返回空字符串。
   *
   * @returns {string}
   */
  function getSessionUserId() {
    const session = readSession();
    return session?.account?.uid ?? '';
  }
  
  
  // Module exports
  __auth_session_reader__.buildSessionHeaders = buildSessionHeaders;
  __auth_session_reader__.buildTraceHeaders = buildTraceHeaders;
  __auth_session_reader__.getSessionUserId = getSessionUserId;
})();


// ============================================================================
// Module: tls
// ============================================================================

(function() {
  /**
   * TLS 配置 — 共享模块
   *
   * 供 client.js（主流程）和 telemetry.js（埋点上送）复用，
   * 确保所有出站 HTTPS 请求使用一致的证书信任策略。
   *
   * 环境变量优先级（高 → 低）：
   *   1. CODEBUDDY_SECURITY_CA_CERT=/path/to/ca.crt  — 自签名证书信任（推荐）
   *   2. CODEBUDDY_SECURITY_TLS_REJECT_UNAUTHORIZED=false — 完全跳过验证
   *   3. NODE_TLS_REJECT_UNAUTHORIZED=0               — 标准 Node.js 跳过验证
   *   4. 内嵌 mcp-security.crt（与 bundle 同目录，自动加载）
   *   5. 默认：系统 CA 信任链（严格验证）
   */
  
  const { readFileSync, existsSync } = require('fs');
  const { join } = require('path');
  const UI = __ui__.UI;
  
  // 内嵌证书路径（CJS bundle 后 __dirname 指向 dist/ 目录，与 mcp-security.crt 同级）
  // 兼容性保护：在原生 ESM 下运行时 __dirname 为 undefined，避免 ReferenceError
  let EMBEDDED_CERT_PATH = '';
  try {
    if (typeof __dirname !== 'undefined') {
      EMBEDDED_CERT_PATH = join(__dirname, 'mcp-security.crt');
    }
  } catch {
    // ESM 环境下安全忽略
  }
  
  /**
   * 构建 TLS 选项（用于 node:https.request）
   *
   * @returns {Object} 可直接展开到 https.request options 的 TLS 字段
   */
  function buildTlsOptions() {
    const debug = process.env.CODEBUDDY_DEBUG === '1';
    if (debug) {
      UI.log(
        `[CLIENT] TLS config: CA_CERT=${process.env.CODEBUDDY_SECURITY_CA_CERT ? '(set)' : '(not set)'} ` +
        `TLS_REJECT_UNAUTHORIZED=${process.env.CODEBUDDY_SECURITY_TLS_REJECT_UNAUTHORIZED ?? '(not set)'} ` +
        `NODE_TLS_REJECT_UNAUTHORIZED=${process.env.NODE_TLS_REJECT_UNAUTHORIZED ?? '(not set)'}`
      );
    }
  
    // 1. 自定义 CA 证书
    const caCertPath = process.env.CODEBUDDY_SECURITY_CA_CERT;
    if (caCertPath) {
      try {
        const ca = readFileSync(caCertPath);
        return { ca, rejectUnauthorized: true };
      } catch (err) {
        UI.log(`[CLIENT] Warning: failed to read CA cert from ${caCertPath}: ${err.message}`);
      }
    }
  
    // 2. 显式跳过验证
    if (process.env.CODEBUDDY_SECURITY_TLS_REJECT_UNAUTHORIZED === 'false') {
      return { rejectUnauthorized: false };
    }
  
    // 3. 标准 Node.js 跳过验证
    if (process.env.NODE_TLS_REJECT_UNAUTHORIZED === '0') {
      return { rejectUnauthorized: false };
    }
  
    // 4. 内嵌证书（与 bundle 同目录的 mcp-security.crt）
    if (existsSync(EMBEDDED_CERT_PATH)) {
      try {
        const ca = readFileSync(EMBEDDED_CERT_PATH);
        if (debug) {
          UI.log(`[CLIENT] TLS: using embedded cert at ${EMBEDDED_CERT_PATH}`);
        }
        return { ca, rejectUnauthorized: true };
      } catch (err) {
        UI.log(`[CLIENT] Warning: failed to read embedded cert: ${err.message}`);
      }
    }
  
    // 5. 默认：系统 CA 信任链
    return {};
  }
  
  
  // Module exports
  __tls__.buildTlsOptions = buildTlsOptions;
})();


// ============================================================================
// Module: repo
// ============================================================================

(function() {
  /**
   * Repo Detection Module (Simplified Strategy)
   * 
   * 参考 Security-Scan 插件策略：
   * - repo_name: 仅提取项目名（URL 最后一段），不含组织信息（向后兼容旧字段）
   * - repo_branch: 明文上报分支名
   * - remote_url: 永不上报
   * 
   * 核心原则：
   * - 数据最小化：只上报项目名，避免组织结构泄露
   * - Fail-open：任何检测失败都不影响主流程
   * - 隐私优先：无需 hash，天然隐私友好
   *
   * ── D1-28 归因修复 ──────────────────────────────────────────────────
   * 仅用 `repo_name`（URL 最后一段/ basename）做归因存在真实碰撞问题：
   * `github.com/org-a/backend` 与 `gitlab.company.com/org-b/backend`
   * 会被合并成同一个 "backend"，导致接入率/活跃仓库统计失真。
   * Server 侧（telemetry_collector.py）已经支持 repo_id（sha256）、
   * repo_namespace（完整 org/repo 路径）、repo_remote_host 三个更精确的
   * 字段，且对旧 repo_name 做了兼容 fallback——只是 Client 一直没有填充
   * 这三个新字段。本次补上 Client 侧计算逻辑，不改变现有 repo_name 语义
   * （继续只暴露 basename，保持向后兼容），新增字段用于 Server 端更精确
   * 的归因去重，且不引入未受控的 HMAC key 基础设施（feed_update/28 文档
   * 建议的企业级 HMAC key 版本化管理，属于需要基础设施投入的产品决策，
   * 这里先用无密钥 SHA-256 降低碰撞率——在字典猜测防护上比 basename 弱，
   * 但已经远比当前"完全不做区分"更准确，属于低风险的渐进式改进）。
   */
  
  const { execFileSync } = require('child_process');
  const { createHash, createHmac } = require('crypto');
  
  // 进程内缓存，避免重复检测
  const cache = new Map();
  const CACHE_TTL_MS = 30000; // 30 秒
  
  /**
   * 从 git remote URL 提取项目名（最后一段）
   * 
   * 示例：
   * - git@github.com:org/project.git -> "project"
   * - https://github.com/org/project.git -> "project"
   * - ssh://git@gitlab.com/org/sub/project.git -> "project"
   * 
   * @param {string} remoteUrl - 原始 remote URL
   * @returns {string} 项目名（仅最后一段）
   */
  /**
   * 从 remote URL 中剥离一切凭证与敏感片段，仅保留 host + 路径（全路径 namespace）。
   *
   * 处理项：
   * - scheme://user:token@host   -> 删除 user:token@
   * - git@host:path (scp-like)   -> 保留（无凭证，仅身份标识）
   * - ?token=xxx& / #fragment     -> 删除查询串与片段
   * - :port                       -> 保留 host 原样交由下游剥离（见 extractCanonicalIdentity）
   *
   * 设计目标：上报“仓库全路径”（host + org/sub/project），但绝不携带明文凭证。
   * 该函数为纯函数，fail-open：无法解析时原样返回（下游 further 兜底）。
   *
   * @param {string} remoteUrl - 原始 remote URL
   * @returns {string} 脱敏后的 remote URL
   */
  function sanitizeRemoteUrl(remoteUrl) {
    if (!remoteUrl || typeof remoteUrl !== 'string') {
      return '';
    }
  
    let url = remoteUrl.trim();
    if (!url) {
      return '';
    }
  
    // 移除查询串与片段（可能含 token= / access_token= 等）
    url = url.replace(/[?#].*$/, '');
  
    // scheme://[user[:token]@]host... -> 删除 user[:token]@（这才是真正的凭证）
    if (url.includes('://')) {
      const proto = url.split('://')[0];
      const after = url.split('://')[1] || '';
      const atIdx = after.indexOf('@');
      const rest = atIdx >= 0 ? after.slice(atIdx + 1) : after;
      url = `${proto}://${rest}`;
    }
    // scp-like git@host:path 不含凭证（'git' 只是 SSH 用户占位），保持原样，
    // 交由 extractCanonicalIdentity 处理 host/path 拆分。
  
    return url;
  }
  
  function extractProjectName(remoteUrl) {
    if (!remoteUrl || typeof remoteUrl !== 'string') {
      return '';
    }
    
    let url = sanitizeRemoteUrl(remoteUrl);
    
    // 移除 .git 后缀
    url = url.replace(/\.git$/i, '');
    
    // 提取路径部分
    let path = '';
    
    // 处理 git@host:path 格式
    if (url.includes('@') && url.includes(':')) {
      const parts = url.split(':');
      path = parts[parts.length - 1];
    }
    // 处理 protocol://... 格式
    else if (url.includes('://')) {
      const parts = url.split('://')[1].split('/');
      path = parts.slice(1).join('/'); // 跳过 host
    }
    // 其他格式
    else {
      path = url;
    }
    
    // 提取最后一段作为项目名
    const segments = path.split('/').filter(Boolean);
    return segments[segments.length - 1] || '';
  }
  
  /**
   * 从 git remote URL 提取规范化身份：{ host, namespace, repoId }
   *
   * namespace 是完整的 "org/sub/project" 路径（不只是最后一段），host 是远程主机名
   * （不含用户名/端口/凭证），repoId 是 sha256("host/namespace")，用于 Server 侧
   * 去重时不必存储/展示明文路径。
   *
   * 覆盖格式：
   * - git@github.com:org/project.git      (scp-like SSH)
   * - ssh://git@gitlab.com:2222/org/sub/project.git
   * - https://user:token@github.com/org/project.git (凭证会被剥离，不进入 canonical 值)
   * - https://github.com/org/project.git
   *
   * @param {string} remoteUrl - 原始 remote URL
   * @returns {{host: string, namespace: string, repoId: string}} 规范化身份，检测失败时字段为空字符串
   */
  function extractCanonicalIdentity(remoteUrl) {
    if (!remoteUrl || typeof remoteUrl !== 'string') {
      return { host: '', namespace: '', repoId: '' };
    }
  
    // 入口处先脱敏，确保任何调用方传入的 URL 都不会把凭证带入 host/namespace
    let url = sanitizeRemoteUrl(remoteUrl).replace(/\.git$/i, '');
    let host = '';
    let path = '';
  
    if (url.includes('://')) {
      // protocol://[user[:token]@]host[:port]/path
      const afterProto = url.split('://')[1] || '';
      const slashIdx = afterProto.indexOf('/');
      const hostPart = slashIdx >= 0 ? afterProto.slice(0, slashIdx) : afterProto;
      path = slashIdx >= 0 ? afterProto.slice(slashIdx + 1) : '';
      // 剥离凭证（user:token@）和端口，只保留 hostname
      host = hostPart.split('@').pop().split(':')[0].toLowerCase();
      path = path.replace(/^\d+\//, '');
    } else if (url.includes('@') && url.includes(':')) {
      // scp-like: git@host:path 或 git@host:port/path（少见但做兼容）
      const atIdx = url.indexOf('@');
      const rest = url.slice(atIdx + 1); // host:path
      const colonIdx = rest.indexOf(':');
      host = (colonIdx >= 0 ? rest.slice(0, colonIdx) : rest).toLowerCase();
      path = colonIdx >= 0 ? rest.slice(colonIdx + 1) : '';
      // 若 path 开头是端口号（例如 36000/group/project），剥离端口
      path = path.replace(/^\d+\//, '');
    } else if (url.includes('/') && /^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::\d+)?\//.test(url)) {
      // 兼容内网各类无协议域名前缀的 Git URL（如 git.woa.com/group/project）
      const slashIdx = url.indexOf('/');
      const hostPart = url.slice(0, slashIdx);
      host = hostPart.split(':')[0].toLowerCase();
      path = url.slice(slashIdx + 1).replace(/^\d+\//, '');
    } else {
      // 无法识别的格式（如本地路径），无 host 概念
      path = url;
    }
  
    const namespace = path.split('/').filter(Boolean).join('/').toLowerCase();
    if (!namespace) {
      return { host, namespace: '', repoId: '', attributionVersion: _getAttributionVersion() };
    }
  
    const canonical = host ? `${host}/${namespace}` : namespace;
    const repoId = _computeRepoId(canonical);
  
    return { host, namespace, repoId, attributionVersion: _getAttributionVersion() };
  }
  
  /**
   * D1-28（HMAC 切片）—— 计算仓库身份指纹。
   *
   * - 若环境变量 CODEBUDDY_REPO_HMAC_KEY 存在：使用 HMAC-SHA256(key, canonical)
   *   产出 64-char hex。这是 D1-28 文档推荐的方案，抵御字典猜测攻击。
   * - 否则：回退到无密钥 sha256(canonical)，行为与 D1-28 最小切片一致。
   *
   * 两种算法产出的 repoId 长度都是 64 字符 hex，Server 端无需区分存储格式——
   * 但 attribution_version 字段标识了算法版本，用于 Dashboard 区分 v1(sha256)
   * 与 v2(hmac) 归因数据，避免混算（D1-28 文档"migration window 内 Dashboard
   * 分开展示 known-v2、legacy、unknown"）。
   */
  function _computeRepoId(canonical) {
    const hmacKey = process.env.CODEBUDDY_REPO_HMAC_KEY;
    if (hmacKey) {
      return createHmac('sha256', hmacKey).update(canonical).digest('hex');
    }
    return createHash('sha256').update(canonical).digest('hex');
  }
  
  /**
   * D1-28 —— 归因版本：'v2-hmac'（HMAC 算法）或 'v1-sha256'（无密钥 sha256）。
   * Server 端 Dashboard 按此字段分组，避免 v1/v2 混算。
   */
  function _getAttributionVersion() {
    return process.env.CODEBUDDY_REPO_HMAC_KEY ? 'v2-hmac' : 'v1-sha256';
  }
  
  /**
   * 从环境变量检测 repo 信息（优先级最高）
   * 
   * @returns {Object|null} { remoteUrl, branch, source } 或 null
   */
  function detectFromEnv() {
    // CODEBUDDY 优先
    if (process.env.CODEBUDDY_REPO_URL) {
      return {
        remoteUrl: process.env.CODEBUDDY_REPO_URL,
        branch: process.env.CODEBUDDY_REPO_BRANCH || '',
        source: 'env_codebuddy'
      };
    }
    
    // GitHub Actions
    if (process.env.GITHUB_REPOSITORY && process.env.GITHUB_SERVER_URL) {
      const remoteUrl = `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}.git`;
      return {
        remoteUrl,
        branch: process.env.GITHUB_REF_NAME || process.env.GITHUB_HEAD_REF || '',
        source: 'env_github'
      };
    }
    
    // GitLab CI
    if (process.env.CI_PROJECT_URL) {
      return {
        remoteUrl: process.env.CI_PROJECT_URL + '.git',
        branch: process.env.CI_COMMIT_REF_NAME || '',
        source: 'env_gitlab'
      };
    }
    
    // Azure DevOps
    if (process.env.BUILD_REPOSITORY_URI) {
      return {
        remoteUrl: process.env.BUILD_REPOSITORY_URI,
        branch: process.env.BUILD_SOURCEBRANCHNAME || '',
        source: 'env_azure'
      };
    }
    
    return null;
  }
  
  /**
   * 从 git 命令检测 repo 信息
   * 
   * @param {string} cwd - 工作目录
   * @returns {Object|null} { remoteUrl, branch, source } 或 null
   */
  function detectFromGit(cwd) {
    try {
      // 1. 检测 git remote origin url（超时 200ms）
      let remoteUrl = '';
      try {
        remoteUrl = execFileSync('git', ['config', '--get', 'remote.origin.url'], {
          cwd,
          timeout: 200,
          encoding: 'utf8',
          stdio: ['ignore', 'pipe', 'ignore']
        }).trim();
      } catch {}
  
      // 2. 若无 origin，尝试匹配任意已配置 remote
      if (!remoteUrl) {
        try {
          const anyRemote = execFileSync('git', ['config', '--get-regexp', '^remote\\..*\\.url'], {
            cwd,
            timeout: 200,
            encoding: 'utf8',
            stdio: ['ignore', 'pipe', 'ignore']
          }).trim();
          if (anyRemote) {
            remoteUrl = anyRemote.split(/\s+/)[1] || '';
          }
        } catch {}
      }
      
      // 检测当前分支（超时 200ms）
      let branch = '';
      try {
        branch = execFileSync('git', ['rev-parse', '--abbrev-ref', 'HEAD'], {
          cwd,
          timeout: 200,
          encoding: 'utf8',
          stdio: ['ignore', 'pipe', 'ignore']
        }).trim();
        
        // detached HEAD 情况
        if (branch === 'HEAD') {
          branch = '';
        }
      } catch {
        // branch 检测失败不影响 remote 信息
      }
      
      if (remoteUrl) {
        return {
          remoteUrl,
          branch,
          source: 'git_remote'
        };
      }
  
      // 3. 兜底策略：当完全无 Git Remote 时，读取当前目录顶层文件夹名称（git rev-parse --show-toplevel）
      const toplevelName = getProjectNameFromDir(cwd);
      if (toplevelName) {
        return {
          remoteUrl: '',
          branch,
          source: 'git_dir',
          projectName: toplevelName,
        };
      }
  
      return null;
    } catch {
      // git 命令失败（不存在、超时、非 git 仓库等）
      return null;
    }
  }
  
  /**
   * 从 git 根目录名提取项目名（fallback）
   * 
   * @param {string} cwd - 工作目录
   * @returns {string} 目录名或空字符串
   */
  function getProjectNameFromDir(cwd) {
    try {
      const toplevel = execFileSync('git', ['rev-parse', '--show-toplevel'], {
        cwd,
        timeout: 200,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'ignore']
      }).trim();
      
      if (!toplevel) {
        return '';
      }
      
      // 提取目录名
      const parts = toplevel.split(/[/\\]/);
      return parts[parts.length - 1] || '';
    } catch {
      return '';
    }
  }
  
  /**
   * 检测 repo 信息（带缓存和 fail-open）
   * 
   * 上报字段：
   * - repo_name: 项目名（仅最后一段，不含组织信息）
   * - repo_branch: 明文分支名
   * - repo_detection_source: 检测来源
   * 
   * @param {Object} options - 选项
   * @param {string} options.cwd - 工作目录（默认 process.cwd()）
   * @returns {Object} repo 信息
   */
  function detectRepo(options = {}) {
    const cwd = options.cwd || process.cwd();
    
    // 检查缓存
    const cacheKey = cwd;
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      return cached.value;
    }
    
    // 默认返回值（fail-open）
    const defaultResult = {
      repo_name: '',
      repo_branch: '',
      repo_detection_source: 'none',
      // D1-28: 精确归因字段，检测失败时留空，Server 侧会 fallback 到 repo_name
      repo_id: '',
      repo_namespace: '',
      repo_remote_host: '',
      attribution_version: '',
    };
    
    try {
      // Priority 1: 环境变量
      let detected = detectFromEnv();
      
      // Priority 2: git 命令
      if (!detected) {
        detected = detectFromGit(cwd);
      }
      
      // 未检测到任何 repo 信息
      if (!detected) {
        cache.set(cacheKey, { value: defaultResult, timestamp: Date.now() });
        return defaultResult;
      }
  
      // 若来自 git_dir 兜底（本地 Git 仓库无 remote 配置）
      if (detected.source === 'git_dir') {
        const projectName = detected.projectName || getProjectNameFromDir(cwd) || '';
        const host = 'internal-git';
        const namespace = projectName.toLowerCase();
        const canonical = `${host}/${namespace}`;
        const repoId = _computeRepoId(canonical);
        const result = {
          repo_name: projectName,
          repo_branch: detected.branch || '',
          repo_detection_source: 'git_dir',
          repo_id: repoId,
          repo_namespace: namespace,
          repo_remote_host: host,
          attribution_version: _getAttributionVersion(),
        };
        cache.set(cacheKey, { value: result, timestamp: Date.now() });
        return result;
      }
      
      // B 方案：上报仓库全路径，但统一消除凭证（user:token@ / ?token= / #fragment）
      const sanitizedRemoteUrl = sanitizeRemoteUrl(detected.remoteUrl);
      
      // 提取项目名（仅最后一段，向后兼容旧字段）
      let projectName = extractProjectName(sanitizedRemoteUrl);
      
      // Fallback: 从目录名提取
      if (!projectName) {
        projectName = getProjectNameFromDir(cwd);
      }
  
      // D1-28: 提取完整 host + namespace，计算 repo_id，避免不同组织/host
      // 下同名仓库（如 org-a/backend 与 org-b/backend）被 repo_name 合并统计
      // 传入已脱敏 URL，确保 host/namespace 不含凭证
      const { host, namespace, repoId, attributionVersion } = extractCanonicalIdentity(sanitizedRemoteUrl);
      
      // 构造结果
      const result = {
        repo_name: projectName,
        repo_branch: detected.branch,
        repo_detection_source: detected.source,
        repo_id: repoId,
        repo_namespace: namespace,
        repo_remote_host: host,
        // D1-28 HMAC 切片：归因版本标识（v1-sha256 或 v2-hmac），用于 Dashboard 分组
        attribution_version: attributionVersion,
      };
      
      // 缓存结果
      cache.set(cacheKey, { value: result, timestamp: Date.now() });
      
      return result;
    } catch (error) {
      // 任何异常都 fail-open，返回默认值
      cache.set(cacheKey, { value: defaultResult, timestamp: Date.now() });
      return defaultResult;
    }
  }
  
  /**
   * 清空缓存（主要用于测试）
   */
  function clearCache() {
    cache.clear();
  }
  
  
  // Module exports
  __repo__.sanitizeRemoteUrl = sanitizeRemoteUrl;
  __repo__.detectRepo = detectRepo;
  __repo__.clearCache = clearCache;
})();


// ============================================================================
// Module: local_audit_adapter
// ============================================================================

(function() {
  /**
   * LocalAuditAdapter 安全执行工具 —— O1-11（最小切片）
   *
   * 所有 Adapter 共用同一套子进程安全规则（见
   * fix_update/optimizations/11_Local_Native_Audit_Adapter.md 的"安全执行"
   * 章节）：
   * - execFile + 参数数组，不拼接 shell 字符串（不使用 exec/shell:true）。
   * - 固定超时，超时后子进程被终止。
   * - stdout/stderr 截断到字节上限，防止超大输出占满内存/日志。
   * - 不解释退出码本身为"成功/失败"——不同 CLI 工具对"发现问题"和"命令
   *   执行失败"的退出码语义不一致（如 npm audit 发现漏洞时退出码非 0，
   *   但这不代表命令执行失败），由各 Adapter 自己的 normalize() 判断。
   *
   * LocalAuditAdapter 接口契约（用 JSDoc 描述，项目是纯 JS 不用 TypeScript）：
   *   detect()    - 工具是否存在、版本是否支持
   *   plan()      - 根据事件判断是否应该运行
   *   scan()      - 使用固定参数执行
   *   normalize() - 转为统一结果
   *   health()    - 返回 ready/degraded/disabled
   *
   * @typedef {Object} AdapterCommandResult
   * @property {number|null} code - 子进程退出码（不代表"成功/失败"，见上）
   * @property {string} stdout - 截断到字节上限的 stdout
   * @property {string} stderr - 截断到字节上限的 stderr
   * @property {boolean} timedOut - 是否因超时被终止
   * @property {Error|null} spawnError - 命令本身找不到等启动失败错误（ENOENT），
   *   区别于"命令启动成功但执行结果里包含错误"
   *
   * @typedef {Object} NormalizedAuditResult
   * @property {string} adapter - Adapter 名称
   * @property {string|null} adapter_version - 底层工具版本
   * @property {'completed'|'degraded'|'unsupported'} state
   * @property {Array<Object>} findings
   * @property {number} duration_ms
   */
  
  const { execFile } = require('child_process');
  
  const MAX_OUTPUT_BYTES = 5 * 1024 * 1024; // 5MB，防止超大 audit 输出占满内存
  
  /**
   * 安全执行一个本地扫描工具命令。
   *
   * @param {string} command - 可执行文件名（依赖 PATH 解析，不是拼接来的字符串）
   * @param {string[]} args - 固定参数数组，不包含任何来自项目内容的动态 CLI option
   * @param {Object} options
   * @param {string} options.cwd
   * @param {number} [options.timeoutMs=8000]
   * @returns {Promise<AdapterCommandResult>}
   */
  function runAdapterCommand(command, args, { cwd, timeoutMs = 8000 } = {}) {
    return new Promise((resolve) => {
      const child = execFile(
        command,
        args,
        { cwd, timeout: timeoutMs, maxBuffer: MAX_OUTPUT_BYTES, windowsHide: true },
        (error, stdout, stderr) => {
          const timedOut = !!error && error.killed && error.signal === 'SIGTERM';
          resolve({
            code: error?.code && typeof error.code === 'number' ? error.code : (error ? 1 : 0),
            stdout: String(stdout || '').slice(0, MAX_OUTPUT_BYTES),
            stderr: String(stderr || '').slice(0, MAX_OUTPUT_BYTES),
            timedOut,
            // ENOENT 等"命令本身找不到"错误——用于 detect() 判断工具缺失，
            // 而不是当作扫描失败重试
            spawnError: error && error.code === 'ENOENT' ? error : null,
          });
        }
      );
      // 安全边界：Adapter 命令不需要交互输入，主动结束 stdin，避免子进程
      // 意外挂起等待输入
      child.stdin?.end();
    });
  }
  
  
  // Module exports
  __local_audit_adapter__.runAdapterCommand = runAdapterCommand;
})();


// ============================================================================
// Module: local_audit_npm_audit
// ============================================================================

(function() {
  /**
   * npm audit Adapter —— O1-11（最小切片）
   *
   * 只提供证据，不直接输出 Hook 决策（文档"Adapter 只提供证据，不直接
   * 输出 Hook 决策"）。本次未接入任何自动触发路径——当前架构是 100% 同步
   * PreToolUse（没有 PostToolUse 审计触发通道、没有 CI/后台任务系统），
   * 文档自己把"每次 manifest Write 全量扫描"列为不推荐场景。因此本次只把
   * detect()/health() 接入只读诊断命令（--status），scan()/normalize()
   * 保持独立可调用，留给未来的 PostToolUse/CI 触发基础设施使用。
   */
  
  const { existsSync } = require('fs');
  const { join } = require('path');
  const runAdapterCommand = __local_audit_adapter__.runAdapterCommand;
  
  const ADAPTER_NAME = 'npm-audit';
  
  /**
   * 检测 npm 是否可用（工具存在性），不检测项目是否有 lockfile——那是
   * plan() 的职责（"是否应该运行"和"工具是否存在"是两个独立问题）。
   *
   * @returns {Promise<{available: boolean, version: string|null}>}
   */
  async function detect() {
    const result = await runAdapterCommand('npm', ['--version'], { cwd: process.cwd(), timeoutMs: 3000 });
    if (result.spawnError || result.code !== 0) {
      return { available: false, version: null };
    }
    return { available: true, version: result.stdout.trim() };
  }
  
  /**
   * 判断在给定项目目录下是否应该运行 npm audit —— 只在存在 lockfile 时
   * 才有意义运行（没有 lockfile 时 npm audit 会返回 ENOLOCK 错误，运行
   * 它毫无价值，plan() 提前拦掉，不浪费一次子进程调用）。
   *
   * @param {string} projectDir
   * @returns {{shouldRun: boolean, reason: string}}
   */
  function plan(projectDir) {
    const hasLockfile = existsSync(join(projectDir, 'package-lock.json')) ||
      existsSync(join(projectDir, 'npm-shrinkwrap.json'));
    if (!hasLockfile) {
      return { shouldRun: false, reason: 'no_lockfile' };
    }
    return { shouldRun: true, reason: 'lockfile_present' };
  }
  
  /**
   * 执行 npm audit --json，返回原始结果（未归一化）。
   *
   * @param {string} projectDir
   * @param {number} [timeoutMs]
   * @returns {Promise<import('./adapter.js').AdapterCommandResult>}
   */
  async function scan(projectDir, timeoutMs = 8000) {
    // 固定参数数组，不受任何项目输入影响——见 adapter.js 的安全执行规则
    return runAdapterCommand('npm', ['audit', '--json'], { cwd: projectDir, timeoutMs });
  }
  
  /**
   * 将 scan() 的原始结果归一化为统一结果格式。
   *
   * npm audit 的退出码语义：发现漏洞时退出码非 0，这不代表命令执行失败——
   * 必须靠 stdout 是否为合法 JSON 且不含 top-level "error" 字段来判断
   * "命令是否真正执行成功"，不能直接用退出码判断（已用真实 npm audit
   * 输出验证过这三种场景：无漏洞→退出码0；有漏洞→退出码非0但 stdout 是
   * 完整合法 JSON；无 lockfile→退出码非0且 stdout 含 error.code=ENOLOCK）。
   *
   * @param {import('./adapter.js').AdapterCommandResult} scanResult
   * @param {Object} [meta]
   * @param {number} [meta.durationMs]
   * @param {string|null} [meta.adapterVersion]
   * @returns {import('./adapter.js').NormalizedAuditResult}
   */
  function normalize(scanResult, { durationMs = 0, adapterVersion = null } = {}) {
    const base = { adapter: ADAPTER_NAME, adapter_version: adapterVersion, duration_ms: durationMs };
  
    if (scanResult.spawnError) {
      return { ...base, state: 'unsupported', findings: [] }; // 工具缺失
    }
    if (scanResult.timedOut) {
      return { ...base, state: 'degraded', findings: [] };
    }
  
    let parsed;
    try {
      parsed = JSON.parse(scanResult.stdout);
    } catch {
      return { ...base, state: 'degraded', findings: [] }; // 无效 JSON，不阻塞主流程
    }
  
    if (parsed.error) {
      // ENOLOCK 等——理论上 plan() 已经提前拦掉，这里是防御纵深
      return { ...base, state: 'unsupported', findings: [] };
    }
  
    const findings = Object.values(parsed.vulnerabilities || {}).map((v) => ({
      package: v.name,
      version: null, // npm audit v2 输出不含当前安装的具体版本字段，只有 range；不伪造
      advisory_ids: (v.via || [])
        .filter((item) => typeof item === 'object' && item.url)
        .map((item) => item.url),
      reachability: 'unknown', // npm audit 不提供可达性证据
      fix_versions: v.fixAvailable && typeof v.fixAvailable === 'object' ? [v.fixAvailable.version] : [],
    }));
  
    return { ...base, state: 'completed', findings };
  }
  
  /**
   * 返回该 Adapter 当前的可用性摘要，供只读诊断命令（--status）展示。
   *
   * @returns {Promise<{state: 'ready'|'disabled', version: string|null}>}
   */
  async function health() {
    const { available, version } = await detect();
    return { state: available ? 'ready' : 'disabled', version };
  }
  
  
  // Module exports
  __local_audit_npm_audit__.plan = plan;
  __local_audit_npm_audit__.normalize = normalize;
  __local_audit_npm_audit__.detect = detect;
  __local_audit_npm_audit__.scan = scan;
  __local_audit_npm_audit__.health = health;
})();


// ============================================================================
// Module: client
// ============================================================================

(function() {
  /**
   * HTTP Client
   * 
   * 与 MCP Security Server 通信
   * 
   * P2 优化：
   * - 默认超时从 5000ms 降到 2000ms
   * - 添加 Connection: keep-alive 头
   * - 优化重试策略
   *
   * TLS 配置（环境变量）：
   * - CODEBUDDY_SECURITY_SERVER_URL=https://host:443     服务器地址（支持 HTTPS）
   * - CODEBUDDY_SECURITY_CA_CERT=/path/to/ca.crt        指定自定义 CA 证书路径（推荐，用于自签名证书）
   * - CODEBUDDY_SECURITY_TLS_REJECT_UNAUTHORIZED=false  跳过证书验证（仅开发/测试环境）
   * - NODE_TLS_REJECT_UNAUTHORIZED=0                    标准 Node.js 跳过验证（同上，向后兼容）
   *
   * 优先级（高 → 低）：
   *   1. CODEBUDDY_SECURITY_CA_CERT        — 自签名证书信任（推荐）
   *   2. CODEBUDDY_SECURITY_TLS_REJECT_UNAUTHORIZED=false — 完全跳过验证
   *   3. NODE_TLS_REJECT_UNAUTHORIZED=0   — 标准 Node.js 跳过验证
   *   4. 默认：系统 CA 信任链（严格验证）
   *
   * 典型错误码（出现在 reason 字段）：
   * - tls_certificate_error_fail_open → 证书验证失败，设置 CODEBUDDY_SECURITY_CA_CERT 或跳过验证
   * - DEPTH_ZERO_SELF_SIGNED_CERT / SELF_SIGNED_CERT_IN_CHAIN → 自签名证书未受信任
   * - ERR_TLS_CERT_ALTNAME_INVALID                           → 证书域名不匹配，检查 CN/SAN
   * - ECONNREFUSED                                           → 服务端未启动或端口错误
   */
  const { request: httpsRequest } = require('https');
  const { request: httpRequest } = require('http');
  const { URL, fileURLToPath } = require('url');
  const { readFileSync } = require('fs');
  const { resolve, dirname } = require('path');
  const buildSessionHeaders = __auth_session_reader__.buildSessionHeaders;
  const UI = __ui__.UI;
  const buildTlsOptions = __tls__.buildTlsOptions;
  // S2 组件明细采集：仓库检测（进程内 30s 缓存，失败 fail-open 返回空字段）
  const detectRepo = __repo__.detectRepo;
  // 从 package.json 读取版本号，避免硬编码
  const CLIENT_VERSION = '1.3.0'; // injected by bundle-cjs.js
  /**
   * 基于 Node.js 内置 http/https 模块发送 POST 请求
   *
   * @param {string} urlStr - 目标 URL
   * @param {Object} headers - 请求头
   * @param {string} body - 请求体（JSON 字符串）
   * @param {number} timeout - 本次尝试的超时毫秒（D1-20：调用方传入的是"剩余预算"，不是
   *   固定满额值——见 checkPackagesChunk() 的调用处）
   * @returns {Promise<{status: number, data: any}>}
   */
  function httpPost(urlStr, headers, body, timeout) {
    return new Promise((resolve, reject) => {
      const url = new URL(urlStr);
      const isHttps = url.protocol === 'https:';
      const tlsOptions = isHttps ? buildTlsOptions() : {};
      const options = {
        hostname: url.hostname,
        port: url.port || (isHttps ? 443 : 80),
        path: url.pathname + url.search,
        method: 'POST',
        headers: {
          ...headers,
          'Content-Length': Buffer.byteLength(body),
        },
        ...tlsOptions,
      };
      const req = (isHttps ? httpsRequest : httpRequest)(options, (res) => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode, data: JSON.parse(data) });
          } catch (e) {
            reject(new Error(`Failed to parse response: ${e.message}`));
          }
        });
      });
      req.setTimeout(timeout, () => {
        req.destroy();
        const err = new Error('Request timeout');
        err.name = 'AbortError';
        reject(err);
      });
      req.on('error', reject);
      req.write(body);
      req.end();
    });
  }
  /**
   * 基于 Node.js 内置 http/https 模块发送 GET 请求
   *
   * @param {string} urlStr - 目标 URL
   * @param {number} timeout - 超时毫秒
   * @returns {Promise<{status: number}>}
   */
  function httpGet(urlStr, timeout) {
    return new Promise((resolve, reject) => {
      const url = new URL(urlStr);
      const isHttps = url.protocol === 'https:';
      const tlsOptions = isHttps ? buildTlsOptions() : {};
      const options = {
        hostname: url.hostname,
        port: url.port || (isHttps ? 443 : 80),
        path: url.pathname + url.search,
        method: 'GET',
        headers: {
          'X-Service-Id': 'chainguard',
        },
        ...tlsOptions,
      };
      const req = (isHttps ? httpsRequest : httpRequest)(options, (res) => {
        res.resume(); // 消耗响应体
        res.on('end', () => resolve({ status: res.statusCode }));
      });
      req.setTimeout(timeout, () => {
        req.destroy();
        const err = new Error('Request timeout');
        err.name = 'AbortError';
        reject(err);
      });
      req.on('error', reject);
      req.end();
    });
  }
  // Server 端 MAX_PACKAGES_PER_REQUEST 默认值（src/config.py HTTPConfig.max_packages_per_request）。
  // 超过此数量单次请求会被 Server 拒绝（HTTP 400），此前 Client 会把 400 当作普通请求错误
  // 走 Fail-Open，导致整批包（可能是几十上百个依赖）完全跳过审计。现在 Client 主动分片，
  // 保证超限时仍能对全部包分批完成真实审计，而不是整批放弹。
  const DEFAULT_MAX_PACKAGES_PER_CHUNK = 50;
  /**
   * 检查包安全性
   * 
   * @param {string} ecosystem - 生态系统 (npm, pypi, go, etc)
   * @param {Array} packages - 包列表 [{n, v}]
   * @param {Object} context - 上下文信息
   * @param {string} serverUrl - Server URL
   * @param {number} timeout - 超时时间 (ms)，默认 2000ms
   * @param {number} retries - 重试次数
   * @param {number} maxPackagesPerChunk - 单次请求最大包数，超过则自动分片（默认 50，
   *   与 Server 侧 MAX_PACKAGES_PER_REQUEST 默认值保持一致；可通过环境变量覆盖两侧配置时
   *   建议同步调整）
   * @returns {Promise<Object>} Server 响应
   */
  async function checkPackages(ecosystem, packages, context, serverUrl, timeout = 2000, retries = 1, maxPackagesPerChunk = DEFAULT_MAX_PACKAGES_PER_CHUNK) {
    // P0-2: 清洗无效/空包名，避免空包触发服务端 HTTP 422 校验失败导致降级放行
    const validPackages = (packages || []).filter(p => p && typeof p.n === 'string' && p.n.trim().length > 0);
    if (validPackages.length === 0) {
      return {
        s: 'PASS',
        t: 0,
        reason: 'no_packages',
        hook_action: 'allow',
        coverage: 'COMPLETE',
        decision: 'PASS',
        reason_code: null,
        policy_result: null,
      };
    }
    const cleanedPackages = validPackages.map(p => ({
      ...p,
      n: p.n.trim(),
      v: typeof p.v === 'string' ? p.v.trim() : (p.v || ''),
    }));
    // P0-3: 超时预算动态分级优化 (解决 738 次 timeout_fail_open)
    // 1. 若外部环境变量显式指定 CODEBUDDY_SECURITY_TIMEOUT，以显式配置为准；
    // 2. 常规小批量 (<= 5 个包且非文件清单全量扫描)：维持传入 timeout (默认 2000ms)；
    // 3. 大清单/多依赖扫描 (> 5 个包或涉及清单文件)：放宽至 3500ms，为服务端多源判定（OSV+License）预留充足时间。
    let effectiveTimeout = timeout;
    const envTimeout = parseInt(process.env.CODEBUDDY_SECURITY_TIMEOUT || process.env.CODEBUDDY_SECURITY_TIMEOUT_MS, 10);
    if (!isNaN(envTimeout) && envTimeout > 0) {
      effectiveTimeout = envTimeout;
    } else if (!context?.customTimeout && (cleanedPackages.length > 5 || (context && context.file_path && /\.(json|lock|txt|xml|toml|mod)$/i.test(context.file_path)))) {
      effectiveTimeout = Math.max(timeout, 3500);
    }
    if (cleanedPackages.length <= maxPackagesPerChunk) {
      return checkPackagesChunk(ecosystem, cleanedPackages, context, serverUrl, effectiveTimeout, retries);
    }
    return checkPackagesInChunks(ecosystem, cleanedPackages, context, serverUrl, effectiveTimeout, retries, maxPackagesPerChunk);
  }
  /**
   * 将超限的包列表分片，逐片调用 Server 并合并结果。
   *
   * 合并策略（"最严格优先"，与多 ecosystem 合并的策略一致）：
   * - 任一分片 BLOCK → 整体视为 BLOCK，合并所有分片的 unfixable 列表，但不合并
   *   fixed_content（多个分片各自基于同一份 context.original_content 独立计算出的
   *   fixed_content 无法安全叠加应用到同一个文件，强行合并有更高的正确性风险，
   *   因此分片场景下不做文件级 Autofix，只做安全审计+明确阻断，用户/Agent 需要
   *   分批安装或手动处理，比"跳过审计静默放行"更安全）
   * - 无 BLOCK 但存在 WARN → 整体 WARN
   * - 全部 PASS → 整体 PASS
   */
  async function checkPackagesInChunks(ecosystem, packages, context, serverUrl, timeout, retries, maxPackagesPerChunk) {
    const chunks = [];
    for (let i = 0; i < packages.length; i += maxPackagesPerChunk) {
      chunks.push(packages.slice(i, i + maxPackagesPerChunk));
    }
    // Bounded concurrency: process chunks in batches of MAX_CONCURRENT
    // with a shared cross-batch deadline
    const MAX_CONCURRENT = 3;
    const batchDeadline = Date.now() + timeout;
    const chunkResults = [];
    for (let i = 0; i < chunks.length; i += MAX_CONCURRENT) {
      const batch = chunks.slice(i, i + MAX_CONCURRENT);
      const remainingMs = batchDeadline - Date.now();
      if (remainingMs <= 0) {
        // Cross-batch deadline exhausted — remaining chunks get fail-open
        for (let j = i; j < chunks.length; j++) {
          chunkResults.push({
            s: 'PASS', t: 0, reason: 'batch_deadline_exhausted_fail_open',
            hook_action: 'allow', fail_open: true, decision: 'PASS',
            reason_code: null, policy_result: null,
          });
        }
        break;
      }
      // Each chunk gets min(remaining, original timeout) as its budget
      const chunkTimeout = Math.min(remainingMs, timeout);
      const batchResults = await Promise.all(
        batch.map(chunk => checkPackagesChunk(ecosystem, chunk, context, serverUrl, chunkTimeout, retries))
      );
      chunkResults.push(...batchResults);
    }
    const blocked = chunkResults.filter(r => r?.s === 'BLOCK');
    const warned = chunkResults.filter(r => r?.s === 'WARN');
    const anyFailOpen = chunkResults.some(r => r?.fail_open === true);
    const maxTime = chunkResults.reduce((max, r) => Math.max(max, r?.t || 0), 0);
    if (blocked.length > 0) {
      const mergedUnfixable = blocked.flatMap(r => r.unfixable || r.u || []);
      return {
        s: 'BLOCK',
        t: maxTime,
        reason: blocked.map(r => r.reason || r.r).filter(Boolean).join(';') || 'CHUNKED_BLOCK',
        hook_action: 'deny',
        unfixable: mergedUnfixable,
        _chunked: true,
        _chunk_count: chunks.length,
        fail_open: anyFailOpen,
        // D0-12：合成的 chunk merge 响应也带 decision 字段（= s），
        // 让 Client 下游无需特殊处理 chunked 响应。reason_code/policy_result
        // 在 merge 场景无法干净归并（多个 chunk 可能各自命中不同 reason），
        // 留 null，Client 回退读 reason。
        decision: 'BLOCK',
        reason_code: null,
        policy_result: null,
      };
    }
    if (warned.length > 0) {
      // F-04: WARN + fail-open must not return plain 'CHUNKED_WARN'
      if (anyFailOpen) {
        return {
          s: 'WARN',
          t: maxTime,
          reason: 'partial_audit_warn_fail_open',
          hook_action: 'allow',
          fail_open: true,
          coverage: 'PARTIAL',
          checked_count: chunkResults.filter(r => r?.s === 'PASS' || r?.s === 'WARN').length,
          degraded_count: chunkResults.filter(r => r?.fail_open).length,
          _chunked: true,
          _chunk_count: chunks.length,
          decision: 'WARN',
          reason_code: null,
          policy_result: null,
        };
      }
      return {
        s: 'WARN',
        t: maxTime,
        reason: 'CHUNKED_WARN',
        hook_action: 'allow',
        coverage: 'COMPLETE',
        _chunked: true,
        _chunk_count: chunks.length,
        fail_open: anyFailOpen,
        decision: 'WARN',
        reason_code: null,
        policy_result: null,
      };
    }
    // F-04 修复：任一 chunk fail-open 时不返回 reason='safe'，
    // 改返回 'partial_audit_fail_open'（以 _fail_open 结尾，isFailOpenReason 会识别）
    // 并新增 coverage/checked_count/degraded_count 字段
    if (anyFailOpen) {
      return {
        s: 'PASS',
        t: maxTime,
        reason: 'partial_audit_fail_open',
        hook_action: 'allow',
        fail_open: true,
        coverage: 'PARTIAL',
        checked_count: chunkResults.filter(r => r?.s === 'PASS' || r?.s === 'WARN').length,
        degraded_count: chunkResults.filter(r => r?.fail_open).length,
        _chunked: true,
        _chunk_count: chunks.length,
        decision: 'PASS',
        reason_code: null,
        policy_result: null,
      };
    }
    return {
      s: 'PASS',
      t: maxTime,
      reason: 'safe',
      hook_action: 'allow',
      coverage: 'COMPLETE',
      _chunked: true,
      _chunk_count: chunks.length,
      fail_open: anyFailOpen,
      decision: 'PASS',
      reason_code: null,
      policy_result: null,
    };
  }
  // D1-20：一次有意义的请求尝试所需的最小时间。剩余预算低于"退避时间 + 这个值"时，
  // 直接放弹最后一次重试而不是硬发一个几乎必然再次超时的请求——语义上等价于放弹，
  // 但避免多消耗一次网络往返和日志噪音。
  const MIN_ATTEMPT_BUDGET_MS = 100;
  /**
   * 检查单个分片（不超过 maxPackagesPerChunk 的包列表）。
   *
   * D1-20 修复：此前每次重试都会重新拿到完整的 `timeout` 值（例如 timeout=2000ms，
   * 第一次尝试耗尽 2000ms 超时后，重试时 `req.setTimeout` 仍然是满额 2000ms），导致
   * 总耗时可能达到 timeout*(retries+1)，远超调用方期望的预算。现在改为整个函数共享
   * 一个 `deadline`（本次调用开始时刻 + timeout），每次尝试只使用"剩余时间"，退避前
   * 也检查剩余预算是否还够一次有意义的尝试，不够则直接放弹（对外结果与"最后一次尝试
   * 失败"完全一致，只是不再多发一次几乎必然超时的请求）。
   */
  async function checkPackagesChunk(ecosystem, packages, context, serverUrl, timeout = 2000, retries = 1) {
    const endpoint = `${serverUrl}/hook/check-with-fix`;
    const deadline = Date.now() + timeout; // 本次调用（含所有重试）共享的总预算终点
    const requestBody = {
      e: ecosystem,
      p: packages,
      context: context
    };
    let lastError = null;
    let lastAttempt = 0;
    for (let attempt = 0; attempt <= retries; attempt++) {
      lastAttempt = attempt;
      const remainingMs = deadline - Date.now();
      if (remainingMs <= 0) {
        // 预算已耗尽（通常发生在上一次尝试恰好用满整个 timeout 之后），不再发起新尝试
        break;
      }
      try {
        // ── 构造请求 headers ────────────────────────────────────────────────────
        //
        // 优先级（高 → 低）：
        //   1. 固定客户端标识头（X-Client-Type / X-Service-Id 等）
        //   2. buildSessionHeaders() —— 从本地 auth 文件读取，还原：
        //        Layer 1: enterpriseHeaders(auth)        → X-Domain
        //        Layer 2: axios AuthenticationHttpInterceptor
        //                   → Authorization / X-User-Id / X-Enterprise-Id / X-Tenant-Id
        //        Layer 3: OpenTelemetrySpan.requestHeaders
        //                   → X-Request-ID / b3 / X-B3-*
        //   3. 环境变量覆盖（CODEBUDDY_USER_ID / CODEBUDDY_SECURITY_JWT_TOKEN 等）
        //      —— 保留向后兼容，环境变量显式配置时优先级更高
        //
        const sessionHeaders = buildSessionHeaders();
        // S2 组件明细采集头（方案 §3.1）：只透传，不做任何兜底推断——
        // context.phase 缺失说明上游未按方案改造，服务端应视为未确认（不采集）。
        // detectRepo 内部 fail-open 且带 30s 进程内缓存，检测失败字段为空串。
        const _cgRepo = detectRepo();
        const headers = {
          'Content-Type':    'application/json',
          'Connection':      'keep-alive',
          'X-Client-Type':   'nodejs',
          'X-Client-Version': CLIENT_VERSION,
          'X-Service-Id':    'chainguard',
          // S2 组件采集头（X-CG-Phase 仅透传；服务端仅接受字面量 PRECHECK）
          'X-CG-Phase':         typeof context?.phase === 'string' ? context.phase : '',
          'X-CG-Repo-Id':       _cgRepo?.repo_id || '',
          'X-CG-Repo-Namespace': _cgRepo?.repo_namespace || '',
          'X-CG-Repo-Host':     _cgRepo?.repo_remote_host || '',
          'X-CG-Repo-Branch':   _cgRepo?.repo_branch || '',
          'X-CG-Call-Id':       context?.call_id || '',
          // session 中的身份 + trace 头（Authorization / X-User-Id / X-Domain / X-Request-ID …）
          ...sessionHeaders,
        };
        // 环境变量覆盖：若外部显式配置则覆盖 session 中的对应字段
        const envUserId = process.env.CODEBUDDY_USER_ID;
        if (envUserId) {
          headers['X-User-Id'] = envUserId;
        }
        const envUserName = process.env.CODEBUDDY_USER_NAME || process.env.CODEBUDDY_RTX;
        if (envUserName) {
          headers['X-User-Name'] = envUserName;
          headers['X-RTX-Name']  = envUserName;
        }
        if (context?.session_id) {
          headers['X-Codebuddy-Session-Id'] = String(context.session_id);
          headers['X-Session-Id']           = String(context.session_id);
        }
        const envJwt = process.env.CODEBUDDY_SECURITY_JWT_TOKEN;
        if (envJwt) {
          headers['Authorization'] = `Bearer ${envJwt}`;
        }
        const envEnterprise = process.env.CODEBUDDY_ENTERPRISE_ID;
        if (envEnterprise) {
          headers['X-Enterprise-Id'] = envEnterprise;
          headers['X-Tenant-Id']     = envEnterprise;
        }
        const envTenant = process.env.CODEBUDDY_TENANT_ID;
        if (envTenant) {
          headers['X-Tenant-Id'] = envTenant;
        }
        // D1-20：告知 Server 本次请求剩余的预算（相对毫秒数，不是绝对时钟时间——避免
        // 依赖 Client/Server 时钟同步）。Server 收到后与自己的上限取 min()，不会因为
        // 这个头被无限延长超时；Server 不识别/不读取此头时行为不受影响（向后兼容）。
        headers['X-Request-Deadline-Ms'] = String(Math.max(0, remainingMs));
        UI.log(`[CLIENT] attempt=${attempt} endpoint=${endpoint} remaining_budget_ms=${remainingMs}`);
        const { status, data } = await httpPost(endpoint, headers, JSON.stringify(requestBody), remainingMs);
        // 网关 401 特殊处理：直接 fail-open，不重试（避免触发 CodeBuddy 登出）
        if (status === 401) {
          return { ...createFailOpenResponse(new Error('gateway_401_fail_open')), _retry_count: attempt, _http_status: 401 };
        }
        if (status < 200 || status >= 300) {
          throw new Error(`Server returned ${status}`);
        }
        return { ...data, _retry_count: attempt, _http_status: status };
      } catch (error) {
        lastError = error;
        // 如果是中止错误（超时），不重试
        if (error.name === 'AbortError') {
          break;
        }
        // 如果不是最后一次尝试，等待后重试（指数退避）
        if (attempt < retries) {
          const backoffMs = 100 * Math.pow(2, attempt);  // P2: 指数退避 100ms, 200ms, 400ms...
          // D1-20：退避前检查剩余预算是否还够"退避等待 + 一次最小有意义的尝试"，
          // 不够就直接放弹，避免明知道会再次超时还硬发一次请求
          const remainingAfterBackoff = (deadline - Date.now()) - backoffMs;
          if (remainingAfterBackoff < MIN_ATTEMPT_BUDGET_MS) {
            break;
          }
          await sleep(backoffMs);
        }
      }
    }
    
    // 所有尝试都失败，返回 Fail-Open 响应
    return { ...createFailOpenResponse(lastError), _retry_count: lastAttempt, _http_status: null };
  }
  /**
   * 创建 Fail-Open 响应
   * 
   * @param {Error} error - 错误对象
   * @returns {Object} Fail-Open 响应
   */
  function createFailOpenResponse(error) {
    let reason = 'unknown_error_fail_open';
    
    if (error) {
      if (error.name === 'AbortError') {
        reason = 'timeout_fail_open';
      } else if (error.code === 'ECONNREFUSED') {
        reason = 'connection_refused_fail_open';
      } else if (error.code === 'ENOTFOUND') {
        reason = 'server_not_found_fail_open';
      } else if (
        error.code === 'DEPTH_ZERO_SELF_SIGNED_CERT' ||
        error.code === 'SELF_SIGNED_CERT_IN_CHAIN' ||
        error.code === 'ERR_TLS_CERT_ALTNAME_INVALID' ||
        error.code === 'UNABLE_TO_VERIFY_LEAF_SIGNATURE' ||
        error.code === 'CERT_HAS_EXPIRED' ||
        (error.message && /certificate/i.test(error.message))
      ) {
        reason = 'tls_certificate_error_fail_open';
      } else {
        reason = 'request_error_fail_open';
      }
    }
    
    return {
      s: 'PASS',
      t: 0,
      reason: reason,
      fail_open: true,
      // D0-12：fail-open 响应也带 decision 字段（= s = PASS），reason_code 复用
      // fail-open reason 字符串（虽然这些 reason 不在 v1 ReasonCode 枚举中，但
      // 保持字段形状一致让 Client 下游无需特殊处理）。policy_result 留 null
      // （fail-open 场景未完成合规检查，但语义上属于"网络/系统故障"而非"License
      // 数据源不可用"，不走 SOURCE_UNAVAILABLE——后者是 Server 端明确判断后的
      // 结果，这里是 Client 端网络失败）。
      decision: 'PASS',
      reason_code: null,
      policy_result: null,
    };
  }
  /**
   * 睡眠函数
   * 
   * @param {number} ms - 毫秒数
   * @returns {Promise<void>}
   */
  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  /**
   * 健康检查
   * 
   * @param {string} serverUrl - Server URL
   * @param {number} timeout - 超时时间 (ms)
   * @returns {Promise<boolean>} 是否健康
   */
  async function healthCheck(serverUrl, timeout = 2000) {
    try {
      const { status } = await httpGet(`${serverUrl}/health`, timeout);
      return status >= 200 && status < 300;
    } catch (error) {
      return false;
    }
  }
  __client__.default = checkPackages;
  
  // Module exports
  __client__.checkPackages = checkPackages;
  __client__.healthCheck = healthCheck;
})();


// ============================================================================
// Module: autofix_manifest_adapter_npm
// ============================================================================

(function() {
  /**
   * npm Manifest Adapter (O1-17) —— package.json 本地结构化 Autofix
   *
   * 实现 parse/locate/apply/validate/render 5 个方法（对齐
   * fix_update/optimizations/17_Local_Structured_File_Autofix.md）：
   * - parse: 安全解析 JSON（不用 eval，用 JSON.parse）
   * - locate: 找到指定依赖在 dependencies/dev/peer/optional 中的位置
   * - apply: 只修改目标依赖版本，保留格式、注释和无关字段
   * - validate: 重新解析修改结果，验证目标版本 + 语法 + 未修改字段
   * - render: 输出最终文件内容
   *
   * 安全约束（文档"安全约束"章节）：
   * - 不允许 fix plan 修改 scripts/repository/registry/plugin 配置
   * - from_spec 不匹配时拒绝应用
   * - 多 edit 必须全部成功才提交
   * - 输出大小和 edit 数量有限制
   */
  
  const MAX_EDITS = 50;
  const MAX_OUTPUT_BYTES = 1024 * 1024; // 1MB
  
  /**
   * 安全解析 package.json
   * @param {string} content - 文件原文
   * @returns {{ok: true, data: Object} | {ok: false, error: string}}
   */
  function parse(content) {
    if (!content || typeof content !== 'string') {
      return { ok: false, error: 'empty content' };
    }
    if (content.length > MAX_OUTPUT_BYTES) {
      return { ok: false, error: 'content exceeds 1MB limit' };
    }
    try {
      const data = JSON.parse(content);
      if (typeof data !== 'object' || data === null || Array.isArray(data)) {
        return { ok: false, error: 'not a JSON object' };
      }
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: `JSON parse error: ${err.message}` };
    }
  }
  
  /**
   * 依赖 section 名称（按优先级查找）
   */
  const DEPENDENCY_SECTIONS = ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'];
  
  /**
   * 定位指定包在 package.json 中的位置
   * @param {Object} data - 已解析的 package.json 对象
   * @param {string} packageName - 包名
   * @returns {{section: string, currentSpec: string} | null}
   */
  function locate(data, packageName) {
    if (!data || typeof data !== 'object') return null;
    // F-03.3: Block prototype pollution — reject constructor/__proto__/prototype
    const PROTOTYPE_BLOCKLIST = new Set(['constructor', '__proto__', 'prototype', 'hasOwnProperty', 'toString', 'valueOf']);
    if (PROTOTYPE_BLOCKLIST.has(packageName)) return null;
    for (const section of DEPENDENCY_SECTIONS) {
      const deps = data[section];
      // F-03.3: Use hasOwnProperty instead of `in` to prevent prototype chain lookup
      if (deps && typeof deps === 'object' && Object.prototype.hasOwnProperty.call(deps, packageName)) {
        return { section, currentSpec: deps[packageName] };
      }
    }
    return null;
  }
  
  /**
   * 应用结构化 edit plan 到 package.json
   *
   * @param {string} content - 原始文件内容
   * @param {Array<{package_id: string, from_spec: string, to_spec: string}>} edits
   * @returns {{ok: true, content: string, applied: number} | {ok: false, error: string}}
   */
  function apply(content, edits) {
    if (!Array.isArray(edits) || edits.length === 0) {
      return { ok: false, error: 'no edits provided' };
    }
    if (edits.length > MAX_EDITS) {
      return { ok: false, error: `too many edits (${edits.length} > ${MAX_EDITS})` };
    }
  
    const parsed = parse(content);
    if (!parsed.ok) {
      return { ok: false, error: parsed.error };
    }
    const data = parsed.data;
  
    // 安全约束：拒绝修改非依赖字段
    const FORBIDDEN_FIELDS = new Set(['scripts', 'repository', 'registry', 'config', 'name', 'version', 'private']);
    for (const edit of edits) {
      if (FORBIDDEN_FIELDS.has(edit.package_id)) {
        return { ok: false, error: `forbidden field modification: ${edit.package_id}` };
      }
    }
  
    // 应用每个 edit
    let appliedCount = 0;
    for (const edit of edits) {
      const location = locate(data, edit.package_id);
      if (!location) {
        return { ok: false, error: `package not found in any dependency section: ${edit.package_id}` };
      }
      // from_spec 校验：防止竞态覆盖
      if (edit.from_spec && location.currentSpec !== edit.from_spec) {
        return { ok: false, error: `from_spec mismatch for ${edit.package_id}: expected "${edit.from_spec}", found "${location.currentSpec}"` };
      }
      // F-03.2: to_spec must be a Registry version — reject URL/git/file sources
      const toSpec = edit.to_spec || '';
      if (toSpec.includes('://') || toSpec.startsWith('git+') || toSpec.startsWith('file:') || toSpec.startsWith('http')) {
        return { ok: false, error: `to_spec must be a Registry version, got: ${toSpec}` };
      }
      // F-03.2: to_spec must start with a digit or version range operator (^, ~, >=, etc.)
      if (!/^[\d~^>=<]/.test(toSpec)) {
        return { ok: false, error: `to_spec must start with a version or range operator, got: ${toSpec}` };
      }
      // V12: to_spec must contain at least one digit (reject bare ^, ~, >=, etc.)
      if (!/\d/.test(toSpec)) {
        return { ok: false, error: `to_spec must contain a version number, got: ${toSpec}` };
      }
      // V13: to_spec must contain at least major.minor or major.x/major.* (e.g. 4.17, >=4.17.21, ^4.x)
      const bareVersion = toSpec.replace(/^[~^>=<\s]+/, '').trim();
      if (!/^\d+\.[\d x *]/.test(bareVersion.replace(/\s/g, ''))) {
        return { ok: false, error: `to_spec must contain major.minor version, got: ${toSpec}` };
      }
      // V14: Reject to_spec containing shell metacharacters
      // Strip all valid version operators first (>=, <=, >, <, ~, ^) then check for dangerous chars
      const _stripped = toSpec.replace(/^[~^>=<]+/, '').replace(/>=/g, '').replace(/<=/g, '').replace(/>/g, '').replace(/</g, '');
      if (/[;&|`\n()<>!]/.test(_stripped)) {
        return { ok: false, error: `to_spec contains invalid characters, got: ${toSpec}` };
      }
      // V16: bareVersion must match npm semver-like pattern
      // Allows: 4.17, 4.17.21, 4.17.x, 4.x, 4.17.*, 4.17.21-pre, 4.17.21+build.1
      // Rejects: 4.17.21evil, 1.2.3.4, latest, tag names
      if (!/^\d+\.(\d+|x|\*)(?:\.(\d+|x|\*))?(?:-[a-zA-Z0-9.]+)?(?:\+[a-zA-Z0-9.]+)?$/.test(bareVersion)) {
        return { ok: false, error: `to_spec must be valid npm semver (e.g. 4.17.21, ^4.17.x), got: ${toSpec}` };
      }
      // F-03 v10: Major version compatibility check — to_spec should not introduce
      // a major version DOWNGRADE (e.g. 4.x → 3.x). Upgrades (0.x → 1.x, 4.x → 5.x) are allowed.
      // V11: Also reject ^0 / >=0 as target when source is >= 1 (downgrade to 0.x)
      const extractMajor = (spec) => {
        const m = (spec || '').match(/(\d+)/);
        return m ? parseInt(m[1], 10) : -1;
      };
      const fromMajor = extractMajor(edit.from_spec || location.currentSpec);
      const toMajor = extractMajor(toSpec);
      // Reject if source is >= 1 and target is lower (including 0.x)
      if (fromMajor >= 1 && toMajor >= 0 && toMajor < fromMajor) {
        return { ok: false, error: `to_spec major version downgrade: ${fromMajor}.x → ${toMajor}.x for ${edit.package_id}` };
      }
      // 应用修改
      data[location.section][edit.package_id] = edit.to_spec;
      appliedCount++;
    }
  
    // 渲染结果
    const rendered = render(data);
    if (rendered.length > MAX_OUTPUT_BYTES) {
      return { ok: false, error: 'output exceeds 1MB limit' };
    }
  
    // 验证修改后语法正确
    const validation = validate(content, rendered, edits);
    if (!validation.ok) {
      return { ok: false, error: `validation failed: ${validation.error}` };
    }
  
    return { ok: true, content: rendered, applied: appliedCount };
  }
  
  /**
   * 验证修改结果
   * - 修改后文件可被 JSON.parse
   * - 每个 edit 的 to_spec 已生效
   * - 非 edit 字段未被修改
   */
  function validate(originalContent, modifiedContent, edits) {
    const origParsed = parse(originalContent);
    const modParsed = parse(modifiedContent);
    if (!origParsed.ok) return { ok: false, error: 'original parse failed' };
    if (!modParsed.ok) return { ok: false, error: 'modified parse failed' };
  
    const orig = origParsed.data;
    const mod = modParsed.data;
  
    // 验证每个 edit 生效
    for (const edit of edits) {
      const loc = locate(mod, edit.package_id);
      if (!loc) return { ok: false, error: `package missing after apply: ${edit.package_id}` };
      if (loc.currentSpec !== edit.to_spec) {
        return { ok: false, error: `to_spec not applied for ${edit.package_id}: expected "${edit.to_spec}", got "${loc.currentSpec}"` };
      }
    }
  
    // 验证非依赖字段未被修改
    const FORBIDDEN_FIELDS = new Set(['scripts', 'repository', 'registry', 'config', 'name', 'version', 'private']);
    for (const field of FORBIDDEN_FIELDS) {
      if (JSON.stringify(orig[field]) !== JSON.stringify(mod[field])) {
        return { ok: false, error: `forbidden field modified: ${field}` };
      }
    }
  
    return { ok: true };
  }
  
  /**
   * 渲染 package.json（2 空格缩进，与 npm 默认一致）
   * @param {Object} data
   * @returns {string}
   */
  function render(data) {
    return JSON.stringify(data, null, 2) + '\n';
  }
  
  
  // Module exports
  __autofix_manifest_adapter_npm__.parse = parse;
  __autofix_manifest_adapter_npm__.locate = locate;
  __autofix_manifest_adapter_npm__.apply = apply;
  __autofix_manifest_adapter_npm__.validate = validate;
  __autofix_manifest_adapter_npm__.render = render;
})();


// ============================================================================
// Module: response
// ============================================================================

(function() {
  /**
   * Response Handler
   * 
   * 构造 Claude Code Hook 响应
   * 
   * 参考文档: https://code.claude.com/docs/en/hooks
   * 
   * PreToolUse Hook 输出格式:
   * {
   *   "systemMessage": "...",  // 顶级字段，显示给用户和 Claude
   *   "hookSpecificOutput": {
   *     "hookEventName": "PreToolUse",
   *     "permissionDecision": "allow" | "deny" | "ask",
   *     "permissionDecisionReason": "...",  // allow/ask 时显示给用户，deny 时显示给 Claude
   *     "updatedInput" / "modifiedInput": { ... },  // 可选：修改工具输入
   *     "additionalContext": "..."  // 可选：显示给 Claude 的上下文
   *   }
   * }
   */
  
  const getRiskLevel = __risk_policy__.getRiskLevel;
  const getMaxCvss = __risk_policy__.getMaxCvss;
  const findCrossMajorChanges = __version__.findCrossMajorChanges;
  const { createHash } = require('crypto');
  const { readFileSync, writeFileSync, existsSync } = require('fs');
  const { tmpdir } = require('os');
  const { join: pathJoin } = require('path');
  // V8-F05: consent.js imports removed — dead code after F-01 v3 ToC decision
  // (REVIEW_REQUIRED → deterministic allow+record, no consent cache needed)
  const applyManifestEdits = __autofix_manifest_adapter_npm__.apply;
  const isIdeClient = __parsers_input__.isIdeClient;
  
  function normalizeServerChanges(changes = []) {
    if (!Array.isArray(changes)) return [];
    return changes.map(change => ({
      from: change?.from ?? change?.f ?? '',
      to: change?.to ?? change?.t ?? '',
      cve: change?.cve ?? change?.c ?? null,
      cvss: change?.cvss ?? change?.s ?? null,
      reason: change?.reason ?? change?.r ?? null,
    }));
  }
  
  function normalizeUnfixablePackages(unfixable = []) {
    if (!Array.isArray(unfixable)) return [];
    return unfixable.map(pkg => ({
      n: pkg?.n ?? '',
      v: pkg?.v ?? '',
      reason: pkg?.reason ?? pkg?.r ?? null,
      cve: pkg?.cve ?? pkg?.c ?? null,
    }));
  }
  
  function normalizeLicenseInfo(licenseInfo = null) {
    if (!licenseInfo || typeof licenseInfo !== 'object') return null;
    const label = licenseInfo.name ?? licenseInfo.spdx_id ?? licenseInfo.n ?? licenseInfo.s ?? null;
    return {
      name: label,
      spdx_id: licenseInfo.spdx_id ?? licenseInfo.s ?? label,
      risk_level: licenseInfo.risk_level ?? licenseInfo.l ?? null,
      recommendation: licenseInfo.recommendation ?? licenseInfo.r ?? null,
      isolation_measures: licenseInfo.isolation_measures ?? licenseInfo.i ?? null,
      obligations: licenseInfo.obligations ?? licenseInfo.o ?? null,
    };
  }
  
  function normalizeRecommendedFix(recommendedFix = null) {
    if (!recommendedFix || typeof recommendedFix !== 'object') return null;
    return {
      constraint: recommendedFix.constraint ?? recommendedFix.c ?? null,
      reason: recommendedFix.reason ?? recommendedFix.r ?? null,
      policy: recommendedFix.policy ?? recommendedFix.p ?? null,
    };
  }
  
  function normalizeAgentInstruction(agentInstruction = null) {
    if (!agentInstruction || typeof agentInstruction !== 'object') return null;
    return {
      message: agentInstruction.message ?? agentInstruction.m ?? null,
      user_message: agentInstruction.user_message ?? agentInstruction.um ?? null,
      agent_message: agentInstruction.agent_message ?? agentInstruction.am ?? null,
    };
  }
  
  /**
   * D0-12（统一决策契约）—— 规范化 policy_result 字段
   *
   * Server 端在 License 路径上填充此字段（v1 仅 License 合规结果）。Client 优先
   * 读 policy_result.license_status 来驱动 ASK UX：
   *   - REVIEW_REQUIRED → buildLicenseReviewRecordResponse（真实灰名单，需要用户确认）
   *   - UNKNOWN / SOURCE_UNAVAILABLE → degraded fail-open（明确告知"未完成合规检查"，
   *     不是 silent PASS，避免"防护形同虚设"问题，见 D1-26 文档）
   *   - DENIED → 走原有 BLOCK+license deny 分支
   *   - ALLOWED → 走原有 PASS 分支
   *
   * 当 Server 未返回 policy_result（旧 Server 或非 License 场景），返回 null，
   * Client 回退读旧 license_info + hook_action。
   */
  function normalizePolicyResult(policyResult = null) {
    if (!policyResult || typeof policyResult !== 'object') return null;
    return {
      license_status:   policyResult.license_status ?? policyResult.ls ?? null,
      license_expressions: Array.isArray(policyResult.license_expressions ?? policyResult.le)
        ? (policyResult.license_expressions ?? policyResult.le)
        : null,
      source:           policyResult.source ?? policyResult.src ?? null,
      confidence:       policyResult.confidence ?? policyResult.conf ?? null,
      policy_version:   policyResult.policy_version ?? policyResult.pv ?? null,
    };
  }
  
  function normalizeServerResponse(serverResponse = {}) {
    return {
      ...serverResponse,
      fixed_content: serverResponse.fixed_content ?? serverResponse.fc ?? null,
      changes: normalizeServerChanges(serverResponse.changes ?? serverResponse.ch ?? []),
      unfixable: normalizeUnfixablePackages(serverResponse.unfixable ?? serverResponse.u ?? []),
      reason: serverResponse.reason ?? serverResponse.r ?? null,
      hook_action: serverResponse.hook_action ?? serverResponse.a ?? null,
      license_info: normalizeLicenseInfo(serverResponse.license_info ?? serverResponse.li ?? null),
      recommended_fix: normalizeRecommendedFix(serverResponse.recommended_fix ?? serverResponse.rf ?? null),
      fatal: serverResponse.fatal ?? serverResponse.f ?? false,
      agent_instruction: normalizeAgentInstruction(serverResponse.agent_instruction ?? serverResponse.ai ?? null),
      // D0-12：3 个新字段，优先读新字段（长名/短名），fallback 到旧字段（仅 decision）
      decision: serverResponse.decision ?? serverResponse.dec ?? serverResponse.s ?? null,
      reason_code: serverResponse.reason_code ?? serverResponse.rc ?? null,
      policy_result: normalizePolicyResult(serverResponse.policy_result ?? serverResponse.pr ?? null),
    };
  }
  
  function summarizeServerResponseForLog(serverResponse = {}) {
    const normalized = normalizeServerResponse(serverResponse);
    const summary = {
      s: normalized.s ?? 'UNKNOWN',
      t: normalized.t ?? 0,
    };
  
    if (normalized.reason) summary.r = normalized.reason;
    if (normalized.hook_action) summary.a = normalized.hook_action;
    if (normalized.fixed_content) summary.fc = `[${normalized.fixed_content.length} chars]`;
    if (normalized.changes?.length) summary.ch = normalized.changes.map(c => ({ f: c.from, t: c.to, c: c.cve ?? undefined, s: c.cvss ?? undefined }));
    if (normalized.unfixable?.length) summary.u = normalized.unfixable.map(pkg => ({ n: pkg.n, v: pkg.v, c: pkg.cve ?? undefined }));
    if (normalized.license_info?.spdx_id || normalized.license_info?.name) {
      summary.li = {
        n: normalized.license_info.spdx_id || normalized.license_info.name,
        l: normalized.license_info.risk_level || undefined,
      };
    }
    if (normalized.recommended_fix?.constraint) summary.rf = normalized.recommended_fix.constraint;
    if (normalized.fatal) summary.f = true;
    if (normalized.fail_open) summary.fo = true;
  
    return summary;
  }
  
  /**
   * 构造 Hook 响应
   *
   * @param {Object} serverResponse - Server 响应
   * @param {string} toolName - 工具名称
   * @param {Object} toolInput - 原始工具输入
   * @param {Object} context - 上下文信息
   * @returns {Object} Hook 响应
   */
  function buildHookResponse(serverResponse, toolName, toolInput, context) {
    const normalized = normalizeServerResponse(serverResponse);
    // D0-12：优先读 `decision`（Server v2+ 填充），fallback 到 `s`（normalizeServerResponse
    // 已经做了 fallback，所以这里 decision 一定有值——除非 Server 返回完全空响应）
    const { s: legacyStatus, decision, fixed_content, changes, unfixable, reason, reason_code, hook_action, license_info, recommended_fix, fatal, agent_instruction, policy_result } = normalized;
    const status = decision || legacyStatus;
    const ecosystem = context?.ecosystem || null;
    // IDE 环境使用 Markdown 格式，CLI 使用纯文本
    const isIDE = isIdeClient(context?.client);
  
    // PASS: 检查是否是降级操作（Edit/MultiEdit 从安全版本降级到漏洞版本）
    if (status === 'PASS') {
      if ((toolName === 'Edit' || toolName === 'MultiEdit') && context?.disk_packages) {
        const downgradeInfo = detectDowngrade(context.disk_packages, toolInput, context, serverResponse);
        if (downgradeInfo) {
          return buildDowngradeDenyResponse(downgradeInfo, isIDE);
        }
      }
      // F-07: If policy_result indicates UNKNOWN/SOURCE_UNAVAILABLE, don't show clean PASS
      const licenseStatus = policy_result?.license_status;
      if (licenseStatus === 'UNKNOWN' || licenseStatus === 'SOURCE_UNAVAILABLE') {
        return buildAllowResponse('license_check_degraded_fail_open', { sessionId: context?.session_id });
      }
      return buildAllowResponse(reason, { sessionId: context?.session_id });
    }
  
    // WARN: 检查是否是 license 警告 (灰名单: hook_action=ask)
    if (status === 'WARN') {
      // D0-12 + D1-26：优先读 policy_result.license_status 驱动 ASK UX
      // - REVIEW_REQUIRED → 真实灰名单，走 ask
      // - UNKNOWN / SOURCE_UNAVAILABLE → degraded fail-open（明确告知"未完成合规检查"）
      // - 其他/无 policy_result → 回退到旧 hook_action + license_info 判断
      if (policy_result?.license_status === 'REVIEW_REQUIRED') {
        return buildLicenseReviewRecordResponse(normalized, unfixable, ecosystem, isIDE, { sessionId: context?.session_id });
      }
      if (policy_result?.license_status === 'UNKNOWN' || policy_result?.license_status === 'SOURCE_UNAVAILABLE') {
        // degraded fail-open：不放行 silent PASS，而是 allow + 明确 readiness 信号
        // （复用 buildAllowResponse 的 fail-open 可见性机制，reason 标识未完成合规检查）
        return buildAllowResponse('license_check_unverified_fail_open', { sessionId: context?.session_id });
      }
      // 无 policy_result（旧 Server 或非 License WARN）→ 旧逻辑
      if (hook_action === 'ask' && license_info) {
        return buildLicenseReviewRecordResponse(normalized, unfixable, ecosystem, isIDE, { sessionId: context?.session_id });
      }
      return buildAllowResponse('security_warning', { sessionId: context?.session_id });
    }
  
    // O1-13 audit mode: 不因普通 CVE/License 阻断开发。
    // 降级 BLOCK → allow+记录，但保留 PACKAGE_NOT_FOUND（幻觉风险）和 fatal（熔断）的 deny。
    // 这是在安全防护形同虚设和过度阻断之间的折中——audit 模式用于记录但不阻断的
    // 观察/评估场景，不改变 smooth/strict 的行为。
    if (status === 'BLOCK' && context?.auditMode === true
        && reason_code !== 'PACKAGE_NOT_FOUND'
        && reason !== 'PACKAGE_NOT_FOUND'
        && !fatal) {
      return buildAllowResponse('audit_mode_recorded_allow', { sessionId: context?.session_id });
    }
  
    // BLOCK + hook_action=allow + fixed_content: 可修复场景
    if (status === 'BLOCK' && hook_action === 'allow' && fixed_content) {
      const riskConfig = context?.riskConfig || {};
      const riskLevel = getRiskLevel(changes, riskConfig);
      const maxCvssScore = getMaxCvss(changes);
      const disableAutofix = context?.disableAutofix || false;
  
      // P0-1（客户端侧纵深防御）：服务端已保证新版不返回跨 Major 的 fixed_content，
      // 但旧版服务端 / local-audit / 其他来源仍可能给出跨 Major 变更——客户端自己
      // 再判一次。命中则**绝不自动改写**，退回"人工确认"语义。
      // v1 恒定如此：即使 majorAutofix=true 也不解锁行为，只打 opted_in_pending
      // 标记（见 SECURITY_GUARD_ALLOW_MAJOR_AUTOFIX 说明），先观测真实诉求量。
      const crossMajorChanges = findCrossMajorChanges(changes);
      const crossMajorHit = crossMajorChanges.length > 0;
      const adviceMetadata = {
        recommended_fix,
        cross_major: crossMajorChanges,
      };
      const markMajorOptIn = (response) => {
        if (crossMajorHit && context?.majorAutofix === true && response?.hookSpecificOutput) {
          response.hookSpecificOutput.cross_major_opt_in = 'opted_in_pending';
        }
        return response;
      };
  
      // 全局开关 ON 且非跨 Major: 全部自动替换
      if (!disableAutofix && !crossMajorHit) {
        // F-03 v6: inject changes AND audited_packages into context
        const contextWithChanges = { ...context, changes };
        if (toolName !== 'Bash') {
          return buildAutofixResponse(toolName, toolInput, fixed_content, changes, contextWithChanges, { recommended_fix, agent_instruction });
        }
        return buildBashAutofixResponse(toolInput, fixed_content, changes, contextWithChanges, { recommended_fix, agent_instruction });
      }
  
      // 跨 Major（v1 恒定）或全局开关 OFF + 高危: deny + 告知用户 + 引导 Agent 知晓
      if (riskLevel === 'high') {
        return markMajorOptIn(
          buildHighRiskDenyResponse(changes, maxCvssScore, fixed_content, isIDE, adviceMetadata)
        );
      }
  
      // 跨 Major（v1 恒定）或全局开关 OFF + 中低危: 允许放行 + 展示修复建议
      return markMajorOptIn(
        buildAllowWithAdviceResponse(changes, fixed_content, isIDE, adviceMetadata)
      );
    }
  
    // BLOCK + fatal: 熔断，人类接管
    if (status === 'BLOCK' && fatal) {
      let userMsg = agent_instruction?.user_message || agent_instruction?.message || reason || 'Fatal security block';
      if (userMsg.startsWith('安全修复熔断：')) {
        userMsg = userMsg.slice('安全修复熔断：'.length);
      }
      const agentMsg = agent_instruction?.agent_message || agent_instruction?.message || reason || 'Stop autonomous retries and ask the human developer for help.';
  
      const formattedSystemMsg = userMsg.startsWith('需要人工处理：') ? userMsg : `需要人工处理：${userMsg}`;
      const formattedDenyReason = userMsg.startsWith('🚫 熔断拦截：') ? userMsg : `🚫 熔断拦截：${userMsg}`;
  
      return {
        continue: false,
        suppressOutput: false,
        systemMessage: `${formattedSystemMsg}（反馈:@selinasong）`,
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: formattedDenyReason,
          additionalContext: agentMsg
        }
      };
    }
  
    // BLOCK + license violation (黑名单: hook_action=deny + license_info)
    // D0-12：也检查 policy_result.license_status === 'DENIED' 作为等价信号
    if (status === 'BLOCK' && hook_action === 'deny' && (license_info || policy_result?.license_status === 'DENIED')) {
      return buildLicenseDenyResponse(normalized, unfixable, toolName === 'Bash' ? context.command : null, ecosystem, isIDE);
    }
  
    // BLOCK + hook_action=deny (兜底: 包不存在/不可修复/Bash 风险等)
    if (status === 'BLOCK') {
      return buildDenyResponse(unfixable || [], toolName === 'Bash' ? context.command : null, isIDE, {
        changes, fixed_content, recommended_fix, reason, reason_code, agent_instruction
      });
    }
  
    // 未知状态: 放行 (Fail-Open)
    return buildAllowResponse('unknown_status_fail_open', { sessionId: context?.session_id });
  }
  
  /**
   * 检测是否是降级操作（从安全版本降级到漏洞版本）
   *
   * 降级检测逻辑：
   * 1. 磁盘上有安全版本（如 Django>=4.3.4）
   * 2. 用户尝试改为漏洞版本（如 Django==4.2.7）
   * 3. 检查是否有之前 Hook 修复的记录（通过 /tmp/security-guard-fix-info.json）
   *
   * @param {Array} diskPackages - 磁盘上的依赖列表
   * @param {Object} toolInput - 工具输入
   * @param {Object} context - 上下文信息
   * @param {Object} serverResponse - 服务器响应（包含之前的修复记录）
   * @returns {Object|null} 降级信息，如果不是降级返回 null
   */
  function detectDowngrade(diskPackages, toolInput, context, serverResponse) {
    if (!diskPackages || diskPackages.length === 0) {
      return null;
    }
  
    // 尝试读取之前 Hook 保存的修复信息（跨操作查询：这里要找的是"最近一次
    // 针对该文件的 autofix"，而不是本次操作自身的 fix info，因此不能按
    // tool_use_id/call_id 精确匹配，而是在候选文件里找时间最新且未过期的一个）
    //
    // 背景（D1-19）：此前 PreToolUse/PostToolUse 共用固定单一文件
    // `/tmp/security-guard-fix-info.json`，本函数原本直接读这个固定路径。
    // D1-19 修复把 PreToolUse 写入路径改为按 tool_use_id/call_id 派生的独立
    // 文件（见 src/index.js 的 getFixInfoPath()），如果这里仍然读旧的固定路径，
    // 会永远读不到数据，导致"降级检测"功能被静默破坏。现改为扫描新的命名模式
    // （security-guard-fix-info-*.json），取其中最新修改的一个作为"最近一次修复"。
    let previousFixInfo = null;
    try {
      const fs = require('node:fs');
      const os = require('node:os');
      const path = require('node:path');
      const dir = os.tmpdir();
      const prefix = 'security-guard-fix-info-';
      const candidates = fs.readdirSync(dir)
        .filter(name => name.startsWith(prefix) && name.endsWith('.json'))
        .map(name => {
          const fullPath = path.join(dir, name);
          try {
            return { fullPath, mtimeMs: fs.statSync(fullPath).mtimeMs };
          } catch {
            return null;
          }
        })
        .filter(Boolean)
        .sort((a, b) => b.mtimeMs - a.mtimeMs);
  
      if (candidates.length > 0) {
        const content = fs.readFileSync(candidates[0].fullPath, 'utf-8');
        previousFixInfo = JSON.parse(content);
      }
    } catch {
      // 忽略读取错误（目录不存在、权限问题等），降级检测本身允许 fail-open
    }
  
    // 从 toolInput 中解析 old_str 和 new_str
    const oldStr = toolInput.old_string || toolInput.old_str || '';
    const newStr = toolInput.new_string || toolInput.new_str || '';
  
    if (!oldStr || !newStr) {
      return null;
    }
  
    // 检查磁盘上的包是否被改成了漏洞版本
    const downgradePackages = [];
  
    for (const diskPkg of diskPackages) {
      const pkgName = diskPkg.n;
  
      // 构建 old_str 和 new_str 中的包版本匹配模式
      const oldPkgPattern = new RegExp(`${escapeRegExp(pkgName)}[=<>~!]*([\\d.]+[\\w.]*)`, 'i');
      const newPkgPattern = new RegExp(`${escapeRegExp(pkgName)}[=<>~!]*([\\d.]+[\\w.]*)`, 'i');
  
      const oldMatch = oldStr.match(oldPkgPattern);
      const newMatch = newStr.match(newPkgPattern);
  
      if (oldMatch && newMatch) {
        const oldVersion = oldMatch[1];
        const newVersion = newMatch[1];
  
        // 检查这个包是否是之前 Hook 修复过的
        const wasFixedByHook = previousFixInfo?.changes?.some(c => {
          const changeFrom = c.from || '';
          const changeTo = c.to || '';
          return changeFrom.includes(pkgName) && changeTo.includes(pkgName);
        });
  
        // 如果是 Hook 修复过的包，且新版本与原始漏洞版本相同，则是降级操作
        if (wasFixedByHook) {
          const originalVulnerableVersion = previousFixInfo.changes.find(c => c.from?.includes(pkgName))?.from;
          const originalVulnerableVer = extractVersionFromStr(originalVulnerableVersion || '', pkgName);
  
          if (newVersion === originalVulnerableVer || newStr.includes('==') && newStr.includes(newVersion)) {
            downgradePackages.push({
              name: pkgName,
              diskVersion: oldVersion,
              targetVersion: newVersion,
              originalVulnerableVersion: originalVulnerableVer,
              reason: '尝试将 Hook 修复的安全版本降级到原始漏洞版本'
            });
          }
        }
      }
    }
  
    if (downgradePackages.length > 0) {
      return {
        packages: downgradePackages,
        oldStr: oldStr,
        newStr: newStr
      };
    }
  
    return null;
  }
  
  /**
   * 转义正则表达式特殊字符
   *
   * @param {string} str - 原始字符串
   * @returns {string} 转义后的字符串
   */
  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  
  /**
   * 从字符串中提取包版本
   *
   * @param {string} str - 字符串
   * @param {string} pkgName - 包名
   * @returns {string} 版本号
   */
  function extractVersionFromStr(str, pkgName) {
    const pattern = new RegExp(`${pkgName}[=<>~!]+([\\d.]+)`, 'i');
    const match = str.match(pattern);
    return match ? match[1] : 'unknown';
  }
  
  /**
   * 构造降级阻止响应
   *
   * @param {Object} downgradeInfo - 降级信息
   * @param {boolean} isIDE - 是否是 IDE 环境
   * @returns {Object} Hook 响应
   */
  function buildDowngradeDenyResponse(downgradeInfo, isIDE) {
    const packages = downgradeInfo.packages;
    let reasonText;
  
    if (isIDE) {
      // IDE 确认弹窗：纯文本格式
      const pkgLines = packages.map(pkg =>
        `  - ${pkg.name}: ${pkg.diskVersion} → ${pkg.targetVersion} (${pkg.reason})`
      ).join('\n');
      reasonText = `🚫 安全降级拦截\n\n检测到尝试将安全版本降级到漏洞版本：\n${pkgLines}\n\n请保持安全版本，不要尝试降级。`;
    } else {
      // CLI: 纯文本
      const pkgList = packages.map(pkg => `${pkg.name}: ${pkg.diskVersion} → ${pkg.targetVersion}`).join(', ');
      reasonText = `🚫 安全降级拦截: 检测到尝试将安全版本降级到漏洞版本 (${pkgList})。请保持安全版本。`;
    }
  
    return {
      continue: false,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reasonText
      }
    };
  }
  
  /**
   * D1-15 修复：判断一个 fail-open reason 字符串是否代表"审计本身没有真正完成"
   * （超时/网络错误/网关鉴权失败/证书错误等），而不是"审计完成且确认安全"。
   *
   * 背景：`buildAllowResponse` 此前对"真实 PASS"和"fail-open 放行"一视同仁地
   * 使用 `suppressOutput: true` 完全静默处理，用户/研发无法区分"这次真的做了
   * 安全检查且通过了"和"这次安全检查本身失败/超时，只是保守放行"——后者意味着
   * 插件在这次操作上完全没有提供保护，运营数据也可能把它误统计为"检查通过"。
   *
   * 命名约定见 client.js::createFailOpenResponse 和 index.js 各处 skip_reason：
   * 所有 fail-open 原因字符串统一以 `_fail_open` 结尾。
   */
  // D1-14 复用：dedup.js 需要判断某个 reason 是否是 fail-open（fail-open 不走
  // "相同输入重复"语义的去重，而是 D1-15 独立的健康↔降级状态切换语义），因此
  // 导出这个已有判断，避免在两处分别维护"以 `_fail_open` 结尾"这条规则。
  function isFailOpenReason(reason) {
    return typeof reason === 'string' && reason.endsWith('_fail_open');
  }
  
  /**
   * D1-15 修复：同一会话内，fail-open 提示只显示一次（状态变化时提示，持续同一
   * 状态时保持安静），避免网络持续不稳定时每次操作都弹一遍提示造成骚扰。
   *
   * 用会话级临时状态文件实现（与 D1-19 的 fix-info 隔离机制同构：按 session_id
   * 派生独立文件，不使用固定全局路径）。文件不存在或读取失败时保守地当作
   * "本会话尚未提示过"，允许提示一次——宁可稍微多提示，不可因为状态文件问题
   * 导致用户永远看不到任何 fail-open 信号。
   *
   * @param {string|null} sessionId
   * @param {boolean} currentlyFailOpen - 本次请求是否处于 fail-open 状态
   * @returns {boolean} 是否应该在本次响应中显示提示
   */
  function shouldShowFailOpenNotice(sessionId, currentlyFailOpen) {
    if (!sessionId) {
      // 无 session_id 时无法去重，每次都提示——比"因为没有 session_id 就永远
      // 不提示"更安全，也是唯一符合"宁可多提示"原则的选择
      return currentlyFailOpen;
    }
  
    try {
      const safeKey = String(sessionId).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 128);
      const statePath = pathJoin(tmpdir(), `security-guard-readiness-${safeKey}.json`);
  
      let previousState = null;
      try {
        previousState = JSON.parse(readFileSync(statePath, 'utf-8'));
      } catch {
        // 文件不存在（本会话第一次请求）或损坏，视为"之前是健康状态"
        previousState = { failOpen: false };
      }
  
      // 写回本次状态，供下一次请求比较（fail-open 用 mode 0o600，内容极简，
      // 不含任何请求内容/凭证，符合文档"/status 输出约束"的最小化原则）
      try {
        writeFileSync(statePath, JSON.stringify({ failOpen: currentlyFailOpen, ts: Date.now() }), { mode: 0o600 });
      } catch {
        // 写入失败不影响本次判断结果，只是下次可能重新提示一次
      }
  
      // 只在"状态发生变化"时提示：healthy→degraded 或 degraded→healthy 都提示一次；
      // 持续 degraded（前后都是 fail-open）保持安静，避免刷屏
      return currentlyFailOpen !== previousState.failOpen;
    } catch {
      // 任何异常都不应阻塞主流程；保守选择"提示"而不是"永久安静"
      return currentlyFailOpen;
    }
  }
  
  /**
   * 构造 Allow 响应
   * 
   * @param {string} reason - 原因（显示给用户，不显示给 Claude）
   * @param {Object} [options] - 可选项
   * @param {string|null} [options.sessionId] - 当前会话 ID，用于 fail-open 提示去重
   * @returns {Object} Hook 响应
   */
  function buildAllowResponse(reason = null, options = {}) {
    const response = {
      continue: true,
      suppressOutput: true,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'allow'
      }
    };
    
    if (reason) {
      response.hookSpecificOutput.permissionDecisionReason = reason;
    }
  
    // D1-15: fail-open（审计未真正完成，保守放行）时，在状态发生变化的这一次
    // 打破静默，用最小化的一句话让用户知道"这次插件没能提供保护"，而不是让
    // 所有 allow 场景（无论是否真的做了检查）都表现为完全一致的静默通过
    const failOpen = isFailOpenReason(reason);
    if (failOpen && shouldShowFailOpenNotice(options.sessionId, true)) {
      response.suppressOutput = false;
      response.systemMessage = '⚠️ 安全检查本次未能完成（网络/服务异常），已放行但未确认安全性。';
    } else if (!failOpen) {
      // 从 degraded 恢复到正常状态时，同样提示一次（"之前失败，现在恢复了"）
      if (shouldShowFailOpenNotice(options.sessionId, false)) {
        response.suppressOutput = false;
        response.systemMessage = '✅ 安全检查已恢复正常。';
      }
    }
    
    return response;
  }
  
  function summarizeChangeSet(changes = [], maxItems = 2) {
    if (!Array.isArray(changes) || changes.length === 0) return '';
  
    // 附带 CVE 编号（若有），让 deny/warn 原因对用户/Agent 可解释——早期版本
    // (commit d99a639) 曾在 changeLines 中包含 CVE + CVSS 明细，后续精简
    // systemMessage 格式时（commit db65585）复用了不含 CVE 的短格式，导致
    // 具体是"哪个 CVE"这一关键信息从用户可见文案中完全消失
    const items = changes.slice(0, maxItems).map(change => {
      const label = `${change.from} → ${change.to}`;
      return change.cve ? `${label} (${change.cve})` : label;
    });
    if (changes.length > maxItems) {
      items.push(`等${changes.length}项`);
    }
    return items.join('；');
  }
  
  function summarizePackageSet(packages = [], maxItems = 2) {
    if (!Array.isArray(packages) || packages.length === 0) return '';
  
    // 附带 CVE 编号（若有），让 deny 原因对用户/Agent 可解释——此前只展示
    // 包名@版本，CVE 信息完全丢失，用户无法判断这次拦截具体对应哪个已知漏洞
    const items = packages.slice(0, maxItems).map(pkg => {
      const label = `${pkg.n}@${pkg.v}`;
      return pkg.cve ? `${label} (${pkg.cve})` : label;
    });
    if (packages.length > maxItems) {
      items.push(`等${packages.length}个`);
    }
    return items.join('、');
  }
  
  function buildRecommendedFixNote(recommendedFix = null) {
    if (!recommendedFix?.constraint) return '';
    return recommendedFix?.reason
      ? `推荐版本：${recommendedFix.constraint}（${recommendedFix.reason}）`
      : `推荐版本：${recommendedFix.constraint}`;
  }
  
  /**
   * 跨 Major 提示文案（P0-1 客户端侧纵深防御，用户可见面）
   *
   * 只在确实判定出跨 Major 变更时返回文案；判定不确定时 findCrossMajorChanges()
   * 返回空数组，这里也返回空串——不制造噪声、不制造假安全感（见 src/version.js
   * 顶部关于"误判代价"的约束）。
   *
   * @param {Array} crossMajorChanges - findCrossMajorChanges() 的产出
   * @returns {string} 中文提示文案；无跨 Major 时为 ''
   */
  function buildCrossMajorNote(crossMajorChanges = []) {
    if (!Array.isArray(crossMajorChanges) || crossMajorChanges.length === 0) return '';
    const pairs = crossMajorChanges
      .slice(0, 2)
      .map(c => `${c?.from || '?'} → ${c?.to || '?'}`)
      .join('、');
    return `⚠️ 跨 Major 升级（${pairs}）可能存在不兼容变更，需人工确认，本次未自动替换。`;
  }
  
  /**
   * 跨 Major 提示文案（Agent 可见面，英文指令式）
   *
   * 与 buildCrossMajorNote() 同源同阈值，只是面向 Agent 用英文明确"不要自动改写"。
   *
   * @param {Array} crossMajorChanges - findCrossMajorChanges() 的产出
   * @returns {string} 英文提示文案；无跨 Major 时为 ''
   */
  function buildCrossMajorAgentNote(crossMajorChanges = []) {
    if (!Array.isArray(crossMajorChanges) || crossMajorChanges.length === 0) return '';
    const pairs = crossMajorChanges
      .slice(0, 2)
      .map(c => `${c?.from || '?'} -> ${c?.to || '?'}`)
      .join(', ');
    return `CROSS_MAJOR_CHECKPOINT: ${pairs} crosses a major version boundary (possible breaking change); autofix withheld — do not rewrite the input, ask the human developer to confirm.`;
  }
  
  /**
   * 构造 License Ask 响应 (灰名单许可证，需用户确认)
   *
   * O1-16（一次确认子集）：Claude Code Hook 协议里 `ask` 由 CLI 弹窗询问人类
   * 用户，Hook 进程收不到"用户是否真的点了允许"这个反馈——此前同一批组件 +
   * 同一许可证在同一会话内重复出现时会一遍遍重复弹窗。现在先计算 consent-key
   * （组件+版本+许可证），若本会话内已经展示过完全相同的事实（TTL 内），直接
   * 复用 buildAllowResponse() 视为已确认，不再重复打断；否则正常展示 ask 并
   * 记录"已经问过一次"。deny 相关路径完全不引用这个机制（结构上不会碰到）。
   *
   * @param {Object} serverResponse - 服务器响应
   * @param {Array} unfixable - 无法修复的包列表
   * @param {string} ecosystem - 生态系统
   * @param {boolean} isIDE - 是否为 IDE 环境
   * @param {Object} [options] - 可选项
   * @param {string|null} [options.sessionId] - 当前会话 ID，用于一次确认缓存
   * @returns {Object} Hook 响应
   */
  function buildLicenseReviewRecordResponse(serverResponse, unfixable = [], ecosystem = null, isIDE = false, options = {}) {
    const { license_info } = serverResponse;
    const licenseName = license_info ? (license_info.name || license_info.spdx_id || '未知许可证') : '未知许可证';
    const riskLevel = license_info?.risk_level ? ` (${license_info.risk_level})` : '';
    const pkgSummary = summarizePackageSet(unfixable);
    const recommendation = license_info?.recommendation || '请确认是否允许继续使用该组件。';
  
    // V8-F05: Removed dead consent cache code (computeLicenseConsentKey/hasValidConsent/recordConsentShown)
    // F-01 v3 (ToC final decision): REVIEW_REQUIRED maps to allow + record,
    // NOT ask. Hook protocol can't receive user click result, so ASK creates
    // an uncloseable loop. Deterministic mapping per ToC:
    //   ALLOWED → allow
    //   DENIED → deny (handled by buildLicenseDenyResponse elsewhere)
    //   REVIEW_REQUIRED → allow + record (here)
    //   UNKNOWN/SOURCE_UNAVAILABLE → degraded allow (handled elsewhere)
    const reasonText = `⚠️ License 审核记录：${pkgSummary || '当前组件'} 使用 ${licenseName}${riskLevel}。${recommendation}`;
    const response = {
      continue: true,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'allow',
        permissionDecisionReason: reasonText,
      }
    };
  
    response.systemMessage = `License 风险记录：${pkgSummary || '当前组件'} 使用 ${licenseName}。${recommendation}`;
  
    const claudeContext = buildLicenseLookupContext(unfixable, license_info, ecosystem);
    if (claudeContext) {
      response.hookSpecificOutput.additionalContext = claudeContext;
    }
  
    // F-01 v3: No consent tracking — deterministic allow+record per ToC
    return response;
  }
  
  /**
   * 构造 License Deny 响应 (黑名单许可证，禁止使用)
   * 
   * @param {Object} serverResponse - 服务器响应
   * @param {Array} unfixable - 无法修复的包列表
   * @param {string} command - 被拒绝的命令（可选）
   * @returns {Object} Hook 响应
   */
  function buildLicenseDenyResponse(serverResponse, unfixable = [], command = null, ecosystem = null, isIDE = false) {
    const { license_info } = serverResponse;
    const licenseName = license_info ? (license_info.name || license_info.spdx_id || '未知许可证') : '未知许可证';
    const riskLevel = license_info?.risk_level ? ` (${license_info.risk_level})` : '';
    const pkgSummary = summarizePackageSet(unfixable);
    const recommendation = license_info?.recommendation || '请改用兼容商用的替代组件。';
  
    const reasonText = command
      ? `🚫 License 合规拦截：命令包含 ${licenseName}${riskLevel} 许可证依赖。${recommendation}`
      : `🚫 License 合规拦截：${pkgSummary || '当前组件'} 使用 ${licenseName}${riskLevel}。${recommendation}`;
  
    const response = {
      continue: false,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reasonText
      }
    };
  
    response.systemMessage = `License 不兼容商用：${pkgSummary || '当前组件'} 使用 ${licenseName}。${recommendation}`;
  
    const claudeContext = buildLicenseLookupContext(unfixable, license_info, ecosystem);
    if (claudeContext) {
      response.hookSpecificOutput.additionalContext = claudeContext;
    }
  
    return response;
  }
  
  /**
   * 构建 License 查询上下文（additionalContext）
   * 
   * 引导 Claude 主动查询组件的真实 license 信息，用于 license 拦截/警告场景。
   * 
   * @param {Array} unfixable - 受影响的包列表 [{n, v}, ...]
   * @param {Object} license_info - license 信息（可能包含 spdx_id、name、risk_level 等）
   * @param {string} ecosystem - 生态系统（npm / pypi / cargo / go / maven / rubygems）
   * @returns {string|null} additionalContext 文本
   */
  function buildLicenseLookupContext(unfixable = [], license_info = null, ecosystem = null) {
    if (!unfixable || unfixable.length === 0) return null;
  
    const licenseLabel = license_info
      ? (license_info.spdx_id || license_info.name || 'unknown')
      : 'unknown';
    const pkgSummary = summarizePackageSet(unfixable, 3);
    const ecosystemLabel = ecosystem || 'registry';
  
    return `[License Block] ${pkgSummary} 使用 ${licenseLabel}。不要重试原组件；请先核实 ${ecosystemLabel} 中的真实 license，再寻找可商用替代组件（MIT/Apache-2.0/BSD）。`;
  }
  
  /**
   * 构造 Deny 响应
   * 
   * @param {Array} unfixable - 无法修复的包列表
   * @param {string} command - 被拒绝的命令（可选）
   * @returns {Object} Hook 响应
   */
  function buildDenyResponse(unfixable, command = null, isIDE = false, metadata = {}) {
    const { changes, fixed_content, recommended_fix, reason, reason_code } = metadata;
    const pkgSummary = summarizePackageSet(unfixable);
    const changeSummary = summarizeChangeSet(changes);
    const recommendedNote = buildRecommendedFixNote(recommended_fix);
    const safeTarget = typeof fixed_content === 'string' ? fixed_content.trim() : '';
    const firstUnfixableReason = Array.isArray(unfixable)
      ? (unfixable.find(pkg => pkg?.reason)?.reason || '')
      : '';
    let reasonText;
  
    // D0-12：优先读 reason_code（新字段），fallback 到 reason（旧字段）
    if (reason_code === 'PACKAGE_NOT_FOUND' || reason === 'PACKAGE_NOT_FOUND') {
      const missingSummary = pkgSummary || '当前组件';
      reasonText = command
        ? `🚫 组件不存在：命令中的 ${missingSummary} 未在注册表中找到。请先核实包名或版本，不要直接重试。`
        : `🚫 组件不存在：${missingSummary} 未在注册表中找到。请检查包名或版本，可能是 AI 幻觉或拼写错误。`;
  
      return {
        continue: false,
        systemMessage: firstUnfixableReason || `已阻止写入：${missingSummary} 未在注册表中找到。请检查包名或版本。`,
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: reasonText
        }
      };
    }
  
    if (pkgSummary) {
      reasonText = command
        ? `🚫 安全拦截：命令包含不安全依赖 ${pkgSummary}。请改用安全版本。`
        : `🚫 安全拦截：${pkgSummary} 存在已知漏洞。请改用安全版本。`;
    } else if (changeSummary) {
      reasonText = command
        ? `🚫 安全拦截：命令包含漏洞依赖 ${changeSummary}。请改用安全版本。`
        : `🚫 安全拦截：检测到漏洞依赖 ${changeSummary}。请改用安全版本。`;
    } else {
      reasonText = command
        ? '🚫 安全拦截：命令包含不安全依赖，请使用安全版本。'
        : '🚫 安全拦截：检测到不安全依赖，请使用安全版本。';
    }
  
    const response = {
      continue: false,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reasonText
      }
    };
  
    const agentContext = metadata?.agent_instruction?.agent_message || metadata?.agent_instruction?.message;
    if (agentContext) {
      response.hookSpecificOutput.additionalContext = agentContext;
    }
  
    const systemParts = ['已阻止不安全依赖写入。'];
    if (safeTarget) systemParts.push(`安全版本：${safeTarget}`);
    if (recommendedNote && recommended_fix?.constraint !== fixed_content) systemParts.push(recommendedNote);
    response.systemMessage = systemParts.join(' ');
  
    return response;
  }
  
  /**
   * 构造开关 OFF 时的拦截响应：deny + 修复建议展示
   *
   * 不篡改任何内容，只告诉研发和 Agent 应该用什么版本。
   * 根据 CVSS 分级调整提示强度（🔴🟠🟡）。
   *
   * @param {Array}  changes       - 变更列表 [{from, to, cve, cvss}, ...]
   * @param {number} maxCvssScore  - 最高 CVSS 分数
   * @param {string} fixedContent  - 修复后内容
   * @param {boolean} isIDE        - 是否为 IDE 环境
   * @param {Object} metadata      - 元数据 (security_autofix, recommended_fix)
   * @returns {Object} Hook 响应
   */
  function buildBlockWithAdviceResponse(changes, maxCvssScore, fixedContent, isIDE, metadata = {}) {
    const safeChanges = changes || [];
    const icon = getSeverityIcon(maxCvssScore);
    const changeSummary = summarizeChangeSet(changes);
    const recommendedNote = buildRecommendedFixNote(metadata?.recommended_fix);
    const fixedTarget = typeof fixedContent === 'string' ? fixedContent.trim() : '';
    const reasonText = `${icon} 安全拦截：自动修复已关闭，${changeSummary || '检测到漏洞依赖'}。本次仅阻断并提示，请先由用户确认，不要直接改写为建议版本。`;
  
    // IDE 使用 Markdown 表格展示变更明细，CLI 使用纯文本行
    let systemMsg;
    if (isIDE) {
      const lines = [
        `## ${icon} 安全漏洞拦截（自动修复已关闭）`,
        '',
        '检测到安全漏洞，已阻止原始操作：',
        '',
        '| 原始版本 | 建议版本 | CVE | CVSS |',
        '|---------|---------|-----|------|',
      ];
      for (const c of safeChanges) {
        const cve = c.cve ? `**${c.cve}**` : '—';
        const cvss = typeof c.cvss === 'number' ? `${getSeverityIcon(c.cvss)} ${c.cvss.toFixed(1)}` : 'N/A';
        lines.push(`| \`${c.from}\` | \`${c.to}\` | ${cve} | ${cvss} |`);
      }
      lines.push('');
      lines.push(`**可参考安全版本**: \`${fixedTarget}\``);
      if (recommendedNote && metadata?.recommended_fix?.constraint !== fixedContent) {
        lines.push(`**${recommendedNote}**`);
      }
      lines.push('如需升级请先由用户确认。');
      systemMsg = lines.join('\n');
    } else {
      const systemParts = ['自动修复已关闭，已阻止原始操作。'];
      if (fixedTarget) systemParts.push(`可参考安全版本：${fixedTarget}`);
      if (recommendedNote && metadata?.recommended_fix?.constraint !== fixedContent) {
        systemParts.push(recommendedNote);
      }
      systemParts.push('如需升级请先由用户确认。');
      systemMsg = systemParts.join(' ');
    }
  
    // 引导 Agent：明确告知不要自行重试改写为建议版本，需等待用户确认
    const claudeContext = `SECURITY_BLOCK_ADVICE_ONLY: Autofix is disabled (DISABLE_AUTOFIX). ${changeSummary || 'Vulnerable dependency detected'}. Suggested safe version: ${fixedTarget}. Do NOT retry by rewriting to the suggested version yourself — wait for explicit user confirmation first.`;
  
    return {
      continue: false,
      suppressOutput: false,
      systemMessage: systemMsg,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reasonText,
        additionalContext: claudeContext
      }
    };
  }
  
  /**
   * 构造开关 OFF + 高危时的拦截响应：deny + 告知用户 + 引导 Agent 知晓
   *
   * @param {Array}  changes       - 变更列表 [{from, to, cve, cvss}, ...]
   * @param {number} maxCvssScore  - 最高 CVSS 分数
   * @param {string} fixedContent  - 修复后内容（最小爆炸半径）
   * @param {boolean} isIDE        - 是否为 IDE 环境
   * @param {Object} metadata      - 元数据 (recommended_fix)
   * @returns {Object} Hook 响应
   */
  function buildHighRiskDenyResponse(changes, maxCvssScore, fixedContent, isIDE, metadata = {}) {
    const cvssDisplay = (typeof maxCvssScore === 'number' && !isNaN(maxCvssScore))
      ? maxCvssScore.toFixed(1)
      : 'N/A';
    const changeSummary = summarizeChangeSet(changes);
    const recommendedNote = buildRecommendedFixNote(metadata?.recommended_fix);
    // P0-1：仅当本次确实判定出跨 Major 变更时才追加提示（空数组 → 空串，不产生噪声）
    const crossMajorNote = buildCrossMajorNote(metadata?.cross_major);
    const crossMajorAgentNote = buildCrossMajorAgentNote(metadata?.cross_major);
  
    // 告知用户：清晰的风险说明和安全版本
    const reasonText = fixedContent
      ? `🔴 高危漏洞拦截（CVSS ${cvssDisplay}）：${changeSummary || '检测到高危漏洞依赖'}。请改用安全版本 ${fixedContent} 后重试。`
      : `🔴 高危漏洞拦截（CVSS ${cvssDisplay}）：${changeSummary || '检测到高危漏洞依赖'}。请升级到安全版本后重试。`;
  
    const systemParts = [
      `⚠️ 已阻止高危漏洞依赖写入（CVSS ${cvssDisplay}）`,
      `变更：${changeSummary}`,
    ];
    if (fixedContent) {
      systemParts.push(`最小安全版本：${fixedContent}`);
    }
    if (recommendedNote && metadata?.recommended_fix?.constraint !== fixedContent) {
      systemParts.push(`推荐版本：${metadata.recommended_fix.constraint} (${metadata.recommended_fix.reason || 'LTS'})`);
    }
    systemParts.push('自动替换已关闭，请手动升级到安全版本。');
    if (crossMajorNote) systemParts.push(crossMajorNote);
  
    // 兼容性提示（来自服务端，如主版本升级可能存在的 API 变更提示），仅当有内容时展示
    // 此功能曾在 commit d99a639 实现，后续精简 systemMessage 格式时（commit db65585）
    // 被意外一并移除，现恢复
    const hints = metadata?.compatibility_hints;
    if (hints && hints.length > 0) {
      systemParts.push('⚠️ 兼容性提示:');
      for (const hint of hints) systemParts.push(`  ${hint}`);
    }
  
    // 引导 Agent 知晓：英文上下文，引导后续行为
    const claudeContext = `HIGH_RISK_VULNERABILITY_BLOCKED: CVSS ${cvssDisplay}. ${changeSummary}. Minimum safe version: ${fixedContent}. Autofix is disabled. Please inform the user and ask for confirmation before retrying with the safe version. In your response to the user, you MUST prominently display this vulnerability interception warning with CVE IDs, CVSS score, and the recommended safe version.`
      + (crossMajorAgentNote ? ` ${crossMajorAgentNote}` : '');
  
    return {
      continue: false,
      suppressOutput: false,
      systemMessage: systemParts.join('\n'),
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reasonText,
        additionalContext: claudeContext
      }
    };
  }
  
  /**
   * 构造开关 OFF + 中低危时的放行响应：allow + 展示修复建议
   *
   * 不阻止操作，但告知用户存在漏洞，建议升级。
   *
   * @param {Array}  changes       - 变更列表 [{from, to, cve, cvss}, ...]
   * @param {string} fixedContent  - 修复后内容
   * @param {boolean} isIDE        - 是否为 IDE 环境
   * @param {Object} metadata      - 元数据 (recommended_fix)
   * @returns {Object} Hook 响应
   */
  function buildAllowWithAdviceResponse(changes, fixedContent, isIDE, metadata = {}) {
    const changeSummary = summarizeChangeSet(changes);
    const recommendedNote = buildRecommendedFixNote(metadata?.recommended_fix);
    const fixedTarget = typeof fixedContent === 'string' ? fixedContent.trim() : '';
    // P0-1：同上，只在确实判定出跨 Major 变更时追加提示
    const crossMajorNote = buildCrossMajorNote(metadata?.cross_major);
    const crossMajorAgentNote = buildCrossMajorAgentNote(metadata?.cross_major);
  
    const reasonText = `🟡 检测到漏洞依赖：${changeSummary}。建议升级到 ${fixedContent}。`;
  
    const systemParts = [`检测到漏洞依赖，已放行。`];
    if (fixedTarget) systemParts.push(`建议升级到：${fixedTarget}`);
    if (recommendedNote && metadata?.recommended_fix?.constraint !== fixedContent) {
      systemParts.push(`推荐版本：${metadata.recommended_fix.constraint} (${metadata.recommended_fix.reason || 'LTS'})`);
    }
    systemParts.push('高危漏洞自动替换已关闭，建议手动升级。');
    if (crossMajorNote) systemParts.push(crossMajorNote);
  
    // agent 面上下文：仅以指令式文本引导 agent 手动改为安全版本，绝不补
    // updatedInput/modifiedInput（守住 disableAutofix=true 的"不自动改写用户输入"契约）。
    const safeConstraint = metadata?.recommended_fix?.constraint || fixedTarget;
    const cveList = (Array.isArray(changes) ? changes : [])
      .map(c => c?.cve)
      .filter(Boolean);
    const uniqueCves = Array.from(new Set(cveList));
    const claudeContext =
      `SECURITY_ADVICE_ONLY (autofix disabled): 检测到漏洞依赖 ${changeSummary}` +
      (uniqueCves.length ? `（${uniqueCves.join(', ')}）` : '') +
      `。当前为严格/审计模式，自动替换已关闭，请勿保留漏洞版本。` +
      (safeConstraint
        ? `请将依赖改为安全版本 ${safeConstraint} 后重新写入；不要以自动替换方式改写本工具输入。`
        : '请手动升级到安全版本后重试。')
      + (crossMajorAgentNote ? ` ${crossMajorAgentNote}` : '');
  
    return {
      continue: true,
      suppressOutput: false,
      systemMessage: systemParts.join(' '),
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'allow',
        permissionDecisionReason: reasonText,
        additionalContext: claudeContext
      }
    };
  }
  
  /**
   * 构造 Autofix 响应
   * 
   * 通过 updatedInput / modifiedInput 修改工具输入，实现自动修复
   * 
   * 安全原则：如果无法确保修复安全，则降级为 deny
   * 
   * 输出规范（符合 Claude Code Hook 规范）：
   * - systemMessage: 顶级字段，显示详细漏洞列表给用户
   * - permissionDecisionReason: 显示简要摘要给用户（allow/ask 时）
   * - additionalContext: 显示给 Claude 的上下文说明
   * 
   * @param {string} toolName - 工具名称
   * @param {Object} toolInput - 原始工具输入
   * @param {string} fixedContent - 修复后的完整文件内容
   * @param {Array} changes - 变更列表 [{from, to, cve, cvss, reason}, ...]
   * @param {Object} context - 上下文信息
   * @returns {Object} Hook 响应
   */
  function buildAutofixResponse(toolName, toolInput, fixedContent, changes, context, metadata = {}) {
    // F-03 v3: inject changes into context for buildUpdatedInput's manifest adapter
    const contextWithChanges = { ...context, changes };
    // 尝试构造 updatedInput
    const updatedInput = buildUpdatedInput(toolName, toolInput, fixedContent, contextWithChanges);
    const isIDE = isIdeClient(context?.client);
    
    // 安全校验：如果 buildUpdatedInput 返回 null，表示无法安全修复
    // 降级为 deny 响应
    if (updatedInput === null) {
      return buildDenyResponse(
        changes?.map(c => ({ n: c.from?.split('@')[0] || 'unknown', v: c.from?.split('@')[1] || '*', reason: 'autofix_validation_failed' })) || [],
        null,
        isIDE
      );
    }
    
    // 第一层：静默自愈 (Silent Patching)
    // 不打断 Agent 工作流（allow），但保留人类可见日志和 Agent 上下文
    const reasonText = buildReasonSummary(changes, updatedInput);
    
    // 生成 systemMessage（IDE 使用 Markdown，CLI 使用纯文本）
    const systemMsg = buildSystemMessage(changes, isIDE, metadata);
  
    // 给 Agent 的上下文保持短小，实际执行内容以 updatedInput/modifiedInput 为准
    const claudeContext = buildClaudeContext(changes, updatedInput, metadata);
  
    // CLI 使用 updatedInput，IDE 使用 modifiedInput
    const inputFieldName = isIDE ? 'modifiedInput' : 'updatedInput';
  
    const response = {
      continue: true,
      suppressOutput: false,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'allow',
        permissionDecisionReason: reasonText,
        [inputFieldName]: updatedInput
      }
    };
    
    // 添加 systemMessage（顶级字段，显示给用户）
    if (systemMsg) {
      response.systemMessage = systemMsg;
    }
    
    // 添加 additionalContext（显示给 Claude）
    if (claudeContext) {
      response.hookSpecificOutput.additionalContext = claudeContext;
    }
  
    // D2-v4: 审计语义补全（仅 smooth / disableAutofix=false 的成功自动修复路径）。
    // 原始输入始终未放行；放行的是 server-verified fixedContent 经本地 buildUpdatedInput
    // 结构校验后的安全内容。记录原始/生效哈希 + 修复数，供安全审计明确区分
    // server_decision=BLOCK 与 client_action=AUTO_REMEDIATE_AND_ALLOW，避免日后歧义。
    // 强约束：disableAutofix=true（audit/strict）绝不产出该字段——即使被误调用也自洽。
    if (!context?.disableAutofix) {
    const _originalContent = toolInput?.content ?? toolInput?.command ?? '';
    response.hookSpecificOutput.client_action = 'AUTO_REMEDIATE_AND_ALLOW';
    response.hookSpecificOutput.original_hash = createHash('sha256').update(_originalContent).digest('hex').slice(0, 32);
    response.hookSpecificOutput.effective_hash = createHash('sha256').update(fixedContent || '').digest('hex').slice(0, 32);
    response.hookSpecificOutput.findings_fixed = Array.isArray(changes) ? changes.length : 0;
    }
  
    return response;
  }
  
  /**
   * 构建简要摘要（permissionDecisionReason）
   *
   * 一行简洁的摘要，显示给用户（中文）
   *
   * @param {Array} changes - 变更列表
   * @param {Object} updatedInput - 修改后的输入（可选，用于显示实际内容）
   * @returns {string} 摘要文本
   */
  function buildReasonSummary(changes) {
    const changeSummary = summarizeChangeSet(changes);
    return changeSummary
      ? `🛡️ 安全修复：已替换为安全版本（${changeSummary}）`
      : '🛡️ 安全修复：已替换为安全版本';
  }
  
  function buildSystemMessage(changes, isIDE = false, metadata = {}) {
    const changeSummary = summarizeChangeSet(changes);
    const recommendedNote = buildRecommendedFixNote(metadata?.recommended_fix);
    const parts = [changeSummary ? `已自动替换为安全版本：${changeSummary}` : '已自动替换为安全版本。'];
    if (recommendedNote) parts.push(recommendedNote);
    if (metadata?.agent_instruction?.user_message) {
      parts.push(metadata.agent_instruction.user_message);
    }
    return parts.join(' ');
  }
  
  function buildClaudeContext(changes, updatedInput, metadata = {}) {
    if (metadata?.agent_instruction?.agent_message) {
      return metadata.agent_instruction.agent_message;
    }
    if (metadata?.agent_instruction?.message) {
      return metadata.agent_instruction.message;
    }
    return null;
  }
  
  function truncatePreview(text, maxLength = 120) {
    if (typeof text !== 'string') return null;
    if (text.length <= maxLength) return text;
    return `${text.slice(0, maxLength - 1)}…`;
  }
  
  function buildContentPreview(content) {
    if (typeof content !== 'string') return null;
  
    const trimmed = content.trim();
    if (!trimmed) return null;
  
    const lines = trimmed.split('\n').filter(Boolean);
    if (lines.length !== 1) return null;
  
    return truncatePreview(lines[0].trim());
  }
  
  function extractExplanationTarget(explanation) {
    if (typeof explanation !== 'string') return null;
  
    const match = explanation.match(/到\s+(.+)$/);
    return match?.[1]?.trim() || null;
  }
  
  function rewriteWriteExplanation(toolInput, fixedContent) {
    const originalExplanation = typeof toolInput?.explanation === 'string'
      ? toolInput.explanation
      : null;
  
    if (!originalExplanation) {
      return null;
    }
  
    const originalPreview = buildContentPreview(toolInput?.content);
    const fixedPreview = buildContentPreview(fixedContent);
  
    if (originalPreview && fixedPreview && originalExplanation.includes(originalPreview)) {
      return originalExplanation.replace(originalPreview, fixedPreview);
    }
  
    const target = extractExplanationTarget(originalExplanation);
    if (!target) {
      return originalExplanation;
    }
  
    if (fixedPreview) {
      return `写入 ${fixedPreview} 到 ${target}`;
    }
  
    return `写入安全修复后的内容到 ${target}`;
  }
  
  function applyChangeReplacements(text, changes = []) {
    if (typeof text !== 'string' || !text) {
      return text;
    }
  
    let rewritten = text;
    for (const change of changes) {
      const from = typeof change?.from === 'string' ? change.from : null;
      const to = typeof change?.to === 'string' ? change.to : null;
  
      if (from && to && rewritten.includes(from)) {
        rewritten = rewritten.split(from).join(to);
      }
    }
  
    return rewritten;
  }
  
  function rewriteBashDisplayText(text, originalCommand, fixedCommand, changes = []) {
    if (typeof text !== 'string' || !text) {
      return null;
    }
  
    let rewritten = text;
  
    if (
      typeof originalCommand === 'string' &&
      originalCommand &&
      typeof fixedCommand === 'string' &&
      fixedCommand &&
      rewritten.includes(originalCommand)
    ) {
      rewritten = rewritten.replace(originalCommand, fixedCommand);
    }
  
    rewritten = applyChangeReplacements(rewritten, changes);
    return rewritten;
  }
  
  /**
   * O1-22（最小切片）：此前这里会把 fixInfo.modifiedContent（即将/已经写入
   * 磁盘的完整文件内容）原样塞进 markdown code fence 发给 Claude，且 change
   * 列表无数量上限——这正是文档"stack、raw JSON、完整命令、fixed content
   * 禁止进入上下文"明确禁止的模式：扫描本身不调用 LLM，但这段长文本会进入
   * 后续模型会话上下文，累积消耗 Token 预算（见
   * fix_update/optimizations/22_Model_Context_Token_Budget.md）。
   *
   * 修复：change 列表复用已有的 summarizeChangeSet()（top-2 + 超出计数，
   * 与 buildBlockWithAdviceResponse/buildHighRiskDenyResponse 已经在用的
   * 同一套摘要逻辑），完全删除完整文件内容的注入——保留"请反映实际写入版本"
   * 这条指令性文案（这是模型需要采取行动的合法场景：据实回复而不是照抄原始
   * 请求），但不再附带内容原文作为"证据"。需要查看完整写入内容的场景，走
   * buildUpdatedMCPToolOutput()（IDE 界面同步用途，是工具输出字段，不进入
   * 模型上下文）。
   */
  function buildPostToolUseAdditionalContext(fixInfo) {
    if (!fixInfo?.changes?.length) return null;
  
    const changeSummary = summarizeChangeSet(fixInfo.changes);
  
    return `## 🛡️ Security Guard 安全修复通知
  
  检测到依赖存在安全漏洞，已自动替换为安全版本：${changeSummary}
  
  **重要提示**：请在回复中反映实际写入的安全版本，而不是原始请求的版本。`;
  }
  
  function buildUpdatedMCPToolOutput(toolResponse, fixInfo) {
    if (!toolResponse || typeof toolResponse !== 'object') {
      return toolResponse;
    }
  
    const modifiedContent = typeof fixInfo?.modifiedContent === 'string'
      ? fixInfo.modifiedContent
      : null;
  
    const updatedToolOutput = {
      ...toolResponse,
      securityAutofix: {
        applied: true,
        changes: fixInfo?.changes || [],
        actualWrittenContent: modifiedContent,
      },
    };
  
    if (!modifiedContent) {
      return updatedToolOutput;
    }
  
    updatedToolOutput.actualWrittenContent = modifiedContent;
    updatedToolOutput.actualContent = modifiedContent;
    updatedToolOutput.requestedContentRewritten = true;
    updatedToolOutput.summary = `Actual written content after Security Guard autofix: ${modifiedContent}`;
    updatedToolOutput.notice = `Security Guard rewrote the requested content. Actual written content:\n${modifiedContent}`;
  
    if (toolResponse.type === 'write_to_file_result') {
      updatedToolOutput.content = modifiedContent;
      updatedToolOutput.bytesWritten = Buffer.byteLength(modifiedContent, 'utf8');
      updatedToolOutput.addedChars = modifiedContent.length;
    }
  
    return updatedToolOutput;
  }
  
  function buildPostToolUseResponse(toolResponse = null, fixInfo = null, context = {}) {
    const response = {
      continue: true,
      hookSpecificOutput: {
        hookEventName: 'PostToolUse'
      }
    };
  
    const additionalContext = buildPostToolUseAdditionalContext(fixInfo);
    if (additionalContext) {
      response.hookSpecificOutput.additionalContext = additionalContext;
    }
  
    if (isIdeClient(context?.client) && additionalContext) {
      response.hookSpecificOutput.updatedMCPToolOutput = buildUpdatedMCPToolOutput(toolResponse, fixInfo);
    }
  
    return response;
  }
  
  /**
   * F-05: Build PostToolUse final audit response (lockfile re-audit)
   * Short output — zero token for FINAL_PASS, minimal context for FINAL_BLOCK/WARN
   */
  function buildPostToolUseFinalResponse(serverResponse, packages, context = {}) {
    const normalized = normalizeServerResponse(serverResponse || {});
    const status = normalized.decision || normalized.s || 'PASS';
  
    // FINAL_PASS: zero token — no additionalContext
    if (status === 'PASS') {
      return {
        continue: true,
        hookSpecificOutput: {
          hookEventName: 'PostToolUse',
        }
      };
    }
  
    // FINAL_BLOCK/WARN: short additionalContext
    const blocked = normalized.unfixable || [];
    const cveSummary = blocked.length > 0
      ? blocked.map(u => `${u.n}@${u.v}`).join(', ')
      : packages.map(p => `${p.name}@${p.version}`).join(', ');
  
    const label = status === 'BLOCK' ? 'FINAL_BLOCK' : 'FINAL_WARN';
  
    return {
      continue: true,
      hookSpecificOutput: {
        hookEventName: 'PostToolUse',
        additionalContext: `Dependency final review · ${packages.length} resolved\n${label}  ${cveSummary}\nNext dependency operation will be checked by PreToolUse gate.`,
      }
    };
  }
  
  /**
   * 根据 CVSS 分数获取严重等级图标
   * 
   * @param {number} cvss - CVSS 分数
   * @returns {string} 图标
   */
  function getSeverityIcon(cvss) {
    if (cvss >= 9.0) return '🔴';  // Critical
    if (cvss >= 7.0) return '🟠';  // High  
    if (cvss >= 4.0) return '🟡';  // Medium
    if (cvss >= 0.1) return '🟢';  // Low
    return '⚪';                   // Unknown
  }
  
  /**
   * 根据 CVSS 分数获取严重等级描述
   * 
   * @param {number} cvss - CVSS 分数
   * @returns {string} 严重等级
   */
  function getSeverityLevel(cvss) {
    if (cvss >= 9.0) return 'CRITICAL - 严重';
    if (cvss >= 7.0) return 'HIGH - 高危';
    if (cvss >= 4.0) return 'MEDIUM - 中危';
    if (cvss >= 0.1) return 'LOW - 低危';
    return 'UNKNOWN';
  }
  
  /**
   * O1-17（最小切片）：竞态校验——重新读取磁盘当前内容，与发起 Server 请求
   * 之前捕获的快照对比。用于检测"读取原始内容 → 发给 Server → 收到
   * fixed_content"这段网络往返期间，磁盘文件是否被外部修改过（对应文档
   * fix_update/optimizations/17_Local_Structured_File_Autofix.md 的
   * Client 应用流程第 4 步"验证当前值仍等于 from_spec，防止竞态覆盖"）。
   *
   * 当前协议是整文件 fixed_content 字符串，没有逐依赖的 from_spec 概念——
   * 用整份磁盘快照做整文件粒度的竞态校验，是当前协议下能做到的最细粒度
   * 检查，完全覆盖"外部改动 vs 基于旧快照写回"这个核心风险场景。
   *
   * @param {string} filePath
   * @param {string} snapshotContent - 发起请求前捕获的磁盘快照
   * @returns {boolean} true 表示磁盘内容已经变化（竞态），应该拒绝应用
   */
  function hasFileChangedSinceSnapshot(filePath, snapshotContent) {
    try {
      const currentContent = existsSync(filePath) ? readFileSync(filePath, 'utf-8') : '';
      return currentContent !== snapshotContent;
    } catch {
      // 读取异常（权限变化等）：保守起见视为"已变化"，拒绝应用而不是盲目写入
      return true;
    }
  }
  
  /**
   * 构造更新后的工具输入 (updatedInput)
   * 
   * 关键逻辑：
   * - Write: 替换 content，并同步 explanation 等 IDE 展示字段
   * - Edit: 需要特殊处理
   *   - 如果原本是局部替换，需要转换为：用磁盘原内容替换为修复后完整内容
   *   - old_string = 磁盘上的原文件内容
   *   - new_string = 修复后的完整文件内容
   * - MultiEdit: 转换为单次全量替换
   * 
   * 安全原则：
   * - 对于 package.json 文件，校验修复后内容是有效 JSON
   * - 对于 Edit/MultiEdit，确保 disk_content 存在
   * - O1-17：若此前捕获过磁盘快照（disk_content），重新读取磁盘当前内容，
   *   与快照对比，检测请求 Server 期间文件是否被外部修改（竞态）
   * - 校验失败返回 null，触发降级为 deny
   * 
   * @param {string} toolName - 工具名称
   * @param {Object} toolInput - 原始工具输入
   * @param {string} fixedContent - 修复后的完整文件内容
   * @param {Object} context - 上下文信息
   * @returns {Object|null} 更新后的工具输入，校验失败返回 null
   */
  function buildUpdatedInput(toolName, toolInput, fixedContent, context) {
    const filePath = toolInput.file_path || '';
  
    // F-03.4: Race check must be BEFORE adapter path — not after.
    // O1-17：竞态校验——只在此前确实捕获过快照时才检查（undefined/null 表示
    // 从未捕获，不属于本次要处理的场景，维持现状行为）
    if (context?.disk_content !== undefined && context?.disk_content !== null) {
      if (hasFileChangedSinceSnapshot(filePath, context.disk_content)) {
        return null; // 竞态：拒绝应用，触发既有的降级为 deny 路径
      }
    }
  
    // F-03 修复：对 package.json 使用结构化 manifest adapter，
    // 不直接信任 Server 返回的完整文件内容。adapter 会验证只改了目标依赖版本，
    // scripts/repository/其他依赖不变。
    if (filePath.endsWith('package.json')) {
      // 从 context.changes 构造结构化 edits
      const changes = context?.changes || [];
      const edits = changes.map(c => {
        // change.from 格式: "lodash@4.17.20" 或 "lodash==4.17.20"
        // F-03.1: Handle scoped packages (@scope/pkg@1.0.0 → pkg="@scope/pkg", spec="1.0.0")
        const fromStr = c.from || '';
        const toStr = c.to || '';
        // Extract package name: handles both "lodash@4.17.20" and "@scope/pkg@1.0.0"
        const fromMatch = fromStr.match(/^(@[^@/]+\/[^@/]+|[^@=]+)(?:[@=](.+))?$/);
        const toMatch = toStr.match(/^(@[^@/]+\/[^@/]+|[^@=]+)(?:[@=](.+))?$/);
        const pkgName = (fromMatch && fromMatch[1]) || (toMatch && toMatch[1]) || '';
        return {
          package_id: pkgName,
          from_spec: (fromMatch && fromMatch[2]) || '',
          to_spec: (toMatch && toMatch[2]) || toStr,
        };
      }).filter(e => e.package_id);
  
      if (edits.length > 0) {
        // V6-F04: audited_packages must be present and non-empty — fail-closed when missing
        const auditedPackages = context?.audited_packages;
        if (!auditedPackages || !Array.isArray(auditedPackages) || auditedPackages.length === 0) {
          return null; // No audited package set → deny autofix (fail-closed)
        }
        const auditedSet = new Set(auditedPackages.map(p => p.n || p));
        for (const edit of edits) {
          if (!auditedSet.has(edit.package_id)) {
            // Server is trying to modify a package that wasn't locally audited → deny
            return null;
          }
        }
  
        // F-03 v6: Use proposed content as edit base. For Write, toolInput.content has
        // the full proposed content. For Edit/MultiEdit, context.original_content has it
        // (computed by index.js from disk_content + edit operations).
        const originalContent = toolInput.content || context?.original_content || context?.disk_content || '';
        const result = applyManifestEdits(originalContent, edits);
        if (result.ok) {
          // adapter 验证通过，使用 adapter 生成的内容（而非 Server 的 fixed_content）
          return _buildUpdatedToolInput(toolName, toolInput, result.content, context);
        } else {
          // adapter 验证失败——降级为 deny
          return null;
        }
      }
      // F-03 v3: No edits → deny. Do NOT fall back to accepting Server's complete file.
      // The adapter is the only safe path for package.json autofix.
      return null;
    }
  
    // 安全校验 2: 对于 requirements.txt，校验基本格式
    if (/(?:^|[\\/])requirements(?:[-_.].*)?\.txt$/.test(filePath)) {
      if (!validateRequirementsTxt(fixedContent)) {
        return null; // 格式无效，降级为 deny
      }
    }
  
    // Race check already done above (F-03.4 moved it before adapter path)
  
    return _buildUpdatedToolInput(toolName, toolInput, fixedContent, context);
  }
  
  /**
   * F-03: 从指定的 content 构造 updatedInput/modifiedInput。
   * 被 buildUpdatedInput 的 adapter 路径和原路径共用。
   */
  function _buildUpdatedToolInput(toolName, toolInput, content, context) {
    switch (toolName) {
      case 'Write': {
        const updatedWriteInput = {
          file_path: toolInput.file_path,
          content: content
        };
        const rewrittenExplanation = rewriteWriteExplanation(toolInput, content);
        if (rewrittenExplanation) {
          updatedWriteInput.explanation = rewrittenExplanation;
        }
        return updatedWriteInput;
      }
  
      case 'Edit':
        if (context.disk_content === undefined || context.disk_content === null) {
          return null;
        }
        return {
          file_path: toolInput.file_path,
          old_string: context.disk_content,
          new_string: content
        };
  
      case 'MultiEdit':
        if (context.disk_content === undefined || context.disk_content === null) {
          return null;
        }
        return {
          file_path: toolInput.file_path,
          edits: [{
            old_string: context.disk_content,
            new_string: content
          }]
        };
  
      default:
        return null;
    }
  }
  
  /**
   * 校验 JSON 格式是否有效
   * 
   * @param {string} content - JSON 字符串
   * @returns {boolean} 是否有效
   */
  function validateJson(content) {
    if (!content || typeof content !== 'string') {
      return false;
    }
    
    try {
      JSON.parse(content);
      return true;
    } catch {
      return false;
    }
  }
  
  /**
   * 校验 requirements.txt 格式是否有效
   * 
   * 基本校验：
   * - 不为空
   * - 每行要么是注释、空行、选项行，要么是有效的包名格式
   * 
   * @param {string} content - requirements.txt 内容
   * @returns {boolean} 是否有效
   */
  function validateRequirementsTxt(content) {
    if (!content || typeof content !== 'string') {
      return false;
    }
    
    const lines = content.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      // 空行：有效
      if (!trimmed) continue;
      
      // 注释行：有效
      if (trimmed.startsWith('#')) continue;
      
      // 选项行 (-r, -e, -i, --index-url 等)：有效
      if (trimmed.startsWith('-')) continue;
      
      // 包名行：必须以字母或数字开头
      if (!/^[a-zA-Z0-9]/.test(trimmed)) {
        return false; // 无效行
      }
    }
    
    return true;
  }
  
  /**
   * 识别"包安装子命令"的正则列表。
   *
   * D1-18 修复：此前 index.js 的 isPackageInstallCommand() 和这里各维护一份几乎
   * 相同的正则拷贝（同 D1-09 已确认过的"多处手写同一份识别规则"这类结构性风险），
   * 现在导出为唯一事实来源，两处共用，避免未来新增/修改识别规则时只改了一处。
   * 放在 response.js（而不是 index.js）是因为 index.js 已经 import response.js，
   * 反向 import 会造成循环依赖。
   */
  const INSTALL_COMMAND_PATTERNS = [
    /^(npm|yarn|pnpm|bun)\s+(install|add|i)\s/,
    /^(pip3?|python3?\s+-m\s+pip|uv\s+pip|pipenv)\s+install\s/,
    /^(poetry|pdm|uv)\s+add\s/,
    /^go\s+(get|install)\s/,
    /^cargo\s+(add|install)\s/,
    /^gem\s+install\s/,
    /^bundle\s+(install|add)\s/,
    /^composer\s+(install|require)\s/,
    /^(?:mvn|mvnw|\.\/mvnw)\s+.*(?:dependency:get|dependency:copy|install:install-file|-Dartifact=|-DgroupId=)/,
  ];
  
  /**
   * 将修复后的安装命令替换回原始链式命令中，保留非安装子命令（cd 等前缀/后缀）
   *
   * D1-18 修复：此前遇到第一个匹配的安装子命令就替换并停止扫描（`replaced` 置
   * true 后后续 token 直接跳过），如果链式命令里有第二个及以后的安装子命令
   * （如 `npm install a@1 && npm install b@2`，两者都需要升级），第二个会被原样
   * 保留成漏洞版本——而 Server 侧此时理应也已经改为不会为这种多包场景生成单条
   * fixed_content（见 http_server.py 的对应修复），但 Client 侧仍需要独立的
   * 防御纵深：即使某种未预见的路径下 Server 仍返回了这类命令，Client 也不能
   * 无条件地把它当作"安全的整条替换"直接执行。
   *
   * 现在改为先扫描整条命令里有多少个安装子命令：只有恰好 1 个时才满足"用一条
   * fixed_content 字符串安全地整体替换"的前提，替换该 token 并保留其余
   * token/分隔符；0 个或 ≥2 个时返回 null，表示"无法安全地 all-or-nothing 重写"，
   * 交给调用方（buildBashAutofixResponse）降级为不自动改写、只展示建议。
   *
   * @param {string[]} commandTokens - 带分隔符的 token 列表，如 ["cd /a", "&&", "npm install foo"]
   * @param {string} fixedContent - 修复后的安装命令，如 "npm install axios@0.29.0"
   * @returns {string|null} 重建后的完整命令；无法安全重建时返回 null
   */
  function rebuildCommand(commandTokens, fixedContent) {
    // F-02 v2: Structured local reconstruction — never trust Server's complete command string.
    // Instead, parse the original install token, extract ONLY the version from fixedContent,
    // and reconstruct the command locally with the version replaced.
    if (!commandTokens || commandTokens.length === 0) {
      return null; // can't reconstruct without original tokens
    }
  
    const SEPARATORS = new Set(['&&', '||', ';']);
    const installIndexes = [];
    commandTokens.forEach((token, i) => {
      if (SEPARATORS.has(token)) return;
      if (INSTALL_COMMAND_PATTERNS.some(p => p.test(token))) {
        installIndexes.push(i);
      }
    });
  
    if (installIndexes.length !== 1) {
      return null;
    }
  
    const targetIndex = installIndexes[0];
    const originalToken = commandTokens[targetIndex];
  
    // Parse original install token to extract: {cmd, pkg, ver}
    // e.g. "npm install lodash@4.17.20" → {cmd:"npm install", pkg:"lodash", ver:"4.17.20"}
    // e.g. "pip install django==4.2" → {cmd:"pip install", pkg:"django", ver:"4.2"}
    const parsed = parseInstallToken(originalToken);
    if (!parsed) {
      return null; // can't parse original token safely
    }
  
    // Extract the full package+version spec from Server's fixedContent
    // e.g. "npm install lodash@4.17.21" → "lodash@4.17.21"
    // e.g. "pip install Django>=4.2.30" → "Django>=4.2.30"
    // We trust the version part but validate the package name matches original
    const serverSpec = extractPackageSpec(fixedContent);
    if (!serverSpec) {
      return null; // can't extract spec
    }
  
    // Validate the package name in serverSpec matches the original package name
    // V7-F06: Handle scoped npm packages (@scope/pkg@1.0.0 → @scope/pkg)
    const serverPkgMatch = serverSpec.match(/^(@[^@/]+\/[^@/]+|[^@=><~^]+)(?:[@=><~^](.+))?$/);
    const serverPkgName = serverPkgMatch ? serverPkgMatch[1] : '';
    if (serverPkgName !== parsed.pkg) {
      return null; // package name changed — reject
    }
  
    // Validate the version part contains only version-like characters
    // Extract everything after the package name + separator
    const versionPart = serverSpec.slice(parsed.pkg.length);
    // Allowed: @>=<~^ + digits/dots/letters/+/-
    if (!/^[@=><~^]*[\d][\w.\-+]*$/.test(versionPart)) {
      return null; // version contains non-version characters — reject
    }
    // F-02 v4: Reject bare > and < (shell redirect) — only >= and <= are valid version operators
    // >1 → redirect to file "1"; >>1 → append to file "1"; <1 → read from file "1"
    if (/[<>](?![=])/.test(versionPart)) {
      return null; // bare > or < without = → shell redirect — reject
    }
    // Double-check: no shell metacharacters. Allow >= and <= in versionPart,
    // but reject bare >, <, ;, &, |, `, \n, $, (, )
    // Strategy: temporarily strip >= and <= then check for remaining >, <
    const strippedVersionPart = versionPart.replace(/>=/g, '').replace(/<=/g, '');
    if (/[<>;&|`\n$()]/.test(strippedVersionPart)) {
      return null; // contains shell metacharacters — reject
    }
  
    // F-02 v5: Quote the entire package spec to prevent Shell from interpreting
    // >=/<= as redirects. e.g. npm install 'lodash@>=4.17.21' or pip install 'Django>=4.2.30'
    // This is safe because:
    // F-02 v6: Reject if serverSpec contains single quotes — they would break the outer quoting
    if (serverSpec.includes("'")) {
      return null; // package name/spec contains single quote → cannot safely quote → reject
    }
  
    // - Single quotes prevent ALL shell interpretation of the spec content
    // - The spec has already been validated to contain only version-like characters
    // - npm/pip accept quoted version specs
    const newToken = `${parsed.cmd} '${serverSpec}'`;
  
    // Validate: reconstructed token has same number of space-separated parts as original
    const origParts = originalToken.split(/\s+/).filter(Boolean);
    const newParts = newToken.split(/\s+/).filter(Boolean);
    if (origParts.length !== newParts.length) {
      return null; // token structure changed — reject
    }
  
    // Verify: only the version part changed, cmd and pkg are identical
    for (let i = 0; i < origParts.length; i++) {
      if (origParts[i] === newParts[i]) continue;
      // Allow the last part (pkg@ver) to differ since that's where the version lives
      if (i === origParts.length - 1) {
        // Strip quotes for comparison
        const origPkg = origParts[i].replace(/^['"]/, '').split(/[@=><~^]/)[0];
        const newPkg = newParts[i].replace(/^['"]/, '').split(/[@=><~^]/)[0];
        if (origPkg !== newPkg) {
          return null; // package name changed — reject
        }
      } else {
        return null; // non-version part changed — reject
      }
    }
  
    return commandTokens.map((token, i) => (i === targetIndex ? newToken : token)).join(' ');
  }
  
  /**
   * Parse an install command token into {cmd, pkg, ver} parts.
   * e.g. "npm install lodash@4.17.20" → {cmd:"npm install", pkg:"lodash", ver:"4.17.20"}
   * e.g. "pip install django==4.2" → {cmd:"pip install", pkg:"django", ver:"4.2"}
   * e.g. "npm install @scope/pkg@1.0.0" → {cmd:"npm install", pkg:"@scope/pkg", ver:"1.0.0"}
   * Returns null if the token can't be safely parsed.
   */
  function parseInstallToken(token) {
    if (!token || typeof token !== 'string') return null;
    // Split into parts: ["npm", "install", "lodash@4.17.20"]
    const parts = token.split(/\s+/).filter(Boolean);
    if (parts.length < 3) return null;
  
    // Last part is the package spec (pkg@ver or pkg==ver)
    const spec = parts[parts.length - 1];
    // Handle scoped packages: @scope/pkg@1.0.0
    // Match: @scope/pkg@1.0.0, lodash@4.17.20, django==4.2, lodash (no version)
    const specMatch = spec.match(/^(@[^@/]+\/[^@/]+|[^@=]+)(?:[@=](.+))?$/);
    if (!specMatch) return null;
  
    const pkg = specMatch[1];
    const ver = specMatch[2] || '';
    // cmd is everything except the last part: "npm install"
    const cmd = parts.slice(0, -1).join(' ');
  
    return { cmd, pkg, ver };
  }
  
  /**
   * Extract the version spec from a Server-provided install command.
   * We trust ONLY the version spec (e.g. "4.17.21", ">=4.2.30"), not the command structure.
   * e.g. "npm install lodash@4.17.21" → "4.17.21"
   * e.g. "pip install django>=4.2.7" → ">=4.2.7"
   * Returns null if no version can be safely extracted.
   */
  /**
   * Extract the full package+version spec from a Server-provided install command.
   * e.g. "npm install lodash@4.17.21" → "lodash@4.17.21"
   * e.g. "pip install Django>=4.2.30" → "Django>=4.2.30"
   * e.g. "npm install @scope/pkg@1.0.0" → "@scope/pkg@1.0.0"
   * Returns null if no spec can be safely extracted.
   */
  function extractPackageSpec(command) {
    if (!command || typeof command !== 'string') return null;
    const tokens = command.trim().split(/\s+/);
    for (let i = tokens.length - 1; i >= 0; i--) {
      const token = tokens[i];
      if (/^[@a-zA-Z]/.test(token) && /[@=><~^]/.test(token)) {
        return token;
      }
    }
    return null;
  }
  
  /**
   * 构造 Bash 命令 Autofix 响应
   * 
   * 将 Server 返回的修复命令（fixed_content）替换原安装子命令，
   * 保留 cd 等非安装前缀子命令，通过 updatedInput.command 传回完整命令。
   * 
   * @param {Object} toolInput - 原始工具输入
   * @param {string} fixedContent - 修复后的安装命令
   * @param {Array} changes - 变更列表
   * @param {Object} context - 上下文信息（含 commandTokens）
   * @param {Object} metadata - 服务端元数据（security_autofix, recommended_fix）
   * @returns {Object} Hook 响应
   */
  function buildBashAutofixResponse(toolInput, fixedContent, changes, context, metadata = {}) {
    const commandTokens = context?.commandTokens || [];
    const rebuiltCommand = rebuildCommand(commandTokens, fixedContent);
    const isIDE = isIdeClient(context?.client);
  
    // F-02 v2: When rebuildCommand returns null, the fixedContent is either
    // unparseable or suspicious. In either case, we must NOT allow execution.
    // The original D1-18 fallback to buildAllowWithAdviceResponse is wrong for
    // the injection case — it would allow the original command to execute.
    if (rebuiltCommand === null) {
      const riskConfig = context?.riskConfig || {};
      const riskLevel = getRiskLevel(changes, riskConfig);
      const maxCvssScore = getMaxCvss(changes);
      // Always deny when we can't safely rebuild — the original command has a vulnerability
      return buildHighRiskDenyResponse(changes, maxCvssScore, null, isIDE, metadata);
    }
  
    const originalDisplayText = isIDE
      ? (toolInput.explanation ?? toolInput.description ?? '')
      : (toolInput.description ?? '');
    const rewrittenDisplayText = rewriteBashDisplayText(
      originalDisplayText,
      toolInput.command,
      rebuiltCommand,
      changes,
    );
  
    // 构建修改后的输入对象
    const modifiedInputObj = {
      command: rebuiltCommand,
    };
  
    if (isIDE) {
      if (originalDisplayText || rewrittenDisplayText) {
        modifiedInputObj.explanation = rewrittenDisplayText ?? originalDisplayText;
      }
    } else {
      modifiedInputObj.description = rewrittenDisplayText ?? originalDisplayText;
    }
  
    // 第一层：静默自愈 (Silent Patching)
    // 不打断 Agent 工作流（allow），但保留人类可见日志和 Agent 上下文
    const reasonText = buildReasonSummary(changes, modifiedInputObj);
    
    // 生成 systemMessage（IDE 使用 Markdown，CLI 使用纯文本）
    const systemMsg = buildSystemMessage(changes, isIDE, metadata);
  
    // 给 Agent 的上下文保持短小，英文，实际执行内容以 updatedInput/modifiedInput 为准
    const claudeContext = buildClaudeContext(changes, modifiedInputObj, metadata);
  
    // CLI 使用 updatedInput，IDE 使用 modifiedInput
    const inputFieldName = isIDE ? 'modifiedInput' : 'updatedInput';
  
    const response = {
      continue: true,
      suppressOutput: false,
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'allow',
        permissionDecisionReason: reasonText,
        [inputFieldName]: modifiedInputObj
      }
    };
    
    // 添加 systemMessage（顶级字段，显示给用户）
    if (systemMsg) {
      response.systemMessage = systemMsg;
    }
    
    // 添加 additionalContext（显示给 Claude）
    if (claudeContext) {
      response.hookSpecificOutput.additionalContext = claudeContext;
    }
  
    // D2-v4: 审计语义补全（Bash smooth autofix，与 manifest 路径同语义）。
    // 原始命令未放行；放行的是 rebuiltCommand（server-verified 修复后命令）。
    // 强约束：disableAutofix=true 绝不产出该字段。
    if (!context?.disableAutofix) {
    const _originalCmd = toolInput?.command ?? '';
    response.hookSpecificOutput.client_action = 'AUTO_REMEDIATE_AND_ALLOW';
    response.hookSpecificOutput.original_hash = createHash('sha256').update(_originalCmd).digest('hex').slice(0, 32);
    response.hookSpecificOutput.effective_hash = createHash('sha256').update(rebuiltCommand || '').digest('hex').slice(0, 32);
    response.hookSpecificOutput.findings_fixed = Array.isArray(changes) ? changes.length : 0;
    }
  
    return response;
  }
  
  /**
   * 格式化变更列表为文本
   * 
   * @param {Array} changes - 变更列表
   * @returns {string} 格式化的文本
   */
  function formatChanges(changes) {
    if (!changes || changes.length === 0) {
      return '';
    }
    
    return changes.map(c => {
      let text = `${c.from} → ${c.to}`;
      if (c.cve) {
        text += ` (${c.cve})`;
      }
      return text;
    }).join('\n');
  }
  
  __response__.default = buildHookResponse;
  
  
  // Module exports
  __response__.normalizeServerResponse = normalizeServerResponse;
  __response__.summarizeServerResponseForLog = summarizeServerResponseForLog;
  __response__.buildHookResponse = buildHookResponse;
  __response__.isFailOpenReason = isFailOpenReason;
  __response__.buildAllowResponse = buildAllowResponse;
  __response__.buildLicenseReviewRecordResponse = buildLicenseReviewRecordResponse;
  __response__.buildLicenseDenyResponse = buildLicenseDenyResponse;
  __response__.buildDenyResponse = buildDenyResponse;
  __response__.buildBlockWithAdviceResponse = buildBlockWithAdviceResponse;
  __response__.buildHighRiskDenyResponse = buildHighRiskDenyResponse;
  __response__.buildAllowWithAdviceResponse = buildAllowWithAdviceResponse;
  __response__.buildAutofixResponse = buildAutofixResponse;
  __response__.buildPostToolUseResponse = buildPostToolUseResponse;
  __response__.buildPostToolUseFinalResponse = buildPostToolUseFinalResponse;
  __response__.buildUpdatedInput = buildUpdatedInput;
  __response__.buildBashAutofixResponse = buildBashAutofixResponse;
  __response__.formatChanges = formatChanges;
  __response__.INSTALL_COMMAND_PATTERNS = INSTALL_COMMAND_PATTERNS;
})();


// ============================================================================
// Module: operation_router
// ============================================================================

(function() {
  /**
   * Operation Router —— O2-32（Strangler 模式第一步）
   *
   * 职责：把一次 Hook 调用的原始输入（文件路径/Bash 命令字符串）路由判断为
   * "是否是需要审计的依赖操作"，以及必要时把链式命令拆分为可分别处理的
   * token。对应 fix_update/optimizations/32_Module_Boundary_Refactor.md
   * 目标模块表里的 `operation-router`（"tool → dependency operation"）。
   *
   * 依赖规则（文档"依赖规则"）：本模块只依赖纯数据/纯函数模块
   * （detectEcosystem/INSTALL_COMMAND_PATTERNS），不引用网络、UI、
   * Telemetry、文件系统 I/O——保证可以独立于完整 Hook 运行时被单元测试。
   *
   * 本次是从 src/index.js 原样迁移（不改变任何函数行为），用 21 个 golden
   * benchmark case（见 benchmark/run.js）在提取前后验证过黑盒行为等价。
   */
  
  const detectEcosystem = __parsers_manifests_index__.detectEcosystem;
  const INSTALL_COMMAND_PATTERNS = __response__.INSTALL_COMMAND_PATTERNS;
  
  /**
   * 判断文件是否为依赖清单文件
   */
  function isDependencyManifest(filePath) {
    if (!filePath) return false;
  
    // D1-09 修复：此前维护了两套独立的文件识别正则列表——这里的 `patterns`
    // 与 parsers/manifests/index.js 的 `detectEcosystem` 各自手写一份，曾经
    // 出现过 detectEcosystem 已支持 .gemspec，但这里的 patterns 漏掉了
    // .gemspec 的情况，导致 .gemspec 文件永远不会触发 Hook 审计（在到达
    // parseManifest 之前就被这里拦截放行）。现在改为直接复用 detectEcosystem
    // 作为唯一事实来源，消除"有 pattern 无 Parser 或有 Parser 无 pattern"
    // 这一类结构性 bug 的可能性。
    return detectEcosystem(filePath) !== null;
  }
  
  /**
   * 将 shell 链式命令拆分为带分隔符的 token 列表
   * 
   * @param {string} command - 完整命令字符串
   * @returns {string[]} token 数组，子命令与分隔符交替排列
   *   例: "cd /a && npm install foo" -> ["cd /a", "&&", "npm install foo"]
   */
  function splitShellCommandWithSeparators(command) {
    if (!command) return [];
    const tokens = [];
    // 按 &&、||、; 拆分，保留分隔符
    const parts = command.split(/(&&|\|\||;)/);
    for (const part of parts) {
      const trimmed = part.trim();
      if (trimmed) tokens.push(trimmed);
    }
    return tokens;
  }
  
  /**
   * 将 shell 链式命令拆分为子命令列表
   * 支持 &&、||、; 操作符，并对每个子命令做 trim
   * 
   * @param {string} command - 完整命令字符串
   * @returns {string[]} 子命令数组
   */
  function splitShellCommand(command) {
    if (!command) return [];
    // 按 &&、||、; 拆分，过滤掉空字符串
    return command.split(/&&|\|\||;/).map(s => s.trim()).filter(Boolean);
  }
  
  /**
   * 判断命令是否为包安装命令（支持 shell 链式命令）
   */
  function isPackageInstallCommand(command) {
    if (!command) return false;
  
    // 拆分链式命令，任意子命令匹配即返回 true
    const subCommands = splitShellCommand(command);
    return subCommands.some(sub => INSTALL_COMMAND_PATTERNS.some(p => p.test(sub)));
  }
  
  /**
   * D1-18：检测命令中是否包含 command substitution（$()/backtick）或 heredoc（<<
   * 紧跟标识符），这类语法下无法安全地静态判断"包名"边界（内容可能在执行时才展开），
   * 禁止自动修复——只审计+展示建议，不自动改写命令。
   *
   * 这是一个保守的启发式检测：宁可对"合法但恰好包含这些字符序列"的命令误报（后果
   * 只是少了一次自动修复机会），也不能漏报导致把动态展开的内容错误地当包名送进
   * Autofix 流程。
   */
  function isComplexShellSyntax(command) {
    if (!command) return false;
    return /\$\(|`|<<[-~]?\s*['"]?\w/.test(command);
  }
  
  
  // Module exports
  __operation_router__.isDependencyManifest = isDependencyManifest;
  __operation_router__.splitShellCommandWithSeparators = splitShellCommandWithSeparators;
  __operation_router__.splitShellCommand = splitShellCommand;
  __operation_router__.isPackageInstallCommand = isPackageInstallCommand;
  __operation_router__.isComplexShellSyntax = isComplexShellSyntax;
})();


// ============================================================================
// Module: redactor
// ============================================================================

(function() {
  /**
   * Redactor (D0-05 Stage B) —— 统一日志脱敏序列化器
   *
   * 设计原则（对齐 fix_update/defects/05_Sensitive_Logging_Redaction.md）：
   * - 调用端不传原文是首要原则；Redactor 是防御纵深，不是"可以先记录原文"的理由
   * - 递归处理对象/数组，按字段名 allowlist + 内容模式删除 token、URL 凭证、私网地址、绝对路径
   * - 默认拒绝（deny-by-default）：未在 allowlist 中的字段名一律 redact 为 `[REDACTED_FIELD]`
   * - debug 模式同样走 Redactor（文档明确："Debug 模式执行同一测试，仍不得出现原文"）
   *
   * 使用方式：
   *   const redactForLog = __redactor__.redactForLog;
  const redactString = __redactor__.redactString;
   *   UI.log(`[DIAG] input=${JSON.stringify(redactForLog(sensitiveObj))}`);
   *   UI.log(`[DIAG] msg=${redactString(maybeSensitiveText)}`);
   *
   * allowlist 是保守默认值，未来可通过配置文件覆盖（O1-33 配置 schema 的一部分）。
   * 当前不提供运行时配置入口——修改 allowlist 需要改源码，避免配置被篡改后日志边界
   * 被意外放宽。
   */
  
  const { createHash } = require('crypto');
  
  /**
   * 字段名 allowlist：这些字段名可以原样记录值（但仍会经过内容模式 redact）。
   * 选取原则：字段名本身不敏感，且值通常是结构化元数据（数字、枚举、短字符串）。
   *
   * 注意：包名（package_name / n）不在 allowlist 中——私有包名是敏感的。
   * 路径（file_path / path）也不在——绝对路径会泄漏用户目录结构。
   */
  const FIELD_ALLOWLIST = new Set([
    // 类型/枚举字段
    'tool_name', 'tool', 'hook_event_name', 'ecosystem', 'client_type',
    'client', 'codebuddy_version', 'ai_model', 'session_id', 'call_id',
    'tool_use_id', 'status', 's', 'decision', 'hook_action', 'a',
    'reason_code', 'risk_tier', 'risk_level', 'priority', 'source',
    'skip_reason', 'fail_open', 'fatal', 'degraded', 'multi_ecosystem',
    'ecosystem_count', 'dedup_state', 'dedup_retry_count',
    'policy_result', 'license_status', 'confidence', 'policy_version',
    'attribution_version', 'repo_detection_source',
    // 数字/计数字段
    't', 'elapsed_ms', 'duration_ms', 'package_count_total',
    'package_count_sent', 'package_count_filtered', 'package_count_checked',
    'package_count_degraded', 'context_chars', 'context_estimated_tokens',
    'additional_context_emitted', 'duplicate_context_suppressed',
    'autofix_applied', 'autofix_cve_count', 'autofix_pkg_count',
    'autofix_max_cvss', 'autofix_type', 'autofix_verified',
    'http_status_code', 'retry_count', 'fail_mode_trigger',
    'error_type', 'block_reason', 'reason',
    // 短字符串标识符（非敏感）
    'event_name', 'schema_version', 'event_id', 'operation_id',
    'client_ver', 'plugin_version', 'client_version', 'source_revision',
    'build_profile', 'build_timestamp', 'dirty', 'obfuscator_config_sha256',
    'protocol_schema_version',
    // 数组长度字段（值是数字）
    'length', 'count', 'size', 'changes_count', 'modified_content_length',
    'raw_input_length',
  ]);
  
  /**
   * 内容模式 redact 规则：对 allowlist 字段的字符串值，仍按这些模式扫描并替换。
   * 顺序很重要：先 redact 凭证（避免凭证片段被后续规则部分暴露），再 redact 路径/IP。
   */
  const CONTENT_PATTERNS = [
    // 1. Bearer / Authorization header
    { pattern: /\bBearer\s+[A-Za-z0-9._\-+/=]{10,}/gi, replacement: 'Bearer [REDACTED_TOKEN]' },
    // 2. 常见 token 前缀（sk- / ghp_ / xox / npm_ / pypi- 等）
    //    前缀后可能跟 - 或 _，且 token 主体至少 8 字符
    { pattern: /\b(sk|ghp|gho|ghu|ghs|ghr|xox[abps]|glpat|pypi)[-_][A-Za-z0-9_\-]{8,}/gi, replacement: '[REDACTED_TOKEN]' },
    { pattern: /\bnpm_[A-Za-z0-9]{8,}/gi, replacement: '[REDACTED_TOKEN]' },
    // 3. URL 中的 user:password@ 凭证
    { pattern: /([a-zA-Z][a-zA-Z0-9+.-]*:\/\/)[^\s/:@]+:[^\s/:@]+@/g, replacement: '$1[REDACTED_CRED]@' },
    // 4. 私网 IP（RFC 1918 + loopback + link-local）
    { pattern: /\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3}|169\.254\.\d{1,3}\.\d{1,3})\b/g, replacement: '[REDACTED_IP]' },
    // 5. Unix 绝对路径（/Users/alice/... / /home/bob/... / /tmp/xxx/...）
    //    保留 basename（文件名通常不敏感，且对排障有用），redact 目录部分
    { pattern: /(?:\/(?:Users|home|root|tmp|var|opt|etc|srv)\/)[^\s"'<>:|()]+/g, replacement: '[REDACTED_PATH]' },
  ];
  
  /**
   * 对字符串值做内容模式 redact
   * @param {string} str
   * @returns {string}
   */
  function redactString(str) {
    if (!str || typeof str !== 'string') return str;
    let result = str;
    for (const { pattern, replacement } of CONTENT_PATTERNS) {
      result = result.replace(pattern, replacement);
    }
    return result;
  }
  
  /**
   * 递归 redact 对象/数组：按字段名 allowlist 决定是否保留值，再对字符串值做内容模式 redact。
   *
   * - allowlist 中的字段：保留值，但字符串值经过 redactString()
   * - 不在 allowlist 中的字段：值替换为 '[REDACTED_FIELD]'
   * - 数组：每个元素递归 redact（但数组本身不按字段名过滤——数组元素没有字段名）
   * - 原始类型（number/boolean/null）：原样返回
   *
   * @param {*} obj - 任意值
   * @param {number} depth - 递归深度上限，避免循环引用/超深嵌套
   * @returns {*} redact 后的值（深拷贝，不修改原对象）
   */
  function redactForLog(obj, depth = 0) {
    if (depth > 10) return '[REDACTED_DEPTH_LIMIT]';
    if (obj === null || obj === undefined) return obj;
    if (typeof obj === 'number' || typeof obj === 'boolean') return obj;
    if (typeof obj === 'string') return redactString(obj);
    if (typeof obj === 'function' || typeof obj === 'symbol') return '[REDACTED_FN]';
  
    if (Array.isArray(obj)) {
      return obj.map(item => redactForLog(item, depth + 1));
    }
  
    if (typeof obj === 'object') {
      const result = {};
      for (const [key, value] of Object.entries(obj)) {
        if (FIELD_ALLOWLIST.has(key)) {
          result[key] = redactForLog(value, depth + 1);
        } else {
          result[key] = '[REDACTED_FIELD]';
        }
      }
      return result;
    }
  
    return '[REDACTED_UNKNOWN]';
  }
  
  /**
   * 计算 package fingerprint（不可逆）用于 Server 端日志/聚合。
   * 公开包名不敏感（npm lodash 等是公共知识），但 D0-05 文档要求"包名默认不进入
   * 普通日志；需要聚合时使用不可逆 package fingerprint，并区分公开/私有"。
   *
   * 这里用 sha256(ecosystem:package_name) 作为指纹——不引入 HMAC key（D1-28 的
   * HMAC 化是仓库身份的归因问题，package fingerprint 的威胁模型不同：包名本身
   * 是公开 registry 可查的，不需要字典攻击防护）。
   *
   * @param {string} ecosystem
   * @param {string} packageName
   * @returns {string} 64-char hex sha256，或空字符串（输入为空时）
   */
  function packageFingerprint(ecosystem, packageName) {
    if (!ecosystem || !packageName) return '';
    return createHash('sha256').update(`${ecosystem}:${packageName}`).digest('hex');
  }
  
  // All exports are inline (export function / export default). No re-export needed.
  
  
  // Module exports
  __redactor__.redactString = redactString;
  __redactor__.redactForLog = redactForLog;
  __redactor__.packageFingerprint = packageFingerprint;
})();


// ============================================================================
// Module: audit_log
// ============================================================================

(function() {
  /**
   * Audit Log
   *
   * 将安全替换事件追加写入 JSONL 格式的审计日志。
   * 格式：每行一条 JSON，UTF-8，追加写入（多进程安全）。
   * 默认路径：~/.security-guard/audit.jsonl
   *
   * F-11 修复：不再保存 raw command / 完整 file_path，只保存 basename + fingerprint。
   * 文件权限设为 0600，目录权限 0700。接入 Redactor 对 changes 做 redact。
   */
  
  const { appendFileSync, mkdirSync, chmodSync, existsSync, readFileSync, writeFileSync } = require('fs');
  const { dirname, join } = require('path');
  const { homedir } = require('os');
  const getMaxCvss = __risk_policy__.getMaxCvss;
  const packageFingerprint = __redactor__.packageFingerprint;
  const redactString = __redactor__.redactString;
  
  const DEFAULT_AUDIT_LOG = join(homedir(), '.security-guard', 'audit.jsonl');
  
  function appendAuditLog(entry, logPath = DEFAULT_AUDIT_LOG) {
    try {
      mkdirSync(dirname(logPath), { recursive: true, mode: 0o700 });
      appendFileSync(logPath, JSON.stringify(entry) + '\n', { encoding: 'utf-8', mode: 0o600 });
      // F-11: Fix permissions on existing file (mode only applies to new files)
      if (existsSync(logPath)) {
        try { chmodSync(logPath, 0o600); } catch { /* ignore */ }
      }
    } catch {
      // 审计日志是可观测性工具，写入失败不阻断主流程
    }
  }
  
  function buildAuditEntry({
    toolName,
    toolInput,
    changes,
    decision,
    riskLevel,
    context,
    exemptionReason = null,
    clientVer = null,
    sessionId = null,
  }) {
    const safeChanges = changes || [];
    const maxCvss = getMaxCvss(safeChanges);
    const cveCount = safeChanges.filter(c => c.cve).length;
  
    // F-11 修复：只保存 file basename（不含目录路径），不保存 raw command
    const filePath = toolName !== 'Bash' ? (toolInput?.file_path || null) : null;
    const fileBasename = filePath ? filePath.split(/[\\/]/).pop() : null;
  
    // F-11：Bash 命令只保存不可逆 fingerprint，不保存原文
    const bashCommand = toolName === 'Bash' ? (toolInput?.command || null) : null;
    const commandFingerprint = bashCommand ? packageFingerprint('bash', bashCommand) : null;
  
    return {
      ts:               new Date().toISOString(),
      session_id:       sessionId,
      client_ver:       clientVer,
      tool:             toolName,
      file:             fileBasename,           // 只存 basename，不存完整路径
      command:          null,                   // F-11: 不保存 raw command
      command_fingerprint: commandFingerprint,   // 不可逆 fingerprint 用于聚合
      risk_level:       riskLevel,
      max_cvss:         maxCvss,
      cve_count:        cveCount,
      decision,
      exemption_reason: exemptionReason,
      changes:          safeChanges.map(c => ({
        // F-11: redact from/to in case they contain source URLs or credentials
        from: redactString(c.from || ''),
        to:   redactString(c.to || ''),
        cve:  c.cve  || null,
        cvss: c.cvss || null,
      })),
      compatibility_hints: context?.compatibility_hints || [],
      repo:      context?.repo      || null,
      branch:    context?.branch    || null,
      ecosystem: context?.ecosystem || null,
      // P0-1：跨 Major 判定结果（客户端侧纵深防御）。v1 只留痕：即使 opt-in
      // 为 opted_in_pending，执行结果也不变（不解锁跨 Major 自动修复）。
      cross_major:        context?.cross_major        ?? false,
      cross_major_opt_in: context?.cross_major_opt_in ?? null,
    };
  }
  
  function escapeMarkdownTableCell(value) {
    if (value === null || value === undefined) return '';
    return String(value).replace(/\|/g, '\\|').replace(/`/g, '\\`').replace(/\n/g, ' ');
  }
  
  /**
   * 渲染确定性 Markdown 报告。
   * 纯字符串模板拼接，不调用 LLM。
   *
   * @param {Array<Object>} entries - buildAuditEntry() 产出的记录数组
   * @param {Object} byRiskLevel
   * @param {Object} byDecision
   * @param {Object} byEcosystem
   * @param {Object} [meta] - 报告元数据（数据源路径等）
   * @returns {string} Markdown 文本
   */
  function renderReportMarkdown(entries, byRiskLevel, byDecision, byEcosystem, meta = {}) {
    const lines = [];
    lines.push('# ChainGuard Runtime Security Audit Report');
    lines.push('');
    lines.push(`Generated: ${new Date().toISOString()}`);
    if (meta.auditLogPath) {
      lines.push(`Data Source: ${escapeMarkdownTableCell(meta.auditLogPath)}`);
    }
    lines.push('Scope: Local runtime audit history (machine/environment level; not a static repository scan)');
    lines.push(`Total runtime events: ${entries.length}`);
    lines.push('');
    lines.push('> [!NOTE]');
    lines.push('> This report summarizes historical runtime interception and audit events recorded by ChainGuard');
    lines.push('> during tool execution on this machine. It does NOT represent a static repository vulnerability scan');
    lines.push('> (such as npm audit or SCA) and does not verify the security posture of files currently in the workspace.');
    lines.push('> Historical interception events represent prevented or audited package operations, not confirmed');
    lines.push('> vulnerabilities in the current repository. Repository attribution is unverified or unknown for');
    lines.push('> records where repository metadata was not captured at runtime.');
    lines.push('');
  
    if (entries.length === 0) {
      lines.push('## Runtime Audit Events');
      lines.push('');
      lines.push('No runtime security events were recorded in the audit log.');
      lines.push('');
      lines.push('> [!NOTE]');
      lines.push('> An empty audit history indicates that no dependency operations were intercepted or audited');
      lines.push('> by ChainGuard on this machine. It does NOT imply that the current repository has been scanned');
      lines.push('> or is free of vulnerabilities.');
      lines.push('');
      return lines.join('\n');
    }
  
    const renderCountTable = (title, counts) => {
      lines.push(`## ${title}`);
      lines.push('');
      lines.push('| Value | Count |');
      lines.push('|---|---|');
      for (const [key, count] of Object.entries(counts)) {
        lines.push(`| ${escapeMarkdownTableCell(key)} | ${count} |`);
      }
      lines.push('');
    };
  
    renderCountTable('Runtime Events by Risk Level', byRiskLevel);
    renderCountTable('Runtime Events by Policy Decision', byDecision);
    renderCountTable('Runtime Events by Ecosystem', byEcosystem);
  
    lines.push('## Runtime Audit Events');
    lines.push('');
    lines.push('| Time | Tool | Component/Command | Decision | Risk Level | CVE Count | Max CVSS | Repository Attribution |');
    lines.push('|---|---|---|---|---|---|---|---|');
    for (const e of entries) {
      const target = e.tool !== 'Bash' ? (e.file || '') : (e.command || e.command_fingerprint || '');
      const repoAttr = e.repo ? `${escapeMarkdownTableCell(e.repo)}${e.branch ? ` (${escapeMarkdownTableCell(e.branch)})` : ''}` : 'Unknown (unattributed)';
      lines.push(
        `| ${escapeMarkdownTableCell(e.ts)} | ${escapeMarkdownTableCell(e.tool)} | ${escapeMarkdownTableCell(target)} | ` +
        `${escapeMarkdownTableCell(e.decision)} | ${escapeMarkdownTableCell(e.risk_level)} | ${e.cve_count ?? 0} | ${e.max_cvss ?? ''} | ${repoAttr} |`
      );
    }
    lines.push('');
  
    return lines.join('\n');
  }
  
  /**
   * `--report` 只读诊断入口的报告构造器。
   * 读取本地审计日志，生成 Markdown 格式的运行时审计报告，并返回路径与统计摘要。
   *
   * @param {string} [auditLogPath] - 审计日志路径，默认 DEFAULT_AUDIT_LOG
   * @returns {{ reportPath: string|null, summary: Object }}
   */
  function buildReportOutput(auditLogPath = DEFAULT_AUDIT_LOG) {
    if (!existsSync(auditLogPath)) {
      return {
        reportPath: null,
        summary: {
          totalEvents: 0,
          message: `No audit history found at ${auditLogPath}. Run a dependency install/edit operation to trigger runtime checks. (Note: this does not indicate that any repository has been scanned or is free of vulnerabilities.)`,
        },
      };
    }
  
    let lines = [];
    try {
      lines = readFileSync(auditLogPath, 'utf-8').trim().split('\n').filter(Boolean);
    } catch (err) {
      return {
        reportPath: null,
        summary: {
          totalEvents: 0,
          message: `Failed to read audit log at ${auditLogPath}: ${err.message}. Data source unreadable.`,
        },
      };
    }
  
    const entries = [];
    for (const line of lines) {
      try {
        entries.push(JSON.parse(line));
      } catch {
        // 跳过损坏的行，不阻断整体报告生成
      }
    }
  
    const byRiskLevel = {};
    const byDecision = {};
    const byEcosystem = {};
    for (const e of entries) {
      const riskKey = e.risk_level ?? 'unknown';
      const decisionKey = e.decision ?? 'unknown';
      const ecosystemKey = e.ecosystem ?? 'unknown';
      byRiskLevel[riskKey] = (byRiskLevel[riskKey] || 0) + 1;
      byDecision[decisionKey] = (byDecision[decisionKey] || 0) + 1;
      byEcosystem[ecosystemKey] = (byEcosystem[ecosystemKey] || 0) + 1;
    }
  
    const safeTimestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const reportDir = join(dirname(auditLogPath), 'reports');
    mkdirSync(reportDir, { recursive: true });
    const reportPath = join(reportDir, `report-${safeTimestamp}.md`);
  
    const markdown = renderReportMarkdown(entries, byRiskLevel, byDecision, byEcosystem, { auditLogPath });
    writeFileSync(reportPath, markdown, 'utf-8');
  
    return {
      reportPath,
      summary: {
        totalEvents: entries.length,
        byRiskLevel,
        byDecision,
        byEcosystem,
      },
    };
  }
  
  
  // Module exports
  __audit_log__.appendAuditLog = appendAuditLog;
  __audit_log__.buildAuditEntry = buildAuditEntry;
  __audit_log__.escapeMarkdownTableCell = escapeMarkdownTableCell;
  __audit_log__.renderReportMarkdown = renderReportMarkdown;
  __audit_log__.buildReportOutput = buildReportOutput;
  __audit_log__.DEFAULT_AUDIT_LOG = DEFAULT_AUDIT_LOG;
})();


// ============================================================================
// Module: rollout
// ============================================================================

(function() {
  /**
   * Progressive Rollout (O2-31) —— cohort 分配 + feature flag 客户端机制
   *
   * 设计原则（对齐 fix_update/optimizations/31_Progressive_Rollout.md）：
   * - cohort 分配稳定：相同 repo_id 总是分到同一个 0-99 bucket，不会每次漂移
   * - feature flag 从配置文件读取（~/.codebuddy/plugins/chainguard/flags.json）
   * - kill switch：任何 flag 可被全局关闭，不依赖故障数据源
   * - flag 配置签名/认证留给 v2（需要 Server 端签名服务，见 DQ-15）
   *
   * 当前切片实现：
   * - assignCohort(repo_id) → 0-99 整数（稳定哈希）
   * - isEnabled(flagName, context) → boolean（基于 cohort + flag 配置）
   * - 默认安全：flag 缺失/非法/过期时回到旧行为（false，不启用新功能）
   *
   * 不在本切片范围（DQ-15）：
   * - flag 配置签名/认证（需要 Server 端签名服务）
   * - 自动回滚 guardrail（需要 Dashboard 实时指标 + 自动化触发器）
   * - Server 端 cohort 比较 API
   */
  
  const { createHash } = require('crypto');
  const { readFileSync, existsSync } = require('fs');
  const { homedir } = require('os');
  const { join } = require('path');
  
  const FLAGS_FILE = join(homedir(), '.codebuddy', 'plugins', 'chainguard', 'flags.json');
  
  // 进程内缓存：flag 配置只在首次访问时读取一次
  let _flagsCache = null;
  let _flagsCacheTime = 0;
  const FLAGS_CACHE_TTL_MS = 60000; // 60 秒
  
  /**
   * 稳定 cohort 分配：相同 repo_id 总是分到同一个 0-99 bucket。
   *
   * 使用 sha256(repo_id) 的前 8 字节作为 uint32，mod 100 得到 bucket。
   * 不引入随机盐——稳定性是 cohort 的核心要求（文档："不能每次随机漂移"）。
   *
   * @param {string} repoId - 仓库身份指纹（D1-28 的 repo_id 字段）
   * @returns {number} 0-99 整数
   */
  function assignCohort(repoId) {
    if (!repoId) return 0; // 无 repo_id 时默认 bucket 0（最保守）
    const hash = createHash('sha256').update(repoId).digest();
    const bucket = hash.readUInt32BE(0) % 100;
    return bucket;
  }
  
  /**
   * 读取 flag 配置文件（带 TTL 缓存）。
   *
   * 配置文件格式（~/.codebuddy/plugins/chainguard/flags.json）：
   * {
   *   "parser_pipfile": {
   *     "enabled": true,
   *     "rollout_pct": 50,        // 启用范围 0-100
   *     "expires_at": "2026-12-31", // 可选，过期后 flag 失效
   *     "owner": "team-chainguard"
   *   },
   *   "kill_switch_autofix": {
   *     "enabled": false,          // kill switch: 全局关闭 autofix
   *     "rollout_pct": 0
   *   }
   * }
   *
   * 缺失/非法/过期 flag 一律视为 disabled（默认安全）。
   */
  function loadFlags() {
    const now = Date.now();
    if (_flagsCache && (now - _flagsCacheTime) < FLAGS_CACHE_TTL_MS) {
      return _flagsCache;
    }
  
    try {
      if (!existsSync(FLAGS_FILE)) {
        _flagsCache = {};
        _flagsCacheTime = now;
        return _flagsCache;
      }
      const raw = readFileSync(FLAGS_FILE, 'utf-8');
      const parsed = JSON.parse(raw);
      if (typeof parsed !== 'object' || parsed === null) {
        _flagsCache = {};
      } else {
        _flagsCache = parsed;
      }
    } catch {
      // 读取/解析失败：默认安全（空 flag 集）
      _flagsCache = {};
    }
    _flagsCacheTime = now;
    return _flagsCache;
  }
  
  /**
   * 清空 flag 缓存（主要用于测试）。
   */
  function clearFlagsCache() {
    _flagsCache = null;
    _flagsCacheTime = 0;
  }
  
  /**
   * 判断某个 feature flag 是否对当前上下文启用。
   *
   * 启用条件（全部满足）：
   * 1. flag 存在于配置且 `enabled: true`
   * 2. flag 未过期（`expires_at` 未到）
   * 3. cohort bucket < `rollout_pct`（如 rollout_pct=50，cohort 0-49 启用，50-99 不启用）
   *
   * 任何条件不满足 / 配置缺失 / 解析错误 → 返回 false（默认安全，回到旧行为）。
   *
   * @param {string} flagName - flag 名称（如 'parser_pipfile'）
   * @param {Object} context - 上下文（需包含 repo_id 用于 cohort 分配）
   * @param {string} [context.repo_id] - 仓库身份指纹
   * @returns {boolean}
   */
  function isEnabled(flagName, context = {}) {
    const flags = loadFlags();
    const flag = flags[flagName];
    if (!flag || typeof flag !== 'object') return false;
    if (flag.enabled !== true) return false;
  
    // 过期检查
    if (flag.expires_at) {
      const expiry = new Date(flag.expires_at);
      if (isNaN(expiry.getTime())) return false; // 非法日期 → 默认安全
      if (Date.now() > expiry.getTime()) return false;
    }
  
    // rollout 百分比检查
    const rolloutPct = typeof flag.rollout_pct === 'number' ? flag.rollout_pct : 0;
    if (rolloutPct <= 0) return false;
    if (rolloutPct >= 100) return true;
  
    // cohort 分配
    const cohort = assignCohort(context.repo_id || '');
    return cohort < rolloutPct;
  }
  
  /**
   * 获取所有 flag 的当前状态（用于 --status 诊断输出）。
   * 不暴露 owner 等元数据，只返回 enabled + rollout_pct + expires_at。
   */
  function getFlagsStatus() {
    const flags = loadFlags();
    const result = {};
    for (const [name, flag] of Object.entries(flags)) {
      if (typeof flag !== 'object') continue;
      result[name] = {
        enabled: flag.enabled === true,
        rollout_pct: typeof flag.rollout_pct === 'number' ? flag.rollout_pct : 0,
        expires_at: flag.expires_at || null,
      };
    }
    return result;
  }
  
  
  // Module exports
  __rollout__.assignCohort = assignCohort;
  __rollout__.clearFlagsCache = clearFlagsCache;
  __rollout__.isEnabled = isEnabled;
  __rollout__.getFlagsStatus = getFlagsStatus;
})();


// ============================================================================
// Module: telemetry
// ============================================================================

(function() {
  /**
   * Telemetry - Hook 埋点数据收集与上送
   *
   * 设计原则：
   * - recordAndSend() 在 stdout.write() 之后的 setImmediate 中调用，绝不阻塞主流程
   * - 上送超时 3000ms，失败静默丢弃（主流程已结束，不影响用户体验）
   * - 全链路 try/catch，不向外抛任何异常
   * - 复用 tls.js 的 buildTlsOptions()，与主流程共享 TLS 证书信任策略
   * - 落盘由 server 端负责，client 不做本地写盘
   */
  const { request: httpsRequest } = require('https');
  const { request: httpRequest } = require('http');
  const { URL, fileURLToPath } = require('url');
  const { readFileSync } = require('fs');
  const { dirname, resolve } = require('path');
  const buildSessionHeaders = __auth_session_reader__.buildSessionHeaders;
  const buildTlsOptions = __tls__.buildTlsOptions;
  const UI = __ui__.UI;
  const detectRepo = __repo__.detectRepo;
  const SEND_TIMEOUT_MS = 3000;
  // 从 package.json 读取版本号，避免硬编码
  const CLIENT_VERSION = '1.3.0'; // injected by bundle-cjs.js
  /**
   * 采集一次 hook 执行事件并异步上送
   *
   * 调用时机：process.stdout.write(hookResponse) 之后，在 setImmediate 回调内
   *
   * @param {Object} event  - 埋点字段（见字段清单）
   * @param {string} serverUrl - 上送目标（复用主流程的 serverUrl）
   */
  function recordAndSend(event, serverUrl, cwd) {
    // 检测 repo 信息（如果 event 已包含 repo 字段，则不覆盖）
    let repo = {};
    if (!event.repo_name) {
      try {
        repo = detectRepo(cwd ? { cwd } : undefined);
      } catch {
        // repo 检测失败 fail-open，不影响 telemetry 发送
        repo = {
          repo_name: '',
          repo_branch: '',
          repo_detection_source: 'none'
        };
      }
    }
    
    const payload = {
      ts: Date.now(),
      client_ver: CLIENT_VERSION,
      ...event,
      ...repo, // 合并 repo 字段
    };
    // 异步上送，fire-and-forget
    const telemetryUrl = `${serverUrl}/telemetry/hook-event`;
    UI.log(`[TELEMETRY] sending server_status=${payload.server_status ?? '-'} hook_decision=${payload.hook_decision ?? '-'} ecosystem=${payload.ecosystem ?? '-'} tool=${payload.tool_name ?? '-'} to ${telemetryUrl}`);
    _sendAsync(payload, serverUrl, '/telemetry/hook-event');
  }
  /**
   * 采集一次采纳闭环事件并异步上送
   *
   * @param {Object} event - 采纳闭环字段
   * @param {string} serverUrl - 上送目标
   * @param {string} [cwd] - 执行路径
   */
  async function recordAdoptionEvent(event, serverUrl, cwd) {
    if (!serverUrl) return;
    let repo = {};
    if (!event.repo_name) {
      try {
        repo = detectRepo(cwd ? { cwd } : undefined);
      } catch {
        repo = {
          repo_name: '',
          repo_branch: '',
          repo_detection_source: 'none'
        };
      }
    }
    const payload = {
      ts: Date.now(),
      client_ver: CLIENT_VERSION,
      event_type: 'adoption_event',
      ...event,
      ...repo,
    };
    UI.log(`[TELEMETRY] sending adoption_event pkg=${payload.package_name ?? '-'} status=${payload.status ?? '-'} commit=${payload.commit_sha ?? '-'}`);
    try {
      await _doSend(payload, serverUrl, '/telemetry/hook-event', false);
    } catch (err) {
      UI.log(`[TELEMETRY] adoption_event send failed: ${err?.message ?? err}`);
    }
  }
  /**
   * 异步上送，不 await，不向外抛异常
   * @param {Object} payload
   * @param {string} serverUrl
   * @param {string} [path]
   */
  function _sendAsync(payload, serverUrl, path = '/telemetry/hook-event') {
    _doSend(payload, serverUrl, path, true).catch((err) => {
      UI.log(`[TELEMETRY] send failed: ${err?.message ?? err}`);
    });
  }
  /**
   * 实际 HTTP 上送（使用 node:https/node:http，复用 TLS 配置）
   * @param {Object} payload
   * @param {string} serverUrl
   * @param {string} [path]
   * @param {boolean} [unrefSocket] 是否 unref 底层 socket
   * @returns {Promise<void>}
   */
  function _doSend(payload, serverUrl, path = '/telemetry/hook-event', unrefSocket = true) {
    return new Promise((resolve, reject) => {
      try {
        const url = new URL(`${serverUrl}${path}`);
        const isHttps = url.protocol === 'https:';
        const tlsOptions = isHttps ? buildTlsOptions() : {};
        const sessionHeaders = buildSessionHeaders();
        const body = JSON.stringify(payload);
        const options = {
          hostname: url.hostname,
          port: url.port || (isHttps ? 443 : 80),
          path: url.pathname + url.search,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(body),
            'X-Service-Id': 'chainguard',
            ...sessionHeaders,
          },
          ...tlsOptions,
        };
        const req = (isHttps ? httpsRequest : httpRequest)(options, (res) => {
          // 消耗响应体，不关心内容
          res.resume();
          res.on('end', () => {
            // 网关 401：静默丢弃，不触发任何重试（避免 CodeBuddy 登出）
            if (res.statusCode === 401) {
              UI.log(`[TELEMETRY] gateway 401, discarding silently`);
              resolve();
              return;
            }
            UI.log(`[TELEMETRY] sent ok status=${res.statusCode} server_status=${payload.server_status ?? '-'} hook_decision=${payload.hook_decision ?? '-'} ecosystem=${payload.ecosystem ?? '-'}`);
            resolve();
          });
        });
        if (unrefSocket) {
          req.on('socket', (socket) => {
            socket.unref();
          });
        }
        // 超时处理
        req.setTimeout(SEND_TIMEOUT_MS, () => {
          req.destroy();
          UI.log(`[TELEMETRY] send timeout after ${SEND_TIMEOUT_MS}ms`);
          reject(new Error('telemetry_timeout'));
        });
        req.on('error', reject);
        req.write(body);
        req.end();
      } catch (err) {
        reject(err);
      }
    });
  }
  __telemetry__.default = recordAndSend;
  
  // Module exports
  __telemetry__.recordAndSend = recordAndSend;
  __telemetry__.recordAdoptionEvent = recordAdoptionEvent;
})();


// ============================================================================
// Module: dedup
// ============================================================================

(function() {
  /**
   * D1-14: 全原因 Session 去重（Session-Wide Deduplication）
   *
   * 修复背景：此前循环控制主要覆盖有 fix list 的 Autofix 场景（D1-19 的 fix-info
   * 跨操作降级检测）。License deny、package-not-found、无修复 CVE、fatal 熔断等
   * 阻断原因，在 Agent 重试时会用完全相同的输入反复触发相同的 deny/ask，每次都
   * 重新展示完整的 systemMessage/additionalContext——既没有帮助 Agent 意识到
   * "重试没有意义"，也造成日志/上下文的重复膨胀。
   *
   * 本模块只负责"计算指纹 + 按 session 维护状态机"，不负责决定响应内容如何收缩
   * （那部分在 index.js 的 applyDedup() 里做，保持 response.js 的 builder 函数
   * 是不感知去重的纯函数，最小侵入）。
   *
   * 状态机语义（对应文档 FIRST_SEEN → RESPOND_ONCE / UNCHANGED_RETRY →
   * SUPPRESS_OR_STOP / INPUT_CHANGED → REEVALUATE）：
   * - first:      本次 fingerprint 在会话内首次出现，或输入已变化（新 fingerprint）——完整展示。
   * - suppressed: 相同 fingerprint 重复出现（未达终止阈值）——收缩为短 machine reason。
   * - terminal:   相同 fingerprint 达到终止阈值——明确要求停止自动重试。
   *
   * 存储：会话级 tmpdir 状态文件，与 D1-15（readiness）、D1-19（fix-info）同构，
   * 复用同一套"按 session/操作派生独立文件名 + TTL 清理"模式，而不是引入新机制。
   */
  
  const { createHash } = require('crypto');
  const { readFileSync, writeFileSync, readdirSync, statSync, unlinkSync } = require('fs');
  const { tmpdir } = require('os');
  const { join: pathJoin } = require('path');
  
  const DEDUP_FILE_PREFIX = 'security-guard-dedup-';
  const DEDUP_TTL_MS = 30 * 60 * 1000;      // 30 分钟：覆盖一次典型会话的时长
  const MAX_ENTRIES_PER_SESSION = 50;       // 超过则按 lastSeen 做 LRU 淘汰，避免长会话无限增长
  const TERMINAL_THRESHOLD = 3;             // 第 3 次起判定为 TERMINAL_LOOP
  
  /**
   * 计算稳定的操作指纹（SHA-256，截断到 32 位十六进制）。
   *
   * 只使用包名（归一化小写）、版本号、decision、reason code、fix target 参与计算，
   * 不包含完整文件内容、命令原文、路径或私有包明文——符合文档"不得包含完整文件、
   * 命令、路径和私有包明文"的要求（私有包在到达这里之前已经过隐私过滤器移除）。
   *
   * @param {Object} input
   * @param {string} [input.toolName]
   * @param {string} [input.ecosystem]
   * @param {Array<{n?: string, v?: string}>} [input.packages]
   * @param {string} [input.decision] - 'BLOCK' | 'WARN' | ...
   * @param {string} [input.reasonCode]
   * @param {string} [input.fixTarget]
   * @returns {string} 32 位十六进制指纹
   */
  function computeFingerprint({ toolName, ecosystem, packages, decision, reasonCode, fixTarget, contentHash } = {}) {
    const pkgPart = (Array.isArray(packages) ? packages : [])
      .map(p => `${String(p?.n ?? '').toLowerCase()}@${p?.v ?? ''}`)
      .sort()
      .join(',');
  
    const raw = [
      toolName || '',
      ecosystem || '',
      pkgPart,
      decision || '',
      reasonCode || '',
      fixTarget || '',
      // D2-v4: 可选内容哈希，用于精确判定“完全相同失败输入又提交一遍”。
      // 缺省为空串（向后兼容现有 22 个 dedup 测试，不改变其指纹）。
      // 注意：仅哈希，不含明文/路径/私有包（隐私约束）。
      contentHash || '',
    ].join('|');
  
    return createHash('sha256').update(raw).digest('hex').slice(0, 32);
  }
  
  /**
   * D2-v4: 计算“当前仍 actionable 的 finding 唯一标识集合”的摘要。
   *
   * finding 标识优先使用 package + currentVersion + vulnId/reasonCode，
   * 来源是下一轮 Server 重新审计结果（归一化 unfixable + changes 里仍 BLOCK 的项），
   * 不新增 Server 字段。
   *
   * @param {Array<{n?: string, v?: string, cve?: string, reason?: string, reason_code?: string}>} findings
   * @returns {string} 32 位十六进制摘要；findings 为空返回 'EMPTY'
   */
  function findingSetDigest(findings) {
    const list = (Array.isArray(findings) ? findings : [])
      .map(f => {
        const name = String(f?.n ?? f?.package ?? '').toLowerCase();
        const ver = f?.v ?? f?.version ?? '';
        const vid = f?.cve ?? f?.vulnId ?? '';
        const rc = f?.reason_code ?? f?.reason ?? '';
        return `${name}@${ver}#${vid}|${rc}`;
      })
      .sort();
    if (list.length === 0) return 'EMPTY';
    return createHash('sha256').update(list.join(',')).digest('hex').slice(0, 32);
  }
  
  function safeSessionKey(sessionId) {
    return String(sessionId).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 128);
  }
  
  // D2-v4: remediation session 状态文件独立存放（与 exact-fingerprint 状态分离），
  // 以 sessionKey（tool+file+sessionId）为锚，跟踪“连续相同 finding state”的 no-progress streak。
  const REMEDIATION_FILE_PREFIX = 'security-guard-remediation-';
  
  function remediationStatePath(sessionId, sessionKey) {
    const sk = safeSessionKey(sessionKey || sessionId || 'unknown');
    return pathJoin(tmpdir(), `${REMEDIATION_FILE_PREFIX}${safeSessionKey(sessionId)}__${sk}.json`);
  }
  
  /**
   * D2-v4: 精确清除某条 dedup fingerprint 的 retry 计数。
   * 用于 exact retry 场景（完全相同输入又提交）。不影响其他 fingerprint / remediation session。
   *
   * @param {string|null} sessionId
   * @param {string} fingerprint - computeFingerprint() 的输出
   */
  function resetExactFingerprint(sessionId, fingerprint) {
    if (!sessionId || !fingerprint) return;
    try {
      const statePath = dedupStatePath(sessionId);
      const state = readState(statePath);
      if (state[fingerprint]) {
        delete state[fingerprint];
        writeState(statePath, state);
      }
    } catch {
      // 清失败不影响主流程（下次可能重新计为 first），静默
    }
  }
  
  /**
   * D2-v4: 重置整个 remediation session 的失败状态。
   *
   * 用于“本轮 remediation 已结束”的场景：
   *   - Server decision === 'PASS'
   *   - actionable finding set 为空
   *   - smooth autofix 成功落盘后
   *
   * 注意：PASS 这一轮 contentHash 已变（vulnerable H1 → clean H2），
   * 不能只 reset(currentHash)（清不掉真正积累 retry 的 H1），
   * 必须以 sessionKey 为锚清掉 session 内记录的 lastFailureFingerprint + noProgressStreak。
   *
   * @param {string|null} sessionId
   * @param {string} sessionKey - tool + normalizedFilePath + sessionId
   */
  function resetRemediationSession(sessionId, sessionKey) {
    if (!sessionId) return;
    try {
      const statePath = remediationStatePath(sessionId, sessionKey);
      // 直接删除 session 文件即完成 reset（noProgressStreak + lastFailureFingerprint 一并清空）
      try { unlinkSync(statePath); } catch { /* 不存在则无操作 */ }
    } catch {
      // 静默
    }
  }
  
  /**
   * D2-v4: 跟踪 remediation progress，判断“是否连续无进展”。
   *
   * 判定规则（基于 finding state 而非 retry 次数）：
   *   - current === 'EMPTY'          → session resolved，reset，streak=0
   *   - current === previous         → no progress，streak++
   *   - current ⊂ previous (严格子集) → progress，streak=0
   *   - current changed but not subset（如 {A}→{B}）→ state changed，streak=0（不当无进展，避免误熔断）
   *
   * @param {string|null} sessionId
   * @param {string} sessionKey
   * @param {string} currentDigest - findingSetDigest() 的输出（'EMPTY' 或哈希）
   * @returns {{noProgressStreak: number, shouldTrip: boolean, resolved: boolean, progressed: boolean}}
   */
  function trackRemediationProgress(sessionId, sessionKey, currentDigest) {
    const empty = { noProgressStreak: 0, shouldTrip: false, resolved: false, progressed: false };
    if (!sessionId || !currentDigest) return empty;
  
    try {
      const statePath = remediationStatePath(sessionId, sessionKey);
      const now = Date.now();
      const state = readState(statePath);
  
      if (currentDigest === 'EMPTY') {
        // 本轮已无 actionable finding → session resolved
        try { unlinkSync(statePath); } catch { /* noop */ }
        return { noProgressStreak: 0, shouldTrip: false, resolved: true, progressed: true };
      }
  
      const previous = state.findingDigest || null;
      let noProgressStreak = state.noProgressStreak || 0;
      let progressed = false;
  
      if (previous === null) {
        // 第一次记录：baseline 即视为「第 1 次相同状态」，streak=1。
        // 与 TERMINAL_THRESHOLD=3 对齐：第2次相同→2，第3次相同→3 即 trip。
        noProgressStreak = 1;
      } else if (previous === currentDigest) {
        // 完全相同失败状态 → 无进展（累加）
        noProgressStreak = (state.noProgressStreak || 0) + 1;
      } else {
        // 状态变化（含严格子集 / 换包 / 增删）→ 不算无进展，streak 清零
        noProgressStreak = 0;
        progressed = true;
      }
  
      state.findingDigest = currentDigest;
      state.noProgressStreak = noProgressStreak;
      state.lastSeenTs = now;
      writeState(statePath, state);
  
      const shouldTrip = noProgressStreak >= TERMINAL_THRESHOLD;
      return { noProgressStreak, shouldTrip, resolved: false, progressed };
    } catch {
      // 异常不阻塞主流程，保守返回“不熔断”
      return empty;
    }
  }
  
  function dedupStatePath(sessionId) {
    return pathJoin(tmpdir(), `${DEDUP_FILE_PREFIX}${safeSessionKey(sessionId)}.json`);
  }
  
  function readState(statePath) {
    try {
      const parsed = JSON.parse(readFileSync(statePath, 'utf-8'));
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch {
      // 文件不存在（会话第一次写入）或损坏，视为空状态——保守选择，不阻塞主流程
      return {};
    }
  }
  
  function writeState(statePath, state) {
    try {
      writeFileSync(statePath, JSON.stringify(state), { mode: 0o600 });
    } catch {
      // 写入失败不影响本次判断结果，只是下次可能重新计为 first
    }
  }
  
  /**
   * 对本次 fingerprint 分类并更新会话状态。
   *
   * @param {string|null} sessionId - 当前会话 ID，缺失时无法去重
   * @param {string} fingerprint - computeFingerprint() 的输出
   * @returns {{state: 'first'|'suppressed'|'terminal', retryCount: number}}
   */
  function classifyAndRecord(sessionId, fingerprint) {
    if (!sessionId || !fingerprint) {
      // 无 session_id 时无法去重——比"永远不提示"更安全的选择是每次都完整展示
      return { state: 'first', retryCount: 1 };
    }
  
    try {
      const statePath = dedupStatePath(sessionId);
      const now = Date.now();
      const state = readState(statePath);
  
      // 清理过期条目（不属于本次 fingerprint 的旧记录，防止 TTL 到期后仍参与 LRU 判断）
      for (const key of Object.keys(state)) {
        if (now - (state[key]?.lastSeenTs ?? 0) > DEDUP_TTL_MS) {
          delete state[key];
        }
      }
  
      const existing = state[fingerprint];
      const retryCount = existing ? existing.count + 1 : 1;
      state[fingerprint] = {
        count: retryCount,
        firstSeenTs: existing ? existing.firstSeenTs : now,
        lastSeenTs: now,
      };
  
      // LRU 淘汰：超过容量时丢弃 lastSeenTs 最旧的条目（保留刚更新的当前 fingerprint）
      const keys = Object.keys(state);
      if (keys.length > MAX_ENTRIES_PER_SESSION) {
        keys
          .sort((a, b) => state[a].lastSeenTs - state[b].lastSeenTs)
          .slice(0, keys.length - MAX_ENTRIES_PER_SESSION)
          .forEach(key => delete state[key]);
      }
  
      writeState(statePath, state);
  
      if (retryCount >= TERMINAL_THRESHOLD) return { state: 'terminal', retryCount };
      if (retryCount > 1) return { state: 'suppressed', retryCount };
      return { state: 'first', retryCount };
    } catch {
      // 任何异常都不应阻塞主流程；保守选择"完整展示"而不是"永久静默"
      return { state: 'first', retryCount: 1 };
    }
  }
  
  /**
   * 清理过期的去重状态文件（TTL 回收），避免异常退出场景下的文件无限堆积。
   * 与 D1-19 的 cleanupStaleFixInfoFiles() 同构，静默失败：清理本身不是关键路径。
   */
  function cleanupStaleDedupFiles() {
    try {
      const dir = tmpdir();
      const now = Date.now();
      for (const name of readdirSync(dir)) {
        if (!name.startsWith(DEDUP_FILE_PREFIX) || !name.endsWith('.json')) continue;
        const fullPath = pathJoin(dir, name);
        try {
          const stat = statSync(fullPath);
          if (now - stat.mtimeMs > DEDUP_TTL_MS) {
            unlinkSync(fullPath);
          }
        } catch {
          // 单个文件清理失败不影响其他文件，静默跳过
        }
      }
    } catch {
      // 目录读取失败（权限/不存在等），静默忽略，不影响主流程
    }
  }
  
  
  // Module exports
  __dedup__.computeFingerprint = computeFingerprint;
  __dedup__.findingSetDigest = findingSetDigest;
  __dedup__.resetExactFingerprint = resetExactFingerprint;
  __dedup__.resetRemediationSession = resetRemediationSession;
  __dedup__.trackRemediationProgress = trackRemediationProgress;
  __dedup__.classifyAndRecord = classifyAndRecord;
  __dedup__.cleanupStaleDedupFiles = cleanupStaleDedupFiles;
})();


// ============================================================================
// Module: build_info
// ============================================================================

(function() {
  function getBuildInfo() {
    return {
    "plugin_version": "1.3.0",
    "client_version": "1.3.0",
    "source_revision": "639a29c4b28d95b1b241b9ac6f4fb76321ea946e",
    "build_timestamp": "2026-10-21T10:19:46.686Z",
    "build_profile": "release-bundled",
    "dirty": false,
    "obfuscator_config_sha256": null,
    "protocol_schema_version": 2
  };
  }
  
  __build_info__.default = getBuildInfo;
  
  
  // Module exports
  __build_info__.getBuildInfo = getBuildInfo;
})();


// ============================================================================
// Module: adoption
// ============================================================================

(function() {
  /**
   * Adoption Closed-Loop Module (产研采纳与风险消除闭环模块)
   *
   * 核心目标：
   * 追踪产研工程师或 Claude Code Agent 在收到供应链安全建议/拦截后，
   * 是否最终采纳建议并提交到 Git 代码库中。
   *
   * 状态机：
   * - PENDING:   PreToolUse 拦截/建议下发，写入待闭环状态
   * - ADOPTED:   git commit 包含该组件，且版本 >= 建议安全版本
   * - BYPASSED:  git commit 包含该组件，但版本仍为高危版本（产研绕过）
   * - REMOVED:   git commit 清单中移除了该组件（放弃引入）
   * - ABANDONED: 会话结束（Stop hook）或超时未提交（会话放弃/代码回滚）
   *
   * 对标实现：Anthropic official security-guidance plugin
   */
  
  const { readFileSync, writeFileSync, renameSync, unlinkSync, existsSync, statSync } = require('fs');
  const { resolve, relative, isAbsolute, join: pathJoin, basename } = require('path');
  const { tmpdir } = require('os');
  const { execFileSync } = require('child_process');
  const { createHash } = require('crypto');
  const parseManifest = __parsers_manifests_index__.parseManifest;
  const compareVersions = __version__.compareVersions;
  const extractVersion = __version__.extractVersion;
  const recordAdoptionEvent = __telemetry__.recordAdoptionEvent;
  const UI = __ui__.UI;
  
  const PENDING_STORE_TTL_MS = 24 * 60 * 60 * 1000; // 24 小时
  const GIT_TIMEOUT_MS = 5000;
  
  // 正则匹配 git commit 命令
  const GIT_COMMIT_RE = /(?:^|\s|&&|;|\|\|)git(?:\.exe)?\s+commit(?:\s+|$)/i;
  const GIT_AMEND_RE = /(?:^|\s|&&|;|\|\|)git(?:\.exe)?\s+commit\s+.*--amend(?:\s+|$)/i;
  // 提取 [branch-name abc1234] 格式的 commit sha
  const COMMIT_SHA_RE = /\[(?:[\w.\-_/]+)\s+([a-f0-9]{7,40})\]/;
  
  /**
   * 获取 Git 根目录（带 fail-safe 保护）
   *
   * @param {string} [cwd]
   * @returns {string|null}
   */
  function findGitRoot(cwd) {
    try {
      const root = execFileSync('git', ['rev-parse', '--show-toplevel'], {
        cwd: cwd || process.cwd(),
        timeout: 3000,
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'ignore'],
      }).trim();
      return root || null;
    } catch {
      return null;
    }
  }
  
  /**
   * 获取待采纳状态存储文件路径
   *
   * @param {string} [cwd]
   * @returns {string}
   */
  function getAdoptionStorePath(cwd) {
    const gitRoot = findGitRoot(cwd);
    if (gitRoot) {
      const gitDir = pathJoin(gitRoot, '.git');
      if (existsSync(gitDir)) {
        return pathJoin(gitDir, 'sg-pending-adoptions.json');
      }
    }
    const key = createHash('sha256').update(gitRoot || cwd || process.cwd()).digest('hex').slice(0, 8);
    return pathJoin(tmpdir(), `sg-pending-adoptions-${key}.json`);
  }
  
  /**
   * 读取待采纳状态
   *
   * @param {string} storePath
   * @returns {{ version: number, records: Object }}
   */
  function loadPendingAdoptions(storePath) {
    try {
      if (!existsSync(storePath)) {
        return { version: 1, records: {} };
      }
      const raw = readFileSync(storePath, 'utf-8');
      const parsed = JSON.parse(raw);
      const records = parsed.records || {};
      const now = Date.now();
      const active = {};
      for (const [key, item] of Object.entries(records)) {
        if (item && item.created_at && (now - item.created_at) < PENDING_STORE_TTL_MS) {
          active[key] = item;
        }
      }
      return { version: 1, records: active };
    } catch {
      return { version: 1, records: {} };
    }
  }
  
  /**
   * 原子保存待采纳状态
   *
   * @param {string} storePath
   * @param {Object} data
   */
  function savePendingAdoptions(storePath, data) {
    try {
      const tmp = `${storePath}.${process.pid}.${Date.now()}.tmp`;
      writeFileSync(tmp, JSON.stringify(data, null, 2), { mode: 0o600, encoding: 'utf-8' });
      renameSync(tmp, storePath);
    } catch (err) {
      UI.log(`[ADOPTION] failed to save store ${storePath}: ${err.message}`);
    }
  }
  
  /**
   * 从变更或包名中抽取包名
   *
   * @param {string} spec
   * @returns {string}
   */
  function extractPackageName(spec) {
    if (typeof spec !== 'string') return '';
    let s = spec.trim();
    // 去除 ==, >=, @version 等
    const atIdx = s.lastIndexOf('@');
    if (atIdx > 0) {
      return s.slice(0, atIdx).trim();
    }
    const match = s.match(/^([a-zA-Z0-9_\-./@]+?)(?:[=><~^]|$)/);
    return match ? match[1].trim() : s;
  }
  
  /**
   * 记录待采纳的安全建议项
   *
   * @param {Object} params
   */
  function recordPendingAdoptions({
    ecosystem,
    packages = [],
    changes = [],
    unfixable = [],
    serverResponse = {},
    toolInput = {},
    inputRaw = {},
    cwd = null,
  }) {
    try {
      const pendingItems = [];
      const eco = ecosystem || 'unknown';
  
      // 1. 处理 autofix 推荐变更
      if (Array.isArray(changes) && changes.length > 0) {
        for (const ch of changes) {
          const pkgName = extractPackageName(ch.from || ch.to);
          const blockedVer = extractVersion(ch.from) || '';
          const suggestedVer = extractVersion(ch.to) || '';
          if (pkgName) {
            pendingItems.push({
              ecosystem: eco,
              name: pkgName,
              blocked_version: blockedVer,
              suggested_version: suggestedVer,
              action_type: serverResponse.decision === 'BLOCK' ? 'BLOCK_WITH_AUTOFIX' : 'WARN_WITH_AUTOFIX',
              cve_ids: ch.cve ? [ch.cve] : [],
              license_risk: serverResponse.license_info?.risk_level || null,
            });
          }
        }
      }
  
      // 2. 处理 unfixable 高危项
      if (Array.isArray(unfixable) && unfixable.length > 0) {
        for (const u of unfixable) {
          if (u.n) {
            pendingItems.push({
              ecosystem: eco,
              name: u.n,
              blocked_version: u.v || '',
              suggested_version: null,
              action_type: 'BLOCK_UNFIXABLE',
              cve_ids: u.cve ? [u.cve] : [],
              license_risk: null,
            });
          }
        }
      }
  
      // 3. 处理单纯的 License 拦截或无 changes 的直接拦截
      if (pendingItems.length === 0 && (serverResponse.decision === 'BLOCK' || serverResponse.decision === 'WARN')) {
        for (const p of packages) {
          const pkgName = p.n || p.name;
          if (pkgName) {
            pendingItems.push({
              ecosystem: eco,
              name: pkgName,
              blocked_version: p.v || p.version || '',
              suggested_version: null,
              action_type: serverResponse.decision,
              cve_ids: [],
              license_risk: serverResponse.license_info?.risk_level || (serverResponse.policy_result?.license_status === 'DENIED' ? 'HIGH' : null),
            });
          }
        }
      }
  
      if (pendingItems.length === 0) return;
  
      const storePath = getAdoptionStorePath(cwd);
      const store = loadPendingAdoptions(storePath);
      const now = Date.now();
      const manifestPath = toolInput.file_path || null;
  
      for (const item of pendingItems) {
        const recordKey = `${item.ecosystem}:${item.name}`;
        store.records[recordKey] = {
          ...item,
          session_id: inputRaw.session_id || null,
          call_id: inputRaw.call_id || null,
          tool_use_id: inputRaw.tool_use_id || null,
          manifest_path: manifestPath,
          created_at: now,
        };
        UI.log(`[ADOPTION] recorded pending recommendation: ${recordKey} (suggested: ${item.suggested_version || 'none'})`);
      }
  
      savePendingAdoptions(storePath, store);
    } catch (err) {
      UI.log(`[ADOPTION] recordPendingAdoptions error: ${err.message}`);
    }
  }
  
  /**
   * 判断命令是否为 git commit
   *
   * @param {string} command
   * @returns {boolean}
   */
  function isGitCommitCommand(command) {
    if (typeof command !== 'string') return false;
    return GIT_COMMIT_RE.test(command);
  }
  
  /**
   * 判断是否为 git commit --amend
   *
   * @param {string} command
   * @returns {boolean}
   */
  function isGitAmendCommand(command) {
    if (typeof command !== 'string') return false;
    return GIT_AMEND_RE.test(command);
  }
  
  /**
   * 解析本次提交产生的 Commit SHA
   *
   * @param {string} command
   * @param {string} output
   * @param {string} [cwd]
   * @returns {string|null}
   */
  function resolveCommitSha(command, output, cwd) {
    // 1. 优先从输出解析 [branch abc1234]
    if (output && typeof output === 'string') {
      const match = output.match(COMMIT_SHA_RE);
      if (match && match[1]) {
        return match[1];
      }
    }
  
    // 2. 回退通过 git rev-parse 获取
    try {
      const sha = execFileSync('git', ['rev-parse', 'HEAD'], {
        cwd: cwd || process.cwd(),
        timeout: 3000,
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'ignore'],
      }).trim();
      return sha || null;
    } catch {
      return null;
    }
  }
  
  /**
   * 获取某次提交包含的变更清单文件
   *
   * @param {string} sha
   * @param {string} [cwd]
   * @returns {string[]}
   */
  function getCommitChangedFiles(sha, cwd) {
    try {
      const out = execFileSync('git', ['show', '--name-only', '--format=', sha, '--'], {
        cwd: cwd || process.cwd(),
        timeout: GIT_TIMEOUT_MS,
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'ignore'],
      });
      return out.split('\n').map(s => s.trim()).filter(Boolean);
    } catch {
      return [];
    }
  }
  
  /**
   * 获取指定 commit 中的文件内容
   *
   * @param {string} sha
   * @param {string} relPath
   * @param {string} gitRoot
   * @returns {string|null}
   */
  function getFileContentAtCommit(sha, relPath, gitRoot) {
    try {
      return execFileSync('git', ['show', `${sha}:${relPath}`], {
        cwd: gitRoot,
        timeout: GIT_TIMEOUT_MS,
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'ignore'],
      });
    } catch {
      return null;
    }
  }
  
  /**
   * 核心检查：当 Bash 执行 git commit 后，审查提交是否采纳了安全建议
   *
   * @param {Object} params
   * @returns {Object[]} 已闭环判定的事件列表
   */
  async function inspectGitCommitAdoption({
    command,
    output = '',
    cwd = null,
    session_id = null,
    call_id = null,
    serverUrl = null,
  }) {
    const evaluatedEvents = [];
  
    try {
      const gitRoot = findGitRoot(cwd);
      if (!gitRoot) return evaluatedEvents;
  
      const storePath = getAdoptionStorePath(cwd);
      const store = loadPendingAdoptions(storePath);
      const keys = Object.keys(store.records);
      if (keys.length === 0) return evaluatedEvents;
  
      const sha = resolveCommitSha(command, output, cwd);
      if (!sha) return evaluatedEvents;
  
      const changedFiles = getCommitChangedFiles(sha, gitRoot);
      if (changedFiles.length === 0) return evaluatedEvents;
  
      const keysToRemove = [];
      const sendPromises = [];
  
      for (const key of keys) {
        const item = store.records[key];
        if (!item) continue;
  
        // 计算该组件对应的清单文件相对路径
        let targetRelPath = null;
        if (item.manifest_path) {
          targetRelPath = isAbsolute(item.manifest_path)
            ? relative(gitRoot, item.manifest_path).replace(/\\/g, '/')
            : item.manifest_path.replace(/\\/g, '/');
        }
  
        // 如果未记录具体清单路径，在 changedFiles 中匹配常见清单
        let matchedFile = null;
        if (targetRelPath && changedFiles.includes(targetRelPath)) {
          matchedFile = targetRelPath;
        } else {
          matchedFile = changedFiles.find(f => {
            const b = basename(f);
            return ['package.json', 'pom.xml', 'requirements.txt', 'Pipfile', 'pyproject.toml', 'Cargo.toml', 'go.mod'].includes(b);
          });
        }
  
        // 如果本次 commit 没有触及相关的清单文件，保留 PENDING，等待后续 commit
        if (!matchedFile) continue;
  
        // 读取 commit 中的清单内容
        const fileContent = getFileContentAtCommit(sha, matchedFile, gitRoot);
        let status = 'REMOVED';
        let finalVersion = null;
  
        if (fileContent !== null) {
          const parsed = parseManifest(matchedFile, fileContent);
          const pkg = parsed?.packages?.find(p => (p.name || p.n) === item.name);
          if (pkg) {
            finalVersion = pkg.version || pkg.v || '';
            if (item.suggested_version) {
              const cmp = compareVersions(finalVersion, item.suggested_version);
              if (cmp !== null && cmp >= 0) {
                status = 'ADOPTED';
              } else {
                status = 'BYPASSED';
              }
            } else {
              // 没有明确 autofix 建议版本的情况（例如被阻断的无解版本/高危包）
              if (item.blocked_version && finalVersion === item.blocked_version) {
                status = 'BYPASSED';
              } else {
                status = 'ADOPTED';
              }
            }
          } else {
            status = 'REMOVED';
          }
        }
  
        const event = {
          ecosystem: item.ecosystem,
          package_name: item.name,
          blocked_version: item.blocked_version,
          suggested_version: item.suggested_version,
          final_version: finalVersion,
          status,
          action_type: item.action_type,
          cve_ids: item.cve_ids || [],
          license_risk: item.license_risk || null,
          commit_sha: sha,
          session_id: session_id || item.session_id,
          call_id: call_id || item.call_id,
          duration_to_commit_sec: Math.max(0, Math.round((Date.now() - (item.created_at || Date.now())) / 1000)),
        };
  
        evaluatedEvents.push(event);
        keysToRemove.push(key);
  
        UI.log(`[ADOPTION] evaluated closed-loop for ${item.name}: status=${status} commit=${sha.slice(0, 7)}`);
  
        if (serverUrl) {
          sendPromises.push(recordAdoptionEvent(event, serverUrl, cwd));
        }
      }
  
      // 移除已闭环的记录并保存
      if (keysToRemove.length > 0) {
        for (const k of keysToRemove) {
          delete store.records[k];
        }
        savePendingAdoptions(storePath, store);
      }
  
      if (sendPromises.length > 0) {
        await Promise.allSettled(sendPromises);
      }
    } catch (err) {
      UI.log(`[ADOPTION] inspectGitCommitAdoption error: ${err.message}`);
    }
  
    return evaluatedEvents;
  }
  
  /**
   * 处理 Stop Hook 事件（会话终止时的未闭环归档）
   *
   * @param {Object} params
   */
  async function handleSessionStop({ session_id, cwd = null, serverUrl = null }) {
    try {
      const storePath = getAdoptionStorePath(cwd);
      const store = loadPendingAdoptions(storePath);
      const keys = Object.keys(store.records);
      if (keys.length === 0) return;
  
      const keysToRemove = [];
      const sendPromises = [];
      for (const key of keys) {
        const item = store.records[key];
        if (!item) continue;
  
        // 如果属于当前会话，判定为 ABANDONED
        if (!session_id || item.session_id === session_id) {
          const event = {
            ecosystem: item.ecosystem,
            package_name: item.name,
            blocked_version: item.blocked_version,
            suggested_version: item.suggested_version,
            final_version: null,
            status: 'ABANDONED',
            action_type: item.action_type,
            cve_ids: item.cve_ids || [],
            license_risk: item.license_risk || null,
            commit_sha: '',
            session_id: session_id || item.session_id,
            call_id: item.call_id,
            duration_to_commit_sec: Math.max(0, Math.round((Date.now() - (item.created_at || Date.now())) / 1000)),
          };
  
          keysToRemove.push(key);
          UI.log(`[ADOPTION] session stop: marked ${item.name} as ABANDONED`);
  
          if (serverUrl) {
            sendPromises.push(recordAdoptionEvent(event, serverUrl, cwd));
          }
        }
      }
  
      if (keysToRemove.length > 0) {
        for (const k of keysToRemove) {
          delete store.records[k];
        }
        savePendingAdoptions(storePath, store);
      }
  
      if (sendPromises.length > 0) {
        await Promise.allSettled(sendPromises);
      }
    } catch (err) {
      UI.log(`[ADOPTION] handleSessionStop error: ${err.message}`);
    }
  }
  
  
  // Module exports
  __adoption__.findGitRoot = findGitRoot;
  __adoption__.getAdoptionStorePath = getAdoptionStorePath;
  __adoption__.loadPendingAdoptions = loadPendingAdoptions;
  __adoption__.savePendingAdoptions = savePendingAdoptions;
  __adoption__.recordPendingAdoptions = recordPendingAdoptions;
  __adoption__.isGitCommitCommand = isGitCommitCommand;
  __adoption__.isGitAmendCommand = isGitAmendCommand;
  __adoption__.resolveCommitSha = resolveCommitSha;
  __adoption__.getCommitChangedFiles = getCommitChangedFiles;
  __adoption__.getFileContentAtCommit = getFileContentAtCommit;
  __adoption__.inspectGitCommitAdoption = inspectGitCommitAdoption;
  __adoption__.handleSessionStop = handleSessionStop;
})();


// ============================================================================
// Module: index
// ============================================================================

(function() {
  /**
   * MCP Security Guard - Node.js Hook Client
   * 
   * 供应链安全防? Hook，拦截依赖安装操作进行安全审?
   * 
   * 使用方式:
   *   echo '{"tool_name": "Write", ...}' | node src/index.js
   * 
   * 参数:
   *   --server-url <url>  MCP Server 地址 (默认: ? CODEBUDDY_SERVICE_PROXY_URL 环境变量获取)
   *   --timeout <ms>      请求超时时间 (默认: 2000)
   *   --debug             启用调试模式
   *   --version-json      输出构建元数据后退? (只读，不联网，不? stdin)
   *   --status            输出插件状态诊断后退? (只读，会 ping Server 探测连通?)
   *   --report            读取本地审计日志生成 Markdown 报告后退? (只读，不联网，不? stdin)
   */
  
  const { readFileSync, existsSync, appendFileSync, writeFileSync, unlinkSync, statSync, readdirSync, mkdirSync, copyFileSync } = require('fs');
  const { randomUUID, createHash } = require('crypto');
  const { tmpdir, homedir } = require('os');
  const { join: pathJoin, dirname } = require('path');
  const { execSync } = require('child_process');
  
  // F-05: sha256 helper for lockfile re-audit
  function _sha256(content) {
    return createHash('sha256').update(content || '').digest('hex');
  }
  const parseInput = __parsers_input__.parseInput;
  const extractFileContent = __parsers_input__.extractFileContent;
  const computeEditResult = __parsers_input__.computeEditResult;
  const isIdeClient = __parsers_input__.isIdeClient;
  const getClientType = __parsers_input__.getClientType;
  const parseReplOperations = __parsers_repl__.parseReplOperations;
  const parseManifest = __parsers_manifests_index__.parseManifest;
  const parseNpmLockfile = __parsers_manifests_package_lock_json__.parseNpmLockfile;
  const parsePnpmLockfile = __parsers_manifests_package_lock_json__.parsePnpmLockfile;
  const parseYarnLockfile = __parsers_manifests_package_lock_json__.parseYarnLockfile;
  const lockfilePackagesToMap = __parsers_manifests_package_lock_json__.lockfilePackagesToMap;
  const resolveInstalledVersion = __parsers_lockfiles_resolve_installed__.resolveInstalledVersion;
  const parseCommand = __parsers_commands_index__.parseCommand;
  const filterPrivatePackages = __filters_privacy__.filterPrivatePackages;
  const loadConfigFromEnv = __filters_privacy__.loadConfigFromEnv;
  const checkPackages = __client__.checkPackages;
  const healthCheck = __client__.healthCheck;
  const buildHookResponse = __response__.buildHookResponse;
  const buildPostToolUseResponse = __response__.buildPostToolUseResponse;
  const buildPostToolUseFinalResponse = __response__.buildPostToolUseFinalResponse;
  const normalizeServerResponse = __response__.normalizeServerResponse;
  const summarizeServerResponseForLog = __response__.summarizeServerResponseForLog;
  const buildAllowResponse = __response__.buildAllowResponse;
  const isFailOpenReason = __response__.isFailOpenReason;
  const UI = __ui__.UI;
  const localTimestamp = __ui__.localTimestamp;
  const setGlobalDebugMode = __ui__.setGlobalDebugMode;
  const recordAndSend = __telemetry__.recordAndSend;
  const computeFingerprint = __dedup__.computeFingerprint;
  const classifyAndRecord = __dedup__.classifyAndRecord;
  const cleanupStaleDedupFiles = __dedup__.cleanupStaleDedupFiles;
  const resetExactFingerprint = __dedup__.resetExactFingerprint;
  const resetRemediationSession = __dedup__.resetRemediationSession;
  const trackRemediationProgress = __dedup__.trackRemediationProgress;
  const findingSetDigest = __dedup__.findingSetDigest;
  const getBuildInfo = __build_info__.getBuildInfo;
  const getSessionUserId = __auth_session_reader__.getSessionUserId;
  const npmAuditAdapter = __local_audit_npm_audit__;
  const appendAuditLog = __audit_log__.appendAuditLog;
  const buildAuditEntry = __audit_log__.buildAuditEntry;
  const DEFAULT_AUDIT_LOG = __audit_log__.DEFAULT_AUDIT_LOG;
  const buildReportOutput = __audit_log__.buildReportOutput;
  const renderReportMarkdown = __audit_log__.renderReportMarkdown;
  const escapeMarkdownTableCell = __audit_log__.escapeMarkdownTableCell;
  const getRiskLevel = __risk_policy__.getRiskLevel;
  const findCrossMajorChanges = __version__.findCrossMajorChanges;
  const recordPendingAdoptions = __adoption__.recordPendingAdoptions;
  const inspectGitCommitAdoption = __adoption__.inspectGitCommitAdoption;
  const isGitCommitCommand = __adoption__.isGitCommitCommand;
  const handleSessionStop = __adoption__.handleSessionStop;
  const isDependencyManifest = __operation_router__.isDependencyManifest;
  const splitShellCommandWithSeparators = __operation_router__.splitShellCommandWithSeparators;
  const splitShellCommand = __operation_router__.splitShellCommand;
  const isPackageInstallCommand = __operation_router__.isPackageInstallCommand;
  const isComplexShellSyntax = __operation_router__.isComplexShellSyntax;
  const getFlagsStatus = __rollout__.getFlagsStatus;
  
  // ============================================================================
  // Fail-Open 安全? - 顶层异常处理
  // ============================================================================
  
  const FAIL_OPEN_RESPONSE = JSON.stringify({
    suppressOutput: true,
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'allow',
      permissionDecisionReason: 'uncaught_exception_fail_open'
    }
  });
  
  const CRASH_LOG_PATH = '/tmp/security-guard-crash.log';
  const CRASH_LOG_MAX_SIZE = 1 * 1024 * 1024; // 1MB，避免无限增?
  const CRASH_MESSAGE_MAX_LEN = 300;
  
  // D1-19 修复：PreToolUse/PostToolUse 之间传? Autofix 信息的临时文件目录前缀?
  //
  // 修复背景：此前使用固定的单一全局路径 /tmp/security-guard-fix-info.json?
  // 意味着任意两次 PreToolUse→PostToolUse 配对之间共享同一个文件。若其中一?
  // 缺失 call_id（Claude Code 某些客户?/版本可能不带），mismatch 校验
  // （`fixInfo.callId && currentCallId && fixInfo.callId !== currentCallId`?
  // 会因为条件短路直接判定为"不冲?"而误用上一次操作残留的 fix 信息，向 Agent
  // 展示"修复已验?"这类与当前操作无关的上下文（跨调用状态串扰）?
  // 现在改为? operation 关联键（tool_use_id 优先，缺失时 fallback call_id?
  // 两者都缺失时使用随? UUID——随? UUID 保证这次 PostToolUse 一定读不到任何
  // 旧文件，属于"宁可什么都不展示，也不能展示错误信?"的保守选择）各自独?
  // 命名文件，从根源上消除文件级别的状态共享，而不是仅在读取时事后校验?
  const FIX_INFO_DIR_PREFIX = pathJoin(tmpdir(), 'security-guard-fix-info');
  const FIX_INFO_TTL_MS = 5 * 60 * 1000; // 5 分钟：覆盖绝大多数工具执行耗时，同时避免异常退出时的文件无限堆?
  
  /**
   * 派生本次操作专属? fix-info 文件路径?
   *
   * @param {string|null} toolUseId - Hook 输入中的 tool_use_id（优先使用，粒度最细）
   * @param {string|null} callId - Hook 输入中的 call_id（次优先?
   * @returns {{path: string, isEphemeral: boolean}} isEphemeral=true 表示用的是随?
   *   UUID（无可靠关联键），调用方应据此判?"这次必然读不到旧数据"，仅用于保证不会
   *   误读，不代表这次操作真的没有关联键可用于其它场景?
   */
  function getFixInfoPath(toolUseId, callId) {
    const key = toolUseId || callId;
    if (key) {
      // 关联键可能包含路径不安全字符，做一次简单清洗后再拼入文件名
      const safeKey = String(key).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 128);
      return { path: `${FIX_INFO_DIR_PREFIX}-${safeKey}.json`, isEphemeral: false };
    }
    return { path: `${FIX_INFO_DIR_PREFIX}-${randomUUID()}.json`, isEphemeral: true };
  }
  
  /**
   * 清理过期? fix-info 临时文件（TTL 回收），避免异常退出场景下的文件无限堆积?
   * 静默失败：清理本身不是关键路径，任何异常都不应影响主流程?
   */
  function cleanupStaleFixInfoFiles() {
    try {
      const dir = tmpdir();
      const prefix = 'security-guard-fix-info-';
      const now = Date.now();
      for (const name of readdirSync(dir)) {
        if (!name.startsWith(prefix) || !name.endsWith('.json')) continue;
        const fullPath = pathJoin(dir, name);
        try {
          const stat = statSync(fullPath);
          if (now - stat.mtimeMs > FIX_INFO_TTL_MS) {
            unlinkSync(fullPath);
          }
        } catch {
          // 单个文件清理失败不影响其他文件，静默跳过
        }
      }
    } catch {
      // 目录读取失败（权?/不存在等），静默忽略，不影响主流?
    }
  }
  
  /**
   * D1-14 修复：根据去重分类结果收缩已构造好? Hook 响应?
   *
   * 只在"相同 fingerprint 重复出现"时收缩文案，不改变任? continue/
   * permissionDecision 字段——去重只影响用户/Agent 看到的信息量，不改变安全
   * 决策本身，这是刻意的保守选择（避免去重逻辑本身成为新的安全决策来源）?
   *
   * @param {Object} hookResponse - buildHookResponse() ? handleMultiEcosystemBash 已构造的响应
   * @param {{state: 'first'|'suppressed'|'terminal', retryCount: number}} dedupResult
   * @returns {Object} 收缩后的响应（first 状态原样返回）
   */
  function applyDedup(hookResponse, dedupResult) {
    if (!hookResponse || !dedupResult || dedupResult.state === 'first') {
      return hookResponse;
    }
  
    const shortReason = hookResponse.hookSpecificOutput?.permissionDecisionReason || '安全拦截';
  
    if (dedupResult.state === 'terminal') {
      return {
        ...hookResponse,
        systemMessage: `${shortReason}（已连续 ${dedupResult.retryCount} 次相同结果，请停止自动重试，等待人工处理）`,
        hookSpecificOutput: {
          ...hookResponse.hookSpecificOutput,
          additionalContext: 'TERMINAL_LOOP_DETECTED: Stop retrying this exact operation. Ask the human developer for help instead of repeating the same change.',
        },
      };
    }
  
    // suppressed
    return {
      ...hookResponse,
      systemMessage: `${shortReason}（相同结果第 ${dedupResult.retryCount} 次出现，已省略详情）`,
      hookSpecificOutput: {
        ...hookResponse.hookSpecificOutput,
        additionalContext: undefined,
      },
    };
  }
  
  /**
   * 从错? stack 中移除文件路径的用户目录/绝对路径部分，只保留文件名和行号?
   * 避免把本机用户名、目录结构等信息写入崩溃日志?
   * ?: "at foo (/Users/alice/project/src/index.js:42:10)" -> "at foo (index.js:42:10)"
   */
  function redactStackPaths(stack) {
    if (!stack) return '';
    return stack
      .split('\n')
      .map(line => line.replace(/(?<!node:internal|node:\S*)\/(?:[^\s():]+\/)+([^/\s():]+:\d+:\d+)/g, '$1'))
      .join('\n');
  }
  
  /**
   * 对错? message 做基础模式脱敏：移除常见密?/token 形态的子串和绝对路径?
   * 这是防御纵深，不是完整方案——error.message 本身可能携带任意上游异常携带?
   * 原始输入片段，无法穷举所有敏感模式，因此仍配? CRASH_MESSAGE_MAX_LEN 限长?
   * 缩小任何未被模式覆盖到的残留内容的暴露面?
   */
  function redactMessagePatterns(message) {
    if (!message) return '';
    return message
      // 形如 sk-xxx / ghp_xxx / Bearer xxx 等常? token 前缀
      .replace(/\b(sk|ghp|gho|ghu|ghs|ghr|xox[abps])-[A-Za-z0-9_-]{6,}/gi, '[REDACTED_TOKEN]')
      .replace(/\bBearer\s+[A-Za-z0-9._-]{10,}/gi, 'Bearer [REDACTED_TOKEN]')
      // 绝对路径（Unix），? redactStackPaths 的处理原?
      .replace(/(?<!node:internal|node:\S*)\/(?:[^\s():]+\/)+([^/\s():]+)/g, '$1');
  }
  
  /**
   * 记录崩溃日志（静默失败）
   *
   * 安全边界：只记录 error class、脱敏后? message（限长）和已移除路径信息? stack?
   * 不记录可能包含敏感原文的 error.message 中的具体值（如异常携带的原始输入片段）?
   * 崩溃日志设大小上限并做简单轮转，避免无限增长和跨会话无限期留存?
   */
  function logCrash(type, error) {
    try {
      // 超过大小上限时截断重建，而不是无限追?
      try {
        const stat = statSync(CRASH_LOG_PATH);
        if (stat.size >= CRASH_LOG_MAX_SIZE) {
          unlinkSync(CRASH_LOG_PATH);
        }
      } catch {
        // 文件不存在，无需处理
      }
  
      const timestamp = localTimestamp();
      let message;
      if (error instanceof Error) {
        const redactedMessage = redactMessagePatterns(error.message || '').slice(0, CRASH_MESSAGE_MAX_LEN);
        const redactedStack = redactStackPaths(error.stack).slice(0, CRASH_MESSAGE_MAX_LEN * 4);
        message = `${error.constructor?.name || 'Error'}: ${redactedMessage}\n${redactedStack}`;
      } else {
        message = redactMessagePatterns(String(error)).slice(0, CRASH_MESSAGE_MAX_LEN);
      }
      appendFileSync(CRASH_LOG_PATH, `${timestamp} [${type}] ${message}\n`, { mode: 0o600 });
    } catch {
      // 静默忽略日志写入失败
    }
  }
  
  /**
   * 处理未捕获异? - 输出 Fail-Open 响应并退?
   */
  process.on('uncaughtException', (error) => {
    logCrash('UNCAUGHT_EXCEPTION', error);
    process.stdout.write(FAIL_OPEN_RESPONSE);
    process.exit(0);
  });
  
  /**
   * 处理未处理的 Promise 拒绝 - 输出 Fail-Open 响应并退?
   */
  process.on('unhandledRejection', (reason) => {
    logCrash('UNHANDLED_REJECTION', reason);
    process.stdout.write(FAIL_OPEN_RESPONSE);
    process.exit(0);
  });
  
  // ============================================================================
  // 配置
  // ============================================================================
  
  const DEFAULT_CONFIG = {
    serverUrl: '',  // ? parseArgs 从环境变量动态解?
    timeout: 2000,  // P2: ? 5000ms 降到 2000ms，减少用户等?
    retries: 1,
    debug: false
  };
  
  /**
   * 解析命令行参?
   */
  function parseArgs(args) {
    const config = { ...DEFAULT_CONFIG };
  
    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
  
      if (arg === '--server-url' && args[i + 1]) {
        config.serverUrl = args[++i];
      } else if (arg === '--timeout' && args[i + 1]) {
        config.timeout = parseInt(args[++i], 10);
        config.customTimeout = true;
      } else if (arg === '--debug') {
        config.debug = true;
      } else if (arg === '--retries' && args[i + 1]) {
        config.retries = parseInt(args[++i], 10);
      }
    }
  
    // 环境变量覆盖
    // 未通过 --server-url 设置时，按优先级从环境变量取值：
    //   1. CODEBUDDY_SERVICE_PROXY_URL           ? 网关模式（CLI 平台统一注入?
    //   2. CODEBUDDY_SECURITY_SERVER_URL         ? 直连模式（向后兼?/用户手动配置?
    //   3. 内嵌默认?                             ? IDE 环境兜底（不依赖环境变量注入?
    if (!config.serverUrl) {
      config.serverUrl =
        process.env.CODEBUDDY_SERVICE_PROXY_URL ||
        process.env.CODEBUDDY_SECURITY_SERVER_URL ||
        'https://copilot.tencent.com/v2/service-proxy';
    }
    if (process.env.CODEBUDDY_SECURITY_TIMEOUT) {
      config.timeout = parseInt(process.env.CODEBUDDY_SECURITY_TIMEOUT, 10);
    }
    const debugFlagExists = existsSync('/tmp/security-guard-debug') || existsSync(pathJoin(homedir(), '.codebuddy', '.chainguard-debug'));
    if (process.env.CODEBUDDY_DEBUG === '1' || process.env.SECURITY_GUARD_DEBUG === '1' || debugFlagExists) {
      config.debug = true;
    }
  
    return config;
  }
  
  /**
   * O1-33（最小切片）：`--status` 只读诊断入口的报告构造?
   *
   * ? `--version-json` 的关键区别：这里会真实发起一? GET {serverUrl}/health
   * 探测连通性（否则"status"这个词没有意义），但仍然不读 stdin、不走审?
   * 主流程、不上报 Telemetry、不读取/发送任何项目依赖内容——只报告"插件本身
   * 是否配置正确、能否连? Server"，不触碰用户的项目文件?
   *
   * @param {Object} config - parseArgs() 的解析结?
   * @returns {Promise<Object>} 状态报?
   */
  async function buildStatusReport(config) {
    const buildInfo = getBuildInfo();
    const privacyConfig = loadConfigFromEnv();
  
    let reachable = null; // null 表示 serverUrl 未配置，不是"探测失败"——与
    // "配置了但连不?"区分成两种需要不同修复动作的失败原因
    if (config.serverUrl) {
      reachable = await healthCheck(config.serverUrl, config.timeout);
    }
  
    // O1-11（最小切片）：展示本地原生审计能力（LocalAuditAdapter）当前是?
    // 可用——这是对已有诊断命令的自然延伸，只调? health()（内部只?
    // `npm --version` 探测工具存在性），不触发任何真实扫描，不读取/发?
    // 项目依赖内容
    const npmAuditHealth = await npmAuditAdapter.health();
  
    return {
      enabled: true,
      plugin_version: buildInfo.plugin_version,
      client_version: buildInfo.client_version,
      // O1-13（最小切片）：展示当前生效的产品模式及其来源（explicit/
      // legacy_env/default/invalid_fallback），? filters/privacy.js ?
      // resolveMode()
      mode: {
        name: privacyConfig.mode,
        source: privacyConfig.modeSource,
      },
      server: {
        configured: !!config.serverUrl,
        reachable,
      },
      autofix: {
        enabled: !privacyConfig.disableAutofix,
      },
      // 当前所? manifest parser 支持的生态列表（parsers/manifests/index.js
      // ? detectEcosystem() 覆盖范围），直接抄一遍现状用于展示，不是编?
      ecosystems: ['npm', 'pypi', 'go', 'cargo', 'maven', 'rubygems', 'packagist'],
      localAudit: {
        npm: npmAuditHealth, // { state: 'ready'|'disabled', version: string|null }
      },
      session: {
        // 只报 present/missing，不暴露 uid/token 本身——同 D0-05 已经
        // 建立的日/诊断输出脱敏边界，诊断命令也不能变成敏感信息泄露通道
        present: getSessionUserId() !== '',
      },
      support: {
        owner: '@selinasong',
        feedback: '如遇误报或异常，可联系 @selinasong 或执行 /chainguard-debug 导出排障日志',
      },
    };
  }
  
  /**
   * 转义 Markdown 表格里的特殊字符（| 会破坏表格列结构，反引号会破坏代?
   * 片段边界），防止审计条目里的组件?/命令内容意外破坏报告的表格渲染?
   *
   * @param {*} value - 任意值，非字符串会先转为字符?
   * @returns {string}
   */
  
  /**
   * O1-33 doctor: extended readiness checks beyond --status.
   *
   * 检查项（对齐 fix_update/optimizations/33_First_Run_Onboarding_and_Configuration.md）：
   * - writable_state_dir: ~/.security-guard/ 是否可写（审计日志/fix-info 文件需要）
   * - config_parse: 环境变量配置是否能被 loadConfigFromEnv() 正确解析
   * - hook_registration: hooks.json 是否存在且可解析（plugin 安装完整性）
   * - protocol_schema_version: Client/Server 协议版本兼容性
   *
   * 不检查：真实项目依赖内容（不读 stdin、不扫描文件）。
   */
  async function runDoctorChecks(config) {
    const checks = {};
  
    // 1. writable_state_dir
    try {
      const stateDir = pathJoin(homedir(), '.security-guard');
      if (!existsSync(stateDir)) {
        mkdirSync(stateDir, { recursive: true });
      }
      // 尝试写一个临时文件验证可写
      const testFile = pathJoin(stateDir, '.doctor-write-test');
      writeFileSync(testFile, 'ok', { mode: 0o600 });
      unlinkSync(testFile);
      checks.writable_state_dir = { state: 'ok', path: stateDir };
    } catch (err) {
      checks.writable_state_dir = { state: 'fail', error: err?.message ?? String(err) };
    }
  
    // 2. config_parse
    try {
      const cfg = loadConfigFromEnv();
      checks.config_parse = {
        state: 'ok',
        mode: cfg.mode,
        mode_source: cfg.modeSource,
        autofix_enabled: !cfg.disableAutofix,
      };
    } catch (err) {
      checks.config_parse = { state: 'fail', error: err?.message ?? String(err) };
    }
  
    // 3. hook_registration (检查 plugin 目录下 hooks.json 是否存在)
    try {
      const pluginRoot = process.env.CODEBUDDY_PLUGIN_ROOT || '';
      const hooksJsonPath = pluginRoot ? pathJoin(pluginRoot, 'hooks', 'hooks.json') : '';
      if (hooksJsonPath && existsSync(hooksJsonPath)) {
        const hooksJson = JSON.parse(readFileSync(hooksJsonPath, 'utf-8'));
        checks.hook_registration = {
          state: 'ok',
          pre_tool_use: !!(hooksJson.hooks?.PreToolUse),
          post_tool_use: !!(hooksJson.hooks?.PostToolUse),
        };
      } else {
        checks.hook_registration = { state: 'unknown', reason: 'CODEBUDDY_PLUGIN_ROOT not set or hooks.json not found' };
      }
    } catch (err) {
      checks.hook_registration = { state: 'fail', error: err?.message ?? String(err) };
    }
  
    // 4. protocol_schema_version
    try {
      const buildInfo = getBuildInfo();
      checks.protocol_schema_version = {
        state: 'ok',
        client_version: buildInfo.protocol_schema_version,
      };
    } catch (err) {
      checks.protocol_schema_version = { state: 'fail', error: err?.message ?? String(err) };
    }
  
    // 5. feature_flags (O2-31)
    try {
      const flagsStatus = getFlagsStatus();
      checks.feature_flags = {
        state: 'ok',
        flags_count: Object.keys(flagsStatus).length,
        flags: flagsStatus,
      };
    } catch (err) {
      checks.feature_flags = { state: 'fail', error: err?.message ?? String(err) };
    }
  
    return checks;
  }
  
  
  
  // ============================================================================
  // 主流?
  // ============================================================================
  
  /**
   * ? stdin 读取输入
   */
  async function readStdin() {
    const chunks = [];
    
    for await (const chunk of process.stdin) {
      chunks.push(chunk);
    }
    
    return Buffer.concat(chunks).toString('utf-8');
  }
  
  /**
   * 安全读取磁盘文件内容
   * 
   * @param {string} filePath - 文件路径
   * @returns {string} 文件内容，读取失败返回空字符?
   */
  function readDiskFile(filePath) {
    try {
      if (filePath && existsSync(filePath)) {
        return readFileSync(filePath, 'utf-8');
      }
    } catch (error) {
      // 忽略读取错误
    }
    return '';
  }
  
  // isDependencyManifest / splitShellCommandWithSeparators / splitShellCommand /
  // isPackageInstallCommand / isComplexShellSyntax 已提取到 operation-router.js
  // （O2-32 Strangler 模式第一步，见文件顶? import?
  /**
   * 计算工具执行后的最终文件内?
   * 
   * 关键：对? Edit/MultiEdit，需要读取磁盘文件并应用修改
   * 
   * @param {string} toolName - 工具名称
   * @param {Object} toolInput - 工具输入
   * @param {UI} ui - UI 实例用于调试输出
   * @returns {Object} { content, diskContent }
   */
  function computeFinalContent(toolName, toolInput, ui) {
    const filePath = toolInput.file_path;
    
    switch (toolName) {
      case 'Write':
        // Write: 完整覆写文件，content 就是最终内?
        return {
          content: toolInput.content || '',
          diskContent: readDiskFile(filePath)
        };
        
      case 'Edit': {
        // Edit: 需要读取磁盘文件，应用 old_string -> new_string 替换
        const diskContent = readDiskFile(filePath);
        const finalContent = extractFileContent('Edit', toolInput, diskContent);
        
        ui.debug(`Edit: disk content length=${diskContent.length}, final content length=${finalContent.length}`);
        
        return {
          content: finalContent,
          diskContent: diskContent
        };
      }
        
      case 'MultiEdit': {
        // MultiEdit: 需要读取磁盘文件，依次应用所? edits
        const diskContent = readDiskFile(filePath);
        const finalContent = extractFileContent('MultiEdit', toolInput, diskContent);
        
        ui.debug(`MultiEdit: disk content length=${diskContent.length}, edits count=${toolInput.edits?.length || 0}`);
        
        return {
          content: finalContent,
          diskContent: diskContent
        };
      }
        
      default:
        return { content: '', diskContent: '' };
    }
  }
  
  /**
   * 主函?
   */
  /**
   * 构建所有路径共用的基础遥测事件
   *
   * @param {Object} hookMeta - ? hook 输入提取的环境信?
   * @param {number|null} startTime - 处理开始时间戳（ms），null 表示无法计算
   * @returns {Object} 基础事件字段
   */
  function buildBaseEvent(hookMeta, startTime) {
    return {
      schema_version:    1,
      client_type:       hookMeta.client_type,
      codebuddy_version: hookMeta.codebuddy_version,
      ai_model:          hookMeta.ai_model,
      session_id:        hookMeta.session_id,
      call_id:           hookMeta.call_id ?? null,
      tool_use_id:       hookMeta.tool_use_id ?? null,
      hook_event_name:   hookMeta.hook_event_name ?? null,
      ecosystem:         hookMeta.ecosystem ?? null,
      tool_name:         hookMeta.toolName ?? null,
      duration_total:    startTime != null ? (Date.now() - startTime) : null,
    };
  }
  
  /**
   * D1-27（最小切片）：为"本次 Hook 调用不适用/无需审计"? early-return 路径上报
   * 一个轻量分母事件，避免这些路径完全不产? telemetry 造成的分母幸存者偏?
   * （此前只统计?"真正发起了审?"的调用，"不适用"的调用完全不可见，导?
   * applicable rate/protection rate 这类比率指标的分母存在幸存者偏差）?
   *
   * 复用"all_packages_private"分支已经验证过的事件形状：server_status='N/A' 表示
   * "没有真正询问 Server"，hook_decision='allow' 表示最终放行，skip_reason 说明
   * 具体原因。fire-and-forget，异常静默吞掉，不影响主流程（与所有既? recordAndSend
   * 调用点的错误处理策略一致）?
   *
   * @param {Object} hookMeta - 当前已知? hook 元信息（可能只有部分字段已填充）
   * @param {number} startTime - 处理开始时间戳
   * @param {string} serverUrl - 上报目标
   * @param {string} skipReason - 具体跳过原因（自由文本，? 'not_dependency_manifest'?
   * @param {Object} [extra] - 可选覆盖字段（? { ecosystem, toolName }?
   */
  function reportApplicabilitySkip(hookMeta, startTime, serverUrl, skipReason, extra = {}) {
    // 性能与网络优化：在日常编码 / vibe coding 场景下，非依赖操作（非清单文件、非安装命令等）
    // 默认静默退出，不产生额外的 HTTP 网络请求，保证 <1ms 的极致响应速度。
    // 仅在明确开启环境变量 SECURITY_GUARD_REPORT_SKIPS='true' 时（如离线分母采集测试）才发送。
    if (process.env.SECURITY_GUARD_REPORT_SKIPS !== 'true') {
      return;
    }
  
    if (extra.ecosystem !== undefined) hookMeta.ecosystem = extra.ecosystem;
    if (extra.toolName  !== undefined) hookMeta.toolName  = extra.toolName;
  
    setImmediate(() => {
      try {
        recordAndSend({
          ...buildBaseEvent(hookMeta, startTime),
          package_count_total: 0,
          package_count_sent:  0,
          server_status:       'N/A',
          hook_decision:       'allow',
          fail_mode_trigger:   false,
          skip_reason:         skipReason,
        }, serverUrl);
      } catch {
        // 静默忽略，telemetry 绝不影响主流?
      }
    });
  }
  
  /**
   * 处理 PostToolUse 事件
   *
   * 当工具执行完成后，检查是否发生了安全修复，并? AI 模型提供上下文信?
   *
   * @param {Object} parsedRaw - 原始解析后的输入
   * @param {UI} ui - UI 实例
   */
  async function handlePostToolUse(parsedRaw, ui, runtime = {}) {
    const toolName = parsedRaw.tool_name;
    const toolInput = parsedRaw.tool_input || {};
    const isIDE = isIdeClient(parsedRaw.client, toolName);
  
    UI.log(`[DIAG] PostToolUse: tool=${toolName}, isIDE=${isIDE}`);
  
    // 1. 产研采纳与风险闭环：若当前命令为 git commit，检测提交是否采纳安全建议
    let isGitCommit = false;
    if (toolName === 'Bash' && isGitCommitCommand(toolInput?.command)) {
      isGitCommit = true;
      const toolResp = parsedRaw.tool_response || parsedRaw.tool_result || {};
      const exitCode = toolResp.exit_code;
      const toolSucceeded = (exitCode === 0 || exitCode === undefined) && !toolResp.isError;
      if (toolSucceeded) {
        const output = typeof toolResp === 'string' ? toolResp : (toolResp.stdout || toolResp.output || '');
        await inspectGitCommitAdoption({
          command: toolInput.command,
          output,
          cwd: process.cwd(),
          session_id: parsedRaw.session_id || null,
          call_id: parsedRaw.call_id || null,
          serverUrl: runtime?.config?.serverUrl || null,
        });
      }
    }
  
    // 2. 检查本次操作关联的修复信息 (fix-info)
    const { path: fixInfoPath } = getFixInfoPath(parsedRaw.tool_use_id, parsedRaw.call_id);
    const fixInfoExists = existsSync(fixInfoPath);
  
    // Vibe Coding 快速路径剪枝：
    // PostToolUse 专职于向 AI 模型通知安全修复上下文（additionalContext）及检测 git commit 采纳。
    // 若既非 git commit，也没有安全修复上下文 (fixInfoExists === false)，
    // 说明只是日常常规开发动作（ls, git status, npm test, 源码编辑等）。
    // 此时无上下文需要注入 LLM，直接以 <1ms 静默放行，避免磁盘扫描与无意义的网络上报。
    if (!fixInfoExists && !isGitCommit) {
      process.stdout.write(JSON.stringify({
        continue: true,
        hookSpecificOutput: { hookEventName: 'PostToolUse' }
      }));
      return;
    }
  
    let fixInfo = null;
    if (fixInfoExists) {
      try {
        const stat = statSync(fixInfoPath);
        if (Date.now() - stat.mtimeMs > FIX_INFO_TTL_MS) {
          UI.log(`[DIAG] PostToolUse: fix info file stale, discarding`);
          try { unlinkSync(fixInfoPath); } catch { /* ignore */ }
        } else {
          const fixInfoContent = readFileSync(fixInfoPath, 'utf-8');
          fixInfo = JSON.parse(fixInfoContent);
          UI.log(`[DIAG] PostToolUse: found fix info: callId=${fixInfo.callId}, phase=${fixInfo.phase || 'legacy'}`);
        }
      } catch {
        UI.log(`[DIAG] PostToolUse: no fix info found`);
      } finally {
        try { unlinkSync(fixInfoPath); } catch { /* ignore */ }
        cleanupStaleFixInfoFiles();
        cleanupStaleDedupFiles();
      }
  
      // callId mismatch check
      const currentCallId = parsedRaw.call_id;
      if (fixInfo && currentCallId && fixInfo.callId && fixInfo.callId !== currentCallId) {
        UI.log(`[DIAG] PostToolUse: fix info callId mismatch, skipping`);
        fixInfo = null;
      }
    }
  
    // 若无有效 fixInfo（如纯 git commit 或 fixInfo 过期失效），直接静默返回放行，不发送冗余 telemetry
    if (!fixInfo) {
      process.stdout.write(JSON.stringify({
        continue: true,
        hookSpecificOutput: { hookEventName: 'PostToolUse' }
      }));
      return;
    }
  
    // F-05: PostToolUse lockfile re-audit
    // Only attempt re-audit if: precheck transaction exists AND lockfile_path exists AND
    // lockfile actually exists on disk (not just path in precheck)
    let _f05FinalResponse = null;
    // V25: When lockfile is unavailable, we still run legacy buildPostToolUseResponse to
    // display the autofix diff (users expect to see "lodash@4.17.0 → lodash@4.17.21"),
    // but we tag the response with PRECHECK_ONLY and emit telemetry so dashboards know
    // the Final Audit was skipped — not silently passed.
    let _lockfileUnavailable = false;
    // V24: Enter F-05 block even when bash_path_resolved===false — we need to emit explicit
    // PRECHECK_ONLY rather than silently falling through to legacy buildPostToolUseResponse.
    if (fixInfo && fixInfo.phase === 'PRECHECK' && fixInfo.packages?.length > 0) {
      // V24: Bash cwd unresolved — explicit PRECHECK_ONLY + telemetry, no legacy fallback
      if (fixInfo.bash_path_resolved === false) {
        UI.log(`[DIAG] PostToolUse: bash cwd unresolved → PRECHECK_ONLY`);
        _f05FinalResponse = {
          continue: true,
          hookSpecificOutput: {
            hookEventName: 'PostToolUse',
            additionalContext: `Final audit unavailable — working directory unresolved.`,
          }
        };
        setImmediate(() => {
          try {
            recordAndSend({
              ...buildBaseEvent({
                client_type: getClientType(parsedRaw.client, toolName),
                codebuddy_version: parsedRaw.codebuddy_version ?? null,
                ai_model: parsedRaw.ai_model ?? null,
                session_id: parsedRaw.session_id ?? null,
                call_id: parsedRaw.call_id ?? null,
                tool_use_id: parsedRaw.tool_use_id ?? null,
                hook_event_name: 'PostToolUse',
                toolName,
              }, runtime.startTime ?? Date.now()),
              hook_event: 'PostToolUse',
              tool_name: toolName,
              phase: 'POSTTOOLUSE_FINAL',
              // V25: null (not 'PASS') — Final Audit was NOT completed. skip_reason carries the cause.
              // Using 'PASS' here would pollute protection-rate and Final Audit success-rate dashboards.
              final_decision: null,
              operation_id: fixInfo.operation_id,
              skip_reason: 'working_directory_unresolved',
            }, runtime.config.serverUrl);
          } catch { /* telemetry silent fail */ }
        });
      } else if (!fixInfo.lockfile_path || !existsSync(fixInfo.lockfile_path)) {
        // V25: No lockfile — fall through to legacy buildPostToolUseResponse (fix-info display),
        // but mark _lockfileUnavailable so we append a PRECHECK_ONLY marker and emit telemetry
        // after the legacy response is built. This preserves the autofix diff display while
        // making clear to Agent and dashboards that Final Audit did not run.
        _lockfileUnavailable = true;
        UI.log(`[DIAG] PostToolUse: lockfile unavailable → legacy fix-info + PRECHECK_ONLY marker`);
      } else {
      const toolResp = parsedRaw.tool_response || {};
      // V20-FIX: Tool success = exit_code 0 (or undefined). stderr warnings don't mean failure.
      const exitCode = toolResp.exit_code;
      const toolSucceeded = (exitCode === 0 || exitCode === undefined) && !toolResp.isError;
  
      if (!toolSucceeded) {
        UI.log(`[DIAG] PostToolUse: tool failed, skipping re-audit`);
        _f05FinalResponse = { continue: true, hookSpecificOutput: { hookEventName: 'PostToolUse' } };
      } else {
        // Read post-execution lockfile
        const lockfileAfter = readDiskFile(fixInfo.lockfile_path);
        const lockfileAfterHash = _sha256(lockfileAfter || '');
  
        // Only skip re-audit if lockfile existed before AND is unchanged
        // If lockfile didn't exist before (empty hash), don't skip — fall to legacy
        // V21-FIX: Removed unchanged+EXACT shortcut — always send to Server for final audit
        // Even if lockfile+manifest are unchanged, the vulnerability DB may have updated since precheck.
        // Only short-circuit if lockfile doesn't exist at all (can't re-audit without lockfile).
        if (!lockfileAfter) {
          UI.log(`[DIAG] PostToolUse: no lockfile found → PRECHECK_ONLY`);
          _f05FinalResponse = {
            continue: true,
            hookSpecificOutput: {
              hookEventName: 'PostToolUse',
              additionalContext: `Dependency precheck only — no lockfile to verify resolved versions.`,
            }
          };
        } else if (runtime?.config?.serverUrl) {
          // D4-FIX (B 侧): 所有生态 PostToolUse 闭环。
          // 裸包名 install（resolution_state === 'NAME_ONLY'）装完后用对应生态探测命令
          // 拿 resolved version，再发一次精确 CVE 审计；带版本/EXACT 直接走 lockfile/npm 路径。
          try {
            let resolvedVersions = parseNpmLockfile(lockfileAfter);
            if (resolvedVersions.size === 0 && fixInfo.lockfile_path) {
              if (/pnpm-lock\.yaml$/.test(fixInfo.lockfile_path)) {
                resolvedVersions = lockfilePackagesToMap(parsePnpmLockfile(lockfileAfter).packages);
              } else if (/yarn\.lock$/.test(fixInfo.lockfile_path)) {
                resolvedVersions = lockfilePackagesToMap(parseYarnLockfile(lockfileAfter).packages);
              }
            }
            const finalPackages = await Promise.all(fixInfo.packages.map(async (p) => {
              // npm: 优先从 lockfile 解析（保持原行为）
              if (fixInfo.ecosystem === 'npm') {
                const resolved = resolvedVersions.get(p.name);
                return resolved ? { ...p, version: resolved, resolution_state: 'EXACT', source: 'lockfile' } : p;
              }
              // 其余生态：仅对 NAME_ONLY 包做 PostToolUse 版本解析（fail-open）
              if (p.resolution_state === 'NAME_ONLY') {
                const resolved = await resolveInstalledVersion(fixInfo.ecosystem, p.name, { lockfileContent: lockfileAfter });
                if (resolved) {
                  UI.log(`[DIAG] PostToolUse: resolved ${p.name} -> ${resolved} via ${fixInfo.ecosystem} probe`);
                  return { ...p, version: resolved, resolution_state: 'EXACT', source: `${fixInfo.ecosystem}-probe` };
                }
                UI.log(`[DIAG] PostToolUse: ${fixInfo.ecosystem}/${p.name} probe failed → keep NAME_ONLY (degraded)`);
              }
              return p;
            }));
            UI.log(`[DIAG] PostToolUse: resolved ${finalPackages.filter(p => p.resolution_state === 'EXACT').length}/${finalPackages.length} from lockfile`);
  
            // V20-EVIDENCE: Include evidence binding fields in final audit request
            const _manifestAfterHash = _sha256(readDiskFile(fixInfo.manifest_path) || '');
            const _finalContext = {
              phase: 'POSTTOOLUSE_FINAL',
              operation_id: fixInfo.operation_id,
              manifest_sha256: _manifestAfterHash,
              lockfile_sha256: lockfileAfterHash,
              precheck_phase: 'PRECHECK',
            };
            const finalResponse = await checkPackages(
              fixInfo.ecosystem,
              finalPackages.map(p => ({ n: p.name, v: p.version, declared_spec: p.declared_spec, resolution_state: p.resolution_state })),
              _finalContext,
              runtime.config.serverUrl,
              runtime.config.timeout || 2000,
              0
            );
            const normalizedFinal = normalizeServerResponse(finalResponse);
            _f05FinalResponse = buildPostToolUseFinalResponse(normalizedFinal, finalPackages, { client: parsedRaw.client });
  
            // Telemetry for final audit
            setImmediate(() => {
              try {
                recordAndSend({
                  ...buildBaseEvent({
                    client_type: getClientType(parsedRaw.client, toolName),
                    codebuddy_version: parsedRaw.codebuddy_version ?? null,
                    ai_model: parsedRaw.ai_model ?? null,
                    session_id: parsedRaw.session_id ?? null,
                    call_id: parsedRaw.call_id ?? null,
                    tool_use_id: parsedRaw.tool_use_id ?? null,
                    hook_event_name: 'PostToolUse',
                    toolName,
                  }, runtime.startTime ?? Date.now()),
                  hook_event: 'PostToolUse',
                  tool_name: toolName,
                  phase: 'POSTTOOLUSE_FINAL',
                  final_decision: normalizedFinal.decision || normalizedFinal.s || 'PASS',
                  operation_id: fixInfo.operation_id,
                  manifest_sha256: _manifestAfterHash,
                  lockfile_sha256: lockfileAfterHash,
                  audit_packages_count: finalPackages.length,
                  resolved_exact_count: finalPackages.filter(p => p.resolution_state === 'EXACT').length,
                  skip_reason: null,
                }, runtime.config.serverUrl);
              } catch { /* telemetry silent fail */ }
            });
          } catch (e) {
            UI.log(`[DIAG] PostToolUse: re-audit failed: ${e.message}`);
            // V22: Explicit PRECHECK_ONLY instead of silent legacy fallback
            _f05FinalResponse = {
              continue: true,
              hookSpecificOutput: {
                hookEventName: 'PostToolUse',
                additionalContext: `Final audit unavailable — precheck only. Reason: lockfile_parse_failed`,
              }
            };
          }
        } else {
          // V23: No serverUrl — can't do final audit, explicit PRECHECK_ONLY
          UI.log(`[DIAG] PostToolUse: no server URL, marking PRECHECK_ONLY`);
          _f05FinalResponse = {
            continue: true,
            hookSpecificOutput: {
              hookEventName: 'PostToolUse',
              additionalContext: `Final audit unavailable — no server configured. Precheck only.`,
            }
          };
        }
      }
      } // V24: close new else (lockfile exists) branch
    }
  
    // If F-05 re-audit completed, output and return
    if (_f05FinalResponse) {
      process.stdout.write(JSON.stringify(_f05FinalResponse));
      return;
    }
  
    // Legacy PostToolUse: fix-info display (backward compat)
    const response = buildPostToolUseResponse(parsedRaw.tool_response || null, fixInfo, {
      client: parsedRaw.client,
    });
  
    // V25: When lockfile is unavailable, append a short PRECHECK_ONLY marker to whatever
    // additionalContext the legacy path produced (could be the autofix diff, or empty).
    // This tells the Agent that Final Audit did not run, without hiding the fix info.
    if (_lockfileUnavailable) {
      const _marker = `Fix prepared; final audit unavailable — lockfile not found`;
      response.hookSpecificOutput.additionalContext = response.hookSpecificOutput.additionalContext
        ? `${response.hookSpecificOutput.additionalContext}\n${_marker}`
        : _marker;
      UI.log(`[DIAG] PostToolUse: appended PRECHECK_ONLY marker to legacy response`);
    }
  
    if (response.hookSpecificOutput.additionalContext) {
      UI.log(`[DIAG] PostToolUse: sending additionalContext to AI`);
    }
  
    if (response.hookSpecificOutput.updatedMCPToolOutput) {
      UI.log(`[DIAG] PostToolUse: rewriting MCP tool output for IDE display sync`);
    }
  
    process.stdout.write(JSON.stringify(response));
  
    // Legacy telemetry
    if (runtime?.config?.serverUrl) {
      const toolResp = parsedRaw.tool_response || {};
      // V20-FIX: Tool success = exit_code 0 (or undefined). stderr warnings don't mean failure.
      const exitCode = toolResp.exit_code;
      const toolSucceeded = (exitCode === 0 || exitCode === undefined) && !toolResp.isError;
      const autofixVerified = !!(fixInfo && toolSucceeded);
  
      setImmediate(() => {
        try {
          recordAndSend({
            ...buildBaseEvent({
              client_type:       getClientType(parsedRaw.client, toolName),
              codebuddy_version: parsedRaw.codebuddy_version ?? null,
              ai_model:          parsedRaw.ai_model ?? null,
              session_id:        parsedRaw.session_id ?? null,
              call_id:           parsedRaw.call_id ?? null,
              tool_use_id:       parsedRaw.tool_use_id ?? null,
              hook_event_name:   'PostToolUse',
              toolName,
            }, runtime.startTime ?? Date.now()),
            hook_event: 'PostToolUse',
            tool_name: toolName,
            // D1-27 ֶΣverified  generated
            autofix_generated:  !!fixInfo,
            autofix_tool_succeeded: autofixVerified,
            autofix_verified:   false,
            tool_succeeded:     toolSucceeded,
            // V25: When lockfile unavailable, signal PRECHECK_ONLY — not silent legacy pass.
            // final_decision stays null (not 'PASS') so dashboards don't count this as Final Audit success.
            final_decision: _lockfileUnavailable ? null : undefined,
            skip_reason: _lockfileUnavailable ? 'lockfile_unavailable' : null,
          }, runtime.config.serverUrl);
        } catch {
          // Ĭԣtelemetry Ӱ
        }
      });
    }
  }
  
  /**
   * 处理混合? ecosystem 的链? Bash 命令（如 `npm install lodash && pip install Django`?
   *
   * 设计原则：每? ecosystem 分组各自? Server 发起独立审计请求（复用现有单请求协议?
   * 不改? Client-Server 契约），结果?"最严格优先"合并?
   *   - 任一分组 BLOCK ? 整体 deny（不尝试跨多个不同生态的 Autofix 合并重建命令?
   *     因为将两个不同语言的修复命令合并回一? shell 命令风险较高，保守起见改?
   *     deny + 提示，引? Agent 分别处理，而不是冒险生成一个可能语义错误的合并命令?
   *   - 全部 PASS/WARN（无 BLOCK）→ 整体 allow（分级信息取自各分组结果，仅用于日志/埋点?
   *
   * @param {Map<string, Array>} packagesByEcosystem - ecosystem -> packages[]
   * @param {Object} baseContext - 不含 ecosystem 字段的公? context
   * @param {string} toolName - 工具名（此路径下固定? 'Bash'?
   * @param {Object} toolInput - 原始工具输入
   * @param {Object} config - CLI 配置（serverUrl/timeout/retries?
   * @param {Object} hookMeta - 埋点用的 hook 元信?
   * @param {number} startTime - 请求开始时?
   * @param {UI} ui - UI 实例
   */
  async function handleMultiEcosystemBash(packagesByEcosystem, baseContext, toolName, toolInput, config, hookMeta, startTime, ui) {
    ui.debug(`Mixed-ecosystem Bash command detected: ${[...packagesByEcosystem.keys()].join(', ')}`);
  
    if (!config.serverUrl) {
      ui.debug('serverUrl is empty, skipping audit (fail-open)');
      // D1-15: 复用 buildAllowResponse 统一处理 fail-open 可见性（状态变化时提示一次）?
      // 不再手写不带可见性逻辑的裸响应
      process.stdout.write(JSON.stringify(buildAllowResponse('no_server_url_fail_open', { sessionId: baseContext?.session_id })));
      return;
    }
  
    const privacyConfig = loadConfigFromEnv();
    privacyConfig.debug = config.debug;
  
    // V11: Bounded concurrency for multi-ecosystem (same pattern as chunk concurrency)
    const _ecoEntries = [...packagesByEcosystem.entries()];
    const MAX_ECO_CONCURRENT = 3;
    const ecoBatchDeadline = Date.now() + config.timeout;
    const groupResults = [];
  
    for (let i = 0; i < _ecoEntries.length; i += MAX_ECO_CONCURRENT) {
      const ecoBatch = _ecoEntries.slice(i, i + MAX_ECO_CONCURRENT);
      const remainingMs = ecoBatchDeadline - Date.now();
      if (remainingMs <= 0) {
        // Deadline exhausted — remaining ecosystems get fail-open
        for (let j = i; j < _ecoEntries.length; j++) {
          groupResults.push({
            ecosystem: _ecoEntries[j][0], packages: [],
            response: { s: 'PASS', fail_open: true, reason: 'eco_deadline_exhausted_fail_open', decision: 'PASS' },
            skipped: false,
          });
        }
        break;
      }
      const batchResults = await Promise.all(
        ecoBatch.map(async ([groupEcosystem, groupPackages]) => {
          const { filtered: filteredPackages } = filterPrivatePackages(groupPackages, privacyConfig);
          if (filteredPackages.length === 0) {
            return { ecosystem: groupEcosystem, packages: filteredPackages, response: null, skipped: true };
          }
          const groupContext = { ...baseContext, ecosystem: groupEcosystem };
          const response = await checkPackages(
            groupEcosystem, filteredPackages, groupContext,
            config.serverUrl, Math.min(remainingMs, config.timeout), config.retries
          );
          return { ecosystem: groupEcosystem, packages: filteredPackages, response: normalizeServerResponse(response), skipped: false };
        })
      );
      groupResults.push(...batchResults);
    }
  
    // D0-12ȶ `decision`Server v2+ 䣩fallback  `s`normalizeServerResponse
    //  multi-ecosystem Bash ·ϵãֱӶ raw responseҪֶ fallback
    const _decisionOf = (r) => r?.decision ?? r?.dec ?? r?.s;
    const blockedGroups = groupResults.filter(g => !g.skipped && _decisionOf(g.response) === 'BLOCK');
    const warnedGroups = groupResults.filter(g => !g.skipped && _decisionOf(g.response) === 'WARN');
    const anyFailOpen = groupResults.some(g => !g.skipped && g.response?.fail_open === true);
  
    // D1-14: 全原? Session 去重也覆盖混合生? Bash ? blocked 分支——这条路径不
    // 经过 buildHookResponse()/主流程的去重调用点，需要单独接一?
    let dedupResult = { state: 'first', retryCount: 1 };
  
    let hookResponse;
    if (blockedGroups.length > 0) {
      // 最严格优先：只要有一? ecosystem 分组 BLOCK，整? deny
      const summary = blockedGroups
        .map(g => `[${g.ecosystem}] ${g.response?.reason || 'security_block'}`)
        .join('; ');
      hookResponse = {
        continue: false,
        systemMessage: `已阻止不安全的多生态命令：${summary}`,
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: `🚫 安全拦截（混合生态命令）?${summary}。请分别针对每个生态单独安装以便自动修复，或改用安全版本。`
        }
      };
      const fingerprint = computeFingerprint({
        toolName,
        ecosystem: [...packagesByEcosystem.keys()].sort().join('+'),
        packages: blockedGroups.flatMap(g => g.packages || []),
        decision: 'BLOCK',
        reasonCode: blockedGroups.map(g => g.response?.reason || 'security_block').sort().join(','),
        fixTarget: '',
      });
      dedupResult = classifyAndRecord(baseContext?.session_id, fingerprint);
      hookResponse = applyDedup(hookResponse, dedupResult);
    } else if (warnedGroups.length > 0) {
      hookResponse = {
        continue: true,
        suppressOutput: true,
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'allow',
          permissionDecisionReason: 'security_warning_multi_ecosystem'
        }
      };
    } else if (anyFailOpen) {
      // D1-15: 复用 buildAllowResponse 统一处理 fail-open 可见性（状态变化时提示一次）?
      // 而不是像此前那样只写? permissionDecisionReason 却始? suppressOutput:true?
      // 导致用户实际上永远看不到"部分/全部分组未完成审?"这个信号
      hookResponse = buildAllowResponse('partial_or_full_fail_open_multi_ecosystem', { sessionId: baseContext?.session_id });
    } else {
      hookResponse = {
        continue: true,
        suppressOutput: true,
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'allow'
        }
      };
    }
  
    // 产研采纳与风险闭环：记录多生态命令中被拦截或告警的分组
    for (const g of blockedGroups.concat(warnedGroups)) {
      recordPendingAdoptions({
        ecosystem: g.ecosystem,
        packages: g.packages || [],
        changes: g.response?.changes || [],
        unfixable: g.response?.unfixable || [],
        serverResponse: g.response || {},
        toolInput: baseContext?.toolInput || {},
        inputRaw: baseContext?.raw || {},
        cwd: process.cwd(),
      });
    }
  
    process.stdout.write(JSON.stringify(hookResponse));
  
    const totalPackages = [...packagesByEcosystem.values()].reduce((sum, list) => sum + list.length, 0);
    // V7-F10: count actually sent (filtered) packages
    const filteredTotalPackages = groupResults
      .filter(g => !g.skipped)
      .reduce((sum, g) => sum + (g.packages?.length || 0), 0);
    hookMeta.ecosystem = [...packagesByEcosystem.keys()].join('+');
    hookMeta.toolName = toolName;
  
    setImmediate(() => {
      try {
        const decision = hookResponse?.hookSpecificOutput?.permissionDecision ?? 'allow';
        recordAndSend({
          ...buildBaseEvent(hookMeta, startTime),
          package_count_total: totalPackages,
          package_count_sent:  filteredTotalPackages, // V7-F10: use filtered count
          server_status:       blockedGroups.length > 0 ? 'BLOCK' : (warnedGroups.length > 0 ? 'WARN' : 'PASS'),
          hook_decision:       decision,
          block_reason:        blockedGroups.length > 0 ? blockedGroups.map(g => g.response?.reason).join(';') : null,
          autofix_applied:     false, // 多生态命令不? Autofix 合并，见函数顶部设计说明
          fail_mode_trigger:   anyFailOpen,
          skip_reason:         null,
          multi_ecosystem:     true,
          ecosystem_count:     packagesByEcosystem.size,
          dedup_state:         dedupResult.state,
          dedup_retry_count:   dedupResult.retryCount,
        }, config.serverUrl);
      } catch {
        // 静默忽略，埋点绝不影响主流程
      }
    });
  }
  
  /**
   * 一键调试管理与诊断包导出 (Debug Mode & Diagnostic Export)
   *
   * 支持动作:
   * - on:     开启调试模式 (创建标记文件，后续 Hook 自动全量记详细日志)
   * - off:    关闭调试模式 (删除标记文件)
   * - export: 导出并打包排障日志 (/tmp/chainguard-debug-<timestamp>.tar.gz)
   * - status: 查询当前调试状态
   */
  function handleDebugCommand(action, config) {
    const DEBUG_FLAG_1 = '/tmp/security-guard-debug';
    const DEBUG_FLAG_2 = pathJoin(homedir(), '.codebuddy', '.chainguard-debug');
  
    if (action === 'on') {
      try { writeFileSync(DEBUG_FLAG_1, '1\n'); } catch {}
      try {
        const dir = pathJoin(homedir(), '.codebuddy');
        if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
        writeFileSync(DEBUG_FLAG_2, '1\n');
      } catch {}
      return {
        status: 'enabled',
        message: '✅ ChainGuard 调试模式已开启。后续依赖检查与拦截将全量记录详细日志至 /tmp/security-guard.log。',
        logPath: '/tmp/security-guard.log',
        support: {
          owner: '@selinasong',
        },
      };
    }
  
    if (action === 'off') {
      try { unlinkSync(DEBUG_FLAG_1); } catch {}
      try { unlinkSync(DEBUG_FLAG_2); } catch {}
      return {
        status: 'disabled',
        message: '✅ ChainGuard 调试模式已关闭。',
        support: {
          owner: '@selinasong',
        },
      };
    }
  
    if (action === 'export') {
      const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const exportArchive = `/tmp/chainguard-debug-${ts}.tar.gz`;
      const exportFallback = `/tmp/chainguard-debug-${ts}.log`;
  
      const diagMeta = {
        timestamp: new Date().toISOString(),
        platform: process.platform,
        arch: process.arch,
        nodeVersion: process.version,
        build: getBuildInfo(),
        serverUrl: config.serverUrl,
        mode: process.env.SECURITY_GUARD_MODE || 'strict',
      };
      const metaPath = `/tmp/chainguard-diag-meta.json`;
      try { writeFileSync(metaPath, JSON.stringify(diagMeta, null, 2)); } catch {}
  
      const logFile = '/tmp/security-guard.log';
      let fileToExport = exportFallback;
      let exported = false;
  
      try {
        const filesToTar = [metaPath];
        if (existsSync(logFile)) filesToTar.push(logFile);
        execSync(`tar -czf ${exportArchive} ${filesToTar.join(' ')} 2>/dev/null`);
        fileToExport = exportArchive;
        exported = true;
      } catch {
        if (existsSync(logFile)) {
          try { copyFileSync(logFile, exportFallback); fileToExport = exportFallback; exported = true; } catch {}
        }
      }
  
      let logLines = 0;
      if (existsSync(logFile)) {
        try {
          const content = readFileSync(logFile, 'utf8');
          logLines = content.split('\n').filter(Boolean).length;
        } catch {}
      }
  
      return {
        status: 'exported',
        exportPath: fileToExport,
        logLines,
        support: {
          owner: '@selinasong',
          tip: '请将此诊断文件通过企业微信发送给 @selinasong 进行快速分析定位。',
        },
      };
    }
  
    // 默认查看状态 (status)
    const isDebugOn = existsSync(DEBUG_FLAG_1) || existsSync(DEBUG_FLAG_2) || process.env.CODEBUDDY_DEBUG === '1' || process.env.SECURITY_GUARD_DEBUG === '1';
    let logSizeBytes = 0;
    if (existsSync('/tmp/security-guard.log')) {
      try { logSizeBytes = statSync('/tmp/security-guard.log').size; } catch {}
    }
    return {
      status: isDebugOn ? 'enabled' : 'disabled',
      debugEnabled: isDebugOn,
      logFile: '/tmp/security-guard.log',
      logSizeBytes,
      instructions: {
        enable: '/chainguard-debug on',
        disable: '/chainguard-debug off',
        export: '/chainguard-debug export',
      },
      support: {
        owner: '@selinasong',
        feedback: '如需技术支持，可随时联系 @selinasong',
      },
    };
  }
  
  async function main() {
    // D1-01：只读诊断入口，必须在任何主流程副作用（读 stdin、设置调试模式等）之前短路返回
    if (process.argv.includes('--version-json')) {
      process.stdout.write(JSON.stringify(getBuildInfo()));
      return;
    }
  
    // 一键调试管理入口: --debug-toggle [on|off|export|status] 或 --debug [on|off|export|status]
    const debugToggleIdx = process.argv.indexOf('--debug-toggle');
    const debugArgIdx = process.argv.indexOf('--debug');
    const debugActionArg = debugToggleIdx !== -1
      ? process.argv[debugToggleIdx + 1]
      : (debugArgIdx !== -1 && ['on', 'off', 'export', 'status'].includes(process.argv[debugArgIdx + 1]) ? process.argv[debugArgIdx + 1] : null);
  
    if (debugToggleIdx !== -1 || debugActionArg) {
      const action = debugActionArg || 'status';
      const debugConfig = parseArgs(process.argv.slice(2));
      const result = handleDebugCommand(action, debugConfig);
      process.stdout.write(JSON.stringify(result, null, 2));
      return;
    }
  
    // O1-33（最小切片）：--status 诊断入口
    if (process.argv.includes('--status') || process.argv.includes('--doctor')) {
      const statusConfig = parseArgs(process.argv.slice(2));
      const report = await buildStatusReport(statusConfig);
      if (process.argv.includes('--doctor')) {
        report.doctor = await runDoctorChecks(statusConfig);
      }
      process.stdout.write(JSON.stringify(report, null, 2));
      return;
    }
  
    // O2-23（最小切片）：--report 报告入口
    if (process.argv.includes('--report')) {
      const { reportPath, summary } = buildReportOutput(process.env.SECURITY_GUARD_AUDIT_LOG || undefined);
      process.stdout.write(JSON.stringify({ reportPath, summary }, null, 2));
      return;
    }
  
    const config = parseArgs(process.argv.slice(2));
    setGlobalDebugMode(config.debug);
    const ui = new UI(config.debug);
    
    // 记录开始时间，用于计算处理耗时
    const startTime = Date.now();
  
    try {
      // 1. 读取 stdin
      // 客户端环境元信息，用于遥测（? parseInput 成功前使用默认值）
      let hookMeta = {
        client_type:       'CLI',
        codebuddy_version: null,
        ai_model:          null,
        session_id:        null,
        call_id:           null,
        tool_use_id:       null,
        hook_event_name:   null,
      };
          const rawInput = await readStdin();
      const _phaseStdinMs = Date.now() - startTime;  // O2-30: stdin read phase
      
      if (!rawInput.trim()) {
        // 空输入，直接放行
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'allow'
          }
        }));
        reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'empty_stdin');
        return;
      }
      
      // 安全边界：不记录原始 Hook 输入原文（可能包含文件内容、shell 命令、路径?
      // 凭证等敏感信息），仅记录长度这一元数据，用于排障时判断是否收到了输入?
      ui.debug(`Raw input received, length=${rawInput.length}`);
      UI.log(`[DIAG] raw_input_length=${rawInput.length}`);
  
      // 2. 解析原始 JSON 获取 hook_event_name
      let parsedRaw;
      try {
        parsedRaw = JSON.parse(rawInput);
      } catch {
        ui.debug('Invalid JSON, allowing');
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'allow'
          }
        }));
        reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'invalid_json');
        return;
      }
  
      const hookEventName = parsedRaw.hook_event_name || 'PreToolUse';
      UI.log(`[DIAG] hook_event_name=${hookEventName}`);
  
      // 3. 根据 hook 事件类型分发处理
      if (hookEventName === 'PostToolUse') {
        await handlePostToolUse(parsedRaw, ui, { config, startTime });
        return;
      }
  
      if (hookEventName === 'Stop') {
        await handleSessionStop({
          session_id: parsedRaw.session_id || null,
          cwd: process.cwd(),
          serverUrl: config.serverUrl,
        });
        process.stdout.write(JSON.stringify({
          continue: true,
          hookSpecificOutput: {
            hookEventName: 'Stop',
          }
        }));
        return;
      }
  
      // 4. PreToolUse: 解析 Hook Input
      const input = parseInput(rawInput);
      const _phaseParseMs = Date.now() - startTime - _phaseStdinMs;  // O2-30: parse phase
  
      if (!input) {
        ui.debug('Invalid input, allowing');
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'allow'
          }
        }));
        reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'invalid_hook_input');
        return;
      }
      
      // 安全边界：不打印完整 input（含 raw.tool_input 原始文件内容/命令），
      // 下方已有专门? keys-only 元数据日志（[DIAG] raw_tool=...），这里只记录概?
      ui.debug(`Parsed input: toolName=${input.toolName}, hasToolInput=${!!input.toolInput}`);
  
      const { toolName, toolInput } = input;
      // 更新 hookMeta：从 hook 输入中提取客户端环境信息
      hookMeta = {
        client_type:       input.raw.client ?? 'CLI',
        codebuddy_version: input.raw.version ?? null,
        ai_model:          input.raw.model ?? null,
        session_id:        input.raw.session_id ?? null,
        call_id:           input.raw.call_id ?? null,
        tool_use_id:       input.raw.tool_use_id ?? null,
        hook_event_name:   parsedRaw.hook_event_name ?? 'PreToolUse',
      };
  
      // 安全边界：不记录 toolInput 的具体值（文件内容、shell 命令、路径等可能?
      // 敏感原文，截断不等于脱敏）。只记录字段名（key）和值的类型/长度这类结构?
      // 元数据，足以排障"是否收到了预期字?"而不泄露内容本身?
      UI.log(`[DIAG] raw_tool=${input.raw.tool_name} normalized=${toolName} keys=${Object.keys(toolInput || {}).join(',')}`);
      for (const [k, v] of Object.entries(toolInput || {})) {
        const meta = typeof v === 'string' ? `string(len=${v.length})` : `${typeof v}`;
        UI.log(`[DIAG]   ${k}: ${meta}`);
      }
  
      // 3. 判断是否需要审?
      let packages = null;
      let ecosystem = null;
      let context = null;
      
      if (toolName === 'Write' || toolName === 'Edit' || toolName === 'MultiEdit') {
        // 文件操作：检查是否为依赖清单
        const filePath = toolInput.file_path;
  
        if (!isDependencyManifest(filePath)) {
          // 安全边界：不记录完整绝对路径（可能含用户?/项目结构），只记? basename
          ui.debug(`File ${filePath ? filePath.split(/[\\/]/).pop() : '(none)'} is not a dependency manifest, allowing`);
          process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'allow'
            }
          }));
          reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'not_dependency_manifest', { toolName });
          return;
        }
  
        // 计算最终文件内容（关键：需要读取磁盘文件）
        const { content, diskContent } = computeFinalContent(toolName, toolInput, ui);
  
        ui.debug(`Computed final content for ${toolName}, length=${content.length}`);
  
        // 解析目标依赖（即将写入的内容?
        const parseResult = parseManifest(filePath, content);
  
        if (!parseResult || parseResult.packages.length === 0) {
          ui.debug('No packages found in manifest, allowing');
          process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'allow'
            }
          }));
          reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'no_packages_in_manifest', {
            toolName,
            ecosystem: parseResult?.ecosystem ?? null,
          });
          return;
        }
  
        // O1-10（最小切片）：npm 场景下，若同目录存在可读? package-lock.json
        // （v2/v3 格式），用其中的 resolved exact version 纠正 manifest 声明
        // 的版本范围——normalizeVersion() 只能取范围下界近似（?
        // "^4.17.20" -> "4.17.20"），真实锁定安装的版本可能不同，? lockfile
        // 纠正能让 CVE 判断更准确。找不到 lockfile 或找不到对应条目的包保持
        // 原有近似值不变（declared-only 状态的自然回退，不新增状态标记，?
        // 伪造版本）。只处理直接依赖，不读取传递依赖（?
        // parsers/manifests/package-lock-json.js 顶部注释）?
        if (parseResult.ecosystem === 'npm' && /(?:^|[\\/])package\.json$/.test(filePath)) {
          let lockfilePath = filePath.replace(/package\.json$/, 'package-lock.json');
          let lockfileContent = readDiskFile(lockfilePath);
          let resolvedVersions = lockfileContent ? parseNpmLockfile(lockfileContent) : null;
          if (!resolvedVersions || resolvedVersions.size === 0) {
            const pnpmPath = filePath.replace(/package\.json$/, 'pnpm-lock.yaml');
            const pnpmContent = readDiskFile(pnpmPath);
            if (pnpmContent) {
              resolvedVersions = lockfilePackagesToMap(parsePnpmLockfile(pnpmContent).packages);
            }
          }
          if (!resolvedVersions || resolvedVersions.size === 0) {
            const yarnPath = filePath.replace(/package\.json$/, 'yarn.lock');
            const yarnContent = readDiskFile(yarnPath);
            if (yarnContent) {
              resolvedVersions = lockfilePackagesToMap(parseYarnLockfile(yarnContent).packages);
            }
          }
          if (resolvedVersions && resolvedVersions.size > 0) {
            let correctedCount = 0;
            for (const pkg of parseResult.packages) {
              const resolved = resolvedVersions.get(pkg.n);
              if (resolved && resolved !== pkg.v) {
                // F-05: Preserve declared spec before overwriting with resolved version
                pkg.declared_spec = pkg.declared_spec || pkg.v;
                pkg.resolution_state = 'STALE_LOCK';
                pkg.v = resolved;
                correctedCount++;
              }
            }
            if (correctedCount > 0) {
              UI.log(`[DIAG] O1-10: corrected ${correctedCount} package version(s) using lockfile resolved versions`);
            }
          }
        }
  
        packages = parseResult.packages;
        ecosystem = parseResult.ecosystem;
  
        // 对于 Edit/MultiEdit，额外解析磁盘内容用于降级检?
        let diskPackages = null;
        if ((toolName === 'Edit' || toolName === 'MultiEdit') && diskContent) {
          const diskParseResult = parseManifest(filePath, diskContent);
          if (diskParseResult && diskParseResult.packages.length > 0) {
            diskPackages = diskParseResult.packages;
            UI.log(`[DIAG] Downgrade detection: disk has ${diskPackages.length} packages, new content has ${packages.length} packages`);
          }
        }
  
        context = {
          file_path: filePath,
          original_content: content,      // F-03 v6: proposed content for Edit/MultiEdit
          disk_content: diskContent,      // 竞态基线校验
          disk_packages: diskPackages,    // 磁盘上的依赖列表（用于降级检测）
          audited_packages: null,         // F-03 v6: set after privacy filtering
          auditMode: false,              // V7-F02: set after privacy filtering
          tool_name: toolName,
          ecosystem: parseResult.ecosystem,
          client: hookMeta.client_type,
          session_id: hookMeta.session_id,
          // S2 门禁 G1：显式 phase（服务端仅接受字面量 PRECHECK，缺失即不采集）
          phase: 'PRECHECK',
          // S2 关联键：仅透传用于服务端组件行关联，不参与任何去重
          call_id: hookMeta.call_id ?? null,
          customTimeout: config.customTimeout || false
        };
  
      } else if (toolName === 'Bash') {
        // 命令执行：检查是否为包安装命?
        const command = toolInput.command;
        
        if (!isPackageInstallCommand(command)) {
          ui.debug(`Command is not a package install, allowing`);
          process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'allow'
            }
          }));
          reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'not_package_install_command', { toolName: 'Bash' });
          return;
        }
        
        // 拆分链式命令，逐段解析，按各自 ecosystem 分组（而不?"第一? ecosystem 覆盖全部"?
        // 背景：混合语言链式命令（如 `npm install lodash && pip install Django`）此前会?
        // 第二个及之后子命令的包也归到第一个识别到? ecosystem 下查询，导致其被以错误的
        // 生态系统语义审计（例如? npm registry 语义查一? PyPI 包），造成漏检?
        const subCommands = splitShellCommand(command);
        const packagesByEcosystem = new Map(); // ecosystem -> packages[]
        
        for (const sub of subCommands) {
          const parseResult = parseCommand(sub);
          if (parseResult && parseResult.packages.length > 0) {
            const list = packagesByEcosystem.get(parseResult.ecosystem) || [];
            list.push(...parseResult.packages);
            packagesByEcosystem.set(parseResult.ecosystem, list);
          }
        }
        
        if (packagesByEcosystem.size === 0) {
          ui.debug('No packages found in command, allowing');
          process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'allow'
            }
          }));
          reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'no_packages_in_command', { toolName: 'Bash' });
          return;
        }
  
        const commandTokens = splitShellCommandWithSeparators(command);
        // V8-F02: Inject auditMode into baseContext for multi-ecosystem Bash
        const _bashPrivacyConfig = loadConfigFromEnv();
        const baseContext = {
          command: command,
          commandTokens,
          tool_name: toolName,
          client: hookMeta.client_type,
          session_id: hookMeta.session_id,
          auditMode: _bashPrivacyConfig.auditMode || false,
          // S2 门禁 G1：显式 phase（多生态路径，服务端仅接受字面量 PRECHECK）
          phase: 'PRECHECK',
          // S2 关联键：仅透传用于服务端组件行关联，不参与任何去重
          call_id: hookMeta.call_id ?? null,
          customTimeout: config.customTimeout || false
        };
  
        if (packagesByEcosystem.size === 1) {
          // 单一 ecosystem：与此前行为完全一致，走原有单请求路径（零回归风险?
          const [onlyEcosystem, onlyPackages] = [...packagesByEcosystem.entries()][0];
          packages = onlyPackages;
          ecosystem = onlyEcosystem;
          context = { ...baseContext, ecosystem: onlyEcosystem };
          if (isComplexShellSyntax(command)) {
            // D1-18：含 $()/backtick/heredoc 的命令禁止自动改写，强制?"仅展?
            // 建议不自动修"的路径（复用现有? disableAutofix 开关语义）
            context.disableAutofix = true;
          }
        } else {
          // 混合多 ecosystem：按各自生态分别请求 Server 审计，结果保守合并后直接
          // 在此处输出响应并返回，不复用下方的单 ecosystem 的通用主流程
          await handleMultiEcosystemBash(
            packagesByEcosystem, baseContext, toolName, toolInput, config,
            hookMeta, startTime, ui
          );
          return;
        }
        
      } else if (toolName === 'REPL') {
        // PTC (Program-The-Conversation) Agent 模式自适应：
        // 嗅探 REPL 代码中调用的依赖写入（Write/Edit）或安装命令（Bash）
        const code = toolInput.code || toolInput.command || toolInput.script || '';
  
        if (!code || typeof code !== 'string') {
          ui.debug('REPL has no code to inspect, allowing');
          process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'allow'
            }
          }));
          reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'no_code_in_repl', { toolName });
          return;
        }
  
        const replOps = parseReplOperations(code);
        if (!replOps || replOps.length === 0) {
          ui.debug('No dependency operations found in REPL code, allowing');
          process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'allow'
            }
          }));
          reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'no_dependency_ops_in_repl', { toolName });
          return;
        }
  
        const packagesByEcosystem = new Map();
        let primaryContext = null;
  
        for (const op of replOps) {
          if (op.type === 'Write' || op.type === 'Edit') {
            if (!op.filePath || !isDependencyManifest(op.filePath)) continue;
            let content = op.content;
            if (op.type === 'Edit') {
              const diskContent = readDiskFile(op.filePath);
              content = computeEditResult(diskContent || '', op.oldString, op.newString);
            }
            if (!content) continue;
            const parseResult = parseManifest(op.filePath, content);
            if (parseResult && parseResult.packages.length > 0) {
              const list = packagesByEcosystem.get(parseResult.ecosystem) || [];
              list.push(...parseResult.packages);
              packagesByEcosystem.set(parseResult.ecosystem, list);
              if (!primaryContext) {
                primaryContext = {
                  file_path: op.filePath,
                  original_content: content,
                  tool_name: 'REPL',
                  ecosystem: parseResult.ecosystem,
                  client: hookMeta.client_type,
                  session_id: hookMeta.session_id,
                  phase: 'PRECHECK',
                  call_id: hookMeta.call_id ?? null,
                  disableAutofix: true,
                  customTimeout: config.customTimeout || false
                };
              }
            }
          } else if (op.type === 'Bash') {
            if (!op.command || !isPackageInstallCommand(op.command)) continue;
            const subCommands = splitShellCommand(op.command);
            for (const sub of subCommands) {
              const parseResult = parseCommand(sub);
              if (parseResult && parseResult.packages.length > 0) {
                const list = packagesByEcosystem.get(parseResult.ecosystem) || [];
                list.push(...parseResult.packages);
                packagesByEcosystem.set(parseResult.ecosystem, list);
                if (!primaryContext) {
                  primaryContext = {
                    command: op.command,
                    tool_name: 'REPL',
                    ecosystem: parseResult.ecosystem,
                    client: hookMeta.client_type,
                    session_id: hookMeta.session_id,
                    phase: 'PRECHECK',
                    call_id: hookMeta.call_id ?? null,
                    disableAutofix: true,
                    customTimeout: config.customTimeout || false
                  };
                }
              }
            }
          }
        }
  
        if (packagesByEcosystem.size === 0) {
          ui.debug('No parseable packages found in REPL dependency ops, allowing');
          process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'allow'
            }
          }));
          reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'no_packages_in_repl', { toolName });
          return;
        }
  
        if (packagesByEcosystem.size === 1) {
          const [onlyEcosystem, onlyPackages] = [...packagesByEcosystem.entries()][0];
          packages = onlyPackages;
          ecosystem = onlyEcosystem;
          context = { ...primaryContext, ecosystem: onlyEcosystem };
        } else {
          const allPackages = [];
          for (const [eco, pkgs] of packagesByEcosystem.entries()) {
            allPackages.push(...pkgs);
          }
          packages = allPackages;
          ecosystem = [...packagesByEcosystem.keys()][0];
          context = { ...primaryContext, ecosystem };
        }
  
      } else {
        // 其他工具，直接放行
        ui.debug(`Tool ${toolName} not monitored, allowing`);
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'allow'
          }
        }));
        reportApplicabilitySkip(hookMeta, startTime, config.serverUrl, 'tool_not_monitored', { toolName });
        return;
      }
      
      // 安全边界：不记录具体包名/版本（隐私过滤在下方才执行，此处如果打印包名?
      // 把本应被过滤掉的私有包名也提前写入日志），只记录数量
      ui.debug(`Found ${packages.length} packages in ${ecosystem}`);
  
      // 3.5 serverUrl 为空时直接放行（网关地址未配置）
      if (!config.serverUrl) {
        ui.debug('serverUrl is empty, skipping audit (fail-open)');
        // D1-15: 复用 buildAllowResponse 统一处理 fail-open 可见?
        process.stdout.write(JSON.stringify(buildAllowResponse('no_server_url_fail_open', { sessionId: hookMeta.session_id })));
        return;
      }
  
      // 4. 隐私过滤 - 移除私有包，防止敏感信息泄露
      const privacyConfig = loadConfigFromEnv();
      privacyConfig.debug = config.debug;
  
      // [DIAG] 打印 autofix 开关状?
      UI.log(`[DIAG] SECURITY_GUARD_DISABLE_AUTOFIX env: ${process.env.SECURITY_GUARD_DISABLE_AUTOFIX}`);
      UI.log(`[DIAG] disableAutofix: ${privacyConfig.disableAutofix}`);
  
      const { filtered: filteredPackages, removed: removedPackages, stats } = filterPrivatePackages(packages, privacyConfig);
  
      // F-03 v6: Inject audited package set into context (after privacy filtering)
      // V7-F02: Also inject auditMode from privacyConfig
      if (context) {
        context.audited_packages = filteredPackages;
        context.auditMode = privacyConfig.auditMode || false;
      }
      
      if (removedPackages.length > 0) {
        // 安全边界：绝不记录被隐私过滤移除的包名——这些正是被判定?"私有/敏感"?
        // 组件名，打印出来等于让日志文件成为隐私过滤器的绕过通道
        ui.debug(`Privacy filter removed ${removedPackages.length} private package(s)`);
      }
      
      // 如果所有包都被过滤了，直接放行
      if (filteredPackages.length === 0) {
        ui.debug('All packages filtered by privacy filter, allowing');
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'allow',
            permissionDecisionReason: 'all_packages_filtered_private'
          }
        }));
        // 更新 hookMeta 以包? ecosystem ? toolName
        hookMeta.ecosystem = ecosystem;
        hookMeta.toolName = toolName;
  
        // 上报：所有包被隐私过滤，插件工作了但主动跳过
        setImmediate(() => {
          try {
            recordAndSend({
              ...buildBaseEvent(hookMeta, startTime),
              package_count_total: packages.length,
              package_count_sent:  0,
              server_status:       'N/A',
              hook_decision:       'allow',
              fail_mode_trigger:   false,
              skip_reason:         'all_packages_private',
            }, config.serverUrl);
          } catch {
            // 静默忽略
          }
        });
        return;
      }
      
      ui.debug(`Sending ${filteredPackages.length} packages to server (filtered ${stats.removed} private)`);
      
      // 记录发送给服务器之前的耗时
      const beforeServerTime = Date.now();
      const processingTimeMs = beforeServerTime - startTime;
      ui.performance(`Processing time before server call: ${processingTimeMs}ms, packages=${filteredPackages.length}, ecosystem=${ecosystem}`);
      
      // 5. 调用 Server 检?
      const serverStartTime = Date.now();
      const serverResponse = await checkPackages(
        ecosystem,
        filteredPackages,
        context,
        config.serverUrl,
        config.timeout,
        config.retries
      );
      const serverEndTime = Date.now();
      const serverTimeMs = serverEndTime - serverStartTime;
      const normalizedServerResponse = normalizeServerResponse(serverResponse);
      const serverResponseSummary = summarizeServerResponseForLog(normalizedServerResponse);
      
      ui.performance(`Server request time: ${serverTimeMs}ms, status=${normalizedServerResponse.s || 'unknown'}, fail_open=${normalizedServerResponse.fail_open || false}`);
      ui.debug('Server response:', serverResponseSummary);
  
      // [DIAG] 只打印精简摘要，避? fixed_content 等长文本污染会话
      UI.log(`[DIAG] server_response: ${JSON.stringify(serverResponseSummary)}`);
  
      // 6. 注入分级审查配置和全局开?
      if (context && typeof context === 'object') {
        context.riskConfig = {
          highThreshold:   privacyConfig.highThreshold,
          mediumThreshold: privacyConfig.mediumThreshold,
        };
        // D1-18：用"或运?"而不是直接赋值覆盖——如? Bash 分支已经因为检测到复杂
        // shell 语法?$()/backtick/heredoc）提前把 context.disableAutofix 设为
        // true，这里绝不能把它静默清空? privacyConfig 的默认?
        context.disableAutofix = context.disableAutofix || privacyConfig.disableAutofix || false;
        // P0-1 risk-policy 维度（与 mode 正交）：机器授权边界。v1 只作为标记贯穿
        // context / 审计 / 埋点，**不解锁跨 Major 自动修复**（见 SECURITY_GUARD_ALLOW_MAJOR_AUTOFIX）
        context.majorAutofix = context.majorAutofix || privacyConfig.majorAutofix || false;
      }
  
      // 7. 构? Hook 响应
      const preDedupResponse = buildHookResponse(normalizedServerResponse, toolName, toolInput, context);
  
      // D1-14: 全原? Session 去重。只?"? PASS 且非 fail-open"的结果去重—?
      // PASS 本身不构成阻断循环，fail-open 已由 D1-15 用独立的健康↔降级状态切?
      // 语义处理，混?"相同输入重复 N ?"语义会冲突（fail-open 不是"相同输入"
      // 的概念，?"这次检查没有真正完?"）?
      // D2-v4: finding-state-aware session 去重 + 熔断。
      // 设计边界（用户裁定）：
      //  - resetRemediationSession 必须以 serverDecision/findingSet 为准，绝不依赖本地 client response；
      //  - terminal 主判据改为 trackRemediationProgress().shouldTrip（连续相同 finding state）；
      //  - classifyAndRecord 仅保留做 exact-retry 统计/收缩，不再单独触发 terminal（避免与 progress-aware 打架）。
      let dedupResult = { state: 'first', retryCount: 1 };
      // D0-12ȶ `decision`normalizeServerResponse  fallback  s fallback s
      const _dedupDecision = normalizedServerResponse.decision || normalizedServerResponse.s;
  
      // sessionKey：以 tool + 归一化文件/依赖意图 + session 为锚（Bash / REPL 用依赖意图而非命令全文）
      const _sessionAnchor = (toolName === 'Bash' || toolName === 'REPL')
        ? (ecosystem || toolName.toLowerCase()) + ':' + (filteredPackages || []).map(p => `${String(p?.n ?? '').toLowerCase()}@${p?.v ?? ''}`).sort().join(',')
        : (toolInput?.file_path || context?.file_path || 'unknown');
      const _sessionKey = `${toolName}|${_sessionAnchor}|${hookMeta?.session_id ?? ''}`;
  
      // 构造“当前仍 actionable 的 finding 集合”（用下一轮 Server 重新审计结果归一化；不新增 Server 字段）
      const _actionableFindings = normalizedServerResponse.unfixable?.length
        ? normalizedServerResponse.unfixable
        : (normalizedServerResponse.changes?.length ? normalizedServerResponse.changes : []);
      const _findingDigest = findingSetDigest(
        _actionableFindings.map(f => ({
          n: f?.n || f?.package || (f?.to?.split('@')[0]) || (f?.from?.split('@')[0]) || '',
          v: f?.v || (f?.to?.split('@')[1]) || (f?.from?.split('@')[1]) || '',
          cve: f?.cve || f?.vulnId || '',
          reason: f?.reason_code || f?.reason || '',
        }))
      );
  
      // 边界1：Server PASS 或 finding 集合为空 → 本轮 remediation 已结束，直接 reset session（不依赖 fingerprint）
      if (_dedupDecision === 'PASS' || _findingDigest === 'EMPTY' || isFailOpenReason(normalizedServerResponse.reason)) {
        resetRemediationSession(hookMeta?.session_id, _sessionKey);
      } else {
        // 边界2：terminal 主判据 = finding-state-aware 熔断
        // classifyAndRecord 仍运行（做 exact-retry 统计/收缩），但其 terminal 不再单独生效
        const fingerprintPackages = _actionableFindings.length
          ? _actionableFindings.map(f => ({ n: f?.n || f?.package || (f?.to?.split('@')[0]) || (f?.from?.split('@')[0]) || '', v: f?.v || (f?.to?.split('@')[1]) || (f?.from?.split('@')[1]) || '' }))
          : filteredPackages;
        const fingerprint = computeFingerprint({
          toolName,
          ecosystem,
          packages: fingerprintPackages,
          // D0-12dedup fingerprint  decisionֶΣ+ reason_codeֶΣ
          // fallback  reason/hook_action֤ Server Ӧȷȥ
          decision: _dedupDecision,
          reasonCode: normalizedServerResponse.reason_code || normalizedServerResponse.reason || normalizedServerResponse.hook_action || '',
          fixTarget: normalizedServerResponse.fixed_content || '',
        });
        // classifyAndRecord 保留做 exact-retry 统计/收缩（suppressed 文案仍生效），
        // 但其 terminal 不再单独触发——terminal 主判据统一交给 progress 熔断。
        dedupResult = classifyAndRecord(hookMeta.session_id, fingerprint);
        const _progress = trackRemediationProgress(hookMeta?.session_id, _sessionKey, _findingDigest);
        if (process.env.SECURITY_GUARD_DEBUG === '1') process.stderr.write(`[D2V4] decision=${_dedupDecision} digest=${_findingDigest} shouldTrip=${_progress.shouldTrip} streak=${_progress.noProgressStreak}\n`);
        if (_progress.shouldTrip) {
          // 连续相同 finding state 达阈值 → 升级为 terminal（覆盖 classify 的 suppressed/first）
          dedupResult = { state: 'terminal', retryCount: _progress.noProgressStreak };
        }
      }
      const hookResponse = applyDedup(preDedupResponse, dedupResult);
  
      // 6.5 Save precheck transaction for PostToolUse lockfile re-audit
      // V20-FIX: Save for ALL dependency operations, not just Autofix
      // This ensures PostToolUse can re-audit even when PreToolUse was PASS or BLOCK-without-autofix
      const inputFieldName = isIdeClient(context?.client) ? 'modifiedInput' : 'updatedInput';
      const hasModifiedInput = !!(hookResponse?.hookSpecificOutput?.modifiedInput || hookResponse?.hookSpecificOutput?.updatedInput);
      // V20: Save precheck transaction whenever there are audited packages (even without autofix)
      if (filteredPackages && filteredPackages.length > 0) {
        const modifiedInput = hasModifiedInput ? hookResponse?.hookSpecificOutput?.[inputFieldName] : null;
        // F-05 V23: Resolve manifest+lockfile path for Write/Edit (file_path) and Bash/REPL
        let _manifestPath = toolInput.file_path || context?.file_path || null;
        let _lockfilePath = null;
        let _bashPathResolved = true;  // V23: track if we confidently resolved Bash cwd
        if (_manifestPath) {
          if (/package\.json$/.test(_manifestPath)) {
            _lockfilePath = _manifestPath.replace(/package\.json$/, 'package-lock.json');
            if (!existsSync(_lockfilePath)) {
              const pnpmPath = _manifestPath.replace(/package\.json$/, 'pnpm-lock.yaml');
              if (existsSync(pnpmPath)) {
                _lockfilePath = pnpmPath;
              } else {
                const yarnPath = _manifestPath.replace(/package\.json$/, 'yarn.lock');
                if (existsSync(yarnPath)) {
                  _lockfilePath = yarnPath;
                }
              }
            }
          } else if (/(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock)$/.test(_manifestPath)) {
            _lockfilePath = _manifestPath;
          } else if (/Cargo\.toml$/.test(_manifestPath)) {
            _lockfilePath = _manifestPath.replace(/Cargo\.toml$/, 'Cargo.lock');
          }
        } else if (toolName === 'Bash') {
          // V23: Parse shell command to find effective working directory
          // Handle: cd <dir> &&, cd <dir> ;, cd <dir> ||, cd <dir> && cd <dir2> &&, ~ expansion
          const _cmd = toolInput.command || '';
          let _cwd = process.cwd();
          // Split on && ; || to process cd segments in order
          const _segments = _cmd.split(/\s*(?:&&|;|\|\|)\s*/);
          let _cdFound = false;
          for (const seg of _segments) {
            const _cdM = seg.match(/^cd\s+["']?([^"'&|;]+)["']?\s*$/);
            if (_cdM) {
              let dir = _cdM[1].replace(/^~/, process.env.HOME || '~');
              if (!dir.startsWith('/')) dir = pathJoin(_cwd, dir);
              _cwd = dir;
              _cdFound = true;
            }
          }
          if (_cdFound) {
            _manifestPath = pathJoin(_cwd, 'package.json');
            _lockfilePath = pathJoin(_cwd, 'package-lock.json');
          } else {
            // V24: No cd found — we cannot confidently associate process.cwd() with this
            // tool operation. process.cwd() is the hook process's directory, which may
            // differ from the Agent's project root and could collide with an unrelated
            // package.json. Mark unresolved → PostToolUse will emit PRECHECK_ONLY.
            _bashPathResolved = false;
          }
        }
        const _lockfileContent = _lockfilePath ? readDiskFile(_lockfilePath) : '';
        const fixInfo = {
          timestamp: new Date().toISOString(),
          callId: input.raw.call_id || null,
          filePath: _manifestPath,
          changes: normalizedServerResponse.changes || [],
          modifiedContent: modifiedInput?.content || modifiedInput?.command || null,
          // F-05: Precheck transaction for lockfile re-audit
          phase: "PRECHECK",
          operation_id: input.raw.tool_use_id || input.raw.call_id || null,
          ecosystem: ecosystem || null,
          manifest_path: _manifestPath,
          lockfile_path: _lockfilePath,
          bash_path_resolved: _bashPathResolved, // V23: track if Bash cwd was confidently resolved
          packages: (filteredPackages || []).map(p => ({
            name: p.n, version: p.v,
            declared_spec: p.declared_spec || p.v,
            resolution_state: p.resolution_state || 'EXACT',
          })),
          manifest_before_sha256: _sha256(context?.disk_content || toolInput.content || ''),
          lockfile_before_sha256: _sha256(_lockfileContent || ''),
        };
        try {
          // D1-19 修复：按本次操作关联键派生专属文件路径，? handlePostToolUse()
          // 中的读取逻辑保持一致的派生规则，避免使用固定全局文件造成跨操作串?
          const { path: writeFixInfoPath } = getFixInfoPath(input.raw.tool_use_id, input.raw.call_id);
          writeFileSync(writeFixInfoPath, JSON.stringify(fixInfo), { mode: 0o600 });
          UI.log(`[DIAG] Saved fix info for PostToolUse: ${JSON.stringify({
            timestamp: fixInfo.timestamp,
            callId: fixInfo.callId,
            // 安全边界：不记录完整绝对路径，只记录 basename 便于排障关联文件类型
            fileName: fixInfo.filePath ? fixInfo.filePath.split(/[\\/]/).pop() : null,
            changes_count: fixInfo.changes?.length ?? 0,
            modifiedContent: fixInfo.modifiedContent ? `[${fixInfo.modifiedContent.length} chars]` : null,
          })}`);
        } catch (e) {
          UI.log(`[DIAG] Failed to save fix info: ${e.message}`);
        }
  
        // 产研采纳与风险闭环：记录待确认的安全建议项
        recordPendingAdoptions({
          ecosystem,
          packages: filteredPackages,
          changes: normalizedServerResponse.changes || [],
          unfixable: normalizedServerResponse.unfixable || [],
          serverResponse: normalizedServerResponse,
          toolInput,
          inputRaw: input.raw,
          cwd: process.cwd(),
        });
      }
  
      // 7. 记录总处理耗时
      const endTime = Date.now();
      const totalTimeMs = endTime - startTime;
      ui.performance(`Total processing time: ${totalTimeMs}ms (pre-server: ${processingTimeMs}ms, server: ${serverTimeMs}ms, post-server: ${totalTimeMs - processingTimeMs - serverTimeMs}ms)`);
  
      // [DIAG] 打印最? Hook 响应（关键决策信息）
      const finalDecision = hookResponse?.hookSpecificOutput?.permissionDecision ?? 'allow';
      const finalReason = hookResponse?.hookSpecificOutput?.permissionDecisionReason ?? '';
      UI.log(`[DIAG] ===== HOOK RESPONSE SUMMARY =====`);
      UI.log(`[DIAG] client: ${context?.client || 'CLI'}`);
      UI.log(`[DIAG] permissionDecision: ${finalDecision}`);
      UI.log(`[DIAG] permissionDecisionReason: ${finalReason.substring(0, 100)}${finalReason.length > 100 ? '...' : ''}`);
      UI.log(`[DIAG] has_${inputFieldName}: ${hasModifiedInput}`);
      if (hasModifiedInput) {
        const inputContent = hookResponse?.hookSpecificOutput?.[inputFieldName];
        const inputSummary = inputContent
          ? {
              ...inputContent,
              content: inputContent.content ? `[${inputContent.content.length} chars]` : undefined,
              command: inputContent.command
                ? (inputContent.command.length > 200 ? `${inputContent.command.slice(0, 200)}...` : inputContent.command)
                : undefined,
            }
          : null;
        UI.log(`[DIAG] ${inputFieldName}: ${JSON.stringify(inputSummary)}`);
      }
      UI.log(`[DIAG] continue: ${hookResponse?.continue ?? true}`);
      UI.log(`[DIAG] hook_response: ${JSON.stringify({
        continue: hookResponse?.continue ?? true,
        suppressOutput: hookResponse?.suppressOutput ?? false,
        systemMessage: hookResponse?.systemMessage
          ? `${hookResponse.systemMessage.substring(0, 200)}${hookResponse.systemMessage.length > 200 ? '...' : ''}`
          : undefined,
        hookSpecificOutput: {
          hookEventName: hookResponse?.hookSpecificOutput?.hookEventName,
          permissionDecision: finalDecision,
          permissionDecisionReason: finalReason
            ? `${finalReason.substring(0, 200)}${finalReason.length > 200 ? '...' : ''}`
            : undefined,
          additionalContext: hookResponse?.hookSpecificOutput?.additionalContext
            ? `[${hookResponse.hookSpecificOutput.additionalContext.length} chars]`
            : undefined,
        },
      })}`);
      UI.log(`[DIAG] ==================================`);
  
      // 8. 记录最终输出日?
      ui.debug('Final hook response:', hookResponse);
      
      // 9. 输出 Hook 响应 (stdout) - 只输出纯 JSON，不输出任何其他内容
      process.stdout.write(JSON.stringify(hookResponse));
  
      // 更新 hookMeta 以包? ecosystem ? toolName
      hookMeta.ecosystem = ecosystem;
      hookMeta.toolName = toolName;
  
      // P0-1：跨 Major 观测。v1 恒定"不解锁跨 Major 自动修复"——这里只是把判定
      // 结果送进埋点与审计留痕，用于观测真实诉求量（opt-in 命中率），不影响执行结果。
      const crossMajorChanges = findCrossMajorChanges(normalizedServerResponse.changes);
      const crossMajorHit = crossMajorChanges.length > 0;
      const crossMajorOptIn = (crossMajorHit && context?.majorAutofix === true) ? 'opted_in_pending' : null;
  
      // 10. 埋点上送（主流程已结束，fire-and-forget，不影响 Claude Code?
      setImmediate(() => {
        try {
          const decision = hookResponse?.hookSpecificOutput?.permissionDecision ?? 'allow';
          const isFail = normalizedServerResponse.fail_open === true;
          recordAndSend({
            ...buildBaseEvent(hookMeta, startTime),
            // 业务维度
            package_count_total:  packages.length,
            package_count_sent:   filteredPackages.length,
            // 决策结果
            server_status:        normalizedServerResponse.s ?? 'PASS',
            // D0-12ϱͳһֶΣȣ+ reason_codeö٣Ϊ null
            server_decision:      normalizedServerResponse.decision ?? null,
            reason_code:          normalizedServerResponse.reason_code ?? null,
            hook_decision:        decision,
            block_reason:         normalizedServerResponse.reason ?? null,
            // Autofix 效果量化
            autofix_applied:      !!(normalizedServerResponse.fixed_content && decision === 'allow'),
            autofix_cve_count:    normalizedServerResponse.changes?.filter(c => c.cve)?.length ?? 0,
            autofix_max_cvss:     normalizedServerResponse.changes?.reduce((max, c) => c.cvss ? Math.max(max, c.cvss) : max, 0) || null,
            autofix_type:         normalizedServerResponse.fixed_content
                                    ? (toolName !== 'Bash' ? 'file' : 'command')
                                    : null,
            autofix_pkg_count:    normalizedServerResponse.changes?.length ?? 0,
            // P0-1 跨 Major 风险策略（v1 只观测：命中 ≠ 放行，只是需求观测信号）
            cross_major_hit:      crossMajorHit,
            cross_major_opt_in:   crossMajorOptIn,
            // 网络健康
            http_status_code:     normalizedServerResponse._http_status ?? null,
            retry_count:          normalizedServerResponse._retry_count ?? 0,
            // 运行健康
            fail_mode_trigger:    isFail,
            error_type:           isFail ? (normalizedServerResponse.reason ?? null) : null,
            skip_reason:          null,
            // D1-14: 去重状态（不上? fingerprint 明文本身，只上报分类结果和次数）
            dedup_state:          dedupResult.state,
            dedup_retry_count:    dedupResult.retryCount,
            // O1-22 (minimal slice): model context token budget telemetry
            context_chars:              hookResponse?.hookSpecificOutput?.additionalContext?.length ?? 0,
            additional_context_emitted: !!hookResponse?.hookSpecificOutput?.additionalContext,
            duplicate_context_suppressed: dedupResult.state === 'suppressed',
            // O2-30 (minimal slice): phase timing instrumentation for SLO
            // phase_stdin_ms: stdin read duration
            // phase_parse_ms: input parsing duration
            // phase_network_ms: server-side processing time (from server response 't' field)
            // phase_decision_ms: decision construction + response building (derived)
            phase_stdin_ms:   _phaseStdinMs ?? null,
            phase_parse_ms:   _phaseParseMs ?? null,
            phase_network_ms: normalizedServerResponse.t ?? null,
            phase_decision_ms: (Date.now() - startTime) - (_phaseStdinMs ?? 0) - (_phaseParseMs ?? 0) - (normalizedServerResponse.t ?? 0),
            // O1-25 (3-state slice): package confidence signal category
            // NOT_FOUND_PUBLIC: package not in registry (possible hallucination/typo)
            // EXISTS_NO_KNOWN_MALWARE: package exists, no known malware (not 'SAFE' — see doc)
            // SOURCE_UNAVAILABLE: registry/degraded, cannot determine existence
            signal_category: normalizedServerResponse.reason_code === 'PACKAGE_NOT_FOUND'
              ? 'NOT_FOUND_PUBLIC'
              : (normalizedServerResponse.reason_code === 'SOURCE_UNAVAILABLE'
                ? 'SOURCE_UNAVAILABLE'
                : (normalizedServerResponse.fail_open ? 'SOURCE_UNAVAILABLE' : 'EXISTS_NO_KNOWN_MALWARE')),
          }, config.serverUrl);
  
          // O2-23：接入此前已经写好但从未被调用的本地审计日志（区别于
          // Telemetry——这是完全本地、不上网的结构化记录，供 --report 命令
          // 读取生成报告）。只记录? PASS 且非 fail-open 的真正决策事件，
          // PASS 静默放行不构?"处置"事件——与上面 D1-14 dedup 判断"什么算
          // 需要记录的事件"用同一个边界条件，不新造一个判断口径?
          if (normalizedServerResponse.s !== 'PASS' && !isFail) {
            const riskLevel = getRiskLevel(normalizedServerResponse.changes, context?.riskConfig || {});
            const auditEntry = buildAuditEntry({
              toolName,
              toolInput,
              changes: normalizedServerResponse.changes,
              decision,
              riskLevel,
              context: {
                repo:      context?.repo || null,
                branch:    context?.branch || null,
                ecosystem,
                // P0-1：跨 Major 只在审计里留痕；opt-in 同样只标记、不解锁行为
                cross_major:        crossMajorHit,
                cross_major_opt_in: crossMajorOptIn,
              },
              clientVer: hookMeta.codebuddy_version,
              sessionId: hookMeta.session_id,
            });
            // 复用 loadConfigFromEnv() 已经解析出的 auditLog 路径（来?
            // SECURITY_GUARD_AUDIT_LOG），未设置时 appendAuditLog 自己?
            // 回退? DEFAULT_AUDIT_LOG——不在这里重复默认值判断逻辑
            appendAuditLog(auditEntry, privacyConfig.auditLog || undefined); // 内部已有 try/catch，写入失败静默忽?
          }
        } catch {
          // 静默忽略，埋点绝不影响主流程
        }
      });
      
    } catch (error) {
      // 错误? Fail-Open - 只输? JSON，不输出错误信息
      // 将错误写入日志文件，便于调试；同 logCrash() 一样脱敏路径信息，不记录原?
      UI.log(`[ERROR] Uncaught exception in main(): ${error instanceof Error ? `${error.constructor?.name || 'Error'}: ${redactMessagePatterns(error.message || '').slice(0, CRASH_MESSAGE_MAX_LEN)}\n${redactStackPaths(error.stack)}` : redactMessagePatterns(String(error)).slice(0, CRASH_MESSAGE_MAX_LEN)}`);
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'allow',
          permissionDecisionReason: 'security_guard_error_fail_open'
        }
      }));
      // 上报：Fail-Open 触发，用于稳定性监?
      setImmediate(() => {
        try {
          recordAndSend({
            ...buildBaseEvent(hookMeta, null),
            server_status:    'FAIL_OPEN',
            hook_decision:    'allow',
            fail_mode_trigger: true,
            error_type:        error instanceof Error ? error.message : String(error),
            http_status_code:  null,
            retry_count:       0,
            skip_reason:       null,
          }, config.serverUrl);
        } catch {
          // 静默忽略
        }
      });
    }
  }
  
  // 运行 - 只输? JSON，不输出任何其他内容
  main().catch(() => {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'allow'
      }
    }));
    process.exit(0);
  });
})();
