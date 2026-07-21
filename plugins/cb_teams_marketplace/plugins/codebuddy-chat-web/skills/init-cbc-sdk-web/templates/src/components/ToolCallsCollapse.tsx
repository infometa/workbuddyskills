import { useState, useEffect, useMemo } from 'react';
import { Loading } from 'tdesign-react';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  CheckCircleFilledIcon,
  CloseCircleFilledIcon,
} from 'tdesign-icons-react';
import { 
  Terminal, 
  Sparkles, 
  Search, 
  Globe, 
  Wrench,
  FileText,
  Code,
  FolderSearch,
  Edit,
  Trash2,
  Eye,
  Image,
  MessageSquare,
  Database,
  Settings,
  Zap
} from 'lucide-react';
import { ToolCall } from '../types';

interface ToolCallsCollapseProps {
  toolCalls: ToolCall[];
  isStreaming?: boolean;
}

// 工具图标映射 - 根据 SDK 实际返回的工具名（截图显示为 PascalCase）
const getToolIcon = (toolName: string) => {
  const name = toolName.toLowerCase();
  
  // Skill 技能调用
  if (name === 'skill') {
    return { icon: Sparkles, color: 'var(--td-warning-color)' };
  }
  // Bash 命令执行
  if (name === 'bash') {
    return { icon: Terminal, color: 'var(--td-text-color-secondary)' };
  }
  // Web 搜索
  if (name === 'websearch') {
    return { icon: Search, color: '#1890ff' };
  }
  // Web 抓取
  if (name === 'webfetch') {
    return { icon: Globe, color: '#52c41a' };
  }
  // 写入文件
  if (name === 'write') {
    return { icon: FileText, color: '#fa8c16' };
  }
  // 读取文件
  if (name === 'read' || name === 'readfile') {
    return { icon: Eye, color: '#722ed1' };
  }
  // 编辑文件
  if (name === 'edit' || name === 'editfile') {
    return { icon: Edit, color: '#fa8c16' };
  }
  // 删除文件
  if (name === 'delete' || name === 'deletefile') {
    return { icon: Trash2, color: '#ff4d4f' };
  }
  // 搜索
  if (name === 'search' || name === 'grep') {
    return { icon: FolderSearch, color: '#13c2c2' };
  }
  // 列出目录
  if (name === 'listdir' || name === 'ls') {
    return { icon: FolderSearch, color: '#13c2c2' };
  }
  // 图片生成
  if (name === 'imagegen') {
    return { icon: Image, color: '#f5222d' };
  }
  // 任务
  if (name === 'task') {
    return { icon: Zap, color: '#faad14' };
  }
  
  // 默认图标
  return { icon: Wrench, color: 'var(--td-text-color-secondary)' };
};

// 获取工具类型标识（用于汇总显示）
const getToolType = (toolName: string): string => {
  const name = toolName.toLowerCase();
  
  if (name === 'skill') return 'skill';
  if (name === 'bash') return 'bash';
  if (name === 'websearch') return 'websearch';
  if (name === 'webfetch') return 'webfetch';
  if (name === 'write') return 'write';
  if (name === 'read' || name === 'readfile') return 'read';
  if (name === 'edit' || name === 'editfile') return 'edit';
  if (name === 'delete' || name === 'deletefile') return 'delete';
  if (name === 'search' || name === 'grep' || name === 'listdir') return 'search';
  if (name === 'imagegen') return 'image';
  if (name === 'task') return 'task';
  
  return 'other';
};

export function ToolCallsCollapse({ toolCalls, isStreaming = false }: ToolCallsCollapseProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  // 可折叠工具的展开状态（按 toolId 管理）
  const [expandedToolIds, setExpandedToolIds] = useState<Set<string>>(new Set());
  
  // 切换工具的展开状态
  const toggleToolExpanded = (toolId: string) => {
    setExpandedToolIds(prev => {
      const next = new Set(prev);
      if (next.has(toolId)) {
        next.delete(toolId);
      } else {
        next.add(toolId);
      }
      return next;
    });
  };
  
  // 是否所有工具都已完成
  const allCompleted = toolCalls.every(tool => tool.status === 'completed' || tool.status === 'error');
  
  // 是否有任何工具正在运行
  const hasRunning = toolCalls.some(tool => tool.status === 'running');
  
  // 是否有失败的工具
  const hasError = toolCalls.some(tool => tool.status === 'error');
  
  // 汇总工具类型（去重）
  const toolSummary = useMemo(() => {
    const typeMap = new Map<string, { icon: any; color: string; count: number }>();
    toolCalls.forEach(tool => {
      const type = getToolType(tool.name);
      const { icon, color } = getToolIcon(tool.name);
      if (typeMap.has(type)) {
        typeMap.get(type)!.count++;
      } else {
        typeMap.set(type, { icon, color, count: 1 });
      }
    });
    return Array.from(typeMap.entries()).map(([type, info]) => ({
      type,
      ...info
    }));
  }, [toolCalls]);
  
  // 找到最新的正在运行的工具（用于连续调用时展示）
  const latestRunningTool = useMemo(() => {
    for (let i = toolCalls.length - 1; i >= 0; i--) {
      if (toolCalls[i].status === 'running') {
        return { tool: toolCalls[i], index: i };
      }
    }
    return null;
  }, [toolCalls]);
  
  // 当有新的工具调用开始时，如果之前是展开状态且所有都完成了，保持折叠
  useEffect(() => {
    if (toolCalls.length === 1 && hasRunning) {
      setIsExpanded(true);
    } else if (allCompleted && !isStreaming) {
      setIsExpanded(false);
    }
  }, [toolCalls.length, hasRunning, allCompleted, isStreaming]);

  // 渲染单个工具调用详情
  const renderToolDetail = (tool: ToolCall, index: number) => {
    const isRunning = tool.status === 'running';
    const isCompleted = tool.status === 'completed';
    const isError = tool.status === 'error' || tool.isError;
    
    const input = tool.input || {};
    const { icon: ToolIcon, color: iconColor } = getToolIcon(tool.name);
    const toolExpanded = expandedToolIds.has(tool.id);
    
    // 判断工具类型 - 根据截图实际的工具名（PascalCase）
    const toolNameLower = tool.name.toLowerCase();
    const isSkill = toolNameLower === 'skill';
    const isBash = toolNameLower === 'bash';
    const isWebSearch = toolNameLower === 'websearch';
    const isWebFetch = toolNameLower === 'webfetch';
    const isWrite = toolNameLower === 'write';
    
    // Skill 工具的特殊渲染
    // 标题: 使用 {skill名称} 技能，内容: args
    if (isSkill) {
      const skillName = (input.skill || 'Unknown') as string;
      const skillArgs = (input.args || '') as string;
      
      return (
        <div
          key={tool.id}
          className="rounded-lg overflow-hidden transition-all"
          style={{ backgroundColor: 'var(--td-bg-color-secondarycontainer)' }}
        >
          <div className="flex items-center gap-2 px-3 py-2">
            {isRunning ? (
              <Loading size="small" />
            ) : isCompleted && !isError ? (
              <CheckCircleFilledIcon style={{ color: 'var(--td-success-color)' }} />
            ) : (
              <CloseCircleFilledIcon style={{ color: 'var(--td-error-color)' }} />
            )}
            <ToolIcon size={16} style={{ color: iconColor }} />
            <span
              className="flex-1 text-sm font-medium"
              style={{ color: 'var(--td-text-color-primary)' }}
            >
              使用 <span style={{ color: 'var(--td-brand-color)' }}>{skillName}</span> 技能
            </span>
            <span
              className="text-xs"
              style={{ color: 'var(--td-text-color-placeholder)' }}
            >
              {isRunning ? '执行中...' : isError ? '失败' : '完成'}
            </span>
          </div>
          
          {skillArgs && (
            <div
              className="px-3 py-2 text-xs whitespace-pre-wrap break-all max-h-24 overflow-y-auto border-t"
              style={{
                color: 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              {String(skillArgs).length > 300 ? String(skillArgs).slice(0, 300) + '...' : String(skillArgs)}
            </div>
          )}
          
          {tool.result && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border-t"
              style={{
                color: isError ? 'var(--td-error-color)' : 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <span style={{ color: 'var(--td-text-color-placeholder)' }}>{isError ? '错误: ' : '结果: '}</span>
              {tool.result.length > 500 ? tool.result.slice(0, 500) + '...' : tool.result}
            </div>
          )}
        </div>
      );
    }
    
    // Bash 工具的特殊渲染
    // 标题: description，展开后显示: command
    if (isBash) {
      const command = (input.command || '') as string;
      const description = (input.description || '执行命令') as string;
      
      return (
        <div
          key={tool.id}
          className="rounded-lg overflow-hidden transition-all"
          style={{ backgroundColor: 'var(--td-bg-color-secondarycontainer)' }}
        >
          <div 
            className="flex items-center gap-2 px-3 py-2 cursor-pointer"
            onClick={() => toggleToolExpanded(tool.id)}
          >
            {isRunning ? (
              <Loading size="small" />
            ) : isCompleted && !isError ? (
              <CheckCircleFilledIcon style={{ color: 'var(--td-success-color)' }} />
            ) : (
              <CloseCircleFilledIcon style={{ color: 'var(--td-error-color)' }} />
            )}
            <ToolIcon size={16} style={{ color: iconColor }} />
            <span
              className="flex-1 text-sm font-medium truncate"
              style={{ color: 'var(--td-text-color-primary)' }}
            >
              {description || '执行命令'}
            </span>
            <span
              className="text-xs"
              style={{ color: 'var(--td-text-color-placeholder)' }}
            >
              {isRunning ? '执行中...' : isError ? '失败' : '完成'}
            </span>
            {command && (
              toolExpanded ? (
                <ChevronUpIcon size={14} style={{ color: 'var(--td-text-color-placeholder)' }} />
              ) : (
                <ChevronDownIcon size={14} style={{ color: 'var(--td-text-color-placeholder)' }} />
              )
            )}
          </div>
          
          {toolExpanded && command && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border-t"
              style={{
                color: 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <span style={{ color: 'var(--td-text-color-placeholder)' }}>$ </span>
              {command.length > 500 ? command.slice(0, 500) + '...' : command}
            </div>
          )}
          
          {tool.result && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border-t"
              style={{
                color: isError ? 'var(--td-error-color)' : 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <span style={{ color: 'var(--td-text-color-placeholder)' }}>{isError ? '错误: ' : '输出: '}</span>
              {tool.result.length > 500 ? tool.result.slice(0, 500) + '...' : tool.result}
            </div>
          )}
        </div>
      );
    }
    
    // WebSearch 工具的特殊渲染
    // 标题: 搜索 {query}
    if (isWebSearch) {
      const query = (input.query || '') as string;
      
      return (
        <div
          key={tool.id}
          className="rounded-lg overflow-hidden transition-all"
          style={{ backgroundColor: 'var(--td-bg-color-secondarycontainer)' }}
        >
          <div className="flex items-center gap-2 px-3 py-2">
            {isRunning ? (
              <Loading size="small" />
            ) : isCompleted && !isError ? (
              <CheckCircleFilledIcon style={{ color: 'var(--td-success-color)' }} />
            ) : (
              <CloseCircleFilledIcon style={{ color: 'var(--td-error-color)' }} />
            )}
            <ToolIcon size={16} style={{ color: iconColor }} />
            <span
              className="flex-1 text-sm font-medium"
              style={{ color: 'var(--td-text-color-primary)' }}
            >
              搜索: <span style={{ color: '#1890ff' }}>{query || '...'}</span>
            </span>
            <span
              className="text-xs"
              style={{ color: 'var(--td-text-color-placeholder)' }}
            >
              {isRunning ? '搜索中...' : isError ? '失败' : '完成'}
            </span>
          </div>
          
          {tool.result && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border-t"
              style={{
                color: isError ? 'var(--td-error-color)' : 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <span style={{ color: 'var(--td-text-color-placeholder)' }}>{isError ? '错误: ' : '结果: '}</span>
              {tool.result.length > 500 ? tool.result.slice(0, 500) + '...' : tool.result}
            </div>
          )}
        </div>
      );
    }
    
    // WebFetch 工具的特殊渲染
    // 标题: prompt（获取目的），展开显示: url
    if (isWebFetch) {
      const url = (input.url || '') as string;
      const prompt = (input.prompt || '获取网页内容') as string;
      
      return (
        <div
          key={tool.id}
          className="rounded-lg overflow-hidden transition-all"
          style={{ backgroundColor: 'var(--td-bg-color-secondarycontainer)' }}
        >
          <div 
            className="flex items-center gap-2 px-3 py-2 cursor-pointer"
            onClick={() => toggleToolExpanded(tool.id)}
          >
            {isRunning ? (
              <Loading size="small" />
            ) : isCompleted && !isError ? (
              <CheckCircleFilledIcon style={{ color: 'var(--td-success-color)' }} />
            ) : (
              <CloseCircleFilledIcon style={{ color: 'var(--td-error-color)' }} />
            )}
            <ToolIcon size={16} style={{ color: iconColor }} />
            <span
              className="flex-1 text-sm font-medium truncate"
              style={{ color: 'var(--td-text-color-primary)' }}
            >
              {prompt}
            </span>
            <span
              className="text-xs"
              style={{ color: 'var(--td-text-color-placeholder)' }}
            >
              {isRunning ? '获取中...' : isError ? '失败' : '完成'}
            </span>
            {url && (
              toolExpanded ? (
                <ChevronUpIcon size={14} style={{ color: 'var(--td-text-color-placeholder)' }} />
              ) : (
                <ChevronDownIcon size={14} style={{ color: 'var(--td-text-color-placeholder)' }} />
              )
            )}
          </div>
          
          {/* 展开显示 URL */}
          {toolExpanded && url && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all border-t"
              style={{
                color: 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <span style={{ color: 'var(--td-text-color-placeholder)' }}>URL: </span>
              {url}
            </div>
          )}
          
          {tool.result && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border-t"
              style={{
                color: isError ? 'var(--td-error-color)' : 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <span style={{ color: 'var(--td-text-color-placeholder)' }}>{isError ? '错误: ' : '内容: '}</span>
              {tool.result.length > 500 ? tool.result.slice(0, 500) + '...' : tool.result}
            </div>
          )}
        </div>
      );
    }
    
    // Write 工具的特殊渲染
    // 标题: file_path，展开显示: content
    if (isWrite) {
      const filePath = (input.file_path || '') as string;
      const content = (input.content || '') as string;
      // 提取文件名
      const fileName = filePath.split('/').pop() || filePath;
      
      return (
        <div
          key={tool.id}
          className="rounded-lg overflow-hidden transition-all"
          style={{ backgroundColor: 'var(--td-bg-color-secondarycontainer)' }}
        >
          <div 
            className="flex items-center gap-2 px-3 py-2 cursor-pointer"
            onClick={() => toggleToolExpanded(tool.id)}
          >
            {isRunning ? (
              <Loading size="small" />
            ) : isCompleted && !isError ? (
              <CheckCircleFilledIcon style={{ color: 'var(--td-success-color)' }} />
            ) : (
              <CloseCircleFilledIcon style={{ color: 'var(--td-error-color)' }} />
            )}
            <ToolIcon size={16} style={{ color: iconColor }} />
            <span
              className="flex-1 text-sm font-medium truncate"
              style={{ color: 'var(--td-text-color-primary)' }}
              title={filePath}
            >
              写入 <span style={{ color: '#fa8c16' }}>{fileName}</span>
            </span>
            <span
              className="text-xs"
              style={{ color: 'var(--td-text-color-placeholder)' }}
            >
              {isRunning ? '写入中...' : isError ? '失败' : '完成'}
            </span>
            {content && (
              toolExpanded ? (
                <ChevronUpIcon size={14} style={{ color: 'var(--td-text-color-placeholder)' }} />
              ) : (
                <ChevronDownIcon size={14} style={{ color: 'var(--td-text-color-placeholder)' }} />
              )
            )}
          </div>
          
          {/* 展开显示完整路径和内容 */}
          {toolExpanded && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-48 overflow-y-auto border-t"
              style={{
                color: 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <div className="mb-2" style={{ color: 'var(--td-text-color-placeholder)' }}>
                路径: {filePath}
              </div>
              {content && (
                <div>
                  <span style={{ color: 'var(--td-text-color-placeholder)' }}>内容:</span>
                  <pre className="mt-1 whitespace-pre-wrap">
                    {content.length > 1000 ? content.slice(0, 1000) + '...' : content}
                  </pre>
                </div>
              )}
            </div>
          )}
          
          {tool.result && (
            <div
              className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border-t"
              style={{
                color: isError ? 'var(--td-error-color)' : 'var(--td-text-color-secondary)',
                borderColor: 'var(--td-component-stroke)',
                backgroundColor: 'var(--td-bg-color-container)',
              }}
            >
              <span style={{ color: 'var(--td-text-color-placeholder)' }}>{isError ? '错误: ' : '结果: '}</span>
              {tool.result.length > 500 ? tool.result.slice(0, 500) + '...' : tool.result}
            </div>
          )}
        </div>
      );
    }
    
    // 默认工具渲染（其他工具）
    const formatInput = (inputObj: Record<string, unknown> | undefined) => {
      if (!inputObj || Object.keys(inputObj).length === 0) return null;
      try {
        return JSON.stringify(inputObj, null, 2);
      } catch {
        return String(inputObj);
      }
    };
    
    const inputStr = formatInput(tool.input);
    
    return (
      <div
        key={tool.id}
        className="rounded-lg overflow-hidden transition-all"
        style={{ backgroundColor: 'var(--td-bg-color-secondarycontainer)' }}
      >
        <div className="flex items-center gap-2 px-3 py-2">
          {isRunning ? (
            <Loading size="small" />
          ) : isCompleted && !isError ? (
            <CheckCircleFilledIcon style={{ color: 'var(--td-success-color)' }} />
          ) : (
            <CloseCircleFilledIcon style={{ color: 'var(--td-error-color)' }} />
          )}
          <ToolIcon size={16} style={{ color: iconColor }} />
          <span
            className="flex-1 text-sm font-medium truncate"
            style={{ color: 'var(--td-text-color-primary)' }}
          >
            {tool.name}
          </span>
          <span
            className="text-xs"
            style={{ color: 'var(--td-text-color-placeholder)' }}
          >
            {isRunning ? '执行中...' : isError ? '失败' : '完成'}
          </span>
        </div>
        
        {inputStr && (
          <div
            className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-24 overflow-y-auto border-t"
            style={{
              color: 'var(--td-text-color-secondary)',
              borderColor: 'var(--td-component-stroke)',
              backgroundColor: 'var(--td-bg-color-container)',
            }}
          >
            <span style={{ color: 'var(--td-text-color-placeholder)' }}>输入: </span>
            {inputStr.length > 300 ? inputStr.slice(0, 300) + '...' : inputStr}
          </div>
        )}
        
        {tool.result && (
          <div
            className="px-3 py-2 text-xs font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border-t"
            style={{
              color: isError ? 'var(--td-error-color)' : 'var(--td-text-color-secondary)',
              borderColor: 'var(--td-component-stroke)',
              backgroundColor: 'var(--td-bg-color-container)',
            }}
          >
            <span style={{ color: 'var(--td-text-color-placeholder)' }}>{isError ? '错误: ' : '结果: '}</span>
            {tool.result.length > 500 ? tool.result.slice(0, 500) + '...' : tool.result}
          </div>
        )}
      </div>
    );
  };

  // 渲染收缩横条（带工具汇总）
  const renderCollapseBar = () => (
    <div
      className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-all hover:opacity-80"
      style={{ backgroundColor: 'var(--td-bg-color-component)' }}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      {/* 左侧：展开图标 + 状态图标 + 文字 + 数量 */}
      <div className="flex items-center gap-1.5">
        {isExpanded ? (
          <ChevronUpIcon size={16} style={{ color: 'var(--td-text-color-secondary)' }} />
        ) : (
          <ChevronDownIcon size={16} style={{ color: 'var(--td-text-color-secondary)' }} />
        )}
        {hasRunning ? (
          <Loading size="small" />
        ) : hasError ? (
          <CloseCircleFilledIcon size={16} style={{ color: 'var(--td-error-color)' }} />
        ) : (
          <CheckCircleFilledIcon size={16} style={{ color: 'var(--td-success-color)' }} />
        )}
        <span
          className="text-sm"
          style={{ color: 'var(--td-text-color-primary)' }}
        >
          {hasRunning ? '执行中...' : isExpanded ? '收起步骤' : '查看步骤'}
        </span>
        {toolCalls.length > 1 && (
          <span
            className="text-xs"
            style={{ color: 'var(--td-text-color-placeholder)' }}
          >
            ({toolCalls.length})
          </span>
        )}
      </div>
      
      {/* 右侧：工具图标汇总 */}
      <div className="flex items-center gap-1">
        {toolSummary.map(({ type, icon: Icon, color, count }) => (
          <div 
            key={type} 
            className="flex items-center gap-0.5 px-1.5 py-0.5 rounded"
            style={{ backgroundColor: 'var(--td-bg-color-secondarycontainer)' }}
            title={`${type} x${count}`}
          >
            <Icon size={12} style={{ color }} />
            {count > 1 && (
              <span 
                className="text-xs"
                style={{ color: 'var(--td-text-color-placeholder)', fontSize: '10px' }}
              >
                {count}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染最新运行中的工具（用于连续调用场景）
  const renderLatestRunningTool = () => {
    if (!latestRunningTool) return null;
    
    const { tool, index } = latestRunningTool;
    const previousCount = index;
    
    return (
      <div className="space-y-2">
        {previousCount > 0 && (
          <div
            className="flex items-center justify-between gap-1.5 px-3 py-1.5 rounded-lg cursor-pointer transition-all hover:opacity-80"
            style={{ backgroundColor: 'var(--td-bg-color-component)' }}
            onClick={() => setIsExpanded(true)}
          >
            <div className="flex items-center gap-1.5">
              <ChevronDownIcon size={14} style={{ color: 'var(--td-text-color-placeholder)' }} />
              <CheckCircleFilledIcon size={14} style={{ color: 'var(--td-success-color)' }} />
              <span
                className="text-xs"
                style={{ color: 'var(--td-text-color-secondary)' }}
              >
                {previousCount} 个步骤已完成
              </span>
            </div>
            {/* 已完成工具的图标汇总 */}
            <div className="flex items-center gap-1">
              {toolSummary.slice(0, -1).map(({ type, icon: Icon, color }) => (
                <Icon key={type} size={12} style={{ color }} />
              ))}
            </div>
          </div>
        )}
        
        {renderToolDetail(tool, index)}
      </div>
    );
  };

  // 单个工具调用的情况
  if (toolCalls.length === 1) {
    const tool = toolCalls[0];
    
    if (tool.status === 'running') {
      return (
        <div className="w-full">
          {renderToolDetail(tool, 0)}
        </div>
      );
    }
    
    return (
      <div className="w-full space-y-2">
        {renderCollapseBar()}
        {isExpanded && (
          <div className="space-y-2 pl-2">
            {renderToolDetail(tool, 0)}
          </div>
        )}
      </div>
    );
  }

  // 多个工具调用的情况
  if (hasRunning && !isExpanded) {
    return (
      <div className="w-full">
        {renderLatestRunningTool()}
      </div>
    );
  }

  return (
    <div className="w-full space-y-2">
      {renderCollapseBar()}
      {isExpanded && (
        <div className="space-y-2 pl-2">
          {toolCalls.map((tool, index) => renderToolDetail(tool, index))}
        </div>
      )}
    </div>
  );
}

export default ToolCallsCollapse;
