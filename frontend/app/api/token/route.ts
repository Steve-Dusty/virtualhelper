import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const room = searchParams.get('room') || 'default-room';
  const username = searchParams.get('username') || `user-${Date.now()}`;

  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/token?room=${encodeURIComponent(
        room
      )}&username=${encodeURIComponent(username)}`
    );

    if (!response.ok) {
      throw new Error('Failed to get token from backend');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching token:', error);
    return NextResponse.json(
      { error: 'Failed to generate token' },
      { status: 500 }
    );
  }
}
