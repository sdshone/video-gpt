import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import Login from './components/Login';
import VideoTranscriber from './components/VideoTranscriber';
import toast from 'react-hot-toast';

const queryClient = new QueryClient();

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  );

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    queryClient.clear(); // Clear any cached queries
    toast.success('Logged out successfully');
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-100">
        <div className="max-w-4xl mx-auto p-4">
          {!isAuthenticated ? (
            <Login onSuccess={() => setIsAuthenticated(true)} />
          ) : (
            <VideoTranscriber onLogout={handleLogout} />
          )}
        </div>
      </div>
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;