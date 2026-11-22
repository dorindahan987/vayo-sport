/* ── VAYO Cart ── */
(function () {
  const STORAGE_KEY = 'vayo-cart';

  // ── Data ──────────────────────────────────────────────
  function getCart() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }
    catch { return []; }
  }
  function saveCart(cart) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
  }
  function getCount() {
    return getCart().reduce((n, i) => n + i.qty, 0);
  }
  function getTotal() {
    return getCart().reduce((n, i) => n + i.price * i.qty, 0);
  }

  function addItem(item) {
    const cart = getCart();
    const existing = cart.find(i => i.id === item.id);
    if (existing) { existing.qty += 1; }
    else { cart.push({ ...item, qty: 1 }); }
    saveCart(cart);
    updateBadge();
    renderDrawer();
    openDrawer();
  }
  function removeItem(id) {
    saveCart(getCart().filter(i => i.id !== id));
    updateBadge();
    renderDrawer();
  }
  function setQty(id, qty) {
    if (qty < 1) { removeItem(id); return; }
    const cart = getCart();
    const item = cart.find(i => i.id === id);
    if (item) item.qty = qty;
    saveCart(cart);
    updateBadge();
    renderDrawer();
  }

  // ── UI helpers ────────────────────────────────────────
  function updateBadge() {
    const n = getCount();
    document.querySelectorAll('.cart-badge').forEach(b => {
      b.textContent = n;
      b.style.display = n > 0 ? 'flex' : 'none';
    });
  }

  function openDrawer() {
    document.getElementById('cart-drawer')?.classList.add('open');
    document.getElementById('cart-overlay')?.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeDrawer() {
    document.getElementById('cart-drawer')?.classList.remove('open');
    document.getElementById('cart-overlay')?.classList.remove('open');
    document.body.style.overflow = '';
  }

  function isRtl() { return document.body.classList.contains('rtl'); }

  function renderDrawer() {
    const list = document.getElementById('cart-items');
    const footer = document.getElementById('cart-footer');
    if (!list) return;
    const cart = getCart();
    const rtl = isRtl();

    if (cart.length === 0) {
      list.innerHTML = `<div class="cart-empty">${rtl ? 'הסל ריק' : 'Your cart is empty'}</div>`;
      if (footer) footer.style.display = 'none';
      return;
    }
    if (footer) footer.style.display = '';

    list.innerHTML = cart.map(item => `
      <div class="cart-item" data-id="${item.id}">
        <img src="${item.img}" alt="${item.name}" class="cart-item-img" />
        <div class="cart-item-info">
          <div class="cart-item-name">${item.name}</div>
          <div class="cart-item-variant mono-el">${item.variant || ''}</div>
          <div class="cart-item-price">${item.price * item.qty} ₪</div>
        </div>
        <div class="cart-item-qty">
          <button class="cart-qty-btn" data-action="dec" data-id="${item.id}">−</button>
          <span>${item.qty}</span>
          <button class="cart-qty-btn" data-action="inc" data-id="${item.id}">+</button>
        </div>
        <button class="cart-remove" data-id="${item.id}" aria-label="הסר">✕</button>
      </div>
    `).join('');

    document.getElementById('cart-total-price').textContent = getTotal() + ' ₪';

    // events
    list.querySelectorAll('.cart-qty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        const item = getCart().find(i => i.id === id);
        if (!item) return;
        setQty(id, item.qty + (btn.dataset.action === 'inc' ? 1 : -1));
      });
    });
    list.querySelectorAll('.cart-remove').forEach(btn => {
      btn.addEventListener('click', () => removeItem(btn.dataset.id));
    });
  }

  // ── Inject HTML ───────────────────────────────────────
  function injectCartHTML() {
    // Cart icon in nav
    const navRight = document.querySelector('.nav-right');
    if (navRight) {
      const btn = document.createElement('button');
      btn.className = 'cart-nav-btn';
      btn.setAttribute('aria-label', 'סל קניות');
      btn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
          <line x1="3" y1="6" x2="21" y2="6"/>
          <path d="M16 10a4 4 0 01-8 0"/>
        </svg>
        <span class="cart-badge" style="display:none">0</span>`;
      btn.addEventListener('click', openDrawer);
      navRight.insertBefore(btn, navRight.firstChild);
    }

    // Overlay
    const overlay = document.createElement('div');
    overlay.id = 'cart-overlay';
    overlay.addEventListener('click', closeDrawer);

    // Drawer
    const drawer = document.createElement('div');
    drawer.id = 'cart-drawer';
    drawer.innerHTML = `
      <div class="cart-header">
        <span class="cart-title mono-el">הסל שלי</span>
        <button class="cart-close" id="cart-close-btn">✕</button>
      </div>
      <div class="cart-items" id="cart-items"></div>
      <div class="cart-footer" id="cart-footer" style="display:none">
        <div class="cart-total">
          <span class="mono-el">סה"כ</span>
          <span id="cart-total-price">0 ₪</span>
        </div>
        <div class="cart-shipping-note mono-el">משלוח 30 ₪ יתווסף בתשלום</div>
        <a href="/pages/checkout.html" class="btn-cart-checkout" id="cart-checkout-btn">לתשלום →</a>
      </div>`;

    document.body.appendChild(overlay);
    document.body.appendChild(drawer);

    document.getElementById('cart-close-btn').addEventListener('click', closeDrawer);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });
  }

  function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      /* Cart nav button */
      .cart-nav-btn {
        position: relative;
        background: none;
        border: none;
        cursor: none;
        color: var(--white, #fff);
        padding: 4px;
        display: flex;
        align-items: center;
        margin-left: 4px;
        transition: color 0.2s;
      }
      .cart-nav-btn:hover { color: var(--teal, #6AEBD6); }
      .cart-badge {
        position: absolute;
        top: -4px;
        right: -6px;
        background: var(--teal, #6AEBD6);
        color: #060606;
        font-family: 'Space Mono', monospace;
        font-size: 9px;
        font-weight: 700;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        align-items: center;
        justify-content: center;
        line-height: 1;
      }

      /* Overlay */
      #cart-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.6);
        z-index: 1100;
      }
      #cart-overlay.open { display: block; }

      /* Drawer */
      #cart-drawer {
        position: fixed;
        top: 0;
        right: -420px;
        width: min(420px, 100vw);
        height: 100dvh;
        background: #0a0a0a;
        border-left: 1px solid #1a1a1a;
        z-index: 1200;
        display: flex;
        flex-direction: column;
        transition: right 0.35s cubic-bezier(.4,0,.2,1);
      }
      #cart-drawer.open { right: 0; }

      .cart-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 24px 24px 20px;
        border-bottom: 1px solid #1a1a1a;
        flex-shrink: 0;
      }
      .cart-title {
        font-size: 11px;
        letter-spacing: 0.12em;
        color: var(--teal, #6AEBD6);
        text-transform: uppercase;
      }
      .cart-close {
        background: none;
        border: none;
        color: #555;
        font-size: 16px;
        cursor: pointer;
        padding: 4px 8px;
        line-height: 1;
        transition: color 0.2s;
      }
      .cart-close:hover { color: #fff; }

      .cart-items {
        flex: 1;
        overflow-y: auto;
        padding: 8px 0;
      }

      .cart-empty {
        padding: 60px 24px;
        text-align: center;
        font-size: 14px;
        color: #444;
        font-family: 'IBM Plex Sans Hebrew', sans-serif;
      }

      .cart-item {
        display: grid;
        grid-template-columns: 72px 1fr auto auto;
        gap: 0 14px;
        align-items: center;
        padding: 16px 24px;
        border-bottom: 1px solid #111;
      }
      .cart-item-img {
        width: 72px;
        height: 72px;
        object-fit: cover;
        background: #111;
      }
      .cart-item-info { min-width: 0; }
      .cart-item-name {
        font-size: 13px;
        font-weight: 700;
        color: #fff;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .cart-item-variant {
        font-size: 10px;
        letter-spacing: 0.06em;
        color: #444;
        margin-top: 3px;
        text-transform: uppercase;
      }
      .cart-item-price {
        font-size: 14px;
        font-weight: 700;
        color: var(--teal, #6AEBD6);
        margin-top: 6px;
      }

      .cart-item-qty {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #fff;
      }
      .cart-qty-btn {
        background: #1a1a1a;
        border: none;
        color: #fff;
        width: 24px;
        height: 24px;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
        transition: background 0.15s;
      }
      .cart-qty-btn:hover { background: #6AEBD6; color: #060606; }

      .cart-remove {
        background: none;
        border: none;
        color: #333;
        font-size: 13px;
        cursor: pointer;
        padding: 4px;
        transition: color 0.2s;
        align-self: flex-start;
        margin-top: 4px;
      }
      .cart-remove:hover { color: #ff4444; }

      .cart-footer {
        border-top: 1px solid #1a1a1a;
        padding: 20px 24px 32px;
        flex-shrink: 0;
        background: #0a0a0a;
      }
      .cart-total {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 15px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 6px;
      }
      .cart-total .mono-el {
        font-size: 11px;
        letter-spacing: 0.08em;
        color: #555;
        font-weight: 400;
      }
      .cart-shipping-note {
        font-size: 10px;
        letter-spacing: 0.06em;
        color: #333;
        text-transform: uppercase;
        margin-bottom: 20px;
      }
      .btn-cart-checkout {
        display: block;
        width: 100%;
        padding: 15px;
        background: var(--teal, #6AEBD6);
        color: #060606;
        font-family: 'Space Grotesk', 'IBM Plex Sans Hebrew', sans-serif;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        text-align: center;
        text-decoration: none;
        transition: opacity 0.2s;
        box-sizing: border-box;
      }
      .btn-cart-checkout:hover { opacity: 0.88; }
    `;
    document.head.appendChild(style);
  }

  // ── Fix checkout link based on page depth ─────────────
  function fixCheckoutLink() {
    const isRoot = !location.pathname.includes('/pages/');
    const link = document.getElementById('cart-checkout-btn');
    if (link) link.href = isRoot ? 'pages/checkout.html' : 'checkout.html';
  }

  // ── Init ──────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    injectStyles();
    injectCartHTML();
    fixCheckoutLink();
    updateBadge();
    renderDrawer();
  });

  // ── Public API ────────────────────────────────────────
  window.VayoCart = { add: addItem, open: openDrawer, close: closeDrawer };
})();
