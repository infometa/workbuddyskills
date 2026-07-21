import { Button } from 'tdesign-react';
import { 
  TerminalIcon, 
  FileIcon, 
  FolderOpenIcon,
  SearchIcon,
  Code1Icon,
  EditIcon,
  DeleteIcon
} from 'tdesign-icons-react';
import { PermissionRequest } from '../types';

interface InlinePermissionCardProps {
  request: PermissionRequest;
  onAllow: () => void;
  onDeny: () => void;
}

// 工具名称到图标和颜色的映射
const TOOL_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  'Bash': { icon: <TerminalIcon />, color: '#e34d59', label: '执行命令' },
  'Write': { icon: <EditIcon />, color: '#0052d9', label: '写入文件' },
  'Edit': { icon: <EditIcon />, color: '#0052d9', label: '编辑文件' },
  'Read': { icon: <FileIcon />, color: '#2ba471', label: '读取文件' },
  'ReadFile': { icon: <FileIcon />, color: '#2ba471', label: '读取文件' },
  'ListDir': { icon: <FolderOpenIcon />, color: '#ed7b2f', label: '列出目录' },
  'Search': { icon: <SearchIcon />, color: '#8a6be5', label: '搜索' },
  'Grep': { icon: <SearchIcon />, color: '#8a6be5', label: '文本搜索' },
  'Delete': { icon: <DeleteIcon />, color: '#e34d59', label: '删除文件' },
  'DeleteFile': { icon: <DeleteIcon />, color: '#e34d59', label: '删除文件' },
};

// 获取工具配置
const getToolConfig = (toolName: string) => {
  return TOOL_CONFIG[toolName] || { 
    icon: <Code1Icon />, 
    color: '#666666', 
    label: toolName 
  };
};

// 获取文件路径或主要信息
const getMainInfo = (toolName: string, input: Record<string, unknown>): string => {
  if (toolName === 'Bash' && input.command) {
    const cmd = String(input.command);
    return cmd.length > 60 ? cmd.slice(0, 60) + '...' : cmd;
  }
  if (input.filePath) {
    return String(input.filePath);
  }
  if (input.path) {
    return String(input.path);
  }
  if (input.target_file) {
    return String(input.target_file);
  }
  // 返回第一个有意义的参数值
  for (const [, value] of Object.entries(input)) {
    if (value && typeof value === 'string') {
      return value.length > 60 ? value.slice(0, 60) + '...' : value;
    }
  }
  return '';
};

export function InlinePermissionCard({ request, onAllow, onDeny }: InlinePermissionCardProps) {
  const toolConfig = getToolConfig(request.toolName);
  const mainInfo = getMainInfo(request.toolName, request.input);
  const isDangerous = request.toolName === 'Bash' || request.toolName === 'Delete' || request.toolName === 'DeleteFile';
  
  return (
    <div className="animate-fade-in flex items-center gap-3 flex-wrap py-2">
      {/* 工具图标和标签 */}
      <div 
        className="flex items-center gap-2 px-3 py-1.5 rounded-full"
        style={{ 
          backgroundColor: `${toolConfig.color}15`,
          color: toolConfig.color
        }}
      >
        <span className="flex items-center text-base">{toolConfig.icon}</span>
        <span className="text-sm font-medium">{toolConfig.label}</span>
      </div>
      
      {/* 文件路径/命令 */}
      {mainInfo && (
        <code 
          className="text-sm px-2.5 py-1 rounded-md font-mono truncate max-w-[400px]"
          style={{ 
            backgroundColor: 'var(--td-bg-color-component)',
            color: 'var(--td-text-color-primary)'
          }}
          title={mainInfo}
        >
          {mainInfo}
        </code>
      )}
      
      {/* 危险操作警告标记 */}
      {isDangerous && (
        <span 
          className="text-xs px-2 py-0.5 rounded"
          style={{ 
            backgroundColor: 'rgba(227, 77, 89, 0.1)',
            color: '#e34d59'
          }}
        >
          ⚠️ 危险操作
        </span>
      )}
      
      {/* 操作按钮 */}
      <div className="flex items-center gap-2 ml-auto">
        <Button 
          size="small"
          theme="danger"
          variant="text"
          onClick={onDeny}
          style={{ 
            color: '#e34d59',
            fontWeight: 500
          }}
        >
          拒绝
        </Button>
        <Button 
          size="small"
          theme="success"
          variant="base"
          onClick={onAllow}
          style={{ 
            backgroundColor: '#2ba471',
            borderColor: '#2ba471',
            color: 'white',
            fontWeight: 500
          }}
        >
          允许
        </Button>
      </div>
    </div>
  );
}
