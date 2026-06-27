# 🧠 Tổng hợp & Kế hoạch Hackathon

## ✅ Project: Personal Autonomous Agent with Computer Use

> CLI agent tự điều khiển browser, nhìn màn hình, suy luận và hành động như người thật — có memory dài hạn và tự cá nhân hóa theo user

---

## Install & Run

```bash
uv tool install . --reinstall
aria demo
```

Local configuration:

```bash
cp .env.example .env
aria config check
```

Useful commands:

```bash
aria "Research browser-use and produce a short report for ARIA"
aria run "Research browser-use and produce a short report for ARIA"
aria memory search "browser screenshots"
```

Do not commit real API keys. Keep them in `.env` or shell environment variables.

---

## 🏗️ Architecture

```
User Input (CLI)
      ↓
Master Agent (Claude API)
      ↓
Tool Router
   ├── Browser Agent (Playwright + Firefox)
   │      ↓
   │   Screenshot → Vision (Claude API)
   │      ↓
   │   Act (click/type/scroll)
   │
   ├── Memory Agent (ChromaDB)
   │      ↓
   │   Compress → Store → Prune
   │
   └── Summarizer Agent
          ↓
       Output đẹp ra CLI (Rich)
```

---

## 📦 Stack

| Layer | Tool | Lý do |
|---|---|---|
| Browser control | Playwright (Python) | Stable, async support |
| Vision + Reasoning | Claude API | Nhanh, vision tốt nhất |
| Memory | ChromaDB | Em đã biết rồi |
| CLI UI | Rich | Đẹp, dễ demo |
| Auth | Playwright tự login | Không cần OAuth |

---

## ⏱️ Timeline 9h - 19h

**9:00 - 9:30 | Setup**
```
- Tạo project structure
- pip install playwright chromadb anthropic rich
- playwright install firefox
```

**9:30 - 11:00 | Core Browser Agent**
```
- Playwright mở Firefox
- Chụp screenshot
- Gửi lên Claude Vision
- Nhận action → thực thi
- Loop cơ bản chạy được
```

**11:00 - 12:30 | Memory System**
```
- ChromaDB setup
- Compression: tóm tắt thông tin trước khi lưu
- Retrieval: query relevant memory trước mỗi action
- Prune: tự đánh giá memory nào outdated
```

**12:30 - 13:00 | Nghỉ trưa 🍜**

**13:00 - 14:30 | Master Agent + Tool Router**
```
- Master agent nhận task từ user
- Tự quyết định dùng tool nào
- Orchestrate browser agent + memory agent
- ReAct loop: Thought → Action → Observation
```

**14:30 - 16:00 | Personalization Layer**
```
- User profile (ngành, năm học, interests)
- Filter thông tin theo profile
- Agent tự hỏi lại nếu task mơ hồ
```

**16:00 - 17:30 | Test & Fix**
```
- Test end-to-end với task thật
- Fix edge cases
- Đảm bảo demo không vỡ
```

**17:30 - 18:30 | Polish Demo**
```
- Chuẩn bị 2-3 demo scenarios cụ thể
- CLI output trông đẹp với Rich
- Pre-cache các trang hay dùng
```

**18:30 - 19:00 | Chuẩn bị Present**
```
- Slide/note giải thích architecture
- Nhấn mạnh: memory system + computer use = novel
```

---

## 🎯 Demo Scenarios (gợi ý)

1. **"Check thông báo mới nhất từ trường em"**
   → Agent tự mở portal, login, đọc, tóm tắt, lưu memory

2. **"Những gì quan trọng với em tuần này?"**
   → Agent query memory + browser → filter theo profile → trả lời

3. **"Nhắc em deadline nào gần nhất"**
   → Agent tổng hợp từ memory đã học được trước đó

---

## 🔑 Điểm Novel khi Present

> *"Không phải chatbot, không phải scraper — là agent thật sự **nhìn** và **suy nghĩ** như người dùng, nhớ được context theo thời gian, và tự cá nhân hóa"*

---

## 📁 Project Structure gợi ý

```
personal-agent/
├── main.py              # CLI entry point
├── agents/
│   ├── master.py        # Orchestrator
│   ├── browser.py       # Playwright + Vision
│   ├── memory.py        # ChromaDB CRUD
│   └── summarizer.py    # Tóm tắt output
├── tools/
│   ├── screenshot.py
│   └── actions.py       # click, type, scroll
├── profile/
│   └── user.json        # Personalization data
└── config.py            # API keys, settings
```

---
