/**
 * 云知 MCP 参数校验和修复工具
 * 用于检查和修复常见的 MCP 调用参数错误
 */

// ============ 类型定义 ============

interface ValidationError {
  field: string;
  message: string;
  suggestion: string;
  severity: 'error' | 'warning';
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  fixedArgs?: object;
}

interface ApplyUploadArgs {
  parent_entry_id?: string;
  name?: string;
  mime_type?: string;
  size?: number;
  file_id?: string;
  upload_type?: string;
}

interface CreateBlockDescendantArgs {
  entry_id?: string;
  parent_block_id?: string;
  descendant?: any[];
  children?: string[];
  index?: number;
}

interface Block {
  block_id?: string;
  block_type?: string;
  children?: string[];
  [key: string]: any;
}

// ============ 常量定义 ============

// 叶子节点类型（不支持 children）
const LEAF_BLOCK_TYPES = new Set([
  'h1', 'h2', 'h3', 'h4', 'h5',
  'code', 'image', 'attachment', 'video',
  'divider', 'mermaid', 'plantuml'
]);

// 容器类型（必须有 children）
const CONTAINER_BLOCK_TYPES = new Set([
  'callout', 'table', 'table_cell',
  'column_list', 'column', 'toggle'
]);

// 块类型到内容字段的映射
const BLOCK_TYPE_TO_FIELD: Record<string, string> = {
  'p': 'text',
  'h1': 'heading1',
  'h2': 'heading2',
  'h3': 'heading3',
  'h4': 'heading4',
  'h5': 'heading5',
  'bulleted_list': 'bulleted',
  'numbered_list': 'numbered',
  'code': 'code',
  'toggle': 'toggle',
  'callout': 'callout',
  'task': 'task',
  'table': 'table',
  'table_cell': 'table_cell',
  'column_list': 'column_list',
  'column': 'column',
  'divider': 'divider',
  'mermaid': 'mermaid',
  'plantuml': 'plantuml'
};

// MIME 类型映射
const EXT_TO_MIME: Record<string, string> = {
  '.md': 'text/markdown',
  '.markdown': 'text/markdown',
  '.txt': 'text/plain',
  '.json': 'application/json',
  '.pdf': 'application/pdf',
  '.doc': 'application/msword',
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  '.xls': 'application/vnd.ms-excel',
  '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml'
};

// ============ 校验器 ============

/**
 * 校验 apply_upload 参数
 */
export function validateApplyUpload(
  args: ApplyUploadArgs,
  context: { isUpdate: boolean; currentEntryId?: string; fileId?: string }
): ValidationResult {
  const errors: ValidationError[] = [];
  const fixedArgs = { ...args };

  // 1. 必填字段检查
  if (!args.parent_entry_id) {
    errors.push({
      field: 'parent_entry_id',
      message: '缺少 parent_entry_id',
      suggestion: context.isUpdate
        ? `更新文件时，parent_entry_id 应填写当前文件的 entry_id: "${context.currentEntryId}"`
        : '新建文件时，parent_entry_id 应填写父目录的 entry_id',
      severity: 'error'
    });
  }

  if (!args.name) {
    errors.push({
      field: 'name',
      message: '缺少文件名 name',
      suggestion: '请提供文件名，包含扩展名，如 "document.md"',
      severity: 'error'
    });
  }

  // 2. ⚠️ 关键：文件大小检查
  if (args.size === undefined || args.size === null) {
    errors.push({
      field: 'size',
      message: '【关键】缺少文件大小 size',
      suggestion: '必须指定文件大小（字节数）。可通过 fs.statSync(path).size 获取',
      severity: 'error'
    });
  } else if (args.size <= 0) {
    errors.push({
      field: 'size',
      message: '文件大小必须大于 0',
      suggestion: `当前值: ${args.size}，请检查文件是否存在或为空`,
      severity: 'error'
    });
  }

  // 3. MIME 类型检查
  if (!args.mime_type && args.name) {
    const ext = args.name.substring(args.name.lastIndexOf('.')).toLowerCase();
    const guessedMime = EXT_TO_MIME[ext];
    if (guessedMime) {
      fixedArgs.mime_type = guessedMime;
      errors.push({
        field: 'mime_type',
        message: '缺少 mime_type，已自动推断',
        suggestion: `根据文件扩展名 "${ext}" 推断为 "${guessedMime}"`,
        severity: 'warning'
      });
    } else {
      fixedArgs.mime_type = 'application/octet-stream';
      errors.push({
        field: 'mime_type',
        message: '缺少 mime_type，使用默认值',
        suggestion: '无法识别的扩展名，使用 "application/octet-stream"',
        severity: 'warning'
      });
    }
  }

  // 4. upload_type 检查
  if (!args.upload_type) {
    fixedArgs.upload_type = 'PRE_SIGNED_URL';
    errors.push({
      field: 'upload_type',
      message: '缺少 upload_type，已自动设置',
      suggestion: '已设置为 "PRE_SIGNED_URL"',
      severity: 'warning'
    });
  }

  // 5. ⚠️ 关键：更新文件时的参数检查
  if (context.isUpdate) {
    if (!args.file_id) {
      errors.push({
        field: 'file_id',
        message: '【关键】更新文件时缺少 file_id',
        suggestion: `更新文件必须提供 file_id。可通过 describe_entry 获取条目详情，返回的 target_id 即为 file_id${context.fileId ? `，当前文件的 file_id 应为: "${context.fileId}"` : ''}`,
        severity: 'error'
      });
    }

    // 检查 parent_entry_id 是否正确（更新时应该是当前文件的 entry_id）
    if (args.parent_entry_id && context.currentEntryId &&
        args.parent_entry_id !== context.currentEntryId) {
      errors.push({
        field: 'parent_entry_id',
        message: '【关键】更新文件时 parent_entry_id 设置错误',
        suggestion: `更新文件时，parent_entry_id 应填写当前文件自己的 entry_id "${context.currentEntryId}"，而不是父目录的 entry_id`,
        severity: 'error'
      });
      fixedArgs.parent_entry_id = context.currentEntryId;
    }
  } else {
    // 新建文件时不应该有 file_id
    if (args.file_id) {
      errors.push({
        field: 'file_id',
        message: '新建文件时不应提供 file_id',
        suggestion: 'file_id 仅在更新已有文件时使用，新建文件请移除此参数',
        severity: 'warning'
      });
      delete fixedArgs.file_id;
    }
  }

  return {
    valid: errors.filter(e => e.severity === 'error').length === 0,
    errors,
    fixedArgs
  };
}

/**
 * 校验 create_block_descendant 参数
 */
export function validateCreateBlockDescendant(args: CreateBlockDescendantArgs): ValidationResult {
  const errors: ValidationError[] = [];
  const fixedArgs = { ...args };
  const fixedDescendant = args.descendant ? [...args.descendant] : [];

  // 1. 必填字段检查
  if (!args.entry_id) {
    errors.push({
      field: 'entry_id',
      message: '缺少 entry_id',
      suggestion: '请提供目标文档的 entry_id',
      severity: 'error'
    });
  }

  if (!args.descendant || args.descendant.length === 0) {
    errors.push({
      field: 'descendant',
      message: '缺少 descendant 数组或数组为空',
      suggestion: 'descendant 必须包含至少一个块定义',
      severity: 'error'
    });
    return { valid: false, errors };
  }

  // 2. 遍历检查每个块
  const blockIds = new Set<string>();
  const childrenRefs = new Set<string>();

  for (let i = 0; i < args.descendant.length; i++) {
    const block = args.descendant[i] as Block;
    const blockPath = `descendant[${i}]`;

    // 2.1 检查 block_id
    if (!block.block_id) {
      errors.push({
        field: `${blockPath}.block_id`,
        message: '块缺少 block_id',
        suggestion: '每个块必须有唯一的 block_id（临时ID），如 "blk_1"',
        severity: 'error'
      });
    } else {
      if (blockIds.has(block.block_id)) {
        errors.push({
          field: `${blockPath}.block_id`,
          message: `block_id "${block.block_id}" 重复`,
          suggestion: '每个块的 block_id 必须唯一',
          severity: 'error'
        });
      }
      blockIds.add(block.block_id);
    }

    // 2.2 检查 block_type
    if (!block.block_type) {
      errors.push({
        field: `${blockPath}.block_type`,
        message: '块缺少 block_type',
        suggestion: '请指定块类型，如 "p", "h1", "callout" 等',
        severity: 'error'
      });
      continue;
    }

    // 2.3 ⚠️ 关键：检查叶子节点是否错误地包含 children
    if (LEAF_BLOCK_TYPES.has(block.block_type) && block.children && block.children.length > 0) {
      errors.push({
        field: `${blockPath}.children`,
        message: `【关键】${block.block_type} 是叶子节点，不能包含 children`,
        suggestion: `标题块 (h1-h5)、代码块 (code)、分割线 (divider)、图表块 (mermaid/plantuml) 等不支持子节点。请移除 children: ${JSON.stringify(block.children)}`,
        severity: 'error'
      });

      // 自动修复：移除 children
      const fixedBlock = { ...fixedDescendant[i] };
      delete fixedBlock.children;
      fixedDescendant[i] = fixedBlock;
    }

    // 2.4 检查容器类型是否缺少 children
    if (CONTAINER_BLOCK_TYPES.has(block.block_type) && (!block.children || block.children.length === 0)) {
      errors.push({
        field: `${blockPath}.children`,
        message: `${block.block_type} 是容器类型，必须指定 children`,
        suggestion: `容器类型块（callout, table, table_cell, column_list, column, toggle）必须包含子块。服务端会自动创建空白子块，但建议显式指定。`,
        severity: 'warning'
      });
    }

    // 2.5 收集 children 引用
    if (block.children) {
      for (const childId of block.children) {
        childrenRefs.add(childId);
      }
    }

    // 2.6 检查内容字段是否正确
    const expectedField = BLOCK_TYPE_TO_FIELD[block.block_type];
    if (expectedField && !block[expectedField]) {
      // 对于需要内容的块类型，检查是否有内容
      if (!CONTAINER_BLOCK_TYPES.has(block.block_type) && block.block_type !== 'divider') {
        errors.push({
          field: `${blockPath}.${expectedField}`,
          message: `${block.block_type} 块缺少内容字段 "${expectedField}"`,
          suggestion: `请添加 "${expectedField}" 字段，参考: { "${expectedField}": { "elements": [{ "text_run": { "content": "文本内容" } }] } }`,
          severity: 'warning'
        });
      }
    }
  }

  // 3. 检查 children 引用的有效性
  for (const childId of childrenRefs) {
    if (!blockIds.has(childId)) {
      errors.push({
        field: 'children',
        message: `children 引用了不存在的 block_id: "${childId}"`,
        suggestion: `确保 "${childId}" 在 descendant 数组中有对应的块定义`,
        severity: 'error'
      });
    }
  }

  // 4. 检查顶层 children
  if (!args.children || args.children.length === 0) {
    // 尝试自动推断顶层 children（非被引用的块）
    const topLevelBlocks = [...blockIds].filter(id => !childrenRefs.has(id));
    if (topLevelBlocks.length > 0) {
      fixedArgs.children = topLevelBlocks;
      errors.push({
        field: 'children',
        message: '缺少顶层 children，已自动推断',
        suggestion: `根据块引用关系，推断顶层块为: ${JSON.stringify(topLevelBlocks)}`,
        severity: 'warning'
      });
    }
  }

  fixedArgs.descendant = fixedDescendant;

  return {
    valid: errors.filter(e => e.severity === 'error').length === 0,
    errors,
    fixedArgs
  };
}

/**
 * 校验 update_blocks 参数
 */
export function validateUpdateBlocks(args: { entry_id?: string; updates?: Record<string, any> }): ValidationResult {
  const errors: ValidationError[] = [];

  if (!args.entry_id) {
    errors.push({
      field: 'entry_id',
      message: '缺少 entry_id',
      suggestion: '请提供目标文档的 entry_id',
      severity: 'error'
    });
  }

  if (!args.updates || Object.keys(args.updates).length === 0) {
    errors.push({
      field: 'updates',
      message: '缺少 updates 或 updates 为空',
      suggestion: 'updates 必须包含至少一个 block_id 到更新操作的映射',
      severity: 'error'
    });
  } else if (Object.keys(args.updates).length > 20) {
    errors.push({
      field: 'updates',
      message: `updates 包含 ${Object.keys(args.updates).length} 个块，超过限制`,
      suggestion: '单次最多更新 20 个块，请分批调用',
      severity: 'error'
    });
  }

  return {
    valid: errors.filter(e => e.severity === 'error').length === 0,
    errors
  };
}

/**
 * 校验 move_blocks 参数
 */
export function validateMoveBlocks(args: {
  entry_id?: string;
  block_ids?: string[];
  parent_block_id?: string;
  after?: string;
}): ValidationResult {
  const errors: ValidationError[] = [];

  if (!args.entry_id) {
    errors.push({
      field: 'entry_id',
      message: '缺少 entry_id',
      suggestion: '请提供目标文档的 entry_id',
      severity: 'error'
    });
  }

  if (!args.block_ids || args.block_ids.length === 0) {
    errors.push({
      field: 'block_ids',
      message: '缺少 block_ids 或数组为空',
      suggestion: 'block_ids 必须包含至少一个要移动的块 ID',
      severity: 'error'
    });
  } else if (args.block_ids.length > 20) {
    errors.push({
      field: 'block_ids',
      message: `block_ids 包含 ${args.block_ids.length} 个块，超过限制`,
      suggestion: '单次最多移动 20 个块，请分批调用',
      severity: 'error'
    });
  }

  if (!args.parent_block_id) {
    errors.push({
      field: 'parent_block_id',
      message: '缺少 parent_block_id',
      suggestion: '请提供目标父节点的 block_id',
      severity: 'error'
    });
  }

  return {
    valid: errors.filter(e => e.severity === 'error').length === 0,
    errors
  };
}

// ============ 辅助函数 ============

/**
 * 格式化校验结果为可读字符串
 */
export function formatValidationResult(result: ValidationResult): string {
  const lines: string[] = [];

  if (result.valid) {
    lines.push('✅ 参数校验通过');
  } else {
    lines.push('❌ 参数校验失败');
  }

  if (result.errors.length > 0) {
    lines.push('');
    lines.push('问题列表:');
    for (const error of result.errors) {
      const icon = error.severity === 'error' ? '🔴' : '🟡';
      lines.push(`${icon} [${error.field}] ${error.message}`);
      lines.push(`   💡 ${error.suggestion}`);
    }
  }

  if (result.fixedArgs) {
    lines.push('');
    lines.push('修复后的参数:');
    lines.push(JSON.stringify(result.fixedArgs, null, 2));
  }

  return lines.join('\n');
}

/**
 * 快速修复 apply_upload 参数
 */
export function fixApplyUploadArgs(
  args: ApplyUploadArgs,
  fileInfo: { path: string; size: number; entryId?: string; fileId?: string }
): ApplyUploadArgs {
  const isUpdate = !!fileInfo.fileId;
  const ext = fileInfo.path.substring(fileInfo.path.lastIndexOf('.')).toLowerCase();
  const fileName = fileInfo.path.substring(fileInfo.path.lastIndexOf('/') + 1);

  return {
    parent_entry_id: isUpdate ? fileInfo.entryId : args.parent_entry_id,
    name: args.name || fileName,
    mime_type: args.mime_type || EXT_TO_MIME[ext] || 'application/octet-stream',
    size: fileInfo.size,
    file_id: isUpdate ? fileInfo.fileId : undefined,
    upload_type: 'PRE_SIGNED_URL'
  };
}

/**
 * 快速修复 create_block_descendant 参数
 * 移除叶子节点的 children，补全容器节点的 children
 */
export function fixCreateBlockDescendantArgs(args: CreateBlockDescendantArgs): CreateBlockDescendantArgs {
  if (!args.descendant) return args;

  const fixedDescendant = args.descendant.map(block => {
    const fixedBlock = { ...block };

    // 移除叶子节点的 children
    if (LEAF_BLOCK_TYPES.has(block.block_type) && fixedBlock.children) {
      delete fixedBlock.children;
    }

    return fixedBlock;
  });

  // 推断顶层 children
  const blockIds = new Set(fixedDescendant.map(b => b.block_id));
  const childrenRefs = new Set<string>();
  for (const block of fixedDescendant) {
    if (block.children) {
      for (const childId of block.children) {
        childrenRefs.add(childId);
      }
    }
  }
  const topLevelBlocks = [...blockIds].filter(id => !childrenRefs.has(id));

  return {
    ...args,
    descendant: fixedDescendant,
    children: args.children && args.children.length > 0 ? args.children : topLevelBlocks
  };
}

// ============ 导出 ============

export {
  ValidationError,
  ValidationResult,
  ApplyUploadArgs,
  CreateBlockDescendantArgs,
  Block,
  LEAF_BLOCK_TYPES,
  CONTAINER_BLOCK_TYPES,
  BLOCK_TYPE_TO_FIELD,
  EXT_TO_MIME
};
