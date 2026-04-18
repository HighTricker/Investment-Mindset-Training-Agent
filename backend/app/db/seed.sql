-- portfolio.db 种子数据
-- SSOT: ../../../开发文档/SQL_prompt_schema.md 第 192-198 行（cash_accounts）+ 第 232-245 行（user_settings）

-- ========================================
-- cash_accounts：4 条默认账户
-- 全部 amount=0, currency='CNY', is_active=1
-- 用户可在 P2.1 页面修改金额或增删账户
-- ========================================
INSERT INTO cash_accounts (name, amount, currency, is_active) VALUES
    ('日常消费卡',      0, 'CNY', 1),
    ('应急事件应对卡',   0, 'CNY', 1),
    ('5年及以上不动卡', 0, 'CNY', 1),
    ('资产卡',          0, 'CNY', 1);


-- ========================================
-- user_settings：1 条默认记录
-- 所有目标字段为 0，邮箱 NULL
-- 用户在 P2.1 页面设置目标，在 P5 页面设置邮箱（V2 阶段）
-- ========================================
INSERT INTO user_settings (
    target_monthly_living, target_living_currency,
    target_passive_income, target_passive_currency,
    target_cash_savings,   target_cash_currency,
    email
) VALUES (
    0, 'CNY',
    0, 'CNY',
    0, 'CNY',
    NULL
);
