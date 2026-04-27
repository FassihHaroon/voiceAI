import sys
import urllib.request, json

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = 'http://127.0.0.1:8001/api/v1'

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        return json.loads(urllib.request.urlopen(req).read()), None
    except urllib.error.HTTPError as e:
        return None, (e.code, json.loads(e.read()))

SEP = '-' * 62

# ─────────────────────────────────────────────────────────────
# TEST 1: Special Choice — Leg (1st) + Thigh (2nd) + Normal
# dish 708010, price=0, base=755
# option 185814 Packaging   : 862314=Normal(755), 862315=Boxed(770)
# option 189818 1st Piece   : 887331=Chest, 887332=Leg, 887333=Thigh, 887334=Wing
# option 189821 2nd Piece   : 887347=Chest, 887348=Leg, 887349=Thigh, 887350=Wing
# ─────────────────────────────────────────────────────────────
print(SEP)
print('TEST 1: Special Choice  |  Leg + Thigh + Normal packaging')
print(SEP)
order, err = post(f'{base}/orders', {
    'customer_name': 'Ali Hassan',
    'customer_phone': '03211234567',
    'customer_address': '5 Model Town, Lahore',
    'order_type': 'delivery',
    'payment_method': 'cash',
    'delivery_fee': 50,
    'discount': 0,
    'items': [{
        'dish_id': 708010,
        'quantity': 1,
        'selected_options': [
            {'option_id': 185814, 'sub_option_id': 862314},  # Packaging: Normal (Rs 755)
            {'option_id': 189818, 'sub_option_id': 887332},  # 1st piece: Leg   (free)
            {'option_id': 189821, 'sub_option_id': 887349},  # 2nd piece: Thigh (free)
        ]
    }]
})
if order:
    print(f'  [PASS] Order created: {order["id"]}')
    print(f'  Subtotal Rs {order["subtotal"]} + delivery Rs {order["delivery_fee"]} = Total Rs {order["total_amount"]}')
    for it in order['items']:
        print(f'  Item: {it["dish_name"]} x{it["quantity"]} @ Rs {it["unit_price"]} = Rs {it["item_total"]}')
        for s in it['selected_options']:
            print(f'    {s["option_name"]:30s}  ->  {s["choice_name"]}  (extra=Rs {s["extra_price"]})')
else:
    print(f'  [FAIL] HTTP {err[0]}: {err[1]["detail"]}')

# ─────────────────────────────────────────────────────────────
# TEST 2: Special Choice — Wing + Chest + Boxed
# ─────────────────────────────────────────────────────────────
print()
print(SEP)
print('TEST 2: Special Choice  |  Wing + Chest + Boxed packaging')
print(SEP)
order2, err2 = post(f'{base}/orders', {
    'customer_name': 'Sara Khan',
    'customer_phone': '03001234567',
    'order_type': 'pickup',
    'payment_method': 'card',
    'delivery_fee': 0,
    'discount': 0,
    'items': [{
        'dish_id': 708010,
        'quantity': 2,
        'selected_options': [
            {'option_id': 185814, 'sub_option_id': 862315},  # Packaging: Boxed (Rs 770)
            {'option_id': 189818, 'sub_option_id': 887334},  # 1st piece: Wing  (free)
            {'option_id': 189821, 'sub_option_id': 887347},  # 2nd piece: Chest (free)
        ]
    }]
})
if order2:
    it = order2['items'][0]
    print(f'  [PASS] Order created | unit=Rs {it["unit_price"]} x{it["quantity"]} = Rs {it["item_total"]}')
    for s in it['selected_options']:
        print(f'    {s["option_name"]:30s}  ->  {s["choice_name"]}')
else:
    print(f'  [FAIL] HTTP {err2[0]}: {err2[1]["detail"]}')

# ─────────────────────────────────────────────────────────────
# TEST 3: SECURITY — sub_option from wrong option group (must block)
#   887333 = Thigh, but belongs to option 189818, NOT 189821
# ─────────────────────────────────────────────────────────────
print()
print(SEP)
print('TEST 3: Wrong sub_option for option group  (must be BLOCKED)')
print(SEP)
_, err3 = post(f'{base}/orders', {
    'customer_name': 'Hacker', 'customer_phone': '0000',
    'order_type': 'delivery', 'payment_method': 'cash',
    'delivery_fee': 0, 'discount': 0,
    'items': [{
        'dish_id': 708010, 'quantity': 1,
        'selected_options': [
            {'option_id': 185814, 'sub_option_id': 862314},
            {'option_id': 189818, 'sub_option_id': 887332},
            {'option_id': 189821, 'sub_option_id': 887333},  # 887333 belongs to 189818, not 189821
        ]
    }]
})
if err3:
    print(f'  [PASS] Blocked correctly (HTTP {err3[0]}): {err3[1]["detail"]}')
else:
    print('  [FAIL] Should have been blocked!')

# ─────────────────────────────────────────────────────────────
# TEST 4: Missing required option group (must block)
# ─────────────────────────────────────────────────────────────
print()
print(SEP)
print('TEST 4: Missing 2nd piece selection  (must be BLOCKED)')
print(SEP)
_, err4 = post(f'{base}/orders', {
    'customer_name': 'Test', 'customer_phone': '0300',
    'order_type': 'delivery', 'payment_method': 'cash',
    'delivery_fee': 0, 'discount': 0,
    'items': [{
        'dish_id': 708010, 'quantity': 1,
        'selected_options': [
            {'option_id': 185814, 'sub_option_id': 862314},
            {'option_id': 189818, 'sub_option_id': 887332},
            # option 189821 intentionally missing
        ]
    }]
})
if err4:
    print(f'  [PASS] Blocked correctly (HTTP {err4[0]}): {err4[1]["detail"]}')
else:
    print('  [FAIL] Should have been blocked!')

# ─────────────────────────────────────────────────────────────
# TEST 5: Single Choice (708006) — one chicken piece + packaging
# option 189813 Chicken Variation: 887315=Chest, 887316=Leg, 887317=Thigh, 887318=Wing
# option 189820 Packaging        : 887337=Normal(575), 887338=Boxed(590)
# ─────────────────────────────────────────────────────────────
print()
print(SEP)
print('TEST 5: Single Choice  |  Thigh + Normal packaging')
print(SEP)
order5, err5 = post(f'{base}/orders', {
    'customer_name': 'Omar Farooq',
    'customer_phone': '03331234567',
    'customer_address': '10 Gulberg, Lahore',
    'order_type': 'delivery',
    'payment_method': 'cash',
    'delivery_fee': 50,
    'discount': 0,
    'items': [{
        'dish_id': 708006, 'quantity': 1,
        'selected_options': [
            {'option_id': 189813, 'sub_option_id': 887317},  # Chicken Variation: Thigh
            {'option_id': 189820, 'sub_option_id': 887337},  # Packaging: Normal (Rs 575)
        ]
    }]
})
if order5:
    it = order5['items'][0]
    print(f'  [PASS] Order created | unit=Rs {it["unit_price"]} | total=Rs {order5["total_amount"]}')
    for s in it['selected_options']:
        print(f'    {s["option_name"]:30s}  ->  {s["choice_name"]}  (Rs {s["extra_price"]})')
else:
    print(f'  [FAIL] HTTP {err5[0]}: {err5[1]["detail"]}')

print()
print(SEP)
print('ALL TESTS COMPLETE')
print(SEP)
