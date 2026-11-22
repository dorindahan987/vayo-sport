# VAYO Website — הוראות הפעלה

---

## להעלאה לאוויר (Netlify)

1. נכנס לאתר: **netlify.com**
2. לחץ **"Sign up"** (חינמי)
3. לחץ **"Add new site"** ← **"Deploy manually"**
4. גרור את תיקיית **vayo-website** לתוך הדפדפן
5. האתר עולה תוך שניות ✓

לחיבור דומיין קבוע — לחץ **"Domain settings"** ועקוב אחרי ההוראות.

---

## לעריכת האתר עם Claude

**צעד 1 — התקן Node.js**
הורד מ: nodejs.org ← הרץ את ההתקנה

**צעד 2 — התקן Claude Code**
פתח PowerShell והרץ:
```
npm install -g @anthropic-ai/claude-code
```

**צעד 3 — היכנס לתיקייה**
```
cd C:\Users\שם-המשתמש-שלך\vayo-website
```

**צעד 4 — הפעל Claude**
```
claude
```

**צעד 5 — דבר עם Claude בעברית**
פשוט כתוב מה אתה רוצה לשנות, למשל:
> "תוסיף מחיר של 49 שקל לגריפ"
> "תשנה את הצבע של הכפתור"
> "תוסיף עמוד יצירת קשר"

---

## מבנה הקבצים

```
vayo-website/
├── index.html          ← עמוד הבית
├── pages/
│   ├── grip.html       ← עמוד גריפ
│   ├── frame-protector.html  ← עמוד מגן מחבט
│   └── serum.html      ← עמוד סרום
├── css/
│   └── style.css       ← כל העיצוב
├── js/
│   ├── main.js         ← לוגיקה + תרגומים
│   └── hero-bg.js      ← אנימציית הרקע
└── images/
    ├── hero.mov        ← סרטון הרקע (להמיר ל-MP4 לפני העלאה!)
    ├── vayo-logo.png   ← הלוגו
    └── products/       ← תמונות מוצרים (להכניס לכאן)
```

---

## תמונות מוצרים

להכניס לתיקייה `images/products/` עם השמות:
- `grip.jpg`
- `frame-protector.jpg`
- `serum.jpg`

---

## הערה חשובה על הסרטון

הסרטון `hero.mov` הוא 124MB — כבד מדי לאינטרנט.
לפני העלאה, המר אותו ל-MP4 עם **HandBrake** (חינמי):
1. הורד מ: handbrake.fr
2. פתח את `hero.mov`
3. בחר Preset: **"Web → Gmail Medium 5 minutes 720p30"**
4. לחץ **"Start Encode"**
5. שנה את שם הקובץ המתקבל ל-`hero.mp4`
6. עדכן בקוד: שנה `hero.mov` ל-`hero.mp4` בקובץ `index.html`
