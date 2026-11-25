from flask import Flask, request, jsonify, redirect
import json, os, uuid, urllib.request, urllib.error
from datetime import datetime

app = Flask(__name__)

RESERVATIONS_FILE = '/var/www/vayo-sport.com/api/reservations.json'
NOTIFY_EMAIL = 'vayo@blade-agency.net'
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

MORNING_CLIENT_ID     = 'a83f4e69-4bfe-4e24-a999-5237e5920c01'
MORNING_CLIENT_SECRET = 'g-2TGn:UA!y5B7Pu0^7OhJ{3]YsyS@1-'
MORNING_PLUGIN_ID     = '06061227-8a07-454f-93a5-2a47353617d2'

PRICE_MAP = {
    'grip-3':          45,
    'grip-15':        150,
    'grip-30':        350,
    'serum-50':        69,
    'serum-100':      109,
    'frame-protector': 45,
}

SHIPPING     = 30
ORDERS_FILE  = '/var/www/vayo-sport.com/api/orders.json'
SUCCESS_URL  = 'https://www.vayo-sport.com/pages/order-success.html'


@app.after_request
def cors(r):
    r.headers['Access-Control-Allow-Origin'] = 'https://www.vayo-sport.com'
    r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return r

@app.route('/api/reserve', methods=['OPTIONS'])
@app.route('/api/payment', methods=['OPTIONS'])
def options():
    return '', 204

@app.route('/api/reserve', methods=['POST'])
def reserve():
    data = request.get_json(silent=True) or {}
    name  = (data.get('name')  or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip()
    size  = (data.get('size')  or '').strip()

    if not all([name, phone, email, size]):
        return jsonify({'error': 'missing_fields'}), 400

    reservation = {
        'name': name, 'phone': phone, 'email': email, 'size': size,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    reservations = []
    if os.path.exists(RESERVATIONS_FILE):
        try:
            reservations = json.load(open(RESERVATIONS_FILE, encoding='utf-8'))
        except Exception:
            reservations = []
    reservations.append(reservation)
    with open(RESERVATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reservations, f, ensure_ascii=False, indent=2)

    if RESEND_API_KEY:
        try:
            send_resend_admin(reservation)
        except Exception as e:
            print(f'Admin email error: {e}')
        try:
            send_resend_customer(reservation)
        except Exception as e:
            print(f'Customer email error: {e}')

    return jsonify({'success': True})


# ── Order persistence ─────────────────────────────────────────────────────────

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        return json.load(open(ORDERS_FILE, encoding='utf-8'))
    except Exception:
        return []

def save_orders(orders):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def create_order(order_id, items, customer, total):
    orders = load_orders()
    orders.append({
        'id': order_id, 'items': items, 'customer': customer,
        'total': total, 'status': 'pending',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    save_orders(orders)

def find_order(order_id):
    return next((o for o in load_orders() if o['id'] == order_id), None)

def mark_paid(order_id):
    orders = load_orders()
    for o in orders:
        if o['id'] == order_id and o['status'] == 'pending':
            o['status'] = 'paid'
            o['paid_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_orders(orders)

# ── Morning (Green Invoice) payment ──────────────────────────────────────────

def morning_token():
    payload = json.dumps({
        'grant_type':    'client_credentials',
        'client_id':     MORNING_CLIENT_ID,
        'client_secret': MORNING_CLIENT_SECRET
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.morning.co/idp/v1/oauth/token',
        data=payload,
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())['access_token']

@app.route('/api/payment', methods=['POST'])
def payment():
    data     = request.get_json(silent=True) or {}
    items    = data.get('items', [])
    customer = data.get('customer', {})

    if not items:
        return jsonify({'error': 'empty_cart'}), 400

    name  = (customer.get('name')  or '').strip()
    email = (customer.get('email') or '').strip()

    if not name or not email:
        return jsonify({'error': 'missing_customer'}), 400

    # Server-side price validation
    subtotal   = 0
    desc_parts = []
    for item in items:
        item_id        = (item.get('id') or '').strip()
        qty            = max(1, int(item.get('qty', 1)))
        expected_price = PRICE_MAP.get(item_id)
        if expected_price is None:
            return jsonify({'error': 'invalid_item', 'id': item_id}), 400
        subtotal += expected_price * qty
        desc_parts.append(f"{item.get('name', item_id)} ×{qty}")

    total       = subtotal + SHIPPING
    description = ', '.join(desc_parts) + ' + משלוח'

    try:
        token = morning_token()
    except Exception as e:
        print(f'Morning token error: {e}')
        return jsonify({'error': 'payment_unavailable'}), 503

    order_id    = uuid.uuid4().hex[:8].upper()
    create_order(order_id, items, customer, total)
    success_url = f'https://www.vayo-sport.com/pages/order-success.html?order={order_id}'

    payload = json.dumps({
        'description': f'[{order_id}] {description}',
        'type':        320,
        'amount':      total,
        'currency':    'ILS',
        'vatType':     0,
        'lang':        'he',
        'pluginId':    MORNING_PLUGIN_ID,
        'group':       100,
        'successUrl':  success_url,
        'client':      {'name': name, 'emails': [email]}
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.greeninvoice.co.il/api/v1/payments/form',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type':  'application/json',
            'Accept':        'application/json'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        # Patch success URL into Morning redirect — append as query param if possible
        payment_url = result['url']
        sep = '&' if '?' in payment_url else '?'
        # Store order_id for client to pass to confirm endpoint
        return jsonify({'url': payment_url, 'total': total, 'order': order_id})
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'Morning payment form error {e.code}: {body}')
        return jsonify({'error': 'payment_form_failed'}), 502

    return jsonify({'success': True})


# ── Payment confirmation ──────────────────────────────────────────────────────

@app.route('/api/payment/confirm', methods=['GET'])
def payment_confirm():
    order_id = (request.args.get('order') or '').strip().upper()
    order    = find_order(order_id) if order_id else None
    if not order:
        return redirect(SUCCESS_URL)
    if order.get('status') != 'paid':
        mark_paid(order_id)
        order['status'] = 'paid'
        try:
            send_order_email_customer(order)
            print(f'[{order_id}] customer email sent to {order["customer"].get("email")}')
        except Exception as e:
            print(f'[{order_id}] customer email ERROR: {e}')
        try:
            send_order_email_admin(order)
            print(f'[{order_id}] admin email sent')
        except Exception as e:
            print(f'[{order_id}] admin email ERROR: {e}')
    return redirect(f'{SUCCESS_URL}?order={order_id}')

@app.route('/api/payment/webhook', methods=['POST', 'OPTIONS'])
def payment_webhook():
    if request.method == 'OPTIONS':
        return '', 204
    data     = request.get_json(silent=True) or {}
    order_id = (data.get('clientNote') or data.get('description') or '').strip().upper()
    # Try to extract 8-char order id from description string
    import re
    match = re.search(r'([0-9A-F]{8})', order_id)
    order_id = match.group(1) if match else order_id
    order = find_order(order_id) if order_id else None
    if order and order.get('status') != 'paid':
        mark_paid(order_id)
        order['status'] = 'paid'
        try:    send_order_email_customer(order)
        except Exception as e: print(f'Webhook email customer: {e}')
        try:    send_order_email_admin(order)
        except Exception as e: print(f'Webhook email admin: {e}')
    return jsonify({'ok': True})


# ── Order status (public) ─────────────────────────────────────────────────────

@app.route('/api/order/status', methods=['GET'])
def order_status():
    order_id = (request.args.get('order') or '').strip().upper()
    email    = (request.args.get('email')  or '').strip().lower()
    if not order_id or not email:
        return jsonify({'error': 'missing_params'}), 400
    order = find_order(order_id)
    if not order or order.get('customer', {}).get('email', '').lower() != email:
        return jsonify({'error': 'not_found'}), 404
    return jsonify({
        'id':       order['id'],
        'status':   order.get('status', 'pending'),
        'total':    order.get('total'),
        'items':    order.get('items', []),
        'tracking': order.get('tracking'),
        'carrier':  order.get('carrier'),
        'paid_at':  order.get('paid_at'),
        'shipped_at': order.get('shipped_at'),
        'created_at': order.get('created_at'),
    })

# ── Admin: list orders ────────────────────────────────────────────────────────

ORDERS_ADMIN_KEY = os.environ.get('ORDERS_ADMIN_KEY', 'vayo-admin-2026')

def admin_auth():
    return request.args.get('key') == ORDERS_ADMIN_KEY or            request.headers.get('X-Admin-Key') == ORDERS_ADMIN_KEY

@app.route('/api/admin/orders', methods=['GET'])
def admin_orders():
    if not admin_auth():
        return jsonify({'error': 'unauthorized'}), 401
    orders = load_orders()
    # newest first
    orders.sort(key=lambda o: o.get('created_at', ''), reverse=True)
    return jsonify(orders)

@app.route('/api/admin/orders/<order_id>/ship', methods=['POST'])
def admin_ship(order_id):
    if not admin_auth():
        return jsonify({'error': 'unauthorized'}), 401
    data     = request.get_json(silent=True) or {}
    tracking = (data.get('tracking') or '').strip()
    carrier  = (data.get('carrier')  or '').strip()
    orders   = load_orders()
    order    = next((o for o in orders if o['id'] == order_id.upper()), None)
    if not order:
        return jsonify({'error': 'not_found'}), 404
    if order.get('status') == 'shipped':
        return jsonify({'error': 'already_shipped'}), 400
    order['status']     = 'shipped'
    order['tracking']   = tracking or None
    order['carrier']    = carrier  or None
    order['shipped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_orders(orders)
    try:
        send_shipped_email(order)
        print(f'[{order_id}] shipped email sent')
    except Exception as e:
        print(f'[{order_id}] shipped email error: {e}')
    return jsonify({'ok': True, 'order': order})

@app.route('/api/admin/orders/<order_id>/status', methods=['POST'])
def admin_update_status(order_id):
    """Generic status update (refund, cancel, etc.)"""
    if not admin_auth():
        return jsonify({'error': 'unauthorized'}), 401
    data   = request.get_json(silent=True) or {}
    status = (data.get('status') or '').strip()
    if status not in ('pending', 'paid', 'shipped', 'cancelled', 'refunded'):
        return jsonify({'error': 'invalid_status'}), 400
    orders = load_orders()
    order  = next((o for o in orders if o['id'] == order_id.upper()), None)
    if not order:
        return jsonify({'error': 'not_found'}), 404
    order['status'] = status
    save_orders(orders)
    return jsonify({'ok': True})

def resend_post(payload_dict):
    payload = json.dumps(payload_dict).encode('utf-8')
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'python-requests/2.28.0'
        }
    )
    urllib.request.urlopen(req, timeout=10)

def send_resend_admin(r):
    html = f"""<!DOCTYPE html>
<html lang="he">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#060606;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#060606;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0d0d0d;border:1px solid #1a1a1a;">

        <!-- HEADER -->
        <tr>
          <td style="padding:32px 40px 24px;border-bottom:1px solid #1a1a1a;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <img src="https://www.vayo-sport.com/images/vayo-logo.png" alt="VAYO" height="36" style="display:block;height:36px;width:auto;" />
                </td>
                <td align="right">
                  <span style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.08em;color:#6AEBD6;text-transform:uppercase;">New Reservation</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- PRODUCT IMAGE -->
        <tr>
          <td style="padding:0;background:#111111;">
            <img src="https://www.vayo-sport.com/images/products/serum-h.jpg"
                 alt="VAYO Grip Serum"
                 width="600"
                 style="display:block;width:100%;max-width:600px;height:auto;" />
          </td>
        </tr>

        <!-- TITLE -->
        <tr>
          <td style="padding:32px 40px 8px;" dir="rtl">
            <p style="margin:0 0 6px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">N / SERIES 01</p>
            <h1 style="margin:0 0 4px;font-size:26px;font-weight:700;letter-spacing:0.08em;color:#ffffff;text-transform:uppercase;">GRIP SERUM</h1>
            <p style="margin:0;font-family:'Courier New',monospace;font-size:12px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;">שריון בקבוקון חדש</p>
          </td>
        </tr>

        <!-- DIVIDER -->
        <tr><td style="padding:16px 40px 0;"><div style="height:1px;background:linear-gradient(90deg,#6AEBD6 0%,transparent 100%);"></div></td></tr>

        <!-- DETAILS TABLE -->
        <tr>
          <td style="padding:24px 40px 32px;" dir="rtl">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:12px 0;border-bottom:1px solid #1a1a1a;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;width:130px;">שם</td>
                      <td style="font-size:15px;color:#ffffff;font-weight:500;">{r['name']}</td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 0;border-bottom:1px solid #1a1a1a;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;width:130px;">טלפון</td>
                      <td style="font-size:15px;color:#6AEBD6;font-weight:500;">{r['phone']}</td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 0;border-bottom:1px solid #1a1a1a;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;width:130px;">אימייל</td>
                      <td style="font-size:15px;color:#ffffff;">{r['email']}</td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 0;border-bottom:1px solid #1a1a1a;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;width:130px;">גודל</td>
                      <td style="font-size:15px;color:#ffffff;font-weight:700;">{r['size']}</td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 0;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;width:130px;">תאריך</td>
                      <td style="font-family:'Courier New',monospace;font-size:13px;color:#444444;">{r['timestamp']}</td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #1a1a1a;background:#0a0a0a;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.08em;color:#333333;text-transform:uppercase;">
                  VAYO &nbsp;·&nbsp; Made in Israel &nbsp;·&nbsp; Engineered for Padel
                </td>
                <td align="right" style="font-family:'Courier New',monospace;font-size:10px;color:#333333;">
                  vayo-sport.com
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""
    resend_post({
        'from': 'VAYO <noreply@vayo-sport.com>',
        'to': [NOTIFY_EMAIL],
        'subject': f'שריון בקבוקון חדש - {r["name"]} / {r["size"]}',
        'html': html
    })

def send_resend_customer(r):
    html = f"""<!DOCTYPE html>
<html lang="he">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#060606;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#060606;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0d0d0d;border:1px solid #1a1a1a;">

        <!-- HEADER -->
        <tr>
          <td style="padding:32px 40px 24px;border-bottom:1px solid #1a1a1a;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <img src="https://www.vayo-sport.com/images/vayo-logo.png" alt="VAYO" height="36" style="display:block;height:36px;width:auto;" />
                </td>
                <td align="right">
                  <span style="display:inline-block;padding:5px 14px;border:1px solid #6AEBD6;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">Confirmed</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- PRODUCT IMAGE -->
        <tr>
          <td style="padding:0;background:#111111;">
            <img src="https://www.vayo-sport.com/images/products/serum-h.jpg"
                 alt="VAYO Grip Serum"
                 width="600"
                 style="display:block;width:100%;max-width:600px;height:auto;" />
          </td>
        </tr>

        <!-- HERO TEXT -->
        <tr>
          <td style="padding:36px 40px 0;" dir="rtl">
            <p style="margin:0 0 6px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">N / SERIES 01</p>
            <h1 style="margin:0 0 20px;font-size:28px;font-weight:700;letter-spacing:0.06em;color:#ffffff;text-transform:uppercase;">GRIP SERUM</h1>
            <p style="margin:0 0 8px;font-size:16px;color:#cccccc;line-height:1.7;">היי {r['name']},</p>
            <p style="margin:0 0 16px;font-size:15px;color:#888888;line-height:1.8;">
              הבקבוקון שלך שוריין בהצלחה.<br>אין צורך לשלם כרגע.
            </p>
            <p style="margin:0 0 0;font-size:15px;color:#888888;line-height:1.8;">
              ברגע שהמלאי יתחדש, נשלח לך הודעת וואטסאפ למספר <span style="color:#6AEBD6;font-weight:600;">{r['phone']}</span><br>עם לינק לתשלום במחיר ההשקה המוזל, לפני כולם.
            </p>
          </td>
        </tr>

        <!-- DIVIDER -->
        <tr><td style="padding:28px 40px 0;"><div style="height:1px;background:linear-gradient(90deg,#6AEBD6 0%,transparent 100%);"></div></td></tr>

        <!-- ORDER SUMMARY -->
        <tr>
          <td style="padding:24px 40px 32px;" dir="rtl">
            <p style="margin:0 0 16px;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#444444;text-transform:uppercase;">פרטי השריון</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #1a1a1a;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;width:130px;">גודל</td>
                      <td style="font-size:15px;color:#ffffff;font-weight:700;">{r['size']}</td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.06em;color:#555555;text-transform:uppercase;width:130px;">תאריך שריון</td>
                      <td style="font-family:'Courier New',monospace;font-size:12px;color:#444444;">{r['timestamp']}</td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td style="padding:0 40px 36px;" dir="rtl">
            <a href="https://www.vayo-sport.com/pages/serum.html"
               style="display:inline-block;padding:14px 32px;background:#6AEBD6;color:#060606;font-family:Arial,sans-serif;font-size:13px;font-weight:700;letter-spacing:0.1em;text-decoration:none;text-transform:uppercase;">
              לעמוד המוצר
            </a>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #1a1a1a;background:#0a0a0a;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.08em;color:#333333;text-transform:uppercase;">
                  VAYO &nbsp;·&nbsp; Made in Israel &nbsp;·&nbsp; Engineered for Padel
                </td>
                <td align="right">
                  <a href="mailto:vayo@blade-agency.com" style="font-family:'Courier New',monospace;font-size:10px;color:#333333;text-decoration:none;">vayo@blade-agency.com</a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""
    resend_post({
        'from': 'VAYO <noreply@vayo-sport.com>',
        'to': [r['email']],
        'subject': 'השריון שלך אושר - VAYO Grip Serum',
        'html': html
    })


def send_order_email_customer(order):
    c     = order.get('customer', {})
    items = order.get('items', [])
    rows  = ''
    for item in items:
        rows += f"""
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #1a1a1a;font-size:14px;color:#fff;">{item.get('name','')}</td>
                <td style="padding:10px 0;border-bottom:1px solid #1a1a1a;font-family:'Courier New',monospace;font-size:11px;color:#555;">{item.get('variant','')}</td>
                <td style="padding:10px 0;border-bottom:1px solid #1a1a1a;font-family:'Courier New',monospace;font-size:12px;color:#aaa;text-align:center;">{item.get('qty',1)}</td>
                <td style="padding:10px 0;border-bottom:1px solid #1a1a1a;font-family:'Courier New',monospace;font-size:13px;color:#6AEBD6;text-align:left;">{item.get('price',0)*item.get('qty',1)} ₪</td>
              </tr>"""
    subtotal = order['total'] - SHIPPING
    html = f"""<!DOCTYPE html>
<html lang="he"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#060606;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#060606;padding:40px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0d0d0d;border:1px solid #1a1a1a;">
  <tr><td style="padding:32px 40px 24px;border-bottom:1px solid #1a1a1a;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td><img src="https://www.vayo-sport.com/images/vayo-logo.png" alt="VAYO" height="32" style="display:block;" /></td>
      <td align="left" style="padding-right:0;"><span style="display:inline-block;padding:5px 14px;border:1px solid #6AEBD6;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">הזמנה אושרה</span></td>
    </tr></table>
  </td></tr>
  <tr><td style="padding:32px 40px 8px;" dir="rtl">
    <p style="margin:0 0 6px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">הזמנה #{order['id']}</p>
    <h1 style="margin:0 0 20px;font-size:24px;font-weight:700;letter-spacing:0.06em;color:#ffffff;text-transform:uppercase;">תודה, {c.get('name','')}</h1>
    <p style="margin:0;font-size:15px;color:#888;line-height:1.8;">ההזמנה שלך התקבלה ואושרה. המלאי הראשון כבר בדרך אלינו. נשלח לך ישירות ברגע שיגיע למחסן.</p>
  </td></tr>
  <tr><td style="padding:16px 40px 0;"><div style="height:1px;background:linear-gradient(90deg,#6AEBD6 0%,transparent 100%);"></div></td></tr>
  <tr><td style="padding:24px 40px 8px;" dir="rtl">
    <p style="margin:0 0 16px;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#444;text-transform:uppercase;">פרטי ההזמנה</p>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <th style="font-family:'Courier New',monospace;font-size:10px;color:#444;text-transform:uppercase;text-align:right;padding-bottom:8px;">מוצר</th>
        <th style="font-family:'Courier New',monospace;font-size:10px;color:#444;text-transform:uppercase;text-align:right;padding-bottom:8px;">גרסה</th>
        <th style="font-family:'Courier New',monospace;font-size:10px;color:#444;text-transform:uppercase;text-align:center;padding-bottom:8px;">כמות</th>
        <th style="font-family:'Courier New',monospace;font-size:10px;color:#444;text-transform:uppercase;text-align:left;padding-bottom:8px;">מחיר</th>
      </tr>
      {rows}
      <tr>
        <td colspan="3" style="padding:10px 0;font-family:'Courier New',monospace;font-size:11px;color:#555;text-transform:uppercase;border-bottom:1px solid #1a1a1a;">משלוח</td>
        <td style="padding:10px 0;font-family:'Courier New',monospace;font-size:13px;color:#aaa;text-align:left;border-bottom:1px solid #1a1a1a;">{SHIPPING} ₪</td>
      </tr>
      <tr>
        <td colspan="3" style="padding:14px 0 0;font-size:14px;font-weight:700;color:#fff;">סה"כ</td>
        <td style="padding:14px 0 0;font-family:'Courier New',monospace;font-size:16px;font-weight:700;color:#6AEBD6;text-align:left;">{order['total']} ₪</td>
      </tr>
    </table>
  </td></tr>
  <tr><td style="padding:28px 40px;" dir="rtl">
    <p style="margin:0 0 6px;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#444;text-transform:uppercase;">כתובת למשלוח</p>
    <p style="margin:0;font-size:14px;color:#888;">{c.get('address','')}</p>
  </td></tr>
  <tr><td style="padding:0 40px 32px;" dir="rtl">
    <p style="margin:0 0 14px;font-size:13px;color:#555;">האישור נשלח לכתובת המייל שלך. לבדיקת סטטוס ההזמנה בכל עת:</p>
    <a href="https://www.vayo-sport.com/pages/order-status.html?order={order['id']}"
       style="display:inline-block;padding:12px 24px;background:transparent;border:1px solid #6AEBD6;color:#6AEBD6;font-family:'Courier New',monospace;font-size:11px;font-weight:700;letter-spacing:0.1em;text-decoration:none;text-transform:uppercase;">
      בדיקת סטטוס הזמנה
    </a>
  </td></tr>
  <tr><td style="padding:20px 40px;border-top:1px solid #1a1a1a;background:#0a0a0a;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.08em;color:#333;text-transform:uppercase;">VAYO &nbsp;·&nbsp; Engineered for Padel</td>
      <td align="right"><a href="mailto:vayo@blade-agency.net" style="font-family:'Courier New',monospace;font-size:10px;color:#333;text-decoration:none;">vayo@blade-agency.net</a></td>
    </tr></table>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
    resend_post({
        'from': 'VAYO <noreply@vayo-sport.com>',
        'to':   [c.get('email', NOTIFY_EMAIL)],
        'subject': f'הזמנה #{order["id"]} אושרה — VAYO',
        'html': html
    })

def send_order_email_admin(order):
    c     = order.get('customer', {})
    items = order.get('items', [])
    rows  = ''.join(
        f"<tr><td style='padding:8px 0;border-bottom:1px solid #1a1a1a;color:#fff;font-size:14px;'>{i.get('name','')} · {i.get('variant','')}</td>"
        f"<td style='padding:8px 0;border-bottom:1px solid #1a1a1a;font-family:monospace;color:#6AEBD6;text-align:right;'>{i.get('price',0)*i.get('qty',1)} ₪ (×{i.get('qty',1)})</td></tr>"
        for i in items
    )
    html = f"""<!DOCTYPE html>
<html lang="he"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#060606;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#060606;padding:40px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0d0d0d;border:1px solid #1a1a1a;">
  <tr><td style="padding:28px 40px;border-bottom:1px solid #1a1a1a;">
    <img src="https://www.vayo-sport.com/images/vayo-logo.png" alt="VAYO" height="30" style="display:block;margin-bottom:12px;" />
    <p style="margin:0;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">הזמנה חדשה #{order['id']}</p>
  </td></tr>
  <tr><td style="padding:24px 40px;" dir="rtl">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-family:monospace;font-size:11px;color:#555;text-transform:uppercase;width:120px;">שם</td><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-size:15px;color:#fff;">{c.get('name','')}</td></tr>
      <tr><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-family:monospace;font-size:11px;color:#555;text-transform:uppercase;">טלפון</td><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-size:15px;color:#6AEBD6;">{c.get('phone','')}</td></tr>
      <tr><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-family:monospace;font-size:11px;color:#555;text-transform:uppercase;">מייל</td><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-size:14px;color:#fff;">{c.get('email','')}</td></tr>
      <tr><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-family:monospace;font-size:11px;color:#555;text-transform:uppercase;">כתובת</td><td style="padding:8px 0;border-bottom:1px solid #1a1a1a;font-size:14px;color:#fff;">{c.get('address','')}</td></tr>
      <tr><td colspan="2" style="padding:16px 0 8px;"><p style="margin:0;font-family:monospace;font-size:10px;color:#444;text-transform:uppercase;letter-spacing:0.08em;">פרטי הזמנה</p></td></tr>
      {rows}
      <tr><td style="padding:12px 0 0;font-size:14px;font-weight:700;color:#fff;">סה"כ</td><td style="padding:12px 0 0;font-family:monospace;font-size:16px;font-weight:700;color:#6AEBD6;text-align:right;">{order['total']} ₪</td></tr>
    </table>
  </td></tr>
  <tr><td style="padding:16px 40px;border-top:1px solid #1a1a1a;background:#0a0a0a;font-family:monospace;font-size:10px;color:#333;">
    {order.get('created_at','')}
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
    resend_post({
        'from':    'VAYO <noreply@vayo-sport.com>',
        'to':      [NOTIFY_EMAIL],
        'subject': f'הזמנה חדשה #{order["id"]} — {c.get("name","")} | {order["total"]} ₪',
        'html':    html
    })


def send_shipped_email(order):
    c        = order.get('customer', {})
    tracking = order.get('tracking')
    carrier  = order.get('carrier', 'שליח')
    items    = order.get('items', [])
    rows = ''
    for item in items:
        rows += f"<tr><td style='padding:8px 0;border-bottom:1px solid #1a1a1a;font-size:14px;color:#fff;'>{item.get('name','')} · {item.get('variant','')}</td><td style='padding:8px 0;border-bottom:1px solid #1a1a1a;font-family:monospace;font-size:12px;color:#aaa;text-align:left;'>×{item.get('qty',1)}</td></tr>"

    tracking_block = ''
    if tracking:
        tracking_block = f"""
  <tr><td style="padding:0 40px 32px;" dir="rtl">
    <div style="background:#111;border:1px solid rgba(106,235,214,0.2);padding:20px 24px;">
      <p style="margin:0 0 8px;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">{carrier} - מספר מעקב</p>
      <p style="margin:0;font-family:'Courier New',monospace;font-size:18px;font-weight:700;color:#fff;letter-spacing:0.08em;">{tracking}</p>
    </div>
  </td></tr>"""

    html = f"""<!DOCTYPE html>
<html lang="he"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#060606;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#060606;padding:40px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0d0d0d;border:1px solid #1a1a1a;">
  <tr><td style="padding:32px 40px 24px;border-bottom:1px solid #1a1a1a;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td><img src="https://www.vayo-sport.com/images/vayo-logo.png" alt="VAYO" height="32" style="display:block;" /></td>
      <td align="left"><span style="display:inline-block;padding:5px 14px;border:1px solid #6AEBD6;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">ההזמנה בדרך</span></td>
    </tr></table>
  </td></tr>
  <tr><td style="padding:32px 40px 24px;" dir="rtl">
    <p style="margin:0 0 6px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.1em;color:#6AEBD6;text-transform:uppercase;">הזמנה #{order['id']}</p>
    <h1 style="margin:0 0 16px;font-size:24px;font-weight:700;letter-spacing:0.06em;color:#fff;text-transform:uppercase;">ההזמנה שלך בדרך, {c.get('name','').split()[0]}!</h1>
    <p style="margin:0;font-size:15px;color:#888;line-height:1.8;">האריזה יצאה מהמחסן ובדרכה אליך. צפי הגעה: 3-5 ימי עסקים.</p>
  </td></tr>
  <tr><td style="padding:16px 40px 0;"><div style="height:1px;background:linear-gradient(90deg,#6AEBD6 0%,transparent 100%);"></div></td></tr>
  {tracking_block}
  <tr><td style="padding:24px 40px 8px;" dir="rtl">
    <p style="margin:0 0 12px;font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.1em;color:#444;text-transform:uppercase;">פרטי הזמנה</p>
    <table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
  </td></tr>
  <tr><td style="padding:12px 40px 32px;" dir="rtl">
    <p style="margin:0 0 4px;font-family:'Courier New',monospace;font-size:10px;color:#444;text-transform:uppercase;">כתובת למשלוח</p>
    <p style="margin:0;font-size:14px;color:#888;">{c.get('address','')}</p>
  </td></tr>
  <tr><td style="padding:20px 40px;border-top:1px solid #1a1a1a;background:#0a0a0a;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td style="font-family:'Courier New',monospace;font-size:10px;color:#333;text-transform:uppercase;">VAYO &nbsp;·&nbsp; Engineered for Padel</td>
      <td align="right"><a href="mailto:vayo@blade-agency.net" style="font-family:'Courier New',monospace;font-size:10px;color:#333;text-decoration:none;">vayo@blade-agency.net</a></td>
    </tr></table>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
    resend_post({
        'from': 'VAYO <noreply@vayo-sport.com>',
        'to':   [c.get('email', NOTIFY_EMAIL)],
        'subject': f'ההזמנה שלך בדרך — VAYO #{order["id"]}',
        'html': html
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
