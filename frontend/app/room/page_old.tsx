'use client';

import { useState } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useParticipants,
  useTracks,
  ParticipantTile,
  ControlBar,
  TrackRefContext,
} from '@livekit/components-react';
import '@livekit/components-styles';
import { Track } from 'livekit-client';

function ClassroomLayout() {
  const participants = useParticipants();
  const tracks = useTracks([Track.Source.Camera, Track.Source.Microphone]);

  // Debug logging
  console.log('All participants:', participants.map(p => ({
    identity: p.identity,
    metadata: p.metadata
  })));

  const teacher = participants.find((p) => {
    console.log('Checking participant:', p.identity, 'metadata:', p.metadata);
    return p.identity === 'Teacher' || p.identity.includes('Teacher');
  });

  const students = participants.filter((p) => {
    return p.identity !== 'Teacher' && !p.identity.includes('Teacher');
  });

  console.log('Teacher found:', teacher?.identity);
  console.log('Students:', students.map(s => s.identity));

  const teacherTracks = tracks.filter((track) => {
    const isTeacher = track.participant.identity === teacher?.identity;
    console.log('Track:', track.participant.identity, 'is teacher?', isTeacher);
    return isTeacher;
  });

  const studentTracks = tracks.filter((track) => {
    return students.some((s) => s.identity === track.participant.identity);
  });

  console.log('Teacher tracks:', teacherTracks.length);
  console.log('Student tracks:', studentTracks.length);

  return (
    <div className="h-screen flex flex-col bg-gray-900">
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
