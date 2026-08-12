# نشر Yellow Duck مجاناً (Render + MongoDB Atlas)

> **الرابط النهائي:** `https://yellowduck-xxxx.onrender.com`  
> Flask + React + MongoDB على استضافة مجانية للتجربة ومشاركة المشروع مع أصدقائك.

---

## نظرة سريعة

| الخدمة | الدور | التكلفة |
|--------|-------|---------|
| [Render](https://render.com) | تشغيل التطبيق (Docker) | مجاني |
| [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) | قاعدة البيانات | مجاني (M0) |
| [GitHub](https://github.com) | رفع الكود | مجاني |

**ملاحظة:** الخطة المجانية على Render **بتنام** بعد 15 دقيقة بدون زيارات — أول فتح بعد كده ممكن ياخد 30–90 ثانية (خصوصاً ML).

---

## الخطوة 1 — MongoDB Atlas (قاعدة البيانات)

1. سجّل على [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. **Create** → Cluster **M0 FREE**
3. **Database Access** → Add User (username + password) → احفظهم
4. **Network Access** → **Add IP Address** → **Allow Access from Anywhere** (`0.0.0.0/0`)
5. **Database** → **Connect** → **Drivers** → انسخ الـ connection string:

```
mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

6. استبدل `<password>` بكلمة المرور الحقيقية
7. أضف اسم الداتابيز: `...mongodb.net/graduation?retryWrites=...`

**مثال:**
```
mongodb+srv://yellowduck:MyPass123@cluster0.abc123.mongodb.net/graduation?retryWrites=true&w=majority
```

---

## الخطوة 2 — رفع المشروع على GitHub

### لو Git مش مثبت
1. نزّل [GitHub Desktop](https://desktop.github.com)
2. **File → Add Local Repository** → اختار مجلد `yellowduck`
3. **Publish repository** (Public أو Private)

### أو من Terminal (لو Git مثبت)
```bash
cd yellowduck
git init
git add .
git commit -m "Yellow Duck — ready for deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/yellowduck.git
git push -u origin main
```

---

## الخطوة 3 — Render (الاستضافة)

1. سجّل على [render.com](https://render.com) (Login with GitHub)
2. **New +** → **Web Service**
3. Connect الـ repo بتاع `yellowduck`
4. الإعدادات:

| الحقل | القيمة |
|-------|--------|
| **Name** | `yellowduck` |
| **Region** | Frankfurt أو أقرب منطقة |
| **Branch** | `main` |
| **Runtime** | **Docker** |
| **Instance Type** | **Free** |

5. **Environment Variables** (مهم):

| Key | Value |
|-----|-------|
| `MONGO_URI` | connection string من Atlas (الخطوة 1) |
| `MONGO_DB` | `graduation` |
| `SECRET_KEY` | string عشوائي طويل (مثلاً 64 حرف) |
| `FLASK_DEBUG` | `false` |
| `SESSION_COOKIE_SECURE` | `true` |
| `CORS_ORIGINS` | `https://YOUR-APP.onrender.com` *(بعد ما Render يديك الرابط)* |
| `FRONTEND_URL` | `https://YOUR-APP.onrender.com` |
| `REQUIRE_EMAIL_VERIFICATION` | `false` |
| `SMTP_ENABLED` | `false` |

6. **Create Web Service** — الـ build هياخد 5–15 دقيقة

7. بعد ما يشتغل، افتح الرابط وجرّب:
   - `https://YOUR-APP.onrender.com/api/health` → `"mongodb": true`
   - `https://YOUR-APP.onrender.com` → الصفحة الرئيسية

8. **رجّع** حدّث `CORS_ORIGINS` و `FRONTEND_URL` بالرابط الحقيقي لو حطيت placeholder

---

## الخطوة 4 — ابعت الرابط لصحابك

```
https://yellowduck-xxxx.onrender.com
```

### حسابات تجريبية (أنشئها من Sign Up)
- **Founder:** لإنشاء مشاريع + Cash Flow + Funding
- **Investor:** للاستثمار ومشاهدة المشاريع

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| `"mongodb": false` | تأكد من `MONGO_URI` + Network Access `0.0.0.0/0` على Atlas |
| Login مش شغال | `CORS_ORIGINS` و `FRONTEND_URL` = نفس رابط Render بالضبط |
| الصفحة بطيئة أول مرة | طبيعي — Free tier + ML models |
| Build failed (memory) | Dockerfile يستخدم `--workers 1` — انتظر وعيد Deploy |
| Uploads بتختفي | Free tier — الملفات المرفوعة **مش permanent** (Ephemeral disk) |

---

## تحديث بعد تعديل الكود

```bash
git add .
git commit -m "update"
git push
```

Render يعمل **auto-deploy** من GitHub.

---

## بدائل مجانية

| Platform | ملاحظة |
|----------|--------|
| **Railway** | $5 credit/month — أسهل لكن محدود |
| **Fly.io** | Docker — محتاج بطاقة للتحقق أحياناً |
| **PythonAnywhere** | Flask فقط — محتاج build React يدوي |

**الأنسب لمشروعك:** Render + MongoDB Atlas (Docker جاهز + MongoDB cloud).
