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
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';

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

interface AnimationRequest {
  requestId: string;
  question: string;
  status: 'pending' | 'processing' | 'complete' | 'error';
  videoId?: string;
  error?: string;
  timestamp: string;
}

interface AnimationHistory {
  videoId: string;
  question: string;
  timestamp: string;
}

function SmartDashboard() {
  const [cache, setCache] = useState<DashboardCache | null>(null);
  const [qaHistory, setQaHistory] = useState<QAItem[]>([]);
  const [selectedView, setSelectedView] = useState<'summary' | 'in-depth' | 'topics' | 'animations'>('summary');
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [animationInput, setAnimationInput] = useState('');
  const [currentAnimation, setCurrentAnimation] = useState<AnimationRequest | null>(null);
  const [animationHistory, setAnimationHistory] = useState<AnimationHistory[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const room = useRoomContext();

  useEffect(() => {
    if (!room) return;

    const handleData = (payload: Uint8Array, participant: any, kind: any, topic?: string) => {
      if (topic === 'lk.dashboard-cache') {
        try {
          const text = new TextDecoder().decode(payload);
          const data = JSON.parse(text) as DashboardCache;
          setCache(data);
        } catch (e) {
          console.error('Error parsing cache:', e);
        }
      } else if (topic === 'lk.student-qa') {
        try {
          const text = new TextDecoder().decode(payload);
          const qa = JSON.parse(text) as QAItem;
          setQaHistory(prev => [...prev, qa]);
        } catch (e) {
          console.error('Error parsing Q&A:', e);
        }
      } else if (topic === 'lk.animation-processing') {
        try {
          setCurrentAnimation(prev => prev ? { ...prev, status: 'processing' } : null);
        } catch (e) {
          console.error('Error parsing animation-processing:', e);
        }
      } else if (topic === 'lk.animation-complete') {
        try {
          const text = new TextDecoder().decode(payload);
          const data = JSON.parse(text);
          setCurrentAnimation(prev => prev ? { ...prev, status: 'complete', videoId: data.videoId } : null);
          setAnimationHistory(prev => [...prev, {
            videoId: data.videoId,
            question: currentAnimation?.question || '',
            timestamp: new Date().toISOString()
          }]);
          setIsGenerating(false);
        } catch (e) {
          console.error('Error parsing animation-complete:', e);
        }
      } else if (topic === 'lk.animation-error') {
        try {
          const text = new TextDecoder().decode(payload);
          const data = JSON.parse(text);
          setCurrentAnimation(prev => prev ? { ...prev, status: 'error', error: data.error } : null);
          setIsGenerating(false);
        } catch (e) {
          console.error('Error parsing animation-error:', e);
        }
      }
    };

    room.on('dataReceived', handleData);
    return () => {
      room.off('dataReceived', handleData);
    };
  }, [room, currentAnimation]);

  const handleGenerateAnimation = async () => {
    if (!animationInput.trim() || !room) return;

    const requestId = `${Date.now()}-${Math.random().toString(36).substring(7)}`;
    const newRequest: AnimationRequest = {
      requestId,
      question: animationInput,
      status: 'pending',
      timestamp: new Date().toISOString()
    };

    setCurrentAnimation(newRequest);
    setIsGenerating(true);

    try {
      const payload = JSON.stringify({
        question: animationInput,
        requestId
      });

      await room.localParticipant.publishData(
        new TextEncoder().encode(payload),
        { reliable: true, topic: 'lk.animation-request' }
      );
    } catch (error) {
      console.error('Failed to send animation request:', error);
      setCurrentAnimation(prev => prev ? { ...prev, status: 'error', error: 'Failed to send request' } : null);
      setIsGenerating(false);
    }
  };

  if (!cache) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <Card className="w-96 border-border shadow-lg">
          <CardHeader>
            <CardTitle className="text-center">Analyzing Session</CardTitle>
            <CardDescription className="text-center">AI is processing classroom discussion...</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full bg-background">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-foreground">Learning Assistant</h2>
              <p className="text-sm text-muted-foreground mt-0.5">Real-time AI-powered classroom insights</p>
            </div>
            <Badge variant="outline" className="text-xs">
              Live Session
            </Badge>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={selectedView} onValueChange={(v) => setSelectedView(v as any)} className="h-full flex flex-col">
            <div className="bg-card border-b border-border px-6">
              <TabsList className="bg-transparent border-none h-auto p-0">
                <TabsTrigger
                  value="summary"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-4 py-3"
                >
                  Summary
                </TabsTrigger>
                <TabsTrigger
                  value="in-depth"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-4 py-3"
                >
                  Detailed
                </TabsTrigger>
                <TabsTrigger
                  value="topics"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-4 py-3"
                >
                  Topics
                </TabsTrigger>
                <TabsTrigger
                  value="animations"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-4 py-3"
                >
                  Animations
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <TabsContent value="summary" className="mt-0">
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-lg">Quick Summary</CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Last updated: {new Date(cache.last_updated).toLocaleTimeString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground leading-relaxed">{cache.summary}</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="in-depth" className="mt-0">
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-lg">Detailed Explanation</CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Last updated: {new Date(cache.last_updated).toLocaleTimeString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground leading-relaxed">{cache.in_depth}</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="topics" className="mt-0">
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-lg">Discussion Topics</CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Key concepts being covered
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {selectedTopic ? (
                      <div>
                        <Button
                          variant="ghost"
                          onClick={() => setSelectedTopic(null)}
                          className="mb-4 text-sm"
                        >
                          ← Back to topics
                        </Button>
                        <div className="bg-accent p-4 rounded-lg border border-border">
                          <h4 className="font-semibold text-foreground mb-2">{selectedTopic}</h4>
                          <p className="text-muted-foreground text-sm">
                            This topic is being discussed in the current conversation. Check the summary and detailed explanation for more information.
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {cache.topics.length === 0 ? (
                          <p className="text-muted-foreground text-sm">No topics identified yet</p>
                        ) : (
                          cache.topics.map((topic, idx) => (
                            <button
                              key={idx}
                              onClick={() => setSelectedTopic(topic)}
                              className="w-full text-left bg-accent hover:bg-accent/80 border border-border rounded-lg p-4 transition-colors"
                            >
                              <span className="text-foreground font-medium">{topic}</span>
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="animations" className="mt-0 space-y-4">
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-lg">Generate Animation</CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Ask a question to generate a custom animated explanation
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      value={animationInput}
                      onChange={(e) => setAnimationInput(e.target.value)}
                      placeholder="E.g., Can you explain quadratic equations visually?"
                      className="min-h-[100px] resize-none"
                      disabled={isGenerating}
                    />
                    <Button
                      onClick={handleGenerateAnimation}
                      disabled={!animationInput.trim() || isGenerating}
                      className="w-full"
                    >
                      {isGenerating ? 'Generating...' : 'Generate Animation'}
                    </Button>
                  </CardContent>
                </Card>

                {currentAnimation && (
                  <Card className="border-border">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">Current Request</CardTitle>
                        <Badge
                          variant={
                            currentAnimation.status === 'complete' ? 'default' :
                            currentAnimation.status === 'error' ? 'destructive' :
                            'secondary'
                          }
                        >
                          {currentAnimation.status}
                        </Badge>
                      </div>
                      <CardDescription className="text-sm">{currentAnimation.question}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {currentAnimation.status === 'processing' && (
                        <div className="flex items-center gap-3 text-muted-foreground">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                          <span className="text-sm">Generating your animation...</span>
                        </div>
                      )}

                      {currentAnimation.status === 'error' && (
                        <Alert variant="destructive">
                          <AlertDescription className="text-sm">
                            Error: {currentAnimation.error}
                          </AlertDescription>
                        </Alert>
                      )}

                      {currentAnimation.status === 'complete' && currentAnimation.videoId && (
                        <div className="space-y-2">
                          <Separator />
                          <video
                            key={currentAnimation.videoId}
                            controls
                            autoPlay
                            className="w-full rounded-lg bg-black border border-border"
                            src={`${process.env.NEXT_PUBLIC_BACKEND_URL}/animation/${currentAnimation.videoId}`}
                          >
                            Your browser does not support video playback.
                          </video>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {animationHistory.length > 0 && (
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="text-base">Previous Animations</CardTitle>
                      <CardDescription className="text-xs text-muted-foreground">
                        Recently generated content
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {animationHistory.slice(-3).reverse().map((item, idx) => (
                        <div key={idx} className="space-y-2">
                          {idx > 0 && <Separator />}
                          <p className="text-sm text-foreground font-medium">{item.question}</p>
                          <video
                            controls
                            className="w-full rounded-lg bg-black border border-border"
                            src={`${process.env.NEXT_PUBLIC_BACKEND_URL}/animation/${item.videoId}`}
                          >
                            Your browser does not support video playback.
                          </video>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Q&A History */}
              {qaHistory.length > 0 && (
                <Card className="mt-4 border-border">
                  <CardHeader>
                    <CardTitle className="text-base">Recent Q&A</CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Student questions and AI responses
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {qaHistory.slice(-5).reverse().map((qa, idx) => (
                      <div key={idx} className="space-y-2">
                        {idx > 0 && <Separator />}
                        <div>
                          <p className="font-semibold text-foreground text-sm">Q: {qa.question}</p>
                          <p className="text-muted-foreground text-sm mt-2 pl-4 border-l-2 border-border">
                            A: {qa.answer}
                          </p>
                          <p className="text-xs text-muted-foreground/60 mt-2">
                            {new Date(qa.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>
          </Tabs>
        </div>
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
    <div className="h-screen flex bg-background">
      {/* Left side - Video */}
      <div className="flex-1 flex flex-col bg-[var(--surface-darker)]">
        {/* Students bar at top */}
        <div className="bg-[var(--surface-dark)] p-3 flex gap-3 overflow-x-auto" style={{ height: '140px' }}>
          {studentTracks.map((track) => (
            <TrackRefContext.Provider value={track} key={track.participant.identity}>
              <div style={{ minWidth: '180px', width: '180px' }}>
                <ParticipantTile />
              </div>
            </TrackRefContext.Provider>
          ))}
        </div>

        {/* Teacher main stage */}
        <div className="flex-1 p-6 flex items-center justify-center">
          {teacher && teacherTracks.length > 0 ? (
            <TrackRefContext.Provider value={teacherTracks[0]}>
              <div className="w-full h-full max-w-6xl">
                <ParticipantTile />
              </div>
            </TrackRefContext.Provider>
          ) : (
            <div className="text-white text-lg">Waiting for instructor...</div>
          )}
        </div>

        {/* Controls at bottom */}
        <div className="bg-[var(--surface-dark)] p-4 border-t border-border/20">
          <ControlBar />
        </div>
      </div>

      {/* Right side - Smart Dashboard */}
      <div className="w-[420px] border-l border-border bg-card">
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
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md border-border shadow-lg">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Learning Platform</CardTitle>
            <CardDescription>Select your role to join the session</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              onClick={() => handleJoin('teacher')}
              className="w-full h-12 text-base"
              variant="default"
            >
              Join as Instructor
            </Button>
            <Button
              onClick={() => handleJoin('student')}
              className="w-full h-12 text-base"
              variant="outline"
            >
              Join as Student
            </Button>
          </CardContent>
        </Card>
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
