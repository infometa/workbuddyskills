# 场景分析：BUG_ON / NULL 指针 / 异常地址访问

### 必须执行的分析命令

```
run_crash_commands: ["bt -l", "bt -f", "dis -l <fault_function>", "log | grep -i bug", "log | grep -i rip"]

# 检查故障地址
run_crash_commands: ["vm <pid>", "kmem <fault_address>", "rd <stack_area> <length>"]
```

### 排查方向

#### 1. 定位故障代码
- 从 `bt -l` 获取源码行号
- 使用 `dis -l` 反汇编故障函数
- 排查是否是第三方内核模块导致
- 排查是否存在病毒模块
- 结合源码分析触发条件

#### 2. 区分硬件问题与软件问题
- 检查是否有 MCE（Machine Check Exception）记录
- 检查内存错误信息：`log | grep -i mce`、`log | grep -i hardware`
- 如果是硬件问题给出硬件排查建议

#### 3. 内核代码问题
- 分析触发 BUG_ON 的条件在代码中如何被满足
- 尝试从社区找出相关修复 commit
- 使用 `search_knowledge_base` 搜索已知问题

#### 4. 🔴 底层基础设施排查（重要！）

**崩溃可能不是由表面子系统的 bug 引起，而是由更底层的基础设施机制导致。必须识别调用链中涉及的底层机制并逐一排查。**
