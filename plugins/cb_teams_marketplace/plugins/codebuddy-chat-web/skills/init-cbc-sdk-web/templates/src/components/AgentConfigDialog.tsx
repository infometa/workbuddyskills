import { useState } from 'react';
import { 
  Dialog, 
  Form, 
  Input, 
  Textarea, 
  Button, 
  Card,
  Tooltip,
  Popconfirm,
  MessagePlugin
} from 'tdesign-react';
import { 
  AddIcon, 
  EditIcon, 
  DeleteIcon,
  CheckIcon
} from 'tdesign-icons-react';
import { Bot, Sparkles, Code, FileText, Globe, Lightbulb } from 'lucide-react';
import { CustomAgent } from '../types';

interface AgentConfigProps {
  visible: boolean;
  onClose: () => void;
  agents: CustomAgent[];
  onAdd: (agent: Omit<CustomAgent, 'id' | 'createdAt' | 'updatedAt'>) => CustomAgent;
  onUpdate: (id: string, updates: Partial<Omit<CustomAgent, 'id' | 'createdAt'>>) => void;
  onDelete: (id: string) => void;
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

export function AgentConfigDialog({ 
  visible, 
  onClose, 
  agents, 
  onAdd, 
  onUpdate, 
  onDelete 
}: AgentConfigProps) {
  const [editingAgent, setEditingAgent] = useState<CustomAgent | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    systemPrompt: '',
    icon: 'Bot',
    color: '#0052d9',
  });

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      systemPrompt: '',
      icon: 'Bot',
      color: '#0052d9',
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
    <Dialog
      visible={visible}
      onClose={() => { resetForm(); onClose(); }}
      header="Agent 配置"
      width={700}
      footer={null}
      closeOnOverlayClick={false}
    >
      <div className="space-y-6">
        {/* 创建/编辑表单 */}
        {isCreating ? (
          <Card bordered className="p-4">
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-4">
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
                          className="w-9 h-9 rounded-lg flex items-center justify-center transition-all"
                          style={{
                            backgroundColor: formData.icon === name ? formData.color : 'var(--td-bg-color-component)',
                            color: formData.icon === name ? 'white' : 'var(--td-text-color-secondary)',
                          }}
                          onClick={() => setFormData(prev => ({ ...prev, icon: name }))}
                        >
                          <Icon size={18} />
                        </button>
                      ))}
                    </div>
                    <div className="flex gap-1">
                      {PRESET_COLORS.map(color => (
                        <button
                          key={color}
                          type="button"
                          className="w-6 h-6 rounded-full flex items-center justify-center"
                          style={{ backgroundColor: color }}
                          onClick={() => setFormData(prev => ({ ...prev, color }))}
                        >
                          {formData.color === color && <CheckIcon style={{ color: 'white' }} size="14px" />}
                        </button>
                      ))}
                    </div>
                  </div>
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
          </Card>
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
                    <Card 
                      key={template.name} 
                      bordered 
                      hoverShadow
                      className="cursor-pointer transition-all"
                      onClick={() => handleUseTemplate(template)}
                    >
                      <div className="flex items-center gap-3 p-2">
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
                    </Card>
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
                      <Card key={agent.id} bordered className="p-3">
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
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Dialog>
  );
}
