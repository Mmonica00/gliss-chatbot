import { useState, useEffect } from "react";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! Upload a photo or tell me about your hair." },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);

  // --- 1️⃣ Load or create session ID on mount
  useEffect(() => {
    let savedId = localStorage.getItem("chatbot_session_id");
    if (!savedId) {
      savedId = crypto.randomUUID(); // generate new one
      localStorage.setItem("chatbot_session_id", savedId);
    }
    setSessionId(savedId);
  }, []);

  // --- 2️⃣ Handle sending message
  const handleSend = async () => {
    if (!input.trim() || !sessionId) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      // FastAPI /chatbot/analyze expects FormData (not raw JSON)
      const formData = new FormData();
      formData.append("message", input);
      formData.append("session_id", sessionId);

      const res = await fetch("http://127.0.0.1:8000/chatbot/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      // --- 3️⃣ If backend returned a new session (expired etc.), update localStorage
      if (data.session_id && data.session_id !== sessionId) {
        localStorage.setItem("chatbot_session_id", data.session_id);
        setSessionId(data.session_id);
      }

      // --- 4️⃣ Display bot response
      const botReply =
        data.message || data.reply || "Hmm, I’m not sure yet!";
      setMessages((prev) => [...prev, { sender: "bot", text: botReply }]);
    } catch (err) {
      console.error("Chatbot error:", err);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, something went wrong." },
      ]);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              marginBottom: "10px",
              textAlign: m.sender === "user" ? "right" : "left",
            }}
          >
            <strong>{m.sender === "user" ? "You" : "Bot"}:</strong> {m.text}
          </div>
        ))}
      </div>

      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

export default Chatbot;
