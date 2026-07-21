/**
 * 云知 Block 操作辅助脚本
 * 简化 MCP 参数构建，支持批量更新和内容重组
 *
 * 使用方式:
 *   import { BlockBuilder, ContentReorganizer } from './block-helper';
 */

// ============ 类型定义 ============

interface TextStyle {
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  strikethrough?: boolean;
  inline_code?: boolean;
  link?: string;
  text_color?: string;
  background_color?: string;
}

interface TextRun {
  content: string;
  text_style?: TextStyle;
}

interface TextElement {
  text_run?: TextRun;
  mention_staff?: { staff_id: string };
  mention_entry?: { entry_id: string };
  mention_date?: { date: string; time?: string };
}

interface BlockStyle {
  align?: 'left' | 'center' | 'right';
  background_color?: string;
  language?: string;
  wrap?: boolean;
}

interface Text {
  elements: TextElement[];
  style?: BlockStyle;
}

type BlockType = 'p' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' |
  'bulleted_list' | 'numbered_list' | 'code' | 'divider' |
  'toggle' | 'callout' | 'task' | 'table' | 'table_cell' |
  'column_list' | 'column' | 'mermaid' | 'plantuml';

interface Block {
  block_id: string;
  block_type: BlockType;
  parent_id?: string;
  children?: string[];
  text?: Text;
  heading1?: Text;
  heading2?: Text;
  heading3?: Text;
  heading4?: Text;
  heading5?: Text;
  bulleted?: Text;
  numbered?: Text;
  code?: Text;
  toggle?: Text;
  callout?: { color: string; icon: string };
  table?: {
    row_size: number;
    column_size: number;
    column_width?: number[];
    header_row?: boolean;
    header_column?: boolean;
  };
  table_cell?: {
    background_color?: string;
    align?: 'left' | 'center' | 'right';
    vertical_align?: 'top' | 'middle' | 'bottom';
    row_span?: number;
    col_span?: number;
  };
  column_list?: { column_size: number };
  column?: { width_ratio: number };
  divider?: Record<string, never>;
  mermaid?: { content: string };
  plantuml?: { content: string };
}

interface UpdateOperation {
  update_text?: {
    text: Text;
  };
  update_style?: {
    style: BlockStyle;
  };
  update_task?: {
    done?: boolean;
    name?: string;
  };
  insert_text?: {
    position: { index: number };
    text: string;
    text_style?: TextStyle;
  };
  delete_text?: {
    range: { start_index: number; end_index: number };
  };
}

// ============ Block 构建器 ============

/**
 * Block 构建器 - 简化块结构的创建
 */
export class BlockBuilder {
  private idCounter: number = 0;
  private blocks: Block[] = [];
  private rootChildren: string[] = [];

  constructor(private prefix: string = 'blk') {}

  /**
   * 生成唯一的临时 ID
   */
  private generateId(): string {
    return `${this.prefix}_${++this.idCounter}`;
  }

  /**
   * 创建文本元素
   */
  static text(content: string, style?: TextStyle): TextElement {
    return {
      text_run: {
        content,
        text_style: style
      }
    };
  }

  /**
   * 创建包含多个元素的 Text 对象
   */
  static textBlock(elements: TextElement[], style?: BlockStyle): Text {
    return { elements, style };
  }

  /**
   * 创建简单文本块
   */
  static simpleText(content: string, style?: TextStyle): Text {
    return {
      elements: [BlockBuilder.text(content, style)]
    };
  }

  /**
   * 添加段落
   */
  paragraph(content: string, style?: TextStyle): string {
    const id = this.generateId();
    this.blocks.push({
      block_id: id,
      block_type: 'p',
      text: BlockBuilder.simpleText(content, style)
    });
    this.rootChildren.push(id);
    return id;
  }

  /**
   * 添加标题
   */
  heading(level: 1 | 2 | 3 | 4 | 5, content: string, style?: TextStyle): string {
    const id = this.generateId();
    const block: Block = {
      block_id: id,
      block_type: `h${level}` as BlockType
    };

    const textField = `heading${level}` as keyof Block;
    (block as any)[textField] = BlockBuilder.simpleText(content, style);

    this.blocks.push(block);
    this.rootChildren.push(id);
    return id;
  }

  /**
   * 添加 Callout 高亮块
   */
  callout(
    color: string,
    icon: string,
    content: string,
    contentStyle?: TextStyle
  ): string {
    const calloutId = this.generateId();
    const contentId = this.generateId();

    // 内容段落
    this.blocks.push({
      block_id: contentId,
      block_type: 'p',
      text: BlockBuilder.simpleText(content, contentStyle)
    });

    // Callout 容器
    this.blocks.push({
      block_id: calloutId,
      block_type: 'callout',
      callout: { color, icon },
      children: [contentId]
    });

    this.rootChildren.push(calloutId);
    return calloutId;
  }

  /**
   * 添加代码块
   */
  codeBlock(code: string, language: string = 'plaintext', wrap: boolean = false): string {
    const id = this.generateId();
    this.blocks.push({
      block_id: id,
      block_type: 'code',
      code: {
        elements: [{ text_run: { content: code } }],
        style: { language, wrap }
      }
    });
    this.rootChildren.push(id);
    return id;
  }

  /**
   * 添加分割线
   */
  divider(): string {
    const id = this.generateId();
    this.blocks.push({
      block_id: id,
      block_type: 'divider',
      divider: {}
    });
    this.rootChildren.push(id);
    return id;
  }

  /**
   * 添加无序列表
   */
  bulletedList(items: string[]): string[] {
    const ids: string[] = [];
    for (const item of items) {
      const id = this.generateId();
      this.blocks.push({
        block_id: id,
        block_type: 'bulleted_list',
        bulleted: BlockBuilder.simpleText(item)
      });
      this.rootChildren.push(id);
      ids.push(id);
    }
    return ids;
  }

  /**
   * 添加有序列表
   */
  numberedList(items: string[]): string[] {
    const ids: string[] = [];
    for (const item of items) {
      const id = this.generateId();
      this.blocks.push({
        block_id: id,
        block_type: 'numbered_list',
        numbered: BlockBuilder.simpleText(item)
      });
      this.rootChildren.push(id);
      ids.push(id);
    }
    return ids;
  }

  /**
   * 添加表格
   */
  table(
    data: string[][],
    options: {
      headerRow?: boolean;
      headerColumn?: boolean;
      columnWidth?: number[];
      headerBgColor?: string;
    } = {}
  ): string {
    const rowSize = data.length;
    const columnSize = data[0]?.length || 0;
    const tableId = this.generateId();
    const cellIds: string[] = [];

    // 创建单元格
    for (let row = 0; row < rowSize; row++) {
      for (let col = 0; col < columnSize; col++) {
        const cellId = this.generateId();
        const contentId = this.generateId();
        const content = data[row][col] || '';

        // 判断是否是表头
        const isHeader = (options.headerRow && row === 0) ||
                        (options.headerColumn && col === 0);

        // 单元格内容
        this.blocks.push({
          block_id: contentId,
          block_type: 'p',
          text: BlockBuilder.simpleText(content, isHeader ? { bold: true } : undefined)
        });

        // 单元格
        const cellBlock: Block = {
          block_id: cellId,
          block_type: 'table_cell',
          table_cell: {},
          children: [contentId]
        };

        if (isHeader && options.headerBgColor) {
          cellBlock.table_cell!.background_color = options.headerBgColor;
        }

        this.blocks.push(cellBlock);
        cellIds.push(cellId);
      }
    }

    // 表格容器
    this.blocks.push({
      block_id: tableId,
      block_type: 'table',
      table: {
        row_size: rowSize,
        column_size: columnSize,
        column_width: options.columnWidth || Array(columnSize).fill(200),
        header_row: options.headerRow,
        header_column: options.headerColumn
      },
      children: cellIds
    });

    this.rootChildren.push(tableId);
    return tableId;
  }

  /**
   * 添加 Mermaid 图表
   */
  mermaid(content: string): string {
    const id = this.generateId();
    this.blocks.push({
      block_id: id,
      block_type: 'mermaid',
      mermaid: { content }
    });
    this.rootChildren.push(id);
    return id;
  }

  /**
   * 构建最终结果
   */
  build(): { descendant: Block[]; children: string[] } {
    return {
      descendant: this.blocks,
      children: this.rootChildren
    };
  }

  /**
   * 生成 MCP 调用参数
   */
  toMCPCall(entryId: string, parentBlockId?: string, index: number = -1): {
    tool: string;
    args: object;
  } {
    const result = this.build();
    return {
      tool: '云知.block_create_block_descendant',
      args: {
        entry_id: entryId,
        parent_block_id: parentBlockId,
        index,
        descendant: result.descendant,
        children: result.children
      }
    };
  }
}

// ============ 批量更新构建器 ============

/**
 * 批量更新构建器
 */
export class UpdateBlocksBuilder {
  private updates: Record<string, UpdateOperation> = {};

  /**
   * 更新文本内容
   */
  updateText(blockId: string, content: string, style?: TextStyle): this {
    this.updates[blockId] = {
      update_text: {
        text: BlockBuilder.simpleText(content, style)
      }
    };
    return this;
  }

  /**
   * 更新块样式
   */
  updateStyle(blockId: string, style: BlockStyle): this {
    this.updates[blockId] = {
      update_style: { style }
    };
    return this;
  }

  /**
   * 更新任务状态
   */
  updateTask(blockId: string, done: boolean, name?: string): this {
    this.updates[blockId] = {
      update_task: { done, name }
    };
    return this;
  }

  /**
   * 插入文本
   */
  insertText(blockId: string, index: number, text: string, style?: TextStyle): this {
    this.updates[blockId] = {
      insert_text: {
        position: { index },
        text,
        text_style: style
      }
    };
    return this;
  }

  /**
   * 删除文本
   */
  deleteText(blockId: string, startIndex: number, endIndex: number): this {
    this.updates[blockId] = {
      delete_text: {
        range: { start_index: startIndex, end_index: endIndex }
      }
    };
    return this;
  }

  /**
   * 生成 MCP 调用参数
   */
  toMCPCall(entryId: string): { tool: string; args: object } {
    return {
      tool: '云知.block_update_blocks',
      args: {
        entry_id: entryId,
        updates: this.updates
      }
    };
  }

  /**
   * 获取更新数量
   */
  count(): number {
    return Object.keys(this.updates).length;
  }
}

// ============ 内容重组器 ============

/**
 * 内容重组器 - 用于调整文档结构
 */
export class ContentReorganizer {
  private moveOperations: Array<{
    blockIds: string[];
    parentBlockId: string;
    after?: string;
  }> = [];

  /**
   * 移动块到新位置
   */
  move(blockIds: string[], parentBlockId: string, after?: string): this {
    this.moveOperations.push({ blockIds, parentBlockId, after });
    return this;
  }

  /**
   * 生成 MCP 调用序列
   */
  toMCPCalls(entryId: string): Array<{ tool: string; args: object }> {
    return this.moveOperations.map(op => ({
      tool: '云知.block_move_blocks',
      args: {
        entry_id: entryId,
        block_ids: op.blockIds,
        parent_block_id: op.parentBlockId,
        after: op.after
      }
    }));
  }
}

// ============ Markdown 转换器 ============

/**
 * Markdown 到 Block 转换器
 */
export class MarkdownToBlocks {
  private builder: BlockBuilder;
  private theme: any;

  constructor(theme?: any) {
    this.builder = new BlockBuilder();
    this.theme = theme;
  }

  /**
   * 解析 Markdown 并生成 Block 结构
   */
  parse(markdown: string): { descendant: Block[]; children: string[] } {
    const lines = markdown.split('\n');
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) {
        i++;
        continue;
      }

      // 标题
      const headingMatch = trimmed.match(/^(#{1,5})\s+(.+)$/);
      if (headingMatch) {
        const level = headingMatch[1].length as 1 | 2 | 3 | 4 | 5;
        this.builder.heading(level, headingMatch[2]);
        i++;
        continue;
      }

      // 代码块
      if (trimmed.startsWith('```')) {
        const lang = trimmed.slice(3).trim() || 'plaintext';
        const codeLines: string[] = [];
        i++;
        while (i < lines.length && !lines[i].trim().startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        this.builder.codeBlock(codeLines.join('\n'), lang);
        i++;
        continue;
      }

      // 引用块 -> Callout
      if (trimmed.startsWith('>')) {
        const content = trimmed.slice(1).trim();
        const calloutType = this.detectCalloutType(content);
        const calloutConfig = this.theme?.callout?.[calloutType] || {
          color: '#E3F2FD',
          icon: '1f4a1'
        };
        this.builder.callout(calloutConfig.color, calloutConfig.icon, content);
        i++;
        continue;
      }

      // 无序列表
      if (trimmed.match(/^[-*+]\s+/)) {
        const items: string[] = [];
        while (i < lines.length && lines[i].trim().match(/^[-*+]\s+/)) {
          items.push(lines[i].trim().replace(/^[-*+]\s+/, ''));
          i++;
        }
        this.builder.bulletedList(items);
        continue;
      }

      // 有序列表
      if (trimmed.match(/^\d+\.\s+/)) {
        const items: string[] = [];
        while (i < lines.length && lines[i].trim().match(/^\d+\.\s+/)) {
          items.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
          i++;
        }
        this.builder.numberedList(items);
        continue;
      }

      // 分割线
      if (trimmed.match(/^[-*_]{3,}$/)) {
        this.builder.divider();
        i++;
        continue;
      }

      // 普通段落
      this.builder.paragraph(trimmed);
      i++;
    }

    return this.builder.build();
  }

  /**
   * 检测 Callout 类型
   */
  private detectCalloutType(content: string): string {
    const mapping = this.theme?.semantic_mapping?.markdown_to_callout || {};
    
    for (const [pattern, type] of Object.entries(mapping)) {
      if (content.startsWith(pattern.replace('> ', ''))) {
        return type as string;
      }
    }

    // 默认映射
    if (content.includes('核心') || content.includes('重要')) return 'primary';
    if (content.includes('提示') || content.includes('建议')) return 'tip';
    if (content.includes('警告') || content.includes('注意')) return 'warning';
    if (content.includes('成功') || content.includes('完成')) return 'success';
    if (content.includes('错误') || content.includes('危险')) return 'error';

    return 'primary';
  }

  /**
   * 生成 MCP 调用
   */
  toMCPCall(entryId: string, markdown: string): { tool: string; args: object } {
    const result = this.parse(markdown);
    return {
      tool: '云知.block_create_block_descendant',
      args: {
        entry_id: entryId,
        descendant: result.descendant,
        children: result.children
      }
    };
  }
}

// ============ 导出 ============

export {
  Block,
  BlockType,
  TextStyle,
  TextRun,
  TextElement,
  Text,
  BlockStyle,
  UpdateOperation
};
