# L0 Parser 契约 (v0.1)

所有产品 parser 必须遵循的输入/输出约定。

## 一、输入

```python
def parse(self, raw_log: str, ocsf_fields: dict | None = None) -> ParseResult:
    ...
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `raw_log` | str | 是 | SOC 导出 xlsx 中 `raw_log` 列的原始字符串 (可能为空) |
| `ocsf_fields` | dict | 否 | SOC 透出的 OCSF 字段 (除 raw_log 外其他列), 用于交叉验证 |

## 二、输出

必须返回 `ParseResult` (定义在 `_base.py`), 包含:

```python
@dataclass
class ParseResult:
    parsed: dict = field(default_factory=dict)       # 结构化字段 (各产品自定义)
    parse_status: str = "ok"                          # "ok" | "partial" | "failed"
    parse_errors: list[str] = field(default_factory=list)  # 字段级错误
    parser_version: str = "0.1.0"
```

### 2.1 parse_status 语义

| 状态 | 含义 | 后续处理 |
|---|---|---|
| `ok` | 完整解析, 关键字段都填了 | 直接进 L1 |
| `partial` | 部分解析, 缺一些字段但还有用 | 进 L1, 但 L1 要用 `parse_errors` 做兜底 |
| `failed` | 解析失败, raw_log 完全不可读 | 跳过, 记日志, 不进 L1 |

### 2.2 parse_errors 规范

- 每条错误是**字段级**的, 描述具体哪个字段解析失败 + 原因
- 错误信息要便于 L1 / 人定位, 例: `"packet hex 解析失败: 非 IPv4 (version=6)"`
- 错误**不阻断** `parsed` 的返回, L0 尽可能多地返回已知字段

## 三、约束

### 3.1 L0 必须做的事

- 解析 raw_log 字符串, 还原出**事实数据** (IP、端口、协议、时间等)
- 从 `ocsf_fields` 提取 SOC 已结构化的字段 (避免重复解析)
- 字段命名遵循 `references/event-schema.md` 的统一 schema
- 处理常见的格式异常 (空字符串、编码错误、字段缺失), 不抛未捕获异常

### 3.2 L0 禁止做的事

- ❌ **不读文件**: 函数只接受字符串, 文件读取由调用方 (l0_parse.py) 做
- ❌ **不写网络**: 离线运行
- ❌ **不做时间归一化**: 时间字段保留字符串原值, L1 决定怎么归一 (但要求附带 raw 原值供 L1 处理)
- ❌ **不做威胁判定**: 不打分、不分类、不关联
- ❌ **不输出业务术语**: 输出的字段名严格遵循 schema, 不带产品特定的"业务标签"

### 3.3 错误处理原则

- **永不抛异常到外层**: `BaseParser.parse()` 内部已 catch 所有异常, 子类可以抛 `ParseError`, 外层会捕获并返回 `parse_status="failed"`
- **raw_log 为空时**: 返回 `parse_status="partial"`, `parse_errors=["raw_log 为空"]`, `parsed` 可填从 OCSF 透出的字段
- **JSON / kv 解析失败时**: 抛 `ParseError`, 由外层统一返回 `failed`

## 四、子类实现模板

```python
from ._base import BaseParser, ParseResult, ParseError


class XxxParser(BaseParser):
    PRODUCT = "xxx"      # 必须小写, 与 xlsx logsource_subtype 一致
    VERSION = "0.1.0"

    def _do_parse(self, raw_log: str, ocsf_fields: dict) -> ParseResult:
        result = ParseResult(parser_version=self.VERSION)
        
        # 1. 处理 raw_log 为空
        if not raw_log or not raw_log.strip():
            result.parse_status = "partial"
            result.parse_errors.append("raw_log 为空")
            # 仍从 OCSF 提取
            result.parsed = self._from_ocsf(ocsf_fields)
            return result
        
        # 2. 主解析逻辑
        try:
            data = self._parse_raw(raw_log)
        except ParseError as e:
            raise  # 让 BaseParser 统一处理
        
        # 3. 与 OCSF 交叉验证
        result.parsed = self._merge(data, ocsf_fields)
        return result

    def _parse_raw(self, raw_log: str) -> dict:
        # 抛 ParseError 表示不可恢复
        ...

    def _from_ocsf(self, ocsf_fields: dict) -> dict:
        # OCSF 透出字段标准化
        ...
```

## 五、注册规范

新 parser 必须到 `registry.py` 注册:

```python
# parsers/registry.py
from .xxx_parser import XxxParser

_REGISTRY = {
    YujieParser.PRODUCT: YujieParser(),
    CwpParser.PRODUCT: CwpParser(),
    XxxParser.PRODUCT: XxxParser(),  # 新增
}
```

**禁止**: parser 自己跑 import-time 注册, 必须在 registry.py 显式列出 (便于依赖追踪)。

## 六、测试规范

每个 parser 应该有单测 (后续补), 至少覆盖:
- 正常 raw_log 输入 → `ok`
- 空 raw_log 输入 → `partial` 或 `failed`
- 格式错误输入 → `failed`
- 关键字段缺失 → `partial`, `parse_errors` 里有说明
- 与 OCSF 字段不一致 → `parse_errors` 里有 warning (可选, 不强制)

## 七、变更记录

| 版本 | 变更 |
|---|---|
| 0.1 | 初版 |
