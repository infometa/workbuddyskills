import { useState, useEffect, useCallback } from 'react';
import { 
  Form, 
  Input, 
  Textarea, 
  Button, 
  Tooltip,
  Popconfirm,
  MessagePlugin,
  Loading,
  Link,
  Tag,
  Select
} from 'tdesign-react';
import { 
  AddIcon, 
  EditIcon, 
  DeleteIcon,
  CheckIcon,
  CheckCircleFilledIcon,
  CloseCircleFilledIcon,
  RefreshIcon
} from 'tdesign-icons-react';
import { Bot, Sparkles, Code, FileText, Globe, Lightbulb } from 'lucide-react';
import { CustomAgent, PermissionMode } from '../types';

interface SettingsPageProps {
  agents: CustomAgent[];
  onAdd: (agent: Omit<CustomAgent, 'id' | 'createdAt' | 'updatedAt'>) => CustomAgent;
  onUpdate: (id: string, updates: Partial<Omit<CustomAgent, 'id' | 'createdAt'>>) => void;
  onDelete: (id: string) => void;
}

type LoginMethod = 'env' | 'cli' | 'none';

interface LoginStatus {
  isLoggedIn: boolean;
  checking: boolean;
  method?: LoginMethod;
  envConfigured?: boolean;
  cliConfigured?: boolean;
  error?: string;
  apiKey?: string;
  envVars?: {
    apiKey?: string;
    authToken?: string;
    internetEnv?: string;
    baseUrl?: string;
  };
}

const PRESET_ICONS = [
  { name: 'Bot', icon: Bot },
  { name: 'Sparkles', icon: Sparkles },
  { name: 'Code', icon: Code },
  { name: 'FileText', icon: FileText },
  { name: 'Globe', icon: Globe },
  { name: 'Lightbulb', icon: Lightbulb },
];

const PRESET_COLORS = [
  '#0052d9', '#0594fa', '#00a870', '#ed7b2f', 
  '#e34d59', '#a25eb5', '#5c6bc0', '#26a69a'
];

const PERMISSION_MODES: { value: PermissionMode; label: string; description: string }[] = [
  { value: 'default', label: 'default', description: '默认模式，所有操作需确认' },
  { value: 'acceptEdits', label: 'acceptEdits', description: '自动批准文件编辑，Bash 仍需确认' },
  { value: 'plan', label: 'plan', description: '规划模式，仅允许读取操作' },
  { value: 'bypassPermissions', label: 'bypassPermissions', description: '跳过所有权限检查（谨慎使用）' },
];

const PRESET_TEMPLATES = [
  {
    name: '代码助手',
    description: '专注于编程和代码相关任务',
    systemPrompt: '你是一个专业的编程助手。你擅长编写、审查和解释代码。请提供清晰、高效且符合最佳实践的代码解决方案。在解释时，请考虑代码的可读性、性能和可维护性。',
    icon: 'Code',
    color: '#0594fa',
  },
  {
    name: '写作助手',
    description: '帮助撰写和优化各类文档',
    systemPrompt: '你是一个专业的写作助手。你擅长撰写、编辑和优化各类文档，包括文章、报告、邮件等。请帮助用户提升文字表达的清晰度、逻辑性和吸引力。',
    icon: 'FileText',
    color: '#00a870',
  },
  {
    name: '翻译助手',
    description: '提供高质量的多语言翻译',
    systemPrompt: '你是一个专业的翻译助手。你精通多种语言，能够提供准确、自然、符合语境的翻译。请在翻译时保持原文的语气和风格，同时确保目标语言的地道表达。',
    icon: 'Globe',
    color: '#ed7b2f',
  },
  {
    name: '创意助手',
    description: '激发灵感，提供创意建议',
    systemPrompt: '你是一个富有创意的助手。你善于头脑风暴、提供创新想法和独特视角。请帮助用户突破思维定式，探索新的可能性，激发创造力。',
    icon: 'Lightbulb',
    color: '#a25eb5',
  },
];

export function SettingsPage({ 
  agents, 
  onAdd, 
  onUpdate, 
  onDelete 
}: SettingsPageProps) {
  const [editingAgent, setEditingAgent] = useState<CustomAgent | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    systemPrompt: '',
    icon: 'Bot',
    color: '#0052d9',
    permissionMode: 'default' as PermissionMode,
  });
  
  // 登录状态
  const [loginStatus, setLoginStatus] = useState<LoginStatus>({
    isLoggedIn: false,
    checking: true,
  });
  
  // 环境变量配置
  const [showEnvConfig, setShowEnvConfig] = useState(false);
  const [envConfig, setEnvConfig] = useState({
    apiKey: '',
    authToken: '',
    internetEnv: '' as '' | 'internal' | 'iOA',
    baseUrl: '',
  });
  const [savingEnv, setSavingEnv] = useState(false);

  // 检查登录状态
  const checkLoginStatus = useCallback(async () => {
    setLoginStatus(prev => ({ ...prev, checking: true, error: undefined }));
    
    try {
      const response = await fetch('/api/check-login');
      const data = await response.json();
      
      setLoginStatus({
        isLoggedIn: data.isLoggedIn,
        checking: false,
        method: data.method,
        envConfigured: data.envConfigured,
        cliConfigured: data.cliConfigured,
        error: data.error,
        apiKey: data.apiKey,
        envVars: data.envVars,
      });
    } catch (error: any) {
      setLoginStatus({
        isLoggedIn: false,
        checking: false,
        error: error?.message || '检查登录状态失败',
      });
    }
  }, []);
  
  // 保存环境变量配置
  const saveEnvConfig = async () => {
    // 至少需要配置一个有效的值
    const hasAnyConfig = envConfig.apiKey.trim() || envConfig.authToken.trim();
    if (!hasAnyConfig) {
      MessagePlugin.warning('请至少配置 API Key 或 Auth Token');
      return;
    }
    
    setSavingEnv(true);
    try {
      const response = await fetch('/api/save-env-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey: envConfig.apiKey.trim() || undefined,
          authToken: envConfig.authToken.trim() || undefined,
          internetEnv: envConfig.internetEnv || undefined,
          baseUrl: envConfig.baseUrl.trim() || undefined,
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        MessagePlugin.success(data.message);
        setShowEnvConfig(false);
        setEnvConfig({ apiKey: '', authToken: '', internetEnv: '', baseUrl: '' });
        // 重新检查登录状态
        checkLoginStatus();
      } else {
        MessagePlugin.error(data.error || '保存失败');
      }
    } catch (error: any) {
      MessagePlugin.error(error?.message || '保存失败');
    } finally {
      setSavingEnv(false);
    }
  };

  // 初始化时检查登录状态
  useEffect(() => {
    checkLoginStatus();
  }, [checkLoginStatus]);

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      systemPrompt: '',
      icon: 'Bot',
      color: '#0052d9',
      permissionMode: 'default',
    });
    setEditingAgent(null);
    setIsCreating(false);
  };

  const handleEdit = (agent: CustomAgent) => {
    if (agent.id === 'default') return;
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      description: agent.description || '',
      systemPrompt: agent.systemPrompt,
      icon: agent.icon || 'Bot',
      color: agent.color || '#0052d9',
      permissionMode: agent.permissionMode || 'default',
    });
    setIsCreating(true);
  };

  const handleSave = () => {
    if (!formData.name.trim() || !formData.systemPrompt.trim()) {
      MessagePlugin.warning('请填写名称和系统提示词');
      return;
    }

    if (editingAgent) {
      onUpdate(editingAgent.id, formData);
      MessagePlugin.success('Agent 已更新');
    } else {
      onAdd(formData);
      MessagePlugin.success('Agent 已创建');
    }
    resetForm();
  };

  const handleUseTemplate = (template: typeof PRESET_TEMPLATES[0]) => {
    setFormData({
      ...template,
      description: template.description,
    });
    setIsCreating(true);
  };

  const handleDelete = (id: string) => {
    onDelete(id);
    MessagePlugin.success('Agent 已删除');
  };

  const getIconComponent = (iconName: string) => {
    const preset = PRESET_ICONS.find(p => p.name === iconName);
    return preset ? preset.icon : Bot;
  };

  const customAgents = agents.filter(a => a.id !== 'default');

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-8">
        {/* 页面标题 */}
        <div>
          <h1 
            className="text-2xl font-semibold mb-2"
            style={{ color: 'var(--td-text-color-primary)' }}
          >
            设置
          </h1>
          <p style={{ color: 'var(--td-text-color-secondary)' }}>
            管理登录配置和自定义 Agent
          </p>
        </div>

        {/* 登录配置 */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 
                className="text-lg font-medium"
                style={{ color: 'var(--td-text-color-primary)' }}
              >
                登录配置
              </h2>
              <p 
                className="text-sm mt-1"
                style={{ color: 'var(--td-text-color-secondary)' }}
              >
                支持环境变量或 CodeBuddy CLI 登录
              </p>
            </div>
            <Button 
              variant="text" 
              icon={<RefreshIcon />}
              onClick={checkLoginStatus}
              loading={loginStatus.checking}
            >
              刷新
            </Button>
          </div>
          
          {/* 当前状态 */}
          <div className="flex items-center gap-3 mb-6">
            {loginStatus.checking ? (
              <>
                <Loading size="small" />
                <span style={{ color: 'var(--td-text-color-secondary)' }}>
                  正在检查登录状态...
                </span>
              </>
            ) : loginStatus.isLoggedIn ? (
              <>
                <CheckCircleFilledIcon 
                  size="20px" 
                  style={{ color: 'var(--td-success-color)' }} 
                />
                <span style={{ color: 'var(--td-text-color-primary)' }}>
                  已登录
                </span>
                <Tag size="small" variant="outline">
                  {loginStatus.method === 'env' ? '环境变量' : 'CLI'}
                </Tag>
                {loginStatus.method === 'env' && loginStatus.apiKey && (
                  <span 
                    className="text-sm font-mono"
                    style={{ color: 'var(--td-text-color-secondary)' }}
                  >
                    {loginStatus.apiKey}
                  </span>
                )}
              </>
            ) : (
              <>
                <CloseCircleFilledIcon 
                  size="20px" 
                  style={{ color: 'var(--td-text-color-placeholder)' }} 
                />
                <span style={{ color: 'var(--td-text-color-secondary)' }}>
                  未登录
                </span>
              </>
            )}
          </div>
          
          {/* 环境变量配置 */}
          <div className="mb-6">
            <h3 
              className="text-sm font-medium mb-3"
              style={{ color: 'var(--td-text-color-secondary)' }}
            >
              方式一：环境变量
            </h3>
            
            {showEnvConfig ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--td-text-color-placeholder)' }}
                    >
                      CODEBUDDY_API_KEY
                    </label>
                    <Input
                      type="password"
                      size="small"
                      value={envConfig.apiKey}
                      onChange={(v) => setEnvConfig(prev => ({ ...prev, apiKey: v as string }))}
                      placeholder="API 密钥（推荐）"
                    />
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--td-text-color-placeholder)' }}
                    >
                      CODEBUDDY_AUTH_TOKEN
                    </label>
                    <Input
                      type="password"
                      size="small"
                      value={envConfig.authToken}
                      onChange={(v) => setEnvConfig(prev => ({ ...prev, authToken: v as string }))}
                      placeholder="认证令牌"
                    />
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--td-text-color-placeholder)' }}
                    >
                      CODEBUDDY_INTERNET_ENVIRONMENT
                    </label>
                    <Select
                      size="small"
                      value={envConfig.internetEnv}
                      onChange={(v) => setEnvConfig(prev => ({ ...prev, internetEnv: v as any }))}
                      placeholder="网络环境（可选）"
                      clearable
                      options={[
                        { label: 'internal', value: 'internal' },
                        { label: 'iOA', value: 'iOA' },
                      ]}
                    />
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--td-text-color-placeholder)' }}
                    >
                      CODEBUDDY_BASE_URL
                    </label>
                    <Input
                      size="small"
                      value={envConfig.baseUrl}
                      onChange={(v) => setEnvConfig(prev => ({ ...prev, baseUrl: v as string }))}
                      placeholder="自定义 URL（可选）"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button 
                    size="small"
                    theme="primary" 
                    onClick={saveEnvConfig}
                    loading={savingEnv}
                  >
                    保存
                  </Button>
                  <Button 
                    size="small"
                    variant="text" 
                    onClick={() => {
                      setShowEnvConfig(false);
                      setEnvConfig({ apiKey: '', authToken: '', internetEnv: '', baseUrl: '' });
                    }}
                  >
                    取消
                  </Button>
                  <span 
                    className="text-xs"
                    style={{ color: 'var(--td-text-color-placeholder)' }}
                  >
                    仅当前进程有效
                  </span>
                </div>
              </div>
            ) : (
              <Button 
                variant="outline" 
                size="small"
                onClick={() => setShowEnvConfig(true)}
              >
                配置环境变量
              </Button>
            )}
          </div>
          
          {/* CLI 登录 */}
          <div>
            <h3 
              className="text-sm font-medium mb-3"
              style={{ color: 'var(--td-text-color-secondary)' }}
            >
              方式二：CodeBuddy CLI
            </h3>
            <div className="flex items-center gap-3">
              <code 
                className="px-3 py-1.5 rounded text-sm"
                style={{ 
                  backgroundColor: 'var(--td-bg-color-component)',
                  color: 'var(--td-text-color-primary)'
                }}
              >
                codebuddy
              </code>
              <Link 
                href="https://www.codebuddy.ai/docs/zh/cli/settings" 
                target="_blank"
                theme="primary"
                size="small"
              >
                查看文档
              </Link>
            </div>
          </div>
          
          {loginStatus.error && !loginStatus.isLoggedIn && (
            <div 
              className="text-xs mt-4"
              style={{ color: 'var(--td-text-color-placeholder)' }}
            >
              {loginStatus.error}
            </div>
          )}
        </div>

        <div 
          style={{ 
            height: '1px', 
            backgroundColor: 'var(--td-component-border)' 
          }} 
        />

        {/* Agent 配置 */}
        <div>
          <div className="mb-4">
            <h2 
              className="text-lg font-medium"
              style={{ color: 'var(--td-text-color-primary)' }}
            >
              Agent 配置
            </h2>
            <p 
              className="text-sm mt-1"
              style={{ color: 'var(--td-text-color-secondary)' }}
            >
              创建和管理自定义 Agent
            </p>
          </div>

          <div className="space-y-6">
              {/* 创建/编辑表单 */}
              {isCreating ? (
                <div 
                  className="p-5 rounded-xl border"
                  style={{ 
                    backgroundColor: 'var(--td-bg-color-container)',
                    borderColor: 'var(--td-component-border)'
                  }}
                >
                  <div className="space-y-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-base font-medium" style={{ color: 'var(--td-text-color-primary)' }}>
                        {editingAgent ? '编辑 Agent' : '创建新 Agent'}
                      </h4>
                      <Button variant="text" onClick={resetForm}>取消</Button>
                    </div>
                    
                    <Form labelAlign="top">
                      <Form.FormItem label="名称" requiredMark>
                        <Input 
                          value={formData.name}
                          onChange={(v) => setFormData(prev => ({ ...prev, name: v as string }))}
                          placeholder="例如：代码助手"
                        />
                      </Form.FormItem>
                      
                      <Form.FormItem label="描述">
                        <Input 
                          value={formData.description}
                          onChange={(v) => setFormData(prev => ({ ...prev, description: v as string }))}
                          placeholder="简短描述这个 Agent 的用途"
                        />
                      </Form.FormItem>
                      
                      <Form.FormItem label="图标和颜色">
                        <div className="flex gap-4">
                          <div className="flex gap-2">
                            {PRESET_ICONS.map(({ name, icon: Icon }) => (
                              <button
                                key={name}
                                type="button"
                                className="w-9 h-9 rounded-lg flex items-center justify-center transition-all border-2"
                                style={{
                                  backgroundColor: formData.icon === name ? formData.color : 'transparent',
                                  color: formData.icon === name ? 'white' : 'var(--td-text-color-secondary)',
                                  borderColor: formData.icon === name ? formData.color : 'var(--td-component-border)',
                                }}
                                onClick={() => setFormData(prev => ({ ...prev, icon: name }))}
                              >
                                <Icon size={18} />
                              </button>
                            ))}
                          </div>
                          <div className="flex gap-1.5 items-center">
                            {PRESET_COLORS.map(color => (
                              <button
                                key={color}
                                type="button"
                                className="w-7 h-7 rounded-full flex items-center justify-center transition-transform hover:scale-110"
                                style={{ backgroundColor: color }}
                                onClick={() => setFormData(prev => ({ ...prev, color }))}
                              >
                                {formData.color === color && <CheckIcon style={{ color: 'white' }} size="14px" />}
                              </button>
                            ))}
                          </div>
                        </div>
                      </Form.FormItem>
                      
                      <Form.FormItem label="权限模式">
                        <Select
                          value={formData.permissionMode}
                          onChange={(v) => setFormData(prev => ({ ...prev, permissionMode: v as PermissionMode }))}
                          style={{ width: '100%' }}
                        >
                          {PERMISSION_MODES.map(mode => (
                            <Select.Option key={mode.value} value={mode.value} label={mode.label}>
                              <div className="flex flex-col py-1">
                                <span className="font-mono text-sm" style={{ color: 'var(--td-success-color)' }}>
                                  {mode.label}
                                </span>
                                <span className="text-xs" style={{ color: 'var(--td-text-color-placeholder)' }}>
                                  {mode.description}
                                </span>
                              </div>
                            </Select.Option>
                          ))}
                        </Select>
                      </Form.FormItem>
                      
                      <Form.FormItem label="系统提示词" requiredMark>
                        <Textarea 
                          value={formData.systemPrompt}
                          onChange={(v) => setFormData(prev => ({ ...prev, systemPrompt: v as string }))}
                          placeholder="定义 Agent 的行为和能力..."
                          autosize={{ minRows: 4, maxRows: 8 }}
                        />
                      </Form.FormItem>
                    </Form>
                    
                    <div className="flex justify-end gap-2 pt-2">
                      <Button variant="outline" onClick={resetForm}>取消</Button>
                      <Button theme="primary" onClick={handleSave}>
                        {editingAgent ? '保存修改' : '创建 Agent'}
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {/* 快速模板 */}
                  <div>
                    <h4 className="text-sm font-medium mb-3" style={{ color: 'var(--td-text-color-secondary)' }}>
                      快速创建
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      {PRESET_TEMPLATES.map(template => {
                        const Icon = getIconComponent(template.icon);
                        return (
                          <div 
                            key={template.name} 
                            className="p-3 rounded-lg cursor-pointer transition-all hover:shadow-md"
                            style={{ backgroundColor: 'var(--td-bg-color-component)' }}
                            onClick={() => handleUseTemplate(template)}
                          >
                            <div className="flex items-center gap-3">
                              <div 
                                className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: template.color }}
                              >
                                <Icon size={20} color="white" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium truncate" style={{ color: 'var(--td-text-color-primary)' }}>
                                  {template.name}
                                </div>
                                <div className="text-xs truncate" style={{ color: 'var(--td-text-color-placeholder)' }}>
                                  {template.description}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* 自定义创建按钮 */}
                  <Button 
                    icon={<AddIcon />} 
                    variant="dashed" 
                    block 
                    onClick={() => setIsCreating(true)}
                  >
                    从头创建 Agent
                  </Button>

                  {/* 已有的自定义 Agent */}
                  {customAgents.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-3" style={{ color: 'var(--td-text-color-secondary)' }}>
                        我的 Agent ({customAgents.length})
                      </h4>
                      <div className="space-y-2">
                        {customAgents.map(agent => {
                          const Icon = getIconComponent(agent.icon || 'Bot');
                          return (
                            <div 
                              key={agent.id} 
                              className="p-3 rounded-lg"
                              style={{ backgroundColor: 'var(--td-bg-color-component)' }}
                            >
                              <div className="flex items-center gap-3">
                                <div 
                                  className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                                  style={{ backgroundColor: agent.color || '#0052d9' }}
                                >
                                  <Icon size={20} color="white" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium" style={{ color: 'var(--td-text-color-primary)' }}>
                                    {agent.name}
                                  </div>
                                  <div className="text-xs truncate" style={{ color: 'var(--td-text-color-placeholder)' }}>
                                    {agent.description || agent.systemPrompt.slice(0, 50) + '...'}
                                  </div>
                                </div>
                                <div className="flex gap-1">
                                  <Tooltip content="编辑">
                                    <Button 
                                      variant="text" 
                                      shape="circle" 
                                      size="small"
                                      icon={<EditIcon />}
                                      onClick={() => handleEdit(agent)}
                                    />
                                  </Tooltip>
                                  <Popconfirm
                                    content="确定删除这个 Agent 吗？"
                                    onConfirm={() => handleDelete(agent.id)}
                                  >
                                    <Tooltip content="删除">
                                      <Button 
                                        variant="text" 
                                        shape="circle" 
                                        size="small"
                                        icon={<DeleteIcon />}
                                      />
                                    </Tooltip>
                                  </Popconfirm>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
        </div>
      </div>
    </div>
  );
}
