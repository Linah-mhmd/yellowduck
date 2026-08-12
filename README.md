# Yellow Duck — React + Flask

منصة استثمارية ذكية تربط بين رواد الأعمال والمستثمرين، مع تحليل AI للتمويل والتدفق النقدي.

## الهيكل الجديد

```
yellowduck/
├── app.py              # Flask API Backend
├── api_routes.py       # REST API endpoints
├── frontend/           # React SPA (Vite)
│   ├── src/
│   │   ├── components/ # Layout, ProtectedRoute
│   │   ├── context/    # AuthContext
│   │   ├── pages/      # 15 صفحة React
│   │   ├── services/   # API client (axios)
│   │   └── styles/     # CSS
│   └── package.json
├── ai_funding_optimizer.py
├── cash_flow.py
├── recommendations.py
└── requirements.txt
```

## المتطلبات

- Python 3.10+
- Node.js 18+
- MongoDB (localhost:27017)

## الإعداد

```bash
cd yellowduck
copy .env.example .env   # عدّل SECRET_KEY و MONGO_URI
pip install -r requirements.txt
```

## التشغيل — Development

### 1. Backend (Flask API)

```bash
cd yellowduck
pip install -r requirements.txt
python app.py
```

يعمل على: `http://localhost:5001`

### 2. Frontend (React)

```bash
cd yellowduck/frontend
npm install
npm run dev
```

يعمل على: `http://localhost:3000` (مع proxy تلقائي للـ API)

## التشغيل — Production

```bash
cd yellowduck/frontend
npm install
npm run build

cd ..
python app.py
```

Flask يخدم React build من `frontend/dist` تلقائياً.

## الصفحات (React)

| Route | الوصف |
|-------|-------|
| `/` | الصفحة الرئيسية + توصيات AI |
| `/login` | تسجيل الدخول |
| `/signup` | إنشاء حساب |
| `/poll` | استبيان المطابقة |
| `/projects` | قائمة المشاريع |
| `/projects/:id` | تفاصيل المشروع + استثمار |
| `/create-project` | إنشاء مشروع (Founder) |
| `/control-projects` | إدارة المشاريع |
| `/funding-optimizer` | محلل التمويل AI |
| `/cash-flow` | تحليل التدفق النقدي |
| `/portfolio` | عرض الملف الشخصي |
| `/portfolio/form` | إنشاء/تعديل Portfolio |
| `/notifications` | الإشعارات |
| `/investment/:id` | تفاصيل طلب الاستثمار |

## API Endpoints

جميع الـ endpoints تحت `/api/`:

- `GET/POST /api/auth/*` — المصادقة
- `GET /api/home` — التوصيات
- `GET/POST /api/projects` — المشاريع
- `POST /api/funding-optimizer` — تحليل التمويل
- `POST /api/cash-flow` — تحليل التدفق النقدي
- `GET/POST /api/portfolio/*` — الملف الشخصي
- `GET /api/notifications` — الإشعارات

## Docker

```bash
docker-compose up --build
```

## الاختبارات

```bash
py -m pytest tests/ -v
```

## ما تم تحسينه

- **Password hashing** (scrypt) مع ترقية تلقائية للحسابات القديمة
- **صلاحيات المستخدم** — كل founder يعدّل مشاريعه فقط
- **حذف المشاريع** — API + UI في Control Projects
- **Portfolio upsert** — لا duplicates، تحميل تلقائي للبيانات
- **Search** — بحث في المشاريع من Home و Projects
- **إحصائيات حقيقية** — من MongoDB بدل أرقام وهمية
- **404 + ErrorBoundary** — معالجة أخطاء React
- **Docker + .env** — جاهز للـ deployment
- **pytest** — 6 اختبارات API
- **React SPA** بدلاً من Jinja templates — تجربة أسرع بدون reload
- **React Router** — تنقل سلس بين الصفحات
- **AuthContext** — إدارة حالة المستخدم مركزياً
- **Axios API layer** — طلبات منظمة مع error handling
- **Protected Routes** — حماية الصفحات حسب الدور (Founder/Investor)
- **Chart.js via react-chartjs-2** — رسوم بيانية تفاعلية
- **Flask REST API** — فصل Frontend عن Backend
- **CORS + Session cookies** — أمان المصادقة
