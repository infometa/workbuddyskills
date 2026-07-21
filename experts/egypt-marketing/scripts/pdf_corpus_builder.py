#!/usr/bin/env python3
"""
大马企业通 v3.2 PDF 语料库构建器
Download authoritative Malaysian business PDFs and extract plain text to Reference_Texts/.
Each file saved as .txt with metadata: pages, characters, extraction method.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# PDF Library - Authoritative Malaysian Business Reports
# ============================================================
PDF_LIBRARY = [
    {
        "id": "mida_codb_2024",
        "title": "Costs of Doing Business in Malaysia 2024",
        "publisher": "MIDA (Malaysian Investment Development Authority)",
        "url": "https://www.mida.gov.my/wp-content/uploads/2025/03/CODB_ENG_2024-FINAL.pdf",
        "category": "市场进入/建厂成本",
        "trigger": "BD-1/BD-2, DD-5",
        "key_content": "人工成本(按行业/技能)、水电费率、工业用地/厂房租金、物流运输成本、税务激励概览"
    },
    {
        "id": "pwc_doing_business_2025",
        "title": "Doing Business in Malaysia 2025",
        "publisher": "PwC Malaysia",
        "url": "https://www.pwc.com/my/en/assets/publications/2025/doing-business-in-malaysia-2025.pdf",
        "category": "外资准入/税务体系",
        "trigger": "BD-1, DD-3",
        "key_content": "税务体系详解、外资准入政策、公司设立流程"
    },
    {
        "id": "bnm_annual_report_2025",
        "title": "BNM Annual Report 2025",
        "publisher": "Bank Negara Malaysia",
        "url": "https://www.investmalaysia.gov.my/media/1uun2pd4/bank-negara-malaysia-annual-report-2025.pdf",
        "category": "宏观经济/货币政策",
        "trigger": "BD-1, DD-5",
        "key_content": "全年经济回顾、货币政策决策逻辑、金融体系稳定性评估、行业信贷质量分析"
    },
    {
        "id": "bnm_emr_2025",
        "title": "BNM Economic and Monetary Review 2025",
        "publisher": "Bank Negara Malaysia",
        "url": "https://www.investmalaysia.gov.my/media/c42pvntg/bank-negara-malaysia-economic-and-monetary-review-2025.pdf",
        "category": "行业分析/劳动力/外部部门",
        "trigger": "BD-1, DD-7",
        "key_content": "各行业增长深度分析、劳动力市场、通胀驱动因素、外部部门详细数据"
    },
    {
        "id": "worldbank_mem_oct2025",
        "title": "Malaysia Economic Monitor (October 2025)",
        "publisher": "World Bank",
        "url": "https://openknowledge.worldbank.org/bitstreams/39e33781-ca7f-4f11-90e9-462364f00077/download",
        "alt_urls": [
            "https://documents1.worldbank.org/curated/en/099100125221586664/pdf/P5004871a6f0730cc1b30e15df91200cf39.pdf",
            "https://documents.worldbank.org/en/publication/documents-reports/documentdetail/099100125221586664",
        ],
        "category": "国际视角/结构性挑战",
        "trigger": "BD-1, DD-7 (ESG)",
        "key_content": "马来西亚宏观经济展望(4.1%增长)、财政改革进展、结构性挑战、行业专题分析"
    },
    {
        "id": "mof_economic_2026",
        "title": "2026 Economic Outlook & Budget",
        "publisher": "Malaysia Ministry of Finance",
        "url": "https://belanjawan.mof.gov.my/pdf/belanjawan2026/economy/economic-2026.pdf",
        "category": "财政政策/预算",
        "trigger": "BD-1, DD-5",
        "key_content": "2026年国家预算案、财政政策方向、各行业预期增长率"
    },
    # Alternative URLs for fallback
    {
        "id": "bnm_annual_report_2025_alt",
        "title": "BNM Annual Report 2025 (Alt)",
        "publisher": "Bank Negara Malaysia",
        "url": "https://www.acccimserc.com/images/researchpdf/2026/20260331%20BNM%20Annual%20Report%202025.pdf",
        "category": "宏观经济/货币政策 (备用)",
        "trigger": "BD-1, DD-5 (fallback)",
        "key_content": "Same as primary BNM Annual Report 2025"
    },
]

# ============================================================
# Theoretical Foundation Library — open-access academic papers
# ============================================================
THEORETICAL_LIBRARY = [
    {
        "id": "dunning_eclectic_paradigm_2000",
        "title": "The Eclectic Paradigm as an Envelope for Economic and Business Theories of MNE Activity",
        "publisher": "John H. Dunning / International Business Review",
        "url": "https://courses.gdut.edu.cn/pluginfile.php/117847/mod_resource/content/1/Dunning%20Eclectic%20paradigm%202000.pdf",
        "category": "理论：FDI/国际生产理论",
        "trigger": "BD-1, DD-3 (market entry mode)",
        "key_content": "OLI范式（所有权、区位、内部化优势），解释企业为何、何地、以何种方式开展跨国经营"
    },
    {
        "id": "johanson_vahlne_uppsala_1977",
        "title": "The Internationalization Process of the Firm — A Model of Knowledge Development and Increasing Foreign Market Commitments",
        "publisher": "Johanson & Vahlne / Journal of International Business Studies",
        "url": "https://scispace.com/pdf/the-internationalization-process-of-the-firm-a-model-of-4aibougvsw.pdf",
        "alt_urls": [
            "https://link.springer.com/content/pdf/10.1057/palgrave.jibs.8490676.pdf",
        ],
        "category": "理论：国际化过程/Uppsala模型",
        "trigger": "BD-1, DD-3 (gradual internationalization)",
        "key_content": "心理距离、知识积累、市场承诺渐进增加，解释企业国际化路径选择"
    },
    {
        "id": "north_institutions_1991",
        "title": "Institutions",
        "publisher": "Douglass C. North / Journal of Economic Perspectives",
        "url": "https://web.pdx.edu/~nwallace/EHP/NorthInstitutions.pdf",
        "alt_urls": [
            "https://pubs.aeaweb.org/doi/pdfplus/10.1257/jep.5.1.97",
        ],
        "category": "理论：制度经济学",
        "trigger": "DD-5, DD-7 (country/institutional risk)",
        "key_content": "制度的定义、正式与非正式约束、制度变迁与交易成本，理解马来西亚的制度环境"
    },
    {
        "id": "acemoglu_institutions_longrun_2005",
        "title": "Institutions as a Fundamental Cause of Long-Run Growth",
        "publisher": "Acemoglu, Johnson & Robinson / NBER Working Paper 10481",
        "url": "https://economics.mit.edu/sites/default/files/publications/institutions-as-the-fundamental-cause-of-long-run-.pdf",
        "category": "理论：制度与增长",
        "trigger": "DD-5, DD-7 (institutional risk, governance)",
        "key_content": "攫取型 vs 包容性制度，制度差异作为长期经济增长的根本原因"
    },
    {
        "id": "prsgroup_icrg_methodology",
        "title": "International Country Risk Guide (ICRG) Methodology",
        "publisher": "PRS Group",
        "url": "https://www.prsgroup.com/wp-content/uploads/2012/11/icrgmethodology.pdf",
        "alt_urls": [
            "http://www.prsgroup.com/wp-content/uploads/2012/11/icrgmethodology.pdf",
        ],
        "category": "理论/方法：国家风险评估",
        "trigger": "DD-5 (country risk scoring)",
        "key_content": "政治、金融、经济风险指标体系，主权风险评分方法论"
    },
    {
        "id": "balassa_economic_integration_1961",
        "title": "Trade Creation and Trade Diversion in Deep Agreements",
        "publisher": "Mattoo, Mulabdic & Ruta / World Bank Policy Research Working Paper 8206",
        "url": "https://documents1.worldbank.org/curated/en/208101506520778449/pdf/WPS8206.pdf",
        "category": "理论：区域贸易协定/经济一体化",
        "trigger": "BD-1 (ASEAN/AEC market access)",
        "key_content": "贸易创造与贸易转移（Vinerian理论）、深度贸易协定、东盟/AEC框架下的市场进入分析"
    },
    {
        "id": "gereffi_governance_gvc_2005",
        "title": "The Governance of Global Value Chains",
        "publisher": "Gereffi, Humphrey & Sturgeon / Review of International Political Economy",
        "url": "https://www.soc.duke.edu/sloan_2004/Papers/governance_of_gvcs_final.pdf",
        "category": "理论：全球价值链治理",
        "trigger": "BD-1, DD-5 (supply chain, vendor selection)",
        "key_content": "五种GVC治理模式（层级、俘虏、关系、模块化、市场），供应商升级与权力关系"
    },
    {
        "id": "ifsb_corporate_governance_2024",
        "title": "IFSB-30 Revised Guiding Principles on Corporate Governance for Institutions Offering Islamic Financial Services",
        "publisher": "Islamic Financial Services Board",
        "url": "https://www.ifsb.org/wp-content/uploads/2024/01/IFSB-30-Revised-Guiding-Principles-on-Corporate-Governance-for-IIFS.pdf",
        "category": "理论/规范：伊斯兰金融治理",
        "trigger": "BD-1, DD-3 (Islamic finance, halal economy)",
        "key_content": "伊斯兰金融服务机构的治理原则、Shariah合规、透明度与利益相关者责任"
    },
    {
        "id": "adb_asean_integration_2012",
        "title": "ASEAN Economic Integration: Taking Stock and Moving Forward",
        "publisher": "Hill & Menon / ADB Working Paper No. 69",
        "url": "https://aric.adb.org/pdf/workingpaper/WP69_Hill_Menon_ASEAN_Economic_Integration.pdf",
        "alt_urls": [
            "https://www.adb.org/sites/default/files/publication/28551/wp69-hill-menon-asean-economic-integration.pdf",
        ],
        "category": "理论/政策：东盟一体化",
        "trigger": "BD-1 (ASEAN/AEC strategy)",
        "key_content": "东盟经济一体化进程、AEC蓝图、区域内贸易投资自由化与马来西亚角色"
    },
    {
        "id": "due_diligence_framework_2018",
        "title": "A Framework for Operational Due Diligence in Mergers and Acquisitions",
        "publisher": "Korosec & Bamberger / DTU / EurOMA 2017",
        "url": "https://backend.orbit.dtu.dk/ws/portalfiles/portal/150767461/EurOMA_2017_A_Operational_Due_Diligence_Framework_FINAL_1_.pdf",
        "alt_urls": [
            "https://link.springer.com/content/pdf/10.1007/s11740-018-0842-z.pdf",
        ],
        "category": "理论/方法：M&A尽调",
        "trigger": "DD-3, DD-5 (M&A operational due diligence)",
        "key_content": "运营尽调框架、评估方法、运营绩效改善与并购决策"
    },
]

# ============================================================
# Deep Boost Library — risk, legal, ESG, local research, sectoral reports
# ============================================================
BOOST_LIBRARY = [
    {
        "id": "strategicratings_sovereign_methodology",
        "title": "Sovereign Ratings Methodology",
        "publisher": "Strategic Ratings",
        "url": "https://strategicratings.com/uploads/sovereignRatingsBrochure24May20.pdf",
        "category": "方法：主权信用评级",
        "trigger": "DD-5, DD-7 (sovereign credit risk)",
        "key_content": "主权信用评级方法、经济指标、政治与制度因素、偿债能力分析"
    },
    {
        "id": "worldbank_sovereign_methodology",
        "title": "Sovereign Ratings Methodology",
        "publisher": "World Bank Group",
        "url": "https://connect4impact.worldbank.org/system/files/2026-06/Sovereign%20Ratings%20Methodology_0.pdf",
        "category": "方法：主权评级/债务可持续性",
        "trigger": "DD-5 (sovereign risk, debt sustainability)",
        "key_content": "世界银行主权评级框架、债务可持续性、制度与政策评估"
    },
    {
        "id": "coface_country_sector_handbook_2026",
        "title": "Country and Sector Risks Handbook 2026",
        "publisher": "Coface (Allianz Trade)",
        "url": "https://www.coface.com.sg/content/download/96624/file/202602%20Country%20and%20Sector%20Risks%20Handbook%202026.pdf",
        "category": "方法/实务：国别与行业风险",
        "trigger": "DD-5, DD-7 (country and sector risk assessment)",
        "key_content": "160+ 国别风险评估、行业风险模型、商业环境评级、马来西亚风险定位"
    },
    {
        "id": "companies_act_2016",
        "title": "Companies Act 2016 (Act 777)",
        "publisher": "Attorney General's Chambers of Malaysia",
        "url": "https://lom.agc.gov.my/ilims/upload/portal/akta/outputaktap/aktaBI_20160915_CompaniesAct2016Act777.pdf",
        "category": "法律：公司法",
        "trigger": "DD-3, DD-5 (company incorporation, directors, shareholders)",
        "key_content": "马来西亚公司注册、董事责任、股东权利、公司秘书、清算与重组"
    },
    {
        "id": "mida_companies_act_2016_guide",
        "title": "Companies Act 2016: Transforming Malaysia's Corporate Landscape",
        "publisher": "MIDA",
        "url": "https://www.mida.gov.my/wp-content/uploads/2020/09/20170623140246_May2017-1.pdf",
        "category": "法律/实务：公司法指南",
        "trigger": "BD-1, DD-3 (company law practical guide)",
        "key_content": "2016年公司法的核心变化、外资公司实务影响、合规要点"
    },
    {
        "id": "employment_act_1955",
        "title": "Employment Act 1955 (Act 265)",
        "publisher": "Attorney General's Chambers of Malaysia / InvestMalaysia",
        "url": "https://www.investmalaysia.gov.my/media/felj30g0/employment-act-1955.pdf",
        "category": "法律：劳动法",
        "trigger": "DD-3, DD-7 (labour law, employment compliance)",
        "key_content": "马来西亚雇佣合同、工资、工时、解雇、外籍劳工、劳工合规"
    },
    {
        "id": "pdpa_2010",
        "title": "Personal Data Protection Act 2010 (Act 709)",
        "publisher": "Attorney General's Chambers of Malaysia / InvestMalaysia",
        "url": "https://www.investmalaysia.gov.my/media/3x4fsqum/personal-data-protection-act-2010.pdf",
        "category": "法律：数据保护",
        "trigger": "DD-3, DD-7 (data protection, PDPA compliance)",
        "key_content": "个人数据保护原则、数据用户责任、跨境数据传输、处罚与合规"
    },
    {
        "id": "unctad_model_law_competition",
        "title": "Model Law on Competition",
        "publisher": "UNCTAD",
        "url": "https://unctad.org/system/files/official-document/tdrbpconf7d8_en.pdf",
        "category": "法律/规范：竞争法",
        "trigger": "DD-3, DD-5 (competition law, anti-trust, merger control)",
        "key_content": "竞争法模型条款、卡特尔、滥用支配地位、并购控制、执法框架（马来西亚CA 2010被Cloudflare拦截时的替代规范）"
    },
    {
        "id": "msci_esg_methodology",
        "title": "MSCI ESG Ratings Methodology",
        "publisher": "MSCI",
        "url": "https://www.msci.com/documents/1296102/34424357/MSCI+ESG+Ratings+Methodology.pdf",
        "category": "方法：ESG评级",
        "trigger": "DD-7 (ESG due diligence, sustainability risk)",
        "key_content": "MSCI ESG评级框架、行业关键议题、风险暴露与管理评分、争议事件"
    },
    {
        "id": "kri_state_of_households_2024",
        "title": "State of Households 2024",
        "publisher": "Khazanah Research Institute",
        "url": "https://cdn.prod.website-files.com/684b55df28cddcbe52b406f2/68a7ba79c980e6b7787ac8bd_-WEBSITE--20SoH-202024-20Report-20FINAL-20v2.pdf",
        "category": "本土研究：家庭/社会经济",
        "trigger": "BD-1, DD-5 (domestic demand, household income, inequality)",
        "key_content": "马来西亚家庭收入、财富、不平等、消费模式、社会流动性"
    },
    {
        "id": "upm_malaysian_economy_structure",
        "title": "Structure of the Malaysian Economy: An Input-Output Analysis",
        "publisher": "Universiti Putra Malaysia / Institute of Agricultural and Food Policy Studies",
        "url": "https://cdn.prod.website-files.com/684b55df28cddcbe52b406f2/68b7ec31ecac86d5bbd19bdf_Structure-20of-20the-20Malaysian-20Economy_An-20Input_Output-20Analysis_full-20report.pdf",
        "category": "本土研究：经济结构/投入产出",
        "trigger": "BD-1, DD-5 (economic structure, sectoral linkages, multiplier effects)",
        "key_content": "马来西亚投入产出表、产业关联、乘数效应、关键上下游部门"
    },
    {
        "id": "mida_ee_sib_2024",
        "title": "Malaysia's Electrical and Electronics Industry - Strategic Information Brief 2024",
        "publisher": "MIDA",
        "url": "https://www.mida.gov.my/wp-content/uploads/2026/03/EE-SIB-2024.pdf",
        "category": "行业：电子电气",
        "trigger": "BD-1, DD-5 (E&E, semiconductor, electronics manufacturing)",
        "key_content": "马来西亚电子电气产业生态、全球价值链定位、外资机会、激励政策"
    },
    {
        "id": "miti_ee_industry",
        "title": "Electrical and Electronics (E&E) Industry",
        "publisher": "Ministry of Investment, Trade and Industry (MITI)",
        "url": "https://www.miti.gov.my/miti/resources/6._Electrical_and_Electronics_Industry_.pdf",
        "category": "行业：电子电气",
        "trigger": "BD-1, DD-5 (E&E industry overview)",
        "key_content": "电子电气产业四个子行业、产业规模、出口、政府支持措施"
    },
    {
        "id": "nimp_ee_industry",
        "title": "New Industrial Master Plan 2030 - Electrical and Electronics Industry",
        "publisher": "NIMP 2030 Secretariat / MITI",
        "url": "https://www.nimp2030.gov.my/nimp2030/modules_resources/bookshelf/e-03-Sectoral_NIMP-Electrical_Electronics_Industry/e-03-Sectoral_NIMP-Electrical_Electronics_Industry.pdf",
        "category": "行业/政策：电子电气与NIMP2030",
        "trigger": "BD-1, DD-5 (E&E, NIMP 2030, industrial policy)",
        "key_content": "NIMP 2030电子电气行业蓝图、目标、催化项目、投资激励"
    },
    {
        "id": "mpob_palm_oil_overview_2025",
        "title": "Overview of the Malaysian Oil Palm Industry 2025",
        "publisher": "Malaysian Palm Oil Board (MPOB)",
        "url": "https://bepi.mpob.gov.my/images/overview/Overview2025.pdf",
        "category": "行业：棕油/农业",
        "trigger": "BD-1, DD-5 (palm oil, agriculture, commodities)",
        "key_content": "马来西亚棕油产业表现、种植面积、产量、出口、价格、劳动力与可持续性"
    },
    # ===== Local research & digital economy (本土深度补强) =====
    {
        "id": "dosm_economic_census_2023",
        "title": "Economic Census 2023: All Sectors",
        "publisher": "Department of Statistics Malaysia (DOSM)",
        "url": "https://storage.dosm.gov.my/census/census_economy_2022.pdf",
        "category": "本土研究：经济普查/产业结构",
        "trigger": "BD-1, DD-5 (economic structure, sectoral distribution, SMEs)",
        "key_content": "马来西亚2022年经济普查、各行业企业数量、就业、增加值、SME分布、区域结构"
    },
    {
        "id": "kri_ai_governance_2025",
        "title": "AI Governance in Malaysia: Risks, Challenges and Pathways Forward",
        "publisher": "Khazanah Research Institute",
        "url": "https://cdn.prod.website-files.com/684b55df28cddcbe52b406f2/690d93ef2c60698584f6b3f3_KRI-20AIIG-20Report-20Final_v4.7-20-upload-.pdf",
        "category": "本土研究：人工智能治理",
        "trigger": "BD-1, DD-7 (AI policy, digital regulation, emerging tech risk)",
        "key_content": "马来西亚AI治理格局、风险类别、监管挑战、政策建议、国家AI办公室"
    },
    {
        "id": "kri_climate_crisis_2024",
        "title": "What Is To Be Done? Confronting Climate Crisis in Malaysia",
        "publisher": "Khazanah Research Institute",
        "url": "https://cdn.prod.website-files.com/684b55df28cddcbe52b406f2/690d93edbb6805f44c221d57_KRI-20Report_What-20Is-20To-20Be-20Done-20--20CCCIM.pdf",
        "category": "本土研究：气候政策",
        "trigger": "BD-1, DD-7 (climate risk, ESG, energy transition)",
        "key_content": "马来西亚气候战略、气候数据、适应需求、气候公平、政策路径"
    },
    {
        "id": "mdec_bcg_digital_economy_2023",
        "title": "Harnessing the Power of Technology: Building a Strong Digital Economy for Malaysia's Future",
        "publisher": "MDEC / BCG",
        "url": "https://platform.mdec.com.my/cmscdn/v1.aspx?GUID=b7aed424-3c73-44ef-8e64-370d7bd38f65&file=Harnessing%20the%20Power%20of%20Technology%20-Building%20a%20Strong%20Digital%20Economy%20for%20Malaysia%E2%80%99s%20Future.pdf",
        "category": "本土研究：数字经济",
        "trigger": "BD-1, DD-5 (digital economy, business digitalisation)",
        "key_content": "马来西亚商业数字化程度、数字技术采用、未来数字经济增长路径"
    },
    {
        "id": "mdec_regional_digital_gateway_2026",
        "title": "Malaysia as a Regional Digital Economy Gateway",
        "publisher": "MDEC / KFM",
        "url": "https://platform.mdec.com.my/cmscdn/v1.aspx?GUID=09cba31a-9d0c-4c7a-b8df-6644b6322278&file=KFM%20x%20MDEC_06022026.pdf",
        "category": "本土研究：数字经济/投资",
        "trigger": "BD-1, DD-5 (digital investment, data centres, regional gateway)",
        "key_content": "马来西亚作为区域数字经济门户、数字投资趋势、数据中心与房地产"
    },
    # ===== Sector specialization (行业专项补强) =====
    {
        "id": "hdc_halal_master_plan_2030",
        "title": "Halal Industry Master Plan 2030",
        "publisher": "Halal Development Corporation (HDC)",
        "url": "https://www.hdcglobal.com/wp-content/uploads/2020/02/Halal-Industri-Master-Plan-2030.pdf",
        "category": "行业：清真产业",
        "trigger": "BD-1, DD-5 (halal industry, halal ecosystem, export)",
        "key_content": "马来西亚清真产业2030蓝图、生态系统、标准与认证、全球市场定位"
    },
    {
        "id": "nimp_halal_industry",
        "title": "New Industrial Master Plan 2030 - Halal Industry",
        "publisher": "NIMP 2030 Secretariat / MITI",
        "url": "https://www.nimp2030.gov.my/nimp2030/modules_resources/bookshelf/e-10-Sectoral_NIMP-Halal_Industry/e-10-Sectoral_NIMP-Halal_Industry.pdf",
        "category": "行业/政策：清真产业与NIMP2030",
        "trigger": "BD-1, DD-5 (halal, NIMP 2030, industrial policy)",
        "key_content": "NIMP 2030清真行业蓝图、目标、催化项目、投资激励"
    },
    {
        "id": "mida_pharmaceutical_sib_2024",
        "title": "Malaysia's Pharmaceutical Industry - Strategic Information Brief 2024",
        "publisher": "MIDA",
        "url": "https://www.mida.gov.my/wp-content/uploads/2025/12/7.-Pharmaceutical-SIB-2024.pdf",
        "category": "行业：制药/生命科学",
        "trigger": "BD-1, DD-5 (pharmaceutical, life sciences, medical devices)",
        "key_content": "马来西亚制药产业生态、新药与仿制药、投资激励、监管与市场"
    },
    {
        "id": "miti_pharmaceutical_industry",
        "title": "Pharmaceutical Industry",
        "publisher": "Ministry of Investment, Trade and Industry (MITI)",
        "url": "https://www.miti.gov.my/miti/resources/13._Pharmaceutical_Industry_.pdf",
        "category": "行业：制药/生命科学",
        "trigger": "BD-1, DD-5 (pharmaceutical industry overview)",
        "key_content": "马来西亚制药行业历史、产业规模、监管框架、政府支持措施"
    },
    {
        "id": "nimp_pharmaceutical_industry",
        "title": "New Industrial Master Plan 2030 - Pharmaceutical Industry",
        "publisher": "NIMP 2030 Secretariat / MITI",
        "url": "https://www.nimp2030.gov.my/nimp2030/modules_resources/bookshelf/e-04-Sectoral_NIMP-Pharmaceutical_Industry/e-04-Sectoral_NIMP-Pharmaceutical_Industry.pdf",
        "category": "行业/政策：制药与NIMP2030",
        "trigger": "BD-1, DD-5 (pharmaceutical, NIMP 2030, industrial policy)",
        "key_content": "NIMP 2030制药行业蓝图、目标、催化项目、投资激励"
    },
    {
        "id": "petronas_financial_operational_2024",
        "title": "PETRONAS Financial and Operational Report FY2024",
        "publisher": "PETRONAS",
        "url": "https://www.petronas.com/sites/default/files/uploads/content/2025/Financial%20Operational%20Report%20FY%202024.pdf",
        "category": "行业：石油天然气",
        "trigger": "BD-1, DD-5 (oil & gas, energy sector, national oil company)",
        "key_content": "马来西亚国家石油2024财务与运营表现、油气产量、下游业务、资本支出"
    },
    {
        "id": "mpob_palm_oil_overview_2024",
        "title": "Overview of the Malaysian Oil Palm Industry 2024",
        "publisher": "Malaysian Palm Oil Board (MPOB)",
        "url": "https://bepi.mpob.gov.my/images/overview/Overview2024.pdf",
        "category": "行业：棕油/农业",
        "trigger": "BD-1, DD-5 (palm oil, agriculture, commodities)",
        "key_content": "马来西亚棕油产业2024年表现、种植面积、产量、出口、价格、劳动力"
    },
]


def download_pdf(url: str, dest_path: Path, timeout: int = 120) -> bool:
    """Download a PDF using requests with SSL fallback and retries."""
    try:
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except ImportError:
        requests = None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,application/octet-stream,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    # Bypass local system proxies that may break SSL handshakes for some hosts
    proxies = {"http": None, "https": None}

    for attempt in range(3):
        try:
            if requests:
                for verify in [True, False]:
                    try:
                        r = requests.get(url, headers=headers, timeout=timeout, verify=verify, allow_redirects=True, proxies=proxies)
                        if r.status_code == 200 and r.content.startswith(b"%PDF"):
                            dest_path.write_bytes(r.content)
                            return True
                        elif r.status_code == 200 and b"%PDF" in r.content[:1000]:
                            dest_path.write_bytes(r.content)
                            return True
                    except Exception as e:
                        print(f"  Attempt {attempt+1}/3 (requests verify={verify}) failed: {e}")
                        continue
            # Fallback to urllib
            from urllib.request import Request, urlopen
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if data.startswith(b"%PDF"):
                    dest_path.write_bytes(data)
                    return True
        except Exception as e:
            print(f"  Attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(5)
    return False


def extract_text_pypdf2(pdf_path: Path) -> Optional[str]:
    """Extract text using PyPDF2 (fast, basic)."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n--- PAGE BREAK ---\n\n".join(pages)
    except ImportError:
        return None
    except Exception as e:
        print(f"    PyPDF2 error: {e}")
        return None


def extract_text_pdfplumber(pdf_path: Path) -> Optional[str]:
    """Extract text using pdfplumber (better table handling)."""
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n--- PAGE BREAK ---\n\n".join(pages)
    except ImportError:
        return None
    except Exception as e:
        print(f"    pdfplumber error: {e}")
        return None


def generate_summary(text: str, max_lines: int = 50) -> str:
    """Generate a summary from the first N lines of extracted text."""
    lines = text.split("\n")
    meaningful_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 3]
    return "\n".join(meaningful_lines[:max_lines])


def build_corpus(root: Path, dry_run: bool = False, library: List[Dict] = None) -> List[Dict]:
    """Download PDFs and extract text to Reference_Texts/."""
    ref_dir = root / "Reference_Texts"
    ref_dir.mkdir(parents=True, exist_ok=True)

    if library is None:
        library = PDF_LIBRARY

    results = []
    for pdf_def in library:
        pdf_id = pdf_def["id"]
        pdf_path = ref_dir / f"{pdf_id}.pdf"
        txt_path = ref_dir / f"{pdf_id}.txt"
        meta_path = ref_dir / f"{pdf_id}_meta.json"

        print(f"\n  [{pdf_def['publisher']}] {pdf_def['title']}")

        # Skip alt if primary succeeded
        if "_alt" in pdf_id:
            primary_id = pdf_id.replace("_alt", "")
            primary_txt = ref_dir / f"{primary_id}.txt"
            if primary_txt.exists():
                print(f"    Skipping (primary exists)")
                continue

        # Check if already extracted
        if txt_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            results.append(meta)
            print(f"    Already extracted: {meta.get('pages', '?')} pages, {meta.get('chars', 0):,} chars")
            continue

        # If PDF exists but no txt/meta (e.g. user manually placed it), extract only
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            print(f"    PDF already exists, extracting text only...")
            downloaded = True
        else:
            # Download PDF
            print(f"    Downloading from {pdf_def['url'][:80]}...")
            if dry_run:
                print("    [DRY-RUN] Would download and extract")
                results.append({"id": pdf_id, "status": "dry-run", "title": pdf_def["title"], "publisher": pdf_def["publisher"]})
                continue

            downloaded = download_pdf(pdf_def["url"], pdf_path)
            # Try alternative URLs
            if not downloaded:
                for alt_url in pdf_def.get("alt_urls", []):
                    print(f"    Trying alternative URL: {alt_url[:80]}...")
                    if download_pdf(alt_url, pdf_path):
                        downloaded = True
                        break
        # Try alternative URLs
        if not downloaded:
            for alt_url in pdf_def.get("alt_urls", []):
                print(f"    Trying alternative URL: {alt_url[:80]}...")
                if download_pdf(alt_url, pdf_path):
                    downloaded = True
                    break

        if not downloaded:
            print(f"    FAILED to download")
            results.append({"id": pdf_id, "status": "download_failed", "title": pdf_def["title"]})
            continue

        pdf_size = pdf_path.stat().st_size
        print(f"    Downloaded: {pdf_size:,} bytes")

        # Extract text - try pdfplumber first, then PyPDF2
        text = extract_text_pdfplumber(pdf_path)
        method = "pdfplumber" if text else None
        if not text:
            text = extract_text_pypdf2(pdf_path)
            method = "pypdf2" if text else None

        if text is None:
            print(f"    WARNING: No text extraction library available. Installing pdfplumber...")
            if not dry_run:
                import subprocess
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "pdfplumber", "PyPDF2", "-q"],
                    check=False, timeout=60
                )
                text = extract_text_pdfplumber(pdf_path) or extract_text_pypdf2(pdf_path)

        if text is None:
            print(f"    Text extraction FAILED. Saving PDF only.")
            results.append({"id": pdf_id, "status": "extraction_failed", "title": pdf_def["title"]})
            continue

        # Count pages (approximate from page breaks)
        pages = text.count("--- PAGE BREAK ---") + 1
        chars = len(text)
        lines_count = text.count("\n") + 1

        # Write extracted text
        txt_path.write_text(text, encoding="utf-8")
        print(f"    Extracted: ~{pages} pages, {chars:,} chars, {lines_count} lines")

        # Write metadata
        meta = {
            "id": pdf_id,
            "title": pdf_def["title"],
            "publisher": pdf_def["publisher"],
            "category": pdf_def["category"],
            "trigger": pdf_def["trigger"],
            "key_content": pdf_def["key_content"],
            "url": pdf_def["url"],
            "pages": pages,
            "chars": chars,
            "lines": lines_count,
            "pdf_size_bytes": pdf_size,
            "extraction_date": datetime.now().isoformat(),
            "extraction_method": method or "unknown",
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(meta)

    return results


def generate_corpus_report(results: List[Dict], ref_dir: Path) -> str:
    """Generate a summary report of the corpus build."""
    lines = []
    lines.append(f"# 大马企业通 Reference_Texts Corpus Build Report")
    lines.append(f"> Generated: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total documents | {len(results)} |")

    total_pages = sum(r.get("pages", 0) for r in results)
    total_chars = sum(r.get("chars", 0) for r in results)
    lines.append(f"| Total pages | {total_pages} |")
    lines.append(f"| Total characters | {total_chars:,} |")
    lines.append("")
    lines.append("## Documents")
    lines.append("")
    lines.append("| # | Document | Publisher | Pages | Characters | Status |")
    lines.append("|---|----------|-----------|-------|------------|--------|")
    for i, r in enumerate(results, 1):
        pages = r.get("pages", "?")
        chars = r.get("chars", 0)
        status = r.get("status", "ok")
        title = r.get("title", r.get("id", "unknown"))
        publisher = r.get("publisher", r.get("id", "unknown"))
        chars_str = f"{chars:,}" if isinstance(chars, int) and chars > 0 else str(chars)
        lines.append(f"| {i} | {title} | {publisher} | {pages} | {chars_str} | {status} |")

    lines.append("")
    lines.append("## Agent Usage")
    lines.append("")
    lines.append("Reference_Texts/ is now the primary corpus for qualitative analysis. When the agent needs:")
    lines.append("- **MIDA CODB**: construction/manufacturing costs, utility rates, industrial land prices")
    lines.append("- **PwC Doing Business**: tax system, foreign equity rules, company setup procedures")
    lines.append("- **BNM Annual Report**: economic outlook, monetary policy, GDP, CPI, sectoral analysis")
    lines.append("- **BNM EMR**: deep-dive sector growth, labour market, external sector")
    lines.append("- **World Bank MEM**: international perspective, structural reforms, ESG context")
    lines.append("- **MOF Economic 2026**: national budget, fiscal policy, industry growth forecasts")
    lines.append("- **Dunning (2000) / OLI paradigm**: foreign entry mode, ownership/location/internalization advantages")
    lines.append("- **Johanson & Vahlne (1977) / Uppsala model**: gradual internationalization, psychic distance")
    lines.append("- **North (1991) / Acemoglu et al. (2005)**: institutional economics, country risk, governance")
    lines.append("- **PRS ICRG Methodology**: political/financial/economic risk scoring")
    lines.append("- **Balassa (1961) / ADB ASEAN**: regional economic integration, AEC, trade creation/diversion")
    lines.append("- **Gereffi et al. (2005) / GVC governance**: global value chains, supplier governance")
    lines.append("- **IFSB-30**: Islamic finance governance, Shariah compliance")
    lines.append("- **Korosec & Bamberger (2018)**: M&A operational due diligence framework")
    lines.append("- **Strategic Ratings / World Bank sovereign methodology**: sovereign credit risk and debt sustainability")
    lines.append("- **Coface Country & Sector Handbook 2026**: practical country/sector risk assessment for Malaysia")
    lines.append("- **Companies Act 2016 / MIDA guide**: company law, directors, shareholders, compliance")
    lines.append("- **Employment Act 1955 / PDPA 2010**: labour law and data protection compliance")
    lines.append("- **UNCTAD Model Law on Competition**: competition law framework (fallback for Malaysia CA 2010)")
    lines.append("- **MSCI ESG Methodology**: ESG due diligence and ratings framework")
    lines.append("- **KRI State of Households 2024 / UPM Input-Output Analysis**: local research on households and economic structure")
    lines.append("- **MIDA/MITI/NIMP E&E Industry / MPOB Palm Oil**: sectoral deep-dives for E&E, semiconductors, palm oil")
    lines.append("")
    lines.append("> The agent should read the relevant .txt file BEFORE answering questions that fall within these domains.")
    lines.append("> Each _meta.json file contains full metadata for programmatic access.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="大马企业通 PDF 语料库构建器")
    parser.add_argument("--root", default=None, help="Plugin root directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without downloading")
    parser.add_argument("--report-only", action="store_true", help="Only regenerate corpus report from existing files")
    args = parser.parse_args()

    # Determine root — look for plugin root (where .codebuddy-plugin/plugin.json exists)
    if args.root:
        root = Path(args.root)
    else:
        # Search upward from script location
        current = Path(__file__).resolve().parent.parent
        while current != current.parent:
            if (current / ".codebuddy-plugin" / "plugin.json").exists():
                root = current
                break
            current = current.parent
        else:
            root = Path.cwd()

    print(f"大马企业通 PDF 语料库构建器 v3.2")
    print(f"Root: {root}")
    print(f"Target: Reference_Texts/")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")

    ref_dir = root / "Reference_Texts"

    if args.report_only:
        # Regenerate report from existing meta files
        results = []
        for meta_file in sorted(ref_dir.glob("*_meta.json")):
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            results.append(meta)
        report = generate_corpus_report(results, ref_dir)
        report_path = ref_dir / "CORPUS_BUILD_REPORT.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\nReport regenerated: {report_path}")
        print(f"{len(results)} documents indexed, {sum(r.get('pages',0) for r in results)} pages total")
        return

    # Install extraction libraries
    if not args.dry_run:
        import subprocess
        print("Checking text extraction libraries...")
        try:
            import pdfplumber
            print("  pdfplumber: OK")
        except ImportError:
            print("  Installing pdfplumber...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pdfplumber", "-q"], check=False, timeout=60)
        try:
            from PyPDF2 import PdfReader
            print("  PyPDF2: OK")
        except ImportError:
            print("  Installing PyPDF2...")
            subprocess.run([sys.executable, "-m", "pip", "install", "PyPDF2", "-q"], check=False, timeout=60)

    # Build corpus from business reports, theoretical foundation papers, and deep boost library
    full_library = PDF_LIBRARY + THEORETICAL_LIBRARY + BOOST_LIBRARY
    results = build_corpus(root, dry_run=args.dry_run, library=full_library)

    # Generate report
    report = generate_corpus_report(results, ref_dir)
    report_path = ref_dir / "CORPUS_BUILD_REPORT.md"
    if not args.dry_run:
        report_path.write_text(report, encoding="utf-8")
        print(f"\nCorpus build report: {report_path}")

    # Summary
    ok = sum(1 for r in results if r.get("status", "ok") == "ok")
    failed = sum(1 for r in results if r.get("status") == "download_failed" or r.get("status") == "extraction_failed")
    total_pages = sum(r.get("pages", 0) for r in results if r.get("pages"))
    total_chars = sum(r.get("chars", 0) for r in results if r.get("chars"))
    print(f"\n=== CORPUS BUILD {'(DRY-RUN)' if args.dry_run else 'COMPLETE'} ===")
    print(f"  Documents: {len(results)} ({ok} ok, {failed} failed)")
    print(f"  Pages: {total_pages}")
    print(f"  Characters: {total_chars:,}")
    print(f"  Target: {ref_dir}")


if __name__ == "__main__":
    main()
