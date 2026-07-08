# 🧑‍💻 Kaleb Individual Project — Active vs Disabled Users

## 📌 Overview

This project is a small, focused Python application that works with two user lists:

- `Active_Users.txt`
- `Disabled_Users.txt`

The goal is to **load, process, and present information about active and disabled users** from these text files, demonstrating:

- Basic file I/O in Python
- Simple data processing
- Clear separation of data files and application logic
- Early UI/UX thinking (via the `Map_App_Dev.jpeg` concept image)

It was completed as an individual project on **27th April 2026**.

---

## 📂 Project structure

```text
Kaleb_Individual_Project/
│
├── App.py               # Main Python script (core logic / UI)
├── Active_Users.txt     # Text file listing active users
├── Disabled_Users.txt   # Text file listing disabled users
├── Map_App_Dev.jpeg     # Concept image / mockup for the app interface
└── README.md            # Project documentation
```

---

## 🛠️ Tech stack

- **Language:** Python 3.x
- **Data format:** Plain text (`.txt`)
- **Assets:** JPEG image for UI concept

---

## 🔍 What the app does (high-level)

The project focuses on:

- **Reading user data** from `Active_Users.txt` and `Disabled_Users.txt`
- **Separating users by status** (active vs disabled)
- **Providing a simple way to view or reason about user status**
- Using `Map_App_Dev.jpeg` as a **design reference** for how the app could look or be extended in the future (for example, a map-style or dashboard-style interface).

> If each line in the `.txt` files represents a single user, this project is a clean example of how to turn raw text data into structured information.

---

## ▶️ How to run the project

1. **Clone the repo:**

   ```bash
   git clone https://github.com/Kaleb-Mat/Kaleb_Individual_Project.git
   cd Kaleb_Individual_Project
   ```

2. **Make sure you have Python 3 installed.**

3. **Run the main script:**

   ```bash
   python App.py
   ```

Depending on how `App.py` is implemented, it may:

- Print summaries to the terminal (e.g., number of active vs disabled users)
- Display lists of users
- Use the text files as input for further logic or UI.

---

## 📚 Learning outcomes

This project demonstrates:

- **File handling in Python**  
  Reading from and working with `.txt` files.

- **Basic data processing**  
  Distinguishing between different user states (active vs disabled).

- **Project structuring**  
  Keeping data files, code, and design assets separate but connected.

- **Portfolio readiness**  
  A small but clear example of how you think about data and user status.

---

## 🔮 Possible future improvements

- **Add validation**  
  Handle empty lines, duplicate users, or malformed entries in the `.txt` files.

- **Add summary statistics**  
  - Total users  
  - Percentage active vs disabled  
  - Export a combined report (e.g., `User_Status_Report.txt`).

- **Add a simple UI**  
  - CLI menu  
  - Streamlit or Tkinter interface inspired by `Map_App_Dev.jpeg`.

- **Extend to real systems**  
  - Integrate with an actual user directory (e.g., CSV export from AD or a database).
  - Add logging and error handling.

---

## 🧾 Project metadata

- **Author:** Kaleb Ashebir  
- **Type:** Individual project  
- **Date completed:** 27 April 2026  
- **Portfolio focus:** Junior data engineer / data-focused Python developer

