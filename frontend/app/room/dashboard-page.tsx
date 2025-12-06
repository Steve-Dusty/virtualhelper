'use client';

import { useState, useEffect } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useParticipants,
  useTracks,
  ParticipantTile,
  ControlBar,
  TrackRefContext,
  useRoomContext,
} from '@livekit/components-react';
import '@livekit/components-styles';
import { Track } from 'livekit-client';

interface DashboardCache {
  summary: string;
  topics: string[];
  in_depth: string;
  last_updated: string;
}

interface QAItem {
  question: string;
  answer: string;
  timestamp: string;
}

function SmartDashboard() {
  const [cache, setCache] = useState<DashboardCache | null>(null);
  const [qaHistory, setQaHistory] = useState<QAItem[]>([]);
  const [selectedView, setSelectedView] = useState<'summary' | 'in-depth' | 'topics' | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const room = useRoomContext();

  useEffect(() => {
    if (!room) return;

    const handleData = (payload: Uint8Array, participant: any, kind: any, topic?: string) => {
      console.log(`📨 Received data on topic: ${topic}`);

      if (topic === 'lk.dashboard-cache') {
        // Pre-computed dashboard data
        try {
          const text = new TextDecoder().decode(payload);
          const data = JSON.parse(text) as DashboardCache;
          setCache(data);
          console.log('✅ Dashboard cache updated:', data);
        } catch (e) {
          console.error('❌ Error parsing cache:', e);
        }
      } else if (topic === 'lk.student-qa') {
        // Student Q&A
        try {
          const text = new TextDecoder().decode(payload);
          const qa = JSON.parse(text) as QAItem;
          setQaHistory(prev => [...prev, qa]);
          console.log('✅ Q&A added:', qa);
        } catch (e) {
          console.error('❌ Error parsing Q&A:', e);
        }
      } else if (topic === 'lk.transcription') {
        // Just log transcriptions to console
        const text = new TextDecoder().decode(payload);
        console.log('📝 Transcription:', text);
      }
    };

    room.on('dataReceived', handleData);
    return () => {
      room.off('dataReceived', handleData);
    };
  }, [room]);

  const renderContent = () => {
    if (!cache) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Analyzing classroom discussion...</p>
            <p className="text-gray-500 text-sm mt-2">AI is listening and learning...</p>
          </div>
        </div>
      );
    }

    if (!selectedView) {
      return (
        <div className="text-center text-gray-400 py-20">
          <div className="text-6xl mb-4">🎯</div>
          <p className="text-lg">Select a button above to get instant help!</p>
          <p className="text-sm text-gray-500 mt-2">All summaries are pre-computed for instant results</p>
        </div>
      );
    }

    if (selectedView === 'summary') {
      return (
        <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 p-6 rounded-lg">
          <h3 className="text-2xl font-bold text-blue-300 mb-4 flex items-center gap-2">
            <span>📊</span> Quick Summary
          </h3>
          <p className="text-lg leading-relaxed">{cache.summary}</p>
          <div className="mt-4 text-xs text-gray-500">
            Last updated: {new Date(cache.last_updated).toLocaleTimeString()}
          </div>
        </div>
      );
    }

    if (selectedView === 'in-depth') {
      return (
        <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700/50 p-6 rounded-lg">
          <h3 className="text-2xl font-bold text-purple-300 mb-4 flex items-center gap-2">
            <span>📚</span> In-Depth Explanation
          </h3>
          <p className="text-lg leading-relaxed">{cache.in_depth}</p>
          <div className="mt-4 text-xs text-gray-500">
            Last updated: {new Date(cache.last_updated).toLocaleTimeString()}
          </div>
        </div>
      );
    }

    if (selectedView === 'topics') {
      return (
        <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-700/50 p-6 rounded-lg">
          <h3 className="text-2xl font-bold text-green-300 mb-4 flex items-center gap-2">
            <span>💡</span> Topics Being Discussed
          </h3>
          {selectedTopic ? (
            <div>
              <button
                onClick={() => setSelectedTopic(null)}
                className="text-sm text-green-400 hover:text-green-300 mb-4"
              >
                ← Back to topics
              </button>
              <div className="bg-green-950/50 p-4 rounded">
                <h4 className="text-xl font-semibold mb-2">{selectedTopic}</h4>
                <p className="text-gray-300">
                  This topic is being discussed in the current conversation. Check the summary and in-depth explanation for more details!
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {cache.topics.length === 0 ? (
                <p className="text-gray-400">No topics identified yet...</p>
              ) : (
                cache.topics.map((topic, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedTopic(topic)}
                    className="w-full bg-green-950/50 hover:bg-green-900/50 p-4 rounded-lg text-left transition border border-green-700/30 hover:border-green-600"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">📌</span>
                      <span className="text-lg">{topic}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="h-full bg-gray-900 text-white flex flex-col">
      {/* Dashboard Header */}
      <div className="bg-gradient-to-r from-purple-900 to-blue-900 p-4 border-b border-gray-700">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span>🎯</span> AI Learning Dashboard
        </h2>
        <p className="text-sm text-gray-300 mt-1">
          {cache ? '⚡ Instant results - pre-computed every 5 seconds' : 'Initializing...'}
        </p>
      </div>

      {/* Action Buttons */}
      <div className="p-4 border-b border-gray-700 bg-gray-800/50">
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => setSelectedView('summary')}
            disabled={!cache}
            className={`p-4 rounded-lg font-semibold transition ${
              selectedView === 'summary'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
            } ${!cache && 'opacity-50 cursor-not-allowed'}`}
          >
            <div className="text-2xl mb-1">📊</div>
            <div className="text-sm">Summarize</div>
          </button>

          <button
            onClick={() => setSelectedView('in-depth')}
            disabled={!cache}
            className={`p-4 rounded-lg font-semibold transition ${
              selectedView === 'in-depth'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
            } ${!cache && 'opacity-50 cursor-not-allowed'}`}
          >
            <div className="text-2xl mb-1">📚</div>
            <div className="text-sm">In-Depth</div>
          </button>

          <button
            onClick={() => {
              setSelectedView('topics');
              setSelectedTopic(null);
            }}
            disabled={!cache}
            className={`p-4 rounded-lg font-semibold transition ${
              selectedView === 'topics'
                ? 'bg-green-600 text-white'
                : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
            } ${!cache && 'opacity-50 cursor-not-allowed'}`}
          >
            <div className="text-2xl mb-1">💡</div>
            <div className="text-sm">Topics</div>
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {renderContent()}

        {/* Q&A History */}
        {qaHistory.length > 0 && (
          <div className="mt-8">
            <h3 className="text-xl font-bold text-yellow-300 mb-4 flex items-center gap-2">
              <span>❓</span> Recent Questions & Answers
            </h3>
            <div className="space-y-3">
              {qaHistory.slice(-5).reverse().map((qa, idx) => (
                <div key={idx} className="bg-yellow-900/20 border border-yellow-700/50 p-4 rounded-lg">
                  <div className="font-semibold text-yellow-200 mb-2">Q: {qa.question}</div>
                  <div className="text-gray-300 pl-4 border-l-2 border-yellow-600">A: {qa.answer}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    {new Date(qa.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ClassroomLayout() {
  const participants = useParticipants();
  const tracks = useTracks([Track.Source.Camera, Track.Source.Microphone]);

  const teacher = participants.find((p) => p.identity.toLowerCase().includes('teacher'));
  const students = participants.filter((p) => !p.identity.toLowerCase().includes('teacher'));

  const teacherTracks = tracks.filter((track) => track.participant.identity === teacher?.identity);
  const studentTracks = tracks.filter((track) =>
    students.some((s) => s.identity === track.participant.identity)
  );

  return (
    <div className="h-screen flex bg-gray-900">
      {/* Left side - Video */}
      <div className="flex-1 flex flex-col">
        {/* Students bar at top */}
        <div className="bg-gray-800 p-2 flex gap-2 overflow-x-auto justify-center" style={{ height: '150px' }}>
          {studentTracks.map((track) => (
            <TrackRefContext.Provider value={track} key={track.participant.identity}>
              <div style={{ minWidth: '200px', width: '200px' }}>
                <ParticipantTile />
              </div>
            </TrackRefContext.Provider>
          ))}
        </div>

        {/* Teacher main stage */}
        <div className="flex-1 p-4 flex items-center justify-center">
          {teacher && teacherTracks.length > 0 ? (
            <TrackRefContext.Provider value={teacherTracks[0]}>
              <div className="w-full h-full max-w-6xl">
                <ParticipantTile />
              </div>
            </TrackRefContext.Provider>
          ) : (
            <div className="text-white text-2xl">Waiting for teacher...</div>
          )}
        </div>

        {/* Controls at bottom */}
        <div className="bg-gray-800 p-4">
          <ControlBar />
        </div>
      </div>

      {/* Right side - Smart Dashboard */}
      <div className="w-96 border-l border-gray-700">
        <SmartDashboard />
      </div>
    </div>
  );
}

export default function DashboardRoomPage() {
  const [token, setToken] = useState('');

  const handleJoin = async (selectedRole: 'teacher' | 'student') => {
    try {
      const username =
        selectedRole === 'teacher' ? 'Teacher' : `Student-${Math.random().toString(36).substring(7)}`;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/token?room=main-room&username=${username}&role=${selectedRole}`
      );

      if (!response.ok) throw new Error('Failed to get token');

      const data = await response.json();
      setToken(data.token);
    } catch (err) {
      console.error('Failed to connect:', err);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-gray-900">
        <div className="bg-gray-800/90 backdrop-blur p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-700">
          <div className="text-center mb-6">
            <div className="text-6xl mb-4">🎯</div>
            <h1 className="text-3xl font-bold mb-2 text-white">Smart Learning Dashboard</h1>
            <p className="text-gray-400 text-sm">AI-powered instant help for students</p>
          </div>
          <div className="space-y-4">
            <button
              onClick={() => handleJoin('teacher')}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium py-4 px-4 rounded-lg text-lg transition"
            >
              👨‍🏫 Join as Teacher
            </button>
            <button
              onClick={() => handleJoin('student')}
              className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-medium py-4 px-4 rounded-lg text-lg transition"
            >
              👨‍🎓 Join as Student
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen">
      <LiveKitRoom
        video={true}
        audio={true}
        token={token}
        serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
        data-lk-theme="default"
        style={{ height: '100%' }}
      >
        <ClassroomLayout />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}
