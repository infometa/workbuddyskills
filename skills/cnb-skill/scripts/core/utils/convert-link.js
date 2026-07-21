"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = convertLink;
/**
 * 把文本里的相对路径转换为绝对路径
 * 与 src/helpers/convertLink.ts 逻辑一致
 *
 * @param {String} text 待转换的文本
 * @param {String} repoSlug 仓库路径
 * @param {String} branchOrSha 可选，分支或SHA
 * @returns {String}
 */
function convertLink(text, repoSlug, branchOrSha) {
  // 查询所有代码块的位置
  let codeBlockPositions = [];
  let index = 0;
  while (index !== -1) {
    const nextIndex = text.indexOf('```', index);
    if (nextIndex === -1) break;
    codeBlockPositions.push(nextIndex);
    index = nextIndex + 3; // 跳过已匹配的三个反引号
  }
  if (codeBlockPositions.length % 2 !== 0) {
    codeBlockPositions = codeBlockPositions.slice(0, codeBlockPositions.length - 1);
  }

  // 查询所有行内代码块的位置
  let inlineCodeBlockPositions = [];
  index = 0;
  while (index < text.length) {
    const nextIndex = text.indexOf('`', index);
    if (nextIndex === -1) break;
    // 检查是否是单独的反引号（不是代码块的一部分）
    if ((nextIndex === 0 || text.charAt(nextIndex - 1) !== '`') && (nextIndex === text.length - 1 || text.charAt(nextIndex + 1) !== '`')) {
      inlineCodeBlockPositions.push(nextIndex);
    }
    index = nextIndex + 1;
  }
  if (inlineCodeBlockPositions.length % 2 !== 0) {
    inlineCodeBlockPositions = inlineCodeBlockPositions.slice(0, inlineCodeBlockPositions.length - 1);
  }

  // 整理起始和结束位置
  const excludedRanges = [...codeBlockPositions, ...inlineCodeBlockPositions].reduce((result, item, index) => {
    if (index % 2 === 0) {
      return result.concat([[item]]);
    } else {
      result[result.length - 1].push(item);
      return result;
    }
  }, []);

  // Helper function to check if an index is within excluded ranges
  const isInExcludedRange = index => {
    return excludedRanges.some(([start, end]) => index >= start && index < end);
  };
  let match;

  // Collect all replacements with their positions
  const replacements = [];

  // Match markdown links and images: [alt](url), [](url), ![alt](url) and ![](url)
  const markdownLinkRegex = /!?\[([^\]]*)\]\(([^)]+)\)/g;
  while ((match = markdownLinkRegex.exec(text)) !== null) {
    if (!isInExcludedRange(match.index)) {
      // Calculate URL position: match.index + length of "![" + match[1] + "]("
      const prefixLength = (match[0].startsWith('!') ? 1 : 0) + 1 + match[1].length + 2;
      const urlStart = match.index + prefixLength;
      const urlEnd = urlStart + match[2].length;
      const newUrl = normaliseLink(match[2], repoSlug, branchOrSha);
      if (newUrl !== match[2]) {
        replacements.push({
          start: urlStart,
          end: urlEnd,
          newUrl
        });
      }
    }
  }

  // Match HTML tags: <img src="..."> and <a href="...">
  const htmlTagRegex = /\s(src|href)=["']([^"']+)["']/gi;
  while ((match = htmlTagRegex.exec(text)) !== null) {
    if (!isInExcludedRange(match.index)) {
      const urlStart = match.index + match[0].indexOf(match[2]);
      const urlEnd = urlStart + match[2].length;
      const newUrl = normaliseLink(match[2], repoSlug, branchOrSha);
      if (newUrl !== match[2]) {
        replacements.push({
          start: urlStart,
          end: urlEnd,
          newUrl
        });
      }
    }
  }

  // Sort replacements by start position in descending order
  replacements.sort((a, b) => b.start - a.start);

  // Apply replacements from end to start to maintain correct indices
  let result = text;
  for (const {
    start,
    end,
    newUrl
  } of replacements) {
    result = result.substring(0, start) + newUrl + result.substring(end);
  }
  return result;
}

/**
 * 相对路径转换为绝对路径
 * 与 src/helpers/convertLink.ts 逻辑一致
 *
 * @param {String} link 待转换的链接
 * @param {String} repoSlug 仓库路径
 * @param {String} branchOrSha 分支或SHA，默认为 HEAD
 * @returns {String}
 */
function normaliseLink(link, repoSlug, branchOrSha = 'HEAD') {
  const {
    CNB_WEB_ENDPOINT
  } = process.env;
  const baseURL = `${CNB_WEB_ENDPOINT}/${repoSlug}`;
  if (link.startsWith('/-/')) {
    return `${baseURL}${link}`;
  }
  if (link.indexOf('/-/') === -1 && (link.startsWith('../') || link.startsWith('./') || link.startsWith('/') && !link.startsWith('//'))) {
    let chunks = link.split('/');
    // 过滤掉空字符串和 . .. 这些无效路径
    chunks = chunks.filter(chunk => !!chunk && chunk !== '.' && chunk !== '..');
    if (chunks.length === 0) {
      return link;
    }
    chunks.unshift(branchOrSha);
    return `${baseURL}/-/git/raw/${chunks.join('/')}`;
  }
  return link;
}