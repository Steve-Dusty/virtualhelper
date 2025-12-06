import express from 'express';
import { AccessToken, RoomServiceClient, AgentDispatchClient } from 'livekit-server-sdk';
import dotenv from 'dotenv';
import cors from 'cors';
import fs from 'fs';

dotenv.config();

const app = express();
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Range'],
  exposedHeaders: ['Content-Range', 'Accept-Ranges'],
}));
app.use(express.json());

const PORT = process.env.PORT || 3001;
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
  throw new Error('LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in environment variables');
}

const roomService = new RoomServiceClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);
const agentDispatch = new AgentDispatchClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);

app.get('/token', async (req, res) => {
  try {
    const roomName = req.query.room || 'default-room';
    const participantName = req.query.username || `user-${Date.now()}`;
    const role = req.query.role || 'student';

    const at = new AccessToken(
      LIVEKIT_API_KEY,
      LIVEKIT_API_SECRET,
      {
        identity: participantName,
        ttl: '10m',
        metadata: JSON.stringify({ role }),
      }
    );

    at.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    const token = await at.toJwt();

    // Create room and dispatch agent automatically
    try {
      await roomService.createRoom({
        name: roomName,
        emptyTimeout: 300, // 5 minutes
        maxParticipants: 50,
      });
      console.log(`✅ Room created: ${roomName}`);
    } catch (e) {
      // Room might already exist, that's OK
      console.log('Room already exists:', e.message);
    }

    // Dispatch agent to the room
    try {
      const dispatch = await agentDispatch.createDispatch(roomName, '');
      console.log(`✅ Agent dispatched to room: ${roomName}`, dispatch);
    } catch (e) {
      console.error('Failed to dispatch agent:', e.message);
    }

    res.json({
      token,
      url: LIVEKIT_URL,
      roomName,
      participantName,
      role,
    });
  } catch (error) {
    console.error('Error generating token:', error);
    res.status(500).json({ error: 'Failed to generate token' });
  }
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

// Serve animation videos
app.get('/animation/:videoId', (req, res) => {
  try {
    const videoId = req.params.videoId;

    // Security: Validate videoId format (UUID-like)
    if (!/^[a-f0-9\-]{20,36}$/.test(videoId)) {
      return res.status(400).json({ error: 'Invalid video ID format' });
    }

    const videoPath = `/tmp/output_${videoId}.mp4`;

    // Check if file exists
    if (!fs.existsSync(videoPath)) {
      console.log(`❌ Video not found: ${videoPath}`);
      return res.status(404).json({ error: 'Video not found' });
    }

    const stat = fs.statSync(videoPath);
    const fileSize = stat.size;
    const range = req.headers.range;

    // Support video streaming with range requests
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
      const chunksize = (end - start) + 1;
      const file = fs.createReadStream(videoPath, { start, end });

      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mp4',
        'Access-Control-Allow-Origin': '*',
      });

      file.pipe(res);
    } else {
      // No range, send full file
      res.writeHead(200, {
        'Content-Length': fileSize,
        'Content-Type': 'video/mp4',
        'Access-Control-Allow-Origin': '*',
      });

      fs.createReadStream(videoPath).pipe(res);
    }

    console.log(`✅ Serving video: ${videoId}`);

  } catch (error) {
    console.error('Error serving video:', error);
    res.status(500).json({ error: 'Failed to serve video' });
  }
});

app.listen(PORT, () => {
  console.log(`LiveKit backend server listening on port ${PORT}`);
  console.log(`Token endpoint: http://localhost:${PORT}/token`);
  console.log(`LiveKit URL: ${LIVEKIT_URL}`);
});
