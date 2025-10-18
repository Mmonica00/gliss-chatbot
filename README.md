# 💇‍♀️ Smart Hair Advisor

An intelligent chatbot that analyzes a user's hair photo and text description to recommend the best Gliss hair care products — powered by AI and image analysis.

---

## 🚀 Features

- 🧠 **Chatbot Intelligence** — Understands user concerns like dryness, damage, or frizz.  
- 🖼️ **Image Analysis** — Uses hair segmentation and texture detection to assess hair health.  
- 📊 **Dataset Matching** — Maps detected traits to product recommendations using the Gliss dataset.  
- 💬 **Personalized Responses** — Friendly, knowledgeable, and reassuring tone — like a trusted hair expert.  
- 🌐 **Frontend UI** — Simple, intuitive web interface for chatting and uploading images.  

---

## 🧩 Project Structure

```
smart_hair_advisor/
│
├── app/
│   ├── api/                 # FastAPI routes
│   ├── services/            # Analysis, matching, and chatbot logic
│   ├── data/                # Hair dataset (.xlsx)
│   └── frontend/            # (Optional) React or HTML frontend
│
├── frontend/                # Modern React/Tailwind frontend (optional)
├── .venv/                   # Virtual environment (auto-generated)
├── main.py                  # FastAPI entrypoint
├── requirements.txt         # Python dependencies
└── README.md                # You are here
```

---

## ⚙️ Setup Instructions

### 🐍 Backend (FastAPI)

1️⃣ **Create & activate a virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
```

2️⃣ **Install dependencies**
```bash
pip install -r requirements.txt
```

3️⃣ **Run the backend server**
```bash
uvicorn main:app --reload
```

4️⃣ **Access the API**
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Analyze Endpoint: `/chatbot/analyze`

---

### 💻 Frontend (if using React)

1️⃣ **Navigate to the frontend folder**
```bash
cd frontend
```

2️⃣ **Initialize the project**
```bash
npm create vite@latest .
```

3️⃣ **Install dependencies & run**
```bash
npm install
npm run dev
```

4️⃣ **Access UI**
Visit [http://localhost:5173](http://localhost:5173)

---

## 📷 Example Usage (Swagger)

| Input | Description |
|-------|--------------|
| **Message** | "My hair feels dry and frizzy lately." |
| **Image (optional)** | Upload a photo of your hair. |
| **Output** | Hair type & texture detection, top Gliss product matches, and chatbot response. |

---

## 📚 Technologies Used

| Category | Tools |
|-----------|-------|
| **Backend** | FastAPI, Python, NumPy, Pandas |
| **AI / ML** | rembg (U²Net), OpenCV, Pillow |
| **Frontend** | React + Vite + TailwindCSS |
| **Data** | Excel-based Gliss product dataset |
| **Dev Tools** | Uvicorn, Git, VS Code |

---

## 🧑‍💻 Contributors

| Name | Role | Area |
|------|------|------|
| **Maria Awad** | Full-stack Developer | Chatbot logic, frontend, dataset integration |
| **Rodina Alsawy** | Full-stack Developer | Image analysis, matching system |
| **Monica Mina** | Full-stack Developer | API integration, testing, frontend UX |

_All contributors collaborated equally on all major parts of the project._

---

## 🧠 Future Improvements

- 🧬 Enhance AI model accuracy for hair detection.  
- 💅 Add tone & color style recommendations.  
- 📱 Launch mobile version.  
- 💬 Connect to live Gliss product database.

---

## 🪞 License

This project is for **Hackathon / Educational use only**.  
© 2025 Gliss Hair Advisor Team. All rights reserved.

---

## ❤️ Acknowledgments

Special thanks to **Henkel Gliss** and the Hackathon organizers  
for inspiring the idea behind this Smart Hair Advisor.
