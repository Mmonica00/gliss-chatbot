import "./index.css";
import Chatbot from "./components/Chatbot";

function App() {
  return (
    <div>
      <h1 style={{ 
        textAlign: "center", 
        marginTop: "20px",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        backgroundClip: "text",
        fontSize: "2.5rem",
        fontWeight: "700",
        marginBottom: "10px"
      }}>
        ✨ Gliss Hair Expert ✨
      </h1>
      <p style={{ 
        textAlign: "center", 
        color: "#666", 
        fontSize: "1.1rem",
        marginBottom: "20px",
        fontStyle: "italic"
      }}>
        🌟 Software for soft hair 🌟
      </p>
      <Chatbot />
    </div>
  );
}

export default App;
