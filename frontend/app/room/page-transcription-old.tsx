'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useParticipants,
  useTracks,
  ParticipantTile,
  ControlBar,
  TrackRefContext,
  useRoomContext,
  useDataChannel,
} from '@livekit/components-react';
import '@livekit/components-styles';
import { Track } from 'livekit-client';

interface Transcription {
  id: string;
  text: string;
  participantIdentity: string;
  isFinal: boolean;
  timestamp: number;
}

function TranscriptionDisplay() {
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
  const room = useRoomContext();

  useEffect(() => {
    if (!room) {
      console.log('❌ Room not available yet');
      return;
    }

    console.log('✅ Room available, setting up data handler');

    const handleData = (payload: Uint8Array, participant: any, kind: any, topic?: string) => {
      console.log('🔔 Data received:', { topic, participantId: participant?.identity });

      if (topic === 'lk.transcription') {
        try {
          const text = new TextDecoder().decode(payload);
          console.log('📝 Transcription text:', text);

          const transcription: Transcription = {
            id: `${Date.now()}-${Math.random()}`,
            text,
            participantIdentity: participant?.identity || 'Agent',
            isFinal: true,
            timestamp: Date.now(),
          };

          setTranscriptions(prev => [...prev, transcription]);
        } catch (e) {
          console.error('❌ Error parsing transcription:', e);
        }
      }
    };

    room.on('dataReceived', handleData);
    console.log('✅ Data handler registered');

    return () => {
      room.off('dataReceived', handleData);
      console.log('🧹 Data handler cleaned up');
    };
  }, [room]);

  return (
    <div className="h-full bg-gray-900 text-white p-4 overflow-y-auto">
      <h3 className="text-xl font-bold mb-4 sticky top-0 bg-gray-900 pb-2">
        📝 Live Transcription
      </h3>
      <div className="space-y-3">
        {transcriptions.length === 0 ? (
          <p className="text-gray-400 italic">Waiting for speech...</p>
        ) : (
          transcriptions.map((t) => (
            <div
              key={t.id}
              className={`p-3 rounded-lg ${
                t.isFinal ? 'bg-gray-800' : 'bg-gray-700/50'
              }`}
            >
              <div className="text-xs text-gray-400 mb-1">
                {t.participantIdentity} • {new Date(t.timestamp).toLocaleTimeString()}
              </div>
              <div className="text-sm">{t.text}</div>
            </div>
          ))
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
              <div className="text-sm mt-2">
                {participants.length > 0 && `Found ${participants.length} participant(s)`}
              </div>
            </div>
          )}
        </div>

        {/* Controls at bottom */}
        <div className="bg-gray-800 p-4">
          <ControlBar />
        </div>
      </div>

      {/* Right side - Transcription */}
      <div className="w-96 border-l border-gray-700">
        <TranscriptionDisplay />
      </div>
    </div>
  );
}

export default function RoomPage() {
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
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
          <h1 className="text-2xl font-bold mb-6 text-center">Join Classroom</h1>
          <div className="space-y-4">
            <button
              onClick={() => handleJoin('teacher')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-4 px-4 rounded-lg text-lg"
            >
              Join as Teacher
            </button>
            <button
              onClick={() => handleJoin('student')}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-4 px-4 rounded-lg text-lg"
            >
              Join as Student
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
