-- ============================================================
-- Savour Foods — Supabase Schema
-- Menu tables (cleaned) + Ordering System
-- ============================================================

-- ─── EXTENSIONS ──────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- for gen_random_uuid()


-- ─── DROP ORDER TABLES FIRST (depend on menu tables) ─────────
DROP TABLE IF EXISTS order_items   CASCADE;
DROP TABLE IF EXISTS orders        CASCADE;

-- ─── DROP MENU TABLES ────────────────────────────────────────
DROP TABLE IF EXISTS dish_sub_options CASCADE;
DROP TABLE IF EXISTS dish_options      CASCADE;
DROP TABLE IF EXISTS dishes            CASCADE;
DROP TABLE IF EXISTS sub_categories    CASCADE;
DROP TABLE IF EXISTS categories        CASCADE;


-- ============================================================
-- 1. CATEGORIES
-- ============================================================
CREATE TABLE categories (
    id       INT          PRIMARY KEY,
    name     VARCHAR(120) NOT NULL,
    status   SMALLINT     NOT NULL DEFAULT 1,   -- 1 = active
    priority INT          NOT NULL DEFAULT 0
);

INSERT INTO categories VALUES (63928, 'New Arrivals',      1, 16);
INSERT INTO categories VALUES (47790, 'Deals',             1, 15);
INSERT INTO categories VALUES (47786, 'Chicken Pulao',     1, 14);
INSERT INTO categories VALUES (47785, 'Savour Krispo',     1, 13);
INSERT INTO categories VALUES (47791, 'Chicken',           1, 12);
INSERT INTO categories VALUES (63929, 'Meals',             1, 11);
INSERT INTO categories VALUES (47794, 'Sweet',             1, 10);
INSERT INTO categories VALUES (47793, 'Drinks',            1,  9);
INSERT INTO categories VALUES (47789, 'Side Orders',       1,  8);
INSERT INTO categories VALUES (47792, 'Daigh Orders',      1,  7);
INSERT INTO categories VALUES (53259, 'Honey Munch Menu',  1,  1);


-- ============================================================
-- 2. SUB_CATEGORIES
-- ============================================================
CREATE TABLE sub_categories (
    id          INT          PRIMARY KEY,
    category_id INT          NOT NULL REFERENCES categories(id),
    name        VARCHAR(120) NOT NULL,
    status      SMALLINT     NOT NULL DEFAULT 1
);

INSERT INTO sub_categories VALUES (90068, 63928, 'New Arrivals',     1);
INSERT INTO sub_categories VALUES (59681, 47790, 'Deals',            1);
INSERT INTO sub_categories VALUES (59677, 47786, 'Chicken Pulao',    1);
INSERT INTO sub_categories VALUES (59676, 47785, 'Savour Krispo',    1);
INSERT INTO sub_categories VALUES (59682, 47791, 'Chicken',          1);
INSERT INTO sub_categories VALUES (90069, 63929, 'Meals',            1);
INSERT INTO sub_categories VALUES (59685, 47794, 'Sweet',            1);
INSERT INTO sub_categories VALUES (59684, 47793, 'Drinks',           1);
INSERT INTO sub_categories VALUES (59680, 47789, 'Side Orders',      1);
INSERT INTO sub_categories VALUES (59683, 47792, 'Daigh Orders',     1);
INSERT INTO sub_categories VALUES (72946, 53259, 'Honey Munch Menu', 1);


-- ============================================================
-- 3. DISHES
--   price > 0  → shelf price (customer pays this).
--   price = 0  → price lives in dish_sub_options (must pick a variant).
--   base_price → reference / starting price shown on listing pages.
-- ============================================================
CREATE TABLE dishes (
    id              INT           PRIMARY KEY,
    category_id     INT           NOT NULL REFERENCES categories(id),
    sub_category_id INT           NOT NULL REFERENCES sub_categories(id),
    name            VARCHAR(200)  NOT NULL,
    description     TEXT,
    price           NUMERIC(10,2) NOT NULL DEFAULT 0,
    base_price      NUMERIC(10,2) NOT NULL DEFAULT 0,
    tag             VARCHAR(100),   -- e.g. "Best Seller", "Premium"
    status          SMALLINT      NOT NULL DEFAULT 1,
    availability    SMALLINT      NOT NULL DEFAULT 1
);

-- New Arrivals
INSERT INTO dishes VALUES (1910616, 63928, 90068, 'Khara Desi Kyo (Ghee)', 'Savor the authentic taste of Punjab with every bite, as the saying goes, "JO NA KRY MAA NA KRY PYO, O KARY SAVOUR DA DESI KYO."', 2500.00, 0, 'Premium', 1, 1);
INSERT INTO dishes VALUES (1912534, 63928, 90068, 'Berry Breeze',          '', 170.00, 0, 'Top Trending', 1, 1);
INSERT INTO dishes VALUES (1912535, 63928, 90068, 'Sun Kissed',            '', 170.00, 0, 'Top Trending', 1, 1);

-- Deals
INSERT INTO dishes VALUES (708031,  47790, 59681, 'My Deal',        '1 Savour Krispo, 1 Chicken Piece, 1 French Fries & 1 Drink',          1060.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708032,  47790, 59681, 'Hot Deal',       '2 Savour Krispo, 2 Chicken Piece, 2 French Fries & 2 Drink',          2075.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708033,  47790, 59681, 'Krispy Deal',    '1 Chicken Burger, 1 Wing Set, 1 Dinner Roll, 1 French Fries & 2 Drinks', 1240.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708036,  47790, 59681, 'Super Deal',     '2 Krispo Drum Sticks, 2 Wings, 1 French Fries & 2 Drink',             1045.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2249142, 47790, 59681, 'Aftar Plater 2', 'Boondi Chat, 1/4 Chargha, Fries, Fruit, Green Sauce, Dates & Juice',   948.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2249141, 47790, 59681, 'Aftar Plater 1', 'Boondi Chat, Samosa, Pakora, Fries, Fruit, Green Sauce, Imli Sauce, Date & Juice', 668.00, 0, '', 1, 1);

-- Chicken Pulao
INSERT INTO dishes VALUES (708005,   47786, 59677, 'Single',                'A Platter Of Rice With Chicken Piece, Two Shami Kabab Served With Fresh Salad & Traditional Raita',                                           0, 570.00, '', 1, 1);
INSERT INTO dishes VALUES (708008,   47786, 59677, 'Lunch Box (Single)',     'Rice With A Chicken Piece, Two Shami Kabab Packed In Card Box With Fresh Salad & Traditional Raita',                                         595.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708009,   47786, 59677, 'Special',               'A Platter Of Rice With Two Chicken Pieces, Two Shami Kabab Served With Fresh Salad & Traditional Raita',                                      0, 745.00, '', 1, 1);
INSERT INTO dishes VALUES (708010,   47786, 59677, 'Special Choice',        'A Platter Of Rice With Two Chicken Pieces Of Your Choice, Two Shami Kabab Served With Fresh Salad & Traditional Raita',                       0, 755.00, '', 1, 1);
INSERT INTO dishes VALUES (708012,   47786, 59677, 'Special Picinic Pack',  'Rice With Two Chicken Pieces, Two Shami Kababs Packed In Card Box With Fresh Salad & Traditional Raita',                                    770.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708013,   47786, 59677, 'Pulao Kabab',           'A Platter Of Rice With Two Shami Kabab Served With Fresh Salad & Traditional Raita',                                                          0, 395.00, '', 1, 1);
INSERT INTO dishes VALUES (736842,   47786, 59677, 'Shami Kabab',           'Shami Kabab',                                                                                                                                 55.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288368,  47786, 59677, 'Shami Kabab (Frozen)', 'Shami Kabab (Frozen)',                                                                                                                         50.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708007,   47786, 59677, 'Single Without Kabab',  'A Platter Of Rice With A Chicken Piece Served With Fresh Salad & Traditional Raita',                                                           0, 470.00, '', 1, 1);
INSERT INTO dishes VALUES (708014,   47786, 59677, 'Pulao',                 'A Plate Of Rice Served With Fresh Salad & Traditional Raita',                                                                               295.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708006,   47786, 59677, 'Single Choice',         'A Platter Of Rice With A Chicken Piece Of Your Choice, Two Shami Kabab Served With Fresh Salad & Traditional Raita',                          0, 575.00, '', 1, 1);
INSERT INTO dishes VALUES (708011,   47786, 59677, 'Special Without Kabab', 'A Platter Of Rice With Two Chicken Pieces Served With Fresh Salad & Traditional Raita',                                                       0, 645.00, '', 1, 1);

-- Savour Krispo
INSERT INTO dishes VALUES (1915195, 47785, 59676, 'Tangy Stick',              '',              0,    0, '', 1, 1);
INSERT INTO dishes VALUES (1909549, 47785, 59676, 'Krispo Chicken Piece 1/8', '',           265.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708045,  47785, 59676, 'Krispo Broast Full',       '8 Pieces',  2000.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708034,  47785, 59676, 'Hot Shot',                 '12 Pieces',  685.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708035,  47785, 59676, 'Wings Family Basket',      '36 Pieces', 2035.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708043,  47785, 59676, 'Krispo Wings',             '6 Pieces',   395.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708047,  47785, 59676, 'French Fries',             '',           240.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708044,  47785, 59676, 'Krispo Chicken Piece 1/8 -','',          270.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708037,  47785, 59676, 'Krispo Burger',            '',           540.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (2141262, 47785, 59676, 'Krispo Burger With Fries', 'One Krispo Burger with single fries', 715.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708040,  47785, 59676, 'Chicken Burger',           '',           450.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708041,  47785, 59676, 'Chicken Burger With Fries','',           625.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708042,  47785, 59676, 'Chicken Burger & Cheese',  '',           490.00,  0, '', 1, 1);
INSERT INTO dishes VALUES (708046,  47785, 59676, 'Krispo Broast Half',       '4 Pieces',  1025.00,  0, '', 1, 1);

-- Chicken
INSERT INTO dishes VALUES (1909548, 47791, 59682, 'Chicken Piece',        '',                                                           180.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708015,  47791, 59682, 'Chicken Roast',        'One Roasted Chicken Served With Ketchup & Fresh Lemons',    1450.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708017,  47791, 59682, 'Chicken Piece -',      'Chicken Piece Steam Cooked 1/8 Part',                        180.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708016,  47791, 59682, 'Chicken Roast (Half)', 'Half Roasted Chicken Served With Ketchup & Fresh Lemon',     740.00, 0, '', 1, 1);

-- Meals
INSERT INTO dishes VALUES (708030, 63929, 90069, 'Small Deal', '1 Savour Krispo, 1 French Fries & 1 Drink', 785.00, 0, 'Best Seller', 1, 1);

-- Sweet
INSERT INTO dishes VALUES (1003499, 47794, 59685, 'Gajar Halwa',            '',                                                                               0, 190.00, '', 1, 1);
INSERT INTO dishes VALUES (1032200, 47794, 59685, 'Zarda',                  'Traditional Colourful Rice Sweet Dish With Chamcham & Raisins',                  0, 170.00, '', 1, 1);
INSERT INTO dishes VALUES (708027,  47794, 59685, 'Zarda -',                'Traditional Colourful Rice Sweet Dish With Chamcham & Raisins',                  0, 175.00, '', 1, 1);
INSERT INTO dishes VALUES (708028,  47794, 59685, 'Kheer (Single Serving)', 'Traditional Rice Kheer In Milk & Khoye, Served In Thooti',                   185.00, 0,      '', 1, 1);
INSERT INTO dishes VALUES (708029,  47794, 59685, 'Kheer Box (Three Servings)', 'Traditional Rice Kheer In Milk & Khoye, Packed In Aluminium',             495.00, 0,     '', 1, 1);

-- Drinks
INSERT INTO dishes VALUES (1054596, 47793, 59684, 'Savour Water 19 Liter (New)',   'A maximum of 2 bottles will be delivered by one rider.', 1100.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708018,  47793, 59684, 'Mint Margarita',                '',                                                        165.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708019,  47793, 59684, 'Pina Colada',                   '',                                                        285.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (754092,  47793, 59684, 'Soft Drink Cans',               'Soft Drink Cans',                                         120.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708021,  47793, 59684, 'Soft Drink 500 Ml',             'Soft Drink 500 ml',                                       105.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (754046,  47793, 59684, 'Soft Drink 1500 Ml',            'Soft Drink 1500 ml',                                      185.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708023,  47793, 59684, 'Qahwa',                         '',                                                         85.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708024,  47793, 59684, 'Tea',                           '',                                                        115.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708025,  47793, 59684, 'Milk Coffee With Cream',        '',                                                        175.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (736834,  47793, 59684, 'Mineral Water 1500 ML',         '',                                                        115.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708022,  47793, 59684, 'Mineral Water 500 ML',          '',                                                         55.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1055021, 47793, 59684, 'Savour Water 19 Liter (Refil)', 'A maximum of 2 bottles will be delivered by one rider.',    175.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708026,  47793, 59684, 'Milk Coffee Without Cream',     '',                                                        175.00, 0, '', 1, 1);

-- Side Orders
INSERT INTO dishes VALUES (708059, 47789, 59680, 'Ketchup', '',  10.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708057, 47789, 59680, 'Raita',   '',  30.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (708058, 47789, 59680, 'Salad',   '',  30.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1005152, 47789, 59680, 'Naan',   '', 110.00, 0, '', 1, 1);

-- Daigh Orders
INSERT INTO dishes VALUES (1013951, 47792, 59683, 'Beef Qorma Boneless', '', 14100.00,     0, '', 1, 1);
INSERT INTO dishes VALUES (1013941, 47792, 59683, 'Sada Pulao Daig',     '',     0, 6500.00,  '', 1, 1);
INSERT INTO dishes VALUES (1013943, 47792, 59683, 'Chicken Pulao Daig', '',      0, 10500.00, '', 1, 1);
INSERT INTO dishes VALUES (1013942, 47792, 59683, 'Chana Pulao Daig',   '',      0, 7800.00,  '', 1, 1);
INSERT INTO dishes VALUES (1013944, 47792, 59683, 'Chicken Biryani Daig','',     0, 15600.00, '', 1, 1);
INSERT INTO dishes VALUES (1013945, 47792, 59683, 'Chicken Qorma Daig', '',      0, 11000.00, '', 1, 1);
INSERT INTO dishes VALUES (1013946, 47792, 59683, 'Mutton Pulao Daig',  '',      0, 16000.00, '', 1, 1);
INSERT INTO dishes VALUES (1013947, 47792, 59683, 'Mutton Biryani Daig','',      0, 26500.00, '', 1, 1);
INSERT INTO dishes VALUES (1013948, 47792, 59683, 'Mutton Korma Daig',  '',      0, 22500.00, '', 1, 1);
INSERT INTO dishes VALUES (1013949, 47792, 59683, 'Beef Pulao Daig',    '',      0, 12500.00, '', 1, 1);
INSERT INTO dishes VALUES (1013950, 47792, 59683, 'Beef Korma Daig',    '',      0, 13000.00, '', 1, 1);
INSERT INTO dishes VALUES (1013952, 47792, 59683, 'Zarda Daig',         '',      0, 10000.00, '', 1, 1);
INSERT INTO dishes VALUES (1013953, 47792, 59683, 'Kheer 5 Kg',         'Minimum Order 5 To 20 Kg', 4250.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1013954, 47792, 59683, 'Chatni Aloo Bukhara Per Kg', '1 Day Preparation Time Required.', 1200.00, 0, '', 1, 1);

-- Honey Munch Menu
INSERT INTO dishes VALUES (1288369, 53259, 72946, 'Basbausa',               'Basbausa Is A Sweet Syrup Soaked Semolina That Originated In Egypt Baked And Sweetend.',                                                     2069.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288371, 53259, 72946, 'Honey Walnut Tart',      'Tart With The Filling Of Pure Wildflower Honey, Toasted Walnuts, Orange Zest, And Vanilla.',                                                 388.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288372, 53259, 72946, 'Walnut Brownie',         'A Classic Brownie With Crunchy Walnuts Mixed In, Adding A Nutty & Hearty Flavor.',                                                          207.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288374, 53259, 72946, 'White Chocolate Brownie','A Twist On The Classic Brownie, Made With Creamy & Buttery White Chocolate.',                                                              207.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1921336, 53259, 72946, 'Oreo Brownie',           '',                                                                                                                                           207.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1921338, 53259, 72946, 'Chocolate Brownie',      '',                                                                                                                                           207.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061025, 53259, 72946, 'Chocolate Fudge Brownie','',                                                                                                                                           207.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061026, 53259, 72946, 'Nutella Brownie',        '',                                                                                                                                           207.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1921335, 53259, 72946, 'Lotus Filled Donuts',    '',                                                                                                                                           259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288414, 53259, 72946, 'Boston Cream Donut',     'A Classic Donut Filled With Vanilla Custard And Topped With Chocolate Ganache.',                                                             259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288416, 53259, 72946, 'Chocolate Filled Donut', 'Soft And Fluffy Donut With A Creamy Surprise Inside.',                                                                                       259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288407, 53259, 72946, 'Chocolate Donut',        'Rich, Chocolatey Goodness In Every Bite.',                                                                                                   216.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288413, 53259, 72946, 'Rainbow Donut',          'A Burst Of Colors In Every Bite.',                                                                                                           216.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061024, 53259, 72946, 'Lotus Donut',            '',                                                                                                                                           259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288380, 53259, 72946, 'Chocolate Muffins',      'Moist And Chocolatey Muffin.',                                                                                                               259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288382, 53259, 72946, 'Blueberry Muffin',       'Bursting With Juicy Blueberries, This Fluffy Muffin Is A Perfect Balance Of Sweet Flavors.',                                                259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288383, 53259, 72946, 'Strawberry Muffin',      'A Moist & Tender Muffin Filled With Strawberries.',                                                                                          259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288385, 53259, 72946, 'Lotus Muffin',           'A Fluffy & Aromatic Muffin With A Rich, Caramelized Flavor Of Lotus Biscuits.',                                                             259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288387, 53259, 72946, 'Vanilla Muffin',         'A Classic And Tender Muffin With A Subtle Vanilla Flavor.',                                                                                  259.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288388, 53259, 72946, 'Caramel Sundae',         '',                                                                                                                                           276.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288389, 53259, 72946, 'Oreo Sundae',            '',                                                                                                                                           276.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288390, 53259, 72946, 'Lotus Sundae',           '',                                                                                                                                           276.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288391, 53259, 72946, 'Three Milk Sundae',      '',                                                                                                                                           276.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288392, 53259, 72946, 'Red Velvet Sundae',      '',                                                                                                                                           276.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288393, 53259, 72946, 'Nutella Sundae',         '',                                                                                                                                           276.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063453, 53259, 72946, 'Caramel Mini Sundae',    '',                                                                                                                                           138.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063454, 53259, 72946, 'Oreo Mini Sundae',       '',                                                                                                                                           138.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063455, 53259, 72946, 'Lotus Mini Sundae',      '',                                                                                                                                           138.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063456, 53259, 72946, 'Three Milk Mini Sundae', '',                                                                                                                                           138.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063457, 53259, 72946, 'Red Velvet Mini Sundae', '',                                                                                                                                           138.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063458, 53259, 72946, 'Nutella Mini Sundae',    '',                                                                                                                                           138.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1921399, 53259, 72946, 'Mango Milk Cake (1 Pound)',  '',                                                                                                                                       948.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1921415, 53259, 72946, 'Mango Milk Cake (2 Pound)',  '',                                                                                                                                      1897.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288400, 53259, 72946, 'Lotus Cream Cake',           'Fluffy Vanilla Cake With Rich Lotus Cream Filling And Crunchy Biscuit Topping.',                                                       2175.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288401, 53259, 72946, 'Red Velvet Cake',            'Classic Red Velvet Cake With Tangy Cream Cheese Frosting.',                                                                             1897.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1925830, 53259, 72946, 'Belgium Cake',               'A Rich, Chocolatey Delight Made With Premium Cocoa Powder And Dark Chocolate.',                                                         1983.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288403, 53259, 72946, 'Lemon Cheese Cake',          'Tangy, Zesty Flavor With A Rich, Creamy Texture.',                                                                                     2069.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288404, 53259, 72946, 'Three Milk Cake',            'Three Layers Of Moist Chocolate Cake, Filled & Topped With A Creamy Chocolate Frosting.',                                              2069.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288402, 53259, 72946, 'Chocolate Fudge Cake',       'A Pure Chocolate Bliss - Made With Rich, Velvety Chocolate And Topped With Gooey Fudge Icing.',                                       2069.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1925831, 53259, 72946, 'Caramel Classic',            'Infused With The Warm, Sweet Flavors Of Caramel And Butter For A Classic Taste.',                                                      1810.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288405, 53259, 72946, 'Belgium Mini Cake',          'A Rich, Chocolatey Delight Made With Premium Cocoa Powder And Dark Chocolate.',                                                         733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1925832, 53259, 72946, 'Chocolate Fudge Mini Cake',  'A Pure Chocolate Bliss - Made With Rich, Velvety Chocolate And Topped With Gooey Fudge Icing.',                                        733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288411, 53259, 72946, 'Caramel Mini Cake',          'Infused With The Warm, Sweet Flavors Of Caramel And Butter For A Classic Taste.',                                                       733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1925834, 53259, 72946, 'Lotus Mini Cake',            'Fluffy Vanilla Cake With Rich Lotus Cream Filling And Crunchy Biscuit Topping.',                                                        733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1925833, 53259, 72946, 'Red Valvet Mini Cake',       'Classic Red Velvet Cake With Tangy Cream Cheese Frosting.',                                                                              733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061017, 53259, 72946, 'Lotus Cream Mini Cake',      '',                                                                                                                                       733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061018, 53259, 72946, 'Red Velvet Mini Cake',       '',                                                                                                                                       733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061019, 53259, 72946, 'Kit Kat Mini Cake',          '',                                                                                                                                       733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2467875, 53259, 72946, 'Nutella Mini Cake',          '',                                                                                                                                       733.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288399, 53259, 72946, 'NY Cheese Cake',             'Classic New York Cheesecake With A Rich & Creamy Filling Baked On A Graham Cracker Crust.',                                            3017.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061015, 53259, 72946, 'Kit Kat Cake',               '',                                                                                                                                      2069.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061012, 53259, 72946, 'Pistachio Royale 2.5',       '',                                                                                                                                      1902.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061013, 53259, 72946, 'Pistachio Royale 1.25',      '',                                                                                                                                       951.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061014, 53259, 72946, 'Caramel Cake',               '',                                                                                                                                      1729.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061016, 53259, 72946, 'Carrot Cake',                '',                                                                                                                                      1902.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2467873, 53259, 72946, 'Pistachio Milk Cake 2.5',    '',                                                                                                                                      2069.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2467874, 53259, 72946, 'Pistachio Milk Cake 1.25',   '',                                                                                                                                      1034.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2277234, 53259, 72946, 'Strawberry Milk Cake',       'Strawberry Milk Cake 1.25 Pound',                                                                                                        948.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2277236, 53259, 72946, 'San Sebastian Cheesecake',   'San Sebastian Cheesecake',                                                                                                              3448.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063440, 53259, 72946, 'Walnut-date Cake Slice',     '',                                                                                                                                       104.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063441, 53259, 72946, 'Honey Walnut Date Cake',     '',                                                                                                                                       991.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063444, 53259, 72946, 'Lotus Cream Slice',          '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063445, 53259, 72946, 'Red Velvet Slice',           '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063446, 53259, 72946, 'Belgium Slice',              '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063448, 53259, 72946, 'Three Milk Cake Slice',      '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063449, 53259, 72946, 'Chocolate Fudge Slice',      '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063450, 53259, 72946, 'Caramel Slice',              '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063451, 53259, 72946, 'Kit Kat Slice',              '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063452, 53259, 72946, 'Carrot Cake Slice',          '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2063447, 53259, 72946, 'Lemon Cheese Slice',         '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2277235, 53259, 72946, 'San Sebastian Cheesecake Slice', 'San Sebastian Cheesecake Slice',                                                                                                     431.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2467876, 53259, 72946, 'NY Cheese Cake Slice',       '',                                                                                                                                       345.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288394, 53259, 72946, 'Oreo Macron',                '',                                                                                                                                       129.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288395, 53259, 72946, 'Lemon Macron',               '',                                                                                                                                       129.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288396, 53259, 72946, 'Strawberry Macron',          '',                                                                                                                                       129.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288397, 53259, 72946, 'Pistachio Macron',           '',                                                                                                                                       129.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (1288398, 53259, 72946, 'Blueberry Macron',           '',                                                                                                                                       129.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061020, 53259, 72946, 'Croissant Plain',            '',                                                                                                                                       216.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061021, 53259, 72946, 'Chocolate Croissant',        '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061022, 53259, 72946, 'Strawberry Croissant',       '',                                                                                                                                       302.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2061023, 53259, 72946, 'Pistachio Croissant',        '',                                                                                                                                       345.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2467877, 53259, 72946, 'Banana Bread',               '',                                                                                                                                      1034.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2467878, 53259, 72946, 'Banana Bread Slice',         '',                                                                                                                                       129.00, 0, '', 1, 1);
INSERT INTO dishes VALUES (2456308, 53259, 72946, 'Cake Rusk',                  '',                                                                                                                                         0, 750.00, '', 1, 1);
INSERT INTO dishes VALUES (2456310, 53259, 72946, 'Biscuits',                   '',                                                                                                                                         0, 900.00, '', 1, 1);
INSERT INTO dishes VALUES (1288369, 53259, 72946, 'Basbausa',                   'Sweet Syrup Soaked Semolina Baked And Sweetened.',                                                                                     2069.00, 0, '', 1, 1) ON CONFLICT DO NOTHING;


-- ============================================================
-- 4. DISH_OPTIONS  (customisation groups)
--   required = 1  → customer MUST choose before ordering
--   multiselect   → can pick more than one sub-option
-- ============================================================
CREATE TABLE dish_options (
    id          INT          PRIMARY KEY,
    dish_id     INT          NOT NULL REFERENCES dishes(id),
    name        VARCHAR(200) NOT NULL,
    required    SMALLINT     NOT NULL DEFAULT 0,
    multiselect SMALLINT     NOT NULL DEFAULT 0,
    min_select  INT          NOT NULL DEFAULT 0,
    max_select  INT          NOT NULL DEFAULT 0,
    priority    INT          NOT NULL DEFAULT 0
);

INSERT INTO dish_options VALUES (185819, 708031, 'Soft Drink',               0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185820, 708032, '1st Soft Drink',           1, 0, 1, 1, 2);
INSERT INTO dish_options VALUES (185821, 708032, '2nd Soft Drink',           1, 0, 1, 1, 1);
INSERT INTO dish_options VALUES (185822, 708033, 'Soft Drink',               0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185823, 708033, 'Soft Drink',               0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185824, 708036, 'Soft Drink',               0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185825, 708036, 'Soft Drink',               0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (710876, 708005, 'Packaging',                1, 0, 0, 0, 5);
INSERT INTO dish_options VALUES (185813, 708009, 'Packaging',                1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185814, 708010, 'Packaging',                1, 0, 0, 0, 3);
INSERT INTO dish_options VALUES (189818, 708010, '1st Chicken Piece Choice', 1, 0, 0, 0, 2);
INSERT INTO dish_options VALUES (189821, 708010, '2nd Chicken Piece Choice', 1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185816, 708013, 'Packaging',                1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185812, 708007, 'Packaging',                1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185817, 708014, 'Packaging',                1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (189813, 708006, 'Chicken Variation',        1, 0, 0, 0, 2);
INSERT INTO dish_options VALUES (189820, 708006, 'Packaging',                1, 0, 0, 0, 2);
INSERT INTO dish_options VALUES (185815, 708011, 'Packaging',                1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1405650, 1915195, 'Select Quantity',        1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1403853, 1909549, 'Choose Your Piece',      1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (851913,  708047,  'Fries',                  1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1403851, 708044,  'Choose Your Piece',      1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1403852, 1909548, 'Choose Your Piece',      1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1416515, 708015,  'Variant',                1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1403850, 708017,  'Choose Your Piece',      1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1416516, 708016,  'Variant',                1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (185818,  708030,  'Drinks',                 1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1404397, 708030,  'Fries',                  1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (201655,  1003499, 'Gajar Halwa',            1, 1, 1, 1, 1);
INSERT INTO dish_options VALUES (206579,  1032200, 'Variation',              1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1403854, 708027,  'Variation',              1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (190716,  754092,  'Choose Your Drink',      0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (190715,  708021,  'Choose Your Drink',      0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (190714,  754046,  'Choose Your Drink',      0, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (739367,  1013951, 'Beef Qorma Boneless',    0, 1, 1, 6, 1);
INSERT INTO dish_options VALUES (769597,  1013941, 'Sada Pulao Daig',        1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769599,  1013943, 'Chicken Pulao Daig',     1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769598,  1013942, 'Chana Pulao Daig',       1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769600,  1013944, 'Chicken Biryani Daig',   1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769601,  1013945, 'Chicken Qorma Daig',     1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769602,  1013946, 'Mutton Pulao Daig',      1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769603,  1013947, 'Mutton Biryani Daig',    1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769604,  1013948, 'Mutton Qorma Daig',      1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769605,  1013949, 'Beef Pulao Daig',        1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769606,  1013950, 'Beef Qorma Daig',        1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (769607,  1013952, 'Zarda Daig',             1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1624927, 2456308, 'Variation',              1, 0, 0, 0, 1);
INSERT INTO dish_options VALUES (1624928, 2456310, 'Variation',              1, 0, 0, 0, 1);


-- ============================================================
-- 5. DISH_SUB_OPTIONS  (individual choices within an option group)
--   price = 0   → no extra charge (included in dish / base price)
--   price > 0   → IS the final variant price, OR an add-on charge
-- ============================================================
CREATE TABLE dish_sub_options (
    id        INT           PRIMARY KEY,
    option_id INT           NOT NULL REFERENCES dish_options(id),
    dish_id   INT           NOT NULL REFERENCES dishes(id),
    name      VARCHAR(300)  NOT NULL,
    price     NUMERIC(10,2) NOT NULL DEFAULT 0,
    priority  INT           NOT NULL DEFAULT 0
);

-- My Deal drink choices
INSERT INTO dish_sub_options VALUES (862329, 185819, 708031, 'Savour Mineral Water', 0.00, 0);
INSERT INTO dish_sub_options VALUES (862330, 185819, 708031, 'Gourmet',              0.00, 0);
-- Hot Deal drink choices
INSERT INTO dish_sub_options VALUES (862331, 185820, 708032, 'Savour Mineral Water', 0.00, 0);
INSERT INTO dish_sub_options VALUES (862332, 185820, 708032, 'Gourmet',              0.00, 0);
INSERT INTO dish_sub_options VALUES (862333, 185821, 708032, 'Savour Mineral Water', 0.00, 0);
INSERT INTO dish_sub_options VALUES (862334, 185821, 708032, 'Gourmet',              0.00, 0);
-- Krispy Deal drinks
INSERT INTO dish_sub_options VALUES (862340, 185822, 708033, 'Colla Next.',  0.00, 0);
INSERT INTO dish_sub_options VALUES (862341, 185822, 708033, 'Fizzup Next.', 0.00, 0);
INSERT INTO dish_sub_options VALUES (862343, 185823, 708033, 'Colla Next.',  0.00, 0);
INSERT INTO dish_sub_options VALUES (862344, 185823, 708033, 'Fizzup Next.', 0.00, 0);
-- Super Deal drinks
INSERT INTO dish_sub_options VALUES (862348, 185824, 708036, 'Savour Mineral Water', 0.00, 0);
INSERT INTO dish_sub_options VALUES (862349, 185824, 708036, 'Gourmet',              0.00, 0);
INSERT INTO dish_sub_options VALUES (862350, 185825, 708036, 'Savour Mineral Water', 0.00, 0);
INSERT INTO dish_sub_options VALUES (862351, 185825, 708036, 'Gourmet',              0.00, 0);
-- Chicken Pulao packaging
INSERT INTO dish_sub_options VALUES (6059057, 710876, 708005, 'Normal', 570.00, 0);
INSERT INTO dish_sub_options VALUES (6059058, 710876, 708005, 'Boxed',  585.00, 0);
INSERT INTO dish_sub_options VALUES (862310, 185813, 708009, 'Normal', 745.00, 0);
INSERT INTO dish_sub_options VALUES (862311, 185813, 708009, 'Boxed',  760.00, 0);
INSERT INTO dish_sub_options VALUES (862314, 185814, 708010, 'Normal', 755.00, 0);
INSERT INTO dish_sub_options VALUES (862315, 185814, 708010, 'Boxed',  770.00, 0);
INSERT INTO dish_sub_options VALUES (862316, 185815, 708011, 'Normal', 645.00, 0);
INSERT INTO dish_sub_options VALUES (862317, 185815, 708011, 'Boxed',  660.00, 0);
INSERT INTO dish_sub_options VALUES (862322, 185816, 708013, 'Normal', 395.00, 0);
INSERT INTO dish_sub_options VALUES (862323, 185816, 708013, 'Boxed',  410.00, 0);
INSERT INTO dish_sub_options VALUES (862306, 185812, 708007, 'Normal', 470.00, 0);
INSERT INTO dish_sub_options VALUES (862307, 185812, 708007, 'Boxed',  485.00, 0);
INSERT INTO dish_sub_options VALUES (862326, 185817, 708014, 'Normal',  0.00, 2);
INSERT INTO dish_sub_options VALUES (862327, 185817, 708014, '+Boxed', 15.00, 1);
-- Chicken piece choices
INSERT INTO dish_sub_options VALUES (887315, 189813, 708006, 'Chest', 0.00, 0);
INSERT INTO dish_sub_options VALUES (887316, 189813, 708006, 'Leg',   0.00, 0);
INSERT INTO dish_sub_options VALUES (887317, 189813, 708006, 'Thigh', 0.00, 0);
INSERT INTO dish_sub_options VALUES (887318, 189813, 708006, 'Wing',  0.00, 0);
INSERT INTO dish_sub_options VALUES (887337, 189820, 708006, 'Normal', 575.00, 0);
INSERT INTO dish_sub_options VALUES (887338, 189820, 708006, 'Boxed',  590.00, 0);
INSERT INTO dish_sub_options VALUES (887331, 189818, 708010, 'Chest', 0.00, 0);
INSERT INTO dish_sub_options VALUES (887332, 189818, 708010, 'Leg',   0.00, 0);
INSERT INTO dish_sub_options VALUES (887333, 189818, 708010, 'Thigh', 0.00, 0);
INSERT INTO dish_sub_options VALUES (887334, 189818, 708010, 'Wing',  0.00, 0);
INSERT INTO dish_sub_options VALUES (887347, 189821, 708010, 'Chest', 0.00, 0);
INSERT INTO dish_sub_options VALUES (887348, 189821, 708010, 'Leg',   0.00, 0);
INSERT INTO dish_sub_options VALUES (887349, 189821, 708010, 'Thigh', 0.00, 0);
INSERT INTO dish_sub_options VALUES (887350, 189821, 708010, 'Wing',  0.00, 0);
-- Tangy Sticks quantities
INSERT INTO dish_sub_options VALUES (11790206, 1405650, 1915195, 'Tangy Sticks 2 Pieces',  500.00, 0);
INSERT INTO dish_sub_options VALUES (11790207, 1405650, 1915195, 'Tangy Sticks 4 Pieces', 1000.00, 0);
INSERT INTO dish_sub_options VALUES (11790208, 1405650, 1915195, 'Tangy Sticks 8 Pieces', 2000.00, 0);
-- Krispo piece choices
INSERT INTO dish_sub_options VALUES (11778623, 1403853, 1909549, 'Leg',   0.00, 0);
INSERT INTO dish_sub_options VALUES (11778624, 1403853, 1909549, 'Thigh', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778625, 1403853, 1909549, 'Chest', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778626, 1403853, 1909549, 'Wing',  0.00, 0);
INSERT INTO dish_sub_options VALUES (11778615, 1403851, 708044, 'Leg',   0.00, 0);
INSERT INTO dish_sub_options VALUES (11778616, 1403851, 708044, 'Thigh', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778617, 1403851, 708044, 'Chest', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778618, 1403851, 708044, 'Wing',  0.00, 0);
INSERT INTO dish_sub_options VALUES (11778619, 1403852, 1909548, 'Leg',   0.00, 0);
INSERT INTO dish_sub_options VALUES (11778620, 1403852, 1909548, 'Thigh', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778621, 1403852, 1909548, 'Chest', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778622, 1403852, 1909548, 'Wing',  0.00, 0);
INSERT INTO dish_sub_options VALUES (11778611, 1403850, 708017, 'Leg',   0.00, 0);
INSERT INTO dish_sub_options VALUES (11778612, 1403850, 708017, 'Thigh', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778613, 1403850, 708017, 'Chest', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11778614, 1403850, 708017, 'Wing',  0.00, 0);
-- Fries variants
INSERT INTO dish_sub_options VALUES (7439812, 851913, 708047, 'Plain Fries',      0.00, 0);
INSERT INTO dish_sub_options VALUES (7439813, 851913, 708047, 'Masala Fries',    15.00, 0);
INSERT INTO dish_sub_options VALUES (7439814, 851913, 708047, 'Garlic Mayo Fries',35.00, 0);
-- Chicken Roast variants
INSERT INTO dish_sub_options VALUES (11847594, 1416515, 708015, 'Chicken Roast (Steamed)',  0.00, 0);
INSERT INTO dish_sub_options VALUES (11847595, 1416515, 708015, 'Chicken Roast (Deep Fry)', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11847596, 1416516, 708016, 'Chicken Roast (Steamed)',  0.00, 0);
INSERT INTO dish_sub_options VALUES (11847597, 1416516, 708016, 'Chicken Roast (Deep Fry)', 0.00, 0);
-- Small Deal choices
INSERT INTO dish_sub_options VALUES (11781725, 185818, 708030, 'Savour Mineral Water', 0.00, 0);
INSERT INTO dish_sub_options VALUES (11870884, 185818, 708030, 'Gourmet',              0.00, 0);
INSERT INTO dish_sub_options VALUES (11781740, 1404397, 708030, 'Masala Fries', 15.00, 0);
INSERT INTO dish_sub_options VALUES (11781741, 1404397, 708030, 'Mayo Fries',   35.00, 0);
INSERT INTO dish_sub_options VALUES (11781742, 1404397, 708030, 'Plain Fries',   0.00, 0);
-- Gajar Halwa sizes
INSERT INTO dish_sub_options VALUES (933765, 201655, 1003499, '100 Gm',  190.00, 0);
INSERT INTO dish_sub_options VALUES (933766, 201655, 1003499, '500 Gm',  950.00, 0);
INSERT INTO dish_sub_options VALUES (933767, 201655, 1003499, '1 Kg',   1800.00, 0);
-- Zarda variants
INSERT INTO dish_sub_options VALUES (958840, 206579, 1032200, 'Normal', 170.00, 0);
INSERT INTO dish_sub_options VALUES (958841, 206579, 1032200, 'Boxed',  180.00, 0);
INSERT INTO dish_sub_options VALUES (11778627, 1403854, 708027, 'Normal', 175.00, 0);
INSERT INTO dish_sub_options VALUES (11778628, 1403854, 708027, 'Boxed',  190.00, 0);
-- Daigh sizes
INSERT INTO dish_sub_options VALUES (6351431,  739367, 1013951, 'Beef Qorma Boneless 6 Kg Beef',  14100.00, 0);
INSERT INTO dish_sub_options VALUES (11804184, 739367, 1013951, 'Beef Qorma Boneless 8 Kg Beef',  18800.00, 0);
INSERT INTO dish_sub_options VALUES (11804185, 739367, 1013951, 'Beef Qorma Boneless 10 Kg Beef', 23500.00, 0);
INSERT INTO dish_sub_options VALUES (11804186, 739367, 1013951, 'Beef Qorma Boneless 12 Kg Beef', 27800.00, 0);
INSERT INTO dish_sub_options VALUES (6692705, 769597, 1013941, 'Sada Pulao Daig (6 Kg Rice)',   6500.00, 0);
INSERT INTO dish_sub_options VALUES (6692706, 769597, 1013941, 'Sada Pulao Daig (8 Kg Rice)',   8800.00, 0);
INSERT INTO dish_sub_options VALUES (6692707, 769597, 1013941, 'Sada Pulao Daig (10 Kg Rice)', 11000.00, 0);
INSERT INTO dish_sub_options VALUES (6692708, 769597, 1013941, 'Sada Pulao Daig (12 Kg Rice)', 13000.00, 0);
INSERT INTO dish_sub_options VALUES (6692709, 769598, 1013942, 'Chana Pulao Daig (6 Kg Rice + 1 Kg Chana)',   7800.00, 0);
INSERT INTO dish_sub_options VALUES (11779651, 769598, 1013942, 'Chana Pulao Daig (6 Kg Rice + 1.5 Kg Chana)', 8500.00, 0);
INSERT INTO dish_sub_options VALUES (11779652, 769598, 1013942, 'Chana Pulao Daig (8 Kg Rice + 2 Kg Chana)',  11000.00, 0);
INSERT INTO dish_sub_options VALUES (11779653, 769598, 1013942, 'Chana Pulao Daig (10 Kg Rice + 2 Kg Chana)', 13500.00, 0);
INSERT INTO dish_sub_options VALUES (11779654, 769598, 1013942, 'Chana Pulao Daig (12 Kg Rice + 2 Kg Chana)', 15500.00, 0);
INSERT INTO dish_sub_options VALUES (6692711, 769599, 1013943, 'Chicken Pulao Daig (6 Kg Rice + 3 Kg Chicken)',  10500.00, 0);
INSERT INTO dish_sub_options VALUES (6692712, 769599, 1013943, 'Chicken Pulao Daig (8 Kg Rice + 4 Kg Chicken)',  13800.00, 0);
INSERT INTO dish_sub_options VALUES (6692713, 769599, 1013943, 'Chicken Pulao Daig (10 Kg Rice + 5 Kg Chicken)', 17500.00, 0);
INSERT INTO dish_sub_options VALUES (6692714, 769599, 1013943, 'Chicken Pulao Daig (12 Kg Rice + 6 Kg Chicken)', 20500.00, 0);
INSERT INTO dish_sub_options VALUES (11978485, 769600, 1013944, 'Chicken Biryani Daig (6 Kg Rice + 6 Kg Chicken)',  15600.00, 0);
INSERT INTO dish_sub_options VALUES (11978486, 769600, 1013944, 'Chicken Biryani Daig (8 Kg Rice + 8 Kg Chicken)',  21000.00, 0);
INSERT INTO dish_sub_options VALUES (11978487, 769600, 1013944, 'Chicken Biryani Daig (10 Kg Rice + 10 Kg Chicken)',26000.00, 0);
INSERT INTO dish_sub_options VALUES (6692718, 769601, 1013945, 'Chicken Qorma Daig (6 Kg Chicken)',  11000.00, 0);
INSERT INTO dish_sub_options VALUES (6692719, 769601, 1013945, 'Chicken Qorma Daig (8 Kg Chicken)',  14500.00, 0);
INSERT INTO dish_sub_options VALUES (6692720, 769601, 1013945, 'Chicken Qorma Daig (10 Kg Chicken)', 18000.00, 0);
INSERT INTO dish_sub_options VALUES (6692721, 769601, 1013945, 'Chicken Qorma Daig (12 Kg Chicken)', 21000.00, 0);
INSERT INTO dish_sub_options VALUES (6692722, 769602, 1013946, 'Mutton Pulao Daig (6 Kg Rice + 3 Kg Mutton)',  16000.00, 0);
INSERT INTO dish_sub_options VALUES (6692723, 769602, 1013946, 'Mutton Pulao Daig (8 Kg Rice + 4 Kg Mutton)',  21500.00, 0);
INSERT INTO dish_sub_options VALUES (6692724, 769602, 1013946, 'Mutton Pulao Daig (10 Kg Rice + 5 Kg Mutton)', 26800.00, 0);
INSERT INTO dish_sub_options VALUES (6692725, 769602, 1013946, 'Mutton Pulao Daig (12 Kg Rice + 6 Kg Mutton)', 32000.00, 0);
INSERT INTO dish_sub_options VALUES (11978488, 769603, 1013947, 'Mutton Biryani Daig (6 Kg Rice + 6 Kg Mutton)',  26500.00, 0);
INSERT INTO dish_sub_options VALUES (11978489, 769603, 1013947, 'Mutton Biryani Daig (8 Kg Rice + 8 Kg Mutton)',  35300.00, 0);
INSERT INTO dish_sub_options VALUES (11978490, 769603, 1013947, 'Mutton Biryani Daig (10 Kg Rice + 10 Kg Mutton)',44100.00, 0);
INSERT INTO dish_sub_options VALUES (6692729, 769604, 1013948, 'Mutton Qorma Daig (6 Kg Mutton)',  22500.00, 0);
INSERT INTO dish_sub_options VALUES (6692730, 769604, 1013948, 'Mutton Qorma Daig (8 Kg Mutton)',  30000.00, 0);
INSERT INTO dish_sub_options VALUES (6692731, 769604, 1013948, 'Mutton Qorma Daig (10 Kg Mutton)', 37500.00, 0);
INSERT INTO dish_sub_options VALUES (6692732, 769604, 1013948, 'Mutton Qorma Daig (12 Kg Mutton)', 45000.00, 0);
INSERT INTO dish_sub_options VALUES (6692733, 769605, 1013949, 'Beef Pulao Daig (6 Kg Rice + 3 Kg Beef)',  12500.00, 0);
INSERT INTO dish_sub_options VALUES (6692734, 769605, 1013949, 'Beef Pulao Daig (8 Kg Rice + 4 Kg Beef)',  17000.00, 0);
INSERT INTO dish_sub_options VALUES (6692735, 769605, 1013949, 'Beef Pulao Daig (10 Kg Rice + 6 Kg Beef)', 23000.00, 0);
INSERT INTO dish_sub_options VALUES (6692736, 769605, 1013949, 'Beef Pulao Daig (12 Kg Rice + 6 Kg Beef)', 25000.00, 0);
INSERT INTO dish_sub_options VALUES (6692737, 769606, 1013950, 'Beef Qorma Daig (6 Kg Beef)',  13000.00, 0);
INSERT INTO dish_sub_options VALUES (6692738, 769606, 1013950, 'Beef Qorma Daig (8 Kg Beef)',  17000.00, 0);
INSERT INTO dish_sub_options VALUES (6692739, 769606, 1013950, 'Beef Qorma Daig (10 Kg Beef)', 21500.00, 0);
INSERT INTO dish_sub_options VALUES (6692740, 769606, 1013950, 'Beef Qorma Daig (12 Kg Beef)', 25500.00, 0);
INSERT INTO dish_sub_options VALUES (6692741, 769607, 1013952, 'Zarda Daig (5 Kg Rice)',  10000.00, 0);
INSERT INTO dish_sub_options VALUES (6692742, 769607, 1013952, 'Zarda Daig (6 Kg Rice)',  12000.00, 0);
INSERT INTO dish_sub_options VALUES (6692743, 769607, 1013952, 'Zarda Daig (8 Kg Rice)',  16000.00, 0);
INSERT INTO dish_sub_options VALUES (11779660, 769607, 1013952, 'Zarda Daig (10 Kg Rice)', 20000.00, 0);
-- Cake Rusk / Biscuits sizes
INSERT INTO dish_sub_options VALUES (12646119, 1624927, 2456308, 'Half Kg',  650.00, 0);
INSERT INTO dish_sub_options VALUES (12646120, 1624927, 2456308, '1 Kg',    1293.00, 0);
INSERT INTO dish_sub_options VALUES (12646121, 1624928, 2456310, 'Half Kg',  750.00, 0);
INSERT INTO dish_sub_options VALUES (12646122, 1624928, 2456310, '1 Kg',    1552.00, 0);


-- ============================================================
-- 6. ORDERS  (one row per customer order)
-- ============================================================
CREATE TABLE orders (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name    VARCHAR(150)  NOT NULL,
    customer_phone   VARCHAR(20)   NOT NULL,
    customer_address TEXT,                        -- NULL for dine-in / pickup
    order_type       VARCHAR(20)   NOT NULL DEFAULT 'delivery'
                                   CHECK (order_type IN ('delivery', 'pickup', 'dine_in')),
    status           VARCHAR(30)   NOT NULL DEFAULT 'pending'
                                   CHECK (status IN (
                                       'pending', 'confirmed', 'preparing',
                                       'ready', 'out_for_delivery', 'delivered', 'cancelled'
                                   )),
    payment_method   VARCHAR(20)   NOT NULL DEFAULT 'cash'
                                   CHECK (payment_method IN ('cash', 'card', 'online')),
    payment_status   VARCHAR(20)   NOT NULL DEFAULT 'unpaid'
                                   CHECK (payment_status IN ('unpaid', 'paid', 'refunded')),
    subtotal         NUMERIC(12,2) NOT NULL DEFAULT 0,   -- sum of item totals
    delivery_fee     NUMERIC(10,2) NOT NULL DEFAULT 0,
    discount         NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,   -- subtotal + delivery_fee - discount
    notes            TEXT,                               -- special instructions
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_updated_at
BEFORE UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================
-- 7. ORDER_ITEMS  (one row per dish line in an order)
-- ============================================================
CREATE TABLE order_items (
    id             UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id       UUID          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    dish_id        INT           NOT NULL REFERENCES dishes(id),
    dish_name      VARCHAR(200)  NOT NULL,   -- snapshot at time of order
    quantity       INT           NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price     NUMERIC(10,2) NOT NULL,   -- price per unit at time of order
    item_total     NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    -- Selected options (stored as JSONB snapshot so history is preserved even if menu changes)
    -- Example: [{"option": "Packaging", "choice": "Boxed", "extra_price": 15.00}]
    selected_options JSONB        NOT NULL DEFAULT '[]',
    notes          TEXT
);


-- ============================================================
-- USEFUL INDEXES
-- ============================================================
CREATE INDEX idx_orders_status      ON orders (status);
CREATE INDEX idx_orders_created_at  ON orders (created_at DESC);
CREATE INDEX idx_orders_phone       ON orders (customer_phone);
CREATE INDEX idx_order_items_order  ON order_items (order_id);
CREATE INDEX idx_order_items_dish   ON order_items (dish_id);
CREATE INDEX idx_dishes_category    ON dishes (category_id);
CREATE INDEX idx_dishes_status      ON dishes (status, availability);


-- ============================================================
-- HELPER VIEW — flat menu for frontend
-- ============================================================
CREATE OR REPLACE VIEW v_menu AS
SELECT
    c.name          AS category,
    c.priority      AS category_priority,
    d.id            AS dish_id,
    d.name          AS dish_name,
    d.description,
    d.tag,
    CASE WHEN d.price > 0 THEN d.price ELSE d.base_price END AS display_price,
    d.price,
    d.base_price,
    d.status,
    d.availability
FROM dishes d
JOIN categories c ON c.id = d.category_id
WHERE d.status = 1 AND d.availability = 1
ORDER BY c.priority DESC, d.name;


-- ============================================================
-- HELPER VIEW — order summary with items
-- ============================================================
CREATE OR REPLACE VIEW v_order_summary AS
SELECT
    o.id              AS order_id,
    o.customer_name,
    o.customer_phone,
    o.order_type,
    o.status,
    o.payment_method,
    o.payment_status,
    o.subtotal,
    o.delivery_fee,
    o.discount,
    o.total_amount,
    o.notes           AS order_notes,
    o.created_at,
    oi.id             AS item_id,
    oi.dish_name,
    oi.quantity,
    oi.unit_price,
    oi.item_total,
    oi.selected_options,
    oi.notes          AS item_notes
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
ORDER BY o.created_at DESC;