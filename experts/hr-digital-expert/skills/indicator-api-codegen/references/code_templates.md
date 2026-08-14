# 指标查询接口 - 代码模板

```
API_URL = https://dos-dataview-mcp.woa.com/api/indicator
METHOD  = POST
```

---

## 1. JavaScript - fetch

```javascript
async function queryIndicator(apiCode, queryParams = {}) {
  const response = await fetch('https://dos-dataview-mcp.woa.com/api/indicator', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ apiCode, queryParams }),
  });

  const result = await response.json();

  if (result.code === 0) {
    return result.data;
  } else {
    throw new Error(`指标查询失败 [code=${result.code}]: ${result.message}`);
  }
}

// 使用示例
const data = await queryIndicator('inflow-count-proportion', {
  numeratorParams: { flowInBeginDate: '2025-01-21', flowInEndDate: '2025-03-22', org: ['OA000001'] },
  denominatorParams: { flowInBeginDate: '2025-01-21', flowInEndDate: '2025-03-22', org: ['OA000001'] },
  groupByList: ['org', 'careerLevelName'],
});
```

---

## 2. JavaScript - axios

```javascript
import axios from 'axios';

async function queryIndicator(apiCode, queryParams = {}) {
  const { data: result } = await axios.post(
    'https://dos-dataview-mcp.woa.com/api/indicator',
    { apiCode, queryParams },
    { withCredentials: true }
  );

  if (result.code === 0) {
    return result.data;
  } else {
    throw new Error(`指标查询失败 [code=${result.code}]: ${result.message}`);
  }
}
```

---

## 3. TypeScript - fetch（含类型定义）

```typescript
interface IndicatorResponse<T = Record<string, unknown>> {
  code: number;
  message: string;
  data: T[] | null;
}

interface QueryParams {
  commonParam?: Record<string, unknown>;
  numeratorParams?: Record<string, unknown>;
  denominatorParams?: Record<string, unknown>;
  groupByList?: string[];
}

const API_URL = 'https://dos-dataview-mcp.woa.com/api/indicator';

async function queryIndicator<T = Record<string, unknown>>(
  apiCode: string,
  queryParams: QueryParams = {}
): Promise<T[]> {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ apiCode, queryParams }),
  });

  const result: IndicatorResponse<T> = await response.json();

  if (result.code === 0 && result.data) {
    return result.data;
  } else {
    throw new Error(`指标查询失败 [code=${result.code}]: ${result.message}`);
  }
}

// 使用示例
interface InflowProportionRow {
  org: string;
  careerLevelName: string;
  count: number;
  proportion: number;
}

const rows = await queryIndicator<InflowProportionRow>('inflow-count-proportion', {
  numeratorParams: { flowInBeginDate: '2025-01-21', flowInEndDate: '2025-03-22', org: ['OA000001'] },
  denominatorParams: { flowInBeginDate: '2025-01-21', flowInEndDate: '2025-03-22', org: ['OA000001'] },
  groupByList: ['org', 'careerLevelName'],
});
```

---

## 4. React Hook 封装

```typescript
import { useState, useCallback } from 'react';

interface IndicatorResponse<T = Record<string, unknown>> {
  code: number;
  message: string;
  data: T[] | null;
}

interface QueryParams {
  commonParam?: Record<string, unknown>;
  numeratorParams?: Record<string, unknown>;
  denominatorParams?: Record<string, unknown>;
  groupByList?: string[];
}

const API_URL = 'https://dos-dataview-mcp.woa.com/api/indicator';

function useIndicatorQuery<T = Record<string, unknown>>() {
  const [data, setData] = useState<T[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (apiCode: string, queryParams: QueryParams): Promise<T[]> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ apiCode, queryParams }),
      });
      const result: IndicatorResponse<T> = await response.json();
      if (result.code === 0 && result.data) {
        setData(result.data);
        return result.data;
      }
      throw new Error(`指标查询失败 [code=${result.code}]: ${result.message}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}

export default useIndicatorQuery;
```

---

## 5. Vue 3 Composable 封装

```typescript
import { ref } from 'vue';

interface IndicatorResponse<T = Record<string, unknown>> {
  code: number;
  message: string;
  data: T[] | null;
}

interface QueryParams {
  commonParam?: Record<string, unknown>;
  numeratorParams?: Record<string, unknown>;
  denominatorParams?: Record<string, unknown>;
  groupByList?: string[];
}

const API_URL = 'https://dos-dataview-mcp.woa.com/api/indicator';

export function useIndicatorQuery<T = Record<string, unknown>>() {
  const data = ref<T[] | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function execute(apiCode: string, queryParams: QueryParams): Promise<T[]> {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ apiCode, queryParams }),
      });
      const result: IndicatorResponse<T> = await response.json();
      if (result.code === 0 && result.data) {
        data.value = result.data as any;
        return result.data;
      }
      throw new Error(`指标查询失败 [code=${result.code}]: ${result.message}`);
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function reset() {
    data.value = null;
    error.value = null;
    loading.value = false;
  }

  return { data, loading, error, execute, reset };
}
```
