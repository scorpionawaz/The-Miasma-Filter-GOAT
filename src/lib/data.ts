export type Stream = {
  id: string;
  title: string;
  user: string;
  userAvatar: string;
  thumbnailUrl: string;
  category: string;
  viewers: number;
  isLive: boolean;
  tags: string[];
  description: string;
};

export const streams: Stream[] = [
  {
    id: '1',
    title: 'Epic Gameplay Finals',
    user: 'GamerX',
    userAvatar: 'https://picsum.photos/id/1005/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream1/600/400',
    category: 'Gaming',
    viewers: 12500,
    isLive: true,
    tags: ['eSports', 'Tournament', 'Finals'],
    description: 'The grand finals of the annual eSports tournament. Watch as the best players battle it out for the championship title. High-stakes action and expert commentary.'
  },
  {
    id: '2',
    title: 'Live from the Red Carpet',
    user: 'CelebWatch',
    userAvatar: 'https://picsum.photos/id/1011/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream2/600/400',
    category: 'Entertainment',
    viewers: 7800,
    isLive: true,
    tags: ['Celebrity', 'Fashion', 'Awards'],
    description: 'Exclusive live coverage from the movie premiere red carpet. Get the first look at celebrity fashion, interviews, and behind-the-scenes moments.'
  },
  {
    id: '3',
    title: 'Breaking News: Global Summit',
    user: 'NewsNetwork',
    userAvatar: 'https://picsum.photos/id/1025/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream3/600/400',
    category: 'News',
    viewers: 23000,
    isLive: true,
    tags: ['Politics', 'World News', 'Live Report'],
    description: 'Live reporting from the Global Leaders Summit. We bring you real-time updates, analysis, and interviews with key figures on the world stage.'
  },
  {
    id: '4',
    title: 'Acoustic Cafe Sessions',
    user: 'MusicLover',
    userAvatar: 'https://picsum.photos/id/1040/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream4/600/400',
    category: 'Music',
    viewers: 4200,
    isLive: true,
    tags: ['Acoustic', 'Live Music', 'Chill'],
    description: 'Relax and unwind with our weekly acoustic music session. Featuring talented artists performing their original songs and soulful covers in an intimate setting.'
  },
  {
    id: '5',
    title: 'Procreate Masterclass',
    user: 'ArtByAlice',
    userAvatar: 'https://picsum.photos/id/1045/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream5/600/400',
    category: 'Art',
    viewers: 1500,
    isLive: true,
    tags: ['Digital Art', 'Tutorial', 'Creative'],
    description: 'Join professional artist Alice as she demonstrates advanced techniques in Procreate. Learn how to create stunning digital illustrations from scratch. Q&A session included!'
  },
  {
    id: '6',
    title: 'Exploring the Wilderness',
    user: 'AdventureSeeker',
    userAvatar: 'https://picsum.photos/id/1054/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream6/600/400',
    category: 'Travel',
    viewers: 3800,
    isLive: true,
    tags: ['Hiking', 'Nature', 'Adventure'],
    description: 'Embark on a virtual journey through breathtaking landscapes. Today, we are hiking the majestic mountain trails, discovering hidden waterfalls and wildlife.'
  },
  {
    id: '7',
    title: 'Startup Pitch Battle',
    user: 'TechCruncher',
    userAvatar: 'https://picsum.photos/id/1062/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream7/600/400',
    category: 'Tech',
    viewers: 9100,
    isLive: true,
    tags: ['Startups', 'Innovation', 'Business'],
    description: 'Watch the next generation of entrepreneurs pitch their groundbreaking ideas to a panel of venture capitalists. Who will secure the funding?'
  },
  {
    id: '8',
    title: 'Gourmet Cooking at Home',
    user: 'ChefLeo',
    userAvatar: 'https://picsum.photos/id/1080/100/100',
    thumbnailUrl: 'https://picsum.photos/seed/stream8/600/400',
    category: 'Cooking',
    viewers: 2700,
    isLive: true,
    tags: ['Food', 'Recipe', 'Cuisine'],
    description: 'Learn to cook a 3-course gourmet meal with ChefLeo, right from your kitchen. Tonight\'s menu features classic Italian dishes with a modern twist.'
  },
];

// This is a simple in-memory store for the live stream media stream.
// In a real application, you would use a proper media server (e.g., using WebRTC).
export const liveStreamStore: { 
    stream: MediaStream | null,
    // --- WebRTC signaling placeholders ---
    // In a real app, this would be handled by a WebSocket/signaling server
    offer: RTCSessionDescriptionInit | null,
    answer: RTCSessionDescriptionInit | null,
    streamerIceCandidates: RTCIceCandidate[],
    viewerIceCandidates: RTCIceCandidate[],
} = {
    stream: null,
    offer: null,
    answer: null,
    streamerIceCandidates: [],
    viewerIceCandidates: [],
};