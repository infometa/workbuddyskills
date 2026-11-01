# 银行回单/流水待办处理流程（code=BANK）

## Step 1：确认本期是否有回单/流水

可先查询本期回单列表作为佐证：

```shell
zijizhang-cli bank get_bank_bill_data_list --uid='<uid>' --date_begin='<本期开始>' --date_end='<本期结束>' --current=1
```

> 若 `data.total` 大于当前页返回条数，需继续翻页（递增 `--current`）直到获取全部数据，再判断是否有回单/流水。

询问用户确认本期是否存在回单/流水，根据回答进入不同分支。

---

## 分支 A：本期确实没有回单/流水

标记本期无流水：

```shell
zijizhang-cli bank set_month_bank_no_water '<year>' '<month>' --uid='<uid>'
```

> 注意：若列表中已有回单/流水记录，不可标记无流水，需走分支 C。

---

## 分支 B：本期有回单/流水，需要上传

### Step B-1：获取银行账号列表，选择对应账号

```shell
zijizhang-cli bank bank_account_number_list --uid='<uid>'
```

从列表中确认回单对应的 `bank_id` 与 `bank_number`，记录对应的 `bank_account_number_id`。

#### 若列表中没有目标账号

1. 获取支持银行列表，拿到目标银行的 `bank_id`：
   ```shell
   zijizhang-cli bank support_bank_list
   ```

2. 添加银行账号：
   ```shell
   zijizhang-cli bank add_bank_account_number --uid='<uid>' --bank_id='<bank_id>' --bank_number='<bank_number>'
   ```

3. 如需删除账号：
   ```shell
   zijizhang-cli bank del_bank_account_number --uid='<uid>' --bank_id='<bank_id>' --bank_number='<bank_number>'
   ```

### Step B-2：上传回单/明细文件

```shell
zijizhang-cli bank upload_bank_file --uid='<uid>' --file='<file>' --file_type='<回单或明细>' --bank_account_number_id='<id>' --billing_cycle='<YYYY-MM-DD>'
```

> 若可通过文件内容自动识别 `bank_id` 与账号并匹配 `bank_account_number_id`，则无需向用户询问。

### Step B-3：查询上传处理状态（异步）

上传为异步处理，可分页查询文件处理状态：

```shell
zijizhang-cli bank bank_file_list --uid='<uid>' --current=1
```

---

## 分支 C：本期已有回单/流水，需要入账

分页查询回单列表，收集所有 `status=待确认` 的回单：

```shell
zijizhang-cli bank get_bank_bill_data_list --uid='<uid>' --date_begin='<本期开始>' --date_end='<本期结束>' --current=1
```

> **分页规则**：返回的 `data.total` 为服务端总条数。若已累计获取的条数 < `data.total`，则递增 `--current` 继续翻页，直到 `data.bill_list` 为空或已累计条数 >= `data.total` 为止。**必须获取所有页后，再统计 `status=待确认` 的条目**，不能只看第一页。

对每条 `status=待确认` 的回单，逐条执行入账：

```shell
zijizhang-cli bank choose_bank_use '<id>' '<rule_text>' --uid='<uid>'
```

> `rule_text` 建议从该回单的 `use_list` 字段中选取，不可自行编造。

> 列表中已有回单/流水时，不可标记无流水。
