-- 视图名称: dm.v_crm_member_card_with_sly
-- 用途: 会员卡明细表 + 商龙门店映射表，支持通过 group_code/store_code 关联营业表
-- 来源: dw.dwd_crm_member_card_p_store (a) LEFT JOIN dw.dw_sly_store_rel (b)
-- 作者: niuying
-- 日期: 2026-05-11

CREATE OR REPLACE VIEW dm.v_crm_member_card_with_sly AS
SELECT
    -- ① b 表的商龙云编号（统一集团 G 号 / 门店 C 号，覆盖 a 表的原始字段名，供业务关联使用）
    b.group_code                AS group_code,
    b.store_code                AS store_code,

    -- ③ a 表字段（按用户指定列表保留）
    a.card_no,
    a.card_id,
    a.card_type_source,
    a.card_status,
    a.open_shop_id,
    a.last_recharge_shop_id,
    a.last_consume_shop_id,
    a.saled_pos_code,
    a.validate_type,
    a.saled_shop_code,
    a.card_mobile,
    a.member_id,
    a.production_card_id,
    a.saled_shop_name,
    a.open_shop_name,
    a.card_type_id,
    a.card_type_name,
    a.card_status_name,
    a.card_sold_time,
    a.card_charge,
    a.validate_begin_time,
    a.validate_end_time,
    a.total_consume_all_money,
    a.total_consume_all_times,
    a.total_consume_coupon,
    a.total_consume_time,
    a.total_consume_time_times,
    a.total_recharge_time,
    a.total_recharge_time_times,
    a.total_recharge_score,
    a.total_recharge_score_times,
    a.total_consume_score,
    a.total_consume_score_times,
    a.total_recharge_money,
    a.total_recharge_times,
    a.total_recharge_donated_money,
    a.total_consume_donated_money,
    a.total_consume_cashback,
    a.total_recharge_cashback,
    a.last_consume_time,
    a.last_consume_shop_name,
    a.last_consume_shop_code,
    a.last_recharge_time,
    a.last_recharge_shop_name,
    a.last_recharge_shop_code,
    a.balance_principal,
    a.balance_point,
    a.balance_gift,
    a.balance_times,
    a.balance_cashback,
    -- open_id 字段名含中文括号，请确认实际字段名是否为 open_id
    -- a.open_id                   AS open_id,
    a.is_subscribed,
    a.lastime,                   -- 疑似拼写错误，请确认字段名
    a.version,
    a.bindings,
    a.unionid,
    a.card_type_validity_begin,
    a.card_type_validity_end,
    a.card_type_validity_days,
    a.card_type_occur,
    a.card_type_source_name,
    a.company_id,
    a.saled_shop_id,
    a.note,
    a.create_time,
    a.update_time,
    a.last_followorcancelfollow_time,
    a.card_mobile_area,
    a.total_consume_money,
    a.balance_growth,
    a.is_main,
    a.total_recharge_invoice_money,
    a.import_invoice_amount,
    a.first_consume_time,
    a.first_consume_shop_id,
    a.first_consume_all_money
FROM dw.dwd_crm_member_card_p_store AS a
LEFT JOIN dw.dw_sly_store_rel AS b
    ON a.store_code = b.mcid
   AND a.group_code = b.gcid;
