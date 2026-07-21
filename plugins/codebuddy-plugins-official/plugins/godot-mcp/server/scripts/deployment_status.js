/**
 * Godot MCP 部署状态管理
 * 
 * 提供部署状态的查询、更新和错误处理
 */

import { existsSync, readFileSync, writeFileSync, unlinkSync } from 'fs';
import { join, dirname } from 'path';
import { platform, homedir } from 'os';
import { 
  normalizePath, 
  expandTilde, 
  getPlatformInfo, 
  PLATFORM, 
  IS_WINDOWS, 
  PlatformPaths 
} from './path_utils.js';

// 部署状态枚举
export const DeploymentStatus = {
  NOT_DEPLOYED: 'not_deployed',
  DEPLOYED: 'deployed',
  CONFIG_ERROR: 'config_error',
  SERVER_ERROR: 'server_error',
  PLUGIN_NOT_ENABLED: 'plugin_not_enabled',
  CONNECTION_ERROR: 'connection_error'
};

// 状态描述
export const StatusMessages = {
  [DeploymentStatus.NOT_DEPLOYED]: {
    title: '未部署',
    description: 'Godot MCP 尚未配置',
    action: '运行 npm run deploy 进行部署'
  },
  [DeploymentStatus.DEPLOYED]: {
    title: '已部署',
    description: 'Godot MCP 已正确配置',
    action: null
  },
  [DeploymentStatus.CONFIG_ERROR]: {
    title: '配置错误',
    description: 'MCP 配置文件存在问题',
    action: '检查配置文件或重新部署'
  },
  [DeploymentStatus.SERVER_ERROR]: {
    title: 'Server 错误',
    description: 'MCP Server 构建产物缺失或损坏',
    action: '重新运行 npm run build'
  },
  [DeploymentStatus.PLUGIN_NOT_ENABLED]: {
    title: '插件未启用',
    description: 'Godot 编辑器中未启用 MCP 插件',
    action: '在 Godot 中: Project > Project Settings > Plugins > 启用 "Godot MCP"'
  },
  [DeploymentStatus.CONNECTION_ERROR]: {
    title: '连接失败',
    description: '无法连接到 Godot WebSocket 服务器',
    action: '请确保 Godot 编辑器已打开且 MCP 插件已启用'
  }
};

// 获取默认配置路径
export function getDefaultConfigPath() {
  return PlatformPaths.claudeConfig;
}

// 部署状态管理器
export class DeploymentStatusManager {
  constructor(configPath = null) {
    this.configPath = configPath || getDefaultConfigPath();
  }
  
  /**
   * 获取当前部署状态
   */
  getStatus() {
    const result = {
      status: DeploymentStatus.NOT_DEPLOYED,
      details: {},
      message: null
    };
    
    // 检查配置文件
    if (!existsSync(this.configPath)) {
      result.status = DeploymentStatus.NOT_DEPLOYED;
      result.details.configExists = false;
      return result;
    }
    
    result.details.configExists = true;
    result.details.configPath = this.configPath;
    
    // 读取配置
    let config;
    try {
      config = JSON.parse(readFileSync(this.configPath, 'utf-8'));
    } catch (error) {
      result.status = DeploymentStatus.CONFIG_ERROR;
      result.message = `配置文件解析失败: ${error.message}`;
      return result;
    }
    
    // 检查 godot-mcp 配置
    if (!config.mcpServers || !config.mcpServers['godot-mcp']) {
      result.status = DeploymentStatus.NOT_DEPLOYED;
      result.details.mcpConfigured = false;
      return result;
    }
    
    result.details.mcpConfigured = true;
    const godotConfig = config.mcpServers['godot-mcp'];
    
    // 检查 server 路径
    const serverPath = godotConfig.args?.[0];
    if (!serverPath) {
      result.status = DeploymentStatus.CONFIG_ERROR;
      result.message = '配置中缺少 server 路径';
      return result;
    }
    
    result.details.serverPath = serverPath;
    
    if (!existsSync(serverPath)) {
      result.status = DeploymentStatus.SERVER_ERROR;
      result.message = `Server 文件不存在: ${serverPath}`;
      return result;
    }
    
    result.details.serverExists = true;
    result.status = DeploymentStatus.DEPLOYED;
    
    return result;
  }
  
  /**
   * 测试 WebSocket 连接
   */
  async testConnection(url = 'ws://localhost:9080', timeout = 5000) {
    return new Promise((resolve) => {
      try {
        // 动态导入 ws 模块
        import('ws').then(({ default: WebSocket }) => {
          const ws = new WebSocket(url, { protocol: 'json' });
          
          const timer = setTimeout(() => {
            ws.terminate();
            resolve({
              connected: false,
              error: 'Connection timeout'
            });
          }, timeout);
          
          ws.on('open', () => {
            clearTimeout(timer);
            ws.close();
            resolve({ connected: true });
          });
          
          ws.on('error', (error) => {
            clearTimeout(timer);
            resolve({
              connected: false,
              error: error.message
            });
          });
        }).catch((error) => {
          resolve({
            connected: false,
            error: `WebSocket module not available: ${error.message}`
          });
        });
      } catch (error) {
        resolve({
          connected: false,
          error: error.message
        });
      }
    });
  }
  
  /**
   * 获取完整诊断信息
   */
  async diagnose() {
    const status = this.getStatus();
    const diagnosis = {
      ...status,
      connection: null,
      recommendations: []
    };
    
    // 如果配置正确，测试连接
    if (status.status === DeploymentStatus.DEPLOYED) {
      const connectionTest = await this.testConnection();
      diagnosis.connection = connectionTest;
      
      if (!connectionTest.connected) {
        diagnosis.status = DeploymentStatus.CONNECTION_ERROR;
        diagnosis.recommendations.push(StatusMessages[DeploymentStatus.CONNECTION_ERROR].action);
      }
    } else {
      const statusInfo = StatusMessages[status.status];
      if (statusInfo && statusInfo.action) {
        diagnosis.recommendations.push(statusInfo.action);
      }
    }
    
    return diagnosis;
  }
  
  /**
   * 移除 godot-mcp 配置（卸载）
   */
  uninstall() {
    if (!existsSync(this.configPath)) {
      return { success: true, message: '配置文件不存在' };
    }
    
    try {
      const config = JSON.parse(readFileSync(this.configPath, 'utf-8'));
      
      if (config.mcpServers && config.mcpServers['godot-mcp']) {
        delete config.mcpServers['godot-mcp'];
        writeFileSync(this.configPath, JSON.stringify(config, null, 2), 'utf-8');
        return { success: true, message: 'godot-mcp 配置已移除' };
      }
      
      return { success: true, message: 'godot-mcp 配置不存在' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  
  /**
   * 获取用户友好的状态报告
   */
  getStatusReport() {
    const status = this.getStatus();
    const info = StatusMessages[status.status];
    const platformInfo = getPlatformInfo();
    
    let report = `\n📊 Godot MCP 部署状态\n`;
    report += `${'─'.repeat(40)}\n`;
    report += `平台: ${platformInfo.platform} (${platformInfo.arch})\n`;
    report += `状态: ${info.title}\n`;
    report += `描述: ${info.description}\n`;
    
    if (status.details.configPath) {
      report += `配置路径: ${normalizePath(status.details.configPath)}\n`;
    }
    
    if (status.details.serverPath) {
      report += `Server 路径: ${normalizePath(status.details.serverPath)}\n`;
    }
    
    if (status.message) {
      report += `详情: ${status.message}\n`;
    }
    
    if (info.action) {
      report += `\n💡 建议操作: ${info.action}\n`;
    }
    
    return report;
  }
}

// CLI 入口
async function main() {
  const manager = new DeploymentStatusManager();
  const args = process.argv.slice(2);
  
  if (args.includes('--diagnose')) {
    console.log('正在诊断...\n');
    const diagnosis = await manager.diagnose();
    console.log(JSON.stringify(diagnosis, null, 2));
  } else if (args.includes('--uninstall')) {
    const result = manager.uninstall();
    console.log(result.success ? `✓ ${result.message}` : `✗ ${result.error}`);
  } else {
    console.log(manager.getStatusReport());
  }
}

// 如果直接运行此文件
if (process.argv[1] && process.argv[1].includes('deployment_status')) {
  main().catch(console.error);
}
