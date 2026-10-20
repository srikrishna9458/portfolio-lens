-- 1. Transparent serviceable-fleet screen. Known failures override missing data.
SELECT brand,family,variant,max_ram_gb,weight_kg,ram_upgradeable,
CASE WHEN max_ram_gb<64 OR weight_kg>1.5 OR ram_upgradeable=0 THEN 'No match'
     WHEN max_ram_gb IS NULL OR weight_kg IS NULL OR ram_upgradeable IS NULL THEN 'Unresolved'
     ELSE 'Candidate - verify actual SKU' END AS fleet_fit
FROM products ORDER BY brand,family,variant;

-- 2. Research coverage, not market share.
SELECT * FROM v_brand_coverage ORDER BY brand;

-- 3. Keep historical positioning and current offer research separate.
SELECT p.brand,p.family,r.configuration,r.amount,r.currency,r.market,r.kind,
       r.observed_on,r.tax_basis,s.url
FROM prices r JOIN products p ON p.id=r.product_id JOIN sources s ON s.id=r.source_id
ORDER BY r.observed_on DESC;

-- 4. Evidence-backed change audit. Never infer product changes from a page hash alone.
SELECT c.changed_at,p.family,c.field,c.old_value,c.new_value,s.url
FROM changes c JOIN products p ON p.id=c.product_id JOIN sources s ON s.id=c.source_id
ORDER BY c.changed_at DESC;

-- 5. Lowest published starting weights, excluding unknowns.
SELECT brand,family,variant,weight_kg,notes FROM products
WHERE weight_kg IS NOT NULL ORDER BY weight_kg;
