#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amazon 月度统一交易账单对账脚本

功能：
1. 解析 Amazon MonthlyUnifiedTransaction CSV 账单
2. 提取 type/total 汇总及日期范围
3. 通过 nexus MCP 查询 ERP 订单归属及 Amazon 财务汇总
4. 逐项对比 CSV 与 MCP 财务数据的 type/total
5. 汇总差异时自动分析描述构成并定位订单聚合差异
6. 输出分层对账结果；全费用和显式附加查询尚未启用

用法（占位符替换为实际绝对路径，保留引号）：
    PowerShell：
    & "<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --csv "<CSV绝对路径>"
    POSIX shell：
    "<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --csv "<CSV绝对路径>"
    可选参数：[--mcp-url <服务地址>] [--date-type datetime|transaction] [--output "<输出绝对路径>"]
    环境检查：将 --csv 及其值替换为 --check-env；不读账单、不联网、不安装依赖。
    Skill 根目录取本次加载的 SKILL.md 所在目录；不切换工作目录，用户的相对路径仍相对于调用位置。
"""

import sys

if __name__ == '__main__' and '--check-env' in sys.argv[1:]:
    sys.dont_write_bytecode = True

import argparse
import asyncio
import csv
import io
import json
import math
import re
import shlex
from importlib import import_module, metadata
from pathlib import Path
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from collections import OrderedDict
from urllib.parse import urlsplit

DEFAULT_MCP_URL = 'https://datacenter.eccang.com/nexus/mcp/stream'
DATE_TYPES = {
    'datetime': ('entry', 'Date Time'),
    'transaction': ('settlement', '结算时间'),
}
FINANCE_MCP_ARGUMENTS = frozenset({'companyCode', 'userAccount', 'dateType', 'startTime', 'endTime'})
REQUIRED_MCP_TOOLS = {
    'queryOrderByReferenceNo': {'orderId'},
    'queryFmsTransaction': FINANCE_MCP_ARGUMENTS,
}
# 只声明输入契约；新增接口仅在相应业务阶段启用后调用。
MCP_TOOL_ARGUMENT_TYPES = {
    'queryOrderByReferenceNo': {'orderId': 'string'},
    **{name: dict.fromkeys(FINANCE_MCP_ARGUMENTS, 'string') for name in (
        'queryFmsTransaction', 'queryFmsTransactionDescription', 'queryFmsTransactionCount',
    )},
    'queryFmsTransactionDetail': {
        **dict.fromkeys(FINANCE_MCP_ARGUMENTS, 'string'), 'types': 'array',
    },
    'queryFmsTransactionAllFeeDetail': {
        **dict.fromkeys(FINANCE_MCP_ARGUMENTS, 'string'),
        **dict.fromkeys(('type', 'description', 'amazonOrderId', 'sellerSku', 'warehouseSku'), 'string'),
    },
}


class ReconciliationError(ValueError):
    """输入、MCP 协议或业务结果不满足对账要求。"""


@dataclass(frozen=True)
class EnvironmentCheck:
    name: str
    requirement: str
    version: str
    required: bool = True
    error: str | None = None


def dependency_install_hint():
    """保留虚拟环境解释器路径，不解析其符号链接，也不执行安装命令。"""
    executable = str(Path(sys.executable).absolute())
    requirements = str(Path(__file__).resolve().parent / 'requirements.txt')
    arguments = [executable, '-m', 'pip', 'install', '-r', requirements]
    if sys.platform == 'win32':
        command = '& ' + ' '.join("'" + arg.replace("'", "''") + "'" for arg in arguments)
        shell = 'PowerShell'
    else:
        command = shlex.join(arguments)
        shell = 'POSIX shell'
    return (
        '请先确认目标 Python 环境；如需修复当前环境，仅获用户确认后执行，脚本不会自动安装或升级。\n'
        f'{shell}：{command}'
    )


def dependency_import_error(exc):
    if isinstance(exc, ModuleNotFoundError) and exc.name:
        return f'导入失败：缺少模块 {exc.name}（可能是传递依赖）'
    return f'导入失败（{type(exc).__name__}），请检查依赖安装及二进制兼容性'


def inspect_dependency(name, symbol, requirement, minimum_major=None, maximum_major=None, required=True):
    """核验发布包版本和实际入口；不实例化客户端或工作簿。"""
    version = '未知'
    error = None
    try:
        version = metadata.version(name)
        # 只核验稳定发布版本；预发行或未知版本形式不能冒充已支持环境。
        match = re.fullmatch(r'(\d+)(?:\.\d+)*(?:\.post\d+)?(?:\+[a-zA-Z0-9]+(?:[._-][a-zA-Z0-9]+)*)?', version)
        if not match:
            error = '版本格式无法按稳定发布版本核验'
        elif ((minimum_major is not None and int(match[1]) < minimum_major)
              or (maximum_major is not None and int(match[1]) >= maximum_major)):
            error = f'版本不满足 {requirement}'
        else:
            module = import_module(name)
            if not callable(getattr(module, symbol, None)):
                error = f'缺少可调用入口 {name}.{symbol}'
    except metadata.PackageNotFoundError:
        version = '未安装或元数据缺失'
        error = '当前解释器找不到已安装的发布包'
    except Exception as exc:
        error = dependency_import_error(exc)
    return EnvironmentCheck(name, requirement, version, required, error)


def inspect_environment(include_excel=False, require_excel=False):
    """仅检查本地环境；不加载开发依赖目录，不产生导入字节码缓存。"""
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        version = '.'.join(str(part) for part in sys.version_info[:3])
        python_error = None if sys.version_info[:2] >= (3, 10) else '需要 Python 3.10 或更高版本'
        checks = [EnvironmentCheck('Python', '>=3.10', version, error=python_error)]
        if python_error:
            return checks
        checks.append(inspect_dependency('mcp', 'Client', '>=2,<3', 2, 3))
        checks.append(inspect_dependency('anyio', 'fail_after', '可导入 fail_after'))
        if include_excel or require_excel:
            checks.append(inspect_dependency('openpyxl', 'Workbook', '>=3.0.0', 3, required=require_excel))
        return checks
    finally:
        sys.dont_write_bytecode = previous_bytecode


def require_environment(require_excel=False):
    checks = inspect_environment(require_excel=require_excel)
    failures = [f'{item.name} {item.version}：{item.error}' for item in checks if item.required and item.error]
    if failures:
        raise ReconciliationError('运行环境检查失败：\n' + '\n'.join(failures) + '\n' + dependency_install_hint())


def output_environment_check():
    checks = inspect_environment(include_excel=True)
    print('环境检查：仅检查本地依赖，不读取账单、不连接 MCP、不导出文件。')
    print(f'Python 解释器：{Path(sys.executable).absolute()}')
    for item in checks:
        status = ('失败' if item.required else '可选功能不可用') if item.error else '通过'
        scope = '必需' if item.required else '仅 Excel 导出需要'
        print(f'{item.name}：{item.version} | 要求 {item.requirement} | {scope} | {status}')
        if item.error:
            print(f'  {item.error}')
    if any(item.error for item in checks):
        print(dependency_install_hint())
    failed = any(item.required and item.error for item in checks)
    print('核心环境检查失败。' if failed else '核心环境检查通过；不代表 MCP 网络、权限或业务数据已验证。')
    return 1 if failed else 0


@dataclass(frozen=True)
class QueryContext:
    """本次查询的不可变快照；每个接口获得独立参数副本。"""

    company_code: str
    user_account: str
    platform: str
    date_type: str
    start_time: str
    end_time: str

    def __post_init__(self):
        if self.date_type not in DATE_TYPES:
            raise ReconciliationError('不支持的日期类型')

    @property
    def mcp_date_type(self):
        return DATE_TYPES[self.date_type][0]

    @property
    def date_label(self):
        return f'{DATE_TYPES[self.date_type][1]}（{self.date_type} → {self.mcp_date_type}）'

    def arguments(self):
        return {
            'companyCode': self.company_code,
            'userAccount': self.user_account,
            'dateType': self.mcp_date_type,
            'startTime': self.start_time,
            'endTime': self.end_time,
        }


@dataclass
class DrilldownResult:
    local_status: str = '未执行'
    description_status: str = '未执行'
    order_status: str = '未执行'
    raw_types_by_group: dict = field(default_factory=dict)
    local_records: list = field(default_factory=list)
    local_only_groups: list = field(default_factory=list)
    description_records: list = field(default_factory=list)
    detail_records: list = field(default_factory=list)
    description_comparison: list = field(default_factory=list)
    order_differences: list = field(default_factory=list)
    without_order: list = field(default_factory=list)


@dataclass
class ReconciliationResult:
    """保留原始类型汇总及会话内比较结果，供报告和后续下钻复用。"""

    context: QueryContext
    finance_summary: list
    is_match: bool
    differences: list
    comparison_detail: list
    drilldown: DrilldownResult = field(default_factory=DrilldownResult)
    failure: str | None = None


# ============================================================
# 工具函数
# ============================================================

def convert_fr_date_to_en(date_str):
    """将法语日期转换为英语日期格式：'2 avr. 2026 11:48:46 UTC' -> 'Apr 2, 2026 11:48:46 AM UTC'"""
    for fr, en in FR_MONTH_MAP.items():
        if fr in date_str:
            # 法语格式: "2 avr. 2026 11:48:46 UTC"
            # 英语格式: "Apr 2, 2026 11:48:46 AM UTC"
            date_str = date_str.replace(fr, en)
            # 重新排列："2 Apr 2026 ..." -> "Apr 2, 2026 ..."
            parts = date_str.split()
            if len(parts) >= 3 and parts[0].isdigit():
                day = parts[0]
                month = parts[1]
                year = parts[2]
                rest = ' '.join(parts[3:])
                date_str = f"{month} {day}, {year} {rest}".strip()
            break
    return date_str


def parse_amazon_date(date_str):
    """解析 Amazon CSV 中的日期格式，支持英语、法语和德语"""
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip().strip('"')
    if not date_str:
        return None
    # 检测并转换法语日期
    for fr_month in FR_MONTH_MAP:
        if fr_month in date_str:
            date_str = convert_fr_date_to_en(date_str)
            break
    # 检测并转换葡萄牙语日期："1 de dez. de 2025 07:26:52 GMT-8"
    for pt_month in PT_MONTH_MAP:
        if f' {pt_month} ' in date_str or f' de {pt_month} ' in date_str:
            date_str = date_str.replace(pt_month, PT_MONTH_MAP[pt_month])
            # 去掉 "de" 连接词："1 de Dec de 2025 ..." -> "Dec 1, 2025 ..."
            date_str = date_str.replace(' de ', ' ')
            parts = date_str.split()
            if len(parts) >= 3 and parts[0].isdigit():
                day = parts[0]
                month = parts[1]
                year = parts[2]
                rest = ' '.join(parts[3:])
                date_str = f"{month} {day}, {year} {rest}".strip()
            break
    # 检测并转换意大利语日期："2 gen 2026 14:13:41 UTC"
    for it_month in IT_MONTH_MAP:
        if f' {it_month} ' in date_str or date_str.startswith(f'{it_month} '):
            date_str = date_str.replace(it_month, IT_MONTH_MAP[it_month])
            parts = date_str.split()
            if len(parts) >= 3 and parts[0].isdigit():
                day = parts[0]
                month = parts[1]
                year = parts[2]
                rest = ' '.join(parts[3:])
                date_str = f"{month} {day}, {year} {rest}".strip()
            break
    # 检测并转换西班牙语日期："28 feb 2026 10:26:33 p.m. GMT-8"
    for es_month in ES_MONTH_MAP:
        if f' {es_month} ' in date_str or date_str.startswith(f'{es_month} '):
            date_str = date_str.replace(es_month, ES_MONTH_MAP[es_month])
            # 重新排列："28 Feb 2026 ..." -> "Feb 28, 2026 ..."
            parts = date_str.split()
            if len(parts) >= 3 and parts[0].isdigit():
                day = parts[0]
                month = parts[1]
                year = parts[2]
                rest = ' '.join(parts[3:])
                date_str = f"{month} {day}, {year} {rest}".strip()
            break
    date_str = re.sub(r'\s+(PDT|PST|UTC|GMT|GMT-\d+)$', '', date_str)
    # 处理加拿大/西班牙格式 a.m./p.m. -> AM/PM
    date_str = date_str.replace(' a.m.', ' AM').replace(' p.m.', ' PM')
    # 德语日期格式：DD.MM.YYYY HH:MM:SS
    if re.match(r'^\d{2}\.\d{2}\.\d{4}', date_str):
        try:
            return datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d.%m.%Y')
            except ValueError:
                return None
    # UK 日期格式：DD MMM YYYY HH:MM:SS（如 "1 Nov 2025 00:35:59"）
    if re.match(r'^\d{1,2} [A-Z][a-z]+ \d{4}', date_str):
        try:
            return datetime.strptime(date_str, '%d %b %Y %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d %b %Y')
            except ValueError:
                pass
    try:
        return datetime.strptime(date_str, '%b %d, %Y %I:%M:%S %p')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%b %d, %Y %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%b %d, %Y')
            except ValueError:
                return None


def format_date_start(dt):
    """格式化为起始时间：yyyy-MM-dd 00:00:00"""
    return dt.strftime('%Y-%m-%d') + ' 00:00:00'


def format_date_end(dt):
    """格式化为结束时间：yyyy-MM-dd 23:59:59"""
    return dt.strftime('%Y-%m-%d') + ' 23:59:59'


def round_total(value):
    """四舍五入到2位小数"""
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# 法语 -> 英语 列名映射
FR_TO_EN_COLUMNS = {
    'date/heure': 'date/time',
    'numéro de versement': 'settlement id',
    'type': 'type',
    'numéro de la commande': 'order id',
    'sku': 'sku',
    'description': 'description',
    'quantité': 'quantity',
    'Marketplace': 'marketplace',
    'traitement': 'fulfillment',
    "ville d'où provient la commande": 'order city',
    "Région d'où provient la commande": 'order state',
    'code postal de la commande': 'order postal',
    'Modèle de perception des taxes': 'tax collection model',
    'ventes de produits': 'product sales',
    'Taxes sur la vente des produits': 'product sales tax',
    "crédits d'expédition": 'shipping credits',
    "taxe sur les crédits d'expédition": 'shipping credits tax',
    "crédits sur l'emballage cadeau": 'gift wrap credits',
    'Taxes sur les crédits cadeaux': 'giftwrap credits tax',
    'Rabais promotionnels': 'promotional rebates',
    'Taxes sur les remises promotionnelles': 'promotional rebates tax',
    'Taxes retenues sur le site de vente': 'marketplace withheld tax',
    'frais de vente': 'selling fees',
    'Frais Expédié par Amazon': 'fba fees',
    'autres frais de transaction': 'other transaction fees',
    'autre': 'other',
    'total': 'total',
    'Statut de la transaction': 'Transaction Status',
    'Date de sortie de la transaction': 'Transaction Release Date',
}

# 法语 -> 英语 type 名称映射
FR_TO_EN_TYPE = {
    'Commande': 'Order',
    'Remboursement': 'Refund',
    'Frais de service': 'Service Fee',
    'Frais de stock Expédié par Amazon': 'FBA Inventory Fee',
    'Transfert': 'Transfer',
    'Amazon Fees': 'Amazon Fees',
    'Ajustement': 'Adjustment',
    'Liquidations': 'Liquidations',
    'Services de livraison': 'Shipping Services',
    'Frais de transaction FBA': 'FBA Transaction fees',
    'Ajustement des liquidations': 'Liquidations Adjustments',
    'Commande_Retrocharge': 'Order_Retrocharge',
    'Remboursement_Retrocharge': 'Refund_Retrocharge',
    'Dette': 'Debt',
    'Solde négatif': 'Debt',
    'Autres': 'Others',
    'Ajustement des frais': 'Fee Adjustment',
    'Remboursement de rétrofacturation': 'Chargeback Refund',
    'Frais de Lightning Deal': 'Lightning Deal Fee',
}

# 法语月份缩写映射
FR_MONTH_MAP = {
    'janv.': 'Jan', 'févr.': 'Feb', 'mars': 'Mar', 'avr.': 'Apr',
    'mai': 'May', 'juin': 'Jun', 'juil.': 'Jul', 'août': 'Aug',
    'sept.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'déc.': 'Dec',
}

# 德语 -> 英语 列名映射
DE_TO_EN_COLUMNS = {
    'Datum/Uhrzeit': 'date/time',
    'Abrechnungsnummer': 'settlement id',
    'Typ': 'type',
    'Bestellnummer': 'order id',
    'SKU': 'sku',
    'Beschreibung': 'description',
    'Menge': 'quantity',
    'Marketplace': 'marketplace',
    'Versand': 'fulfillment',
    'Ort der Bestellung': 'order city',
    'Bundesland': 'order state',
    'Postleitzahl': 'order postal',
    'Steuererhebungsmodell': 'tax collection model',
    'Umsätze': 'product sales',
    'Produktumsatzsteuer': 'product sales tax',
    'Gutschrift für Versandkosten': 'shipping credits',
    'Steuer auf Versandgutschrift': 'shipping credits tax',
    'Gutschrift für Geschenkverpackung': 'gift wrap credits',
    'Steuer auf Geschenkverpackungsgutschriften': 'giftwrap credits tax',
    'Rabatte aus Werbeaktionen': 'promotional rebates',
    'Steuer auf Aktionsrabatte': 'promotional rebates tax',
    'Einbehaltene Steuer auf Marketplace': 'marketplace withheld tax',
    'Verkaufsgebühren': 'selling fees',
    'Gebühren zu Versand durch Amazon': 'fba fees',
    'Andere Transaktionsgebühren': 'other transaction fees',
    'Andere': 'other',
    'Gesamt': 'total',
    'Transaktionsstatus': 'Transaction Status',
    'Freigabedatum der Transaktion': 'Transaction Release Date',
}

# 德语 -> 英语 type 名称映射
DE_TO_EN_TYPE = {
    'Bestellung': 'Order',
    'Erstattung': 'Refund',
    'Servicegebühr': 'Service Fee',
    'Versand durch Amazon Lagergebühr': 'FBA Inventory Fee',
    'Übertrag': 'Transfer',
    'Gebühren von Amazon': 'Amazon Fees',
    'Anpassung': 'Adjustment',
    'Liquidationen': 'Liquidations',
    'Versanddienstleistungen': 'Shipping Services',
    'Transaktionsgebühren für Versand durch Amazon': 'FBA Transaction fees',
    'Liquidationsanpassungen': 'Liquidations Adjustments',
    'Bestellung_Wiedereinzug': 'Order_Retrocharge',
    'Erstattung_Wiedereinzug': 'Refund_Retrocharge',
    'Verbindlichkeit': 'Debt',
    'Sonstiges': 'Others',
    'Gebührenanpassung': 'Fee Adjustment',
    'Rückbuchungserstattung': 'Chargeback Refund',
    'Lightning Deal Gebühr': 'Lightning Deal Fee',
}

# 德语月份映射（德语日期格式：01.03.2026 09:17:52 UTC，使用数字月份，不需要月份名映射）
# 德语日期格式：DD.MM.YYYY HH:MM:SS TZ

# 西班牙语 -> 英语 列名映射
ES_TO_EN_COLUMNS = {
    'fecha/hora': 'date/time',
    'Id. de liquidación': 'settlement id',
    'tipo': 'type',
    'Id. del pedido': 'order id',
    'sku': 'sku',
    'descripción': 'description',
    'cantidad': 'quantity',
    'marketplace': 'marketplace',
    'cumplimiento': 'fulfillment',
    'ciudad del pedido': 'order city',
    'estado del pedido': 'order state',
    'código postal del pedido': 'order postal',
    'modelo de recaudación de impuestos': 'tax collection model',
    'ventas de productos': 'product sales',
    'impuesto de ventas de productos': 'product sales tax',
    'créditos de envío': 'shipping credits',
    'impuesto de abono de envío': 'shipping credits tax',
    'créditos por envoltorio de regalo': 'gift wrap credits',
    'impuesto de créditos de envoltura': 'giftwrap credits tax',
    'Tarifa reglamentaria': 'regulatory fee',
    'Impuesto sobre tarifa reglamentaria': 'regulatory fee tax',
    'descuentos promocionales': 'promotional rebates',
    'impuesto de reembolsos promocionales': 'promotional rebates tax',
    'impuesto de retenciones en la plataforma': 'marketplace withheld tax',
    'tarifas de venta': 'selling fees',
    'tarifas fba': 'fba fees',
    'tarifas de otra transacción': 'other transaction fees',
    'otro': 'other',
    'total': 'total',
    'Estado de la transacción': 'Transaction Status',
    'Fecha de liberación de la transacción': 'Transaction Release Date',
}

# 西班牙语 -> 英语 type 名称映射
ES_TO_EN_TYPE = {
    'Pedido': 'Order',
    'Reembolso': 'Refund',
    'Tarifa de servicio': 'Service Fee',
    'Tarifa de inventario en logística de Amazon': 'FBA Inventory Fee',
    'Trasferir': 'Transfer',
    'Tarifas de Amazon': 'Amazon Fees',
    'Ajuste': 'Adjustment',
    'Liquidaciones': 'Liquidations',
    'Servicios de envío': 'Shipping Services',
    'Tarifas de transacción de logística de Amazon': 'FBA Transaction fees',
    'Ajustes de liquidaciones': 'Liquidations Adjustments',
    'Pedido_Retrocargo': 'Order_Retrocharge',
    'Reembolso_Retrocargo': 'Refund_Retrocharge',
    'Deuda': 'Debt',
    'Otros': 'Others',
    'Ajuste de tarifa': 'Fee Adjustment',
    'Reembolso de contracargo': 'Chargeback Refund',
    'Tarifa de oferta del día': 'Lightning Deal Fee',
}

# 西班牙语月份缩写映射
ES_MONTH_MAP = {
    'ene': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'abr': 'Apr',
    'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug',
    'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dic': 'Dec',
}

# 葡萄牙语（巴西） -> 英语 列名映射
PT_TO_EN_COLUMNS = {
    'data/hora': 'date/time',
    'id de liquidação': 'settlement id',
    'tipo': 'type',
    'id do pedido': 'order id',
    'sku': 'sku',
    'descrição': 'description',
    'quantidade': 'quantity',
    'mercado': 'marketplace',
    'tipo de conta': 'account type',
    'atendimento': 'fulfillment',
    'cidade do pedido': 'order city',
    'estado do pedido': 'order state',
    'postal do pedido': 'order postal',
    'vendas do produto': 'product sales',
    'créditos de remessa': 'shipping credits',
    'créditos de embalagem de presente': 'gift wrap credits',
    'descontos promocionais': 'promotional rebates',
    'imposto de vendas coletados': 'marketplace withheld tax',
    'tarifas de venda': 'selling fees',
    'taxas fba': 'fba fees',
    'taxas de outras transações': 'other transaction fees',
    'outro': 'other',
    'total': 'total',
}

# 葡萄牙语（巴西） -> 英语 type 名称映射
PT_TO_EN_TYPE = {
    'Pedido': 'Order',
    'Reembolso': 'Refund',
    'Transferir': 'Transfer',
    'Tarifa de serviço': 'Service Fee',
    'Taxa de inventário FBA': 'FBA Inventory Fee',
    'Taxas da Amazon': 'Amazon Fees',
    'Ajuste': 'Adjustment',
    'Liquidações': 'Liquidations',
    'Serviços de envio': 'Shipping Services',
    'Taxas de transação FBA': 'FBA Transaction fees',
    'Ajustes de liquidações': 'Liquidations Adjustments',
    'Pedido_Retrocobrança': 'Order_Retrocharge',
    'Reembolso_Retrocobrança': 'Refund_Retrocharge',
    'Débito': 'Debt',
    'Outros': 'Others',
    'Ajuste de taxa': 'Fee Adjustment',
    'Reembolso de estorno': 'Chargeback Refund',
    'Taxa de Lightning Deal': 'Lightning Deal Fee',
}

# 葡萄牙语月份缩写映射
PT_MONTH_MAP = {
    'jan.': 'Jan', 'fev.': 'Feb', 'mar.': 'Mar', 'abr.': 'Apr',
    'mai.': 'May', 'jun.': 'Jun', 'jul.': 'Jul', 'ago.': 'Aug',
    'set.': 'Sep', 'out.': 'Oct', 'nov.': 'Nov', 'dez.': 'Dec',
}

# 意大利语 -> 英语 列名映射
IT_TO_EN_COLUMNS = {
    'Data/Ora:': 'date/time',
    'Numero pagamento': 'settlement id',
    'Tipo': 'type',
    'Numero ordine': 'order id',
    'SKU': 'sku',
    'Descrizione': 'description',
    'Quantità': 'quantity',
    'Marketplace': 'marketplace',
    'Gestione': 'fulfillment',
    "Città di provenienza dell'ordine": 'order city',
    "Provincia di provenienza dell'ordine": 'order state',
    "CAP dell'ordine": 'order postal',
    'modello di riscossione delle imposte': 'tax collection model',
    'Vendite': 'product sales',
    'imposta sulle vendite dei prodotti': 'product sales tax',
    'Accrediti per le spedizioni': 'shipping credits',
    'imposta accrediti per le spedizioni': 'shipping credits tax',
    'Accrediti per confezioni regalo': 'gift wrap credits',
    'imposta sui crediti confezione regalo': 'giftwrap credits tax',
    'Sconti promozionali': 'promotional rebates',
    'imposta sugli sconti promozionali': 'promotional rebates tax',
    'trattenuta IVA del marketplace': 'marketplace withheld tax',
    'Commissioni di vendita': 'selling fees',
    'Costi del servizio Logistica di Amazon': 'fba fees',
    'Altri costi relativi alle transazioni': 'other transaction fees',
    'Altro': 'other',
    'totale': 'total',
}

# 意大利语 -> 英语 type 名称映射
IT_TO_EN_TYPE = {
    'Ordine': 'Order',
    'Rimborso': 'Refund',
    'Trasferimento': 'Transfer',
    'Commissione di servizio': 'Service Fee',
    'Costo di stoccaggio Logistica di Amazon': 'FBA Inventory Fee',
    'Tariffe e commissioni Amazon': 'Amazon Fees',
    'Tariffe e commissioni Amazon - Correzione': 'Fee Adjustment',
    'Tariffe e commissioni Amazon - Inversione': 'Amazon Fees',
    'Adeguamento': 'Adjustment',
    'Liquidazioni': 'Liquidations',
    'Servizi di spedizione': 'Shipping Services',
    'Commissioni sulle transazioni di Logistica di Amazon': 'FBA Transaction fees',
    'Rettifiche di liquidazione': 'Liquidations Adjustments',
    'Ordine_Retro-addebito': 'Order_Retrocharge',
    'Rimborso_Retro-addebito': 'Refund_Retrocharge',
    'Debito': 'Debt',
    'Altro': 'Others',
    'Rimborso da chargeback': 'Chargeback Refund',
    'Commissione Lightning Deal': 'Lightning Deal Fee',
}

# 意大利语月份缩写映射
IT_MONTH_MAP = {
    'gen': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
    'mag': 'May', 'giu': 'Jun', 'lug': 'Jul', 'ago': 'Aug',
    'set': 'Sep', 'ott': 'Oct', 'nov': 'Nov', 'dic': 'Dec',
}

# Excel type -> 数据库 type 映射表
EXCEL_TO_DB_TYPE_MAP = {
    'Order': 'payment_order',
    'Refund': 'refund_order',
    'Shipping Services': 'shipping_services',
    'Service Fee': 'service_fee',
    'Amazon Fees': 'coupon',
    'Liquidations': 'liquidation',
    'FBA Inventory Fee': 'fba_inventory_fee',
    'Adjustment': 'adjustment',
    'Order_Retrocharge': 'order_retrocharge',
    'Refund_Retrocharge': 'refund_order',
    'Liquidations Adjustments': 'liquidation_adjustment',
    'FBA Transaction fees': 'fba_transaction_fees',
    'Fulfilment by Amazon (FBA) transaction fees': 'fba_transaction_fees',
    'Chargeback Refund': 'chargeback_refund',
    'Lightning Deal Fee': 'lightning_deal_fee',
    'Transfer': 'transfer',
    'Debt': 'debt',
    'Others': 'others',
    'Fee Adjustment': 'fee_adjustment',
}

# 反向映射：数据库 type -> Excel type（优先使用主映射，跳过合并项）
# Refund_Retrocharge 和 Refund 都映射到 refund_order，反向映射取 Refund
DB_TO_EXCEL_TYPE_MAP = {}
for _k, _v in EXCEL_TO_DB_TYPE_MAP.items():
    if _v not in DB_TO_EXCEL_TYPE_MAP:
        DB_TO_EXCEL_TYPE_MAP[_v] = _k

# 合并映射：将某些 type 的金额合并到目标 type 后再对比
# key: 需要被合并的 Excel type, value: 合并到的目标 Excel type
MERGE_TYPES = {
    'Others': 'Service Fee',
    'Refund_Retrocharge': 'Refund',
    'Lightning Deal Fee': 'Amazon Fees',
}

# 跳过的 type：不参与对账比对（Excel 和数据库都过滤掉）
SKIP_TYPES = {'Transfer', 'transfer'}


# ============================================================
# 第一阶段：解析 CSV 账单
# ============================================================

# 新站点仅接入文档中有依据的候选字段；本地化 Type 仍需真实样本确认。
CANDIDATE_COLUMNS = {
    'ES': {
        'fecha y hora': 'date/time', 'identificador de pago': 'settlement id',
        'tipo': 'type', 'número de pedido': 'order id', 'sku': 'sku',
        'descripción': 'description', 'cantidad': 'quantity', 'web de Amazon': 'marketplace',
        'gestión logística': 'fulfillment', 'ciudad de procedencia del pedido': 'order city',
        'comunidad autónoma de procedencia del pedido': 'order state',
        'código postal de procedencia del pedido': 'order postal',
        'Formulario de recaudación de impuestos': 'tax collection model',
        'ventas de productos': 'product sales', 'impuesto de ventas de productos': 'product sales tax',
        'abonos de envío': 'shipping credits', 'impuestos por abonos de envío': 'shipping credits tax',
        'abonos de envoltorio para regalo': 'gift wrap credits',
        'devoluciones promocionales': 'promotional rebates',
        'impuesto retenido en el sitio web': 'marketplace withheld tax',
        'tarifas de venta': 'selling fees', 'tarifas de Logística de Amazon': 'fba fees',
        'tarifas de otras transacciones': 'other transaction fees', 'otro': 'other', 'total': 'total',
    },
    'NL': {
        'datum/tijd': 'date/time', 'schikkings-ID': 'settlement id', 'type': 'type',
        'bestelnummer': 'order id', 'sku': 'sku', 'beschrijving': 'description',
        'aantal': 'quantity', 'marketplace': 'marketplace', 'fulfillment': 'fulfillment',
        'verkoop van producten': 'product sales', 'Verzendtegoeden': 'shipping credits',
        'kredietpunten cadeauverpakking': 'gift wrap credits', 'verkoopkosten': 'selling fees',
        'fba-vergoedingen': 'fba fees', 'overige transactiekosten': 'other transaction fees',
        'overige': 'other', 'totaal': 'total',
    },
    'SE': {
        'datum/tid': 'date/time', 'reglerings-id': 'settlement id', 'typ': 'type',
        'beställnings-id': 'order id', 'sku': 'sku', 'beskrivning': 'description',
        'antal': 'quantity', 'marknadsplats': 'marketplace', 'leverans': 'fulfillment',
        'försäljning av produkter': 'product sales', 'fraktkrediter': 'shipping credits',
        'krediter för presentinslagning': 'gift wrap credits', 'kampanjrabatter': 'promotional rebates',
        'försäljningsavgifter': 'selling fees', 'fba-avgifter': 'fba fees',
        'övriga transaktionsavgifter': 'other transaction fees', 'Övrigt': 'other', 'totalt': 'total',
    },
    'PL': {
        'data/godzina': 'date/time', 'identyfikator rozliczenia': 'settlement id', 'typ': 'type',
        'identyfikator zamówienia': 'order id', 'sku': 'sku', 'opis': 'description',
        'ilość': 'quantity', 'rynek': 'marketplace', 'realizacja': 'fulfillment',
        'sprzedaż produktów': 'product sales', 'noty kredytowe za wysyłkę': 'shipping credits',
        'rabaty promocyjne': 'promotional rebates', 'opłaty za sprzedaż': 'selling fees',
        'opłaty za fba': 'fba fees', 'inne opłaty transakcyjne': 'other transaction fees',
        'inne': 'other', 'suma': 'total',
    },
    'TR': {
        'tarih/saat': 'date/time', 'hesap kesim no': 'settlement id', 'tip': 'type',
        'sipariş no': 'order id', 'sku': 'sku', 'açıklama': 'description', 'adet': 'quantity',
        'pazar yeri': 'marketplace', 'gönderim': 'fulfillment', 'ürün satışları': 'product sales',
        'kargo kredileri': 'shipping credits', 'promosyon indirimleri': 'promotional rebates',
        'satış ücretleri': 'selling fees', 'Amazon Lojistik ücretleri': 'fba fees',
        'diğer işlem ücretleri': 'other transaction fees', 'diğer': 'other', 'toplam': 'total',
    },
    'JP': {
        '日付/時間': 'date/time', '決済番号': 'settlement id', 'トランザクションの種類': 'type',
        '注文番号': 'order id', 'SKU': 'sku', '説明': 'description', '数量': 'quantity',
        'Amazon 出品サービス': 'marketplace', 'フルフィルメント': 'fulfillment',
        '市町村': 'order city', '都道府県': 'order state', '郵便番号': 'order postal',
        '税金徴収型': 'tax collection model', '商品売上': 'product sales',
        '商品の売上税': 'product sales tax', '配送料': 'shipping credits',
        '配送料の税金': 'shipping credits tax', 'ギフト包装手数料': 'gift wrap credits',
        'ギフト包装クレジットの税金': 'giftwrap credits tax',
        'プロモーション割引額': 'promotional rebates', 'プロモーション割引の税金': 'promotional rebates tax',
        '源泉徴収税を伴うマーケットプレイス': 'marketplace withheld tax', '手数料': 'selling fees',
        'FBA 手数料': 'fba fees', 'トランザクションに関するその他の手数料': 'other transaction fees',
        'その他': 'other', '合計': 'total',
    },
    'BE': {
        'date/heure': 'date/time', 'Identifiant du paiement': 'settlement id', 'type': 'type',
        'Numéro de la commande': 'order id', 'SKU': 'sku', 'description': 'description',
        'quantité': 'quantity', 'site de vente': 'marketplace', 'expédition': 'fulfillment',
        'ventes de produits': 'product sales', 'crédits d’expédition': 'shipping credits',
        'crédits d’emballage-cadeau': 'gift wrap credits', 'Total des réductions': 'promotional rebates',
        'frais de vente': 'selling fees', 'Frais pour le service Expédié par Amazon': 'fba fees',
        'autres frais de transaction': 'other transaction fees', 'autres': 'other', 'total': 'total',
    },
    'AU': {},
}
CANDIDATE_MARKERS = {
    'ES': 'fecha y hora', 'NL': 'datum/tijd', 'SE': 'datum/tid',
    'PL': 'data/godzina', 'TR': 'tarih/saat', 'JP': '日付/時間',
}
CANDIDATE_MONTHS = {
    'ES': 'ene feb mar abr may jun jul ago sep oct nov dic'.split(),
    'NL': 'jan feb mrt apr mei jun jul aug sep okt nov dec'.split(),
    'SE': 'jan feb mars apr maj juni juli aug sep okt nov dec'.split(),
    'PL': 'sty lut mar kwi maj cze lip sie wrz paź lis gru'.split(),
    'TR': 'Oca Şub Mar Nis May Haz Tem Ağu Eyl Eki Kas Ara'.split(),
    'BE': 'janv févr mars avr mai juin juil août sept oct nov déc'.split(),
    'AU': 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(),
}
LEGACY_HEADER_MARKERS = {'date/time', 'date/heure', 'Datum/Uhrzeit', 'fecha/hora', 'data/hora', 'Data/Ora:'}


def candidate_error(site, line, field, reason):
    return ReconciliationError(f'CSV [{site}] 第 {line} 行 {field}：{reason}')


def detect_candidate_site(headers, requested, line):
    """仅凭已配置字段选择解析路径；相互冲突的格式不得回退。"""
    values = set(headers)
    sites = {site for site, marker in CANDIDATE_MARKERS.items() if marker in values}
    old = values & LEGACY_HEADER_MARKERS
    if 'date/heure' in values:
        be = values & {'Identifiant du paiement', 'Numéro de la commande'}
        fr = values & {'numéro de versement', 'numéro de la commande'}
        if be and fr:
            raise candidate_error(requested, line, '表头', 'FR 与 BE 字段冲突')
        if be:
            sites.add('BE')
            old.discard('date/heure')
    if len(sites) > 1 or (sites and old):
        raise candidate_error(requested, line, '表头', '同时包含多种不兼容的站点标识')
    if requested != 'AUTO':
        if sites == {requested} or (requested == 'AU' and old == {'date/time'} and not sites):
            return requested
        raise candidate_error(requested, line, '表头', '与指定站点不兼容，不会回退解析')
    return next(iter(sites)) if sites else None


def parse_candidate_date(raw, site, line, field):
    """按本站完整月份词元解析，不使用跨语言子串替换或系统 locale。"""
    text = raw.strip()
    text = re.sub(r'\s+(?:PDT|PST|UTC|GMT|GMT-[0-9]+)$', '', text)
    text = text.replace(' a.m.', ' AM').replace(' p.m.', ' PM')
    date_parts = None
    if site == 'JP':
        match = re.fullmatch(r'([0-9]{4})/([0-9]{1,2})/([0-9]{1,2})(?:\s+(.+))?', text)
        if match:
            year, month, day, clock = match.groups()
            date_parts = (int(year), int(month), int(day))
    else:
        months = {name.casefold(): n for n, name in enumerate(CANDIDATE_MONTHS[site], 1)}
        if site in {'ES', 'NL', 'SE', 'AU'}:
            months['sept'] = 9
        match = re.fullmatch(r'([0-9]{1,2})\s+([^\s]+)\s+([0-9]{4})(?:\s+(.+))?', text)
        if match:
            day, month, year, clock = match.groups()
        elif site == 'AU':
            match = re.fullmatch(r'([^\s]+)\s+([0-9]{1,2}),\s+([0-9]{4})(?:\s+(.+))?', text)
            if match:
                month, day, year, clock = match.groups()
        if match:
            month_number = months.get(month.removesuffix('.').casefold())
            if month_number:
                date_parts = (int(year), month_number, int(day))
    if date_parts:
        hour = minute = second = 0
        if clock:
            time_match = re.fullmatch(r'([0-9]{1,2}):([0-9]{2}):([0-9]{2})(?: (AM|PM))?', clock)
            if not time_match:
                raise candidate_error(site, line, field, '时间或时区未配置，需原始样本确认')
            h, m, s, ampm = time_match.groups()
            hour, minute, second = int(h), int(m), int(s)
            if ampm:
                if not 1 <= hour <= 12:
                    raise candidate_error(site, line, field, '12 小时制的小时无效')
                hour = hour % 12 + (12 if ampm == 'PM' else 0)
        try:
            return datetime(*date_parts, hour, minute, second)
        except ValueError as exc:
            raise candidate_error(site, line, field, '日期或时间数值无效') from exc
    raise candidate_error(site, line, field, '日期为空或格式未配置，需原始样本确认')


def parse_candidate_amounts(raw_amounts, site, with_format=False):
    """全文件选择唯一数字语法；不按国家推定小数点或静默补零。"""
    alternatives = {'.': [], ',': []}
    for line, raw in raw_amounts:
        valid = {}
        text = raw.strip()
        for decimal, grouping in (('.', ','), (',', '.')):
            d, g = re.escape(decimal), re.escape(grouping)
            pattern = rf'[+-]?(?:[0-9]+|[0-9]{{1,3}}(?:{g}[0-9]{{3}})+)(?:{d}[0-9]+)?'
            if re.fullmatch(pattern, text):
                try:
                    amount = Decimal(text.replace(grouping, '').replace(decimal, '.'))
                    if not amount.is_finite() or not math.isfinite(round_total(amount)):
                        raise InvalidOperation
                    valid[decimal] = amount
                except (InvalidOperation, ValueError, OverflowError):
                    pass
        if not valid:
            raise candidate_error(site, line, 'total', '金额为空、格式不支持或超出范围')
        for key in list(alternatives):
            if key in valid:
                alternatives[key].append(valid[key])
            else:
                del alternatives[key]
        if not alternatives:
            raise candidate_error(site, line, 'total', '全文件金额格式冲突，不能混用小数点规则')
    choices = list(alternatives.values())
    if len(choices) == 2 and choices[0] != choices[1]:
        index = next(i for i, (a, b) in enumerate(zip(*choices)) if a != b)
        raise candidate_error(site, raw_amounts[index][0], 'total', '小数点与千位分隔有歧义，需样本确认')
    # 整数文件可能两种语法均成立；一并保留，后续费用列不能自行猜选。
    return (choices[0], tuple(alternatives)) if with_format else choices[0]


def retained_amount(raw, formats):
    """沿用已选数字语法保存 Decimal；失败留给下钻报告，不改变旧站汇总。"""
    if not isinstance(raw, str) or not raw.strip():
        return None, 'total 缺列或为空'
    values = []
    for decimal in formats:
        grouping = ',' if decimal == '.' else '.'
        d, g = re.escape(decimal), re.escape(grouping)
        pattern = rf'[+-]?(?:[0-9]+|[0-9]{{1,3}}(?:{g}[0-9]{{3}})+)(?:{d}[0-9]+)?'
        if not re.fullmatch(pattern, raw.strip()):
            return None, 'total 不符合已选金额格式'
        try:
            amount = Decimal(raw.strip().replace(grouping, '').replace(decimal, '.'))
            if not amount.is_finite() or not math.isfinite(round_total(amount)):
                raise InvalidOperation
        except (InvalidOperation, ValueError, OverflowError):
            return None, 'total 无效或超出范围'
        values.append(amount)
    if not values or any(value != values[0] for value in values):
        return None, 'total 的金额格式存在歧义'
    return values[0], None


def retain_csv_record(row, raw_fields, line, date, released, amount, formats, amount_error=None):
    """保留原始字段与费用值；不以 SKU 关联订单，不对子集重判数字格式。"""
    return {
        'line_number': line, 'raw_type': raw_fields.get('type'), 'type': row.get('type', '').strip(),
        'order_id': row.get('order id', '').strip() or None,
        'description': row.get('description'), 'description_present': 'description' in row,
        'sku': row.get('sku'), 'quantity': row.get('quantity'), 'marketplace': row.get('marketplace'),
        'dateTimeSite': date, 'postedDateSite': released,
        'total': amount, 'number_format': formats, 'amount_error': amount_error,
        'raw_fields': dict(raw_fields),
    }


def parse_candidate_csv(text, headers, header_line, data_line, site, date_type):
    stream = io.StringIO(text, newline='')
    for _ in range(header_line - 1):
        stream.readline()
    try:
        next(csv.reader(stream, strict=True))
    except csv.Error as exc:
        raise candidate_error(site, header_line, '表头', 'CSV 引号或逗号分隔结构无效') from exc
    columns = [CANDIDATE_COLUMNS[site].get(h, h) for h in headers]
    if len(set(columns)) != len(columns):
        raise candidate_error(site, header_line, '表头', '存在重复列名或映射到同一目标的列')
    missing = {'date/time', 'type', 'order id', 'total'} - set(columns)
    if date_type == 'transaction':
        missing |= {'Transaction Release Date'} - set(columns)
    if missing:
        raise candidate_error(site, header_line, '表头', f'缺少必需列：{", ".join(sorted(missing))}')
    rows, raw_amounts, dates, released_dates, order_ids = [], [], [], [], []
    transaction_records = []
    reader = csv.reader(stream, strict=True)
    line = data_line + 1
    try:
        while True:
            line = data_line + reader.line_num + 1
            cells = next(reader, None)
            if cells is None:
                break
            if not cells or not any(c.strip() for c in cells):
                continue
            if len(cells) != len(columns):
                raise candidate_error(site, line, '记录', '列数与表头不一致')
            row = dict(zip(columns, cells))
            raw_fields = dict(row)
            name = row['type'].strip()
            if name not in EXCEL_TO_DB_TYPE_MAP and name != 'transfer':
                raise candidate_error(site, line, 'type', f'类型为空或未配置：{name[:80]!r}')
            if name == 'Fulfilment by Amazon (FBA) transaction fees':
                name = 'FBA Transaction fees'
            row['type'] = name
            date = parse_candidate_date(row['date/time'], site, line, 'date/time')
            raw_release = row.get('Transaction Release Date', '').strip()
            released = parse_candidate_date(raw_release, site, line, 'Transaction Release Date') if raw_release else None
            if name not in SKIP_TYPES:
                dates.append(date)
                if date_type == 'transaction' and released is None:
                    raise candidate_error(site, line, 'Transaction Release Date', '结算模式不允许非 Transfer 记录缺少释放日期')
                if released is not None:
                    released_dates.append(released)
            if row['order id'].strip():
                order_ids.append(row['order id'].strip())
            raw_amounts.append((line, row['total']))
            rows.append(row)
            transaction_records.append(retain_csv_record(row, raw_fields, line, date, released, None, ()))
    except csv.Error as exc:
        raise candidate_error(site, line, '记录', 'CSV 引号或逗号分隔结构无效') from exc
    if not dates:
        raise candidate_error(site, header_line, '记录', '没有可参与比较的非 Transfer 记录')
    if not order_ids:
        raise candidate_error(site, header_line, 'order id', '整份账单没有有效订单号')
    amounts, number_format = parse_candidate_amounts(raw_amounts, site, with_format=True)
    for record, amount in zip(transaction_records, amounts):
        record.update(total=amount, number_format=number_format)
    totals = OrderedDict()
    try:
        with localcontext() as context:
            context.prec = max(28, max(a.adjusted() for a in amounts)
                               - min(a.as_tuple().exponent for a in amounts) + len(str(len(amounts))) + 4)
            for row, amount in zip(rows, amounts):
                if row['type'] not in SKIP_TYPES:
                    totals[row['type']] = totals.get(row['type'], Decimal('0')) + amount
            total_sum = sum(totals.values(), Decimal('0'))
        summary = [(name, round_total(amount)) for name, amount in totals.items()]
        total_sum = round_total(total_sum)
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise candidate_error(site, raw_amounts[-1][0], 'total', '汇总金额超出范围') from exc
    print(f'   已识别 {site} 受限解析配置；本地化 Type 和实际报告版本仍待样本验收')
    return {
        'rows': rows, 'date_start_time': format_date_start(min(dates)),
        'date_end_time': format_date_end(max(dates)),
        'transaction_start_date': format_date_start(min(released_dates)) if released_dates else None,
        'transaction_end_time': format_date_end(max(released_dates)) if released_dates else None,
        'type_summary': sorted(summary, key=lambda x: abs(x[1]), reverse=True),
        'excel_row_count': len(rows), 'order_ids': order_ids, 'excel_total_sum': total_sum,
        'site': site, 'limited_support': True,
        'transaction_records': transaction_records, 'columns': tuple(columns), 'number_format': number_format,
    }


def parse_csv(csv_path, site='auto', date_type='datetime'):
    """新站点进入严格路径，既有格式保留原解析行为。"""
    requested = site.upper()
    if requested not in {'AUTO', *CANDIDATE_COLUMNS}:
        raise ReconciliationError('不支持的站点配置')
    if date_type not in {'datetime', 'transaction'}:
        raise ReconciliationError('不支持的日期类型')
    utf8 = True
    try:
        with open(csv_path, 'r', encoding='utf-8-sig', newline='') as stream:
            text = stream.read()
    except UnicodeDecodeError as exc:
        if requested != 'AUTO':
            raise candidate_error(requested, 1, '编码', '新增站点仅支持 UTF-8（含 BOM）') from exc
        utf8 = False
        # 此解码仅用于旧表头识别，绝不用于新增站点的数据解析。
        with open(csv_path, 'r', encoding='latin-1', newline='') as stream:
            text = stream.read()
    reader = csv.reader(io.StringIO(text, newline=''))
    header_line = 1
    try:
        for cells in reader:
            headers = [c.strip() for c in cells]
            if headers:
                headers[0] = headers[0].lstrip('\ufeff')
            if set(headers) & (LEGACY_HEADER_MARKERS | set(CANDIDATE_MARKERS.values())):
                selected = detect_candidate_site(headers, requested, header_line)
                if selected:
                    if not utf8:
                        raise candidate_error(selected, header_line, '编码', '新增站点仅支持 UTF-8（含 BOM）')
                    return parse_candidate_csv(text, headers, header_line, reader.line_num, selected, date_type)
                return parse_legacy_csv(csv_path)
            header_line = reader.line_num + 1
    except csv.Error as exc:
        raise candidate_error(requested, header_line, '表头', 'CSV 结构无效') from exc
    raise candidate_error(requested, header_line, '表头', '未识别兼容表头；新增站点仅支持 UTF-8 和逗号分隔 CSV')


def parse_legacy_csv(csv_path):
    """
    解析 Amazon MonthlyUnifiedTransaction CSV 文件
    返回：(rows, date_start_time, date_end_time, transaction_start_date, transaction_end_time, type_summary, excel_row_count)
    """
    rows = []
    metadata = []
    transaction_records = []
    all_dates = []
    all_transaction_dates = []
    order_ids = []

    # 尝试多种编码打开CSV（utf-8-sig 优先，避免 BOM 干扰表头检测）
    encoding = 'utf-8-sig'
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'gbk', 'cp1252'):
        try:
            with open(csv_path, 'r', encoding=enc) as f:
                f.read()
            encoding = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    is_french = False
    is_german = False
    is_spanish = False
    is_portuguese = False
    is_italian = False

    # 已知的表头标识列（用于自动检测表头行）
    HEADER_MARKERS = {'date/time', 'date/heure', 'Datum/Uhrzeit', 'fecha/hora', 'data/hora', 'Data/Ora:'}

    headers = None
    with open(csv_path, 'r', encoding=encoding) as f:
        reader = csv.reader(f)
        next_line = 1
        for row in reader:
            line, next_line = next_line, reader.line_num + 1
            if not row or len(row) < 2:
                continue
            # 自动检测表头行：任意单元格匹配已知列名
            if headers is None:
                row_lower = [c.strip() for c in row]
                if any(marker in row_lower for marker in HEADER_MARKERS):
                    headers = row
                    # 检测是否为法语列名
                    if 'date/heure' in headers:
                        is_french = True
                        headers = [FR_TO_EN_COLUMNS.get(h.strip(), h.strip()) for h in headers]
                    # 检测是否为德语列名
                    elif 'Datum/Uhrzeit' in headers:
                        is_german = True
                        headers = [DE_TO_EN_COLUMNS.get(h.strip(), h.strip()) for h in headers]
                    # 检测是否为西班牙语列名
                    elif 'fecha/hora' in headers:
                        is_spanish = True
                        headers = [ES_TO_EN_COLUMNS.get(h.strip(), h.strip()) for h in headers]
                    # 检测是否为葡萄牙语列名
                    elif 'data/hora' in headers:
                        is_portuguese = True
                        headers = [PT_TO_EN_COLUMNS.get(h.strip(), h.strip()) for h in headers]
                    # 检测是否为意大利语列名
                    elif 'Data/Ora:' in headers:
                        is_italian = True
                        headers = [IT_TO_EN_COLUMNS.get(h.strip(), h.strip()) for h in headers]
                    continue
                # 也兼容英文表头
                elif 'date/time' in row_lower:
                    headers = row
                    continue
                continue
            rows.append(dict(zip(headers, row)))
            metadata.append({'line': line, 'raw_fields': dict(rows[-1]),
                             'valid_shape': len(row) == len(headers) and len(set(headers)) == len(headers)})

    if is_french:
        print("   🇫🇷 检测到法语 CSV，已自动转换列名和类型为英文")
    elif is_german:
        print("   🇩🇪 检测到德语 CSV，已自动转换列名和类型为英文")
    elif is_spanish:
        print("   🇪🇸 检测到西班牙语 CSV，已自动转换列名和类型为英文")
    elif is_portuguese:
        print("   🇧🇷 检测到葡萄牙语 CSV，已自动转换列名和类型为英文")
    elif is_italian:
        print("   🇮🇹 检测到意大利语 CSV，已自动转换列名和类型为英文")

    excel_row_count = len(rows)

    for row, meta in zip(rows, metadata):
        # 法语 type 转英文
        if is_french and row.get('type', ''):
            row['type'] = FR_TO_EN_TYPE.get(row['type'].strip(), row['type'].strip())
        # 德语 type 转英文
        elif is_german and row.get('type', ''):
            row['type'] = DE_TO_EN_TYPE.get(row['type'].strip(), row['type'].strip())
        # 西班牙语 type 转英文
        elif is_spanish and row.get('type', ''):
            row['type'] = ES_TO_EN_TYPE.get(row['type'].strip(), row['type'].strip())
        # 葡萄牙语 type 转英文
        elif is_portuguese and row.get('type', ''):
            row['type'] = PT_TO_EN_TYPE.get(row['type'].strip(), row['type'].strip())
        # 意大利语 type 转英文
        elif is_italian and row.get('type', ''):
            row['type'] = IT_TO_EN_TYPE.get(row['type'].strip(), row['type'].strip())

        dt = parse_amazon_date(row.get('date/time', ''))
        if dt:
            all_dates.append(dt)

        trd = parse_amazon_date(row.get('Transaction Release Date', ''))
        if trd:
            all_transaction_dates.append(trd)
        meta.update(date=dt, released=trd)

        oid = row.get('order id', '').strip()
        if oid:
            order_ids.append(oid)

    date_start_time = format_date_start(min(all_dates)) if all_dates else None
    date_end_time = format_date_end(max(all_dates)) if all_dates else None
    transaction_start_date = format_date_start(min(all_transaction_dates)) if all_transaction_dates else None
    transaction_end_time = format_date_end(max(all_transaction_dates)) if all_transaction_dates else None

    type_totals = {}
    number_format = (',' if is_french or is_german or is_portuguese or is_italian else '.',)
    for row, meta in zip(rows, metadata):
        t = row.get('type', '').strip()
        total_raw = row.get('total', '0').strip()
        # 法语/德语/葡萄牙语/意大利语CSV用逗号做小数点（如 "17,54" / "-8.873,00" / "-387,70"），英语/西班牙语CSV用点做小数点
        if is_french or is_german or is_portuguese or is_italian:
            total_str = total_raw.replace('.', '').replace(',', '.')
        else:
            total_str = total_raw.replace(',', '')
        try:
            total_val = float(total_str) if total_str else 0.0
        except ValueError:
            total_val = 0.0
        if t:
            type_totals[t] = type_totals.get(t, 0.0) + total_val
        amount, error = retained_amount(row.get('total'), number_format)
        if not meta['valid_shape']:
            error = '记录列数不一致或表头存在重复列，不能可靠定位'
        transaction_records.append(retain_csv_record(
            row, meta['raw_fields'], meta['line'], meta['date'], meta['released'], amount, number_format, error,
        ))

    type_summary = []
    for t, v in type_totals.items():
        # 跳过 Transfer 类型
        if t in SKIP_TYPES:
            continue
        type_summary.append((t, round_total(v)))

    type_summary.sort(key=lambda x: abs(x[1]), reverse=True)

    return {
        'rows': rows,
        'date_start_time': date_start_time,
        'date_end_time': date_end_time,
        'transaction_start_date': transaction_start_date,
        'transaction_end_time': transaction_end_time,
        'type_summary': type_summary,
        'excel_row_count': excel_row_count,
        'order_ids': order_ids,
        'excel_total_sum': round_total(sum(v for t, v in type_totals.items() if t not in SKIP_TYPES)),
        'transaction_records': transaction_records, 'columns': tuple(headers or ()), 'number_format': number_format,
    }


# ============================================================
# 第二阶段：MCP 会话与结果适配
# ============================================================

@asynccontextmanager
async def mcp_connection(url, timeout):
    """在同一任务中打开和关闭 SDK 会话，避免跨任务退出取消作用域。"""
    try:
        from anyio import fail_after
        from mcp import Client
    except Exception as exc:
        raise ReconciliationError(f'MCP 依赖{dependency_import_error(exc)}\n{dependency_install_hint()}') from exc
    try:
        with fail_after(timeout) as startup:
            async with Client(url, read_timeout_seconds=timeout) as client:
                startup.deadline = math.inf
                yield client
    except ReconciliationError:
        raise
    except TimeoutError as exc:
        raise ReconciliationError('MCP 连接或初始化超时') from exc
    except Exception as exc:
        raise ReconciliationError(
            f'MCP 会话失败（{type(exc).__name__}），请检查服务地址、网络和访问权限'
        ) from exc


async def mcp_request(operation, timeout, label):
    """限制单次请求耗时；不将服务异常或响应正文误判为无数据。"""
    try:
        return await asyncio.wait_for(operation, timeout=timeout)
    except (TimeoutError, asyncio.TimeoutError) as exc:
        raise ReconciliationError(f'MCP {label} 超时') from exc
    except Exception as exc:
        raise ReconciliationError(f'MCP {label} 请求失败（{type(exc).__name__}）') from exc


async def validate_mcp_tools(client, timeout):
    tools = {}
    cursor = None
    seen_cursors = set()
    for _ in range(100):
        page = await mcp_request(client.list_tools(cursor=cursor), timeout, '工具发现')
        tools.update((tool.name, tool) for tool in page.tools)
        cursor = page.next_cursor
        if cursor is None:
            break
        if cursor in seen_cursors:
            raise ReconciliationError('MCP 工具清单出现重复分页游标')
        seen_cursors.add(cursor)
    else:
        raise ReconciliationError('MCP 工具清单超过分页限制')
    for name, arguments in REQUIRED_MCP_TOOLS.items():
        validate_mcp_tool(tools, name, arguments)
    return tools


def validate_mcp_tool(tools, name, argument_names):
    """使用已发现的清单，仅检查本次调用涉及的接口和参数。"""
    if name not in MCP_TOOL_ARGUMENT_TYPES:
        raise ReconciliationError(f'未配置 MCP 工具契约：{name}')
    if name not in tools:
        raise ReconciliationError(f'MCP 缺少必需工具：{name}')
    schema = tools[name].input_schema
    arguments = set(argument_names)
    expected = MCP_TOOL_ARGUMENT_TYPES[name]
    if not isinstance(schema, dict):
        raise ReconciliationError(f'MCP 工具参数结构不兼容：{name}')
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    if (schema.get('type') != 'object' or not isinstance(properties, dict)
            or not isinstance(required, list) or any(not isinstance(key, str) for key in required)
            or not arguments.issubset(expected) or not arguments.issubset(properties)
            or not set(required).issubset(arguments)):
        raise ReconciliationError(f'MCP 工具参数结构不兼容：{name}')
    for key in arguments:
        definition = properties[key]
        if not isinstance(definition, dict) or definition.get('type') != expected[key]:
            raise ReconciliationError(f'MCP 工具参数结构不兼容：{name}')
        if expected[key] == 'array':
            items = definition.get('items')
            if not isinstance(items, dict) or items.get('type') != 'string':
                raise ReconciliationError(f'MCP 工具参数结构不兼容：{name}')


async def call_finance_tool(client, tools, context, name, timeout, **filters):
    """共用查询口径；附加筛选不能覆盖公司、店铺或时间范围。"""
    if name == 'queryOrderByReferenceNo' or name not in MCP_TOOL_ARGUMENT_TYPES:
        raise ReconciliationError(f'未配置 Amazon 财务工具：{name}')
    if FINANCE_MCP_ARGUMENTS.intersection(filters):
        raise ReconciliationError('附加筛选不能覆盖本次查询上下文')
    arguments = {**context.arguments(), **filters}
    required = FINANCE_MCP_ARGUMENTS | ({'types'} if name == 'queryFmsTransactionDetail' else set())
    if not required.issubset(arguments):
        raise ReconciliationError(f'MCP 工具缺少调用参数：{name}')
    validate_mcp_tool(tools, name, arguments)
    for key, value in arguments.items():
        if MCP_TOOL_ARGUMENT_TYPES[name][key] == 'array':
            valid = (isinstance(value, list) and bool(value)
                     and all(isinstance(item, str) and item.strip() for item in value))
        else:
            valid = isinstance(value, str) and bool(value.strip())
        if not valid:
            raise ReconciliationError(f'MCP 工具参数无效：{name}.{key}')
    return await mcp_request(client.call_tool(name, arguments), timeout, name)


def decode_mcp_result(result):
    """解包 SDK 结构化结果或单个文本 JSON；错误结果始终拒绝。"""
    if result.is_error:
        raise ReconciliationError('MCP 工具返回错误，未生成对账结论')
    payload = result.structured_content
    if payload is None:
        blocks = result.content
        if len(blocks) != 1 or getattr(blocks[0], 'type', None) != 'text':
            raise ReconciliationError('MCP 响应结构不兼容：需要结构化结果或单个文本 JSON')
        try:
            payload = json.loads(blocks[0].text, parse_float=Decimal)
        except (ValueError, TypeError) as exc:
            raise ReconciliationError('MCP 文本结果不是有效 JSON') from exc
    for _ in range(8):
        if not isinstance(payload, dict):
            return payload
        if (payload.get('error') not in (None, False, '')
                or payload.get('success') is False
                or ('code' in payload and payload['code'] not in (0, 200, '0', '200'))):
            raise ReconciliationError('MCP 业务结果包含错误状态')
        wrappers = [key for key in ('data', 'result') if key in payload]
        if not wrappers:
            return payload
        if len(wrappers) != 1:
            raise ReconciliationError('MCP 响应同时包含 data 和 result，无法确定数据来源')
        payload = payload[wrappers[0]]
    raise ReconciliationError('MCP 响应包装层级过深')


def normalize_order_info(payload):
    if payload is None or payload == []:
        return None
    if isinstance(payload, list):
        if len(payload) != 1:
            raise ReconciliationError('MCP 返回多条订单归属，不能擅自选择店铺')
        payload = payload[0]
    if not isinstance(payload, dict):
        raise ReconciliationError('MCP 订单归属结构不兼容')
    normalized = {}
    for name, aliases in {
        'company_code': ('companyCode', 'company_code'),
        'user_account': ('userAccount', 'user_account'),
        'platform': ('platform',),
    }.items():
        values = [payload[key] for key in aliases if key in payload]
        if not values or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ReconciliationError(f'MCP 订单归属缺少有效字段：{name}')
        if len({v.strip() for v in values}) != 1:
            raise ReconciliationError(f'MCP 订单归属字段冲突：{name}')
        normalized[name] = values[0].strip()
    return normalized


def normalize_finance_summary(payload):
    if isinstance(payload, dict) and 'type' in payload:
        payload = [payload]
    if not isinstance(payload, list):
        raise ReconciliationError('MCP 财务结果结构不兼容：需要 type/total 记录数组')
    totals = OrderedDict()
    for index, row in enumerate(payload, 1):
        if not isinstance(row, dict):
            raise ReconciliationError(f'MCP 财务第 {index} 条记录不是对象')
        name, raw = row.get('type'), row.get('total')
        if not isinstance(name, str) or not name.strip():
            raise ReconciliationError(f'MCP 财务第 {index} 条记录缺少有效 type')
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float, Decimal)):
            raise ReconciliationError(f'MCP 财务第 {index} 条记录缺少有效 total')
        try:
            amount = Decimal(str(raw))
            if not amount.is_finite():
                raise InvalidOperation
            name = name.strip()
            totals[name] = totals.get(name, Decimal('0')) + amount
            round_total(totals[name])
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise ReconciliationError(f'MCP 财务第 {index} 条记录的金额无效或超出范围') from exc
    return [(name, round_total(total)) for name, total in totals.items()]


def normalize_layer_rows(payload, label, required):
    if not isinstance(payload, list):
        raise ReconciliationError(f'MCP {label}结构不兼容：需要记录数组，请提供脱敏样例')
    normalized = []
    for index, row in enumerate(payload, 1):
        prefix = f'MCP {label}第 {index} 条记录'
        if not isinstance(row, dict) or not required.issubset(row):
            raise ReconciliationError(f'{prefix}缺少必需字段，请提供脱敏样例')
        name = row['type']
        if not isinstance(name, str) or not name.strip():
            raise ReconciliationError(f'{prefix}缺少有效 type')
        raw = row['total']
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float, Decimal)):
            raise ReconciliationError(f'{prefix}缺少有效 total')
        try:
            amount = Decimal(str(raw))
            if not amount.is_finite() or not math.isfinite(round_total(amount)):
                raise InvalidOperation
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise ReconciliationError(f'{prefix}的金额无效或超出范围') from exc
        normalized.append({'type': name.strip(), 'raw_type': name, 'total': amount, 'raw_fields': dict(row)})
    return normalized


def normalize_description_summary(payload):
    records = normalize_layer_rows(payload, '描述汇总', {'type', 'description', 'total'})
    for index, record in enumerate(records, 1):
        description = record['raw_fields']['description']
        if description is not None and not isinstance(description, str):
            raise ReconciliationError(f'MCP 描述汇总第 {index} 条 description 无效')
        record['description'] = description
    return records


def validate_record_time(record, context, label):
    selected = 'dateTimeSite' if context.date_type == 'datetime' else 'postedDateSite'
    value = record.get(selected)
    if not isinstance(value, datetime) or value.tzinfo is not None:
        raise ReconciliationError(f'{label}所选时间 {selected} 无效，不能参与定位')
    start, end = (datetime.strptime(v, '%Y-%m-%d %H:%M:%S') for v in (context.start_time, context.end_time))
    if not start <= value <= end:
        raise ReconciliationError(f'{label}所选时间 {selected} 不在本次查询范围内')


def normalize_transaction_detail(payload, context, types):
    records = normalize_layer_rows(payload, '交易明细',
                                   {'amazonOrderId', 'type', 'total', 'dateTimeSite', 'postedDateSite'})
    for index, record in enumerate(records, 1):
        label = f'MCP 交易明细第 {index} 条'
        if record['type'] not in types:
            raise ReconciliationError(f'{label}返回了请求 types 范围外的类型')
        raw = record['raw_fields']
        order_id = raw['amazonOrderId']
        if order_id is not None and not isinstance(order_id, str):
            raise ReconciliationError(f'{label}的 amazonOrderId 无效')
        record['order_id'] = order_id.strip() or None if isinstance(order_id, str) else None
        for key in ('dateTimeSite', 'postedDateSite'):
            value = raw[key]
            if value is None:
                record[key] = None
                continue
            if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}', value):
                raise ReconciliationError(f'{label}的 {key} 格式不兼容，请提供脱敏样例')
            try:
                record[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError as exc:
                raise ReconciliationError(f'{label}的 {key} 无效') from exc
        validate_record_time(record, context, label)
    return records


async def run_difference_drilldown(client, tools, result, csv_summary, csv_records, has_description, timeout):
    if __package__:
        from . import compare_orders as local
    else:
        import compare_orders as local
    drill = result.drilldown
    stage = 'local_status'
    try:
        scope, csv_groups, remote_groups = local.difference_scope(
            csv_summary, result.finance_summary, result.differences,
            EXCEL_TO_DB_TYPE_MAP, MERGE_TYPES, SKIP_TYPES,
        )
        drill.raw_types_by_group = scope
        drill.local_only_groups = [group for group, types in scope.items() if not types]
        if csv_records is None:
            raise ReconciliationError('CSV 未保留定位记录，需重新解析账单')
        drill.local_records = [dict(row, group=csv_groups[row['type']]) for row in csv_records
                               if csv_groups.get(row['type']) in scope]
        for record in drill.local_records:
            label = f"CSV 第 {record['line_number']} 行"
            if record.get('amount_error') or record['total'] is None:
                raise ReconciliationError(f"{label}：{record.get('amount_error') or 'total 未可靠解析'}")
            validate_record_time(record, result.context, label)
        local_summary = [(name, total) for name, total in csv_summary if csv_groups.get(name) in scope]
        local.verify_totals(drill.local_records, local_summary, 'CSV 定位记录')
        local.verify_group_totals(drill.local_records, local_summary, csv_groups, 'CSV 比较组')
        drill.local_status = '完成'

        stage = 'description_status'
        response = await call_finance_tool(client, tools, result.context, 'queryFmsTransactionDescription', timeout)
        drill.description_records = normalize_description_summary(decode_mcp_result(response))
        descriptions = [row for row in drill.description_records if row['type'] not in SKIP_TYPES]
        finance_summary = [(name, total) for name, total in result.finance_summary if name not in SKIP_TYPES]
        local.verify_totals(descriptions, finance_summary, 'MCP 描述汇总')
        selected = [row for row in descriptions if remote_groups.get(row['type']) in scope]
        selected_summary = [(name, total) for name, total in finance_summary if remote_groups[name] in scope]
        local.verify_group_totals(selected, selected_summary, remote_groups, 'MCP 描述比较组')
        if has_description and any(not row['description_present'] for row in drill.local_records):
            raise ReconciliationError('CSV 描述列存在但部分记录缺少该字段，不能按空描述定位')
        drill.description_comparison = local.compare_descriptions(
            drill.local_records, selected, csv_groups, remote_groups, has_description,
        )
        drill.description_status = '完成' if has_description else '部分可比较（CSV 缺 description 列，仅展示远端构成）'

        stage = 'order_status'
        types = list(dict.fromkeys(raw for values in scope.values() for raw in values))
        if types:
            response = await call_finance_tool(client, tools, result.context, 'queryFmsTransactionDetail', timeout, types=types)
            drill.detail_records = normalize_transaction_detail(decode_mcp_result(response), result.context, types)
            local.verify_totals(drill.detail_records, selected_summary, 'MCP 交易明细')
            local.verify_group_totals(drill.detail_records, selected_summary, remote_groups, 'MCP 交易明细比较组')
        # CSV 单边类型不推断为缺单；保留本地记录和“汇总缺少该类型”的事实。
        comparable_local = [row for row in drill.local_records if scope[csv_groups[row['type']]]]
        drill.order_differences, drill.without_order = local.compare_orders(
            comparable_local, drill.detail_records, csv_groups, remote_groups,
        )
        drill.order_status = '部分可比较（存在远端汇总缺少的类型）' if drill.local_only_groups else '完成'
    except (ReconciliationError, local.ComparisonError, InvalidOperation, OverflowError) as exc:
        setattr(drill, stage, '失败')
        result.failure = f'差异定位失败：{exc}'


def select_date_range(parsed_data, date_type):
    if date_type == 'datetime':
        keys = ('date_start_time', 'date_end_time')
    elif date_type == 'transaction':
        keys = ('transaction_start_date', 'transaction_end_time')
    else:
        raise ReconciliationError('不支持的日期类型')
    start, end = (parsed_data.get(key) for key in keys)
    if not start or not end:
        raise ReconciliationError('CSV 缺少所选日期类型的有效日期范围，不会自动切换日期口径')
    try:
        dates = [datetime.strptime(value, '%Y-%m-%d %H:%M:%S') for value in (start, end)]
    except (ValueError, TypeError) as exc:
        raise ReconciliationError('CSV 日期范围格式无效') from exc
    if dates[0] > dates[1]:
        raise ReconciliationError('CSV 开始时间晚于结束时间')
    return start, end


async def query_mcp_data(parsed_data, date_type='datetime', url=DEFAULT_MCP_URL, timeout=60):
    start, end = select_date_range(parsed_data, date_type)
    csv_summary = list(parsed_data['type_summary'])
    csv_records = deepcopy(parsed_data.get('transaction_records'))
    has_description = 'description' in parsed_data.get('columns', ())
    order_ids = list(dict.fromkeys(
        oid.strip() for oid in parsed_data.get('order_ids', [])
        if isinstance(oid, str) and oid.strip()
    ))[:10]
    if not order_ids:
        raise ReconciliationError('CSV 中未找到有效的 order id')
    reconciled = None
    try:
        async with mcp_connection(url, timeout) as client:
            tools = await validate_mcp_tools(client, timeout)
            order_info = None
            for oid in order_ids:
                result = await mcp_request(
                    client.call_tool('queryOrderByReferenceNo', {'orderId': oid}),
                    timeout, 'queryOrderByReferenceNo',
                )
                order_info = normalize_order_info(decode_mcp_result(result))
                if order_info is not None:
                    break
            if order_info is None:
                raise ReconciliationError('尝试最多 10 个不重复订单后仍未找到订单归属')
            context = QueryContext(**order_info, date_type=date_type, start_time=start, end_time=end)
            result = await call_finance_tool(client, tools, context, 'queryFmsTransaction', timeout)
            summary = normalize_finance_summary(decode_mcp_result(result))
            is_match, differences, comparison_detail = compare_data(csv_summary, summary)
            reconciled = ReconciliationResult(context, summary, is_match, differences, comparison_detail)
            if not is_match:
                await run_difference_drilldown(client, tools, reconciled, csv_summary, csv_records, has_description, timeout)
    except ReconciliationError as exc:
        if reconciled is None:
            raise
        # 会话退出失败也不能抹掉已确认的汇总事实，或覆盖更早的定位错误。
        reconciled.failure = '; '.join(filter(None, [reconciled.failure, str(exc)]))
    return reconciled


# ============================================================
# 第三阶段：数据对比与输出
# ============================================================

def apply_merge_types(type_dict, merge_map, is_db=False):
    """将 MERGE_TYPES 中配置的 type 金额合并到目标 type
    返回：(merged_dict, merge_notes)
    merge_notes: {dst_key: "含 src_key xxx"} 用于报告展示
    """
    merged = OrderedDict(type_dict)
    merge_notes = {}
    for src, dst in merge_map.items():
        if is_db:
            src_key = EXCEL_TO_DB_TYPE_MAP.get(src, src)
            dst_key = EXCEL_TO_DB_TYPE_MAP.get(dst, dst)
        else:
            src_key = src
            dst_key = dst
        if src_key in merged:
            src_val = merged.pop(src_key)
            merged[dst_key] = merged.get(dst_key, 0.0) + src_val
            merge_notes[dst_key] = f"含 {src} {round_total(src_val)}"
    return merged, merge_notes


def compare_data(excel_summary, db_summary):
    """
    对比 Excel 与数据库的 type/total
    使用 EXCEL_TO_DB_TYPE_MAP 做 type 名称映射匹配
    MERGE_TYPES 中的 type 会先合并到目标 type 再比对
    返回：(is_match, differences, comparison_detail)
    comparison_detail: [(type, excel_val, db_val, matched, note), ...]
    """
    excel_dict = OrderedDict(excel_summary)
    db_dict = OrderedDict(db_summary)

    # 应用合并映射
    excel_dict, excel_merge_notes = apply_merge_types(excel_dict, MERGE_TYPES, is_db=False)
    db_dict, _ = apply_merge_types(db_dict, MERGE_TYPES, is_db=True)

    # 过滤掉 SKIP_TYPES（如 Transfer）
    excel_dict = OrderedDict((k, v) for k, v in excel_dict.items() if k not in SKIP_TYPES)
    db_dict = OrderedDict((k, v) for k, v in db_dict.items() if k not in SKIP_TYPES)

    is_match = True
    differences = []
    comparison_detail = []  # (type, excel_val, db_val, matched, note)
    matched_db_types = set()

    for excel_type, excel_val in excel_dict.items():
        db_type = EXCEL_TO_DB_TYPE_MAP.get(excel_type, excel_type)
        db_val = db_dict.get(db_type, None)
        note = excel_merge_notes.get(excel_type, '')

        if db_val is not None:
            matched_db_types.add(db_type)

        if excel_val == 0.0 and db_val is None:
            db_val = 0.0
            comparison_detail.append((excel_type, excel_val, db_val, True, note))
            continue

        if db_val is None:
            db_val = 0.0

        excel_cmp = round_total(excel_val)
        db_cmp = round_total(db_val)
        row_match = (excel_cmp == db_cmp)

        if not row_match:
            is_match = False
            diff = round_total(excel_val - db_val)
            note = f"差额 {diff}" + (f" ({note})" if note else '')
            differences.append({
                'type': excel_type,
                'excel_total': round_total(excel_val),
                'db_total': round_total(db_val),
                'diff': diff,
            })

        comparison_detail.append((excel_type, excel_val, db_val, row_match, note))

    for db_type, db_val in db_dict.items():
        if db_type not in matched_db_types:
            excel_type = DB_TO_EXCEL_TYPE_MAP.get(db_type, db_type)
            if excel_type not in excel_dict:
                row_match = (round_total(db_val) == 0.0)
                note = '' if row_match else f"差额 {round_total(-db_val)}"
                comparison_detail.append((db_type, 0.0, db_val, row_match, note))
                if not row_match:
                    is_match = False
                    differences.append({
                        'type': db_type,
                        'excel_total': 0.0,
                        'db_total': round_total(db_val),
                        'diff': round_total(-db_val),
                    })

    comparison_detail.sort(key=lambda x: abs(x[1]), reverse=True)

    return is_match, differences, comparison_detail


def format_type_rows(summary):
    """格式化 type 汇总行（含 Excel total、DB total、结果列）"""
    lines = []
    for item in summary:
        if len(item) == 5:
            t, excel_val, db_val, matched, note = item
            mark = '✅' if matched else '❌'
            note_str = f" ({note})" if note else ''
            lines.append(f"   {t:<30s} {excel_val:>15.2f} {db_val:>15.2f}   {mark}{note_str}")
        elif len(item) == 3:
            t, excel_val, db_val = item
            lines.append(f"   {t:<30s} {excel_val:>15.2f} {db_val:>15.2f}")
        else:
            t, v = item
            lines.append(f"   {t:<30s} {v:>15.2f}")
    return '\n'.join(lines)


def drilldown_report_lines(result):
    drill = result.drilldown
    lines = [f'CSV 定位记录回勾：{drill.local_status}', f'描述分析：{drill.description_status}',
             f'订单定位：{drill.order_status}', '全费用明细：未执行（尚未启用）']
    if result.failure:
        lines.append(f'流程未完成：{result.failure}')
    if result.is_match:
        lines.append('费用项汇总匹配，未执行明细定位；不代表订单逐笔一致。')
        return lines
    for group, types in drill.raw_types_by_group.items():
        lines.append(f'差异比较组 {group!r} → 原始 types：{types!r}')
    for group in drill.local_only_groups:
        lines.append(f'{group!r}：远端汇总缺少该类型；仅展示本地记录，不推断为缺单。')
        for record in drill.local_records:
            if record['group'] == group:
                lines.append(f"   CSV 行 {record['line_number']} | type={record['raw_type']!r} | "
                             f"订单={record['order_id']!r} | 描述={record['description']!r} | total={record['total']}")
    if drill.description_comparison:
        lines.append('描述构成（描述差异仅作线索，不直接证明缺单；MCP 数量为汇总条目数）：')
    for row in drill.description_comparison:
        amount = '不可比较' if row['csv_total'] is None else str(row['csv_total'])
        lines.append(f"   {row['group']!r} | description={row['description']!r} | CSV={amount} | "
                     f"MCP={row['mcp_total']} | 差额={row['diff']} | {row['kind']} | "
                     f"CSV记录数={row['csv_count']} | MCP汇总条目数={row['mcp_count']}")
        for side, key in (('CSV', 'csv_records'), ('MCP', 'mcp_records')):
            originals = list(dict.fromkeys((r['raw_type'], r['description']) for r in row[key]))
            if originals:
                lines.append(f'      {side} 原始 type/description：{originals!r}')
    if drill.order_status != '未执行':
        lines.append('订单定位覆盖差异类型的完整返回集合，不按 description 筛选或逐笔配对。')
    for row in drill.order_differences:
        lines.append(f"   {row['kind']} | 订单={row['order_id']!r} | 组={row['group']!r} | "
                     f"CSV={row['csv_total']} | MCP={row['mcp_total']} | 差额={row['diff']} | "
                     f"来源记录数 CSV={row['csv_count']}/MCP={row['mcp_count']} | "
                     f"CSV行号={[r['line_number'] for r in row['csv_records']]}")
    for row in drill.without_order:
        lines.append(f"   空订单号费用组={row['group']!r} | {row['kind']} | CSV={row['csv_total']} | "
                     f"MCP={row['mcp_total']} | 差额={row['diff']} | "
                     f"来源记录数 CSV={row['csv_count']}/MCP={row['mcp_count']}")
        for record in row['csv_records']:
            lines.append(f"      CSV 行 {record['line_number']} | 描述={record['description']!r} | total={record['total']}")
    lines.append('金额回勾不能证明不存在正负抵消的漏记录；以上结论不代表订单逐笔一致。')
    return lines


def output_report(parsed_data, result):
    """报告复用实际查询上下文和比较结果，不另选时间口径。"""
    context = result.context
    header = '对账完成，类型汇总金额匹配' if result.is_match else '对账完成，类型汇总金额存在差异'
    if result.failure:
        header = '对账流程未完成；类型汇总金额' + ('匹配' if result.is_match else '存在差异')
    layers = '\n'.join(drilldown_report_lines(result))
    excel_total_sum = parsed_data['excel_total_sum']
    db_total_sum = round_total(sum(v for t, v in result.finance_summary if t not in SKIP_TYPES))
    return f"""
{header}

数据来源：nexus MCP / queryFmsTransaction
客户代码：{context.company_code}
店铺：{context.user_account}
平台：{context.platform}
时间口径：{context.date_label}
账单开始时间：{context.start_time}
账单结束时间：{context.end_time}
CSV 交易记录数：{parsed_data['excel_row_count']}
MCP 财务记录总数：未查询
CSV 总结算金额(total)：{excel_total_sum}
MCP 财务总结算金额(total)：{db_total_sum}

日期范围：
   date_start_time：{parsed_data['date_start_time']}
   date_end_time：{parsed_data['date_end_time']}
   transaction_start_date：{parsed_data['transaction_start_date']}
   transaction_end_time：{parsed_data['transaction_end_time']}

Type 对比汇总（按 |total| 降序）：
   {'type':<30s} {'CSV total':>15s} {'MCP total':>15s}   结果
   {'-'*30} {'-'*15} {'-'*15}   ------
{format_type_rows(result.comparison_detail)}
   {'-'*30} {'-'*15} {'-'*15}   ------
   {'合计':<28s} {excel_total_sum:>15.2f} {db_total_sum:>15.2f}

范围说明：Transfer 不参与金额对比；CSV 记录数包含全部交易行。
{layers}
"""


def export_result_to_excel(output_path, parsed_data, result):
    """仅在显式导出时加载 Excel 依赖，复用本次查询结果。"""
    if result.failure:
        raise ReconciliationError('对账流程未完成，不能导出正常完成报告')
    context = result.context
    db_summary = result.finance_summary
    is_match, differences, comparison_detail = result.is_match, result.differences, result.comparison_detail
    try:
        from openpyxl import Workbook
    except Exception as exc:
        raise ReconciliationError(f'Excel 依赖{dependency_import_error(exc)}\n{dependency_install_hint()}') from exc
    wb_data = []

    wb_data.append([f"date_start_time：{parsed_data['date_start_time']}"])
    wb_data.append([f"date_end_time：{parsed_data['date_end_time']}"])
    wb_data.append([f"transaction_start_date：{parsed_data['transaction_start_date']}"])
    wb_data.append([f"transaction_end_time：{parsed_data['transaction_end_time']}"])
    wb_data.append([])
    wb_data.append([f'客户代码：{context.company_code}'])
    wb_data.append([f'店铺：{context.user_account}'])
    wb_data.append([f'平台：{context.platform}'])
    wb_data.append(['数据来源：nexus MCP / queryFmsTransaction'])
    wb_data.append([f'时间口径：{context.date_label}'])
    wb_data.append([f'账单开始时间：{context.start_time}'])
    wb_data.append([f'账单结束时间：{context.end_time}'])
    wb_data.append([f"CSV 交易记录数：{parsed_data['excel_row_count']}"])
    wb_data.append(['MCP 财务记录总数：未查询'])
    wb_data.append([f"CSV 总结算金额：{parsed_data['excel_total_sum']}"])
    db_total_sum = round_total(sum(v for t, v in db_summary if t not in SKIP_TYPES))
    wb_data.append([f"MCP 财务总结算金额：{db_total_sum}"])
    wb_data.append([])
    wb_data.append(['对账结果：', '类型汇总金额匹配' if is_match else '类型汇总金额存在差异'])
    wb_data.append(['类型汇总及订单聚合比较不代表订单逐笔一致。'])
    wb_data.append(['Transfer 不参与金额对比；CSV 记录数包含全部交易行。'])
    wb_data.append([])

    wb_data.append(['Type 对比汇总'])
    wb_data.append(['type', 'CSV total', 'MCP total', '结果'])
    for item in comparison_detail:
        t, excel_val, db_val, matched, note = item
        mark = '✅' if matched else '❌'
        result_str = mark + (f" ({note})" if note else '')
        wb_data.append([t, excel_val, db_val, result_str])
    wb_data.append(['合计', parsed_data['excel_total_sum'], db_total_sum])
    wb_data.append([])

    if not is_match and differences:
        wb_data.append(['差异明细'])
        wb_data.append(['type', 'CSV total', 'MCP total', '差额'])
        for d in differences:
            wb_data.append([d['type'], d['excel_total'], d['db_total'], d['diff']])

    wb_data.append([])
    wb_data.extend([[line] for line in drilldown_report_lines(result)])
    wb = Workbook()
    ws = wb.active
    ws.title = "对账结果"
    for row in wb_data:
        ws.append(row if row else [''])
    wb.save(output_path)
    return output_path


# ============================================================
# 主流程
# ============================================================

def positive_timeout(value):
    try:
        timeout = float(value)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError('超时必须是有限正数') from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError('超时必须是有限正数')
    return timeout


def mcp_url(value):
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme in ('http', 'https') and parsed.hostname
                 and parsed.username is None and parsed.password is None
                 and not parsed.fragment)
        parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise argparse.ArgumentTypeError('MCP 地址必须是无内嵌凭据的 HTTP/HTTPS URL')
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description='Amazon 月度账单 MCP 分层对账工具', allow_abbrev=False)
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(arg == '--env' or arg.startswith('--env=') for arg in argv):
        parser.error('--env 已移除：数据库查询已迁移到 MCP，请使用 --mcp-url（可省略）')
    parser.add_argument('--csv', help='Amazon 月度交易 CSV 文件路径（对账时必需）')
    parser.add_argument('--check-env', action='store_true', help='仅检查本地环境；不读取账单、不联网、不安装依赖')
    parser.add_argument('--mcp-url', type=mcp_url, default=DEFAULT_MCP_URL, help='nexus MCP 服务地址（默认 HTTPS）')
    parser.add_argument('--mcp-timeout', type=positive_timeout, default=60.0, help='连接和单次请求超时秒数（默认 60）')
    parser.add_argument('--date-type', choices=['datetime', 'transaction'], default='datetime',
                        help='datetime=入账时间（默认），transaction=结算日期')
    parser.add_argument('--site', type=str.upper, default='AUTO', choices=['AUTO', *CANDIDATE_COLUMNS],
                        help='新增站点受限解析配置；默认 auto 自动识别，AU 须显式指定')
    parser.add_argument('--output', default=None, help='仅显式指定时导出 Excel')
    args = parser.parse_args(argv)
    if args.check_env:
        if args.csv is not None or args.output is not None:
            parser.error('--check-env 不能与 --csv 或 --output 同时使用')
        return output_environment_check()
    if args.csv is None:
        parser.error('对账需要 --csv；仅检查环境请使用 --check-env')
    if args.mcp_url.startswith('http://'):
        print('警告：当前 MCP 地址使用明文 HTTP，建议改用 HTTPS。', file=sys.stderr)
    try:
        print('正在解析 CSV 账单')
        parsed_data = parse_csv(args.csv, site=args.site, date_type=args.date_type)
        print(f"CSV 交易记录数：{parsed_data['excel_row_count']}")
        require_environment(require_excel=bool(args.output))
        print('正在通过 MCP 查询订单归属和财务汇总')
        result = asyncio.run(query_mcp_data(
            parsed_data, args.date_type, args.mcp_url, args.mcp_timeout,
        ))
        print(output_report(parsed_data, result))
        if result.failure:
            print(f'错误：{result.failure}', file=sys.stderr)
            return 1
        if args.output:
            export_result_to_excel(args.output, parsed_data, result)
            print(f'对账结果已导出至：{args.output}')
        return 0 if result.is_match else 2
    except (OSError, ValueError, InvalidOperation) as exc:
        print(f'错误：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    sys.exit(main())
