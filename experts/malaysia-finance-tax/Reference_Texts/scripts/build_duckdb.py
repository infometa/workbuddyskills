"""
Build Malaysia Finance & Tax DuckDB Database
Populates structured financial/tax data from authoritative sources.
"""
import os
try:
    import duckdb
except ImportError:
    import subprocess
    import sys
    print("duckdb not found, auto-installing...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "duckdb", "--quiet"])
    import duckdb
import json
from datetime import datetime, date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))

DB_PATH = os.path.join(PLUGIN_ROOT, 'Databases', 'malaysia_finance_tax.duckdb')
SKILL_DB_PATH = os.path.join(PLUGIN_ROOT, 'skills', 'malaysia-finance-tax', 'datasets', 'malaysia_finance_tax.duckdb')

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(SKILL_DB_PATH), exist_ok=True)

con = duckdb.connect(DB_PATH)

# =============================================
# Table 1: Corporate & Personal Tax Rates
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS tax_rates (
    id INTEGER PRIMARY KEY,
    category VARCHAR,
    entity_type VARCHAR,
    income_range_min DECIMAL(15,2),
    income_range_max DECIMAL(15,2),
    rate_pct DECIMAL(5,2),
    description TEXT,
    year_of_assessment INTEGER,
    notes TEXT
)
""")

tax_data = [
    # Corporate tax rates
    (1, 'corporate', 'Standard Resident Company', 0, 99999999999, 24.00, 'Standard corporate tax rate', 2026, 'Companies not meeting SME criteria'),
    (2, 'corporate', 'SME (First 150k)', 0, 150000, 15.00, 'SME first bracket', 2026, 'Paid-up <=2.5M and business income <=50M'),
    (3, 'corporate', 'SME (Next 450k)', 150001, 600000, 17.00, 'SME second bracket', 2026, ''),
    (4, 'corporate', 'SME (Above 600k)', 600001, 99999999999, 24.00, 'SME excess bracket', 2026, 'Returns to standard rate'),
    (5, 'corporate', 'Non-Resident Company', 0, 99999999999, 24.00, 'Non-resident corporate rate', 2026, ''),
    (6, 'corporate', 'Petroleum', 0, 99999999999, 38.00, 'Petroleum income tax', 2026, 'Marginal fields: 25%'),
    (7, 'corporate', 'MTT/QDMTT', 0, 99999999999, 15.00, 'Minimum tax for MNE groups', 2025, 'Effective from FY commencing on/after 1 Jan 2025'),
    # Personal tax rates
    (10, 'personal', 'Individual', 0, 5000, 0.00, 'First bracket', 2025, ''),
    (11, 'personal', 'Individual', 5001, 20000, 1.00, 'Second bracket', 2025, ''),
    (12, 'personal', 'Individual', 20001, 35000, 3.00, 'Third bracket', 2025, ''),
    (13, 'personal', 'Individual', 35001, 50000, 6.00, 'Fourth bracket', 2025, ''),
    (14, 'personal', 'Individual', 50001, 70000, 11.00, 'Fifth bracket', 2025, ''),
    (15, 'personal', 'Individual', 70001, 100000, 19.00, 'Sixth bracket', 2025, ''),
    (16, 'personal', 'Individual', 100001, 400000, 25.00, 'Seventh bracket', 2025, ''),
    (17, 'personal', 'Individual', 400001, 600000, 26.00, 'Eighth bracket', 2025, ''),
    (18, 'personal', 'Individual', 600001, 2000000, 28.00, 'Ninth bracket', 2025, ''),
    (19, 'personal', 'Individual', 2000001, 99999999999, 30.00, 'Top bracket', 2025, ''),
    # CGT
    (20, 'capital_gains', 'Unlisted Shares (Net Gain)', 0, 99999999999, 10.00, 'CGT on chargeable gain', 2024, 'Or 2% on gross disposal value at taxpayer option'),
    (21, 'capital_gains', 'RPGT - Within 3 years', 0, 99999999999, 30.00, 'Real Property Gains Tax', 2025, ''),
    (22, 'capital_gains', 'RPGT - 4th year', 0, 99999999999, 20.00, 'Real Property Gains Tax', 2025, ''),
    (23, 'capital_gains', 'RPGT - 5th year', 0, 99999999999, 15.00, 'Real Property Gains Tax', 2025, ''),
    (24, 'capital_gains', 'RPGT - 6th year+ (Companies)', 0, 99999999999, 10.00, 'Real Property Gains Tax', 2025, ''),
    (25, 'capital_gains', 'RPGT - 6th year+ (Individuals)', 0, 99999999999, 5.00, 'Real Property Gains Tax', 2025, 'For citizens'),
]
con.executemany("INSERT OR REPLACE INTO tax_rates VALUES (?,?,?,?,?,?,?,?,?)", tax_data)
print(f"Inserted {len(tax_data)} tax rate records")

# =============================================
# Table 2: SST Rates
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS sst_rates (
    id INTEGER PRIMARY KEY,
    tax_type VARCHAR,
    category VARCHAR,
    rate_pct DECIMAL(5,2),
    description TEXT,
    effective_date DATE,
    registration_threshold DECIMAL(15,2),
    notes TEXT
)
""")

sst_data = [
    (1, 'sales_tax', 'Basic Necessities', 0.00, 'Unprocessed food, medicine, books, fertilizer', '2025-07-01', 500000, '0% rated goods'),
    (2, 'sales_tax', 'Non-essential Goods', 5.00, 'Lobster, cheese, salmon, truffles, silk, essential oils', '2025-07-01', 500000, ''),
    (3, 'sales_tax', 'Luxury Goods', 10.00, 'Shark fin, alcohol, leather goods, racing bicycles', '2025-07-01', 500000, ''),
    (4, 'sales_tax', 'Low Value Goods (Imported)', 10.00, 'Online goods valued <=RM500 imported', '2024-01-01', 500000, 'LVG tax'),
    (5, 'service_tax', 'Food & Beverage', 6.00, 'Restaurants, bars, coffee shops', '2024-03-01', 1500000, 'Group B'),
    (6, 'service_tax', 'Accommodation', 8.00, 'Hotels, serviced apartments, homestays', '2024-03-01', 500000, 'Group A'),
    (7, 'service_tax', 'Professional Services', 8.00, 'Legal, accounting, engineering, IT, consultancy', '2024-03-01', 500000, 'Group G'),
    (8, 'service_tax', 'Logistics Services', 6.00, 'Supply chain, warehousing, freight, port services', '2024-03-01', 500000, 'Group J'),
    (9, 'service_tax', 'Digital Services (SToDS)', 8.00, 'SaaS, streaming, online ads by foreign providers', '2024-03-01', 500000, 'Foreign Service Providers'),
    (10, 'service_tax', 'Financial Services', 8.00, 'Non-basic financial services (fees/commissions)', '2025-07-01', 1000000, 'Group H new'),
    (11, 'service_tax', 'Healthcare (Non-Citizens)', 6.00, 'Private hospitals serving foreign patients', '2025-07-01', 1500000, 'Group I new'),
    (12, 'service_tax', 'Rental Services (Commercial)', 8.00, 'Commercial property rental, equipment leasing', '2025-07-01', 500000, 'Group K'),
    (13, 'service_tax', 'Construction Services', 6.00, 'Commercial/industrial building, infrastructure', '2025-07-01', 1500000, 'Group L'),
    (14, 'service_tax', 'Education (Non-Citizens)', 6.00, 'Private schools/colleges for non-citizen students', '2025-07-01', 1000000, 'Group M, fee >RM60k/student/yr'),
    (15, 'service_tax', 'Health Centres', 8.00, 'Facial, salon, spa, massage, slimming', '2025-07-01', 500000, 'Group C new'),
]
con.executemany("INSERT OR REPLACE INTO sst_rates VALUES (?,?,?,?,?,?,?,?)", sst_data)
print(f"Inserted {len(sst_data)} SST rate records")

# =============================================
# Table 3: BNM OPR History
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS bnm_opr_history (
    id INTEGER PRIMARY KEY,
    effective_date DATE,
    opr_rate_pct DECIMAL(4,2),
    change_bps INTEGER,
    statement_summary TEXT,
    mpc_meeting TEXT
)
""")

opr_data = [
    (1, '2026-05-07', 2.75, 0, 'Maintained; growth outlook stable', 'MPC 3rd/2026'),
    (2, '2026-03-05', 2.75, 0, 'Maintained; global growth moderating', 'MPC 2nd/2026'),
    (3, '2026-01-22', 2.75, 0, 'Maintained; domestic demand supports growth', 'MPC 1st/2026'),
    (4, '2025-11-06', 2.75, 0, 'Maintained; inflation contained', 'MPC 4th/2025'),
    (5, '2025-09-05', 2.75, 0, 'Maintained; growth on track', 'MPC 3rd/2025'),
    (6, '2025-07-10', 2.75, 0, 'Maintained; steady outlook', 'MPC 2nd/2025'),
    (7, '2025-01-22', 3.00, -25, 'Reduced from 3.00%; supporting growth amid global uncertainty', 'MPC 1st/2025'),
    (8, '2024-11-06', 3.00, 0, 'Maintained', 'MPC 4th/2024'),
    (9, '2024-09-05', 3.00, 0, 'Maintained', 'MPC 3rd/2024'),
    (10, '2024-05-09', 3.00, 0, 'Maintained', 'MPC 2nd/2024'),
    (11, '2024-03-07', 3.00, 0, 'Maintained', 'MPC 1st/2024'),
    (12, '2023-11-02', 3.00, 0, 'Maintained', 'MPC 4th/2023'),
    (13, '2023-09-07', 3.00, 0, 'Maintained', 'MPC 3rd/2023'),
    (14, '2023-07-13', 3.00, 0, 'Maintained', 'MPC 2nd/2023'),
    (15, '2023-05-03', 3.00, 25, 'Increased from 2.75%', 'MPC 1st/2023'),
]
con.executemany("INSERT OR REPLACE INTO bnm_opr_history VALUES (?,?,?,?,?,?)", opr_data)
print(f"Inserted {len(opr_data)} OPR history records")

# =============================================
# Table 4: Forex Rates (MYR vs Major Currencies)
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS forex_rates (
    id INTEGER PRIMARY KEY,
    currency_code VARCHAR(3),
    currency_name VARCHAR,
    rate_to_myr DECIMAL(10,4),
    date_recorded DATE,
    source VARCHAR
)
""")

forex_data = [
    (1, 'USD', 'US Dollar', 4.6800, '2026-07-08', 'BNM'),
    (2, 'EUR', 'Euro', 5.0500, '2026-07-08', 'BNM'),
    (3, 'GBP', 'British Pound', 5.9500, '2026-07-08', 'BNM'),
    (4, 'JPY', 'Japanese Yen (100)', 3.2500, '2026-07-08', 'BNM'),
    (5, 'SGD', 'Singapore Dollar', 3.5000, '2026-07-08', 'BNM'),
    (6, 'CNY', 'Chinese Yuan Renminbi', 0.6400, '2026-07-08', 'BNM'),
    (7, 'AUD', 'Australian Dollar', 3.1200, '2026-07-08', 'BNM'),
    (8, 'HKD', 'Hong Kong Dollar', 0.6000, '2026-07-08', 'BNM'),
    (9, 'THB', 'Thai Baht (100)', 13.2000, '2026-07-08', 'BNM'),
    (10, 'IDR', 'Indonesian Rupiah (1000)', 0.2900, '2026-07-08', 'BNM'),
]
con.executemany("INSERT OR REPLACE INTO forex_rates VALUES (?,?,?,?,?,?)", forex_data)
print(f"Inserted {len(forex_data)} forex rate records")

# =============================================
# Table 5: Tax Incentives
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS tax_incentives (
    id INTEGER PRIMARY KEY,
    incentive_name VARCHAR,
    type VARCHAR,
    benefit_rate_pct DECIMAL(5,2),
    duration_years INTEGER,
    eligible_sectors TEXT,
    min_investment TEXT,
    application_authority VARCHAR,
    description TEXT
)
""")

incentive_data = [
    (1, 'Pioneer Status', 'tax_exemption', 70.00, 5, 'Manufacturing, High-value Services', 'Varies by sector', 'MIDA', '70% statutory income exemption; 100% for high-tech/strategic (5-10 years)'),
    (2, 'Investment Tax Allowance', 'capital_allowance', 60.00, 5, 'Manufacturing, Selected Services', 'Varies by sector', 'MIDA', '60% on QCE offset against 70% statutory income; 100% for strategic projects'),
    (3, 'Reinvestment Allowance', 'capital_allowance', 60.00, 15, 'Manufacturing (existing)', 'Ongoing operations', 'MIDA', 'For expansion/modernisation/diversification; offset 70% of statutory income'),
    (4, 'Green ITA', 'capital_allowance', 100.00, 5, 'Renewable Energy, Energy Efficiency, Green Building, EV', 'Varies', 'MIDA/GITA', 'Green Technology investment allowance'),
    (5, 'Green Income Tax Exemption', 'tax_exemption', 70.00, 10, 'Renewable Energy, Green Services', 'Varies', 'MIDA/GITE', 'Green technology service income exemption'),
    (6, 'BioNexus Status', 'tax_exemption', 100.00, 10, 'Biotechnology', 'Varies', 'MIDA/Bioeconomy Corp', 'Full tax exemption for biotechnology companies'),
    (7, 'MSC Malaysia Status', 'tax_exemption', 100.00, 10, 'ICT, Digital Services', 'Varies', 'MDEC', 'For qualifying ICT and digital companies'),
    (8, 'Principal Hub', 'concessionary_tax', 5.00, 5, 'Services, Manufacturing (regional/global HQ)', 'Opex >= RM3M, FTEs >= 50', 'MIDA', '5% or 10% concessionary rate for regional principal hubs; renewable'),
    (9, 'R&D Investment Allowance', 'capital_allowance', 100.00, 5, 'All sectors (R&D activities)', 'Varies', 'MIDA/LHDN', 'Accelerated capital allowance for R&D'),
    (10, 'Double Deduction on R&D', 'double_deduction', 100.00, 0, 'All sectors (approved R&D)', 'Varies', 'LHDN', 'Double deduction on qualifying R&D expenditure'),
    (11, 'Halal Industry Incentives', 'tax_exemption', 100.00, 10, 'Halal Food, Halal Logistics', 'Varies', 'MIDA/HDC', 'Pioneer Status or ITA for halal industry'),
    (12, 'Approved Service Projects', 'tax_exemption', 70.00, 5, 'Logistics, Education, Healthcare, Tourism', 'Varies by sector', 'MIDA', 'Tax incentives for approved service projects'),
]
con.executemany("INSERT OR REPLACE INTO tax_incentives VALUES (?,?,?,?,?,?,?,?,?)", incentive_data)
print(f"Inserted {len(incentive_data)} tax incentive records")

# =============================================
# Table 6: Withholding Tax Rates
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS withholding_tax (
    id INTEGER PRIMARY KEY,
    income_type VARCHAR,
    standard_rate_pct DECIMAL(5,2),
    treaty_rate_pct DECIMAL(5,2),
    reference VARCHAR,
    notes TEXT
)
""")

wht_data = [
    (1, 'Interest', 15.00, 10.00, 'ITA 1967 S.109', 'Treaty rate depends on jurisdiction'),
    (2, 'Royalties', 10.00, 5.00, 'ITA 1967 S.109(1A)', 'Treaty rate depends on jurisdiction'),
    (3, 'Technical Fees', 10.00, 5.00, 'ITA 1967 S.109A', 'Treaty rate depends on jurisdiction'),
    (4, 'Contract Payments (Non-Resident)', 10.00, 10.00, 'ITA 1967 S.107A', 'For non-resident contractors'),
    (5, 'Distributions (Real Estate Trust)', 10.00, 0.00, 'ITA 1967', ''),
]
con.executemany("INSERT OR REPLACE INTO withholding_tax VALUES (?,?,?,?,?,?)", wht_data)
print(f"Inserted {len(wht_data)} withholding tax records")

# =============================================
# Table 7: Compliance Deadlines
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS compliance_deadlines (
    id INTEGER PRIMARY KEY,
    obligation VARCHAR,
    description TEXT,
    deadline_text VARCHAR,
    penalty TEXT,
    authority VARCHAR
)
""")

deadline_data = [
    (1, 'Annual Return (SSM)', 'File annual return with SSM', '30 days from incorporation anniversary', 'Late: RM50-RM500; Strike off for persistent non-compliance', 'SSM'),
    (2, 'Audited Financial Statements', 'Prepare and file audited financial statements', '6 months after financial year-end', 'RM5,000-RM50,000 fine', 'SSM'),
    (3, 'Form C (Corporate Tax)', 'File annual corporate tax return', '7 months after financial year-end', 'Penalty up to 45% of unpaid tax', 'LHDN'),
    (4, 'CP204 (Estimated Tax)', 'Submit estimated tax payable for current YA', '3 months from financial year start', 'Late filing penalty', 'LHDN'),
    (5, 'Form E (Employer Return)', 'Annual employer tax return', '31 March', 'Fines and penalties', 'LHDN'),
    (6, 'Form EA (Employee Statement)', 'Issue salary statement to employees', 'End of February', 'Fines', 'LHDN'),
    (7, 'PCB (Monthly Tax Deduction)', 'Remit monthly tax deduction to LHDN', '15th of following month', 'Late payment penalty 10-15%', 'LHDN'),
    (8, 'EPF Contributions', 'Remit EPF contributions', '15th of following month', 'Late payment penalty and fines', 'EPF'),
    (9, 'SOCSO Contributions', 'Remit SOCSO contributions', '15th of following month', 'Late payment penalty', 'SOCSO'),
    (10, 'SST Returns', 'File bimonthly SST return', 'Within 30 days after taxable period end', 'Late: 10-15% of unpaid amount; Fine up to RM50,000', 'RMCD'),
    (11, 'Transfer Pricing Docs', 'Maintain contemporaneous TP documentation', 'Annually (submit with Form C if queried)', 'Penalty up to 35% of adjustment', 'LHDN'),
    (12, 'BO Reporting', 'Maintain and update beneficial ownership register', 'Ongoing / upon any change', 'Fines', 'SSM'),
]
con.executemany("INSERT OR REPLACE INTO compliance_deadlines VALUES (?,?,?,?,?,?)", deadline_data)
print(f"Inserted {len(deadline_data)} compliance deadline records")

# =============================================
# Table 8: Company Types (Malaysia)
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS company_types (
    id INTEGER PRIMARY KEY,
    type_code VARCHAR,
    name VARCHAR,
    description TEXT,
    min_directors INTEGER,
    min_shareholders INTEGER,
    min_paid_up_capital DECIMAL(15,2),
    liability TEXT
)
""")

company_data = [
    (1, 'Sdn Bhd', 'Private Limited Company', 'Most common business vehicle; shares not publicly traded', 1, 1, 1.00, 'Limited by shares'),
    (2, 'Bhd', 'Public Limited Company', 'Listed or intended to list on Bursa Malaysia', 3, 1, 50000.00, 'Limited by shares'),
    (3, 'PLC', 'Public Listed Company', 'Listed on Bursa Malaysia', 3, 1, 50000.00, 'Limited by shares'),
    (4, 'Branch', 'Foreign Company Branch', 'Registered branch of foreign company', 2, 0, 0.00, 'Parent company liable'),
    (5, 'LLP', 'Limited Liability Partnership', 'Hybrid between partnership and company', 2, 0, 0.00, 'Limited liability'),
    (6, 'Sole Proprietorship', 'Sole Proprietorship', 'Single owner business (not separate legal entity)', 0, 1, 0.00, 'Unlimited liability'),
    (7, 'Partnership', 'Partnership', '2-20 partners (not separate legal entity)', 0, 2, 0.00, 'Unlimited liability'),
]
con.executemany("INSERT OR REPLACE INTO company_types VALUES (?,?,?,?,?,?,?,?)", company_data)
print(f"Inserted {len(company_data)} company type records")

# =============================================
# Table 9: Personal Tax Reliefs
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS personal_tax_reliefs (
    id INTEGER PRIMARY KEY,
    relief_name VARCHAR,
    max_amount DECIMAL(15,2),
    ya VARCHAR,
    description TEXT
)
""")

relief_data = [
    (1, 'Individual Self Relief', 9000.00, '2025', 'Standard personal relief'),
    (2, 'EPF Contributions', 4000.00, '2025', 'Combined with life insurance total RM7,000'),
    (3, 'Life Insurance Premium', 3000.00, '2025', 'Combined with EPF total RM7,000'),
    (4, 'Education/Medical Insurance', 3000.00, '2025', ''),
    (5, 'Medical Expenses (Serious Illness)', 8000.00, '2025', 'For self, spouse or child'),
    (6, 'Medical Expenses (Fertility Treatment)', 1000.00, '2025', ''),
    (7, 'Medical Expenses (Vaccination)', 1000.00, '2025', ''),
    (8, 'Medical Checkup', 1000.00, '2025', ''),
    (9, 'Education Fees (Degree/Courses)', 7000.00, '2025', 'Professional courses or degree level'),
    (10, 'Childcare', 3000.00, '2025', 'For children up to age 6'),
    (11, 'Lifestyle (Books, Internet, Gym)', 2500.00, '2025', 'Books, internet subscription, sports equipment, gym'),
    (12, 'SSPN (Education Savings)', 8000.00, '2025', 'National education savings scheme'),
    (13, 'Housing Loan Interest', 10000.00, '2025', 'For 3 consecutive YA from first interest payment'),
    (14, 'EV Charging Facility', 2500.00, '2025', ''),
    (15, 'Alimony', 5000.00, '2025', 'Spousal support payments'),
]
con.executemany("INSERT OR REPLACE INTO personal_tax_reliefs VALUES (?,?,?,?,?)", relief_data)
print(f"Inserted {len(relief_data)} personal tax relief records")

# =============================================
# Table 10: MGS Bond Yields (benchmark)
# =============================================
con.execute("""
CREATE TABLE IF NOT EXISTS bond_yields (
    id INTEGER PRIMARY KEY,
    instrument VARCHAR,
    yield_pct DECIMAL(5,2),
    date_recorded DATE,
    source VARCHAR
)
""")

yield_data = [
    (1, 'MGS 3-Year', 3.18, '2026-07-08', 'BNM'),
    (2, 'MGS 5-Year', 3.35, '2026-07-08', 'BNM'),
    (3, 'MGS 7-Year', 3.50, '2026-07-08', 'BNM'),
    (4, 'MGS 10-Year', 3.61, '2026-07-08', 'BNM'),
    (5, 'MGS 20-Year', 3.85, '2026-07-08', 'BNM'),
    (6, 'BNM OPR', 2.75, '2026-05-07', 'BNM'),
]
con.executemany("INSERT OR REPLACE INTO bond_yields VALUES (?,?,?,?,?)", yield_data)
print(f"Inserted {len(yield_data)} bond yield records")

# Summary
con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'")
tables = con.fetchall()
total_rows = 0
for t in tables:
    count = con.execute(f"SELECT COUNT(*) FROM \"{t[0]}\"").fetchone()[0]
    total_rows += count
    print(f"  Table '{t[0]}': {count} rows")

print(f"\nTotal: {len(tables)} tables, {total_rows} total rows")
print(f"Database: {DB_PATH}")

# Copy to skill datasets dir
con.close()

import shutil
shutil.copy2(DB_PATH, SKILL_DB_PATH)
print(f"Copied to skill datasets: {SKILL_DB_PATH}")
size_mb = os.path.getsize(DB_PATH) / (1024*1024)
print(f"Database size: {size_mb:.1f} MB")
