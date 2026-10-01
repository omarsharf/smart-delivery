# توصيل ذكي Smart Delivery



توثيق المشروع (نسخة الـ README) - منصة ويب لإدارة طلبات الشحن وتتبعها من الطلب حتى التسليم - مبنية بـ Django.

## مقدمة المشروع (Project Overview)



الفكرة الأساسية: منصة ويب لإدارة شركة شحن: تسجل العملاء والسائقين والشحنات، وتوزع الشحنات على السائقين، وتتابع حالة كل شحنة خطوة بخطوة (معلقة - مسندة - في الطريق - تم التسليم) مع سجل كامل يوثق من غيّر كل حالة ومتى. وفوق ذلك مساعد ذكي داخل الموقع يقرأ بيانات النظام الحقيقية ويرد على أسئلة العميل عن شحناته.

## التقنيات المستخدمة



* **لغة البرمجة:** Python (الإصدار 3.12).


* **إطار العمل:** Django (الإصدار 6.1 - نمط MVT).


* **قاعدة البيانات العلائقية:** PostgreSQL (الإصدار 17).


* **واجهات المستخدم:** HTML/CSS (قوالب + ملفات ثابتة).


* **إدارة الإصدارات:** Git/GitHub.



## مميزات المشروع (Features)



* تسجيل بدور (عميل أو سائق مع نوع المركبة) - والموزع يضاف إدارياً فقط.


* طلب شحنة (نموذج كامل + رقم تتبع فريد UUID).


* توجيه ذكي بعد الدخول: كل مستخدم يوصل لشاشة دوره مباشرة.


* تتبع عام: الحالة + خط زمني كامل لتغييراتها.


* شحناتي: لوحة العميل بإحصائيات وفلاتر حسب الحالة.


* لوحة السائق: شحناته فقط + أزرار تحديث ذكية حسب الحالة.


* لوحة التوزيع: المعلقات كلها + إسناد لسائق بضغطة واحدة.


* سجل مساءلة: كل تغيير حالة يُسجل (من - إلى + مين + امتى).


* مساعد ذكي يرد على رقم الشحنة بحالتها الحقيقية (مع فحص ملكية).


* حماية بالأدوار: فحص في الخادم لا في الواجهة.



## دليل التثبيت والتشغيل المحلي (Getting Started)



المتطلبات الأساسية: Python 3.12+، PostgreSQL، Git.

1. **استنساخ المشروع:**

```bash
git clone https://github.com/khaledsameh979-web/smart_delivery.git
cd smart_delivery

```


2. **بيئة افتراضية وتفعيلها:**

```bash
python -m venv venv
venv\Scripts\activate

```


3. **تثبيت المكتبات:**

```bash
pip install django psycopg2-binary

```


4. **إنشاء قاعدة البيانات ثم ضبط `mysite/settings.py`:**

```python
# NAME = 'smart_delivery_db', USER = 'postgres'
# PASSWORD = > لا تضعها في الكود أبدأ كلمة مرور قاعدة بياناتك وتنشأ محليا ولا تنشر مع الكود.

```


5. **إنشاء الجداول:** `python manage.py migrate`.


6. **حساب الإدارة:** `python manage.py createsuperuser`.


7. **تشغيل السيرفر:** `python manage.py runserver` ثم افتح `[http://127.0.0.1:8000](http://127.0.0.1:8000)`.



حسابات التجربة في قاعدة بيانات العرض: زبون `mona`، سائق `omar`، موزع `dispatch1`.

## هيكل المشروع (Project Structure)



```text
smart_delivery/
│── manage.py
│── mysite/ # إعدادات المشروع settings.py والقاعدة AUTH_USER_MODEL, LOGIN_URL
│   └── urls.py # توجيه admin + include delivery
└── delivery/ # التطبيق الأساسي
    │── models.py # النماذج الستة وعلاقاتها
    │── views.py # منطق كل صفحة (9 عروض)
    │── forms.py # نموذج الشحنة + التسجيل
    │── urls.py # خريطة روابط التطبيق
    │── static/ # تنسيق
    │   ├── css/style.css
    │   └── js/chatbot.js # واجهة الدردشة الحية
    └── templates/delivery/ # قوالب HTML
        ├── base.html # القالب الأب + ويدجت الشات
        ├── home / login / register / request_shipment / track
        ├── customer_dashboard.html # شحناتي
        ├── driver_home.html # لوحة السائق
        ├── dispatch_home.html # لوحة التوزيع
        └── chat_page.html # المساعد الذكي

```

## توثيق الـ API (API Documentation)



| الرابط | الطريقة | البيانات المرسلة | الاستجابة | مين يسمح له ؟ |
| --- | --- | --- | --- | --- |
| `/api/chat/` | POST | `message` | `JSON {"reply": "..."}` | مسجل دخول

 |
| `/register/` | POST | `username, email, name, phone, password1, password2, role, vehicle_type` | تحويل حسب الدور | زائر

 |
| `/login/` | POST | `username, password` | تحويل حسب الدور | زائر

 |
| `/request/` | POST | `pickup_address, dropoff_address, vehicle_type, notes, scheduled_date` | تحويل لصفحة تتبع الشحنة | عميل

 |
| `/track/?number=` | GET | `number` (رقم التتبع) | صفحة HTML بالحالة والخط الزمني | الجميع

 |
| `/dashboard/?status=` | GET | `status` فلتر (اختياري) | صفحة HTML بشحناته | عميل

 |
| `/driver/` | POST | `delivery_id, new_status` | تحديث + تسجيل في السجل | سائق

 |
| `/dispatch/` | POST | `delivery_id, driver_id` | إسناد + تسجيل في السجل | موزع

 |

مثال - سؤال المساعد الذكي عن شحنة:

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "message=29ea6f72-1bb5-4ff0-94b0-6941f045e1c2"

```

الرد: `{"reply" : "شحنتك (29ea6f72) حالتها الآن Assigned الميعاد 28-09-2026 18:00"}`.

## طريقة المساهمة (Contributing Guidelines)



1. Clone لا ZIP: اعمل `git clone` للمستودع - لا تنزل ZIP (مجلدات متداخلة ونسخة قديمة).


2. اسحب أحدث نسخة قبل الشغل: `git pull` قبل أي تعديل.


3. كل ميزة في Commit واضح: مثال `Add driver screen: role guard + status buttons`.


4. لا ترفع أبداً ملفات البيئة أو كلمات المرور أو نسخ قاعدة البيانات.


5. جرب قبل الرفع: شغل السيرفر وتأكد أن كل الصفحات تعمل.


6. الميزات الكبيرة ناقشها مع الفريق أولاً لتفادي تعارض الشغل.



طبقات التوثيق الكاملة: الـ README (للمطوّر) - التوثيق التفصيلي `Smart_Delivery_Documentation.pdf` (للفاهم) - وسجل الـ Git (للمقيّم).
