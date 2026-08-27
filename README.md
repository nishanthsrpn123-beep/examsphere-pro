# Online Examination Management and Student Performance Analysis System

> **ExamSphere Pro** &mdash; A modern, full-stack, college final-year project designed for managing online examinations, real-time computerized testing, and multi-dimensional student performance analytics.

---

## 🌟 Key Features

### 1. Student Module
- **Authentication**: Registration and login with unique Register Numbers.
- **Student Dashboard**: Live overview of metrics, quick links to exams, and recent scorecards.
- **Interactive Examination Room**:
  - Live countdown timer synchronized with backend limits.
  - Visual warning alerts when time is running out.
  - Dynamic Question Navigation Palette (Answered, Unanswered, Marked for Review, Current).
  - Clear response and Mark for Review capabilities.
  - Automatic submission upon timer expiry (`00:00`).
- **Instant Result & Review**:
  - Scorecard with Marks Obtained, Percentage, Grade, and Pass/Fail status.
  - Question-by-question breakdown with highlighted answers and detailed explanations.
- **Performance Analytics & Report Card**:
  - **Previous vs Current Performance Comparison Table**: Direct delta tracking ($+$/$-$\% progression across multiple attempts).
  - **Multi-Chart Analytics (Chart.js)**:
    1. Subject Mastery Comparison (Latest vs Best Score per subject).
    2. Score Progression Timeline (Line graph showing improvement across attempts).
    3. Question Accuracy Doughnut Chart (Correct vs Incorrect vs Unattempted).
  - **Printable Official College Report Card**: Clean format with college seal, metadata, grading table, CGPA/class, and signature lines.

### 2. Admin Module
- **Institutional Analytics Dashboard**:
  - Real-time counters (Registered Students, Active Exams, Question Bank MCQs, Total Evaluated Attempts, Global Average Score, Pass Rate).
  - Subject Average Score Bar Chart and Grade Distribution Pie Chart.
  - Recent student submissions feed.
- **Examination Management**:
  - Full CRUD operations for exams (Title, Course Code, Description, Duration, Pass Percentage, Active/Inactive toggle).
- **Question Bank Management**:
  - Add, edit, and delete 4-option MCQs per exam with correct answer selector, marks, and detailed solution explanations.
- **Students Directory**:
  - Search students by name, register number, or email. Filter by department.
  - Access any student's individual analytics and official report card.
- **Master Results Log & CSV Export**:
  - Filter attempts by exam and status.
  - One-click export to CSV for institutional archives.

---

## 📂 Project Folder Structure

```
online_exam_system/
│
├── app.py                     # Main Flask Application & Route Controller
├── config.py                  # Database & Application Configuration
├── models.py                  # SQLAlchemy Database Schema (6 Relational Models)
├── seed_data.py               # Database Seeder (Admin, 5 Students, 3 Subject Exams, Attempts)
├── requirements.txt           # Python package dependencies
├── run.bat                    # 1-Click Windows startup batch script
├── README.md                  # Project documentation & demonstration guide
│
├── static/
│   ├── css/
│   │   └── style.css          # Custom styling, dark/light cards, exam interface, print layout
│   └── js/
│       ├── exam.js            # Live countdown timer, palette navigation, auto-submit
│       └── analytics.js       # Chart.js visualizations for student & admin metrics
│
└── templates/
    ├── base.html              # Base layout with navbar, alerts, footer
    ├── auth/
    │   ├── login.html         # Login page with quick-fill demo buttons
    │   └── register.html      # Student registration form
    ├── student/
    │   ├── dashboard.html     # Student metrics, active exam warning, exam catalog
    │   ├── exams.html         # Exam catalog with attempt stats
    │   ├── instructions.html  # Exam guidelines & policy agreement
    │   ├── take_exam.html     # Live examination room with countdown & palette
    │   ├── result.html        # Scorecard and detailed review with explanations
    │   ├── performance.html   # Performance analysis with delta comparison and graphs
    │   └── report_card.html   # Official college grade sheet with print layout
    └── admin/
        ├── dashboard.html     # Admin analytics dashboard with charts
        ├── exams.html         # Manage examinations & status toggle
        ├── exam_form.html     # Create / Edit exam form
        ├── questions.html     # Question bank for specific exam
        ├── question_form.html # Create / Edit MCQ with options & explanation
        ├── students.html      # Registered students directory with search
        ├── student_detail.html# Individual student profile & past attempts
        └── all_results.html   # Comprehensive result log with CSV export
```

---

## ⚙️ Installation & Setup Instructions

### 1. Prerequisites
- **Python 3.8+** installed on Windows. (Check via `python --version`)

### 2. Install Dependencies
Open PowerShell or Command Prompt in the project folder:
```powershell
cd C:\Users\PRADEEP20081\.gemini\antigravity\scratch\online_exam_system
pip install -r requirements.txt
```

### 3. Database Configuration
By default, the project uses **SQLite** (`exam_system.db`), which runs out of the box with zero configuration on Windows.

#### (Optional) Switching to MySQL:
If you want to connect to MySQL:
1. Ensure MySQL Server is running.
2. Create an empty database in MySQL:
   ```sql
   CREATE DATABASE exam_system_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Install PyMySQL:
   ```powershell
   pip install pymysql
   ```
4. Set the `DATABASE_URL` environment variable before running:
   ```powershell
   $env:DATABASE_URL="mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/exam_system_db"
   ```

### 4. Initialize & Seed Sample Data
Run the database seeder to populate realistic exams, questions, students, and attempts:
```powershell
python seed_data.py
```

### 5. Start the Application
Run the Flask server:
```powershell
python app.py
```
*Or simply double-click **`run.bat`** on Windows.*

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Login Credentials

The project comes pre-seeded with realistic demonstration accounts:

### Administrator Account
| Role | Email / Login ID | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@college.edu` | `Admin@123` | Full administrative control |

### Sample Student Accounts
| Register Number | Student Name | Department | Email | Password |
| :--- | :--- | :--- | :--- | :--- |
| `2024CS001` | **Rahul Sharma** | Computer Science & Engg | `rahul@college.edu` | `Student@123` |
| `2024CS002` | **Priya Patel** | Computer Science & Engg | `priya@college.edu` | `Student@123` |
| `2024CS003` | **Amit Kumar** | Computer Science & Engg | `amit@college.edu` | `Student@123` |
| `2024IT004` | **Sneha Reddy** | Information Technology | `sneha@college.edu` | `Student@123` |
| `2024EC005` | **Vikram Singh** | Electronics & Comm | `vikram@college.edu` | `Student@123` |

*(Note: On the login page, you can click any of the **Quick Demo Login** buttons to auto-fill credentials instantly).*

---

## 🧪 Demonstration Guide

### A. Demonstrating Student Live Exam Attempt:
1. Log in as **Rahul Sharma** (`2024CS001` / `Student@123`).
2. Go to **"Available Exams"** from the navigation bar.
3. Select **"CS305: Database Management Systems (DBMS) & SQL"**.
4. Read the instructions, check the agreement box, and click **"Start Examination Now"**.
5. Observe the **Live Sticky Countdown Timer** in the header.
6. Answer questions using the radio options. Notice the **Question Palette** on the right turn **green** for answered questions.
7. Click **"Mark for Review"** on a question; notice the palette button turns **yellow**.
8. Navigate using **Previous / Next** or by clicking numbers in the Question Palette.
9. Click **"Submit Exam"** and confirm.
10. Review your instant scorecard, accuracy percentage, and question-by-question explanations.

### B. Demonstrating Student Performance Analysis & Report Card:
1. From the top navigation, click **"Performance Analysis"**:
   - View key metric cards (Total Attempts, Overall Average, Highest Score, Pass Rate).
   - View **Subject Performance Bar Chart** comparing Latest vs Best scores.
   - View **Score Progression Timeline Chart** showing performance growth over exam attempts.
   - View **Question Accuracy Doughnut Chart**.
   - Inspect the **Previous vs Current Score Comparison Table** showing the calculated **$\pm$\% delta** and trend status.
2. Click **"Report Card"**:
   - View the official college-formatted grade sheet complete with institutional header, student metadata, statement of marks, CGPA/classification, and signature blocks.
   - Click **"Print / Save as PDF"** to test the print styling.

### C. Demonstrating Admin Management & Analytics:
1. Log out and log in as **Admin** (`admin@college.edu` / `Admin@123`).
2. View the **Admin Analytics Dashboard** featuring institutional averages, grade distribution, and recent submissions.
3. Go to **"Manage Exams"**:
   - Create a new exam or toggle an existing exam's active/inactive status.
   - Click **"Questions"** on any exam to add, edit, or delete MCQs with solution explanations.
4. Go to **"Students Directory"**:
   - Search for "Rahul" or filter by "Computer Science & Engineering".
   - Click **"Analytics"** on any student to inspect their performance progression.
   - Click **"Report Card"** to view and print their official grade report.
5. Go to **"All Results"**:
   - Filter attempts by course or pass/fail status.
   - Click **"Export All to CSV"** to download the complete spreadsheet.
