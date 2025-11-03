"use client";

import React, { useRef, useCallback, useEffect, useState } from "react";
import Webcam from "react-webcam";
import { Camera } from "lucide-react";

// Gemini's output audio sample rate (playback)
// const AI_SAMPLE_RATE = 24000;


// Build dynamic WS URL using encoded path segments
// Example base: ws://<host>/ws/<roll>/<name>/<grade>/<subject>/<chapter>
const WS_URL = "ws://localhost:8080/ws/";

const videoConstraints = { width: 640, height: 480, facingMode: "user" };

export default function CameraPanel() {
  const [aiResponseText, setAiResponseText] = useState("");
  const [isStreamingActive, setIsStreamingActive] = useState(false);

  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const webSocket = useRef<WebSocket | null>(null);
  const mediaStream = useRef<MediaStream | null>(null);

  // User audio capture (upload) at 16 kHz
  const userAudioContext = useRef<AudioContext | null>(null);
  const userAudioProcessor = useRef<ScriptProcessorNode | null>(null);

  // AI audio playback at 24 kHz
  // const aiAudioContext = useRef<AudioContext | null>(null);
  // const aiAudioQueue = useRef<Int16Array[]>([]);
  // const isAiAudioPlaying = useRef(false);

  const streamVideoInterval = useRef<NodeJS.Timeout | null>(null);

  const sendVideoFrame = useCallback(() => {
    if (webSocket.current?.readyState === WebSocket.OPEN) {
      const canvas = canvasRef.current;
      const video = webcamRef.current?.video as HTMLVideoElement | undefined;
      if (!canvas || !video || video.readyState < video.HAVE_ENOUGH_DATA) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext("2d");
      if (!context) return;

      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Note: toDataURL has memory overhead; consider toBlob + FileReader for efficiency on large frames. [MDN] [web:6]
      const dataUrl = canvas.toDataURL("image/jpeg", 0.8); // [web:6]
      const base64Data = dataUrl.split(",")[1];

      webSocket.current.send(JSON.stringify({ type: "video", data: base64Data }));
    }
  }, []);

  const setupUserAudioStreaming = useCallback(() => {
    if (!mediaStream.current) return;

    // ScriptProcessorNode is deprecated; consider AudioWorkletNode for future-proofing. [MDN/Chrome] [web:2][web:4][web:11]
    userAudioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)({
      sampleRate: 16000,
    });

    const source = userAudioContext.current.createMediaStreamSource(mediaStream.current);
    userAudioProcessor.current = userAudioContext.current.createScriptProcessor(4096, 1, 1);
    source.connect(userAudioProcessor.current);
    userAudioProcessor.current.connect(userAudioContext.current.destination);

    userAudioProcessor.current.onaudioprocess = (event: AudioProcessingEvent) => {
      if (webSocket.current?.readyState === WebSocket.OPEN) {
        const float32Data = event.inputBuffer.getChannelData(0);
        const int16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
          const s = Math.max(-1, Math.min(1, float32Data[i]));
          int16Data[i] = s < 0 ? s * 32768 : s * 32767;
        }
        const base64Data = btoa(String.fromCharCode(...new Uint8Array(int16Data.buffer)));
        webSocket.current.send(JSON.stringify({ type: "audio", data: base64Data }));
      }
    };
  }, []);

  // Handle AI audio chunks (base64 of 16-bit PCM at 24 kHz)
  // const handleAiAudio = useCallback(
  //   (base64Data: string) => {
  //     const raw = atob(base64Data);
  //     const arr = new Uint8Array(raw.length);
  //     for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  //     const pcm = new Int16Array(arr.buffer);
  //     aiAudioQueue.current.push(pcm);
  //     if (!isAiAudioPlaying.current) playNextAiAudioChunk();
  //   },
  //   // eslint-disable-next-line react-hooks/exhaustive-deps
  //   []
  // );

  // const playNextAiAudioChunk = useCallback(() => {
  //   if (!aiAudioContext.current) return;
  //   const queue = aiAudioQueue.current;
  //   if (queue.length === 0) {
  //     isAiAudioPlaying.current = false;
  //     return;
  //   }
  //   isAiAudioPlaying.current = true;

  //   const pcm = queue.shift()!;
  //   const float32 = new Float32Array(pcm.length);
  //   for (let i = 0; i < pcm.length; i++) float32[i] = pcm[i] / 32768;

  //   const buffer = aiAudioContext.current.createBuffer(1, float32.length, AI_SAMPLE_RATE);
  //   buffer.copyToChannel(float32, 0);

  //   const source = aiAudioContext.current.createBufferSource();
  //   source.buffer = buffer;
  //   source.connect(aiAudioContext.current.destination);
  //   source.onended = () => playNextAiAudioChunk();
  //   source.start();
  // }, []);

  const stopStreaming = useCallback(() => {
    if (streamVideoInterval.current) {
      clearInterval(streamVideoInterval.current);
      streamVideoInterval.current = null;
    }
    if (webSocket.current && webSocket.current.readyState === WebSocket.OPEN) {
      webSocket.current.close();
      webSocket.current = null;
    }
    if (mediaStream.current) {
      mediaStream.current.getTracks().forEach((t) => t.stop());
      mediaStream.current = null;
    }
    if (userAudioProcessor.current) {
      userAudioProcessor.current.disconnect();
      userAudioProcessor.current = null;
    }
    if (userAudioContext.current && userAudioContext.current.state !== "closed") {
      userAudioContext.current.close();
      userAudioContext.current = null;
    }
    // if (aiAudioContext.current && aiAudioContext.current.state !== "closed") {
    //   aiAudioContext.current.close();
    //   aiAudioContext.current = null;
    // }

    setIsStreamingActive(false);
    setAiResponseText("");
    // aiAudioQueue.current = [];
    // isAiAudioPlaying.current = false;
  }, []);

  const startStreaming = useCallback(async () => {
    try {
      mediaStream.current = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });

      if (webcamRef.current?.video) {
        (webcamRef.current.video as any).srcObject = mediaStream.current;
      }

      webSocket.current = new WebSocket(WS_URL);

      webSocket.current.onopen = () => {
        setIsStreamingActive(true);

        // Initialize AI playback context at 24 kHz
        // aiAudioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        //   sampleRate: AI_SAMPLE_RATE,
        // });

        streamVideoInterval.current = setInterval(sendVideoFrame, 1000);
        setupUserAudioStreaming();
      };

      webSocket.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log(message);
          // if (message.type === "audio") {
          //   handleAiAudio(message.data);
          // } else 
          if (message.type === "text") {
            setAiResponseText((prev) => prev + message.data);
          } else {
            // Fallback to text accumulation if backend always sends data
            if (message?.data) setAiResponseText((prev) => prev + String(message.data));
          }
        } catch {
          // Non-JSON payloads ignored
        }
      };

      webSocket.current.onclose = () => {
        stopStreaming();
      };

      webSocket.current.onerror = () => {
        stopStreaming();
      };
    } catch (error) {
      stopStreaming();
    }
  }, [sendVideoFrame, setupUserAudioStreaming, stopStreaming]);

  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, [stopStreaming]);

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-md">
      {!isStreamingActive ? (
        <div className="w-full aspect-video bg-gray-900 rounded-lg flex flex-col items-center justify-center text-center p-4">
          <Camera className="h-16 w-16 text-gray-500 mb-4" />
          <p className="text-gray-400 mb-6">Click the button to start student verification.</p>
          <button
            onClick={startStreaming}
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Start Camera
          </button>
        </div>
      ) : (
        <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
          <Webcam
            ref={webcamRef}
            audio={false}
            muted={true}
            videoConstraints={videoConstraints}
            className="w-full h-full object-cover"
          />
          <canvas ref={canvasRef} className="hidden" />
          <div className="absolute top-2 left-1/2 -translate-x-1/2 px-3 py-1 bg-green-600 bg-opacity-70 text-white text-sm rounded-full flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isStreamingActive ? "bg-green-300 animate-pulse" : "bg-red-300"}`}></div>
            <span>{isStreamingActive ? "Direct Stream Active" : "Stream Inactive"}</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white p-3 text-sm max-h-32 overflow-y-auto">
            {aiResponseText || "Waiting for response..."}
          </div>
          <button
            onClick={stopStreaming}
            className="absolute top-2 right-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Stop
          </button>
        </div>
      )}
    </div>
  );
}
