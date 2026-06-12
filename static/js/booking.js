/* Good Hair Daye — Booking Modal */

const Booking = (() => {
  const state = {
    step: 1,
    isNewClient: null,
    selectedServiceId: null,
    selectedService: null,
    selectedAddons: [],       // [{id, name, duration, price}]
    selectedDate: null,
    selectedTime: null,       // "HH:MM" 24h string sent to API
    selectedTimeLabel: null,  // "9:30 AM" display string
    clientName: '',
    clientEmail: '',
    clientPhone: '',
    clientNotes: '',
    cancellationAcknowledged: false,
    servicesData: null,
    availabilityData: null,
    availabilityCache: {},    // keyed by "service_id:addon_ids"
    preselectedServiceId: null,
    confirmation: null,
    calendarYear: null,
    calendarMonth: null,
  };

  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  function fmt(dateStr) {
    const [y, m, d] = dateStr.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString('en-US', {
      weekday: 'long', month: 'long', day: 'numeric'
    });
  }

  function escHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Open / Close ────────────────────────────────────────────
  function open(preServiceId) {
    state.step = 1;
    state.isNewClient = null;
    state.selectedServiceId = preServiceId || null;
    state.selectedService = null;
    state.selectedAddons = [];
    state.selectedDate = null;
    state.selectedTime = null;
    state.selectedTimeLabel = null;
    state.clientName = '';
    state.clientEmail = '';
    state.clientPhone = '';
    state.clientNotes = '';
    state.cancellationAcknowledged = false;
    state.confirmation = null;
    state.preselectedServiceId = preServiceId || null;
    state.availabilityData = null;
    state.availabilityCache = {};
    state.calendarYear = null;
    state.calendarMonth = null;

    document.getElementById('bk-overlay').style.display = 'flex';
    document.body.style.overflow = 'hidden';
    render();
  }

  function close() {
    document.getElementById('bk-overlay').style.display = 'none';
    document.body.style.overflow = '';
  }

  function goTo(step) {
    state.step = step;
    render();
    document.getElementById('bk-body').scrollTop = 0;
  }

  // ── Data fetching ───────────────────────────────────────────
  async function loadServices() {
    if (state.servicesData) return;
    try {
      const res = await fetch('/book/api/services/');
      const json = await res.json();
      state.servicesData = json.categories || [];
    } catch (e) {
      state.servicesData = [];
    }
  }

  async function loadAvailability() {
    const addonKey = state.selectedAddons.map(a => a.id).join(',');
    const serviceKey = state.selectedServiceId ? String(state.selectedServiceId) : 'consultation';
    const cacheKey = serviceKey + (addonKey ? ':' + addonKey : '');

    if (state.availabilityCache[cacheKey]) {
      state.availabilityData = state.availabilityCache[cacheKey];
      return;
    }
    try {
      const qs = new URLSearchParams();
      if (state.selectedServiceId) qs.set('service_id', state.selectedServiceId);
      if (addonKey) qs.set('addon_ids', addonKey);
      const res = await fetch(`/book/api/availability/?${qs}`);
      const json = await res.json();
      state.availabilityCache[cacheKey] = json;
      state.availabilityData = json;
    } catch (e) {
      state.availabilityData = { dates: [], same_day_fee: '75.00', same_day_fee_enabled: true, today: '' };
    }
  }

  // ── Main render ─────────────────────────────────────────────
  function render() {
    updateStepIndicator();
    const body = document.getElementById('bk-body');
    switch (state.step) {
      case 1: body.innerHTML = renderStep1(); break;
      case 2: renderStep2(body); break;
      case 3: renderStep3(body); break;
      case 4: renderStep4(body); break;
      case 5: body.innerHTML = renderStep5(); break;
      case 6: body.innerHTML = renderStep6(); break;
      case 7: body.innerHTML = renderStep7(); break;
      case 8: body.innerHTML = renderStep8(); break;
    }
  }

  function updateStepIndicator() {
    const total = 7;
    const indicators = document.querySelectorAll('.bk-step-dot');
    indicators.forEach((dot, i) => {
      dot.classList.toggle('active', i + 1 === state.step);
      dot.classList.toggle('done', i + 1 < state.step);
    });
    const label = document.getElementById('bk-step-label');
    const labels = ['Client Type', 'Service', 'Add-Ons', 'Date', 'Time', 'Your Info', 'Review'];
    if (label && state.step <= total) label.textContent = labels[state.step - 1];
    if (state.step === 8 && label) label.textContent = 'Confirmed';
  }

  // ── Step 1: New or returning ────────────────────────────────
  function renderStep1() {
    return `
      <div class="bk-step-content">
        <h2 class="bk-title">Welcome to Good Hair Daye</h2>
        <p class="bk-subtitle">Have you visited us before?</p>
        <div class="bk-client-choice">
          <button class="bk-choice-btn" onclick="Booking.handleClientType(false)">
            <span class="bk-choice-icon">✦</span>
            <span class="bk-choice-label">Returning Client</span>
            <span class="bk-choice-sub">I've booked with Dommi before</span>
          </button>
          <button class="bk-choice-btn" onclick="Booking.handleClientType(true)">
            <span class="bk-choice-icon">✦</span>
            <span class="bk-choice-label">New Client</span>
            <span class="bk-choice-sub">First time visiting Good Hair Daye</span>
          </button>
        </div>
      </div>`;
  }

  function handleClientType(isNew) {
    state.isNewClient = isNew;
    if (isNew) {
      // New clients must book a consultation first — skip add-ons step
      state.selectedServiceId = null;
      state.selectedAddons = [];
      state.selectedService = { name: 'Consultation', price: '$40', duration: '30 min', deposit: '40.00', id: null };
      goTo(2);
      loadAvailability();
    } else if (state.preselectedServiceId) {
      // Coming from services page — skip service selection, go to add-ons
      loadServices().then(() => {
        for (const cat of (state.servicesData || [])) {
          const found = cat.services.find(s => s.id == state.preselectedServiceId);
          if (found) {
            state.selectedService = found;
            state.selectedServiceId = found.id;
            break;
          }
        }
        state.availabilityData = null;
        goTo(3);
      });
    } else {
      goTo(2);
      loadServices();
    }
  }

  // ── Step 2: Consultation info (new) or service list (returning) ─
  function renderStep2(container) {
    if (state.isNewClient) {
      container.innerHTML = `
        <div class="bk-step-content">
          <h2 class="bk-title">First, Let's Meet</h2>
          <p class="bk-subtitle">All new clients are required to start with a consultation before booking any service.</p>

          <div class="bk-consult-card">
            <div class="bk-consult-header">
              <span class="bk-consult-tag">Required for New Clients</span>
            </div>
            <div class="bk-consult-body">
              <h3 class="bk-consult-name">Consultation</h3>
              <p class="bk-consult-desc">A one-on-one session to discuss your hair goals, history, texture, and any concerns — so every service can be tailored specifically to you.</p>
              <div class="bk-consult-meta">
                <div class="bk-consult-meta-item">
                  <span class="bk-consult-meta-label">Duration</span>
                  <span class="bk-consult-meta-value">30 min</span>
                </div>
                <div class="bk-consult-meta-divider"></div>
                <div class="bk-consult-meta-item">
                  <span class="bk-consult-meta-label">Price</span>
                  <span class="bk-consult-meta-value">$40</span>
                </div>
              </div>
            </div>
          </div>

          <div class="bk-notice warning" style="margin-top: 0;">
            After your consultation, we'll work together to schedule your first service appointment. Your $40 consultation fee serves as your deposit.
          </div>

          <div class="bk-nav">
            <button class="bk-btn-ghost" onclick="Booking.goTo(1)">← Back</button>
            <button class="bk-btn-primary" onclick="Booking.goTo(4)">Book My Consultation →</button>
          </div>
        </div>`;
      return;
    }

    container.innerHTML = `<div class="bk-step-content"><p class="bk-loading">Loading services…</p></div>`;
    loadServices().then(() => {
      let html = `<div class="bk-step-content">
        <h2 class="bk-title">Choose a Service</h2>`;

      if (!state.servicesData || state.servicesData.length === 0) {
        html += `<p class="bk-subtitle">No services available at this time.</p>`;
      } else {
        for (const cat of state.servicesData) {
          const mainServices = cat.services.filter(s => !s.is_addon);
          if (mainServices.length === 0) continue;
          html += `<p class="bk-cat-label">${escHtml(cat.category)}</p><div class="bk-service-list">`;
          for (const svc of mainServices) {
            const selected = state.selectedServiceId == svc.id ? 'selected' : '';
            html += `
              <button class="bk-service-row ${selected}" onclick="Booking.selectService(${svc.id})">
                <span class="bk-service-name">${escHtml(svc.name)}</span>
                <span class="bk-service-meta">
                  <span class="bk-service-duration">${escHtml(svc.duration)}</span>
                  <span class="bk-service-price">${escHtml(svc.price)}</span>
                </span>
              </button>`;
          }
          html += `</div>`;
        }
      }

      const canContinue = state.selectedServiceId !== null;
      html += `
        <div class="bk-nav">
          <button class="bk-btn-ghost" onclick="Booking.goTo(1)">← Back</button>
          <button class="bk-btn-primary" ${canContinue ? '' : 'disabled'} onclick="Booking.continueToAddons()">
            Next: Add-Ons →
          </button>
        </div>
      </div>`;
      container.innerHTML = html;
    });
  }

  function selectService(id) {
    if (state.selectedServiceId !== id) {
      state.selectedAddons = [];
      state.availabilityData = null;
      state.availabilityCache = {};
    }
    for (const cat of (state.servicesData || [])) {
      const found = cat.services.find(s => s.id == id);
      if (found) { state.selectedService = found; break; }
    }
    state.selectedServiceId = id;
    renderStep2(document.getElementById('bk-body'));
  }

  function continueToAddons() {
    if (!state.selectedServiceId) return;
    goTo(3);
  }

  // ── Step 3: Add-ons ─────────────────────────────────────────
  function renderStep3(container) {
    container.innerHTML = `<div class="bk-step-content"><p class="bk-loading">Loading add-ons…</p></div>`;
    loadServices().then(() => {
      const addons = [];
      for (const cat of (state.servicesData || [])) {
        for (const svc of cat.services) {
          if (svc.is_addon) addons.push(svc);
        }
      }

      const backStep = (state.preselectedServiceId && !state.isNewClient) ? 1 : 2;

      let html = `<div class="bk-step-content">
        <h2 class="bk-title">Any Add-Ons?</h2>
        <p class="bk-subtitle">Optional extras to include with your <strong>${escHtml(state.selectedService ? state.selectedService.name : 'appointment')}</strong>. You can skip this step if you don't need any.</p>`;

      if (addons.length === 0) {
        html += `<p class="bk-subtitle">No add-ons available at this time.</p>`;
      } else {
        html += `<div class="bk-addon-list">`;
        for (const addon of addons) {
          const isChecked = state.selectedAddons.some(a => a.id == addon.id);
          html += `
            <label class="bk-addon-row${isChecked ? ' selected' : ''}">
              <input type="checkbox" class="bk-addon-check" value="${addon.id}" ${isChecked ? 'checked' : ''}
                onchange="Booking.toggleAddon(${addon.id}, '${escHtml(addon.name)}', '${escHtml(addon.duration)}', '${escHtml(addon.price)}')" />
              <div class="bk-addon-content">
                <span class="bk-addon-name">${escHtml(addon.name)}</span>
                <span class="bk-addon-desc">${escHtml(addon.description)}</span>
              </div>
              <div class="bk-addon-meta">
                <span class="bk-addon-duration">${escHtml(addon.duration)}</span>
                <span class="bk-addon-price">${escHtml(addon.price)}</span>
              </div>
            </label>`;
        }
        html += `</div>`;
      }

      html += `
        <div class="bk-nav">
          <button class="bk-btn-ghost" onclick="Booking.goTo(${backStep})">← Back</button>
          <button class="bk-btn-primary" onclick="Booking.continueFromAddons()" id="bk-addon-continue-btn">Next: Pick a Date →</button>
        </div>
      </div>`;
      container.innerHTML = html;
    });
  }

  function toggleAddon(id, name, duration, price) {
    const idx = state.selectedAddons.findIndex(a => a.id == id);
    if (idx >= 0) {
      state.selectedAddons.splice(idx, 1);
    } else {
      state.selectedAddons.push({ id, name, duration, price });
    }
    // Clear availability cache — total duration changed
    state.availabilityData = null;
    state.availabilityCache = {};
    // Toggle row highlight
    const row = document.querySelector(`.bk-addon-check[value="${id}"]`);
    if (row) row.closest('.bk-addon-row').classList.toggle('selected', idx < 0);
  }

  function continueFromAddons() {
    goTo(4);
  }

  // ── Step 4: Calendar ───────────────────────────────────────
  function renderStep4(container) {
    container.innerHTML = `<div class="bk-step-content"><p class="bk-loading">Checking availability…</p></div>`;
    loadAvailability().then(() => {
      const today = new Date();
      if (!state.calendarYear) {
        state.calendarYear  = today.getFullYear();
        state.calendarMonth = today.getMonth();
      }
      renderCalendar(container);
    });
  }

  function renderCalendar(container) {
    const av   = state.availabilityData;
    const now  = new Date();
    const todayY = now.getFullYear(), todayM = now.getMonth(), todayD = now.getDate();
    const todayStr = `${todayY}-${String(todayM+1).padStart(2,'0')}-${String(todayD).padStart(2,'0')}`;

    // Build a fast lookup: dateStr → {available, fully_booked}
    const dateMap = {};
    if (av && av.dates) {
      for (const d of av.dates) dateMap[d.date] = d;
    }

    const year  = state.calendarYear;
    const month = state.calendarMonth;

    // Min navigable month = today's month
    const minYear = todayY, minMonth = todayM;

    // Max navigable month = last date in availability data
    let maxYear = todayY, maxMonth = todayM;
    if (av && av.dates && av.dates.length > 0) {
      const last = av.dates[av.dates.length - 1].date.split('-').map(Number);
      maxYear = last[0]; maxMonth = last[1] - 1;
    }

    const canGoPrev = year > minYear || (year === minYear && month > minMonth);
    const canGoNext = year < maxYear || (year === maxYear && month < maxMonth);

    const firstDow  = new Date(year, month, 1).getDay();        // 0=Sun
    const startPad  = firstDow === 0 ? 6 : firstDow - 1;       // Mon-first offset
    const daysTotal = new Date(year, month + 1, 0).getDate();
    const monthLabel = new Date(year, month, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

    // Build cells
    let cells = '';
    for (let i = 0; i < startPad; i++) {
      cells += `<div class="bk-cal-cell bk-cal-empty"></div>`;
    }

    for (let day = 1; day <= daysTotal; day++) {
      const ds = `${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
      const cellDate   = new Date(year, month, day);
      const todayMid   = new Date(todayY, todayM, todayD);
      const isPast     = cellDate < todayMid;
      const isToday    = ds === todayStr;
      const isSelected = ds === state.selectedDate;
      const avDay      = dateMap[ds];
      const isAvail    = avDay && !avDay.fully_booked;
      const isFull     = avDay && avDay.fully_booked;

      let cls = 'bk-cal-cell';
      if (isSelected)    cls += ' bk-cal-selected';
      else if (isPast)   cls += ' bk-cal-past';
      else if (isAvail)  cls += ' bk-cal-avail';
      else if (isFull)   cls += ' bk-cal-full';
      else               cls += ' bk-cal-closed';
      if (isToday)       cls += ' bk-cal-today';

      const click = isAvail ? `onclick="Booking.selectDate('${ds}')"` : '';
      const slotTxt = isFull ? `<span class="bk-cal-full-lbl">Full</span>` : '';

      cells += `<div class="${cls}" ${click}>
        <span class="bk-cal-num">${day}</span>
        ${slotTxt}
      </div>`;
    }

    // Trailing empty cells to complete the last row
    const used = startPad + daysTotal;
    const trail = (7 - (used % 7)) % 7;
    for (let i = 0; i < trail; i++) {
      cells += `<div class="bk-cal-cell bk-cal-empty"></div>`;
    }

    const backStep = state.isNewClient ? 2 : 3;
    const canContinue = state.selectedDate !== null;
    const selLabel = state.selectedDate
      ? `<p class="bk-cal-sel-label">Selected: <strong>${fmt(state.selectedDate)}</strong></p>` : '';

    let html = `<div class="bk-step-content">
      <h2 class="bk-title">Choose a Date</h2>`;

    if (av && av.next_month_note) {
      html += `<div class="bk-notice info">${escHtml(av.next_month_note)}</div>`;
    }

    if (!av || !av.dates || av.dates.length === 0) {
      html += `<p class="bk-subtitle">No upcoming availability right now. Please check back soon or reach out directly.</p>`;
    } else {
      html += `
      <div class="bk-calendar">
        <div class="bk-cal-header">
          <button class="bk-cal-nav" ${canGoPrev ? '' : 'disabled'} onclick="Booking.calPrev()">‹</button>
          <span class="bk-cal-month">${monthLabel}</span>
          <button class="bk-cal-nav" ${canGoNext ? '' : 'disabled'} onclick="Booking.calNext()">›</button>
        </div>
        <div class="bk-cal-dow">
          <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
        </div>
        <div class="bk-cal-grid">${cells}</div>
      </div>
      <div class="bk-cal-legend">
        <span class="bk-cal-leg-item"><span class="bk-cal-leg-dot avail"></span>Available</span>
        <span class="bk-cal-leg-item"><span class="bk-cal-leg-dot today"></span>Today</span>
        <span class="bk-cal-leg-item"><span class="bk-cal-leg-dot full"></span>Fully Booked</span>
        <span class="bk-cal-leg-item"><span class="bk-cal-leg-dot closed"></span>Closed</span>
      </div>
      ${selLabel}`;
    }

    html += `
      <div class="bk-nav">
        <button class="bk-btn-ghost" onclick="Booking.goTo(${backStep})">← Back</button>
        <button class="bk-btn-primary" ${canContinue ? '' : 'disabled'} onclick="Booking.goTo(5)">
          Next: Pick a Time →
        </button>
      </div>
    </div>`;

    container.innerHTML = html;
  }

  function calPrev() {
    if (state.calendarMonth === 0) { state.calendarMonth = 11; state.calendarYear--; }
    else state.calendarMonth--;
    renderCalendar(document.getElementById('bk-body'));
  }

  function calNext() {
    if (state.calendarMonth === 11) { state.calendarMonth = 0; state.calendarYear++; }
    else state.calendarMonth++;
    renderCalendar(document.getElementById('bk-body'));
  }

  function selectDate(d) {
    state.selectedDate = d;
    state.selectedTime = null;
    state.selectedTimeLabel = null;
    const parts = d.split('-').map(Number);
    state.calendarYear  = parts[0];
    state.calendarMonth = parts[1] - 1;
    renderCalendar(document.getElementById('bk-body'));
  }

  // ── Step 5: Choose a time ───────────────────────────────────
  function renderStep5() {
    const av = state.availabilityData;
    const dateData = av && av.dates.find(d => d.date === state.selectedDate);
    const slots = dateData ? dateData.available : [];
    const today = av ? av.today : '';
    const isSameDay = state.selectedDate === today;
    const fee = av ? av.same_day_fee : '75.00';
    const feeEnabled = av ? av.same_day_fee_enabled : true;

    let html = `<div class="bk-step-content">
      <h2 class="bk-title">Choose a Time</h2>
      <p class="bk-subtitle">${fmt(state.selectedDate)}</p>`;

    if (isSameDay && feeEnabled) {
      html += `<div class="bk-notice warning">
        <strong>Same-Day Booking:</strong> A $${fee} same-day fee will be added to your deposit.
      </div>`;
    }

    if (slots.length === 0) {
      html += `<p class="bk-subtitle" style="margin-top:1rem;">No available times for this date.</p>`;
    } else {
      html += `<div class="bk-time-grid">`;
      for (const slot of slots) {
        const selected = state.selectedTime === slot.time ? 'selected' : '';
        html += `
          <button class="bk-time-btn ${selected}" onclick="Booking.selectTime('${slot.time}', '${escHtml(slot.label)}')">
            ${escHtml(slot.label)}
          </button>`;
      }
      html += `</div>`;
    }

    const canContinue = state.selectedTime !== null;
    html += `
      <div class="bk-nav">
        <button class="bk-btn-ghost" onclick="Booking.goTo(4)">← Back</button>
        <button class="bk-btn-primary" ${canContinue ? '' : 'disabled'} onclick="Booking.goTo(6)">
          Next: Your Info →
        </button>
      </div>
    </div>`;
    return html;
  }

  function selectTime(time, label) {
    state.selectedTime = time;
    state.selectedTimeLabel = label;
    document.getElementById('bk-body').innerHTML = renderStep5();
  }

  // ── Step 6: Contact info ────────────────────────────────────
  function renderStep6() {
    return `
      <div class="bk-step-content">
        <h2 class="bk-title">Your Information</h2>
        <p class="bk-subtitle">We'll use this to confirm your appointment.</p>
        <div class="bk-form">
          <label class="bk-label">Full Name <span class="bk-req">*</span>
            <input class="bk-input" type="text" id="bk-name" value="${escHtml(state.clientName)}" placeholder="First and last name" />
          </label>
          <label class="bk-label">Phone Number <span class="bk-req">*</span>
            <input class="bk-input" type="tel" id="bk-phone" value="${escHtml(state.clientPhone)}" placeholder="(202) 555-0100" />
          </label>
          <label class="bk-label">Email Address <span class="bk-req">*</span>
            <input class="bk-input" type="email" id="bk-email" value="${escHtml(state.clientEmail)}" placeholder="you@example.com" />
          </label>
          <label class="bk-label">Notes <span class="bk-optional">(optional)</span>
            <textarea class="bk-input bk-textarea" id="bk-notes" placeholder="Anything we should know? e.g. hair history, allergies, inspiration">${escHtml(state.clientNotes)}</textarea>
          </label>
        </div>
        <p id="bk-contact-error" class="bk-error" style="display:none;"></p>
        <div class="bk-nav">
          <button class="bk-btn-ghost" onclick="Booking.goTo(5)">← Back</button>
          <button class="bk-btn-primary" onclick="Booking.continueToReview()">Next: Review →</button>
        </div>
      </div>`;
  }

  function continueToReview() {
    const name = document.getElementById('bk-name').value.trim();
    const phone = document.getElementById('bk-phone').value.trim();
    const email = document.getElementById('bk-email').value.trim();
    const notes = document.getElementById('bk-notes').value.trim();
    const err = document.getElementById('bk-contact-error');

    if (!name || !phone || !email) {
      err.textContent = 'Please fill in your name, phone, and email.';
      err.style.display = 'block';
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      err.textContent = 'Please enter a valid email address.';
      err.style.display = 'block';
      return;
    }

    state.clientName = name;
    state.clientPhone = phone;
    state.clientEmail = email;
    state.clientNotes = notes;
    goTo(7);
  }

  // ── Remaining balance helper ────────────────────────────────
  function remainingBalanceDisplay(svc, addons) {
    const priceStr = String(svc.price || '');
    const depositNum = parseFloat(svc.deposit || 0);
    if (priceStr.toLowerCase().includes('varies') || priceStr.toLowerCase().includes('starting')) return null;
    const m = priceStr.replace(/[$,]/g, '').match(/^(\d+)/);
    if (!m) return null;
    const base = parseFloat(m[1]);
    const isVariable = priceStr.includes('+') || priceStr.toLowerCase().includes('per');
    let addonTotal = 0;
    for (const a of addons) {
      const am = String(a.price || '').replace(/[$,]/g, '').match(/^(\d+)/);
      if (am) addonTotal += parseFloat(am[1]);
    }
    const remaining = Math.max(0, base - depositNum) + addonTotal;
    if (remaining === 0 && !isVariable) return null;
    return `$${remaining.toFixed(0)}${isVariable ? '+' : ''}`;
  }

  // ── Step 7: Review + cancellation ──────────────────────────
  function renderStep7() {
    const av = state.availabilityData;
    const isSameDay = av && state.selectedDate === av.today;
    const feeEnabled = av && av.same_day_fee_enabled;
    const fee = av ? parseFloat(av.same_day_fee) : 75;
    const svc = state.selectedService || { name: 'Consultation', price: '$40', duration: '30 min', deposit: '40.00' };
    const deposit = parseFloat(svc.deposit || 0);
    const totalDeposit = deposit + (isSameDay && feeEnabled ? fee : 0);
    const remaining = remainingBalanceDisplay(svc, state.selectedAddons);

    const cancellationText = `Good Hair Daye requires at least 48 hours notice for cancellations or rescheduling.
    Cancellations made within 48 hours of your appointment will result in forfeiture of your deposit.
    No-shows will be charged the full service price. Same-day cancellations are non-refundable.`;

    let addonsRow = '';
    if (state.selectedAddons.length > 0) {
      addonsRow = `<div class="bk-review-row">
        <span class="bk-review-label">Add-Ons</span>
        <span class="bk-review-value" style="font-size:0.88em;">${state.selectedAddons.map(a => escHtml(a.name)).join(', ')}</span>
      </div>`;
    }

    const remainingRow = remaining ? `
      <div class="bk-review-row">
        <span class="bk-review-label">Remaining Balance</span>
        <span class="bk-review-value" style="color:var(--color-mid);font-size:0.9em;">${escHtml(remaining)} upon arrival</span>
      </div>` : '';

    return `<div class="bk-step-content">
      <h2 class="bk-title">Review Your Booking</h2>

      <div class="bk-review-card">
        <div class="bk-review-row">
          <span class="bk-review-label">Service</span>
          <span class="bk-review-value">${escHtml(svc.name)}</span>
        </div>
        ${addonsRow}
        <div class="bk-review-row">
          <span class="bk-review-label">Date</span>
          <span class="bk-review-value">${fmt(state.selectedDate)}</span>
        </div>
        <div class="bk-review-row">
          <span class="bk-review-label">Time</span>
          <span class="bk-review-value">${escHtml(state.selectedTimeLabel || '')}</span>
        </div>
        <div class="bk-review-row">
          <span class="bk-review-label">Duration</span>
          <span class="bk-review-value">${escHtml(svc.duration)}${state.selectedAddons.length > 0 ? ' <span style="font-size:0.8em;color:var(--color-mid);">+ add-ons</span>' : ''}</span>
        </div>
        <div class="bk-review-row">
          <span class="bk-review-label">Service Price</span>
          <span class="bk-review-value">${escHtml(svc.price)}</span>
        </div>
        ${isSameDay && feeEnabled ? `
        <div class="bk-review-row highlight">
          <span class="bk-review-label">Same-Day Fee</span>
          <span class="bk-review-value">+$${fee.toFixed(2)}</span>
        </div>` : ''}
        <div class="bk-review-row total">
          <span class="bk-review-label">Deposit Due Online</span>
          <span class="bk-review-value">$${totalDeposit.toFixed(2)}</span>
        </div>
        ${remainingRow}
      </div>

      <div class="bk-deposit-note">
        Your deposit of <strong>$${totalDeposit.toFixed(2)}</strong> is paid securely online — you'll receive a payment link at <strong>${escHtml(state.clientEmail)}</strong> after confirming.
      </div>
      ${remaining ? `<div class="bk-arrival-note">
        The remaining balance of <strong>${escHtml(remaining)}</strong> is due upon arrival via <strong>Zelle, CashApp, or Venmo</strong>.
      </div>` : ''}

      <div class="bk-cancellation-box">
        <p class="bk-cancellation-title">Cancellation Policy</p>
        <p class="bk-cancellation-text">${cancellationText}</p>
        <label class="bk-checkbox-label">
          <input type="checkbox" id="bk-cancel-ack" ${state.cancellationAcknowledged ? 'checked' : ''} onchange="Booking.toggleAck(this.checked)" />
          I have read and agree to the cancellation policy
        </label>
      </div>

      <p id="bk-review-error" class="bk-error" style="display:none;"></p>
      <div class="bk-nav">
        <button class="bk-btn-ghost" onclick="Booking.goTo(6)">← Back</button>
        <button class="bk-btn-primary" id="bk-confirm-btn" onclick="Booking.submitBooking()">
          Confirm &amp; Pay Deposit →
        </button>
      </div>
    </div>`;
  }

  function toggleAck(checked) {
    state.cancellationAcknowledged = checked;
  }

  // ── Submit ──────────────────────────────────────────────────
  async function submitBooking() {
    const ack = document.getElementById('bk-cancel-ack');
    if (!ack || !ack.checked) {
      const err = document.getElementById('bk-review-error');
      if (err) { err.textContent = 'Please acknowledge the cancellation policy.'; err.style.display = 'block'; }
      return;
    }

    const btn = document.getElementById('bk-confirm-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Booking…'; }

    try {
      const res = await fetch('/book/api/book/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify({
          date: state.selectedDate,
          start_time: state.selectedTime,
          service_id: state.selectedServiceId,
          addon_ids: state.selectedAddons.map(a => a.id),
          is_new_client: state.isNewClient,
          client_name: state.clientName,
          client_email: state.clientEmail,
          client_phone: state.clientPhone,
          notes: state.clientNotes,
          cancellation_acknowledged: true,
        }),
      });
      const data = await res.json();

      if (data.success) {
        state.confirmation = data;
        goTo(8);
      } else {
        const err = document.getElementById('bk-review-error');
        if (err) { err.textContent = data.error || 'Something went wrong. Please try again.'; err.style.display = 'block'; }
        if (btn) { btn.disabled = false; btn.textContent = 'Confirm Booking →'; }
      }
    } catch (e) {
      const err = document.getElementById('bk-review-error');
      if (err) { err.textContent = 'Network error. Please try again.'; err.style.display = 'block'; }
      if (btn) { btn.disabled = false; btn.textContent = 'Confirm Booking →'; }
    }
  }

  // ── Step 8: Confirmation ────────────────────────────────────
  function renderStep8() {
    const c = state.confirmation || {};
    const totalDeposit = parseFloat(c.total_deposit || 0);
    const svc = state.selectedService || { price: '$40', deposit: '40.00' };
    const remaining = remainingBalanceDisplay(svc, state.selectedAddons);

    const addonsLine = (c.addons && c.addons.length > 0)
      ? `<div class="bk-review-row">
           <span class="bk-review-label">Add-Ons</span>
           <span class="bk-review-value" style="font-size:0.88em;">${c.addons.map(escHtml).join(', ')}</span>
         </div>`
      : '';

    const remainingLine = remaining
      ? `<div class="bk-review-row">
           <span class="bk-review-label">Remaining Balance</span>
           <span class="bk-review-value" style="color:var(--color-mid);font-size:0.9em;">${escHtml(remaining)} upon arrival</span>
         </div>`
      : '';

    return `
      <div class="bk-step-content bk-confirmation">
        <div class="bk-confirm-icon">✓</div>
        <h2 class="bk-title">You're Booked!</h2>
        <p class="bk-subtitle">We can't wait to see you, ${escHtml(state.clientName.split(' ')[0])}.</p>

        <div class="bk-review-card">
          <div class="bk-review-row">
            <span class="bk-review-label">Service</span>
            <span class="bk-review-value">${escHtml(c.service_name || '')}</span>
          </div>
          ${addonsLine}
          <div class="bk-review-row">
            <span class="bk-review-label">Date</span>
            <span class="bk-review-value">${escHtml(c.date || '')}</span>
          </div>
          <div class="bk-review-row">
            <span class="bk-review-label">Time</span>
            <span class="bk-review-value">${escHtml(c.time || '')}</span>
          </div>
          <div class="bk-review-row total">
            <span class="bk-review-label">Deposit Due Online</span>
            <span class="bk-review-value">$${totalDeposit.toFixed(2)}</span>
          </div>
          ${remainingLine}
        </div>

        <div class="bk-deposit-note">
          A payment link for your <strong>$${totalDeposit.toFixed(2)} deposit</strong> has been sent to <strong>${escHtml(state.clientEmail)}</strong>. Please complete your payment within 24 hours to secure your appointment.
        </div>
        ${remaining ? `<div class="bk-arrival-note">
          Your remaining balance of <strong>${escHtml(remaining)}</strong> is due upon arrival via <strong>Zelle, CashApp, or Venmo</strong>.
        </div>` : ''}

        <button class="bk-btn-primary w-full mt-6" onclick="Booking.close()">Done</button>
      </div>`;
  }

  // ── Public API ──────────────────────────────────────────────
  return {
    open,
    close,
    goTo,
    handleClientType,
    selectService,
    continueToAddons,
    toggleAddon,
    continueFromAddons,
    calPrev,
    calNext,
    selectDate,
    selectTime,
    continueToReview,
    toggleAck,
    submitBooking,
  };
})();

// Close on overlay click or Escape key
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('bk-overlay');
  if (overlay) {
    overlay.addEventListener('click', e => { if (e.target === overlay) Booking.close(); });
  }
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && overlay && overlay.style.display !== 'none') Booking.close();
  });
});
