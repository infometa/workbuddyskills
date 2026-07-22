// 使用 Aho-Corasick 算法实现多模式匹配（纯 JS / ESM）
class Node {
  constructor() {
    this.children = new Map();
    this.isEnd = false;
    this.output = null;
    this.fail = null;
  }
}

export default class AhoCorasick {
  constructor(options = {}) {
    this.root = new Node();
    this.ignoreCase = options.ignoreCase || false;
  }

  // 添加模式字符串
  addPattern(pattern) {
    // 注意：当ignoreCase=true时，调用者必须确保pattern已转为小写
    let node = this.root;
    for (const char of pattern) {
      if (!node.children.has(char)) {
        node.children.set(char, new Node());
      }
      node = node.children.get(char);
    }
    node.isEnd = true;
    node.output = pattern;
  }

  // 构建失败指针
  buildFailPointers() {
    const queue = [];

    // 第一层节点的失败指针指向根节点
    const rootChildren = Array.from(this.root.children.values());
    for (let i = 0; i < rootChildren.length; i++) {
      const child = rootChildren[i];
      child.fail = this.root;
      queue.push(child);
    }

    while (queue.length > 0) {
      const currentNode = queue.shift();
      const childrenEntries = Array.from(currentNode.children.entries());

      for (let i = 0; i < childrenEntries.length; i++) {
        const [char, child] = childrenEntries[i];

        let failNode = currentNode.fail;

        // 沿着失败指针向上查找，直到找到匹配的子节点或到达根节点
        while (failNode && !failNode.children.has(char)) {
          failNode = failNode.fail;
        }

        if (failNode?.children.has(char)) {
          child.fail = failNode.children.get(char);
        } else {
          child.fail = this.root;
        }

        queue.push(child);
      }
    }
  }

  // 在文本中搜索所有模式匹配
  search(text) {
    const results = [];
    let currentNode = this.root;

    for (let i = 0; i < text.length; i++) {
      let char = text[i];

      // 使用 charCodeAt 进行大小写转换优化
      if (this.ignoreCase) {
        const charCode = text.charCodeAt(i);
        if (charCode >= 65 && charCode <= 90) { // A-Z
          char = String.fromCharCode(charCode + 32); // 转换为小写
        }
      }

      // 如果当前节点没有该字符的子节点，沿着失败指针回溯
      while (currentNode && !currentNode.children.has(char)) {
        currentNode = currentNode.fail;
      }

      if (!currentNode) {
        currentNode = this.root;
        continue;
      }

      currentNode = currentNode.children.get(char);

      // 收集所有匹配的模式
      let tempNode = currentNode;
      while (tempNode) {
        if (tempNode.isEnd) {
          results.push(tempNode.output);
        }
        tempNode = tempNode.fail;
      }
    }

    return results;
  }

  // 在文本中搜索是否存在任意模式匹配
  searchAny(text) {
    let currentNode = this.root;

    for (let i = 0; i < text.length; i++) {
      let char = text[i];

      // 使用 charCodeAt 进行大小写转换优化
      if (this.ignoreCase) {
        const charCode = text.charCodeAt(i);
        if (charCode >= 65 && charCode <= 90) { // A-Z
          char = String.fromCharCode(charCode + 32); // 转换为小写
        }
      }

      // 如果当前节点没有该字符的子节点，沿着失败指针回溯
      while (currentNode && !currentNode.children.has(char)) {
        currentNode = currentNode.fail;
      }

      if (!currentNode) {
        currentNode = this.root;
        continue;
      }

      currentNode = currentNode.children.get(char);

      // 检查当前节点及其失败链上是否有结束节点
      let tempNode = currentNode;
      while (tempNode) {
        if (tempNode.isEnd) {
          return true; // 找到任意匹配立即返回
        }
        tempNode = tempNode.fail;
      }
    }
    return false; // 未找到任何匹配
  }
}
