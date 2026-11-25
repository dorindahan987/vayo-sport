// ============================
// VAYO — Main JS
// ============================

// ---- TRANSLATIONS ----
const translations = {
  en: {
    nav_products: "Products",
    nav_about: "About",
    nav_contact: "Contact",
    hero_badge: "New Standard · Padel Accessories",
    hero_line1: "EVERY POINT",
    hero_line2: "STARTS IN",
    hero_line3: "YOUR HAND.",

    hero_desc: "Premium padel accessories engineered for players who demand more. Grip harder. Protect smarter.",
    btn_shop: "Shop Now",
    btn_story: "Our Story",
    marquee1: "PRO PADEL OVERGRIP",
    marquee2: "CARBON FIBER TAPE",
    marquee3: "ANTI-SLIP SERUM",
    marquee4: "MADE IN ISRAEL",
    marquee5: "ENGINEERED FOR PADEL",
    sec_products_label: "Our Products",
    sec_products_title: "GEAR UP",
    p1_series: "N / SERIES 03",
    p1_name: "VAYO Overgrip",
    p1_sub: "Pro Padel Overgrip",
    p1_desc: "Engineered for ultimate control. Keeps hands dry, grip firm, no matter the conditions.",
    p1_chip1: "×03 Grips", p1_chip2: "×12 Grips", p1_chip3: "×30 Grips",
    p1_link: "View Product",
    p2_series: "N / SERIES 02",
    p2_name: "FRAME PROTECTOR",
    p2_sub: "Carbon Tape · For Padel",
    p2_desc: "High resistance carbon tape. Shields your racket from impacts, abrasion and court damage.",
    p2_chip1: "High Resistance", p2_chip2: "Anti-Abrasion", p2_chip3: "Carbon",
    p2_link: "View Product",
    p3_series: "N / SERIES 01",
    p3_name: "GRIP SERUM",
    p3_sub: "Advanced Sweat Absorption Formula",
    p3_desc: "Professional serum for sweat neutralization and grip enhancement. Dries in seconds, prevents slippage and delivers maximum racket control at any intensity and humidity. No powder, no sticky residue.",
    p3_chip1: "Sweat-Block", p3_chip2: "Dries Instantly", p3_chip3: "Pro Formula",
    p3_link: "View Product",
    manifesto_eyebrow: "Who we are",
    manifesto_text1: "Living on the court, taking care of every detail around your game.",
    manifesto_text2: "Padel essentials engineered to solve distractions right when it matters most.",
    manifesto_sub: "Vayo · Made in Israel · Engineered for Padel",
    s1_num: "3", s1_lbl: "Products",
    s2_num: "100%", s2_lbl: "Made in IL",
    s3_num: "PRO", s3_lbl: "Grade Quality",
    s4_num: "2", s4_lbl: "Series Live",
    sold_out: "SOLD OUT",
    serum_soon: "COMING SOON",
    rel_title: "More Products",
    footer_sub: "Engineered for Padel",
    f_products: "Products",
    f_about: "About",
    f_contact: "Contact",
    footer_copy: "© 2026 VAYO · ALL RIGHTS RESERVED",
  },
  he: {
    nav_products: "מוצרים",
    nav_about: "אודות",
    nav_contact: "צור קשר",
    hero_badge: "הסטנדרט החדש · אביזרי פאדל",
    hero_line1: "כל נקודה",
    hero_line2: "מתחילה",
    hero_line3: "בידיים שלך.",

    hero_desc: "אביזרי פאדל פרימיום שמתוכננים לשחקנים שדורשים יותר. אחיזה חזקה יותר. הגנה חכמה יותר.",
    btn_shop: "לקנייה",
    btn_story: "הסיפור שלנו",
    marquee1: "גריפ מקצועי לפאדל",
    marquee2: "סרט קרבון",
    marquee3: "סרום אנטי החלקה",
    marquee4: "ייצור ישראלי",
    marquee5: "מתוכנן לפאדל",
    sec_products_label: "המוצרים שלנו",
    sec_products_title: "ציוד מנצח",
    p1_series: "N / סדרה 03",
    p1_name: "VAYO Overgrip",
    p1_sub: "גריפ מקצועי לפאדל",
    p1_desc: "מתוכנן לשליטה מקסימלית. שומר על ידיים יבשות ואחיזה חזקה, בכל תנאי.",
    p1_chip1: "×03 גריפים", p1_chip2: "×12 גריפים", p1_chip3: "×30 גריפים",
    p1_link: "לצפייה במוצר",
    p2_series: "N / סדרה 02",
    p2_name: "מגן מחבט",
    p2_sub: "סרט קרבון · לפאדל",
    p2_desc: "סרט קרבון עמיד. מגן על המחבט שלך מפגיעות, שחיקה ונזקי מגרש.",
    p2_chip1: "עמידות גבוהה", p2_chip2: "אנטי שחיקה", p2_chip3: "קרבון",
    p2_link: "לצפייה במוצר",
    p3_series: "N / סדרה 01",
    p3_name: "GRIP SERUM",
    p3_sub: "פורמולה מתקדמת לספיגת זיעה",
    p3_desc: "סרום מקצועי לנטרול זיעה ושיפור האחיזה. מתייבש תוך שניות, מונע החלקה ומעניק שליטה מקסימלית במחבט בכל עוצמת משחק ולחות. אינו משאיר אבקה או תחושת דביקות.",
    p3_chip1: "ספיגת זיעה", p3_chip2: "מתייבש מיידית", p3_chip3: "פורמולה מקצועית",
    p3_link: "לצפייה במוצר",
    manifesto_eyebrow: "מי אנחנו",
    manifesto_text1: "חיים את המגרש וסוגרים לכם את כל הפינות מסביב\u00A0למחבט.",
    manifesto_text2: "מוצרים נלווים לפאדל שפותרים את מה שמפריע בדיוק בנקודות החשובות.",
    manifesto_sub: "Vayo · ייצור ישראלי · מתוכנן לפאדל",
    s1_num: "3", s1_lbl: "מוצרים",
    s2_num: "100%", s2_lbl: "ייצור ישראלי",
    s3_num: "PRO", s3_lbl: "איכות מקצועית",
    s4_num: "2", s4_lbl: "סדרות זמינות",
    sold_out: "אזל המלאי",
    serum_soon: "בקרוב",
    rel_title: "מוצרים נוספים",
    footer_sub: "מתוכנן לפאדל",
    f_products: "מוצרים",
    f_about: "אודות",
    f_contact: "צור קשר",
    footer_copy: "© 2026 VAYO · כל הזכויות שמורות",
  }
};

let currentLang = 'en';

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem('vayo-lang', lang);
  const t = translations[lang];
  document.body.classList.toggle('rtl', lang === 'he');
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key] !== undefined) {
      const descKeys = ['sr_desc','p3_desc'];
      if (descKeys.includes(key)) {
        el.innerHTML = t[key].replace(/\. /g, '.<br>');
      } else {
        el.textContent = t[key];
      }
    }
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (t[key] !== undefined) el.setAttribute('placeholder', t[key]);
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
  });
}

// ---- CURSOR ----
function initCursor() {
  const dot = document.querySelector('.cursor-dot');
  const ring = document.querySelector('.cursor-ring');
  if (!dot || !ring) return;

  let mouseX = 0, mouseY = 0;
  let ringX = 0, ringY = 0;

  document.addEventListener('mousemove', e => {
    mouseX = e.clientX; mouseY = e.clientY;
    dot.style.left = mouseX + 'px';
    dot.style.top  = mouseY + 'px';
  });

  function animRing() {
    ringX += (mouseX - ringX) * 0.12;
    ringY += (mouseY - ringY) * 0.12;
    ring.style.left = ringX + 'px';
    ring.style.top  = ringY + 'px';
    requestAnimationFrame(animRing);
  }
  animRing();

  document.querySelectorAll('a, button, .product-row').forEach(el => {
    el.addEventListener('mouseenter', () => ring.classList.add('expand'));
    el.addEventListener('mouseleave', () => ring.classList.remove('expand'));
  });
}

// ---- LOADER ----
function initLoader() {
  const loader = document.getElementById('loader');
  if (!loader) return;
  setTimeout(() => loader.classList.add('hidden'), 1800);
}

// ---- NAV SCROLL ----
function initNav() {
  const nav = document.querySelector('nav');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  });

  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => mobileMenu.classList.toggle('open'));
    mobileMenu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => mobileMenu.classList.remove('open')));
  }
}

// ---- SCROLL REVEAL ----
function initReveal() {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
  }, { threshold: 0.08 });
  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
}

// ---- PACK SELECTOR ----
function initPacks() {
  document.querySelectorAll('.pack-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.pack-btns').querySelectorAll('.pack-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

// ---- LANG BUTTONS ----
function initLang() {
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => setLang(btn.getAttribute('data-lang')));
  });
}

// ---- INIT ----
document.addEventListener('DOMContentLoaded', () => {
  initLoader();
  initCursor();
  initNav();
  initReveal();
  initPacks();
  initLang();
  setLang(localStorage.getItem('vayo-lang') || 'he');
});
