export function reg2keywords(reg) {
  return reg.replace(/\(.*?\)/g, '#')
    .replace(/\[.*?]/g, '#')
    .replace(/\{.*?\}/g, '')
    .replace(/\\[wWsSdftv]/g, '')
    .replace(/\W+/g, '#')
    .split('#')
    .filter(Boolean)
    .map(str => str.toLowerCase());
}

/**
 * 从正则表达式中提取最长的字面文本，用于 indexOf 快速预过滤。
 * 如果日志行不包含该字面量，则该正则不可能匹配，可直接跳过 exec。
 *
 * @returns 小写字面量字符串，至少 3 个字符；无法提取时返回 null
 */

// Unicode 私有区域占位符，用于保护转义的字面字符
const PH_DOT = '\uE000';
const PH_DASH = '\uE001';
const PH_UNDER = '\uE002';

export function extractLiteral(reg) {
  const literals = reg
    // 保护转义的字面字符（\. → 占位, \- → 占位, \_ → 占位）
    .replace(/\\\./g, PH_DOT)
    .replace(/\\-/g, PH_DASH)
    .replace(/\\_/g, PH_UNDER)
    // 移除其他转义序列（\w, \s, \d, \n, \|, \( 等 → 空）
    .replace(/\\./g, '')
    // 移除字符集 [...]
    .replace(/\[.*?\]/g, '')
    // 移除含 alternation 的分组（整组不可靠）
    .replace(/\([^)]*\|[^)]*\)/g, ' ')
    // 移除可选分组 (...)? — 内容不一定出现
    .replace(/\([^)]*\)\?/g, ' ')
    // 移除完整分组：命名组 (?<name>, 非捕获组 (?:, 前瞻/后顾
    .replace(/\(\?<[a-zA-Z]\w*>/g, '')  // (?<name>
    .replace(/\(\?[:=!]/g, '')          // (?:, (?=, (?!
    .replace(/\(\?<[=!]/g, '')          // (?<=, (?<!
    .replace(/[()]/g, '')               // 剩余括号
    // 移除量词 {n,m}
    .replace(/\{.*?\}/g, '')
    // 用空格替换正则元字符
    .replace(/[.*+?^$|\\]/g, ' ')
    // 恢复占位符为字面字符
    .replace(new RegExp(PH_DOT, 'g'), '.')
    .replace(new RegExp(PH_DASH, 'g'), '-')
    .replace(new RegExp(PH_UNDER, 'g'), '_')
    .split(/\s+/)
    .filter(s => s.length >= 3);

  if (literals.length === 0) return null;

  // 返回最长的字面量（小写）
  let longest = literals[0];
  for (let i = 1; i < literals.length; i++) {
    if (literals[i].length > longest.length) {
      longest = literals[i];
    }
  }
  return longest.toLowerCase();
}

/**
 * 去除正则表达式无意义的 .* / .*? 前后缀。
 *
 * 在 'im' flag 下，.* 前缀会让 V8 从位置 0 贪婪扫描到行尾再回溯，
 * 去掉后 V8 可以直接用内置的快速前缀扫描定位首次匹配位置。
 *
 * 安全性：不影响匹配结果和捕获组值。
 */
export function optimizeRegex(reg) {
  return reg
    .replace(/^\.\*\??/, '')
    .replace(/\.\*\??$/, '');
}
