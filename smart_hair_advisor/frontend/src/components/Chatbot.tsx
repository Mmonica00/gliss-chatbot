import { useState } from "react";

const Chatbot = () => {
  const [messages, setMessages] = useState([{ sender: "bot", text: "Hi! Upload a photo or tell me about your hair." }]);
  const [input, setInput] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Send to backend (later connect to FastAPI /chatbot/analyze)
    const res = await fetch("http://127.0.0.1:8000/chatbot/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: input }),
    });
    const data = await res.json();

    setMessages((prev) => [...prev, { sender: "bot", text: data.reply || "Hmm, I’m not sure yet!" }]);
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: "10px", textAlign: m.sender === "user" ? "right" : "left" }}>
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
