'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-surface-base to-muted">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">L</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">LearnLive</h1>
              <p className="text-xs text-muted-foreground">AI-Powered Education</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm">About</Button>
            <Button variant="ghost" size="sm">Features</Button>
            <Link href="/room">
              <Button>
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <Badge className="bg-primary/10 text-primary hover:bg-primary/10">
              Next-Generation Learning Platform
            </Badge>
            <h2 className="text-5xl font-bold text-foreground leading-tight">
              Transform Your Classroom with{' '}
              <span className="bg-gradient-to-r from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] bg-clip-text text-transparent">
                AI Intelligence
              </span>
            </h2>
            <p className="text-xl text-muted-foreground leading-relaxed">
              Real-time transcription, instant summaries, and personalized animated explanations
              powered by cutting-edge AI. The future of education is here.
            </p>
            <div className="flex gap-4">
              <Link href="/room">
                <Button size="lg" className="h-14 px-8 text-base">
                  Launch Platform
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="h-14 px-8 text-base">
                Watch Demo
              </Button>
            </div>
            <div className="flex items-center gap-8 pt-4">
              <div>
                <p className="text-3xl font-bold text-foreground">10k+</p>
                <p className="text-sm text-muted-foreground">Active Students</p>
              </div>
              <div className="h-12 w-px bg-border"></div>
              <div>
                <p className="text-3xl font-bold text-foreground">500+</p>
                <p className="text-sm text-muted-foreground">Educators</p>
              </div>
              <div className="h-12 w-px bg-border"></div>
              <div>
                <p className="text-3xl font-bold text-foreground">99%</p>
                <p className="text-sm text-muted-foreground">Satisfaction</p>
              </div>
            </div>
          </div>
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-3xl blur-3xl opacity-20"></div>
            <div className="relative bg-card rounded-2xl shadow-2xl border border-border p-8">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-4 border-b border-border">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-full"></div>
                    <div>
                      <p className="font-semibold text-foreground">Professor Sarah Chen</p>
                      <p className="text-sm text-muted-foreground">Quantum Physics</p>
                    </div>
                  </div>
                  <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Live</Badge>
                </div>
                <div className="space-y-3">
                  <div className="bg-primary/5 rounded-lg p-4 border border-primary/20">
                    <p className="text-sm font-medium text-foreground mb-1">AI Summary</p>
                    <p className="text-sm text-muted-foreground">Discussing wave-particle duality and quantum superposition...</p>
                  </div>
                  <div className="bg-accent rounded-lg p-4 border border-border">
                    <p className="text-sm font-medium text-foreground mb-1">Student Question</p>
                    <p className="text-sm text-muted-foreground">How does quantum entanglement work?</p>
                  </div>
                  <div className="bg-accent rounded-lg p-4 border border-border">
                    <p className="text-sm font-medium text-foreground mb-1">AI Generated Animation</p>
                    <div className="w-full h-24 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center">
                      <div className="text-white text-sm font-medium">▶ Play Animation</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <Badge className="bg-primary/10 text-primary hover:bg-primary/10 mb-4">
            Powerful Features
          </Badge>
          <h3 className="text-4xl font-bold text-foreground mb-4">
            Everything You Need for Modern Education
          </h3>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Comprehensive tools designed to enhance learning and teaching experiences
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="border-border hover:shadow-lg transition-shadow bg-gradient-to-br from-card to-accent/30">
            <CardHeader>
              <div className="w-12 h-12 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <CardTitle className="text-xl">Real-Time Transcription</CardTitle>
              <CardDescription className="text-base">
                Automatic speech-to-text with speaker identification and timestamps
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-border hover:shadow-lg transition-shadow bg-gradient-to-br from-card to-accent/30">
            <CardHeader>
              <div className="w-12 h-12 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <CardTitle className="text-xl">AI-Powered Summaries</CardTitle>
              <CardDescription className="text-base">
                Instant lesson summaries and key topic extraction every 5 seconds
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-border hover:shadow-lg transition-shadow bg-gradient-to-br from-card to-accent/30">
            <CardHeader>
              <div className="w-12 h-12 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                </svg>
              </div>
              <CardTitle className="text-xl">Animated Explanations</CardTitle>
              <CardDescription className="text-base">
                Custom Manim animations generated on-demand for any concept
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-border hover:shadow-lg transition-shadow bg-gradient-to-br from-card to-accent/30">
            <CardHeader>
              <div className="w-12 h-12 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <CardTitle className="text-xl">Smart Q&A</CardTitle>
              <CardDescription className="text-base">
                Automatic question detection and contextual AI responses
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-border hover:shadow-lg transition-shadow bg-gradient-to-br from-card to-accent/30">
            <CardHeader>
              <div className="w-12 h-12 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <CardTitle className="text-xl">Learning Analytics</CardTitle>
              <CardDescription className="text-base">
                Track engagement, comprehension, and learning outcomes in real-time
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-border hover:shadow-lg transition-shadow bg-gradient-to-br from-card to-accent/30">
            <CardHeader>
              <div className="w-12 h-12 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <CardTitle className="text-xl">Personalized Learning</CardTitle>
              <CardDescription className="text-base">
                Tailored content and pacing based on individual student needs
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6 py-20">
        <Card className="border-border bg-gradient-to-br from-[var(--brand-gradient-from)] via-[var(--brand-gradient-to)] to-[var(--brand-gradient-from)] text-white overflow-hidden relative">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0" style={{backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 50px, rgba(255,255,255,0.1) 50px, rgba(255,255,255,0.1) 51px)'}}></div>
          </div>
          <CardContent className="relative py-16 px-8 text-center">
            <Badge className="bg-white/20 text-white hover:bg-white/20 mb-4 border-white/30">
              Ready to Get Started?
            </Badge>
            <h3 className="text-4xl font-bold mb-4">
              Join Thousands of Educators Transforming Learning
            </h3>
            <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
              Start using LearnLive today and experience the future of education
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/room">
                <Button size="lg" className="bg-white text-primary hover:bg-white/90 h-14 px-8 text-base">
                  Start Free Trial
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="h-14 px-8 text-base border-white/30 text-white hover:bg-white/10">
                Schedule Demo
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card">
        <div className="container mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-[var(--brand-gradient-from)] to-[var(--brand-gradient-to)] rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">L</span>
                </div>
                <span className="font-bold text-foreground">LearnLive</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Transforming education with AI-powered learning tools
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-primary transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">Demo</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-primary transition-colors">About</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-primary transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-border text-center text-sm text-muted-foreground">
            <p>&copy; 2024 LearnLive. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
