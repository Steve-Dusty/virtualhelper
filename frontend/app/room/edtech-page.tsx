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

interface Message {
  id: string;
  text: string;
  participantIdentity: string;
  timestamp: number;
  type: 'transcription' | 'helper' | 'qa';
}

function EdTechSidebar() {
  const [transcriptions, setTranscriptions] = useState<Message[]>([]);
  const [helpers, setHelpers] = useState<Message[]>([]);
  const [qaAnswers, setQaAnswers] = useState<Message[]>([]);
  const [activeTab, setActiveTab] = useState<'transcript' | 'ai-helper'>('transcript');
  const room = useRoomContext();

  useEffect(() => {
    if (!room) return;

    const handleData = (payload: Uint8Array, participant: any, kind: any, topic?: string) => {
      const text = new TextDecoder().decode(payload);
      const message: Message = {
        id: `${Date.now()}-${Math.random()}`,
        text,
        participantIdentity: participant?.identity || 'AI Agent',
        timestamp: Date.now(),
        type: 'transcription',
      };

      console.log(`📨 Received data on topic: ${topic}`);

      if (topic === 'lk.transcription') {
        // Raw transcription
        setTranscriptions(prev => [...prev, message]);
      } else if (topic === 'lk.helper') {
        // AI helper summary
        setHelpers(prev => [...prev, { ...message, type: 'helper' }]);
      } else if (topic === 'lk.qa') {
        // Q&A answer
        setQaAnswers(prev => [...prev, { ...message, type: 'qa' }]);
      }
    };

    room.on('dataReceived', handleData);
    return () => {
      room.off('dataReceived', handleData);
    };
  }, [room]);

  return (
    <div className="h-full bg-gray-900 text-white flex flex-col">
      {/* Tabs */}
      <div className="flex border-b border-gray-700">
        <button
          onClick={() => setActiveTab('transcript')}
          className={`flex-1 py-3 px-4 font-medium ${
            activeTab === 'transcript'
              ? 'bg-gray-800 text-white border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          📝 Transcription
        </button>
        <button
          onClick={() => setActiveTab('ai-helper')}
          className={`flex-1 py-3 px-4 font-medium ${
            activeTab === 'ai-helper'
              ? 'bg-gray-800 text-white border-b-2 border-purple-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          🤖 AI Helper
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'transcript' ? (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Live Transcription</h3>
            {transcriptions.length === 0 ? (
              <p className="text-gray-500 italic text-sm">Waiting for speech...</p>
            ) : (
              transcriptions.map((t) => (
                <div key={t.id} className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-400 mb-1">
                    {t.participantIdentity} • {new Date(t.timestamp).toLocaleTimeString()}
                  </div>
                  <div className="text-sm">{t.text}</div>
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {/* AI Helpers Section */}
            <div>
              <h3 className="text-sm font-semibold text-purple-400 mb-3 flex items-center gap-2">
                <span>💡</span> AI Explanations & Summaries
              </h3>
              {helpers.length === 0 ? (
                <p className="text-gray-500 italic text-sm">AI helpers will appear here...</p>
              ) : (
                <div className="space-y-3">
                  {helpers.map((h) => (
                    <div key={h.id} className="bg-purple-900/30 border border-purple-700/50 p-4 rounded-lg">
                      <div className="text-xs text-purple-300 mb-2">
                        {new Date(h.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="text-sm leading-relaxed">{h.text}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Q&A Section */}
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-blue-400 mb-3 flex items-center gap-2">
                <span>❓</span> Questions & Answers
              </h3>
              {qaAnswers.length === 0 ? (
                <p className="text-gray-500 italic text-sm">Q&A will appear here...</p>
              ) : (
                <div className="space-y-3">
                  {qaAnswers.map((qa) => (
                    <div key={qa.id} className="bg-blue-900/30 border border-blue-700/50 p-4 rounded-lg">
                      <div className="text-xs text-blue-300 mb-2">
                        AI Answer • {new Date(qa.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="text-sm leading-relaxed">{qa.text}</div>
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

function ClassroomLayout() {
  const participants = useParticipants();
  const tracks = useTracks([Track.Source.Camera, Track.Source.Microphone]);

  const teacher = participants.find((p) => {
    return p.identity === 'Teacher' || p.identity.includes('Teacher');
  });

  const students = participants.filter((p) => {
    return p.identity !== 'Teacher' && !p.identity.includes('Teacher');
  });

  const teacherTracks = tracks.filter((track) => {
    return track.participant.identity === teacher?.identity;
  });

  const studentTracks = tracks.filter((track) => {
    return students.some((s) => s.identity === track.participant.identity);
  });

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
            <div className="text-white text-2xl">
              Waiting for teacher to join...
            </div>
          )}
        </div>

        {/* Controls at bottom */}
        <div className="bg-gray-800 p-4">
          <ControlBar />
        </div>
      </div>

      {/* Right side - AI Sidebar */}
      <div className="w-96 border-l border-gray-700">
        <EdTechSidebar />
      </div>
    </div>
  );
}

export default function EdTechRoomPage() {
  const [token, setToken] = useState('');

  const handleJoin = async (selectedRole: 'teacher' | 'student') => {
    try {
      const username = selectedRole === 'teacher'
        ? 'Teacher'
        : `Student-${Math.random().toString(36).substring(7)}`;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/token?room=main-room&username=${username}&role=${selectedRole}`
      );

      if (!response.ok) {
        throw new Error('Failed to get token');
      }

      const data = await response.json();
      setToken(data.token);
    } catch (err) {
      console.error('Failed to connect:', err);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              🎓 AI-Powered Classroom
            </h1>
            <p className="text-gray-600 text-sm">
              With real-time transcription and AI assistance
            </p>
          </div>
          <div className="space-y-4">
            <button
              onClick={() => handleJoin('teacher')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-4 px-4 rounded-lg text-lg transition"
            >
              👨‍🏫 Join as Teacher
            </button>
            <button
              onClick={() => handleJoin('student')}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-4 px-4 rounded-lg text-lg transition"
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
