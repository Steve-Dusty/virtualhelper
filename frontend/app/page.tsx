'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Sparkles, Video, Brain, Zap, Users, BarChart, BookOpen, Rocket } from 'lucide-react';

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 100,
      },
    },
  };

  const floatVariants = {
    animate: {
      y: [0, -20, 0],
      transition: {
        duration: 6,
        repeat: Infinity,
        ease: 'easeInOut' as const,
      },
    },
  };

  const features = [
    {
      icon: Video,
      title: 'Real-Time Video Streaming',
      description: 'Crystal-clear HD video streaming with ultra-low latency for seamless virtual interactions',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: Brain,
      title: 'AI-Powered Insights',
      description: 'Smart summaries and topic extraction powered by cutting-edge AI models',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Sparkles,
      title: 'Animated Explanations',
      description: 'Generate stunning mathematical animations on-demand with Manim integration',
      color: 'from-violet-500 to-purple-500',
    },
    {
      icon: Zap,
      title: 'Instant Summaries',
      description: 'Real-time transcription and intelligent summarization every 5 seconds',
      color: 'from-amber-500 to-orange-500',
    },
    {
      icon: Users,
      title: 'Multi-User Collaboration',
      description: 'Support for teachers and multiple students with role-based interactions',
      color: 'from-green-500 to-emerald-500',
    },
    {
      icon: BarChart,
      title: 'Learning Analytics',
      description: 'Track engagement, comprehension, and progress with detailed insights',
      color: 'from-rose-500 to-red-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0f] via-[#1a0a2e] to-[#0f0a1a] relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-purple-600/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 -left-40 w-[500px] h-[500px] bg-blue-600/25 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute bottom-20 right-1/3 w-80 h-80 bg-pink-600/30 rounded-full blur-3xl animate-pulse delay-500" />
        <div className="absolute top-1/4 right-1/4 w-64 h-64 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-700" />
      </div>

      {/* Header */}
      <motion.header
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 100 }}
        className="glass-card border-b sticky top-0 z-50 backdrop-blur-2xl"
      >
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <motion.div
            className="flex items-center gap-3"
            whileHover={{ scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center shadow-lg glow">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-purple-400">
                VirtualHelper
              </h1>
              <p className="text-xs text-muted-foreground">AI-Powered Virtual Assistance</p>
            </div>
          </motion.div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" className="hover-lift">
              About
            </Button>
            <Button variant="ghost" size="sm" className="hover-lift">
              Features
            </Button>
            <Link href="/room">
              <Button className="gradient-primary border-0 shadow-lg glow hover-lift">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 relative z-10">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid lg:grid-cols-2 gap-12 items-center"
        >
          <div className="space-y-6">
            <motion.div variants={itemVariants}>
              <Badge className="gradient-primary border-0 text-white hover:scale-105 transition-transform">
                <Rocket className="w-3 h-3 mr-1" />
                Next-Generation Virtual Platform
              </Badge>
            </motion.div>
            <motion.h2
              variants={itemVariants}
              className="text-6xl font-bold text-foreground leading-tight"
            >
              Revolutionize Learning with{' '}
              <span className="text-purple-400">
                AI Intelligence
              </span>
            </motion.h2>
            <motion.p variants={itemVariants} className="text-xl text-muted-foreground leading-relaxed">
              Experience the future of education with real-time AI summaries, instant animated
              explanations, and seamless video collaboration. All powered by cutting-edge technology.
            </motion.p>
            <motion.div variants={itemVariants} className="flex gap-4">
              <Link href="/room">
                <Button size="lg" className="h-14 px-8 text-base gradient-primary border-0 shadow-xl glow hover-lift">
                  <Sparkles className="w-4 h-4 mr-2" />
                  Launch Platform
                </Button>
              </Link>
              <Button
                size="lg"
                variant="outline"
                className="h-14 px-8 text-base glass-card hover-lift"
              >
                <Video className="w-4 h-4 mr-2" />
                Watch Demo
              </Button>
            </motion.div>
            <motion.div variants={itemVariants} className="flex items-center gap-8 pt-4">
              <div>
                <p className="text-3xl font-bold text-purple-400">
                  10k+
                </p>
                <p className="text-sm text-muted-foreground">Active Users</p>
              </div>
              <div className="h-12 w-px bg-border"></div>
              <div>
                <p className="text-3xl font-bold text-purple-400">
                  500+
                </p>
                <p className="text-sm text-muted-foreground">Educators</p>
              </div>
              <div className="h-12 w-px bg-border"></div>
              <div>
                <p className="text-3xl font-bold text-purple-400">
                  99%
                </p>
                <p className="text-sm text-muted-foreground">Satisfaction</p>
              </div>
            </motion.div>
          </div>

          {/* Animated demo card */}
          <motion.div variants={floatVariants} animate="animate" className="relative">
            <div className="absolute inset-0 gradient-primary rounded-3xl blur-3xl opacity-40 animate-pulse"></div>
            <div className="relative glass-card rounded-2xl shadow-2xl p-8 border border-purple-500/30">
              <div className="space-y-4">
                <motion.div
                  className="flex items-center justify-between pb-4 border-b border-border/50"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 gradient-primary rounded-full ring-4 ring-purple-500/20"></div>
                    <div>
                      <p className="font-semibold text-foreground">Dr. Alex Rivera</p>
                      <p className="text-sm text-muted-foreground">Advanced Mathematics</p>
                    </div>
                  </div>
                  <Badge className="bg-green-500/30 text-green-300 hover:bg-green-500/30 ring-2 ring-green-500/50">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
                    Live
                  </Badge>
                </motion.div>
                <div className="space-y-3">
                  <motion.div
                    className="glass-card rounded-lg p-4 border-l-2 border-purple-500/50"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 }}
                  >
                    <div className="flex items-start gap-2">
                      <Brain className="w-4 h-4 text-purple-400 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-foreground mb-1">AI Summary</p>
                        <p className="text-sm text-muted-foreground">
                          Exploring quantum mechanics and wave-particle duality principles...
                        </p>
                      </div>
                    </div>
                  </motion.div>
                  <motion.div
                    className="glass-card rounded-lg p-4 border-l-2 border-purple-500/50"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.9 }}
                  >
                    <div className="flex items-start gap-2">
                      <Users className="w-4 h-4 text-purple-400 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-foreground mb-1">Student Question</p>
                        <p className="text-sm text-muted-foreground">
                          How does quantum entanglement work?
                        </p>
                      </div>
                    </div>
                  </motion.div>
                  <motion.div
                    className="glass-card rounded-lg p-4 border-l-2 border-purple-500/50"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.1 }}
                  >
                    <div className="flex items-start gap-2">
                      <Sparkles className="w-4 h-4 text-purple-400 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground mb-2">
                          AI Generated Animation
                        </p>
                        <div className="w-full h-24 gradient-primary rounded-lg flex items-center justify-center shadow-lg glow cursor-pointer hover:scale-105 transition-transform">
                          <div className="text-white text-sm font-medium flex items-center gap-2">
                            <Video className="w-4 h-4" />
                            Play Animation
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-6 py-20 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <Badge className="gradient-primary border-0 text-white hover:scale-105 transition-transform mb-4">
            <Zap className="w-3 h-3 mr-1" />
            Powerful Features
          </Badge>
          <h3 className="text-5xl font-bold text-foreground mb-4">
            Everything You Need for Modern Education
          </h3>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Comprehensive tools designed to enhance learning and teaching experiences
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, idx) => (
            <motion.div key={idx} variants={itemVariants}>
              <Card className="glass-card hover-lift h-full group cursor-pointer">
                <CardHeader>
                  <div
                    className={`w-14 h-14 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform`}
                  >
                    <feature.icon className="w-7 h-7 text-white" />
                  </div>
                  <CardTitle className="text-xl group-hover:text-purple-400 transition-colors">
                    {feature.title}
                  </CardTitle>
                  <CardDescription className="text-base">{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6 py-20 relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <Card className="gradient-primary text-white overflow-hidden relative border-0 shadow-2xl">
            <div className="absolute inset-0 opacity-20 animate-gradient bg-gradient-to-r from-transparent via-white to-transparent bg-[length:200%_200%]"></div>
            <CardContent className="relative py-16 px-8 text-center">
              <Badge className="bg-white/20 text-white hover:bg-white/30 mb-4 border-white/30 ring-2 ring-white/20">
                <Rocket className="w-3 h-3 mr-1" />
                Ready to Get Started?
              </Badge>
              <h3 className="text-5xl font-bold mb-4">
                Join Thousands Transforming Education
              </h3>
              <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
                Start using VirtualHelper today and experience the future of learning
              </p>
              <div className="flex gap-4 justify-center">
                <Link href="/room">
                  <Button
                    size="lg"
                    className="bg-white text-purple-600 hover:bg-white/90 h-14 px-8 text-base shadow-xl hover-lift font-semibold"
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Start Free Trial
                  </Button>
                </Link>
                <Button
                  size="lg"
                  variant="outline"
                  className="h-14 px-8 text-base border-white/40 text-white hover:bg-white/10 backdrop-blur-xl"
                >
                  <BookOpen className="w-4 h-4 mr-2" />
                  Schedule Demo
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="glass-card border-t relative z-10">
        <div className="container mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center shadow-lg glow">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold text-purple-400">
                  VirtualHelper
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Revolutionizing education with AI-powered virtual assistance
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Demo
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Careers
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Privacy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Terms
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-primary transition-colors">
                    Security
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-border/50 text-center text-sm text-muted-foreground">
            <p>&copy; 2024 VirtualHelper. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
