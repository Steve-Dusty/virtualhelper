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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Video,
  Brain,
  Users,
  Maximize2,
  Loader2,
  CheckCircle2,
  XCircle,
  BookOpen,
  Lightbulb,
  GraduationCap,
} from 'lucide-react';

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
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<{ id: string; question: string } | null>(null);
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

  const openVideoModal = (videoId: string, question: string) => {
    setSelectedVideo({ id: videoId, question });
    setVideoModalOpen(true);
  };

  if (!cache) {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-br from-[#0a0a0f] via-[#1a0a2e] to-[#0f0a1a]">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="w-96 glass-card border-white/40 shadow-2xl">
            <CardHeader className="text-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className="w-16 h-16 mx-auto mb-4 gradient-primary rounded-2xl flex items-center justify-center shadow-lg glow"
              >
                <Brain className="w-8 h-8 text-white" />
              </motion.div>
              <CardTitle className="text-xl text-purple-400">
                Analyzing Session
              </CardTitle>
              <CardDescription>AI is processing classroom discussion...</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center pb-6">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                className="w-12 h-12 rounded-full border-4 border-purple-500/30 border-t-purple-600"
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gradient-to-br from-[#0a0a0f] via-[#1a0a2e] to-[#0f0a1a]">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="glass-card border-b px-6 py-4 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center shadow-lg glow">
                <GraduationCap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-purple-400">
                  Learning Assistant
                </h2>
                <p className="text-sm text-muted-foreground mt-0.5">Real-time AI-powered insights</p>
              </div>
            </div>
            <Badge className="gradient-primary border-0 text-white shadow-lg">
              <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></div>
              Live Session
            </Badge>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={selectedView} onValueChange={(v) => setSelectedView(v as any)} className="h-full flex flex-col">
            <div className="glass-card border-b px-6 backdrop-blur-xl">
              <TabsList className="bg-transparent border-none h-auto p-0">
                <TabsTrigger
                  value="summary"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-purple-600 rounded-none px-4 py-3 hover-lift"
                >
                  <BookOpen className="w-4 h-4 mr-2" />
                  Summary
                </TabsTrigger>
                <TabsTrigger
                  value="in-depth"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-purple-600 rounded-none px-4 py-3 hover-lift"
                >
                  <Brain className="w-4 h-4 mr-2" />
                  Detailed
                </TabsTrigger>
                <TabsTrigger
                  value="topics"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-purple-600 rounded-none px-4 py-3 hover-lift"
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  Topics
                </TabsTrigger>
                <TabsTrigger
                  value="animations"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-purple-600 rounded-none px-4 py-3 hover-lift"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Animations
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <AnimatePresence mode="wait">
                <TabsContent value="summary" className="mt-0">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <Card className="glass-card border-white/40 hover-lift">
                      <CardHeader>
                        <div className="flex items-center gap-2">
                          <BookOpen className="w-5 h-5 text-purple-600" />
                          <CardTitle className="text-lg">Quick Summary</CardTitle>
                        </div>
                        <CardDescription className="text-xs text-muted-foreground">
                          Last updated: {new Date(cache.last_updated).toLocaleTimeString()}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-foreground leading-relaxed">{cache.summary}</p>
                      </CardContent>
                    </Card>
                  </motion.div>
                </TabsContent>

                <TabsContent value="in-depth" className="mt-0">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <Card className="glass-card hover-lift">
                      <CardHeader>
                        <div className="flex items-center gap-2">
                          <Brain className="w-5 h-5 text-purple-400" />
                          <CardTitle className="text-lg">Detailed Explanation</CardTitle>
                        </div>
                        <CardDescription className="text-xs text-muted-foreground">
                          Last updated: {new Date(cache.last_updated).toLocaleTimeString()}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-foreground leading-relaxed">{cache.in_depth}</p>
                      </CardContent>
                    </Card>
                  </motion.div>
                </TabsContent>

                <TabsContent value="topics" className="mt-0">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <Card className="glass-card">
                      <CardHeader>
                        <div className="flex items-center gap-2">
                          <Lightbulb className="w-5 h-5 text-purple-400" />
                          <CardTitle className="text-lg">Discussion Topics</CardTitle>
                        </div>
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
                              className="mb-4 text-sm hover-lift"
                            >
                              ← Back to topics
                            </Button>
                            <div className="glass-card p-4 rounded-lg border-l-2 border-purple-500/50">
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
                                <motion.button
                                  key={idx}
                                  initial={{ opacity: 0, x: -20 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: idx * 0.1 }}
                                  onClick={() => setSelectedTopic(topic)}
                                  className="w-full text-left glass-card hover:bg-purple-900/20 rounded-lg p-4 transition-all hover-lift"
                                >
                                  <span className="text-foreground font-medium">{topic}</span>
                                </motion.button>
                              ))
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                </TabsContent>

                <TabsContent value="animations" className="mt-0 space-y-4">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <Card className="glass-card">
                      <CardHeader>
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-purple-400" />
                          <CardTitle className="text-lg">Generate Animation</CardTitle>
                        </div>
                        <CardDescription className="text-xs text-muted-foreground">
                          Ask a question to generate a custom animated explanation
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <Textarea
                          value={animationInput}
                          onChange={(e) => setAnimationInput(e.target.value)}
                          placeholder="E.g., Can you explain quadratic equations visually?"
                          className="min-h-[100px] resize-none glass-card border-white/40"
                          disabled={isGenerating}
                        />
                        <Button
                          onClick={handleGenerateAnimation}
                          disabled={!animationInput.trim() || isGenerating}
                          className="w-full gradient-primary border-0 shadow-lg glow hover-lift"
                        >
                          {isGenerating ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Generating...
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-4 h-4 mr-2" />
                              Generate Animation
                            </>
                          )}
                        </Button>
                      </CardContent>
                    </Card>

                    {currentAnimation && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                      >
                        <Card className="glass-card">
                          <CardHeader>
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-base">Current Request</CardTitle>
                              <Badge
                                className={
                                  currentAnimation.status === 'complete'
                                    ? 'bg-green-500/20 text-green-700 ring-2 ring-green-500/30'
                                    : currentAnimation.status === 'error'
                                    ? 'bg-red-500/20 text-red-700 ring-2 ring-red-500/30'
                                    : 'gradient-primary border-0 text-white'
                                }
                              >
                                {currentAnimation.status === 'complete' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                                {currentAnimation.status === 'error' && <XCircle className="w-3 h-3 mr-1" />}
                                {currentAnimation.status === 'processing' && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                                {currentAnimation.status}
                              </Badge>
                            </div>
                            <CardDescription className="text-sm">{currentAnimation.question}</CardDescription>
                          </CardHeader>
                          <CardContent>
                            {currentAnimation.status === 'processing' && (
                              <div className="flex items-center gap-3 text-muted-foreground">
                                <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                                <span className="text-sm">Generating your animation...</span>
                              </div>
                            )}

                            {currentAnimation.status === 'error' && (
                              <Alert variant="destructive" className="glass-card">
                                <XCircle className="w-4 h-4" />
                                <AlertDescription className="text-sm">
                                  Error: {currentAnimation.error}
                                </AlertDescription>
                              </Alert>
                            )}

                            {currentAnimation.status === 'complete' && currentAnimation.videoId && (
                              <div className="space-y-3">
                                <Separator />
                                <div className="relative group">
                                  <video
                                    key={currentAnimation.videoId}
                                    controls
                                    autoPlay
                                    className="w-full rounded-lg bg-black border border-white/30 shadow-xl"
                                    src={`${process.env.NEXT_PUBLIC_BACKEND_URL}/animation/${currentAnimation.videoId}`}
                                  >
                                    Your browser does not support video playback.
                                  </video>
                                  <Button
                                    onClick={() => openVideoModal(currentAnimation.videoId!, currentAnimation.question)}
                                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity glass-card"
                                    size="icon"
                                  >
                                    <Maximize2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    )}

                    {animationHistory.length > 0 && (
                      <Card className="glass-card">
                        <CardHeader>
                          <div className="flex items-center gap-2">
                            <Video className="w-5 h-5 text-purple-400" />
                            <CardTitle className="text-base">Previous Animations</CardTitle>
                          </div>
                          <CardDescription className="text-xs text-muted-foreground">
                            Recently generated content
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {animationHistory.slice(-3).reverse().map((item, idx) => (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: idx * 0.1 }}
                              className="space-y-2"
                            >
                              {idx > 0 && <Separator />}
                              <p className="text-sm text-foreground font-medium">{item.question}</p>
                              <div className="relative group">
                                <video
                                  controls
                                  className="w-full rounded-lg bg-black border border-white/30 shadow-lg hover-lift"
                                  src={`${process.env.NEXT_PUBLIC_BACKEND_URL}/animation/${item.videoId}`}
                                >
                                  Your browser does not support video playback.
                                </video>
                                <Button
                                  onClick={() => openVideoModal(item.videoId, item.question)}
                                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity glass-card"
                                  size="icon"
                                >
                                  <Maximize2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </motion.div>
                          ))}
                        </CardContent>
                      </Card>
                    )}
                  </motion.div>
                </TabsContent>
              </AnimatePresence>

              {/* Q&A History */}
              {qaHistory.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Card className="mt-4 glass-card border-purple-500/20 shadow-[0_0_20px_rgba(168,85,247,0.15)]">
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <Users className="w-5 h-5 text-purple-400" />
                        <CardTitle className="text-base">Recent Q&A</CardTitle>
                      </div>
                      <CardDescription className="text-xs text-muted-foreground">
                        Student questions and AI responses
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {qaHistory.slice(-5).reverse().map((qa, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="space-y-2"
                        >
                          {idx > 0 && <Separator />}
                          <div>
                            <p className="font-semibold text-foreground text-sm">Q: {qa.question}</p>
                            <p className="text-muted-foreground text-sm mt-2 pl-4 border-l-2 border-purple-500/30">
                              A: {qa.answer}
                            </p>
                            <p className="text-xs text-muted-foreground/60 mt-2">
                              {new Date(qa.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </motion.div>
                      ))}
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </div>
          </Tabs>
        </div>
      </div>

      {/* Video Modal */}
      <Dialog open={videoModalOpen} onOpenChange={setVideoModalOpen}>
        <DialogContent className="max-w-4xl glass-card p-0">
          <DialogHeader className="p-6 pb-0">
            <DialogTitle className="flex items-center gap-2">
              <Video className="w-5 h-5 text-purple-400" />
              {selectedVideo?.question}
            </DialogTitle>
            <DialogDescription>Generated Animation</DialogDescription>
          </DialogHeader>
          <div className="p-6 pt-4">
            {selectedVideo && (
              <video
                controls
                autoPlay
                className="w-full rounded-lg bg-black border border-white/30 shadow-2xl"
                src={`${process.env.NEXT_PUBLIC_BACKEND_URL}/animation/${selectedVideo.id}`}
              >
                Your browser does not support video playback.
              </video>
            )}
          </div>
        </DialogContent>
      </Dialog>
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
    <div className="h-screen flex bg-gradient-to-br from-[#0a0a0f] via-[#1a0a2e] to-[#0f0a1a]">
      {/* Left side - Video */}
      <div className="flex-1 flex flex-col bg-gradient-to-br from-[var(--surface-darker)] to-[var(--surface-dark)]">
        {/* Students bar at top */}
        <div className="glass-card p-3 flex gap-3 overflow-x-auto border-b border-white/10 backdrop-blur-xl" style={{ height: '140px' }}>
          {studentTracks.map((track, idx) => (
            <motion.div
              key={track.participant.identity}
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              style={{ minWidth: '180px', width: '180px' }}
            >
              <TrackRefContext.Provider value={track}>
                <div className="rounded-lg overflow-hidden ring-2 ring-purple-500/30 hover:ring-purple-500/60 transition-all hover-lift">
                  <ParticipantTile />
                </div>
              </TrackRefContext.Provider>
            </motion.div>
          ))}
        </div>

        {/* Teacher main stage */}
        <div className="flex-1 p-6 flex items-center justify-center">
          {teacher && teacherTracks.length > 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="w-full h-full max-w-6xl"
            >
              <TrackRefContext.Provider value={teacherTracks[0]}>
                <div className="w-full h-full rounded-2xl overflow-hidden ring-4 ring-purple-500/30 shadow-2xl glow">
                  <ParticipantTile />
                </div>
              </TrackRefContext.Provider>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-white text-lg flex flex-col items-center gap-4"
            >
              <div className="w-16 h-16 gradient-primary rounded-2xl flex items-center justify-center shadow-lg glow animate-pulse">
                <Users className="w-8 h-8 text-white" />
              </div>
              <p>Waiting for instructor...</p>
            </motion.div>
          )}
        </div>

        {/* Controls at bottom */}
        <div className="glass-card p-4 border-t border-white/10 backdrop-blur-xl">
          <ControlBar />
        </div>
      </div>

      {/* Right side - Smart Dashboard */}
      <div className="w-[420px] border-l border-white/10 glass-card backdrop-blur-2xl">
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0a0a0f] via-[#1a0a2e] to-[#0f0a1a] relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-purple-600/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-1/2 -left-40 w-[500px] h-[500px] bg-blue-600/25 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-20 right-1/4 w-80 h-80 bg-pink-600/25 rounded-full blur-3xl animate-pulse" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10"
        >
          <Card className="w-full max-w-md glass-card shadow-2xl">
            <CardHeader className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 gradient-primary rounded-2xl flex items-center justify-center shadow-lg glow">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl text-purple-400">
                VirtualHelper
              </CardTitle>
              <CardDescription>Select your role to join the session</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={() => handleJoin('teacher')}
                className="w-full h-12 text-base gradient-primary border-0 shadow-lg glow hover-lift"
              >
                <GraduationCap className="w-4 h-4 mr-2" />
                Join as Instructor
              </Button>
              <Button
                onClick={() => handleJoin('student')}
                className="w-full h-12 text-base glass-card hover-lift"
                variant="outline"
              >
                <Users className="w-4 h-4 mr-2" />
                Join as Student
              </Button>
            </CardContent>
          </Card>
        </motion.div>
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
