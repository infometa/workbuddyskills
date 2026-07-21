/**
 * Godot MCP 接口回归测试脚本
 * 
 * 用法: 
 *   1. 确保 Godot 编辑器已启动并启用 MCP 插件
 *   2. 运行: node test/test_commands.js
 * 
 * 测试覆盖: 所有 MCP 工具和命令
 */

import WebSocket from 'ws';

const WS_URL = 'ws://localhost:9080';
const TIMEOUT = 10000;

let ws = null;
let commandId = 0;
let pendingCommands = new Map();
let testResults = [];

// 测试用例定义
const TEST_CASES = [
  // ============ Node Commands ============
  {
    name: 'list_nodes',
    command: { type: 'list_nodes', params: { parent_path: '/root' } },
    validate: (result) => result.children !== undefined
  },
  {
    name: 'get_node_properties',
    command: { type: 'get_node_properties', params: { node_path: '/root' } },
    validate: (result) => result.properties !== undefined
  },
  
  // ============ Scene Commands ============
  {
    name: 'get_current_scene',
    command: { type: 'get_current_scene', params: {} },
    validate: (result) => result.scene_path !== undefined
  },
  {
    name: 'get_current_scene_structure',
    command: { type: 'get_current_scene_structure', params: {} },
    validate: (result) => result.scene_path !== undefined || result.structure !== undefined
  },
  
  // ============ Script Commands ============
  {
    name: 'get_current_script',
    command: { type: 'get_current_script', params: {} },
    validate: (result) => result.script_found !== undefined
  },
  
  // ============ Project Commands ============
  {
    name: 'get_project_info',
    command: { type: 'get_project_info', params: {} },
    validate: (result) => result.project_name !== undefined && result.godot_version !== undefined
  },
  {
    name: 'get_project_settings',
    command: { type: 'get_project_settings', params: {} },
    validate: (result) => result.project_name !== undefined
  },
  {
    name: 'get_project_structure',
    command: { type: 'get_project_structure', params: {} },
    validate: (result) => result.directories !== undefined
  },
  {
    name: 'list_project_files (scenes)',
    command: { type: 'list_project_files', params: { extensions: ['.tscn'] } },
    validate: (result) => result.files !== undefined
  },
  {
    name: 'list_project_files (scripts)',
    command: { type: 'list_project_files', params: { extensions: ['.gd'] } },
    validate: (result) => result.files !== undefined
  },
  {
    name: 'list_project_resources',
    command: { type: 'list_project_resources', params: {} },
    validate: (result) => result.scenes !== undefined && result.scripts !== undefined
  },
  
  // ============ Editor Commands ============
  {
    name: 'get_editor_state',
    command: { type: 'get_editor_state', params: {} },
    validate: (result) => result.is_playing !== undefined
  },
  {
    name: 'get_selected_node',
    command: { type: 'get_selected_node', params: {} },
    validate: (result) => result.selected !== undefined || result.name !== undefined
  },
];

// 创建场景、节点、脚本的写入测试（可选，需要手动清理）
const WRITE_TEST_CASES = [
  {
    name: 'create_scene',
    command: { type: 'create_scene', params: { path: 'res://test_scene_temp.tscn', root_node_type: 'Node2D' } },
    validate: (result) => result.scene_path !== undefined,
    cleanup: true
  },
  {
    name: 'create_node',
    command: { type: 'create_node', params: { parent_path: '/root', node_type: 'Node2D', node_name: 'TestNode_Temp' } },
    validate: (result) => result.node_path !== undefined,
    cleanup: true
  },
];

// 连接到 Godot WebSocket
function connect() {
  return new Promise((resolve, reject) => {
    console.log(`Connecting to ${WS_URL}...`);
    ws = new WebSocket(WS_URL, { protocol: 'json' });
    
    const timeout = setTimeout(() => {
      reject(new Error('Connection timeout'));
    }, TIMEOUT);
    
    ws.on('open', () => {
      clearTimeout(timeout);
      console.log('✓ Connected to Godot WebSocket server\n');
      resolve();
    });
    
    ws.on('message', (data) => {
      try {
        const response = JSON.parse(data.toString());
        if (response.commandId && pendingCommands.has(response.commandId)) {
          const { resolve, reject } = pendingCommands.get(response.commandId);
          pendingCommands.delete(response.commandId);
          
          if (response.status === 'success') {
            resolve(response.result);
          } else {
            reject(new Error(response.message || 'Command failed'));
          }
        }
      } catch (error) {
        console.error('Error parsing response:', error);
      }
    });
    
    ws.on('error', (error) => {
      clearTimeout(timeout);
      reject(error);
    });
    
    ws.on('close', () => {
      console.log('\nConnection closed');
    });
  });
}

// 发送命令并等待响应
function sendCommand(type, params) {
  return new Promise((resolve, reject) => {
    const id = `test_${commandId++}`;
    const command = {
      type,
      params,
      commandId: id
    };
    
    const timeout = setTimeout(() => {
      pendingCommands.delete(id);
      reject(new Error(`Command timeout: ${type}`));
    }, TIMEOUT);
    
    pendingCommands.set(id, {
      resolve: (result) => {
        clearTimeout(timeout);
        resolve(result);
      },
      reject: (error) => {
        clearTimeout(timeout);
        reject(error);
      }
    });
    
    ws.send(JSON.stringify(command));
  });
}

// 运行单个测试
async function runTest(testCase) {
  const startTime = Date.now();
  try {
    const result = await sendCommand(testCase.command.type, testCase.command.params);
    const elapsed = Date.now() - startTime;
    
    if (testCase.validate(result)) {
      return { name: testCase.name, status: 'PASS', elapsed, result };
    } else {
      return { name: testCase.name, status: 'FAIL', elapsed, error: 'Validation failed', result };
    }
  } catch (error) {
    const elapsed = Date.now() - startTime;
    return { name: testCase.name, status: 'ERROR', elapsed, error: error.message };
  }
}

// 运行所有测试
async function runAllTests(includeWriteTests = false) {
  console.log('========================================');
  console.log('  Godot MCP 接口回归测试');
  console.log('========================================\n');
  
  const tests = includeWriteTests ? [...TEST_CASES, ...WRITE_TEST_CASES] : TEST_CASES;
  
  let passed = 0;
  let failed = 0;
  let errors = 0;
  
  for (const testCase of tests) {
    const result = await runTest(testCase);
    testResults.push(result);
    
    const statusIcon = result.status === 'PASS' ? '✓' : result.status === 'FAIL' ? '✗' : '⚠';
    const statusColor = result.status === 'PASS' ? '\x1b[32m' : '\x1b[31m';
    
    console.log(`${statusColor}${statusIcon}\x1b[0m ${result.name} (${result.elapsed}ms)`);
    
    if (result.status === 'PASS') {
      passed++;
    } else if (result.status === 'FAIL') {
      failed++;
      console.log(`    Validation failed. Result:`, JSON.stringify(result.result, null, 2).substring(0, 200));
    } else {
      errors++;
      console.log(`    Error: ${result.error}`);
    }
  }
  
  console.log('\n========================================');
  console.log(`  结果: ${passed} 通过, ${failed} 失败, ${errors} 错误`);
  console.log(`  总计: ${tests.length} 个测试`);
  console.log('========================================\n');
  
  return { passed, failed, errors, total: tests.length };
}

// 主函数
async function main() {
  const includeWriteTests = process.argv.includes('--write');
  
  try {
    await connect();
    const results = await runAllTests(includeWriteTests);
    
    ws.close();
    
    // 返回非零退出码表示有测试失败
    process.exit(results.failed + results.errors > 0 ? 1 : 0);
  } catch (error) {
    console.error('Fatal error:', error.message);
    console.error('\n请确保:');
    console.error('  1. Godot 编辑器已启动');
    console.error('  2. Godot MCP 插件已启用');
    console.error('  3. WebSocket 服务器正在运行 (端口 9080)');
    process.exit(1);
  }
}

main();
