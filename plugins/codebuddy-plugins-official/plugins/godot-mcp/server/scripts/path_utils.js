/**
 * 跨平台路径工具
 * 
 * 处理 Windows/macOS/Linux 下的路径差异
 */

import { platform, homedir, arch } from 'os';
import { join, resolve, normalize, sep, posix, win32 } from 'path';
import { existsSync, statSync } from 'fs';

// 当前平台
export const PLATFORM = platform();
export const IS_WINDOWS = PLATFORM === 'win32';
export const IS_MACOS = PLATFORM === 'darwin';
export const IS_LINUX = PLATFORM === 'linux';

/**
 * 平台特定路径配置
 */
export const PlatformPaths = {
  // Claude Desktop 配置文件路径
  get claudeConfig() {
    const paths = {
      win32: join(homedir(), 'AppData', 'Roaming', 'Claude', 'claude_desktop_config.json'),
      darwin: join(homedir(), 'Library', 'Application Support', 'Claude', 'claude_desktop_config.json'),
      linux: join(homedir(), '.config', 'Claude', 'claude_desktop_config.json')
    };
    return paths[PLATFORM] || paths.linux;
  },
  
  // CodeBuddy IDE 配置文件路径（如果适用）
  get codebuddyConfig() {
    const paths = {
      win32: join(homedir(), 'AppData', 'Roaming', 'CodeBuddy', 'mcp_config.json'),
      darwin: join(homedir(), 'Library', 'Application Support', 'CodeBuddy', 'mcp_config.json'),
      linux: join(homedir(), '.config', 'CodeBuddy', 'mcp_config.json')
    };
    return paths[PLATFORM] || paths.linux;
  },
  
  // MCP Server 推荐安装目录
  get mcpServerDir() {
    const paths = {
      win32: join(homedir(), '.mcp-servers', 'godot-mcp'),
      darwin: join(homedir(), '.mcp-servers', 'godot-mcp'),
      linux: join(homedir(), '.mcp-servers', 'godot-mcp')
    };
    return paths[PLATFORM] || paths.linux;
  },
  
  // Node.js 可执行文件名
  get nodeExecutable() {
    return IS_WINDOWS ? 'node.exe' : 'node';
  }
};

/**
 * 获取平台特定路径（兼容旧接口）
 * @deprecated 使用 PlatformPaths.xxx 直接访问
 */
export function getPlatformPath(pathKey) {
  const value = PlatformPaths[pathKey];
  if (value === undefined) {
    throw new Error(`Unknown path key: ${pathKey}`);
  }
  return value;
}

/**
 * 规范化路径（处理斜杠方向）
 */
export function normalizePath(inputPath) {
  if (!inputPath) return inputPath;
  
  // 在 Windows 上使用反斜杠，其他平台使用正斜杠
  let normalized = normalize(inputPath);
  
  // 确保一致性
  if (IS_WINDOWS) {
    // Windows 路径使用反斜杠
    normalized = normalized.replace(/\//g, '\\');
  } else {
    // Unix 路径使用正斜杠
    normalized = normalized.replace(/\\/g, '/');
  }
  
  return normalized;
}

/**
 * 转换为 POSIX 风格路径（用于配置文件）
 * 某些工具要求使用正斜杠路径
 */
export function toPosixPath(inputPath) {
  if (!inputPath) return inputPath;
  return inputPath.replace(/\\/g, '/');
}

/**
 * 转换为原生平台路径
 */
export function toNativePath(inputPath) {
  if (!inputPath) return inputPath;
  
  if (IS_WINDOWS) {
    return inputPath.replace(/\//g, '\\');
  }
  return inputPath.replace(/\\/g, '/');
}

/**
 * 获取绝对路径
 */
export function toAbsolutePath(inputPath, basePath = process.cwd()) {
  if (!inputPath) return inputPath;
  
  // 已经是绝对路径
  if (IS_WINDOWS) {
    // Windows: C:\, D:\, \\server\share
    if (/^[a-zA-Z]:[\\/]/.test(inputPath) || inputPath.startsWith('\\\\')) {
      return normalizePath(inputPath);
    }
  } else {
    // Unix: /path/to/file
    if (inputPath.startsWith('/')) {
      return normalizePath(inputPath);
    }
  }
  
  // 相对路径转绝对路径
  return normalizePath(resolve(basePath, inputPath));
}

/**
 * 检查路径是否为绝对路径
 */
export function isAbsolutePath(inputPath) {
  if (!inputPath) return false;
  
  if (IS_WINDOWS) {
    return /^[a-zA-Z]:[\\/]/.test(inputPath) || inputPath.startsWith('\\\\');
  }
  return inputPath.startsWith('/');
}

/**
 * 获取用户主目录
 */
export function getHomeDir() {
  return homedir();
}

/**
 * 展开路径中的 ~ 符号
 */
export function expandTilde(inputPath) {
  if (!inputPath) return inputPath;
  
  if (inputPath.startsWith('~')) {
    return join(homedir(), inputPath.slice(1));
  }
  return inputPath;
}

/**
 * 验证路径存在性
 */
export function pathExists(inputPath) {
  try {
    return existsSync(inputPath);
  } catch {
    return false;
  }
}

/**
 * 检查是否为目录
 */
export function isDirectory(inputPath) {
  try {
    return statSync(inputPath).isDirectory();
  } catch {
    return false;
  }
}

/**
 * 检查是否为文件
 */
export function isFile(inputPath) {
  try {
    return statSync(inputPath).isFile();
  } catch {
    return false;
  }
}

/**
 * 生成 MCP 配置中的 Server 路径
 * 根据不同 IDE 的要求可能需要不同格式
 */
export function formatServerPathForConfig(serverPath, configType = 'claude') {
  const absolutePath = toAbsolutePath(serverPath);
  
  switch (configType) {
    case 'claude':
      // Claude Desktop 在所有平台上都接受正斜杠
      return toPosixPath(absolutePath);
    
    case 'codebuddy':
      // CodeBuddy 使用原生路径格式
      return absolutePath;
    
    default:
      return absolutePath;
  }
}

/**
 * 解析 Godot 项目路径
 * 检测是否为有效的 Godot 项目目录
 */
export function resolveGodotProjectPath(inputPath) {
  const absolutePath = toAbsolutePath(expandTilde(inputPath));
  
  // 检查 project.godot 文件
  const projectFile = join(absolutePath, 'project.godot');
  
  if (pathExists(projectFile)) {
    return {
      valid: true,
      path: absolutePath,
      projectFile: projectFile
    };
  }
  
  // 检查是否输入的是 project.godot 文件本身
  if (absolutePath.endsWith('project.godot') && pathExists(absolutePath)) {
    const projectDir = absolutePath.replace(/[/\\]project\.godot$/, '');
    return {
      valid: true,
      path: projectDir,
      projectFile: absolutePath
    };
  }
  
  return {
    valid: false,
    path: absolutePath,
    error: 'project.godot not found'
  };
}

/**
 * 获取 Godot 插件目标路径
 */
export function getGodotAddonPath(projectPath, addonName = 'godot_mcp') {
  return join(projectPath, 'addons', addonName);
}

/**
 * 获取平台信息摘要
 */
export function getPlatformInfo() {
  return {
    platform: PLATFORM,
    arch: arch(),
    isWindows: IS_WINDOWS,
    isMacOS: IS_MACOS,
    isLinux: IS_LINUX,
    homeDir: homedir(),
    pathSeparator: sep,
    paths: {
      claudeConfig: PlatformPaths.claudeConfig,
      mcpServerDir: PlatformPaths.mcpServerDir
    }
  };
}

/**
 * 打印平台信息（调试用）
 */
export function printPlatformInfo() {
  const info = getPlatformInfo();
  console.log('\n📋 平台信息');
  console.log('─'.repeat(40));
  console.log(`平台: ${info.platform}`);
  console.log(`主目录: ${info.homeDir}`);
  console.log(`路径分隔符: "${info.pathSeparator}"`);
  console.log(`Claude 配置: ${info.paths.claudeConfig}`);
  console.log(`MCP Server 目录: ${info.paths.mcpServerDir}`);
  console.log('');
}

// CLI 入口
if (process.argv[1] && process.argv[1].includes('path_utils')) {
  printPlatformInfo();
  
  // 测试路径转换
  const testPaths = [
    'C:\\Users\\test\\project',
    '/home/test/project',
    '~/project',
    './relative/path',
    '../parent/path'
  ];
  
  console.log('路径转换测试:');
  console.log('─'.repeat(40));
  for (const p of testPaths) {
    console.log(`原始: ${p}`);
    console.log(`  规范化: ${normalizePath(p)}`);
    console.log(`  POSIX: ${toPosixPath(p)}`);
    console.log(`  绝对路径: ${toAbsolutePath(expandTilde(p))}`);
    console.log('');
  }
}
