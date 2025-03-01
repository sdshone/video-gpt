import React from 'react';
import { useQuery } from 'react-query';
import { getQueryHistory } from '../api/client';

interface QueryHistoryProps {
  videoId: string;
}

export default function QueryHistory({ videoId }: QueryHistoryProps) {
  const { data: history, isLoading, error } = useQuery(
    ['queryHistory', videoId],
    () => getQueryHistory(videoId)
  );

  if (isLoading) return <div>Loading history...</div>;
  if (error) return <div>Error loading history</div>;

  return (
    <div className="mt-6">
      <h2 className="text-xl font-semibold mb-4">Previous Questions</h2>
      <div className="space-y-4">
        {history?.map((interaction) => (
          <div key={interaction.id} className="border rounded-lg p-4">
            <p className="font-medium">Q: {interaction.question}</p>
            <p className="mt-2">A: {interaction.answer}</p>
            <p className="text-sm text-gray-500 mt-2">
              {new Date(interaction.created_at).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
} 