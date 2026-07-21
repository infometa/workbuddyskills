import { useState, useEffect, useMemo } from 'react';
import { Dialog, Select, Input, Button } from 'tdesign-react';
import { FolderOpenIcon } from 'tdesign-icons-react';
import { Bot, Sparkles, Code, FileText, Globe, Lightbulb } from 'lucide-react';
import { CustomAgent, Model } from '../types';

interface NewChatDialogProps {
  visible: boolean;
  onClose: () => void;
  onConfirm: (agentId: string, model: string, cwd?: string) => void;
  agents: CustomAgent[];
  models: Model[];
  defaultModel: string;
  defaultAgentId?: string;
}

const ICON_MAP: Record<string, React.ComponentType<{ size?: number; color?: string }>> = {
  Bot,
  Sparkles,
  Code,
  FileText,
  Globe,
  Lightbulb,
};

export function NewChatDialog({
  visible,
  onClose,
  onConfirm,
  agents,
  models,
  defaultModel,
  defaultAgentId = 'default',
}: NewChatDialogProps) {
  const [selectedAgentId, setSelectedAgentId] = useState(defaultAgentId);
  const [selectedModel, setSelectedModel] = useState(defaultModel);
  const [cwd, setCwd] = useState('');

  // 计算有效的模型值：确保选择的模型在可用模型列表中
  const effectiveModel = useMemo(() => {
    if (models.length === 0) return '';
    // 如果当前选择的模型在列表中，使用它
    if (selectedModel && models.some(m => m.modelId === selectedModel)) {
      return selectedModel;
    }
    // 否则使用 defaultModel（如果有效）或第一个可用模型
    if (defaultModel && models.some(m => m.modelId === defaultModel)) {
      return defaultModel;
    }
    return models[0]?.modelId || '';
  }, [selectedModel, defaultModel, models]);

  // 当 defaultModel 或 models 变化时，更新 selectedModel
  useEffect(() => {
    if (models.length > 0) {
      // 如果当前选择的模型不在列表中，重置为有效值
      if (!selectedModel || !models.some(m => m.modelId === selectedModel)) {
        const validModel = defaultModel && models.some(m => m.modelId === defaultModel)
          ? defaultModel
          : models[0]?.modelId || '';
        setSelectedModel(validModel);
      }
    }
  }, [defaultModel, models]);

  const handleConfirm = () => {
    onConfirm(selectedAgentId, effectiveModel, cwd || undefined);
    // 重置状态
    setSelectedAgentId(defaultAgentId);
    setSelectedModel(effectiveModel);
    setCwd('');
  };

  const handleClose = () => {
    setSelectedAgentId(defaultAgentId);
    setSelectedModel(effectiveModel);
    setCwd('');
    onClose();
  };

  const selectedAgent = agents.find(a => a.id === selectedAgentId);
  const Icon = ICON_MAP[selectedAgent?.icon || 'Bot'] || Bot;

  return (
    <Dialog
      visible={visible}
      onClose={handleClose}
      header="新建对话"
      width={500}
      confirmBtn={
        <Button theme="primary" onClick={handleConfirm}>
          开始对话
        </Button>
      }
      cancelBtn={
        <Button variant="outline" onClick={handleClose}>
          取消
        </Button>
      }
    >
      <div className="space-y-5 py-2">
        {/* Agent 选择 */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--td-text-color-primary)' }}>
            选择 Agent
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-[240px] overflow-y-auto">
            {agents.map(agent => {
              const AgentIcon = ICON_MAP[agent.icon || 'Bot'] || Bot;
              const isSelected = agent.id === selectedAgentId;
              return (
                <div
                  key={agent.id}
                  className="p-3 rounded-lg cursor-pointer transition-all border-2"
                  style={{
                    borderColor: isSelected ? (agent.color || 'var(--td-brand-color)') : 'transparent',
                    backgroundColor: isSelected ? 'var(--td-brand-color-light)' : 'var(--td-bg-color-component)',
                  }}
                  onClick={() => setSelectedAgentId(agent.id)}
                >
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: agent.color || '#0052d9' }}
                    >
                      <AgentIcon size={16} color="white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate" style={{ color: 'var(--td-text-color-primary)' }}>
                        {agent.name}
                      </div>
                      {agent.description && (
                        <div className="text-xs truncate" style={{ color: 'var(--td-text-color-placeholder)' }}>
                          {agent.description}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 模型选择 */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--td-text-color-primary)' }}>
            选择模型
          </label>
          <Select
            value={effectiveModel}
            onChange={(v) => setSelectedModel(v as string)}
            placeholder="选择模型"
            style={{ width: '100%' }}
            filterable
          >
            {models.map(model => (
              <Select.Option key={model.modelId} value={model.modelId} label={model.name} />
            ))}
          </Select>
        </div>

        {/* 工作目录 */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--td-text-color-primary)' }}>
            工作目录 <span style={{ color: 'var(--td-text-color-placeholder)' }}>(可选)</span>
          </label>
          <Input
            value={cwd}
            onChange={(v) => setCwd(v as string)}
            placeholder="例如：/Users/username/projects/my-app"
            prefixIcon={<FolderOpenIcon />}
          />
          <p className="text-xs mt-1" style={{ color: 'var(--td-text-color-placeholder)' }}>
            指定 Agent 的工作目录，用于文件操作等
          </p>
        </div>

        {/* 选中的 Agent 预览 */}
        {selectedAgent && (
          <div 
            className="p-3 rounded-lg"
            style={{ backgroundColor: 'var(--td-bg-color-component)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div 
                className="w-6 h-6 rounded flex items-center justify-center"
                style={{ backgroundColor: selectedAgent.color || '#0052d9' }}
              >
                <Icon size={14} color="white" />
              </div>
              <span className="text-sm font-medium" style={{ color: 'var(--td-text-color-primary)' }}>
                {selectedAgent.name}
              </span>
            </div>
            <p className="text-xs line-clamp-2" style={{ color: 'var(--td-text-color-secondary)' }}>
              {selectedAgent.systemPrompt}
            </p>
          </div>
        )}
      </div>
    </Dialog>
  );
}
