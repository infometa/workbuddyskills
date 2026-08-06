-- 视图名称: dm.v_crm_member_with_sly
-- 用途: 会员维表 + 商龙门店映射表，支持通过 group_code/store_code 关联营业表
-- 来源: dim.dim_crm_member (a) LEFT JOIN dw.dw_sly_store_rel (b)
-- 作者: niuying
-- 日期: 2026-05-11

CREATE OR REPLACE VIEW dm.v_crm_member_with_sly AS
SELECT
    -- ① b 表的商龙云编号（统一集团 G 号 / 门店 C 号，覆盖 a 表的原始字段名，供业务关联使用）
    b.group_code                AS group_code,
    b.store_code                AS store_code,

    -- ③ b 表的门店维度字段（省市、管理类型等）
    b.province                  AS province,
    b.city                      AS city,
    b.region                    AS region,
    b.manage_type               AS manage_type,
    b.store_name                AS store_name,
    b.brand_name                AS brand_name,

    -- ④ a 表的会员基础信息（仅保留指定字段）
    a.mem_code,
    a.mem_name,
    a.country,
    a.province                  AS mem_province,
    a.city                      AS mem_city,
    a.county                    AS mem_county,
    a.mem_sex,
    a.mem_birthday,
    a.mem_age,
    a.mem_create_time,
    a.first_consume_time,
    a.first_people_qty,
    a.sale_type_typ,
    a.first_recv_money,
    a.first_real_income,
    a.first_table_typ,
    a.mem_res,
    a.mem_res_name,
    a.mem_mobile,
    a.mem_tag,
    a.mem_card_kind,
    a.mem_cert_no,
    a.mem_name_en,
    a.mem_work_unit,
    a.mem_job,
    a.mem_landline,
    a.mem_email,
    a.mem_address,
    a.mem_qq,
    a.mem_nation,
    a.mem_birthday_lunar,
    a.mem_invite_name,
    a.system,
    a.mem_constellation,
    a.invite_total,
    a.mem_card_type,
    a.info_improved_flag,
    a.last_consume_time,
    a.last_recharge_time,

    -- ⑤ 余额类字段（维表核心价值，必须保留）
    a.balance_principal,
    a.balance_gift,
    a.balance_cashback,
    a.balance_recharge,
    a.balance_score,

    -- ⑥ 其他
    a.etl_time,
    a.first_recharge_time,
    a.effective_coupon_num,
    a.card_num,
    a.mem_status
FROM dim.dim_crm_member AS a
LEFT JOIN dw.dw_sly_store_rel AS b
    ON a.store_code = b.mcid
   AND a.group_code = b.gcid;
