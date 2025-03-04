import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import VideoTranscriber from './components/VideoTranscriber';
import { useEffect, useState } from 'react';
import Register from './components/Register';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  }, []);

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
              <Navigate to="/" replace /> : 
              <LoginPage />
          } 
        />
        <Route 
          path="/" 
          element={
            isAuthenticated ? 
              <VideoTranscriber /> : 
              <Navigate to="/login" replace />
          } 
        />
        <Route path="/register" element={<Register />} />
      </Routes>
    </Router>
  );
}

export default App;