/**
 * 云知知识库文件夹同步脚本
 * 支持将本地文件夹增量同步到云知知识库
 *
 * 使用方式:
 *   npx ts-node sync-folder.ts --local ./docs --entry-id <parent_entry_id> [--dry-run]
 */

import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

// ============ 类型定义 ============

interface SyncConfig {
  localPath: string;
  parentEntryId: string;
  spaceId?: string;
  dryRun: boolean;
  syncStateFile: string;
  ignoredPatterns: string[];
  supportedExtensions: string[];
}

interface SyncState {
  version: string;
  lastSyncAt: string;
  files: Record<string, FileState>;
}

interface FileState {
  localPath: string;
  entryId: string;
  fileId?: string;
  contentHash: string;
  lastModified: string;
  syncedAt: string;
}

interface LocalFile {
  relativePath: string;
  absolutePath: string;
  isDirectory: boolean;
  contentHash?: string;
  lastModified: Date;
}

interface SyncAction {
  type: 'create_folder' | 'create_file' | 'update_file' | 'delete';
  localPath: string;
  entryId?: string;
  fileId?: string;
  reason: string;
}

interface YunzhiEntry {
  id: string;
  name: string;
  entry_type: 'page' | 'folder' | 'file';
  target_id?: string;
  has_children: boolean;
}

// ============ MCP 调用封装 ============

/**
 * 云知 MCP 调用包装器
 * 实际使用时通过 AI 助手的 MCP 调用能力执行
 */
class YunzhiMCPClient {
  /**
   * 生成 MCP 调用参数（供 AI 助手使用）
   */
  static listChildren(parentId: string): { tool: string; args: object } {
    return {
      tool: '云知.entry_list_children',
      args: { parent_id: parentId, limit: 100 }
    };
  }

  static describeEntry(entryId: string): { tool: string; args: object } {
    return {
      tool: '云知.entry_describe_entry',
      args: { entry_id: entryId }
    };
  }

  static createEntry(params: {
    parentEntryId: string;
    name: string;
    entryType: 'page' | 'folder';
  }): { tool: string; args: object } {
    return {
      tool: '云知.entry_create_entry',
      args: {
        parent_entry_id: params.parentEntryId,
        name: params.name,
        entry_type: params.entryType
      }
    };
  }

  static applyUpload(params: {
    parentEntryId: string;
    name: string;
    mimeType: string;
    size: number;
    fileId?: string;
  }): { tool: string; args: object } {
    return {
      tool: '云知.file_apply_upload',
      args: {
        parent_entry_id: params.parentEntryId,
        name: params.name,
        mime_type: params.mimeType,
        size: params.size,
        file_id: params.fileId,
        upload_type: 'PRE_SIGNED_URL'
      }
    };
  }

  static commitUpload(sessionId: string): { tool: string; args: object } {
    return {
      tool: '云知.file_commit_upload',
      args: { session_id: sessionId }
    };
  }

  static importContent(params: {
    parentId: string;
    name: string;
    content: string;
    contentType: 'markdown' | 'html';
  }): { tool: string; args: object } {
    return {
      tool: '云知.entry_import_content',
      args: {
        parent_id: params.parentId,
        name: params.name,
        content: params.content,
        content_type: params.contentType
      }
    };
  }
}

// ============ 工具函数 ============

/**
 * 计算文件内容 hash
 */
function computeFileHash(filePath: string): string {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('md5').update(content).digest('hex');
}

/**
 * 获取 MIME 类型
 */
function getMimeType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    '.md': 'text/markdown',
    '.markdown': 'text/markdown',
    '.txt': 'text/plain',
    '.json': 'application/json',
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.zip': 'application/zip'
  };
  return mimeTypes[ext] || 'application/octet-stream';
}

/**
 * 检查路径是否匹配忽略模式
 */
function shouldIgnore(relativePath: string, patterns: string[]): boolean {
  for (const pattern of patterns) {
    if (pattern.startsWith('*')) {
      // 扩展名匹配
      if (relativePath.endsWith(pattern.slice(1))) return true;
    } else if (pattern.endsWith('/')) {
      // 目录匹配
      if (relativePath.includes(pattern) || relativePath.startsWith(pattern)) return true;
    } else {
      // 精确匹配或包含匹配
      if (relativePath === pattern || relativePath.includes(pattern)) return true;
    }
  }
  return false;
}

/**
 * 递归扫描本地目录
 */
function scanLocalDirectory(
  basePath: string,
  config: SyncConfig,
  currentPath: string = ''
): LocalFile[] {
  const files: LocalFile[] = [];
  const absolutePath = path.join(basePath, currentPath);

  if (!fs.existsSync(absolutePath)) {
    return files;
  }

  const entries = fs.readdirSync(absolutePath, { withFileTypes: true });

  for (const entry of entries) {
    const relativePath = path.join(currentPath, entry.name);

    // 检查是否应该忽略
    if (shouldIgnore(relativePath, config.ignoredPatterns)) {
      continue;
    }

    const entryAbsolutePath = path.join(basePath, relativePath);
    const stats = fs.statSync(entryAbsolutePath);

    if (entry.isDirectory()) {
      files.push({
        relativePath,
        absolutePath: entryAbsolutePath,
        isDirectory: true,
        lastModified: stats.mtime
      });

      // 递归扫描子目录
      files.push(...scanLocalDirectory(basePath, config, relativePath));
    } else {
      // 检查是否是支持的文件类型
      const ext = path.extname(entry.name).toLowerCase();
      if (config.supportedExtensions.length > 0 &&
          !config.supportedExtensions.includes(ext)) {
        continue;
      }

      files.push({
        relativePath,
        absolutePath: entryAbsolutePath,
        isDirectory: false,
        contentHash: computeFileHash(entryAbsolutePath),
        lastModified: stats.mtime
      });
    }
  }

  return files;
}

/**
 * 加载同步状态
 */
function loadSyncState(stateFile: string): SyncState {
  if (fs.existsSync(stateFile)) {
    const content = fs.readFileSync(stateFile, 'utf-8');
    return JSON.parse(content);
  }
  return {
    version: '1.0.0',
    lastSyncAt: '',
    files: {}
  };
}

/**
 * 保存同步状态
 */
function saveSyncState(stateFile: string, state: SyncState): void {
  fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
}

// ============ 同步逻辑 ============

/**
 * 计算需要执行的同步操作
 */
function computeSyncActions(
  localFiles: LocalFile[],
  syncState: SyncState,
  remoteEntries: Map<string, YunzhiEntry>
): SyncAction[] {
  const actions: SyncAction[] = [];

  // 按目录层级排序，确保父目录先创建
  localFiles.sort((a, b) => {
    const depthA = a.relativePath.split(path.sep).length;
    const depthB = b.relativePath.split(path.sep).length;
    if (depthA !== depthB) return depthA - depthB;
    if (a.isDirectory !== b.isDirectory) return a.isDirectory ? -1 : 1;
    return a.relativePath.localeCompare(b.relativePath);
  });

  for (const file of localFiles) {
    const existingState = syncState.files[file.relativePath];
    const remoteName = path.basename(file.relativePath);
    const remoteEntry = remoteEntries.get(remoteName);

    if (file.isDirectory) {
      if (!existingState && !remoteEntry) {
        actions.push({
          type: 'create_folder',
          localPath: file.relativePath,
          reason: '新目录'
        });
      }
    } else {
      if (!existingState) {
        // 新文件
        actions.push({
          type: 'create_file',
          localPath: file.relativePath,
          reason: '新文件'
        });
      } else if (existingState.contentHash !== file.contentHash) {
        // 文件内容变更
        actions.push({
          type: 'update_file',
          localPath: file.relativePath,
          entryId: existingState.entryId,
          fileId: existingState.fileId,
          reason: `内容变更 (hash: ${existingState.contentHash.slice(0, 8)} -> ${file.contentHash?.slice(0, 8)})`
        });
      }
    }
  }

  return actions;
}

/**
 * 生成同步操作的 MCP 调用序列
 */
function generateMCPCalls(
  actions: SyncAction[],
  config: SyncConfig,
  localFiles: LocalFile[]
): Array<{ action: SyncAction; mcpCall: { tool: string; args: object }; note: string }> {
  const calls: Array<{ action: SyncAction; mcpCall: { tool: string; args: object }; note: string }> = [];

  // 记录目录路径到 entry_id 的映射（需要在实际执行时更新）
  const pathToEntryId: Record<string, string> = {
    '': config.parentEntryId
  };

  for (const action of actions) {
    const parentPath = path.dirname(action.localPath);
    const parentEntryId = pathToEntryId[parentPath] || config.parentEntryId;
    const name = path.basename(action.localPath);

    switch (action.type) {
      case 'create_folder':
        calls.push({
          action,
          mcpCall: YunzhiMCPClient.createEntry({
            parentEntryId,
            name,
            entryType: 'folder'
          }),
          note: `创建目录: ${action.localPath}`
        });
        // 占位，实际 entry_id 需要从返回值获取
        pathToEntryId[action.localPath] = `<待获取:${action.localPath}>`;
        break;

      case 'create_file':
        const localFile = localFiles.find(f => f.relativePath === action.localPath);
        if (localFile) {
          const stats = fs.statSync(localFile.absolutePath);
          const isMarkdown = ['.md', '.markdown'].includes(
            path.extname(action.localPath).toLowerCase()
          );

          if (isMarkdown) {
            // Markdown 优先使用文件上传方式（便于后续版本更新）
            calls.push({
              action,
              mcpCall: YunzhiMCPClient.applyUpload({
                parentEntryId,
                name,
                mimeType: 'text/markdown',
                size: stats.size
              }),
              note: `上传 Markdown 文件: ${action.localPath} (第1步: 申请上传)`
            });
          } else {
            calls.push({
              action,
              mcpCall: YunzhiMCPClient.applyUpload({
                parentEntryId,
                name,
                mimeType: getMimeType(action.localPath),
                size: stats.size
              }),
              note: `上传文件: ${action.localPath} (第1步: 申请上传)`
            });
          }
        }
        break;

      case 'update_file':
        const updateFile = localFiles.find(f => f.relativePath === action.localPath);
        if (updateFile && action.fileId) {
          const stats = fs.statSync(updateFile.absolutePath);
          calls.push({
            action,
            mcpCall: YunzhiMCPClient.applyUpload({
              parentEntryId: action.entryId!, // 更新时使用当前文件的 entry_id
              name: path.basename(action.localPath),
              mimeType: getMimeType(action.localPath),
              size: stats.size,
              fileId: action.fileId
            }),
            note: `更新文件: ${action.localPath} (第1步: 申请上传, file_id=${action.fileId})`
          });
        }
        break;
    }
  }

  return calls;
}

// ============ 主入口 ============

/**
 * 文件夹同步主函数
 */
export async function syncFolder(config: SyncConfig): Promise<{
  actions: SyncAction[];
  mcpCalls: Array<{ action: SyncAction; mcpCall: { tool: string; args: object }; note: string }>;
  summary: string;
}> {
  console.log('📁 开始扫描本地目录:', config.localPath);

  // 1. 扫描本地文件
  const localFiles = scanLocalDirectory(config.localPath, config);
  console.log(`   找到 ${localFiles.length} 个文件/目录`);

  // 2. 加载同步状态
  const syncState = loadSyncState(config.syncStateFile);
  console.log(`   同步状态文件: ${config.syncStateFile}`);
  console.log(`   上次同步: ${syncState.lastSyncAt || '从未同步'}`);

  // 3. 计算同步操作
  const remoteEntries = new Map<string, YunzhiEntry>();
  // 注意：实际执行时需要先调用 list_children 获取远程条目
  const actions = computeSyncActions(localFiles, syncState, remoteEntries);

  console.log(`\n📋 同步计划:`);
  console.log(`   创建目录: ${actions.filter(a => a.type === 'create_folder').length}`);
  console.log(`   新建文件: ${actions.filter(a => a.type === 'create_file').length}`);
  console.log(`   更新文件: ${actions.filter(a => a.type === 'update_file').length}`);

  // 4. 生成 MCP 调用
  const mcpCalls = generateMCPCalls(actions, config, localFiles);

  // 5. 生成摘要
  const summary = `
同步摘要
========
本地目录: ${config.localPath}
目标节点: ${config.parentEntryId}
文件总数: ${localFiles.length}
同步操作: ${actions.length}

操作详情:
${actions.map(a => `  - [${a.type}] ${a.localPath} (${a.reason})`).join('\n')}

MCP 调用序列:
${mcpCalls.map((c, i) => `  ${i + 1}. ${c.note}`).join('\n')}
  `;

  if (config.dryRun) {
    console.log('\n🔍 Dry Run 模式，不执行实际操作');
    console.log(summary);
  }

  return { actions, mcpCalls, summary };
}

// ============ CLI ============

function parseArgs(): SyncConfig {
  const args = process.argv.slice(2);
  const config: SyncConfig = {
    localPath: '',
    parentEntryId: '',
    dryRun: false,
    syncStateFile: '.yunzhi-sync-state.json',
    ignoredPatterns: [
      'node_modules/',
      '.git/',
      '.DS_Store',
      '*.log',
      '.yunzhi-sync-state.json'
    ],
    supportedExtensions: ['.md', '.markdown', '.txt', '.json', '.pdf', '.doc', '.docx']
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--local':
        config.localPath = args[++i];
        break;
      case '--entry-id':
        config.parentEntryId = args[++i];
        break;
      case '--space-id':
        config.spaceId = args[++i];
        break;
      case '--dry-run':
        config.dryRun = true;
        break;
      case '--state-file':
        config.syncStateFile = args[++i];
        break;
    }
  }

  if (!config.localPath || !config.parentEntryId) {
    console.error('用法: npx ts-node sync-folder.ts --local <路径> --entry-id <entry_id> [--dry-run]');
    process.exit(1);
  }

  return config;
}

// 如果直接运行脚本
if (require.main === module) {
  const config = parseArgs();
  syncFolder(config).catch(console.error);
}

export { SyncConfig, SyncState, SyncAction, LocalFile, YunzhiMCPClient };
