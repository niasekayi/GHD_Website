/* Good Hair Daye — Shop Cart & Checkout */

const Shop = (() => {
  const CART_KEY = 'ghd_shop_cart';

  const state = {
    cart: [],            // [{key, id, name, price, image, stock, qty, optionValueIds, selectionsText}]
    modalProduct: null,  // currently open product-detail modal dataset
    modalOptions: [],    // [{id, name, values: [{id, label, price_delta}]}]
    modalGallery: [],    // [{id, url, option_value_id}]
    modalVariants: [],   // [{value_ids: [int,...], price: float}]
    modalSelections: {}, // {groupId: valueId}
    checkoutStep: 1,      // 1=info, 2=review+pay, 3=confirmation
    customer: {},
    confirmation: null,
  };

  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  function escHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function money(n) {
    return `$${Number(n).toFixed(2)}`;
  }

  function notify(msg) {
    let el = document.getElementById('shop-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'shop-toast';
      el.style.cssText = 'position:fixed;bottom:2rem;left:50%;transform:translateX(-50%);background:var(--color-dark);color:#fff;padding:0.75rem 1.5rem;border-radius:4px;font-size:0.85rem;z-index:2000;opacity:0;transition:opacity 0.25s;pointer-events:none;';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.opacity = '1';
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.style.opacity = '0'; }, 1800);
  }

  // ── Cart persistence ─────────────────────────────────────────
  function loadCart() {
    try {
      const raw = localStorage.getItem(CART_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      state.cart = Array.isArray(parsed) ? parsed : [];
      // Normalize carts saved before per-option line items existed.
      state.cart.forEach(item => {
        if (!item.optionValueIds) item.optionValueIds = [];
        if (!item.key) item.key = _lineKey(item.id, item.optionValueIds);
        if (item.selectionsText === undefined) item.selectionsText = '';
      });
    } catch (e) {
      state.cart = [];
    }
  }

  function saveCart() {
    try { localStorage.setItem(CART_KEY, JSON.stringify(state.cart)); } catch (e) { /* storage unavailable */ }
  }

  function cartSubtotal() {
    return state.cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  }

  function cartCount() {
    return state.cart.reduce((sum, item) => sum + item.qty, 0);
  }

  function renderCartBadge() {
    const badge = document.getElementById('cart-fab-badge');
    if (!badge) return;
    const count = cartCount();
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  }

  // ── Card quantity stepper ────────────────────────────────────
  function stepCardQty(btn, delta) {
    const wrap = btn.closest('.shop-qty-stepper');
    const input = wrap.querySelector('.shop-qty-input');
    const max = parseInt(input.max || '999', 10);
    let val = parseInt(input.value || '1', 10) + delta;
    if (val < 1) val = 1;
    if (val > max) val = max;
    input.value = val;
  }

  function addToCartFromCard(cardEl) {
    const qtyInput = cardEl.querySelector('.shop-qty-input');
    const qty = Math.max(1, parseInt(qtyInput.value || '1', 10));
    const d = cardEl.dataset;
    addToCart(d, qty, [], '', parseFloat(d.price), d.image);
  }

  // ── Product detail modal ─────────────────────────────────────
  function _setModalImage(url) {
    const img = document.getElementById('shop-modal-img');
    const placeholder = document.getElementById('shop-modal-img-placeholder');
    if (url) {
      img.src = url;
      img.style.display = '';
      placeholder.style.display = 'none';
    } else {
      img.style.display = 'none';
      placeholder.style.display = '';
    }
  }

  function _renderModalGallery(d) {
    const wrap = document.getElementById('shop-modal-gallery');
    const gallery = state.modalGallery || [];
    const thumbs = [];
    if (d.image) thumbs.push(d.image);
    gallery.forEach(g => { if (g.url && !thumbs.includes(g.url)) thumbs.push(g.url); });

    if (thumbs.length < 2) {
      wrap.style.display = 'none';
      wrap.innerHTML = '';
      return;
    }
    wrap.style.display = 'flex';
    wrap.innerHTML = thumbs.map(url => `
      <img class="shop-modal-gallery-thumb${url === d.image ? ' active' : ''}"
           src="${escHtml(url)}" onclick="Shop._pickGalleryImage('${escHtml(url)}', this)" />`).join('');
  }

  function _pickGalleryImage(url, thumbEl) {
    _setModalImage(url);
    document.querySelectorAll('.shop-modal-gallery-thumb').forEach(el => el.classList.remove('active'));
    if (thumbEl) thumbEl.classList.add('active');
  }

  function _renderModalOptions() {
    const wrap = document.getElementById('shop-modal-options');
    const groups = state.modalOptions || [];
    if (groups.length === 0) {
      wrap.innerHTML = '';
      return;
    }
    wrap.innerHTML = groups.map(g => `
      <div class="shop-opt-group">
        <label class="shop-opt-label">${escHtml(g.name)}</label>
        <select class="shop-opt-select" onchange="Shop._onOptionChange(${g.id}, this.value)">
          <option value="">Choose an option</option>
          ${g.values.map(v => `<option value="${v.id}">${escHtml(v.label)}${g.contributes_to_price && v.price_delta ? ` (${v.price_delta > 0 ? '+' : '−'}$${Math.abs(v.price_delta).toFixed(2)})` : ''}</option>`).join('')}
        </select>
      </div>`).join('');
  }

  function _onOptionChange(groupId, valueId) {
    if (valueId) state.modalSelections[groupId] = parseInt(valueId, 10);
    else delete state.modalSelections[groupId];

    const group = (state.modalOptions || []).find(g => g.id === groupId);
    const value = group ? group.values.find(v => v.id === parseInt(valueId, 10)) : null;
    if (value) {
      const linkedImg = (state.modalGallery || []).find(img => img.option_value_id === value.id);
      if (linkedImg) _pickGalleryImage(linkedImg.url, [...document.querySelectorAll('.shop-modal-gallery-thumb')].find(el => el.src === linkedImg.url));
    }

    document.getElementById('shop-modal-options-error').style.display = 'none';
    _updateModalPrice();
  }

  function _resolvePrice() {
    const d = state.modalProduct;
    if (!d) return null;
    const groups = state.modalOptions || [];

    if (groups.length === 0) return parseFloat(d.price);

    const priceGroups = groups.filter(g => g.contributes_to_price);

    // No groups contribute to price — product has a fixed base price
    if (priceGroups.length === 0) return parseFloat(d.price);

    // Collect all selected value IDs (for variant lookup)
    const allSelectedIds = [];
    for (const g of groups) {
      const selectedId = state.modalSelections[g.id];
      if (selectedId) allSelectedIds.push(selectedId);
    }

    // Return null until every price-contributing group has a selection
    for (const g of priceGroups) {
      if (!state.modalSelections[g.id]) return null;
    }

    // Check for an exact variant price override (uses all selected options)
    if (allSelectedIds.length > 0) {
      const sortedKey = [...allSelectedIds].sort((a, b) => a - b).join(',');
      const match = (state.modalVariants || []).find(vv =>
        [...vv.value_ids].sort((a, b) => a - b).join(',') === sortedKey
      );
      if (match) return match.price;
    }

    // Fall back to base price + deltas from price-contributing groups only
    let price = parseFloat(d.price);
    for (const g of priceGroups) {
      const selectedId = state.modalSelections[g.id];
      const v = g.values.find(v => v.id === selectedId);
      if (v) price += v.price_delta;
    }
    return price;
  }

  function _updateModalPrice() {
    const price = _resolvePrice();
    const el = document.getElementById('shop-modal-price');
    if (price === null) {
      el.textContent = 'Select a length to see price';
      el.style.fontSize = '0.85rem';
      el.style.color = 'var(--color-mid)';
    } else {
      el.textContent = money(price);
      el.style.fontSize = '';
      el.style.color = '';
    }
  }

  function openProductModal(cardEl) {
    const d = cardEl.dataset;
    state.modalProduct = d;
    state.modalOptions   = JSON.parse(d.options   || '[]');
    state.modalGallery   = JSON.parse(d.gallery   || '[]');
    state.modalVariants  = JSON.parse(d.variants  || '[]');
    state.modalSelections = {};

    document.getElementById('shop-modal-category').textContent = d.category;
    document.getElementById('shop-modal-name').textContent = d.name;
    document.getElementById('shop-modal-description').textContent = d.description || 'No description available.';
    const stock = parseInt(d.stock, 10);
    document.getElementById('shop-modal-stock').textContent = stock > 0 ? `${stock} in stock` : 'Out of stock';

    _setModalImage(d.image);
    _renderModalGallery(d);
    _renderModalOptions();
    _updateModalPrice();

    const qtyInput = document.getElementById('shop-modal-qty');
    qtyInput.value = 1;
    qtyInput.max = stock;

    document.getElementById('shop-modal-options-error').style.display = 'none';

    const addBtn = document.getElementById('shop-modal-add-btn');
    addBtn.disabled = stock === 0;
    addBtn.textContent = stock > 0 ? 'Add to Cart' : 'Out of Stock';

    document.getElementById('shop-modal-overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeProductModal() {
    const overlay = document.getElementById('shop-modal-overlay');
    if (overlay) overlay.classList.remove('open');
    if (!document.querySelector('.shop-overlay.open')) document.body.style.overflow = '';
  }

  function stepModalQty(delta) {
    const input = document.getElementById('shop-modal-qty');
    const max = parseInt(input.max || '999', 10);
    let val = parseInt(input.value || '1', 10) + delta;
    if (val < 1) val = 1;
    if (val > max) val = max;
    input.value = val;
  }

  function addToCartFromModal() {
    if (!state.modalProduct) return;
    const d = state.modalProduct;
    const groups = state.modalOptions || [];

    const missing = groups.find(g => !state.modalSelections[g.id]);
    if (missing) {
      const errEl = document.getElementById('shop-modal-options-error');
      errEl.textContent = `Please choose a ${missing.name}.`;
      errEl.style.display = 'block';
      return;
    }

    const optionValueIds = [];
    const selectionLabels = [];
    groups.forEach(g => {
      const valueId = state.modalSelections[g.id];
      const v = g.values.find(v => v.id === valueId);
      if (v) {
        optionValueIds.push(v.id);
        selectionLabels.push(`${g.name}: ${v.label}`);
      }
    });
    const price = _resolvePrice();

    const qty = Math.max(1, parseInt(document.getElementById('shop-modal-qty').value || '1', 10));
    const imgEl = document.getElementById('shop-modal-img');
    const displayImage = imgEl.style.display !== 'none' ? imgEl.src : (d.image || '');

    addToCart(d, qty, optionValueIds, selectionLabels.join(', '), price, displayImage);
    closeProductModal();
  }

  // ── Cart mutations ───────────────────────────────────────────
  function _lineKey(id, optionValueIds) {
    return `${id}::${[...optionValueIds].sort((a, b) => a - b).join(',')}`;
  }

  function addToCart(d, qty, optionValueIds, selectionsText, unitPrice, displayImage) {
    optionValueIds = optionValueIds || [];
    const id = parseInt(d.id, 10);
    const stock = parseInt(d.stock, 10);
    if (stock <= 0) return;

    const key = _lineKey(id, optionValueIds);
    const existing = state.cart.find(i => i.key === key);
    if (existing) {
      existing.qty = Math.min(stock, existing.qty + qty);
    } else {
      state.cart.push({
        key,
        id,
        name: d.name,
        price: unitPrice,
        image: displayImage || d.image || '',
        stock,
        qty: Math.min(stock, qty),
        optionValueIds,
        selectionsText: selectionsText || '',
      });
    }
    saveCart();
    renderCartBadge();
    notify(`Added ${escHtml(d.name)} to cart`);
  }

  function updateQty(key, delta) {
    const item = state.cart.find(i => i.key === key);
    if (!item) return;
    item.qty = Math.max(1, Math.min(item.stock, item.qty + delta));
    saveCart();
    renderCart();
    renderCartBadge();
  }

  function removeFromCart(key) {
    state.cart = state.cart.filter(i => i.key !== key);
    saveCart();
    renderCart();
    renderCartBadge();
  }

  function clearCart() {
    if (state.cart.length === 0) return;
    if (!confirm('Remove all items from your cart?')) return;
    state.cart = [];
    saveCart();
    renderCart();
    renderCartBadge();
  }

  // ── Cart modal ────────────────────────────────────────────────
  function openCart() {
    renderCart();
    document.getElementById('cart-overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeCart() {
    document.getElementById('cart-overlay').classList.remove('open');
    if (!document.querySelector('.shop-overlay.open')) document.body.style.overflow = '';
  }

  function renderCart() {
    const list = document.getElementById('cart-items-list');
    const emptyMsg = document.getElementById('cart-empty-msg');
    const checkoutBtn = document.getElementById('cart-checkout-btn');

    if (state.cart.length === 0) {
      list.innerHTML = '';
      emptyMsg.style.display = 'block';
      checkoutBtn.disabled = true;
      checkoutBtn.style.opacity = '0.5';
    } else {
      emptyMsg.style.display = 'none';
      checkoutBtn.disabled = false;
      checkoutBtn.style.opacity = '';
      list.innerHTML = state.cart.map(item => `
        <div class="cart-item-row">
          ${item.image
            ? `<img class="cart-item-img" src="${escHtml(item.image)}" alt="" />`
            : `<div class="cart-item-img-placeholder"><i class="fas fa-box"></i></div>`}
          <div>
            <div class="cart-item-name">${escHtml(item.name)}</div>
            ${item.selectionsText ? `<div style="font-size:0.7rem;color:var(--color-mid);margin-bottom:0.15rem;">${escHtml(item.selectionsText)}</div>` : ''}
            <div class="cart-item-price">${money(item.price)} each &middot; ${money(item.price * item.qty)} total</div>
            <button class="cart-item-remove" onclick="Shop.removeFromCart('${item.key}')">Remove</button>
          </div>
          <div class="cart-item-actions">
            <div class="shop-qty-stepper">
              <button type="button" onclick="Shop.updateQty('${item.key}', -1)">−</button>
              <span style="width:32px;text-align:center;display:inline-block;font-size:0.85rem;">${item.qty}</span>
              <button type="button" onclick="Shop.updateQty('${item.key}', 1)" ${item.qty >= item.stock ? 'disabled' : ''}>+</button>
            </div>
          </div>
        </div>`).join('');
    }

    const subtotal = cartSubtotal();
    document.getElementById('cart-subtotal').textContent = money(subtotal);
    document.getElementById('cart-total').textContent = money(subtotal);
  }

  // ── Checkout modal ───────────────────────────────────────────
  function openCheckout() {
    if (state.cart.length === 0) return;
    closeCart();
    state.checkoutStep = 1;
    renderCheckout();
    document.getElementById('checkout-overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeCheckout() {
    document.getElementById('checkout-overlay').classList.remove('open');
    if (!document.querySelector('.shop-overlay.open')) document.body.style.overflow = '';
  }

  function renderCheckout() {
    const body = document.getElementById('checkout-body');
    if (state.checkoutStep === 1) body.innerHTML = renderCheckoutInfo();
    else if (state.checkoutStep === 2) renderCheckoutReview(body);
    else body.innerHTML = renderCheckoutConfirmation();
  }

  function renderCheckoutInfo() {
    const c = state.customer;
    return `
      <div class="bk-step-content">
        <h2 class="bk-title">Shipping & Contact Info</h2>
        <p class="bk-subtitle">We'll use this to ship your order and confirm via email.</p>
        <div class="bk-form">
          <label class="bk-label">Full Name <span class="bk-req">*</span>
            <input class="bk-input" type="text" id="co-name" value="${escHtml(c.name)}" placeholder="First and last name" />
          </label>
          <label class="bk-label">Email Address <span class="bk-req">*</span>
            <input class="bk-input" type="email" id="co-email" value="${escHtml(c.email)}" placeholder="you@example.com" />
          </label>
          <label class="bk-label">Phone Number <span class="bk-req">*</span>
            <input class="bk-input" type="tel" id="co-phone" value="${escHtml(c.phone)}" placeholder="(202) 555-0100" />
          </label>
          <label class="bk-label">Address Line 1 <span class="bk-req">*</span>
            <input class="bk-input" type="text" id="co-addr1" value="${escHtml(c.address1)}" placeholder="Street address" />
          </label>
          <label class="bk-label">Address Line 2 <span class="bk-optional">(optional)</span>
            <input class="bk-input" type="text" id="co-addr2" value="${escHtml(c.address2)}" placeholder="Apt, suite, unit" />
          </label>
          <label class="bk-label">City <span class="bk-req">*</span>
            <input class="bk-input" type="text" id="co-city" value="${escHtml(c.city)}" />
          </label>
          <label class="bk-label">State <span class="bk-req">*</span>
            <input class="bk-input" type="text" id="co-state" value="${escHtml(c.state)}" placeholder="DC" />
          </label>
          <label class="bk-label">ZIP Code <span class="bk-req">*</span>
            <input class="bk-input" type="text" id="co-zip" value="${escHtml(c.zip)}" />
          </label>
        </div>
        <p id="co-info-error" class="bk-error" style="display:none;"></p>
        <div class="bk-nav">
          <button class="bk-btn-ghost" onclick="Shop.closeCheckout()">Cancel</button>
          <button class="bk-btn-primary" onclick="Shop.continueToReview()">Next: Review &amp; Pay →</button>
        </div>
      </div>`;
  }

  function continueToReview() {
    const name = document.getElementById('co-name').value.trim();
    const email = document.getElementById('co-email').value.trim();
    const phone = document.getElementById('co-phone').value.trim();
    const address1 = document.getElementById('co-addr1').value.trim();
    const address2 = document.getElementById('co-addr2').value.trim();
    const city = document.getElementById('co-city').value.trim();
    const stateVal = document.getElementById('co-state').value.trim();
    const zip = document.getElementById('co-zip').value.trim();
    const err = document.getElementById('co-info-error');

    if (!name || !email || !phone || !address1 || !city || !stateVal || !zip) {
      err.textContent = 'Please fill in all required fields.';
      err.style.display = 'block';
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      err.textContent = 'Please enter a valid email address.';
      err.style.display = 'block';
      return;
    }

    state.customer = { name, email, phone, address1, address2, city, state: stateVal, zip };
    state.checkoutStep = 2;
    renderCheckout();
  }

  function renderCheckoutReview(container) {
    const subtotal = cartSubtotal();
    const itemRows = state.cart.map(item => `
      <div class="checkout-review-row">
        <span>${escHtml(item.name)}${item.selectionsText ? ` <span style="color:var(--color-mid);font-size:0.78rem;">(${escHtml(item.selectionsText)})</span>` : ''} &times; ${item.qty}</span>
        <span>${money(item.price * item.qty)}</span>
      </div>`).join('');

    container.innerHTML = `
      <div class="bk-step-content">
        <h2 class="bk-title">Review &amp; Pay</h2>
        <div class="checkout-review-card">
          ${itemRows}
          <div class="checkout-review-row total">
            <span>Total</span>
            <span>${money(subtotal)}</span>
          </div>
        </div>
        <p id="checkout-review-error" class="bk-error" style="display:none;"></p>
        <div class="bk-nav" style="margin-bottom:0.5rem;">
          <button class="bk-btn-ghost" onclick="Shop.backToInfo()">← Back</button>
        </div>
        <div id="checkout-paypal-btn-container"></div>
      </div>`;

    _mountPayPalButtons();
  }

  function backToInfo() {
    state.checkoutStep = 1;
    renderCheckout();
  }

  function _mountPayPalButtons() {
    const container = document.getElementById('checkout-paypal-btn-container');
    if (!container) return;

    if (!window.paypal) {
      container.innerHTML = '<p style="color:var(--color-dark);font-size:0.8rem;padding:0.5rem 0;">PayPal failed to load. Please refresh the page and try again.</p>';
      return;
    }

    container.innerHTML = '';

    window.paypal.Buttons({
      style: { layout: 'vertical', color: 'gold', shape: 'rect', label: 'pay', height: 45 },

      createOrder() {
        const errEl = document.getElementById('checkout-review-error');
        if (errEl) errEl.style.display = 'none';
        return fetch('/shop/api/create-paypal-order/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
          body: JSON.stringify({ items: state.cart.map(i => ({ id: i.id, qty: i.qty, option_value_ids: i.optionValueIds || [] })) }),
        })
          .then(r => r.json())
          .then(d => {
            if (d.error) throw new Error(d.error);
            return d.order_id;
          });
      },

      onApprove(data) {
        return _completeCheckout(data.orderID);
      },

      onError() {
        const errEl = document.getElementById('checkout-review-error');
        if (errEl) { errEl.textContent = 'Payment failed. Please try again or use a different payment method.'; errEl.style.display = 'block'; }
      },

      onCancel() {
        const errEl = document.getElementById('checkout-review-error');
        if (errEl) { errEl.textContent = 'Payment cancelled — your order has not been placed.'; errEl.style.display = 'block'; }
      },
    }).render('#checkout-paypal-btn-container');
  }

  async function _completeCheckout(paypalOrderId) {
    const errEl = document.getElementById('checkout-review-error');
    const container = document.getElementById('checkout-paypal-btn-container');
    if (container) container.innerHTML = '<p style="text-align:center;font-size:0.85rem;color:var(--color-dark);padding:1rem 0;">Confirming your order…</p>';

    try {
      const c = state.customer;
      const res = await fetch('/shop/api/capture-order/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify({
          paypal_order_id: paypalOrderId,
          items: state.cart.map(i => ({ id: i.id, qty: i.qty, option_value_ids: i.optionValueIds || [] })),
          customer_name: c.name,
          customer_email: c.email,
          customer_phone: c.phone,
          shipping_address_line1: c.address1,
          shipping_address_line2: c.address2,
          shipping_city: c.city,
          shipping_state: c.state,
          shipping_zip: c.zip,
        }),
      });
      const data = await res.json();

      if (data.success) {
        state.confirmation = data;
        state.cart = [];
        saveCart();
        renderCartBadge();
        state.checkoutStep = 3;
        renderCheckout();
      } else {
        if (errEl) { errEl.textContent = data.error || 'Something went wrong after payment. Please contact us immediately with your PayPal confirmation.'; errEl.style.display = 'block'; }
        if (container) container.innerHTML = '';
        _mountPayPalButtons();
      }
    } catch (e) {
      if (errEl) { errEl.textContent = 'Network error after payment. Please contact us with your PayPal confirmation to verify your order.'; errEl.style.display = 'block'; }
      if (container) container.innerHTML = '';
      _mountPayPalButtons();
    }
  }

  function renderCheckoutConfirmation() {
    const c = state.confirmation || {};
    return `
      <div class="bk-step-content">
        <div class="bk-confirm-icon">✓</div>
        <h2 class="bk-title">Order Confirmed!</h2>
        <p class="bk-subtitle">Thank you for your order — a confirmation has been sent to <strong>${escHtml(c.customer_email || '')}</strong>.</p>
        <div class="checkout-review-card">
          <div class="checkout-review-row">
            <span>Order Number</span>
            <span>${escHtml(c.order_number || '')}</span>
          </div>
          <div class="checkout-review-row total">
            <span>Total Paid</span>
            <span>${money(c.total || 0)}</span>
          </div>
        </div>
        <button class="bk-btn-primary w-full mt-6" onclick="Shop.closeCheckout(); location.reload();">Continue Shopping</button>
      </div>`;
  }

  // ── Init ──────────────────────────────────────────────────────
  function _init() {
    loadCart();
    renderCartBadge();

    ['shop-modal-overlay', 'cart-overlay'].forEach(id => {
      const overlay = document.getElementById(id);
      if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('open'); });
    });
  }

  document.addEventListener('DOMContentLoaded', _init);

  // ── Public API ──────────────────────────────────────────────
  return {
    openProductModal, closeProductModal, stepModalQty, addToCartFromModal,
    stepCardQty, addToCartFromCard,
    updateQty, removeFromCart, clearCart,
    openCart, closeCart,
    openCheckout, closeCheckout, continueToReview, backToInfo,
    _onOptionChange, _pickGalleryImage,
  };
})();
