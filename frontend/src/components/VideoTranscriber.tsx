import React, { useState } from 'react';
import { useMutation, useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../api/client';

interface VideoHistory {
  video_id: string;
  video_title: string;
  last_interaction: string;
  thumbnail_url: string;
}

interface QueryHistory {
  question: string;
  answer: string;
  timestamp: string;
}

interface VideoDetails {
  video_id: string;
  video_title: string;
  thumbnail_url: string;
  created_at: string;
  status: string;
}

export default function VideoTranscriber() {
  const [videoUrl, setVideoUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const navigate = useNavigate();

  // Fetch video history
  const { data: videoHistory, isLoading: isLoadingHistory } = useQuery<VideoHistory[]>(
    'videoHistory',
    async () => {
      const response = await api.get('/videos/history');
      return response.data;
    }
  );

  // Fetch query history for selected video
  const { data: queryHistory, isLoading: isLoadingQueries } = useQuery<QueryHistory[]>(
    ['queryHistory', selectedVideoId],
    async () => {
      if (!selectedVideoId) return [];
      const response = await api.get(`/videos/${selectedVideoId}/queries`);
      return response.data;
    },
    {
      enabled: !!selectedVideoId,
    }
  );

  // Add query for video details
  const { data: videoDetails, isLoading: isLoadingDetails } = useQuery<VideoDetails>(
    ['videoDetails', selectedVideoId],
    async () => {
      if (!selectedVideoId) return null;
      console.log('Fetching video details for:', selectedVideoId);
      const response = await api.get(`/videos/${selectedVideoId}`);
      console.log('Video details response:', response.data);
      return response.data;
    },
    {
      enabled: !!selectedVideoId,
    }
  );

  const transcribeMutation = useMutation(
    async (url: string) => {
      const response = await api.post('/transcript/transcribe', { 
        video_url: url  // Changed from 'url' to 'video_url' to match backend
      });
      return response.data;
    }
  );

  const askQuestionMutation = useMutation(
    async ({ videoId, question }: { videoId: string; question: string }) => {
      const response = await api.post('/query/ask-question', {
        video_id: videoId,
        question: question,
        username: localStorage.getItem('username')  // Changed from user_id to username
      });
      return response.data;
    }
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await transcribeMutation.mutateAsync(videoUrl);
      // Extract video ID and set as selected
      const videoId = videoUrl.split('v=')[1];
      setSelectedVideoId(videoId);
    } catch (error) {
      console.error('Error transcribing video:', error);
    }
  };

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (!selectedVideoId) {
        throw new Error('No video selected');
      }
      const result = await askQuestionMutation.mutateAsync({
        videoId: selectedVideoId,
        question,
      });
      setAnswer(result.answer);
      setQuestion(''); // Clear question input after asking
    } catch (error) {
      console.error('Error asking question:', error);
    }
  };

  const handleLogout = () => {
    try {
      localStorage.clear();
      delete api.defaults.headers.common['Authorization'];
      window.location.href = '/login';
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  const handleVideoSelect = (videoId: string) => {
    setSelectedVideoId(videoId);
    setVideoUrl(''); // Clear new video input when selecting existing video
  };

  console.log('Current video details:', videoDetails);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Fixed header with logout */}
      <div className="fixed top-0 left-0 right-0 bg-white shadow-sm z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Video AI Assistant</h1>
          <button
            onClick={handleLogout}
            className="bg-white hover:bg-gray-100 text-gray-700 font-semibold py-2 px-4 border border-gray-300 rounded shadow-sm transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main content with proper spacing from fixed header */}
      <div className="max-w-5xl mx-auto px-4 pt-20 pb-8">
        {/* Video History Section */}
        {!selectedVideoId && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-800">Your Videos</h2>
            </div>

            {isLoadingHistory ? (
              <div className="flex justify-center py-8">
                <div className="animate-pulse text-gray-500">Loading videos...</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {videoHistory?.map((video) => (
                  <div
                    key={video.video_id}
                    onClick={() => handleVideoSelect(video.video_id)}
                    className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden cursor-pointer"
                  >
                    <div className="aspect-w-16 aspect-h-9">
                      <img
                        src={video.thumbnail_url}
                        alt={video.video_title}
                        className="object-cover w-full h-full"
                      />
                    </div>
                    <div className="p-4">
                      <h3 className="font-medium text-gray-900 line-clamp-2 mb-2">
                        {video.video_title}
                      </h3>
                      <p className="text-sm text-gray-500">
                        Last interaction: {new Date(video.last_interaction).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* New Video Form */}
            <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Process New Video</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <input
                    type="text"
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter YouTube URL"
                  />
                </div>
                <button
                  type="submit"
                  disabled={transcribeMutation.isLoading}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {transcribeMutation.isLoading ? 'Processing...' : 'Process Video'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Selected Video Section */}
        {selectedVideoId && (
          <div className="max-w-3xl mx-auto space-y-6">
            <button
              onClick={() => setSelectedVideoId(null)}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Back to all videos
            </button>

            {/* Video Details Card */}
            {isLoadingDetails ? (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <p>Loading video details...</p>
              </div>
            ) : videoDetails ? (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="h-48 overflow-hidden">
                  <img
                    src={videoDetails.thumbnail_url}
                    alt={videoDetails.video_title}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    {videoDetails.video_title}
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      Added {new Date(videoDetails.created_at).toLocaleDateString()}
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Status: {videoDetails.status}
                    </div>
                    <a 
                      href={`https://youtube.com/watch?v=${videoDetails.video_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center text-blue-600 hover:text-blue-800"
                    >
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z" />
                      </svg>
                      Watch on YouTube
                    </a>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Query Form */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Ask a Question</h3>
              <form onSubmit={handleAskQuestion} className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter your question"
                />
                <button
                  type="submit"
                  disabled={askQuestionMutation.isLoading}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {askQuestionMutation.isLoading ? '...' : 'Ask'}
                </button>
              </form>
            </div>

            {/* Latest Answer */}
            {answer && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-3">Latest Answer</h2>
                <div className="prose prose-blue max-w-none">
                  <ReactMarkdown>
                    {answer}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* Query History */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Previous Questions</h3>
              {isLoadingQueries ? (
                <div>Loading questions...</div>
              ) : (
                <div className="space-y-6">
                  {queryHistory?.map((query, index) => (
                    <div key={index} className="border-l-4 border-gray-200 pl-4">
                      <p className="font-medium text-gray-900">Q: {query.question}</p>
                      <div className="mt-2 prose prose-blue max-w-none">
                        <ReactMarkdown>
                          {query.answer}
                        </ReactMarkdown>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        {new Date(query.timestamp).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 