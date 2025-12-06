# Frontend Integration Guide - Two Panel Design

## Overview
The agent now supports two distinct interaction modes for a cleaner, less cramped UI:

### LEFT PANEL: Dashboard Analytics
- Pre-computed summaries
- Current topics
- In-depth explanations
- Updates every 5 seconds automatically

### RIGHT PANEL: Private AI Chat
- Student asks questions to AI only
- AI responds automatically
- Private conversation (only visible to student)
- More flexible, personal tutoring

---

## Implementation

### 1. Ask AI Button (Private AI Chat)

```typescript
// When student clicks "Ask AI" button and speaks
async function askAI(questionText: string) {
  const payload = {
    question: questionText,
    studentIdentity: room.localParticipant.identity
  };

  // Send to agent via data channel
  await room.localParticipant.publishData(
    new TextEncoder().encode(JSON.stringify(payload)),
    { topic: 'lk.private-ai-question', reliable: true }
  );
}
```

### 2. Listen for Private AI Responses (Right Panel)

```typescript
// Listen for AI responses
room.on('dataReceived', (payload, participant, kind, topic) => {
  if (topic === 'lk.private-ai-response') {
    const data = JSON.parse(new TextDecoder().decode(payload));

    // Display in right panel chat UI
    addToAIChatPanel({
      question: data.question,
      answer: data.answer,
      timestamp: data.timestamp
    });
  }
});
```

### 3. Ask Entire Class Button (Public Mode)

```typescript
// When student clicks "Ask Class" button
// Just use normal audio transcription - no special handling needed
// The agent will transcribe and broadcast to everyone
// AI will NOT auto-respond in this mode
```

### 4. Dashboard Updates (Left Panel)

```typescript
// Listen for dashboard cache updates
room.on('dataReceived', (payload, participant, kind, topic) => {
  if (topic === 'lk.dashboard-cache') {
    const data = JSON.parse(new TextDecoder().decode(payload));

    // Update left panel
    updateDashboard({
      summary: data.summary,
      topics: data.topics,
      inDepth: data.in_depth
    });
  }
});
```

---

## UI Layout Example

```
┌─────────────────────────────────────────────────────────────┐
│                        Class Room                            │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                   │
│   LEFT PANEL             │   RIGHT PANEL                     │
│   Dashboard Analytics    │   Private AI Chat                 │
│                          │                                   │
│   📊 Summary:            │   💬 You: "What is X?"           │
│   Currently learning...  │                                   │
│                          │   🤖 AI: "X is..."               │
│   🎯 Topics:             │                                   │
│   - Topic 1              │   💬 You: "How do I solve Y?"    │
│   - Topic 2              │                                   │
│                          │   🤖 AI: "To solve Y..."         │
│   📖 In-depth:           │                                   │
│   Detailed explanation   │   [Ask AI] 🎤                    │
│                          │   [Ask Class] 🎤                 │
│   [Generate Summary]     │                                   │
│   [Show Topics]          │                                   │
│                          │                                   │
└──────────────────────────┴──────────────────────────────────┘
```

---

## Data Flow

### Private AI Chat (Right Panel)
1. Student clicks "Ask AI" button → Records question
2. Frontend sends via `lk.private-ai-question`
3. Agent generates answer
4. Agent sends back via `lk.private-ai-response` (destination_identities = [student])
5. Right panel displays conversation

### Ask Entire Class (Public)
1. Student clicks "Ask Class" button → Records audio
2. Agent transcribes via normal audio track
3. Transcription broadcast to everyone via `lk.transcription`
4. AI does NOT respond automatically
5. Teacher/students can respond naturally

### Dashboard (Left Panel)
1. Agent pre-computes every 5 seconds
2. Agent publishes via `lk.dashboard-cache`
3. All participants receive updates
4. Left panel displays analytics

---

## Benefits

✅ **Less Cramped**: Two distinct panels for different purposes
✅ **Private Tutoring**: Students get personalized AI help
✅ **Public Participation**: Normal classroom interaction preserved
✅ **Better UX**: Clear separation of concerns
✅ **Flexible**: Students choose when to ask AI vs class
