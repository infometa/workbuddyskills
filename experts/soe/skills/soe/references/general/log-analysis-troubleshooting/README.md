# Log Analysis Troubleshooting Skill

日志分析与排查技能，专为处理大型日志文件和软件问题排查设计。

## 核心特性

1. **六步排查法** - 概览 → 时间校验 → 范围定位 → 异常聚类 → 事件链重构 → 根因定位
2. **智能日志分析** - 自动识别日志格式，智能去重压缩，控制 token 消耗
3. **时间范围验证** - 确认目标时间是否在日志覆盖范围内，避免无效搜索
4. **事件链分析** - 追踪进程状态变化，重构问题发生链路
5. **结构化结论输出** - 将分析结果转化为清晰的表格和时间线
6. **日志证据原则** - 所有结论必须有日志证据支撑，严禁臆造

## 架构定位

```
用户提问 → 任务识别 → 深度排查
  路由层         执行层（本技能）
```

本技能是日志分析的**执行层**，可独立使用，也可由上层路由调度。

## 使用场景

- 软件线上故障排查
- 批量异常排查
- 问题复现验证
- 性能瓶颈排查
- 进程状态排查（如 服务异常退出）
- 日志量超限处理

## 快速开始

```bash
# 1. 获取日志概览（必做第一步）
python3 tools/smart_log.py overview --file "/path/to/app.log"

# 2. 验证时间范围
python3 tools/smart_log.py validate --file "/path/to/app.log" --time "15:40"

# 3. 智能搜索（带去重）
python3 tools/smart_log.py search --file "/path/to/app.log" \
  --keyword "error|fail|timeout" --start "15:35" --end "15:45" --dedupe --context 3

# 4. 错误聚类分析
python3 tools/smart_log.py errors --file "/path/to/app.log" --start "15:35" --end "15:45" --top 20

# 5. 时间线分析
python3 tools/smart_log.py timeline --file "/path/to/app.log" --start "15:35" --end "15:45"

# 6. 事件链分析
python3 tools/smart_log.py chain --file "/path/to/app.log" \
  --start "15:35" --end "15:45" --events "start,stop,init,exit,connect,disconnect"

# 7. 追踪特定 ID
python3 tools/smart_log.py trace --file "/path/to/app.log" --trace-id "req-12345" --context 3
```

## 命令参考

| 命令 | 用途 | 典型场景 |
|------|------|----------|
| `overview` | 获取日志概览 | 排查第一步，了解基本情况 |
| `validate` | 时间范围验证 | 确认目标时间是否在日志中 |
| `search` | 智能搜索（支持去重） | 搜索特定关键词/时间段 |
| `errors` | 错误聚类分析 | 了解错误分布，识别主要问题 |
| `timeline` | 时间线分析 | 查看关键事件时序 |
| `chain` | 事件链分析 | 追踪进程启动/停止/状态变化 |
| `trace` | ID 追踪 | 追踪特定请求/会话 |

## 与直接使用 grep/cat 的区别

| 方式 | 输出大小 | Token 消耗 | 智能分析 |
|------|----------|-----------|---------|
| `grep "error" app.log` | 可能 10MB | 爆炸 💥 | ❌ |
| `smart_log.py search --dedupe` | < 10KB | 可控 ✅ | ✅ |

## 详细文档

请参考 [SKILL.md](./SKILL.md)
