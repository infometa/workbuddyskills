/**
 * Godot MCP 一键部署脚本
 * 
 * 功能:
 *   1. 检测 Node.js 环境
 *   2. 构建 MCP Server
 *   3. 生成 MCP 配置
 *   4. 复制 Godot 插件到目标项目（可选）
 * 
 * 用法:
 *   node scripts/deploy.js [options]
 * 
 * 选项:
 *   --config-path <path>    MCP 配置文件路径
 *   --godot-project <path>  Godot 项目路径（用于复制插件）
 *   --skip-build            跳过构建步骤
 *   --dry-run               仅显示将要执行的操作
 *   --platform-info         显示平台信息
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync, copyFileSync, writeFileSync, readFileSync, readdirSync, statSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import { platform, homedir } from 'os';
import {
  getPlatformPath,
  normalizePath,
  toPosixPath,
  toAbsolutePath,
  expandTilde,
  resolveGodotProjectPath,
  getGodotAddonPath,
  formatServerPathForConfig,
  getPlatformInfo,
  printPlatformInfo,
  IS_WINDOWS
} from './path_utils.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = resolve(__dirname, '..');
const SERVER_DIR = ROOT_DIR; // server 目录本身
const ADDON_DIR = resolve(ROOT_DIR, '..', 'addons', 'godot_mcp');

// 部署状态
const DeployStatus = {
  NOT_DEPLOYED: 'not_deployed',
  DEPLOYED: 'deployed',
  CONFIG_ERROR: 'config_error',
  BUILD_ERROR: 'build_error'
};

// 获取默认 MCP 配置路径（使用 path_utils）
function getDefaultConfigPath() {
  return getPlatformPath('claudeConfig');
}

// 检测 Node.js 版本
function checkNodeVersion() {
  try {
    const version = execSync('node --version', { encoding: 'utf-8' }).trim();
    const major = parseInt(version.replace('v', '').split('.')[0], 10);
    
    if (major < 18) {
      return { success: false, version, error: 'Node.js >= 18 is required' };
    }
    
    return { success: true, version };
  } catch (error) {
    return { success: false, error: 'Node.js not found' };
  }
}

// 检测 npm
function checkNpm() {
  try {
    const version = execSync('npm --version', { encoding: 'utf-8' }).trim();
    return { success: true, version };
  } catch (error) {
    return { success: false, error: 'npm not found' };
  }
}

// 构建 MCP Server
function buildServer(dryRun = false) {
  console.log('\n📦 构建 MCP Server...');
  
  if (dryRun) {
    console.log('  [DRY RUN] 将执行: npm install && npm run build');
    return { success: true };
  }
  
  try {
    // 安装依赖
    console.log('  安装依赖...');
    execSync('npm install', { cwd: SERVER_DIR, stdio: 'inherit' });
    
    // 构建
    console.log('  编译 TypeScript...');
    execSync('npm run build', { cwd: SERVER_DIR, stdio: 'inherit' });
    
    // 验证构建产物
    const distPath = join(SERVER_DIR, 'dist', 'index.js');
    if (!existsSync(distPath)) {
      return { success: false, error: 'Build output not found' };
    }
    
    return { success: true, outputPath: distPath };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// 生成 MCP 配置
function generateMcpConfig(serverPath, configType = 'claude') {
  // 使用跨平台路径格式化
  const formattedPath = formatServerPathForConfig(serverPath, configType);
  
  return {
    "godot-mcp": {
      "command": "node",
      "args": [formattedPath],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  };
}

// 读取现有配置
function readExistingConfig(configPath) {
  try {
    if (existsSync(configPath)) {
      const content = readFileSync(configPath, 'utf-8');
      return JSON.parse(content);
    }
  } catch (error) {
    console.warn(`  ⚠ 无法读取现有配置: ${error.message}`);
  }
  return { mcpServers: {} };
}

// 写入 MCP 配置
function writeMcpConfig(configPath, dryRun = false, configType = 'claude') {
  console.log('\n⚙️  配置 MCP...');
  
  const serverPath = join(SERVER_DIR, 'dist', 'index.js');
  const mcpConfig = generateMcpConfig(serverPath, configType);
  
  console.log(`  配置文件路径: ${normalizePath(configPath)}`);
  console.log(`  Server 路径: ${normalizePath(serverPath)}`);
  console.log(`  配置格式: ${configType} (路径使用 ${configType === 'claude' ? 'POSIX' : '原生'} 风格)`);
  
  if (dryRun) {
    console.log('  [DRY RUN] 将写入配置:');
    console.log(JSON.stringify(mcpConfig, null, 2));
    return { success: true };
  }
  
  try {
    // 确保目录存在
    const configDir = dirname(configPath);
    if (!existsSync(configDir)) {
      mkdirSync(configDir, { recursive: true });
    }
    
    // 读取现有配置并合并
    const existingConfig = readExistingConfig(configPath);
    existingConfig.mcpServers = existingConfig.mcpServers || {};
    existingConfig.mcpServers['godot-mcp'] = mcpConfig['godot-mcp'];
    
    // 写入配置
    writeFileSync(configPath, JSON.stringify(existingConfig, null, 2), 'utf-8');
    
    return { success: true, config: existingConfig };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// 递归复制目录
function copyDirRecursive(src, dest) {
  if (!existsSync(dest)) {
    mkdirSync(dest, { recursive: true });
  }
  
  const entries = readdirSync(src);
  for (const entry of entries) {
    const srcPath = join(src, entry);
    const destPath = join(dest, entry);
    
    const stat = statSync(srcPath);
    if (stat.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

// 复制 Godot 插件到项目
function copyAddonToProject(projectPath, dryRun = false) {
  console.log('\n📁 复制 Godot 插件...');
  
  // 使用跨平台路径工具
  const destDir = getGodotAddonPath(projectPath);
  console.log(`  源目录: ${normalizePath(ADDON_DIR)}`);
  console.log(`  目标目录: ${normalizePath(destDir)}`);
  
  if (dryRun) {
    console.log('  [DRY RUN] 将复制插件文件');
    return { success: true };
  }
  
  try {
    copyDirRecursive(ADDON_DIR, destDir);
    return { success: true, destPath: destDir };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// 检查 Godot 项目（使用跨平台路径工具）
function checkGodotProject(projectPath) {
  const result = resolveGodotProjectPath(projectPath);
  return result.valid;
}

// 获取部署状态
function getDeployStatus(configPath) {
  try {
    if (!existsSync(configPath)) {
      return DeployStatus.NOT_DEPLOYED;
    }
    
    const config = JSON.parse(readFileSync(configPath, 'utf-8'));
    if (!config.mcpServers || !config.mcpServers['godot-mcp']) {
      return DeployStatus.NOT_DEPLOYED;
    }
    
    const serverPath = config.mcpServers['godot-mcp'].args?.[0];
    if (!serverPath || !existsSync(serverPath)) {
      return DeployStatus.CONFIG_ERROR;
    }
    
    return DeployStatus.DEPLOYED;
  } catch (error) {
    return DeployStatus.CONFIG_ERROR;
  }
}

// 解析命令行参数
function parseArgs(args) {
  const options = {
    configPath: getDefaultConfigPath(),
    godotProject: null,
    skipBuild: false,
    dryRun: false,
    help: false,
    platformInfo: false
  };
  
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--config-path':
        options.configPath = expandTilde(args[++i]);
        break;
      case '--godot-project':
        options.godotProject = expandTilde(args[++i]);
        break;
      case '--skip-build':
        options.skipBuild = true;
        break;
      case '--dry-run':
        options.dryRun = true;
        break;
      case '--platform-info':
        options.platformInfo = true;
        break;
      case '--help':
      case '-h':
        options.help = true;
        break;
    }
  }
  
  return options;
}

// 显示帮助
function showHelp() {
  const info = getPlatformInfo();
  console.log(`
Godot MCP 一键部署工具

用法: node scripts/deploy.js [options]

选项:
  --config-path <path>    MCP 配置文件路径
                          默认: ${info.paths.claudeConfig}
  --godot-project <path>  Godot 项目路径（用于复制插件）
                          支持 ~ 展开
  --skip-build            跳过构建步骤
  --dry-run               仅显示将要执行的操作
  --platform-info         显示平台信息
  -h, --help              显示帮助

示例:
  node scripts/deploy.js
  node scripts/deploy.js --godot-project ~/Projects/MyGame
  node scripts/deploy.js --godot-project "C:\\Games\\MyProject"
  node scripts/deploy.js --dry-run

当前平台: ${info.platform}
`);
}

// 主函数
async function main() {
  const options = parseArgs(process.argv.slice(2));
  
  if (options.help) {
    showHelp();
    return;
  }
  
  if (options.platformInfo) {
    printPlatformInfo();
    return;
  }
  
  console.log('========================================');
  console.log('  Godot MCP 一键部署');
  console.log('========================================');
  
  // 显示平台信息
  const platformInfo = getPlatformInfo();
  console.log(`\n📋 平台: ${platformInfo.platform} | 主目录: ${platformInfo.homeDir}`);
  
  if (options.dryRun) {
    console.log('\n⚠️  DRY RUN 模式 - 不会执行实际操作\n');
  }
  
  // 1. 检测环境
  console.log('\n🔍 检测环境...');
  
  const nodeCheck = checkNodeVersion();
  if (!nodeCheck.success) {
    console.error(`  ✗ Node.js: ${nodeCheck.error}`);
    console.error('\n请安装 Node.js 18 或更高版本: https://nodejs.org/');
    process.exit(1);
  }
  console.log(`  ✓ Node.js: ${nodeCheck.version}`);
  
  const npmCheck = checkNpm();
  if (!npmCheck.success) {
    console.error(`  ✗ npm: ${npmCheck.error}`);
    process.exit(1);
  }
  console.log(`  ✓ npm: ${npmCheck.version}`);
  
  // 2. 构建 Server
  if (!options.skipBuild) {
    const buildResult = buildServer(options.dryRun);
    if (!buildResult.success) {
      console.error(`\n✗ 构建失败: ${buildResult.error}`);
      process.exit(1);
    }
    console.log('  ✓ 构建成功');
  } else {
    console.log('\n⏭️  跳过构建步骤');
  }
  
  // 3. 写入 MCP 配置
  const configResult = writeMcpConfig(options.configPath, options.dryRun);
  if (!configResult.success) {
    console.error(`\n✗ 配置写入失败: ${configResult.error}`);
    process.exit(1);
  }
  console.log('  ✓ MCP 配置已更新');
  
  // 4. 复制 Godot 插件（可选）
  if (options.godotProject) {
    // 使用跨平台路径解析
    const projectResult = resolveGodotProjectPath(options.godotProject);
    if (!projectResult.valid) {
      console.error(`\n✗ 无效的 Godot 项目路径: ${normalizePath(options.godotProject)}`);
      console.error(`  错误: ${projectResult.error}`);
      console.error('  请确保路径包含 project.godot 文件');
      process.exit(1);
    }
    
    console.log(`  项目路径: ${normalizePath(projectResult.path)}`);
    
    const copyResult = copyAddonToProject(projectResult.path, options.dryRun);
    if (!copyResult.success) {
      console.error(`\n✗ 插件复制失败: ${copyResult.error}`);
      process.exit(1);
    }
    console.log('  ✓ 插件已复制');
  }
  
  // 5. 完成
  console.log('\n========================================');
  console.log('  ✓ 部署完成!');
  console.log('========================================');
  
  console.log('\n📋 后续步骤:');
  console.log('  1. 重启 Claude Desktop 以加载新配置');
  console.log('  2. 在 Godot 编辑器中启用 Godot MCP 插件:');
  console.log('     Project > Project Settings > Plugins > 启用 "Godot MCP"');
  console.log('  3. 确认插件 UI 面板显示 "Server Running"');
  console.log('  4. 在 Claude 中使用 Godot MCP 工具\n');
  
  if (!options.godotProject) {
    console.log('💡 提示: 使用 --godot-project <path> 可自动复制插件到您的 Godot 项目');
    console.log(`   示例: npm run deploy -- --godot-project ${IS_WINDOWS ? 'C:\\\\Games\\\\MyProject' : '~/Projects/MyGame'}\n`);
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});