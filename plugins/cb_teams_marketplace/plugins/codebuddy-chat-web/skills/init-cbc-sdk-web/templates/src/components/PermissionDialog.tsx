import { Dialog, Button, Tag, Descriptions } from 'tdesign-react';
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

interface PermissionDialogProps {
  visible: boolean;
  request: PermissionRequest | null;
  onAllow: () => void;
  onDeny: () => void;
}

// 工具名称到图标和颜色的映射
const TOOL_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  'Bash': { icon: <TerminalIcon />, color: '#e34d59', label: '执行命令' },
  'Write': { icon: <EditIcon />, color: '#0052d9', label: '写入文件' },
  'Edit': { icon: <EditIcon />, color: '#0052d9', label: '编辑文件' },
  'Read': { icon: <FileIcon />, color: '#2ba471', label: '读取文件' },
  'ListDir': { icon: <FolderOpenIcon />, color: '#ed7b2f', label: '列出目录' },
  'Search': { icon: <SearchIcon />, color: '#8a6be5', label: '搜索' },
  'Grep': { icon: <SearchIcon />, color: '#8a6be5', label: '文本搜索' },
  'Delete': { icon: <DeleteIcon />, color: '#e34d59', label: '删除文件' },
};

// 获取工具配置
const getToolConfig = (toolName: string) => {
  return TOOL_CONFIG[toolName] || { 
    icon: <Code1Icon />, 
    color: '#666666', 
    label: toolName 
  };
};

// 格式化工具输入为可读的描述
const formatToolInput = (toolName: string, input: Record<string, unknown>) => {
  const items: Array<{ label: string; content: string }> = [];
  
  if (toolName === 'Bash' && input.command) {
    items.push({ label: '命令', content: String(input.command) });
  } else if ((toolName === 'Write' || toolName === 'Edit') && input.filePath) {
    items.push({ label: '文件路径', content: String(input.filePath) });
    if (input.content) {
      const content = String(input.content);
      items.push({ 
        label: '内容预览', 
        content: content.length > 200 ? content.slice(0, 200) + '...' : content 
      });
    }
  } else if (toolName === 'Read' && input.filePath) {
    items.push({ label: '文件路径', content: String(input.filePath) });
  } else if (toolName === 'ListDir' && input.path) {
    items.push({ label: '目录路径', content: String(input.path) });
  } else if ((toolName === 'Search' || toolName === 'Grep') && input.pattern) {
    items.push({ label: '搜索模式', content: String(input.pattern) });
    if (input.path) {
      items.push({ label: '搜索路径', content: String(input.path) });
    }
  } else {
    // 通用处理：显示所有参数
    Object.entries(input).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        const strValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
        items.push({ 
          label: key, 
          content: strValue.length > 200 ? strValue.slice(0, 200) + '...' : strValue 
        });
      }
    });
  }
  
  return items;
};

export function PermissionDialog({ visible, request, onAllow, onDeny }: PermissionDialogProps) {
  if (!request) return null;
  
  const toolConfig = getToolConfig(request.toolName);
  const inputItems = formatToolInput(request.toolName, request.input);
  
  return (
    <Dialog
      visible={visible}
      header={
        <div className="flex items-center gap-2">
          <span style={{ color: toolConfig.color }}>{toolConfig.icon}</span>
          <span>权限确认</span>
        </div>
      }
      onClose={onDeny}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onDeny}>
            拒绝
          </Button>
          <Button theme="primary" onClick={onAllow}>
            允许
          </Button>
        </div>
      }
      width={520}
      destroyOnClose
    >
      <div className="space-y-4">
        {/* 工具标签 */}
        <div className="flex items-center gap-2">
          <span style={{ color: 'var(--td-text-color-secondary)' }}>工具：</span>
          <Tag 
            theme="primary" 
            variant="light"
            icon={toolConfig.icon}
          >
            {toolConfig.label}
          </Tag>
          <Tag variant="outline" size="small">
            {request.toolName}
          </Tag>
        </div>
        
        {/* 工具参数详情 */}
        <div 
          className="rounded-lg p-4"
          style={{ backgroundColor: 'var(--td-bg-color-component)' }}
        >
          {request.toolName === 'Bash' && request.input.command ? (
            // Bash 命令特殊显示
            <div>
              <div 
                className="text-xs mb-2 font-medium"
                style={{ color: 'var(--td-text-color-secondary)' }}
              >
                将要执行的命令：
              </div>
              <pre 
                className="font-mono text-sm p-3 rounded overflow-x-auto whitespace-pre-wrap break-all"
                style={{ 
                  backgroundColor: 'var(--td-bg-color-page)',
                  color: 'var(--td-text-color-primary)',
                  maxHeight: '200px'
                }}
              >
                {String(request.input.command)}
              </pre>
            </div>
          ) : inputItems.length > 0 ? (
            // 其他工具使用描述列表
            <Descriptions 
              column={1} 
              itemStyle={{ 
                paddingBottom: '8px'
              }}
              labelStyle={{
                width: '80px',
                color: 'var(--td-text-color-secondary)'
              }}
              contentStyle={{
                fontFamily: 'monospace',
                fontSize: '13px',
                wordBreak: 'break-all'
              }}
            >
              {inputItems.map((item, index) => (
                <Descriptions.Item key={index} label={item.label}>
                  {item.content}
                </Descriptions.Item>
              ))}
            </Descriptions>
          ) : (
            <div 
              className="text-sm"
              style={{ color: 'var(--td-text-color-placeholder)' }}
            >
              无参数
            </div>
          )}
        </div>
        
        {/* 警告提示 */}
        {request.toolName === 'Bash' && (
          <div 
            className="flex items-start gap-2 text-sm p-3 rounded-lg"
            style={{ 
              backgroundColor: 'rgba(227, 77, 89, 0.1)',
              color: 'var(--td-error-color)'
            }}
          >
            <span className="flex-shrink-0">⚠️</span>
            <span>此操作将在您的系统上执行命令，请确认命令内容安全可信。</span>
          </div>
        )}
        {(request.toolName === 'Write' || request.toolName === 'Edit' || request.toolName === 'Delete') && (
          <div 
            className="flex items-start gap-2 text-sm p-3 rounded-lg"
            style={{ 
              backgroundColor: 'rgba(0, 82, 217, 0.1)',
              color: 'var(--td-brand-color)'
            }}
          >
            <span className="flex-shrink-0">📝</span>
            <span>此操作将修改您的文件系统，请确认操作正确。</span>
          </div>
        )}
      </div>
    </Dialog>
  );
}
