# FlameGraph 工具安装指南

## 概述

FlameGraph 工具集用于将调用栈数据可视化为火焰图 SVG，主要包含：

- **flamegraph.pl**：把折叠栈转换为 SVG
- **stackcollapse-perf.pl**：把 `perf script` 输出转换为折叠栈

在以下两条路径中都会用到：

- **perf-prof 主路径**：perf-prof 生成折叠栈 → flamegraph.pl 生成 SVG
- **perf 原生回退路径**：perf record → perf script | stackcollapse-perf.pl → flamegraph.pl → SVG

## 前置检查

```bash
which flamegraph.pl && which stackcollapse-perf.pl
```

如果未输出路径，按下面方式安装。

## 安装方法 A：yum（推荐）

```bash
yum install -y flamegraph flamegraph-stackcollapse-perf
```

## 安装方法 B：源码安装（无 yum 包或版本过旧时）

```bash
git clone https://github.com/brendangregg/FlameGraph.git /opt/FlameGraph || \
git clone https://gitee.com/mirrors/FlameGraph.git /opt/FlameGraph

export PATH=$PATH:/opt/FlameGraph
```

## 验证

```bash
which flamegraph.pl && which stackcollapse-perf.pl
```

确保两个命令均能找到路径。

## 常见问题

1. **命令找不到**
   - 确认 PATH 已包含 `/opt/FlameGraph`
   - 重新执行 `export PATH=$PATH:/opt/FlameGraph`

2. **权限问题**
   - 确认当前用户对 `/opt/FlameGraph` 有执行权限

3. **系统无 git**
   - 先安装 git：`yum install -y git`

## 相关路径说明

- **perf-prof 主路径**：只需要 `flamegraph.pl`
- **perf 原生回退路径**：需要 `stackcollapse-perf.pl` + `flamegraph.pl`
