# 微云上传协议参考

## 1. 上传流程概览

```
MCP 客户端 (AI Agent)
    │
    │  1. 在本地计算 block_sha_list、check_sha、check_data
    │     （使用 scripts/gen_block_info_list.py 或等价逻辑）
    │
    ├─── 2. 预上传 ──→ weiyun.upload(upload_key="")
    │         │
    │         └── 返回: file_exist(是否秒传), upload_key, channel_list, ex
    │
    ├─── 3. 分片上传 (循环) ──→ weiyun.upload(upload_key="xxx")
    │         │
    │         └── 返回: upload_state(1=继续/2=完成/3=等待), channel_list, ex
    │
    └─── 4. 完成 (upload_state == 2)
```

**关键原则**：哈希计算在**客户端**完成。服务端在预上传阶段不接收原始文件数据用于哈希计算。

## 2. 预上传参数说明

预上传时需要提供以下参数（通过 `weiyun.upload` MCP Tool 传入）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filename | string | **是** | 文件名称 |
| file_size | uint64 | **是** | 文件大小（字节） |
| file_sha | string | **是** | 整个文件的 SHA1（40 字符 hex），必须等于 block_sha_list 最后一个值 |
| file_md5 | string | 否 | 整个文件的 MD5（32 字符 hex），用于秒传校验 |
| block_sha_list | string[] | **是** | 分块 SHA1 列表（每个 40 字符 hex） |
| check_sha | string | **是** | SHA1 校验中间状态（40 字符 hex） |
| check_data | string | 否 | 文件末尾校验字节的 Base64 编码 |
| pdir_key | string | 否 | 上传目标目录 key（不填使用 token 绑定目录） |

### 预上传响应判断

- `file_exist=true` → 秒传成功，上传完毕
- `file_exist=false` → 使用返回的 `upload_key`、`channel_list`、`ex` 进行分片上传

## 3. 分片上传参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| upload_key | string | **是** | 预上传返回的 upload_key |
| channel_list | McpChannelInfo[] | **是** | 预上传返回的通道列表 |
| channel_id | uint32 | **是** | 使用的通道编号 |
| ex | string | **是** | 预上传返回的扩展字段 |
| file_data | bytes | **是** | 分片数据（JSON 传输时为 base64） |
| filename | string | **是** | 文件名称 |

### 上传状态

| 状态码 | 含义 |
|--------|------|
| 1 | 需要上传下一分片 |
| 2 | 上传完成 |
| 3 | 等待其他通道完成 |

## 4. 分块 SHA1 算法 — 详细步骤

### 常量

- `BLOCK_SIZE = 524288`（512KB）

### 文件大小派生变量

```
lastBlockSize = file_size % BLOCK_SIZE
如果 lastBlockSize == 0：lastBlockSize = BLOCK_SIZE

checkBlockSize = lastBlockSize % 128
如果 checkBlockSize == 0：checkBlockSize = 128

beforeBlockSize = file_size - lastBlockSize
```

### 逐步算法

```
sha1 = new SHA1()   // 单个共享的 SHA1 对象

// 第一步：处理最后一块之前的所有块
for offset in range(0, beforeBlockSize, BLOCK_SIZE):
    data = read_file(offset, BLOCK_SIZE)
    sha1.update(data)
    block_sha_list.append(sha1.get_internal_state_little_endian())
    // get_internal_state_little_endian() 返回 h0-h4 以小端序输出的 20 字节 hex 编码

// 第二步：处理最后一块的前半部分，计算 check_sha
between_data = read_file(beforeBlockSize, lastBlockSize - checkBlockSize)
sha1.update(between_data)
check_sha = sha1.get_internal_state_little_endian()

// 第三步：处理文件末尾的 checkBlockSize 字节
check_data_bytes = read_file(file_size - checkBlockSize, checkBlockSize)
sha1.update(check_data_bytes)
file_sha = sha1.hexdigest()  // 标准 SHA1 含 finalization（大端序）
check_data = base64_encode(check_data_bytes)

// 第四步：最后一块的 sha = file_sha（不是内部状态！）
block_sha_list.append(file_sha)
```

### 内部状态提取（get_state）

`get_state()` 函数读取 SHA1 内部寄存器 h0-h4（每个 32 位），以**小端序**字节顺序输出：

```python
result = b""
for h in (h0, h1, h2, h3, h4):
    result += struct.pack("<I", h)  # 小端序 uint32
return result.hex()  # 40 字符 hex 字符串
```

**重要**：调用 `get_state()` 时，已处理的数据长度必须精确对齐到 64 字节边界（SHA1 block 大小）。`BLOCK_SIZE` 为 524288，能被 64 整除，因此所有非最后块都能保证对齐。

## 5. 常见错误码

上传过程中可能遇到的错误码：

| 错误码 | 说明 |
|--------|------|
| -6014 | 空间不足 |
| -20001 | SHA1 校验错误 |
| -44001 | 参数无效 |
| -44003 | 权限不足 |
| -44010 | 文件名过长 |
| -89001 | 分片 SHA 校验失败 |

## 6. 使用建议

### upload_key 和 ex

这两个是预上传返回的不透明字符串，分片上传时**原样传递**，不要额外做编码或解码。

### 推荐使用一键上传脚本

直接使用 `scripts/upload_to_weiyun.py` 可以跳过手动参数计算，一键完成上传：

```bash
python3 scripts/upload_to_weiyun.py /path/to/file --token <mcp_token>
```
