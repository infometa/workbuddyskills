# 多租户 SaaS 架构模式

> 基于 Excellent 跨境电商5Agent系统 + 企业ERP多租户实战蒸馏

## 一、多租户隔离模型

### 三种隔离级别

| 隔离级别 | 数据库策略 | 适用场景 | 成本 |
|----------|-----------|----------|------|
| 独立数据库 | 每租户一个DB | 金融/医疗/政企 | 高 |
| 共享数据库独立Schema | 同一DB不同Schema | 中型SaaS | 中 |
| 共享数据库共享Schema | tenant_id字段隔离 | 小型SaaS/MVP | 低 |

### MVP推荐：共享Schema + tenant_id

```sql
-- 每张表都有tenant_id
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    -- 业务字段...
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 强制租户隔离的行级安全策略
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON orders
    USING (tenant_id = current_setting('app.tenant_id')::UUID);
```

## 二、租户管理架构

### 核心数据模型

```
tenants (租户表)
├── id, name, plan, status, created_at
│
├── tenant_members (成员表)
│   ├── tenant_id, user_id, role
│   └── roles: owner / admin / member / viewer
│
├── tenant_configs (配置表)
│   ├── tenant_id, key, value
│   └── 每租户独立配置（功能开关、限额等）
│
└── tenant_usage (用量表)
    ├── tenant_id, metric, value, period
    └── 计费用量追踪
```

### 租户上下文中间件

```typescript
// Express 中间件
async function tenantContext(req, res, next) {
  const tenantId = req.user.tenantId;  // 从JWT提取
  // 注入到数据库会话
  await db.query(`SET app.tenant_id = '${tenantId}'`);
  req.tenant = await getTenantConfig(tenantId);
  next();
}
```

## 三、权限体系

### RBAC + 租户隔离

```
全局角色（跨租户）
├── platform_admin  -- 平台管理员
└── platform_viewer -- 平台观察者

租户角色（租户内）
├── owner    -- 所有者（唯一，可转让）
├── admin    -- 管理员（邀请成员、配置）
├── member   -- 成员（正常使用）
└── viewer   -- 观察者（只读）
```

### 权限感知 API

```
请求 → JWT解析 → 租户ID + 角色 → 权限过滤 → 只返回有权数据
```

- 查询自动注入 tenant_id 过滤
- 写入自动携带 tenant_id
- 管理接口校验 admin 以上角色

## 四、计费模式

### 常见计费维度

| 维度 | 示例 | 实现 |
|------|------|------|
| 按用户数 | 10人以下免费 | tenant_members COUNT |
| 按API调用量 | 每月10万次 | tenant_usage 计数 |
| 按存储量 | 5GB免费 | 文件存储统计 |
| 按功能模块 | 高级分析加收 | tenant_config 功能开关 |
| 混合计费 | 基础+超额 | 综合以上 |

### 用量追踪

```sql
-- 每日用量快照
INSERT INTO tenant_usage (tenant_id, metric, value, period)
SELECT tenant_id, 'api_calls', COUNT(*), CURRENT_DATE
FROM api_logs
WHERE created_at >= CURRENT_DATE
GROUP BY tenant_id;
```

### 限额执行

```typescript
async function checkQuota(tenantId: string, metric: string): Promise<boolean> {
  const config = await getTenantConfig(tenantId);
  const usage = await getCurrentUsage(tenantId, metric);
  const limit = config.limits[metric];
  return usage < limit;
}

// API中间件
if (!await checkQuota(tenantId, 'api_calls')) {
  return res.status(429).json({ error: 'QUOTA_EXCEEDED', upgradeUrl: '/billing' });
}
```

## 五、数据迁移与扩展

### 租户数据导出

```typescript
async function exportTenantData(tenantId: string): Promise<ExportPackage> {
  // 1. 查询所有租户数据
  // 2. 脱敏处理
  // 3. 打包为JSON/CSV
  // 4. 生成下载链接
}
```

### 升级隔离级别

```
共享Schema → 独立Schema
1. 创建新Schema
2. 迁移数据（INSERT INTO new_schema.table SELECT * FROM public.table WHERE tenant_id = ?）
3. 切换连接路由
4. 验证数据一致性
5. 清理旧数据
```

## 六、MVP 快速实现

### 最小多租户（1天可上线）
1. 所有表加 tenant_id 字段
2. JWT携带 tenant_id
3. 查询自动过滤
4. 简单角色区分（admin / member）

### 生产级多租户（1周可上线）
1. Row Level Security
2. 租户配置表
3. 用量追踪
4. 限额执行
5. 数据导出

### 企业级多租户（持续优化）
1. 独立Schema选项
2. 自定义域名
3. SSO集成
4. 审计日志
5. 数据驻留合规
