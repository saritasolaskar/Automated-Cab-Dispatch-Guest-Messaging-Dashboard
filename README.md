# Automated-Cab-Dispatch-Guest-Messaging-Dashboard
Automated Event Transport Dispatch Dashboard — Ingests Excel allocation sheets, standardizes driver/guest data, and generates error-free WhatsApp messages with 1-click dispatch and live status tracking.


# 🚗 Cab Dispatch & Guest Messaging Automation System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

An automated operations dashboard built with **Python & Streamlit** designed for event transport companies, fleet operators, and logistics coordinators. It eliminates manual data entry by extracting guest and driver allocations from Excel files and instantly generating standardized, validated WhatsApp messages ready for 1-click dispatch.

---

## 📌 Problem & Solution

* **The Problem:** Operations teams spend 30–45 minutes manually copying driver details, car numbers, guest names, pickup times, and addresses into WhatsApp messages for client groups. This manual process frequently leads to typos in phone numbers, incorrect vehicle plates, and missed allocations.
* **The Solution:** A centralized web tool where coordinators drag-and-drop the Excel sheet to produce 100% accurate, formatted messages with smart status tracking (flagging missing information, tracking already-sent messages, and highlighting updated rows upon re-upload).

---

## ✨ Key Features

- **📂 Smart Header Detection:** Automatically parses Excel sheets even when Row 1 contains merged banner titles (e.g., `C2W Cab Details - Igatpuri`).
- **🧹 Automated Data Cleansing:**
  - Standardizes mobile numbers (removes `.0`, fixes multiple numbers like `98202XXXXX / 91372XXXXX`).
  - Normalizes vehicle models (e.g., `Swift Desire` $\to$ `Dzire`, `Ertiga/Innova` $\to$ `Ertiga`).
  - Formats pickup times cleanly (`8:00 AM`, `9.00 A.M.` $\to$ `8:00 AM`).
- **🏷️ Real-Time Status Badges:**
  - 🟢 **`READY TO SEND`**: Fully validated with all required details.
  - 🆕 **`NEW / UPDATED`**: Detects changes and highlights newly assigned drivers when re-uploading an updated Excel version.
  - ⚠️ **`INCOMPLETE`**: Pinpoints exact missing fields (e.g., *Missing Driver Phone*, *Missing Vehicle No*).
  - ✅ **`ALREADY SENT`**: Tracks dispatched messages to prevent duplicate messaging.
- **⚡ 1-Click Operations:**
  - **Instant Copy:** `📋 Copy Text` button copies the message directly to your clipboard with zero page reloads.
  - **Direct WhatsApp:** `📲 Send WhatsApp` opens WhatsApp Web or Desktop pre-populated with the exact text.
- **📦 Batch Export:** Download all messages or only unsent messages as a `.txt` file with one click.

---

## 📱 Standard Output Format

For each row in your Excel sheet, the system automatically produces this exact structured message:

```text
Vehicle and driver details for
Passenger: Seema Rai
Number :- 9324383024

Driver: Shravan Yadav
Number: 6202801624
Vehicle: MH 48 DC 7783
Vehicle : Ertiga
Reporting on 22/08/2026 at 8:00 AM

Reporting address :- Navjeevan Nursing Home, Panchamratna Park, Goldennest Phase 3, Mira Road East
Drop Address :-Rakabi the Fern Igatpuri Series by Marriott
