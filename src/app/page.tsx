"use client";
import Navbar from "@/components/Navbar";
import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Clapperboard, Eye, Star } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

// Define the Stream type
type Stream = {
  id: number;
  title: string;
  user: string;
  userAvatar: string;
  thumbnail: string;
  viewers: string;
  category: string;
};

// Mock for your existing StreamCard component (e.g., from '@/components/stream-card')
const StreamCard = ({
  stream,
  className,
}: {
  stream: Stream;
  className: string;
}) => (
  <Card
    className={`rounded-2xl overflow-hidden shadow-lg border-none ${className}`}
  >
    <div className="relative">
      <Image
        src={stream.thumbnail}
        alt={stream.title}
        width={400}
        height={225}
        className="w-full object-cover aspect-video"
        fill={undefined}
      />
      <div className="absolute top-2 left-2 bg-[#DC2626] text-white text-xs font-bold px-2 py-1 rounded-full">
        LIVE
      </div>
      <div className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded-md flex items-center gap-1">
        <Eye className="w-4 h-4" /> {stream.viewers}
      </div>
    </div>
    <CardContent className="p-4">
      <div className="flex items-start gap-3">
        <Avatar className="w-10 h-10 mt-1">
          <AvatarImage src={stream.userAvatar} />
          <AvatarFallback>{stream.user.charAt(0)}</AvatarFallback>
        </Avatar>
        <div>
          <h3 className="font-bold text-white text-lg truncate leading-tight">
            {stream.title}
          </h3>
          <p className="text-sm text-[#E2E8F0]">{stream.user}</p>
          <div className="mt-2">
            <span className="bg-[#2B6CB0] text-white text-xs font-semibold px-2.5 py-1 rounded-full">
              {stream.category}
            </span>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
);

// Mock Data
const streams = Array.from({ length: 9 }, (_, i) => ({
  id: i + 1,
  title:
    i === 0
      ? 'Conquering the Final Boss in "CyberDrift"'
      : `Exploring the Neon Jungles of Xylos - Part ${i}`,
  user: i === 0 ? "AlphaStreamer" : `GamerPro${i + 1}`,
  userAvatar: `https://i.pravatar.cc/150?u=user${i + 1}`,
  thumbnail: `https://picsum.photos/seed/${i + 1}/400/225`,
  viewers: `${(Math.random() * 20).toFixed(1)}k`,
  category: "Action RPG",
}));

// --- Your Homepage Component ---

export default function Home() {
  const featuredStream = streams[0];

  return (
    // Main container with the deep charcoal background and light gray body text
    <div className="bg-[#0F1419] text-[#E2E8F0] min-h-screen font-sans">
      {/* Navbar with requested margin */}
      <header className="pt-16 mx-4 md:mx-16">
        <Navbar />
      </header>

      <main className="container mx-auto p-4 md:p-8 space-y-12">
        {/* Hero Section */}
        <section className="relative w-full h-[50vh] rounded-2xl overflow-hidden">
          <Image
            src="https://picsum.photos/seed/hero/1600/900"
            alt="Featured stream"
            data-ai-hint="gameplay screenshot"
            fill
            className="object-cover"
            width={undefined}
            height={undefined}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent" />
          <div className="absolute bottom-0 left-0 p-4 md:p-8 text-white">
            <div className="flex items-center gap-4 mb-4">
              <Avatar className="w-16 h-16 border-4 border-[#2B6CB0]">
                <AvatarImage src={featuredStream.userAvatar} />
                <AvatarFallback>{featuredStream.user.charAt(0)}</AvatarFallback>
              </Avatar>
              <div>
                <h1 className="text-4xl lg:text-5xl font-bold tracking-tight text-white">
                  {featuredStream.title}
                </h1>
                <p className="text-lg text-[#E2E8F0]">{featuredStream.user}</p>
              </div>
            </div>
            <p className="max-w-2xl mb-6 text-lg hidden md:block">{`Join ${featuredStream.user} for an exciting live session. Don't miss out!`}</p>
            <Link href={`/stream/${featuredStream.id}`} className={undefined}>
              <Button
                size="lg"
                className="bg-[#2B6CB0] hover:bg-[#255a9a] text-white"
              >
                <Clapperboard className="mr-2 h-5 w-5" /> Watch Now
              </Button>
            </Link>
          </div>
        </section>

        {/* Live Now Section */}
        <section>
          <h2 className="text-3xl font-bold tracking-tight mb-6 text-white">
            Live Now
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {streams.slice(1, 5).map((stream) => (
              <StreamCard
                key={stream.id}
                stream={stream}
                className="bg-[#1A202C]"
              />
            ))}
          </div>
        </section>

        {/* Recommended For You Section */}
        <section>
          <h2 className="text-3xl font-bold tracking-tight mb-6 flex items-center text-white">
            <Star className="w-7 h-7 mr-3 text-[#2B6CB0]" />
            Recommended For You
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {streams.slice(5).map((stream) => (
              <StreamCard
                key={stream.id}
                stream={stream}
                className="bg-[#1A202C]"
              />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
