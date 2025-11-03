import Image from 'next/image';
import Link from 'next/link';
import type { Stream } from '@/lib/data';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Eye } from 'lucide-react';

type StreamCardProps = {
  stream: Stream;
};

export function StreamCard({ stream }: StreamCardProps) {
  return (
    <Link href={`/stream/${stream.id}`}>
      <Card className="hover:border-primary transition-all duration-300 transform hover:-translate-y-1 hover:shadow-2xl hover:shadow-primary/20 overflow-hidden">
        <CardContent className="p-0">
          <div className="relative">
            <Image
              src={stream.thumbnailUrl}
              alt={stream.title}
              width={600}
              height={400}
              className="aspect-video object-cover"
              data-ai-hint="stream thumbnail"
            />
            <Badge className="absolute top-2 left-2 bg-primary text-primary-foreground">
              {stream.category}
            </Badge>
            <div className="absolute top-2 right-2 flex items-center gap-1 bg-black/50 text-white text-xs px-2 py-1 rounded-full">
              <Eye className="w-3 h-3"/>
              <span>{Intl.NumberFormat('en-US', { notation: 'compact' }).format(stream.viewers)}</span>
            </div>
            {stream.isLive && (
              <div className="absolute bottom-2 left-2 flex items-center gap-2">
                <Badge variant="destructive" className="flex items-center gap-1.5">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                  </span>
                  LIVE
                </Badge>
              </div>
            )}
          </div>
          <div className="p-4 flex gap-4">
            <Avatar>
              <AvatarImage src={stream.userAvatar} />
              <AvatarFallback>{stream.user.charAt(0)}</AvatarFallback>
            </Avatar>
            <div className="overflow-hidden">
              <h3 className="font-semibold truncate text-white">{stream.title}</h3>
              <p className="text-sm text-muted-foreground truncate">{stream.user}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
