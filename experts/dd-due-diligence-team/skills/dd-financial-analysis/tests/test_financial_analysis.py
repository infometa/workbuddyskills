import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from calculate import analyze, compute_industry_comparisons  # noqa: E402
from peer_benchmark import (  # noqa: E402
    MIN_SAMPLE_FOR_BENCHMARK,
    MIN_SAMPLE_FOR_PERCENTILES,
    build_benchmark,
    compute_distribution,
)
from render import STANDARD_METRICS, _format_value, build_report  # noqa: E402
from tables import ALL_TABLE_KEYS, build as build_tables  # noqa: E402
from verify import verify  # noqa: E402


def make_period(label, role, period_type, revenue, net_profit):
    year, month = (int(part) for part in label.split('/'))
    period_start = date(year, 1, 1)
    period_end = date(year, month, 31 if month in {3, 12} else 30)
    period_days = (period_end - period_start).days + 1
    source_file = f'{label.replace("/", "-")}-审计报告.pdf'
    return {
        'company_name': '测试企业',
        'fiscal_year': label,
        'period_label': label,
        'period_role': role,
        'period_type': period_type,
        'period_days': period_days,
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
        'source_unit': '万元',
        'currency': 'CNY',
        'statement_scope': '合并',
        'table_units': {'cross_validation': '万元'},
        'source_refs': {'financial_statements': {'file': source_file, 'page': '三表'}},
        'balance_sheet': {
            'cash_and_equivalents': 120,
            'trading_financial_assets': 30,
            'prepaid_accounts': 60,
            'accounts_receivable': 180,
            'inventory': 220,
            'current_assets': 600,
            'fixed_assets': 320,
            'intangible_assets': 50,
            'non_current_assets': 600,
            'total_assets': 1200,
            'short_term_borrowings': 150,
            'accounts_payable': 140,
            'noncurrent_liabilities_due_within_one_year': 50,
            'current_liabilities': 500,
            'non_current_liabilities': 200,
            'total_liabilities': 700,
            'retained_earnings': 100 + net_profit,
            'total_equity': 500,
            # BS-08：负债和所有者权益总计 = 负债总计 + 所有者权益合计
            'total_liabilities_and_equity': 1200,
        },
        'opening_balance_sheet': {
            'cash_and_equivalents': 100,
            'prepaid_accounts': 50,
            'accounts_receivable': 150,
            'inventory': 200,
            'current_assets': 500,
            'fixed_assets': 300,
            'total_assets': 1000,
            'accounts_payable': 120,
            'total_liabilities': 600,
            'retained_earnings': 100,
            'total_equity': 400,
        },
        'income_statement': {
            'revenue': revenue,
            'cost_of_revenue': 600,
            'selling_expense': 100,
            'admin_expense': 100,
            'rd_expense': 50,
            'finance_expense': 50,
            'interest_expense': 40,
            # IS-01：利润总额 = 营业利润 + 营业外收入 - 营业外支出
            'operating_profit': net_profit + 40,
            'non_operating_income': 0,
            'non_operating_expense': 20,
            'total_profit': net_profit + 20,
            'income_tax': 20,
            'net_profit': net_profit,
        },
        'cash_flow': {
            'sales_cash_received': 800,
            'operating_cash_inflow': 1000,
            'operating_cash_outflow': 900,
            'operating_cash_flow': 100,
            'investing_cash_inflow': 50,
            'investing_cash_outflow': 150,
            'investing_cash_flow': -100,
            'capital_expenditure': 80,
            'financing_cash_inflow': 200,
            'financing_cash_outflow': 150,
            'financing_cash_flow': 50,
            'exchange_effect': 0,
            'cash_change': 50,
            'cash_begin': 100,
            'cash_end': 150,
        },
        'financial_supplement': {
            'purchases': 700,
            'restricted_cash': 10,
            'interest_bearing_debt': 300,
            'debt_due_within_one_year': 100,
            'non_recurring_profit': 20,
            'adjusted_net_profit': net_profit - 20,
            'dividends_declared': 0,
            'retained_earnings_other_adjustments': 0,
            'depreciation_and_amortization': 30,
            'top_five_receivables_ratio': 0.60,
            'receivables_over_one_year_ratio': 0.12,
        },
        'opening_financial_supplement': {'interest_bearing_debt': 280},
        'cross_validation': {
            'vat_declared_revenue': 900,
            'bank_operating_inflows': 800,
            'taxable_income': net_profit + 10,
            'business_registry_assets': 1200,
        },
    }


def make_input():
    current = make_period('2026/03', 'current', 'interim', 1000, 80)
    current['public_research'] = {
        'mode': 'provided-only',
        'status': 'not-run',
        'network_attempted': False,
        'queries': [],
        'sources': [],
        'enrichments': [],
        'conflicts': [],
    }
    current['comparative_periods'] = [
        make_period('2022/12', 'calculation_base', 'annual', 1250, 105),
        make_period('2023/12', 'prior_year_3', 'annual', 1200, 100),
        make_period('2024/12', 'prior_year_2', 'annual', 1100, 90),
        make_period('2025/12', 'prior_year', 'annual', 1000, 80),
        make_period('2025/03', 'prior_year_same_period', 'interim', 800, 50),
    ]
    current['industry_benchmarks'] = {
        'classification': '测试行业',
        'as_of_period': '2025',
        'sources': [{'name': '测试来源', 'ref': '测试页', 'sample': '同口径企业样本'}],
        'metrics': {'gross_profit_margin': {'mean': 0.35, 'excellent': 0.45}},
    }
    all_periods = [*current['comparative_periods'], current]
    current['material_manifest'] = [{
        'file_name': period['source_refs']['financial_statements']['file'],
        'doc_type': '审计报告' if period['period_type'] == 'annual' else '财务报表',
        'period': period['period_label'],
        'statement_scope': '合并',
        'currency': 'CNY',
        'source_unit': '万元',
        'usable': True,
    } for period in all_periods]
    return current


def make_industry_enrichment_payload(temp_dir):
    initial = make_input()
    del initial['industry_benchmarks']['metrics']['gross_profit_margin']['mean']
    final = json.loads(json.dumps(initial, ensure_ascii=False))
    source_file = Path(temp_dir) / 'industry-benchmark.pdf'
    source_file.write_bytes(b'official industry benchmark')
    sha256 = 'sha256:' + hashlib.sha256(source_file.read_bytes()).hexdigest()
    source_id = 'public-industry-001'
    final['material_manifest'].append({
        'source_id': source_id,
        'source_origin': 'public-research',
        'file_name': source_file.name,
        'local_file': str(source_file),
        'sha256': sha256,
        'doc_type': 'public_industry_source',
        'period': '2025',
        'statement_scope': 'not-applicable',
        'currency': 'not-applicable',
        'source_unit': 'ratio',
        'usable': True,
    })
    final['industry_benchmarks']['metrics']['gross_profit_margin']['mean'] = 0.35
    final['industry_benchmarks']['sources'].append({
        'name': '官方行业统计',
        'ref': '行业指标表',
        'sample': '同口径企业样本',
        'source_id': source_id,
        'source_origin': 'public-research',
    })
    final['public_research'] = {
        'mode': 'auto-enrich',
        'status': 'completed',
        'network_attempted': True,
        'queries': [{
            'query_id': 'query-001',
            'query': '测试行业 2025 官方行业基准',
            'purpose': '补充毛利率行业均值',
            'outcome': 'accepted',
        }],
        'sources': [{
            'source_id': source_id,
            'query_id': 'query-001',
            'source_type': 'official_government',
            'evidence_scope': 'industry_benchmark',
            'evidence_use': 'numeric',
            'title': '测试行业统计',
            'publisher': '官方统计机构',
            'url': 'https://example.gov.cn/industry-benchmark.pdf',
            'publication_date': '2026-01-01',
            'retrieved_at': '2026-07-20T10:00:00+08:00',
            'period': '2025',
            'locator': '行业指标表',
            'entity_match': 'not-applicable',
            'sample': '同口径企业样本',
            'methodology': '按已披露样本计算行业均值',
            'local_file': str(source_file),
            'sha256': sha256,
        }],
        'enrichments': [{
            'period_role': 'industry_benchmark',
            'field': 'industry_benchmarks.metrics.gross_profit_margin.mean',
            'source_id': source_id,
            'merge_action': 'fill-null',
        }],
        'conflicts': [],
    }
    return initial, final


def make_narrative(**overrides):
    narrative = {
        'balance_sheet_analysis': '资产结构较为稳定，流动资产能够覆盖短期负债，债务安排仍是偿债判断重点。',
        'income_statement_analysis': '主营业务保持盈利，期间费用和非经常因素未改变核心利润判断。',
        'cash_flow_analysis': '经营活动保持净流入，能够对主营还款形成支持。',
        'solvency_analysis': '短期偿债覆盖尚可，杠杆和利息负担处于可控区间。',
        'operating_efficiency_analysis': '应收与存货周转保持稳定，经营资金占用未见明显恶化。',
        'profitability_analysis': '主营盈利和现金实现具有一致性，盈利质量总体稳定。',
        'growth_analysis': '收入和利润保持增长，资产扩张与经营规模基本匹配。',
        'industry_comparison': '毛利水平高于行业均值，主营产品仍具一定盈利空间。',
        'risk_analysis': '规则信号集中于营运资产质量，可能影响经营资金回收。',
        'cross_validation': '已执行的外部数据比较未改变主营经营判断。',
        'analysis_summary': '第一还款来源仍应以主营经营回款为核心。',
    }
    narrative.update(overrides)
    return narrative


class FinancialAnalysisTests(unittest.TestCase):
    def test_calculations_use_opening_balances_and_same_period(self):
        result = analyze(make_input())
        metrics = result['metrics']

        self.assertAlmostEqual(metrics['current_ratio']['value'], 1.2)
        self.assertAlmostEqual(metrics['quick_ratio']['value'], 0.64)
        self.assertAlmostEqual(metrics['receivable_turnover']['value'], 1000 / 165, places=6)
        self.assertAlmostEqual(metrics['roa']['value'], 80 / 1100, places=6)
        self.assertAlmostEqual(metrics['revenue_growth']['value'], 0.25)
        self.assertAlmostEqual(metrics['net_profit_growth']['value'], 0.60)
        self.assertAlmostEqual(metrics['rd_expense_ratio']['value'], 0.05)
        self.assertAlmostEqual(metrics['ebitda_interest_coverage']['value'], 4.25)
        self.assertIsNotNone(metrics['cash_conversion_cycle']['value'])
        self.assertFalse(result['summary']['must_re_extract'])

    def test_ebitda_interest_coverage_requires_disclosed_depreciation(self):
        inputs = make_input()
        del inputs['financial_supplement']['depreciation_and_amortization']
        result = analyze(inputs)
        self.assertIsNone(result['metrics']['ebitda_interest_coverage']['value'])
        self.assertFalse(result['metrics']['ebitda_interest_coverage']['computable'])

    def test_business_rule_signals_are_deterministic_without_rating(self):
        result = analyze(make_input())
        signals = {item['rule_id']: item for item in result['rule_signals']}

        self.assertTrue(signals['BR-S01']['triggered'])
        self.assertTrue(signals['BR-Q05']['triggered'])
        self.assertTrue(signals['BR-Q06']['triggered'])
        self.assertNotIn('risk_level', result['summary'])

    def test_strict_upper_thresholds_do_not_treat_equality_as_above(self):
        inputs = make_input()
        inputs['balance_sheet']['current_assets'] = 1000
        inputs['income_statement']['cost_of_revenue'] = 700
        result = analyze(inputs)
        self.assertEqual(result['rule_bands']['current_ratio']['band'], 'equal_upper_threshold')
        self.assertEqual(result['rule_bands']['gross_profit_margin']['band'], 'equal_upper_threshold')

    def test_render_matches_report_and_backend_contract(self):
        inputs = make_input()
        narrative = make_narrative()
        report, _ = build_report({
            'inputs': inputs,
            'meta': {'company_name': '测试企业', 'display_unit': '万元'},
            'narrative': narrative,
        })

        self.assertEqual([chapter['title'] for chapter in report['chapters']], [
            '1 财务简表', '2 财务指标分析', '3 财务分析总结'
        ])
        provenance = report['_provenance']
        self.assertEqual(provenance['policy'], 'sandbox-only-numeric-computation/v1')
        self.assertTrue(provenance['version'].startswith('2.'))
        stable = json.dumps(report['chapters'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        expected = 'sha256:' + hashlib.sha256(stable.encode('utf-8')).hexdigest()
        self.assertEqual(provenance['chaptersDigest'], expected)

    def test_final_render_requires_explicit_research_mode(self):
        inputs = make_input()
        del inputs['public_research']
        with self.assertRaisesRegex(ValueError, '显式提供 public_research'):
            build_report({
                'inputs': inputs,
                'meta': {},
                'narrative': make_narrative(),
            })

    def test_public_research_non_success_states_remain_renderable(self):
        cases = (
            {
                'mode': 'auto-enrich',
                'status': 'not-needed',
                'network_attempted': False,
                'queries': [],
                'sources': [],
                'enrichments': [],
                'conflicts': [],
            },
            {
                'mode': 'auto-enrich',
                'status': 'no-usable-result',
                'network_attempted': True,
                'queries': [{
                    'query_id': 'query-none',
                    'query': '测试企业 官方重大异动说明',
                    'purpose': '补充重大异动原因',
                    'outcome': 'no-result',
                }],
                'sources': [],
                'enrichments': [],
                'conflicts': [],
            },
            {
                'mode': 'full-research',
                'status': 'network-unavailable',
                'network_attempted': True,
                'failure_reason': '联网工具不可用',
                'queries': [],
                'sources': [],
                'enrichments': [],
                'conflicts': [],
            },
        )
        for research in cases:
            with self.subTest(status=research['status']):
                initial = make_input()
                final = json.loads(json.dumps(initial, ensure_ascii=False))
                final['public_research'] = research
                report, _ = build_report({
                    'initial_inputs': initial,
                    'inputs': final,
                    'meta': {},
                    'narrative': make_narrative(),
                })
                self.assertEqual(report['publicResearch']['status'], research['status'])

    def test_public_enrichment_is_field_linked_and_two_pass_traceable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            initial, final = make_industry_enrichment_payload(temp_dir)
            report, result = build_report({
                'initial_inputs': initial,
                'inputs': final,
                'meta': {},
                'narrative': make_narrative(),
            })
        self.assertEqual(report['publicResearch']['mode'], 'auto-enrich')
        self.assertEqual(report['publicResearch']['status'], 'completed')
        self.assertEqual(
            result['industry_comparisons']['comparisons']['gross_profit_margin']['benchmarks']['mean'],
            0.35,
        )
        provenance = report['_provenance']
        self.assertNotEqual(provenance['initialInputsDigest'], provenance['finalInputsDigest'])
        self.assertRegex(provenance['calculationDigest'], r'^sha256:[a-f0-9]{64}$')
        self.assertRegex(provenance['enrichmentDeltaDigest'], r'^sha256:[a-f0-9]{64}$')
        self.assertNotIn('公开资料增强与来源', report['chapters'][2]['content'])
        self.assertIn(
            'public-industry-001',
            [item['sourceId'] for item in report['reviewRegister']['sources']],
        )
        self.assertRegex(provenance['reviewRegisterDigest'], r'^sha256:[a-f0-9]{64}$')

    def test_public_enrichment_rejects_unknown_field_and_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            initial, final = make_industry_enrichment_payload(temp_dir)
            final['public_research']['enrichments'][0]['field'] = (
                'industry_benchmarks.metrics.not_a_real_metric.mean'
            )
            with self.assertRaisesRegex(ValueError, '不存在或无数值'):
                build_report({
                    'initial_inputs': initial,
                    'inputs': final,
                    'meta': {},
                    'narrative': make_narrative(),
                })

            initial, final = make_industry_enrichment_payload(temp_dir)
            initial['industry_benchmarks']['metrics']['gross_profit_margin']['mean'] = 0.30
            with self.assertRaisesRegex(ValueError, '不得覆盖首次输入已有值'):
                build_report({
                    'initial_inputs': initial,
                    'inputs': final,
                    'meta': {},
                    'narrative': make_narrative(),
                })

            initial, final = make_industry_enrichment_payload(temp_dir)
            final['industry_benchmarks']['metrics']['gross_profit_margin']['median'] = 0.34
            with self.assertRaisesRegex(ValueError, '未登记增强字段'):
                build_report({
                    'initial_inputs': initial,
                    'inputs': final,
                    'meta': {},
                    'narrative': make_narrative(),
                })

    def test_public_source_cannot_masquerade_as_private_bank_evidence(self):
        inputs = make_input()
        inputs['material_manifest'].append({
            'source_id': 'public-bank-001',
            'source_origin': 'public-research',
            'file_name': 'claimed-bank-statement.pdf',
            'doc_type': '银行流水',
            'period': '2026/03',
            'statement_scope': '合并',
            'currency': 'CNY',
            'source_unit': '万元',
            'usable': True,
        })
        with self.assertRaisesRegex(ValueError, '未知公开来源|非公开材料'):
            build_report({
                'inputs': inputs,
                'meta': {},
                'narrative': make_narrative(),
            })

    def test_company_public_fact_requires_strong_identifier_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            initial = make_input()
            initial['balance_sheet']['other_receivables'] = None
            initial['entity_identity'] = {
                'legal_name': '测试企业',
                'security_code': '000001',
            }
            final = json.loads(json.dumps(initial, ensure_ascii=False))
            source_file = Path(temp_dir) / 'company-filing.pdf'
            source_file.write_bytes(b'official company filing')
            sha256 = 'sha256:' + hashlib.sha256(source_file.read_bytes()).hexdigest()
            source_id = 'public-company-001'
            final['balance_sheet']['other_receivables'] = 20
            final['source_refs']['balance_sheet.other_receivables'] = {
                'file': source_file.name,
                'page': '附注页',
                'source_id': source_id,
                'source_origin': 'public-research',
            }
            final['material_manifest'].append({
                'source_id': source_id,
                'source_origin': 'public-research',
                'file_name': source_file.name,
                'local_file': str(source_file),
                'sha256': sha256,
                'doc_type': 'public_filing',
                'period': '2026/03',
                'statement_scope': '合并',
                'currency': 'CNY',
                'source_unit': '万元',
                'usable': True,
            })
            final['public_research'] = {
                'mode': 'auto-enrich',
                'status': 'completed',
                'network_attempted': True,
                'queries': [{
                    'query_id': 'query-company',
                    'query': '测试企业 000001 2026 一季报',
                    'purpose': '补充其他应收款',
                    'outcome': 'accepted',
                }],
                'sources': [{
                    'source_id': source_id,
                    'query_id': 'query-company',
                    'source_type': 'official_exchange',
                    'evidence_scope': 'company_fact',
                    'evidence_use': 'numeric',
                    'title': '测试企业一季报',
                    'publisher': '证券交易所',
                    'url': 'https://example.org/company-filing.pdf',
                    'publication_date': '2026-04-30',
                    'retrieved_at': '2026-07-20T10:00:00+08:00',
                    'period': '2026/03',
                    'locator': '附注页',
                    'entity_match': 'confirmed',
                    'company_name': '测试企业',
                    'security_code': '000002',
                    'statement_scope': '合并',
                    'currency': 'CNY',
                    'source_unit': '万元',
                    'local_file': str(source_file),
                    'sha256': sha256,
                }],
                'enrichments': [{
                    'period_role': 'current',
                    'field': 'balance_sheet.other_receivables',
                    'source_id': source_id,
                    'merge_action': 'fill-null',
                }],
                'conflicts': [],
            }
            with self.assertRaisesRegex(ValueError, '证券代码或统一社会信用代码'):
                build_report({
                    'initial_inputs': initial,
                    'inputs': final,
                    'meta': {},
                    'narrative': make_narrative(),
                })

    def test_actual_backend_validator_accepts_report_and_rejects_tampering(self):
        repo = Path(__file__).resolve().parents[3]
        ts_node = repo / 'backend' / 'node_modules' / '.bin' / 'ts-node'
        if not ts_node.is_file():
            self.skipTest('backend ts-node is not installed')
        report, _ = build_report({
            'inputs': make_input(),
            'meta': {},
            'narrative': make_narrative(),
        })
        script = (
            "import { validateFinancialReportProvenance as validate } "
            "from './src/common/policies/deterministic-computation.policy';"
            "let raw='';process.stdin.on('data',c=>raw+=c);"
            "process.stdin.on('end',()=>console.log(JSON.stringify(validate(JSON.parse(raw)))));"
        )

        def validate_with_backend(payload):
            completed = subprocess.run(
                [str(ts_node), '--transpile-only', '-e', script],
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                cwd=repo / 'backend',
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            return json.loads(completed.stdout)

        self.assertTrue(validate_with_backend(report)['valid'])
        report['chapters'][0]['content'] += '篡改'
        self.assertFalse(validate_with_backend(report)['valid'])
        report, _ = build_report({
            'inputs': make_input(),
            'meta': {},
            'narrative': make_narrative(),
        })
        report['publicResearch']['status'] = 'completed'
        self.assertFalse(validate_with_backend(report)['valid'])
        report, _ = build_report({
            'inputs': make_input(),
            'meta': {},
            'narrative': make_narrative(),
        })
        report['reviewRegister']['items'][0]['impact'] = '篡改'
        self.assertFalse(validate_with_backend(report)['valid'])

    def test_render_rejects_bare_financial_number(self):
        with self.assertRaisesRegex(ValueError, '未通过占位符'):
            build_report({
                'inputs': make_input(),
                'meta': {'display_unit': '万元'},
                'narrative': make_narrative(solvency_analysis='流动比率为1.20倍。'),
            })

    def test_narrative_is_concise_and_process_notes_are_centralized(self):
        with self.assertRaisesRegex(ValueError, '过程性表述'):
            build_report({
                'inputs': make_input(),
                'meta': {},
                'narrative': make_narrative(
                    balance_sheet_analysis='资料不足，具体缺件详见后文。'
                ),
            })
        with self.assertRaisesRegex(ValueError, '套话'):
            build_report({
                'inputs': make_input(),
                'meta': {},
                'narrative': make_narrative(
                    profitability_analysis='综上所述，盈利质量总体稳定。'
                ),
            })
        with self.assertRaisesRegex(ValueError, '超过 280 字符'):
            build_report({
                'inputs': make_input(),
                'meta': {},
                'narrative': make_narrative(growth_analysis='增长保持稳定' * 50),
            })

        report, _ = build_report({
            'inputs': make_input(),
            'meta': {},
            'narrative': make_narrative(
                analysis_basis='该兼容字段不应进入正式报告。',
                limitations='该兼容字段也不应进入正式报告。',
            ),
        })
        body = '\n'.join(chapter['content'] for chapter in report['chapters'])
        self.assertNotIn('兼容字段', body)
        self.assertNotIn('缺件清单', body)
        self.assertNotIn('未匹配附注明细', body)
        self.assertNotIn('公开资料增强与来源', body)
        self.assertNotIn('未命中', body)
        self.assertTrue(report['reviewRegister']['sources'])
        self.assertEqual(
            report['missingMaterials'],
            [
                {
                    'category': item['category'],
                    'required': item['requiredAction'],
                    'impact': item['impact'],
                }
                for item in report['reviewRegister']['items']
                if item['kind'] == 'missing-evidence' and item['status'] == 'open'
            ],
        )

    def test_period_placeholder_can_resolve_history_only_field(self):
        inputs = make_input()
        del inputs['balance_sheet']['trading_financial_assets']
        report, _ = build_report({
            'inputs': inputs,
            'meta': {'display_unit': '万元'},
            'narrative': make_narrative(
                balance_sheet_analysis='历史期交易性金融资产为{{bs_trading_financial_assets:period_0}}，资产配置较为稳定。'
            ),
        })
        self.assertIn('30.00万元', report['chapters'][0]['children'][0]['content'])

    def test_verify_accepts_any_authoritative_metric(self):
        checked = verify({
            'inputs': make_input(),
            'claims': {'working_capital': 1_000_000},
        })
        self.assertTrue(checked['verified'])

    def test_required_period_metadata_has_no_silent_defaults(self):
        for field in (
            'source_unit', 'currency', 'statement_scope', 'period_days',
            'period_start', 'period_end', 'period_role',
        ):
            with self.subTest(field=field):
                inputs = make_input()
                del inputs[field]
                with self.assertRaises(ValueError):
                    analyze(inputs)

        wrong_days = make_input()
        wrong_days['period_days'] = 300
        with self.assertRaisesRegex(ValueError, '起止日不一致'):
            analyze(wrong_days)
        for field, value in (
            ('currency', '文档未披露'),
            ('statement_scope', '未明确'),
            ('company_name', '未知'),
        ):
            with self.subTest(field=field):
                inputs = make_input()
                inputs[field] = value
                with self.assertRaises(ValueError):
                    analyze(inputs)

    def test_period_roles_and_order_are_explicit(self):
        duplicate = make_input()
        duplicate['comparative_periods'][2]['period_role'] = 'prior_year_3'
        with self.assertRaisesRegex(ValueError, '不得重复'):
            analyze(duplicate)

        reversed_periods = make_input()
        annual = reversed_periods['comparative_periods'][:4]
        reversed_periods['comparative_periods'][:4] = list(reversed(annual))
        with self.assertRaisesRegex(ValueError, '时间升序'):
            analyze(reversed_periods)

        swapped_roles = make_input()
        first = next(item for item in swapped_roles['comparative_periods'] if item['period_role'] == 'prior_year_3')
        second = next(item for item in swapped_roles['comparative_periods'] if item['period_role'] == 'prior_year_2')
        first['period_role'], second['period_role'] = second['period_role'], first['period_role']
        with self.assertRaisesRegex(ValueError, '年份必须'):
            analyze(swapped_roles)

        wrong_same_period = make_input()
        same = next(item for item in wrong_same_period['comparative_periods'] if item['period_role'] == 'prior_year_same_period')
        same['period_label'] = '2025/06'
        with self.assertRaisesRegex(ValueError, '不一致|端点一致'):
            analyze(wrong_same_period)

        conflicting_labels = make_input()
        prior = next(
            item for item in conflicting_labels['comparative_periods']
            if item['period_role'] == 'prior_year'
        )
        prior['period_label'] = '2024/12'
        with self.assertRaisesRegex(ValueError, 'period_label 与 fiscal_year 不一致'):
            analyze(conflicting_labels)

        wrong_company = make_input()
        wrong_company['comparative_periods'][0]['company_name'] = '其他企业'
        with self.assertRaisesRegex(ValueError, 'company_name'):
            analyze(wrong_company)

        chinese_period = make_input()
        chinese_period['period_label'] = '2026年第一季度'
        chinese_period['fiscal_year'] = '2026年第一季度'
        self.assertEqual(analyze(chinese_period)['period_label'], '2026年第一季度')

    def test_mixed_currency_and_scope_are_rejected(self):
        for field, value in (('currency', 'USD'), ('statement_scope', '母公司')):
            with self.subTest(field=field):
                inputs = make_input()
                inputs['comparative_periods'][0][field] = value
                with self.assertRaisesRegex(ValueError, field):
                    analyze(inputs)

    def test_interim_growth_does_not_fallback_without_same_period(self):
        inputs = make_input()
        inputs['comparative_periods'] = [
            item for item in inputs['comparative_periods']
            if item['period_role'] != 'prior_year_same_period'
        ]
        result = analyze(inputs)
        self.assertIsNone(result['metrics']['revenue_growth']['value'])
        with self.assertRaisesRegex(ValueError, '上年同期|不可计算|prior_year_same_period'):
            build_report({
                'inputs': inputs,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

    def test_turnover_days_use_actual_period_days(self):
        result = analyze(make_input())
        turnover = result['metrics']['receivable_turnover']['value']
        self.assertAlmostEqual(result['metrics']['receivable_days']['value'], 90 / turnover, places=6)

    def test_opening_balance_is_never_inferred_from_comparison(self):
        inputs = make_input()
        inputs['opening_balance_sheet'] = {}
        result = analyze(inputs)
        self.assertIsNone(result['metrics']['roa']['value'])
        self.assertIsNone(result['metrics']['receivable_turnover']['value'])

    def test_consistency_uses_zero_tolerance(self):
        """配平校验容差为 0%：资产总计与流动+非流动之和差 1 也必须判为不通过。"""
        inputs = make_input()
        inputs['balance_sheet']['total_assets'] = 1199
        result = analyze(inputs)
        check = next(item for item in result['consistency']['checks'] if item['id'] == 'BS-01')
        self.assertFalse(check['passed'])
        self.assertTrue(result['summary']['must_re_extract'])

    def test_comparative_period_critical_failure_requires_re_extraction(self):
        inputs = make_input()
        prior_year_two = next(
            period for period in inputs['comparative_periods']
            if period['period_role'] == 'prior_year_2'
        )
        prior_year_two['balance_sheet']['total_assets'] = 1191
        result = analyze(inputs)
        self.assertTrue(result['summary']['must_re_extract'])

    def test_cash_rollforward_and_adjacent_period_links_are_reported(self):
        """CF-11 期末现金滚动通过，且跨期衔接校验（period_links）照常产出。"""
        result = analyze(make_input())
        rollforward = next(
            item for item in result['consistency']['checks'] if item['id'] == 'CF-11'
        )
        self.assertTrue(rollforward['computable'])
        self.assertTrue(rollforward['passed'])
        self.assertGreater(len(result['period_links']['checks']), 0)

    def test_consistency_rules_cover_all_three_statements(self):
        """21 条配平规则齐备，且 critical 仅覆盖合计/恒等式类。"""
        result = analyze(make_input())
        checks = result['consistency']['checks']
        self.assertEqual(result['consistency']['rule_version'], 2)
        self.assertEqual(len(checks), 21)
        self.assertEqual(
            [item['id'] for item in checks if item['severity'] == 'critical'],
            ['BS-01', 'BS-04', 'BS-08', 'IS-01', 'IS-02', 'CF-01', 'CF-04', 'CF-07', 'CF-10',
             'CF-11'],
        )
        for item in checks:
            with self.subTest(check=item['id']):
                self.assertEqual(item['detail']['tolerance_yuan'], 0.0)

    def test_sum_checks_treat_unlisted_details_as_zero(self):
        """求和类勾稽：报表未列示的明细按 0，合计与已列示明细之和相等即通过。"""
        inputs = make_input()
        bs = inputs['balance_sheet']
        details = (
            'trading_financial_assets', 'derivative_financial_assets',
            'notes_receivable', 'accounts_receivable', 'receivables_financing',
            'prepaid_accounts', 'other_receivables', 'inventory', 'contract_assets',
            'assets_held_for_sale',
            'noncurrent_assets_due_within_one_year', 'other_current_assets',
        )
        for key in details:
            bs.pop(key, None)
        bs['cash_and_equivalents'] = 600
        bs['current_assets'] = 600
        result = analyze(inputs)
        check = next(item for item in result['consistency']['checks'] if item['id'] == 'BS-02')
        self.assertTrue(check['computable'])
        self.assertTrue(check['passed'])
        self.assertEqual(len(check['detail']['missing']['right']), len(details))

    def test_difference_diagnosis_locates_missing_item(self):
        """差额恰等于某个在场明细金额时，自动定位疑似漏项科目。"""
        inputs = make_input()
        bs = inputs['balance_sheet']
        details = (
            'trading_financial_assets', 'derivative_financial_assets',
            'notes_receivable', 'accounts_receivable', 'receivables_financing',
            'prepaid_accounts', 'other_receivables', 'contract_assets', 'assets_held_for_sale',
            'noncurrent_assets_due_within_one_year', 'other_current_assets',
        )
        for key in details:
            bs.pop(key, None)
        bs['cash_and_equivalents'] = 380
        bs['inventory'] = 220
        bs['current_assets'] = 820  # 明细和 = 600，差额 220 恰等于存货
        result = analyze(inputs)
        check = next(item for item in result['consistency']['checks'] if item['id'] == 'BS-02')
        self.assertFalse(check['passed'])
        self.assertEqual(check['diagnosis']['type'], 'single')
        self.assertEqual(check['diagnosis']['field'], 'balance_sheet.inventory')

    def test_missing_cash_begin_blocks_verified_report(self):
        inputs = make_input()
        del inputs['cash_flow']['cash_begin']
        result = analyze(inputs)
        rollforward = next(
            item for item in result['consistency']['checks'] if item['id'] == 'CF-11'
        )
        self.assertFalse(rollforward['computable'])
        with self.assertRaisesRegex(ValueError, 'critical|必需原始字段'):
            build_report({
                'inputs': inputs,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

    def test_render_rejects_bare_integer_and_numeric_credit_meta(self):
        with self.assertRaisesRegex(ValueError, '未通过占位符'):
            build_report({
                'inputs': make_input(),
                'meta': {},
                'narrative': make_narrative(risk_analysis='抽查了3笔交易，仍需核验。'),
            })
        with self.assertRaisesRegex(ValueError, 'credit_context'):
            build_report({
                'inputs': make_input(),
                'meta': {'credit_context': {'purpose': '申请1000万元流动资金贷款'}},
                'narrative': make_narrative(),
            })
        for text in (
            '毛利率约两成。', '同比下降三个百分点。', '期限约六个月。',
            '回款约三分之一。', '客户占比过半。', '收入实现翻倍。',
        ):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, '未通过占位符'):
                build_report({
                    'inputs': make_input(),
                    'meta': {},
                    'narrative': make_narrative(risk_analysis=text),
                })

        for date_text in ('2026年3月', '2026年第一季度', '2026年一季度', '二〇二六年三月'):
            with self.subTest(date_text=date_text):
                report, _ = build_report({
                    'inputs': make_input(),
                    'meta': {},
                    'narrative': make_narrative(
                        analysis_basis=f'截至{date_text}，材料口径已核对。'
                    ),
                })
                self.assertTrue(report['_provenance']['verified'])

    def test_meta_shapes_are_validated_before_rendering(self):
        invalid_meta = (
            {'credit_context': 'abc'},
            {'report_name': ['错误类型']},
            {'business_context': {'industry': ['制造业']}},
        )
        for meta in invalid_meta:
            with self.subTest(meta=meta), self.assertRaises(ValueError):
                build_report({
                    'inputs': make_input(),
                    'meta': meta,
                    'narrative': make_narrative(),
                })
        with self.assertRaisesRegex(ValueError, 'credit_context'):
            build_report({
                'inputs': make_input(),
                'meta': {'credit_context': {'purpose': 1000}},
                'narrative': make_narrative(),
            })

    def test_statement_change_rule_uses_three_complete_years_and_threshold(self):
        inputs = make_input()
        latest_annual = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year'
        )
        latest_annual['balance_sheet']['inventory'] = 330
        result = analyze(inputs)
        changes = result['statement_changes']
        self.assertTrue(changes['computable'])
        inventory = changes['items']['bs_inventory']
        self.assertAlmostEqual(inventory['yoy_change'], 0.5)
        self.assertTrue(inventory['significant'])
        with self.assertRaisesRegex(ValueError, '附注明细'):
            build_report({
                'inputs': inputs,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

    def test_statement_change_absolute_amount_gate_filters_small_base_noise(self):
        inputs = make_input()
        prior_year_2 = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year_2'
        )
        latest_annual = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year'
        )
        # 交易性金融资产：10万 → 30万，同比 +200% 但绝对变动仅 20 万元（<100 万元门槛）。
        prior_year_2['balance_sheet']['trading_financial_assets'] = 10
        latest_annual['balance_sheet']['trading_financial_assets'] = 30
        result = analyze(inputs)
        item = result['statement_changes']['items']['bs_trading_financial_assets']
        self.assertAlmostEqual(item['yoy_change'], 2.0)
        self.assertFalse(item['passes_abs_gate'])
        # 变化率夸张但绝对额不过门槛：不计入显著异动。
        self.assertFalse(item['significant'])
        self.assertEqual(item['severity'], 'none')

    def test_statement_change_grades_mild_severe_and_direction_reversal(self):
        inputs = make_input()
        prior_year_2 = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year_2'
        )
        latest_annual = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year'
        )
        # 存货 600万 → 720万：同比 +20% ∈ [15%,30%)，绝对额 120 万元过门槛 → mild。
        prior_year_2['balance_sheet']['inventory'] = 600
        latest_annual['balance_sheet']['inventory'] = 720
        # 净利润由正转负：方向逆转 → severe。
        prior_year_2['income_statement']['net_profit'] = 90
        latest_annual['income_statement']['net_profit'] = -60
        result = analyze(inputs)
        items = result['statement_changes']['items']
        inventory = items['bs_inventory']
        self.assertAlmostEqual(inventory['yoy_change'], 0.2)
        self.assertTrue(inventory['significant'])
        self.assertEqual(inventory['severity'], 'mild')
        net_profit = items['inc_net_profit']
        self.assertTrue(net_profit['direction_reversed'])
        self.assertTrue(net_profit['significant'])
        self.assertEqual(net_profit['severity'], 'severe')
        severe_keys = {item['key'] for item in result['statement_changes']['severe_items']}
        self.assertIn('inc_net_profit', severe_keys)

    def test_statement_change_attribution_is_deterministic(self):
        inputs = make_input()
        result = analyze(inputs)
        attribution = result['statement_changes']['attribution']
        dupont = attribution['dupont']
        self.assertTrue(dupont['computable'])
        # 杜邦重构 ROE 必须等于三因子乘积（确定性可复算）。
        self.assertAlmostEqual(
            dupont['reconstructed_roe'],
            round(
                dupont['net_profit_margin']
                * dupont['total_asset_turnover']
                * dupont['equity_multiplier'],
                6,
            ),
            places=6,
        )
        divergence = attribution['profit_cash_divergence']
        self.assertTrue(divergence['computable'])
        self.assertIsNotNone(divergence['cfo_to_net_profit'])

    def test_note_details_are_normalized_and_component_contributions_are_scripted(self):
        inputs = make_input()
        prior_two = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year_2'
        )
        latest = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year'
        )
        latest['balance_sheet']['inventory'] = 330
        for period, components in (
            (prior_two, [('原材料', 100), ('产成品', 120)]),
            (latest, [('原材料', 150), ('产成品', 180)]),
        ):
            period['note_details'] = {
                'bs_inventory': {
                    'source_unit': '万元',
                    'currency': 'CNY',
                    'statement_scope': '合并',
                    'source_ref': {
                        'file': period['source_refs']['financial_statements']['file'],
                        'section': '存货附注',
                    },
                    'components': [
                        {'name': name, 'amount': amount} for name, amount in components
                    ],
                    'raw_text': '存货构成取自审计附注。',
                }
            }
        result = analyze(inputs)
        detail = result['matched_note_details']['items']['bs_inventory']
        changes = {item['name']: item for item in detail['component_changes']}
        self.assertEqual(changes['原材料']['change_amount'], 500_000)
        self.assertAlmostEqual(changes['原材料']['contribution_to_line_item_change'], 5 / 11, places=6)

        report, _ = build_report({
            'inputs': inputs,
            'meta': {},
            'narrative': make_narrative(),
        })
        self.assertIn('存货附注明细', report['chapters'][0]['children'][0]['content'])

        latest['note_details']['bs_inventory']['components'] = [
            {'name': '原材料', 'amount': 150},
            {'name': '原材料', 'amount': 180},
        ]
        with self.assertRaisesRegex(ValueError, '重复明细名称'):
            analyze(inputs)

        latest['note_details']['bs_inventory']['components'] = [
            {'name': '原材料', 'amount': 150}
        ]
        missing_component = analyze(inputs)['matched_note_details']['items']['bs_inventory']
        missing_changes = {item['name']: item for item in missing_component['component_changes']}
        self.assertIsNone(missing_changes['产成品']['latest_amount'])
        self.assertIsNone(missing_changes['产成品']['change_amount'])
        with self.assertRaisesRegex(ValueError, '附注明细'):
            build_report({
                'inputs': inputs,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

        del latest['note_details']
        old_only = analyze(inputs)['matched_note_details']['items']['bs_inventory']
        self.assertFalse(old_only['matched'])

    def test_industry_benchmark_and_two_std_signal_are_validated(self):
        inputs = make_input()
        inputs['industry_benchmarks']['metrics'] = {
            'gross_profit_margin_change': {'mean': 0.0, 'std_dev': 0.01}
        }
        result = analyze(inputs)
        signal = next(item for item in result['rule_signals'] if item['rule_id'] == 'BR-I01')
        self.assertTrue(signal['triggered'])

        invalid = make_input()
        invalid['industry_benchmarks']['sources'][0]['sample'] = ''
        with self.assertRaisesRegex(ValueError, 'sample'):
            analyze(invalid)
        invalid_std = make_input()
        invalid_std['industry_benchmarks']['metrics'] = {
            'gross_profit_margin_change': {'mean': 0.0, 'std_dev': 0.0}
        }
        with self.assertRaisesRegex(ValueError, 'positive'):
            analyze(invalid_std)
        invalid_scale = make_input()
        invalid_scale['industry_benchmarks']['metrics'] = {
            'gross_profit_margin': {'mean': 35}
        }
        with self.assertRaisesRegex(ValueError, '小数口径'):
            analyze(invalid_scale)
        stale_period = make_input()
        stale_period['industry_benchmarks']['as_of_period'] = '1990'
        with self.assertRaisesRegex(ValueError, '最近完整年度'):
            analyze(stale_period)

    def test_industry_percentiles_are_preserved_and_compared(self):
        inputs = make_input()
        inputs['industry_benchmarks']['metrics']['gross_profit_margin'].update({
            'p25': 0.25,
            'p50': 0.30,
            'p75': 0.40,
        })
        result = analyze(inputs)
        comparison = result['industry_comparisons']['comparisons']['gross_profit_margin']
        self.assertEqual(comparison['benchmarks']['p25'], 0.25)
        self.assertEqual(comparison['benchmarks']['p50'], 0.30)
        self.assertEqual(comparison['benchmarks']['p75'], 0.40)
        self.assertIsNotNone(comparison['difference_rates']['p50'])

    def test_consecutive_rule_does_not_bridge_missing_annual_value(self):
        inputs = make_input()
        prior_two = next(
            item for item in inputs['comparative_periods'] if item['period_role'] == 'prior_year_2'
        )
        prior_two['balance_sheet']['prepaid_accounts'] = None
        result = analyze(inputs)
        signal = next(item for item in result['rule_signals'] if item['rule_id'] == 'BR-S02')
        self.assertIsNone(signal['triggered'])

    def test_negative_equity_ratios_are_uncomputable(self):
        inputs = make_input()
        inputs['balance_sheet']['total_equity'] = -100
        inputs['balance_sheet']['total_liabilities'] = 1300
        inputs['opening_balance_sheet']['total_equity'] = -50
        result = analyze(inputs)
        self.assertIsNone(result['metrics']['roe']['value'])
        self.assertIsNone(result['metrics']['debt_to_equity']['value'])
        self.assertIsNone(result['metrics']['equity_multiplier']['value'])

    def test_percentage_inputs_must_be_decimal_fractions(self):
        inputs = make_input()
        inputs['financial_supplement']['top_five_receivables_ratio'] = 60
        with self.assertRaisesRegex(ValueError, '0 至 1'):
            analyze(inputs)

    def test_verified_report_requires_all_narratives_and_evidence(self):
        with self.assertRaisesRegex(ValueError, 'narrative'):
            build_report({
                'inputs': make_input(),
                'meta': {'report_mode': 'verified'},
                'narrative': {},
            })
        inputs = make_input()
        inputs['source_refs'] = {}
        with self.assertRaisesRegex(ValueError, 'source_refs'):
            build_report({
                'inputs': inputs,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })
        empty_nested_ref = make_input()
        empty_nested_ref['source_refs'] = {'financial_statements': {}}
        with self.assertRaisesRegex(ValueError, 'file'):
            build_report({
                'inputs': empty_nested_ref,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })
        arbitrary_ref = make_input()
        arbitrary_ref['source_refs'] = {'x': 'y'}
        with self.assertRaisesRegex(ValueError, '对象'):
            build_report({
                'inputs': arbitrary_ref,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })
        wrong_manifest_scope = make_input()
        wrong_manifest_scope['material_manifest'][0]['statement_scope'] = '母公司'
        with self.assertRaisesRegex(ValueError, '报告口径'):
            build_report({
                'inputs': wrong_manifest_scope,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })
        registered_unusable = make_input()
        registered_unusable['material_manifest'].append({
            'file_name': '损坏附件.pdf',
            'doc_type': '其他材料',
            'period': '未识别',
            'statement_scope': '母公司',
            'currency': 'USD',
            'source_unit': '元',
            'usable': False,
        })
        report, _ = build_report({
            'inputs': registered_unusable,
            'meta': {},
            'narrative': make_narrative(),
        })
        self.assertTrue(report['_provenance']['verified'])

        wrong_periods = make_input()
        for item in wrong_periods['material_manifest']:
            item['period'] = '1900/01'
        with self.assertRaisesRegex(ValueError, '对应报告期'):
            build_report({
                'inputs': wrong_periods,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

        coded_doc_types = make_input()
        for item in coded_doc_types['material_manifest']:
            item['doc_type'] = (
                'audit_report' if '审计报告' in item['doc_type'] else 'financial_statements'
            )
        report, _ = build_report({
            'inputs': coded_doc_types,
            'meta': {},
            'narrative': make_narrative(),
        })
        self.assertTrue(report['_provenance']['verified'])

        nonfinancial_refs = make_input()
        for item in nonfinancial_refs['material_manifest']:
            item['doc_type'] = 'business_license'
        nonfinancial_refs['material_manifest'].append({
            'file_name': '未引用审计报告.pdf',
            'doc_type': 'audit_report',
            'period': nonfinancial_refs['period_label'],
            'statement_scope': '合并',
            'currency': 'CNY',
            'source_unit': '万元',
            'usable': True,
        })
        with self.assertRaisesRegex(ValueError, '财务报表或审计报告'):
            build_report({
                'inputs': nonfinancial_refs,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

        wrong_manifest_unit = make_input()
        for item in wrong_manifest_unit['material_manifest']:
            item['source_unit'] = '元'
        with self.assertRaisesRegex(ValueError, '同单位'):
            build_report({
                'inputs': wrong_manifest_unit,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

    def test_render_requires_exact_role_set_and_historical_metrics(self):
        missing_role = make_input()
        missing_role['comparative_periods'] = [
            item for item in missing_role['comparative_periods']
            if item['period_role'] != 'prior_year'
        ]
        missing_role['industry_benchmarks']['metrics'] = {}
        with self.assertRaisesRegex(ValueError, 'prior_year'):
            build_report({
                'inputs': missing_role,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

        missing_opening = make_input()
        annual = next(
            item for item in missing_opening['comparative_periods']
            if item['period_role'] == 'prior_year_2'
        )
        annual['opening_balance_sheet'] = {}
        with self.assertRaisesRegex(ValueError, '标准指标|必需原始字段'):
            build_report({
                'inputs': missing_opening,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

        missing_raw_field = make_input()
        del missing_raw_field['balance_sheet']['short_term_borrowings']
        with self.assertRaisesRegex(ValueError, '必需原始字段'):
            build_report({
                'inputs': missing_raw_field,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

        bad_base = make_input()
        base = next(
            item for item in bad_base['comparative_periods']
            if item['period_role'] == 'calculation_base'
        )
        base['income_statement']['total_profit'] = 999
        with self.assertRaisesRegex(ValueError, 'calculation_base'):
            build_report({
                'inputs': bad_base,
                'meta': {'report_mode': 'verified'},
                'narrative': make_narrative(),
            })

    def test_auto_mode_downgrades_missing_materials_to_limited_report(self):
        inputs = make_input()
        del inputs['cash_flow']['exchange_effect']
        inputs['industry_benchmarks']['metrics'] = {}
        report, _ = build_report({
            'inputs': inputs,
            'meta': {},
            'narrative': {},
        })
        self.assertFalse(report['_provenance']['verified'])
        self.assertEqual(report['_provenance']['reportStatus'], 'limited')
        self.assertTrue(report['_provenance']['renderabilityIssues'])
        self.assertTrue(report['missingMaterials'])
        self.assertNotIn('缺件清单', report['chapters'][2]['content'])
        self.assertTrue(report['reviewRegister']['items'])

    def test_amount_placeholder_carries_selected_unit_and_meta_cannot_relabel(self):
        report, _ = build_report({
            'inputs': make_input(),
            'meta': {'display_unit': '亿元'},
            'narrative': make_narrative(balance_sheet_analysis='资产总额为{{bs_total_assets}}，资产规模保持稳定。'),
        })
        self.assertIn('0.12亿元', report['chapters'][0]['children'][0]['content'])

        with self.assertRaisesRegex(ValueError, '不得硬编码单位'):
            build_report({
                'inputs': make_input(),
                'meta': {'display_unit': '亿元'},
                'narrative': make_narrative(
                    balance_sheet_analysis='资产总额为{{bs_total_assets}}万元。'
                ),
            })
        with self.assertRaisesRegex(ValueError, '不得硬编码单位'):
            build_report({
                'inputs': make_input(),
                'meta': {'display_unit': '万元'},
                'narrative': make_narrative(
                    balance_sheet_analysis='资产总额为{{bs_total_assets}}人民币万元。'
                ),
            })

        with self.assertRaisesRegex(ValueError, 'company_name'):
            build_report({
                'inputs': make_input(),
                'meta': {'company_name': '其他企业'},
                'narrative': make_narrative(),
            })
        with self.assertRaisesRegex(ValueError, 'statement_scope'):
            build_report({
                'inputs': make_input(),
                'meta': {'business_context': {'statement_scope': '母公司'}},
                'narrative': make_narrative(),
            })

    def test_verify_rejects_empty_claims_and_nonfinite_tolerance(self):
        self.assertFalse(verify({'inputs': make_input(), 'claims': {}})['verified'])
        invalid = verify({
            'inputs': make_input(),
            'claims': {'current_ratio': 1.2},
            'tolerance': math.inf,
        })
        self.assertFalse(invalid['verified'])
        drifted = verify({
            'inputs': make_input(),
            'claims': {'working_capital': 1_004_999},
        })
        self.assertFalse(drifted['verified'])

    def test_verify_rejects_non_numeric_claim_for_uncomputable_metric(self):
        inputs = make_input()
        inputs['opening_balance_sheet'] = {}
        self.assertTrue(verify({'inputs': inputs, 'claims': {'roa': None}})['verified'])
        for invalid_claim in ('not-a-number', True, math.nan, math.inf):
            with self.subTest(invalid_claim=invalid_claim):
                checked = verify({'inputs': inputs, 'claims': {'roa': invalid_claim}})
                self.assertFalse(checked['verified'])

    def test_cross_validation_can_use_its_own_explicit_unit(self):
        inputs = make_input()
        inputs['table_units']['cross_validation'] = '元'
        inputs['cross_validation']['vat_declared_revenue'] = 9_000_000
        result = analyze(inputs)
        self.assertAlmostEqual(result['metrics']['revenue_vat_difference_rate']['value'], 1 / 9, places=6)

    def test_cli_round_trip_writes_only_controlled_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            calculation_path = str(Path(temp_dir) / 'financial-calculation.json')
            env = {
                **os.environ,
                'AIDD_CALCULATION_PATH': calculation_path,
            }
            calculated = subprocess.run(
                [sys.executable, str(SCRIPTS / 'calculate.py')],
                input=json.dumps(make_input(), ensure_ascii=False),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(calculated.returncode, 0, calculated.stderr or calculated.stdout)
            self.assertTrue(Path(calculation_path).is_file())
            self.assertIn('metrics', json.loads(calculated.stdout))

            render_payload = {
                'inputs': make_input(),
                'meta': {'company_name': '测试企业', 'display_unit': '万元'},
                'narrative': make_narrative(),
            }
            render_env = {**os.environ, 'AIDD_REPORTS_DIR': temp_dir}
            rendered = subprocess.run(
                [sys.executable, str(SCRIPTS / 'render.py')],
                input=json.dumps(render_payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                env=render_env,
                check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr or rendered.stdout)
            status = json.loads(rendered.stdout)
            self.assertTrue(status['verified'])
            self.assertEqual(status['reportStatus'], 'limited')
            report = json.loads(Path(status['path']).read_text(encoding='utf-8'))
            self.assertEqual(report['_provenance']['artifactKind'], 'financial-analysis')
            self.assertEqual(report['_provenance']['evidenceCoverage'], 'partial')
            docx_path = Path(status['docxPath'])
            self.assertTrue(docx_path.is_file())
            self.assertGreater(docx_path.stat().st_size, 0)
            import zipfile
            with zipfile.ZipFile(docx_path) as archive:
                self.assertIn('word/document.xml', archive.namelist())
            rendered_again = subprocess.run(
                [sys.executable, str(SCRIPTS / 'render.py')],
                input=json.dumps(render_payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                env=render_env,
                check=False,
            )
            self.assertEqual(
                rendered_again.returncode,
                0,
                rendered_again.stderr or rendered_again.stdout,
            )
            second_status = json.loads(rendered_again.stdout)
            self.assertNotEqual(status['path'], second_status['path'])
            self.assertNotEqual(status['docxPath'], second_status['docxPath'])

            limited_inputs = make_input()
            del limited_inputs['cash_flow']['exchange_effect']
            limited_payload = {
                'inputs': limited_inputs,
                'meta': {'company_name': '测试企业', 'display_unit': '万元'},
                'narrative': {},
            }
            limited_rendered = subprocess.run(
                [sys.executable, str(SCRIPTS / 'render.py')],
                input=json.dumps(limited_payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                env=render_env,
                check=False,
            )
            self.assertEqual(
                limited_rendered.returncode,
                0,
                limited_rendered.stderr or limited_rendered.stdout,
            )
            limited_status = json.loads(limited_rendered.stdout)
            self.assertFalse(limited_status['verified'])
            self.assertEqual(limited_status['reportStatus'], 'limited')
            limited_docx = Path(limited_status['docxPath'])
            self.assertTrue(limited_docx.is_file())
            limited_report = json.loads(Path(limited_status['path']).read_text(encoding='utf-8'))
            self.assertTrue(limited_report['missingMaterials'])
            with zipfile.ZipFile(limited_docx) as archive:
                document_xml = archive.read('word/document.xml')
            document_text = ''.join(ET.fromstring(document_xml).itertext())
            opening = '本报告已按现有材料完成分析。进一步核验仍需补充'
            ending = '资料与核验事项'
            self.assertIn(opening, document_text)
            self.assertIn(ending, document_text)
            self.assertLess(document_text.index(opening), document_text.index('1 财务简表'))
            self.assertGreater(document_text.rindex(ending), document_text.index('3 财务分析总结'))
            self.assertGreater(document_text.index('生成追溯'), document_text.rindex(ending))
            first_category = limited_report['missingMaterials'][0]['category']
            self.assertGreaterEqual(document_text.count(first_category), 2)


class AuthoritativeTablesTests(unittest.TestCase):
    """tables.py：报告表格与可引用数值必须全部来自确定性计算，不经 LLM。"""

    @classmethod
    def setUpClass(cls):
        cls.result = analyze(make_input())
        cls.bundle = build_tables(cls.result, '万元', None)

    def test_all_expected_tables_are_present(self):
        self.assertTrue(self.bundle['ok'])
        self.assertEqual(set(self.bundle['tables']), set(ALL_TABLE_KEYS))
        for key in ('balance_sheet', 'income_statement', 'cash_flow', 'metrics', 'consistency'):
            with self.subTest(table=key):
                self.assertTrue(self.bundle['tables'][key]['available'])
                self.assertIn('|', self.bundle['tables'][key]['markdown'])

    def test_unavailable_table_is_flagged_not_faked(self):
        """缺数据的表必须标 available=false 且 markdown 为空，不得编造占位内容。"""
        for table in self.bundle['tables'].values():
            if not table['available']:
                self.assertEqual(table['markdown'], '')

    def test_metric_table_values_match_calculation(self):
        """指标表中的数值必须与 calculate.py 结果逐项一致。"""
        markdown = self.bundle['tables']['metrics']['markdown']
        metrics = self.result['metrics']
        for _, key in STANDARD_METRICS:
            metric = metrics.get(key) or {}
            if not metric.get('computable'):
                continue
            expected = _format_value(
                metric['value'], metric.get('value_type', 'ratio'), '万元'
            )
            with self.subTest(metric=key):
                self.assertIn(expected, markdown)

    def test_facts_display_matches_authoritative_value(self):
        """facts 的 display 必须由权威 value 格式化而来，且原始 value 未被改写。"""
        metrics = self.result['metrics']
        for key, fact in self.bundle['facts'].items():
            metric = metrics.get(key)
            if not metric or not metric.get('computable'):
                continue
            with self.subTest(fact=key):
                self.assertEqual(fact['value'], metric['value'])
                self.assertTrue(fact['display'])
                self.assertNotIn('{{', fact['display'])

    def test_amount_facts_are_converted_to_display_unit(self):
        """金额类事实必须按展示单位换算，避免正文误标单位。"""
        total_assets = self.bundle['facts']['bs_total_assets']
        self.assertEqual(total_assets['value_type'], 'amount')
        self.assertTrue(total_assets['display'].endswith('万元'))
        # calculate.py 归一到元；万元展示应为 value / 10000
        expected = f"{total_assets['value'] / 10000:,.2f}万元"
        self.assertEqual(total_assets['display'], expected)

    def test_turnover_and_ratio_display_suffix(self):
        """周转率用「次」，流动/速动比率不带单位——符合财务惯例。"""
        self.assertTrue(self.bundle['facts']['total_asset_turnover']['display'].endswith('次'))
        self.assertTrue(self.bundle['facts']['inventory_turnover']['display'].endswith('次'))
        for key in ('current_ratio', 'quick_ratio'):
            display = self.bundle['facts'][key]['display']
            with self.subTest(metric=key):
                self.assertFalse(display.endswith('倍'))
                self.assertFalse(display.endswith('次'))

    def test_consistency_table_reports_real_differences(self):
        """勾稽表必须如实反映 calculate.py 的校验结论，含未通过项。"""
        broken = make_input()
        broken['balance_sheet']['total_liabilities_and_equity'] = 1150
        result = analyze(broken)
        bundle = build_tables(result, '万元', None)
        markdown = bundle['tables']['consistency']['markdown']
        failed = [c for c in result['consistency']['checks'] if c['computable'] and c['passed'] is False]
        self.assertTrue(failed, '篡改负债和所有者权益总计后应至少含一项配平差异（BS-08）')
        for check in failed:
            with self.subTest(check=check['id']):
                self.assertIn(check['id'], markdown)
        self.assertIn('不通过', markdown)
        self.assertEqual(
            sorted(bundle['consistency']['failed_ids']),
            sorted(c['id'] for c in failed),
        )

    def test_only_filter_restricts_output(self):
        subset = build_tables(self.result, '万元', {'metrics', 'consistency'})
        self.assertEqual(set(subset['tables']), {'metrics', 'consistency'})

    def test_invalid_display_unit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'display_unit'):
            build_tables(self.result, '美元', None)

    def test_non_result_payload_is_rejected(self):
        """传入三表输入而非计算结果时必须明确报错，不得静默产出空表。"""
        with self.assertRaisesRegex(ValueError, 'metrics/summary'):
            build_tables(make_input(), '万元', None)

    def test_display_unit_switch_rescales_amounts(self):
        in_yuan = build_tables(self.result, '元', None)
        yuan_display = in_yuan['facts']['bs_total_assets']['display']
        wan_display = self.bundle['facts']['bs_total_assets']['display']
        self.assertTrue(yuan_display.endswith('元'))
        self.assertNotEqual(yuan_display, wan_display)


def make_peer(
    name,
    code,
    total_assets,
    total_liabilities,
    total_equity,
    revenue,
    cost,
    net_profit,
    prior_assets,
    prior_equity,
):
    """构造一家可比公司样本（原始三表科目，非现成比率）。"""
    return {
        'name': name,
        'code': code,
        'current': {
            'balance_sheet': {
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
            },
            'income_statement': {
                'revenue': revenue,
                'cost_of_revenue': cost,
                'net_profit': net_profit,
            },
        },
        'prior': {
            'balance_sheet': {'total_assets': prior_assets, 'total_equity': prior_equity},
        },
        'source': {
            'name': f'{name} 2024年年度报告',
            'ref': 'akshare:stock_financial_report_sina',
        },
    }


def make_peer_payload(count=10):
    """生成 count 家电池制造行业样本（量级参考真实行业）。"""
    templates = [
        ('宁德时代', '300750', 7.9e11, 4.9e11, 3.0e11, 3.62e11, 2.6e11, 5.07e10, 7.2e11, 2.6e11),
        ('亿纬锂能', '300014', 1.05e11, 6.8e10, 3.7e10, 4.86e10, 4.0e10, 4.05e9, 9.3e10, 3.3e10),
        ('国轩高科', '002074', 6.4e10, 4.6e10, 1.8e10, 3.16e10, 2.8e10, 1.2e8, 5.8e10, 1.7e10),
        ('孚能科技', '688567', 2.6e10, 1.8e10, 8.0e9, 1.55e10, 1.5e10, -2.2e9, 2.4e10, 9.0e9),
        ('欣旺达', '300207', 6.2e10, 4.3e10, 1.9e10, 5.21e10, 4.5e10, 1.45e9, 5.5e10, 1.7e10),
        ('鹏辉能源', '300438', 1.4e10, 9.0e9, 5.0e9, 8.5e9, 7.5e9, 1.0e8, 1.3e10, 5.2e9),
        ('珠海冠宇', '688772', 2.5e10, 1.5e10, 1.0e10, 1.15e10, 9.8e9, 3.5e8, 2.3e10, 9.6e9),
        ('南都电源', '300068', 1.6e10, 1.1e10, 5.0e9, 1.05e10, 9.2e9, 1.5e8, 1.5e10, 4.8e9),
        ('派能科技', '688063', 8.0e9, 3.0e9, 5.0e9, 3.2e9, 2.5e9, 1.0e8, 8.5e9, 5.1e9),
        ('多氟多', '002407', 1.8e10, 1.0e10, 8.0e9, 1.2e10, 1.1e10, 2.0e8, 1.7e10, 7.8e9),
    ]
    return {
        'classification_standard': 'GB_T_4754_2017',
        'classification_code': 'C384',
        'classification_name': '电池制造',
        'as_of_period': '2024',
        'match_level': 'exact',
        'data_channel': 'akshare',
        'peers': [make_peer(*item) for item in templates[:count]],
    }


class PeerBenchmarkTest(unittest.TestCase):
    """同业对标：行业基准由脚本从样本原始科目计算，不接受 LLM 手填。"""

    def test_percentile_uses_linear_interpolation(self):
        """分位数须用线性插值（等价 numpy linear / R type-7），保证可复现。"""
        distribution = compute_distribution(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], True
        )
        self.assertAlmostEqual(distribution['p25'], 3.25)
        self.assertAlmostEqual(distribution['p50'], 5.5)
        self.assertAlmostEqual(distribution['p75'], 7.75)
        odd = compute_distribution([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], True)
        self.assertAlmostEqual(odd['p25'], 2.5)
        self.assertAlmostEqual(odd['p50'], 4.0)
        self.assertAlmostEqual(odd['p75'], 5.5)

    def test_ten_samples_produce_full_distribution(self):
        result = build_benchmark(make_peer_payload(10))
        self.assertTrue(result['usable'])
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['sample_size'], 10)
        self.assertEqual(
            set(result['metrics']),
            {'debt_ratio', 'gross_profit_margin', 'roe', 'total_asset_turnover'},
        )
        for values in result['metrics'].values():
            self.assertTrue({'mean', 'median', 'p25', 'p50', 'p75'} <= set(values))
        self.assertEqual(len(result['sources']), 10)
        self.assertIsNotNone(result['sample_revenue_profile'])

    def test_sample_between_five_and_nine_hides_percentiles(self):
        """5-9 家只给均值与中位数，与后端 validateBenchmark 门槛一致。"""
        result = build_benchmark(make_peer_payload(7))
        self.assertEqual(result['status'], 'limited')
        for values in result['metrics'].values():
            self.assertIn('mean', values)
            self.assertNotIn('p25', values)
            self.assertNotIn('p75', values)
        self.assertTrue(any(str(MIN_SAMPLE_FOR_PERCENTILES) in item for item in result['limitations']))

    def test_sample_below_five_refuses_numeric_benchmark(self):
        """样本不足 5 家时不得输出基准，也不得补数。"""
        result = build_benchmark(make_peer_payload(4))
        self.assertFalse(result['usable'])
        self.assertEqual(result['status'], 'limited')
        self.assertEqual(result['metrics'], {})
        self.assertIn(str(MIN_SAMPLE_FOR_BENCHMARK), result['reason'])

    def test_missing_prior_equity_drops_sample_without_substitution(self):
        """平均净资产缺期初值时剔除样本，禁止用期末值替代。"""
        payload = make_peer_payload(10)
        payload['peers'][1]['prior']['balance_sheet'].pop('total_equity')
        result = build_benchmark(payload)
        self.assertEqual(result['sample_size'], 9)
        self.assertTrue(any('roe' in item['reason'] for item in result['excluded_peers']))

    def test_ratio_out_of_scale_is_dropped(self):
        """比例超出合理量纲（如百分数误当小数）时剔除，避免污染分位数。"""
        payload = make_peer_payload(10)
        # 令毛利率为负且绝对值 > 1（营业成本远超营业收入）
        payload['peers'][2]['current']['income_statement']['cost_of_revenue'] = 1.0e12
        result = build_benchmark(payload)
        self.assertEqual(result['sample_size'], 9)

    def test_source_reference_is_mandatory(self):
        """每家样本必须带来源引用，否则拒绝出基准（calculate.py 硬校验前置）。"""
        payload = make_peer_payload(10)
        for peer in payload['peers']:
            peer['source'].pop('ref')
        with self.assertRaisesRegex(ValueError, '来源引用'):
            build_benchmark(payload)

    def test_output_is_consumable_by_calculate_comparisons(self):
        """脚本产出须能被 calculate.py 的 compute_industry_comparisons 直接消费。"""
        benchmark = build_benchmark(make_peer_payload(10))
        metrics = {
            'debt_ratio': {'value': 0.6476, 'value_type': 'percentage'},
            'gross_profit_margin': {'value': 0.1770, 'value_type': 'percentage'},
            'roe': {'value': 0.1157, 'value_type': 'percentage'},
            'total_asset_turnover': {'value': 0.4909, 'value_type': 'multiple'},
        }
        comparisons = compute_industry_comparisons(metrics, benchmark, expected_as_of_year=2024)
        self.assertTrue(comparisons['usable'])
        self.assertEqual(comparisons['classification'], '电池制造')
        self.assertEqual(comparisons['as_of_period'], '2024')
        for key, item in comparisons['comparisons'].items():
            self.assertIsNotNone(item['enterprise'], key)
            self.assertIn('mean', item['benchmarks'], key)
            self.assertIn('mean', item['difference_rates'], key)
            self.assertIsNotNone(item['z_score'], key)

    def test_year_mismatch_is_rejected_by_calculate(self):
        """基准年度与最近完整年度不一致时由 calculate.py 拦截（后端据此降级为 limited）。"""
        benchmark = build_benchmark(make_peer_payload(10))
        metrics = {'debt_ratio': {'value': 0.65, 'value_type': 'percentage'}}
        with self.assertRaisesRegex(ValueError, '最近完整年度'):
            compute_industry_comparisons(metrics, benchmark, expected_as_of_year=2023)

    def test_percentage_metrics_use_decimal_scale(self):
        """毛利率等比例指标必须是小数口径，便于 calculate.py 校验通过。"""
        result = build_benchmark(make_peer_payload(10))
        self.assertLessEqual(abs(result['metrics']['gross_profit_margin']['mean']), 1.0)
        self.assertLessEqual(abs(result['metrics']['debt_ratio']['mean']), 1.0)

    def test_content_hash_is_stable_and_sensitive(self):
        """相同样本产出相同摘要；样本变化时摘要必须变化。"""
        first = build_benchmark(make_peer_payload(10))
        second = build_benchmark(make_peer_payload(10))
        self.assertEqual(first['content_hash'], second['content_hash'])
        self.assertNotEqual(first['content_hash'], build_benchmark(make_peer_payload(9))['content_hash'])

    def test_classification_name_is_required(self):
        payload = make_peer_payload(10)
        payload['classification_name'] = '  '
        with self.assertRaisesRegex(ValueError, 'classification_name'):
            build_benchmark(payload)


if __name__ == '__main__':
    unittest.main()
