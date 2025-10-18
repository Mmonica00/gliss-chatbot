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
              marginBottom: "15px",
              display: "flex",
              flexDirection: m.sender === "user" ? "row-reverse" : "row",
              alignItems: "flex-start",
              gap: "8px"
            }}
          >
            {/* Avatar */}
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: m.sender === "user" ? "#6c63ff" : "#4caf50",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              fontSize: "14px",
              fontWeight: "bold",
              flexShrink: 0
            }}>
              {m.sender === "user" ? "👤" : "🤖"}
            </div>
            
            {/* Message bubble */}
            <div style={{ 
              maxWidth: "70%",
              display: "flex",
              flexDirection: "column",
              alignItems: m.sender === "user" ? "flex-end" : "flex-start"
            }}>
              <div style={{ 
                whiteSpace: "pre-wrap", 
                padding: "12px 16px",
                backgroundColor: m.sender === "user" ? "#6c63ff" : "#f5f5f5",
                color: m.sender === "user" ? "white" : "#333",
                borderRadius: m.sender === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                wordWrap: "break-word"
              }}>
                {m.text}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{
            marginBottom: "15px",
            display: "flex",
            flexDirection: "row",
            alignItems: "flex-start",
            gap: "8px"
          }}>
            {/* Bot Avatar */}
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "#4caf50",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              fontSize: "14px",
              fontWeight: "bold",
              flexShrink: 0
            }}>
              🤖
            </div>
            
            {/* Loading bubble */}
            <div style={{ 
              maxWidth: "70%",
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start"
            }}>
              <div style={{ 
                padding: "12px 16px",
                backgroundColor: "#f5f5f5",
                color: "#333",
                borderRadius: "18px 18px 18px 4px",
                boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                <div style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  backgroundColor: "#4caf50",
                  animation: "pulse 1.5s ease-in-out infinite"
                }}></div>
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "100%" }}>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            style={{ 
              width: "100%",
              padding: "8px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontSize: "12px",
              boxSizing: "border-box"
            }}
            placeholder="Upload an image..."
          />
          <div style={{ display: "flex", gap: "8px", width: "100%" }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              style={{ 
                flex: 1, 
                padding: "12px", 
                border: "1px solid #ddd", 
                borderRadius: "4px",
                boxSizing: "border-box"
              }}
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
                cursor: isLoading ? "not-allowed" : "pointer",
                whiteSpace: "nowrap"
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
