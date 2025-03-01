import { useState } from 'react';
import { useMutation, useQuery } from 'react-query';
import { transcribeVideo, getTranscriptionStatus, askQuestion } from '../api/client';
import toast from 'react-hot-toast';
import QueryHistory from './QueryHistory';

interface VideoTranscriberProps {
  onLogout: () => void;
}

export default function VideoTranscriber({ onLogout }: VideoTranscriberProps) {
  const [videoUrl, setVideoUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [question, setQuestion] = useState('');

  const transcribeMutation = useMutation(
    () => transcribeVideo(videoUrl),
    {
      onSuccess: (data) => {
        const id = videoUrl.split('v=')[1];
        setVideoId(id);
        toast.success('Transcription started!');
      },
      onError: () => {
        toast.error('Failed to start transcription');
      },
    }
  );

  const { data: status } = useQuery(
    ['transcriptionStatus', videoId],
    () => getTranscriptionStatus(videoId),
    {
      enabled: !!videoId,
      refetchInterval: (data) => 
        data?.status === 'completed' ? false : 5000,
    }
  );

  const askQuestionMutation = useMutation(
    () => askQuestion(videoId, question),
    {
      onSuccess: (data) => {
        toast.success('Got answer!');
      },
      onError: () => {
        toast.error('Failed to get answer');
      },
    }
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Video Transcriber</h1>
        <button
          onClick={onLogout}
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
        >
          Logout
        </button>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Transcribe Video</h2>
        <div className="flex gap-2">
          <input
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="Enter YouTube URL"
            className="flex-1 p-2 border rounded"
          />
          <button
            onClick={() => transcribeMutation.mutate()}
            disabled={transcribeMutation.isLoading}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Transcribe
          </button>
        </div>
      </div>

      {status && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Status: {status.status}</h3>
          {status.status === 'completed' && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about the video"
                  className="flex-1 p-2 border rounded"
                />
                <button
                  onClick={() => askQuestionMutation.mutate()}
                  disabled={askQuestionMutation.isLoading}
                  className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                >
                  Ask
                </button>
              </div>
              {askQuestionMutation.data && (
                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-semibold mb-2">Answer:</h4>
                  <p>{askQuestionMutation.data.answer}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Add query history */}
      {videoId && <QueryHistory videoId={videoId} />}
    </div>
  );
} 