# 🎓 StudentHub – Student Management System

A web-based Student Management System developed using **Python and Django** to simplify and organize college student records and academic activities.

## 🚀 Features

### 👨‍🎓 Student Management
- Add, edit, view and delete student records.
- Search and manage student information.

### 💰 Fee Management
- Assign student fees.
- Record fee payments.
- View payment history and fee reports.

### 📅 Attendance Management
- Mark student attendance.
- View attendance records.
- Track student attendance reports.

### 📊 Marks Management
- Add and manage semester marks.
- Calculate SGPA.
- Generate individual student marksheets.
- View performance analysis and marks reports.

### 📈 Reports & Analytics
- Student reports.
- Fee reports.
- Attendance reports.
- CSV export functionality.

### 🔐 Authentication
- Secure Django login system.

## 🛠️ Technologies Used

- Python
- Django
- SQLite
- HTML5
- CSS3
- Bootstrap 5
- JavaScript

## 📂 Project Structure

```text
STUDENT_MANAGEMENT_SYSTEM/
│
├── student_records/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── student_system/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/
├── static/
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/anassk03/StudentHub-Management-System.git
cd StudentHub-Management-System
```

### 2. Create a virtual environment

```bash
py -m venv .venv
```

### 3. Activate the environment (Windows)

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
py -m pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-own-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Generate your own secret key. Never share or upload your `.env` file.

### 6. Apply database migrations

```bash
py manage.py migrate
```

### 7. Create an administrator account

```bash
py manage.py createsuperuser
```

### 8. Run the development server

```bash
py manage.py runserver
```

Open your browser and visit:

http://127.0.0.1:8000/

## 👨‍💻 Developer

**Anas Shaik**

GitHub: [@anassk03](https://github.com/anassk03)

## 📄 License

This project is available for educational and learning purposes.