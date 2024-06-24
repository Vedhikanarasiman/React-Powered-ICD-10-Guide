import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [files, setFiles] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
  };

  const handleQuestionChange = (e) => {
    setQuestion(e.target.value);
  };

  const handleFileUpload = async () => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const response = await axios.post('http://localhost:8000/process-pdf/', formData);
      console.log(response.data.message);
    } catch (error) {
      console.error("File upload error: ", error);
      alert('Error uploading files');
    }
  };

  const handleAskQuestion = async () => {
    try {
      const response = await axios.post('http://localhost:8000/ask-question/', { question });
      console.log("Response: ", response.data);
      setAnswer(response.data.answer || "No answer returned");
    } catch (error) {
      console.error("Question processing error: ", error);
      console.log("Error details: ", error.response?.data);
      // Log the error to see its structure
      setAnswer(error.response?.data?.detail || 'Error getting answer');
    }
  };  
  
  return (
    <div className="container">
      <h1 className="app-title">ICD-10 Code Chat Assistant</h1>
      <div className="file-upload-section">
        <input type="file" multiple onChange={handleFileChange} />
        <button className="upload-button" onClick={handleFileUpload}>Upload and Process PDFs</button>
      </div>
      <div className="question-section">
        <input
          type="text"
          value={question}
          onChange={handleQuestionChange}
          className="question-input"
          placeholder="Ask a question"
        />
        <button className="ask-button" onClick={handleAskQuestion}>Ask</button>
      </div>
      <div className="answer-section">
        <h2>Answer:</h2>
        <p className="answer">{typeof answer === "string" ? answer : JSON.stringify(answer)}</p>
      </div>
    </div>
  );
}


export default App;
