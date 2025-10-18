import { useState, useEffect } from "react";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! Upload a photo or tell me about your hair." },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // --- 1️⃣ Load or create session ID on mount
  useEffect(() => {
    let savedId = localStorage.getItem("chatbot_session_id");
    if (!savedId) {
      savedId = crypto.randomUUID(); // generate new one
      localStorage.setItem("chatbot_session_id", savedId);
    }
    setSessionId(savedId);
  }, []);

  // --- 2️⃣ Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Auto-send when file is selected
      handleSend(file);
    }
  };

  // --- 3️⃣ Handle sending message
  const handleSend = async (file?: File) => {
    const messageText = input.trim();
    const fileToSend = file || selectedFile;
    
    if (!messageText && !fileToSend) return;

    const userMessage = { 
      sender: "user" as const, 
      text: messageText || `📷 Uploaded: ${fileToSend?.name}` 
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSelectedFile(null);
    setIsLoading(true);

    try {
      // FastAPI /chatbot/analyze expects FormData (not raw JSON)
      const formData = new FormData();
      // Always send a message, even if empty (backend needs either message or image)
      formData.append("message", messageText || "");
      if (fileToSend) {
        formData.append("image", fileToSend);
      }
      if (sessionId) {
        formData.append("session_id", sessionId);
      }

      console.log("Sending request to backend...", {
        message: messageText,
        hasImage: !!fileToSend,
        sessionId: sessionId
      });

      const res = await fetch("http://127.0.0.1:8000/chatbot/analyze", {
        method: "POST",
        body: formData,
      });

      console.log("Response status:", res.status, res.statusText);

      if (!res.ok) {
        const errorText = await res.text();
        console.error("Backend error response:", errorText);
        throw new Error(`HTTP error! status: ${res.status} - ${errorText}`);
      }

      const data = await res.json();
      console.log("Backend response:", data);

      // --- 4️⃣ Handle error responses from backend
      if (data.error) {
        throw new Error(`Backend error: ${data.error}`);
      }

      // --- 5️⃣ Update session ID if backend returned a new one
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem("chatbot_session_id", data.session_id);
      }

      // --- 6️⃣ Handle different response types
      let botMessage = data.message || "Hmm, I'm not sure yet!";
      
      // Handle combined recommendations
      if (data.combined_recommendations && data.final_recommendation) {
        botMessage += "\n\n**Recommended Products:**\n";
        data.combined_recommendations.forEach((rec: any, index: number) => {
          botMessage += `${index + 1}. ${rec.Step || rec.Product || 'Product'}\n`;
        });
      }

      // Handle clarification requests
      if (data.need_clarification && data.options) {
        botMessage += `\n\n**Options:** ${data.options.join(", ")}`;
      }

      setMessages((prev) => [
        ...prev,
        { sender: "bot" as const, text: botMessage },
      ]);
    } catch (err) {
      console.error("Error:", err);
      let errorMessage = "Error connecting to chatbot. Please try again.";
      
      if (err instanceof Error) {
        if (err.message.includes("Failed to fetch")) {
          errorMessage = "Cannot connect to backend. Please make sure the server is running.";
        } else if (err.message.includes("HTTP error")) {
          errorMessage = `Backend error: ${err.message}`;
        } else {
          errorMessage = `Error: ${err.message}`;
        }
      }
      
      setMessages((prev) => [
        ...prev,
        { sender: "bot" as const, text: errorMessage },
      ]);
    } finally {
      setIsLoading(false);
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
            <strong>{m.sender === "user" ? "You" : "Bot"}:</strong> 
            <div style={{ 
              whiteSpace: "pre-wrap", 
              marginTop: "5px",
              padding: "8px",
              backgroundColor: m.sender === "user" ? "#e3f2fd" : "#f5f5f5",
              borderRadius: "8px",
              display: "inline-block",
              maxWidth: "80%"
            }}>
              {m.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ textAlign: "left", marginBottom: "10px" }}>
            <strong>Bot:</strong> 
            <div style={{ 
              padding: "8px",
              backgroundColor: "#f5f5f5",
              borderRadius: "8px",
              display: "inline-block"
            }}>
              Thinking...
            </div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            style={{ 
              padding: "8px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontSize: "12px"
            }}
            placeholder="Upload an image..."
          />
          <div style={{ display: "flex", gap: "8px" }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              style={{ flex: 1, padding: "12px", border: "1px solid #ddd", borderRadius: "4px" }}
            />
            <button 
              onClick={() => handleSend()} 
              disabled={isLoading}
              style={{
                background: isLoading ? "#ccc" : "#6c63ff",
                color: "white",
                border: "none",
                padding: "12px 20px",
                borderRadius: "4px",
                cursor: isLoading ? "not-allowed" : "pointer"
              }}
            >
              {isLoading ? "..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
