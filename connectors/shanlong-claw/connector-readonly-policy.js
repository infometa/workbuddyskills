const READ_METHODS = new Set(['GET', 'POST', 'LOCAL']);
const DENIED_CATEGORIES = new Set(['action', 'auth']);

const MUTATION_TERMS = [
  'add', 'append', 'apply', 'approve', 'assign', 'audit',
  'activate', 'adjust', 'annul',
  'back', 'bind', 'buy',
  'cancel', 'change', 'check', 'clear', 'close', 'commit', 'confirm', 'connect', 'copy', 'create',
  'calculate', 'complete', 'convert',
  'deactivate', 'deduct', 'dispatch', 'distribute',
  'delay', 'do',
  'del', 'delete', 'disable',
  'edit', 'enable', 'enabel',
  'expire',
  'execute',
  'finish',
  'freeze',
  'generate',
  'grant',
  'import', 'init', 'initialize', 'insert', 'issue',
  'handle',
  'link', 'lock',
  'login', 'logout', 'loss',
  'mark', 'merge', 'move',
  'modify',
  'open',
  'post', 'print', 'process', 'publish', 'purchase', 'push',
  'recharge', 'recover', 'redeem', 'refresh', 'refund', 'reject', 'relate', 'relation', 'release', 'remove', 'renew', 'replace', 'reset', 'restore', 'return', 'revoke', 'run',
  'save', 'sell', 'send', 'set', 'setting', 'sign', 'split', 'start', 'stop', 'submit', 'supplement', 'switch', 'sync',
  'trigger',
  'unbind', 'uncheck', 'unfreeze', 'unlock', 'unlink', 'unsubmit', 'update', 'upgrade', 'upload',
  'void',
  'verify',
  'withdraw',
  'write',
];

const MUTATION_CHINESE = [
  '新增', '创建', '添加', '保存', '修改', '更新', '编辑', '删除', '移除', '清空', '重置',
  '启用', '停用', '发布', '同步', '上传', '导入', '审批', '审核', '驳回', '撤销', '作废',
  '锁定', '解锁', '提交', '反提交', '发放', '授权', '绑定', '解绑', '写入', '开通', '关闭',
  '恢复', '下发', '复制', '关联', '取消关联', '推送', '退回', '回退', '确认', '反审核',
  '新建', '调账', '购买', '售卡', '换卡', '挂失', '退卡', '升级', '延期', '补推', '发券',
  '生成', '初始化', '清除', '充值', '冻结', '解冻', '退款', '作废', '打印',
];

const READ_TERMS = [
  'analysis', 'analyze',
  'count',
  'detail', 'download', 'drop',
  'export',
  'fetch', 'filter', 'find',
  'get',
  'info',
  'list', 'load',
  'option', 'options', 'overview',
  'page', 'preview',
  'query', 'read', 'report', 'retrieve',
  'search', 'select', 'stat', 'statistics', 'summary',
  'state', 'status',
  'tree',
  'view',
];

const READ_CHINESE = [
  '查询', '列表', '详情', '获取', '查看', '读取', '统计', '报表', '分析', '汇总', '概览',
  '预览', '搜索', '检索', '下载', '导出', '选项', '下拉', '树形', '分页', '筛选',
];

function normalizeWords(value) {
  return String(value || '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    .toLowerCase()
    .split(/[^a-z0-9\u3400-\u9fff]+/u)
    .filter(Boolean);
}

function semanticValues(command) {
  return [
    command.action,
    command.name,
    command.description,
    command.description_short,
    command.source_function,
    command.endpoint && command.endpoint.path,
    ...(Array.isArray(command.tags) ? command.tags : []),
  ];
}

function readSignalValues(command) {
  return [
    command.action,
    command.source_function,
    command.endpoint && command.endpoint.path,
  ];
}

function semanticWords(command) {
  return new Set(semanticValues(command).flatMap(normalizeWords));
}

function semanticText(command) {
  return semanticValues(command).map((value) => String(value || '')).join(' ');
}

function findMutation(command) {
  const words = semanticWords(command);
  const term = MUTATION_TERMS.find((candidate) => words.has(candidate));
  if (term) return term;
  const text = semanticText(command);
  return MUTATION_CHINESE.find((candidate) => text.includes(candidate)) || null;
}

function hasReadSignal(command) {
  const words = new Set(readSignalValues(command).flatMap(normalizeWords));
  if (READ_TERMS.some((candidate) => words.has(candidate))) return true;
  const text = readSignalValues(command).map((value) => String(value || '')).join(' ');
  return READ_CHINESE.some((candidate) => text.includes(candidate));
}

function evaluateConnectorReadOnlyCommand(command) {
  if (!command || typeof command !== 'object') {
    return { allowed: false, reason: 'invalid-command' };
  }
  if (command.security_level !== 'S1') {
    return { allowed: false, reason: `security-level:${command.security_level || 'missing'}` };
  }


  const category = String(command.category || '').toLowerCase();
  if (DENIED_CATEGORIES.has(category)) {
    return { allowed: false, reason: `category:${category}` };
  }

  const method = String(command.endpoint && command.endpoint.method || '').toUpperCase();
  if (!READ_METHODS.has(method)) {
    return { allowed: false, reason: `http-method:${method || 'missing'}` };
  }

  const mutation = findMutation(command);
  if (mutation) {
    return { allowed: false, reason: `mutation-semantic:${mutation}` };
  }

  const endpointPath = String(command.endpoint && command.endpoint.path || '');
  const knownReadDispatcher = endpointPath.includes('/external/excByTaskId')
    || endpointPath.startsWith('__cysms_builtin__/');
  if (!knownReadDispatcher && !hasReadSignal(command)) {
    return { allowed: false, reason: `${method.toLowerCase()}-without-read-signal` };
  }

  return { allowed: true, reason: 'read-only' };
}

function isConnectorReadOnlyCommand(command) {
  return evaluateConnectorReadOnlyCommand(command).allowed;
}

module.exports = {
  READ_METHODS,
  evaluateConnectorReadOnlyCommand,
  isConnectorReadOnlyCommand,
};
