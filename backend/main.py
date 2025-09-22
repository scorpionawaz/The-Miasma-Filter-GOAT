
# from checker import *
# # --- FastAPI Application ---
# app = FastAPI()
# audio_loop = AudioLoop()

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     print("WebSocket client connected.")
    
#     audio_loop.start()

#     async def receive_from_client():
#         """Handle incoming messages from the client."""
#         try:
#             while True:
#                 data = await websocket.receive_json()
#                 media_type = data.get("type")
                
#                 if media_type == "audio":
#                     audio_data = base64.b64decode(data['data'])
#                     await audio_loop.media_in_queue.put({"data": audio_data, "mime_type": "audio/pcm"})
#                 elif media_type == "video":
#                     image_data = data['data']
#                     await audio_loop.media_in_queue.put({"mime_type": "image/jpeg", "data": image_data})
#         except WebSocketDisconnect:
#             print("Client disconnected (receive task).")

#     async def send_to_client():
#         """Handle sending messages to the client."""
#         try:
#             while True:
#                 message = await audio_loop.browser_out_queue.get()
#                 await websocket.send_json(message)
#         except WebSocketDisconnect:
#             print("Client disconnected (send task).")

#     # Run both tasks concurrently
#     receive_task = asyncio.create_task(receive_from_client())
#     send_task = asyncio.create_task(send_to_client())

#     # Wait for either task to complete (which happens on disconnect)
#     done, pending = await asyncio.wait(
#         [receive_task, send_task],
#         return_when=asyncio.FIRST_COMPLETED,
#     )

#     # Clean up
#     for task in pending:
#         task.cancel()
#     audio_loop.stop()
#     print("WebSocket connection closed and session stopped.")

# if __name__ == "__main__":
#     print("Starting FastAPI server...")
#     uvicorn.run(app, host="127.0.0.1", port=8000)





# ============================================================================================================

#                                 # Checker funcationality
                            
# # --------------------------------------------------------------------------------------------------------------
# import os
# import asyncio
# import base64
# import io
# import pyaudio
# import traceback
# import argparse
# import json
# from google import genai
# from google.genai import types
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from starlette.websockets import WebSocketState
# import uvicorn

# # --- Keep your original Gemini AI and PyAudio setup ---
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# SEND_SAMPLE_RATE = 16000
# RECEIVE_SAMPLE_RATE = 24000 # This is the sample rate of the audio we'll get from Gemini
# CHUNK_SIZE = 1024
# MODEL = "models/gemini-2.0-flash-live-001"

# client = genai.Client(
#     http_options={"api_version": "v1beta"},
#     api_key="AIzaSyDAS7l4ju1cDGx5BjIS3qgb7Cx0X5LwtdY",
# )

# # --- Function call handler and tools definition ---
# def handle_function_call(function_call):
#     if function_call.name == "scoreupdater":
#         args = function_call.args
#         # Your database code here
#         # db.update_score(args['rollnumber'], args['score'], etc.)
#         print("Received a Function Call for scoreupdater:")
#         print(f"  Grade: {args.get('grade')}")
#         print(f"  Subject: {args.get('subject')}")
#         print(f"  Chapter Number: {args.get('chapternumber')}")
#         print(f"  Chapter Name: {args.get('chaptername')}")
#         print(f"  Roll Number: {args.get('rollnumber')}")
#         print(f"  Score: {args.get('score')}")
#         return {"success": True, "message": "Score updated successfully"}
#     return {"success": False, "message": "Unknown function call"}

# tools = [
#     types.Tool(
#         function_declarations=[
#             types.FunctionDeclaration(
#                 name="scoreupdater",
#                 description="updates the score of the Respective student after completing the exam",
#                 parameters=genai.types.Schema(
#                     type=genai.types.Type.OBJECT,
#                     required=["grade", "subject", "chapternumber", "rollnumber", "score"],
#                     properties={
#                         "grade": genai.types.Schema(
#                             type=genai.types.Type.INTEGER,
#                         ),
#                         "subject": genai.types.Schema(
#                             type=genai.types.Type.STRING,
#                         ),
#                         "chapternumber": genai.types.Schema(
#                             type=genai.types.Type.INTEGER,
#                         ),
#                         "chaptername": genai.types.Schema(
#                             type=genai.types.Type.STRING,
#                         ),
#                         "rollnumber": genai.types.Schema(
#                             type=genai.types.Type.INTEGER,
#                         ),
#                         "score": genai.types.Schema(
#                             type=genai.types.Type.INTEGER,
#                         ),
#                     },
#                 ),
#             ),
#         ]
#     ),
# ]

# CONFIG = types.LiveConnectConfig(
#     response_modalities=["AUDIO"],
#     media_resolution="MEDIA_RESOLUTION_MEDIUM",
#     speech_config=types.SpeechConfig(
#         language_code="mr-IN",
#         voice_config=types.VoiceConfig(
#             prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
#         )
#     ),
#     context_window_compression=types.ContextWindowCompressionConfig(
#         trigger_tokens=25600,
#         sliding_window=types.SlidingWindow(target_tokens=12800),
#     ),
#     tools=tools,
#     system_instruction=types.Content(
#         parts=[types.Part.from_text(text="You are helpful assistant teacher named EHR you only check homework of the particular student and after checking the homework and asking some questions and if something is wrong giving them a suggestion or reply back or correcting them you do not waste time at all you speak to the point and after the score completed after the questions answer are completed after the homework is completed you update the score automatically. Talk in any language whatever user says and if the homework and all details are there then first correct him or tell him what went wrong and update the code without asking but tell that score has been updated")],
#         role="user"
#     ),
# )

# class AudioLoop:
#     def __init__(self):
#         self.media_in_queue = asyncio.Queue(maxsize=10)   # Queue for incoming media from WebSocket
#         self.browser_out_queue = asyncio.Queue()          # Queue for outgoing data (audio/text) to browser
#         self.session = None
#         self.session_task = None

#     async def send_to_gemini(self):
#         """Sends data from the media_in_queue to the Gemini session."""
#         while True:
#             msg = await self.media_in_queue.get()
#             if self.session:
#                 await self.session.send(input=msg)

#     async def receive_from_gemini(self):
#         """Receives audio, text, and tool calls from the Gemini session."""
#         while True:
#             if not self.session:
#                 await asyncio.sleep(0.1)
#                 continue
            
#             turn = self.session.receive()
#             try:
#                 async for response in turn:
#                     # Send audio data to the browser
#                     if data := response.data:
#                         encoded_data = base64.b64encode(data).decode('utf-8')
#                         await self.browser_out_queue.put({"type": "audio", "data": encoded_data})
                    
#                     # Send text responses to the browser
#                     if text := response.text:
#                         print("Response from AI: " + text, end="")
#                         await self.browser_out_queue.put({"type": "text", "data": text})
                        
#                     # Handle function calls
#                     if function_call := response.tool_call:
#                         print(f"\nFunction Call Received: {function_call.function_calls[0].name}")
#                         print(f"Arguments: {function_call.function_calls[0].args}\n")
#                         # Call your handle_function_call and send the result back
#                         result = handle_function_call(function_call.function_calls[0])
#                         print("the result is here: " + str(result))

#                         function_response = types.FunctionResponse(
#                             name="scoreupdater",
#                             response={"result": result},
#                             id=function_call.function_calls[0].id,
#                         )
#                         await self.session.send_tool_response(
#                             function_responses=function_response
#                         )
#             except asyncio.CancelledError:
#                 break
#             except Exception as e:
#                 print(f"Error in receive_from_gemini: {e}")
#                 break

#     async def run_session(self):
#         """Manages the Gemini AI session lifecycle and its I/O tasks."""
#         try:
#             async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
#                 self.session = session
#                 async with asyncio.TaskGroup() as tg:
#                     tg.create_task(self.send_to_gemini())
#                     tg.create_task(self.receive_from_gemini())
#         except Exception as e:
#             print(f"Session ended with error: {e}")
#         finally:
#             self.session = None

#     def start(self):
#         """Starts the main Gemini session task."""
#         if not self.session_task or self.session_task.done():
#             self.session_task = asyncio.create_task(self.run_session())

#     def stop(self):
#         """Stops the Gemini session task."""
#         if self.session_task and not self.session_task.done():
#             self.session_task.cancel()
            
            
# -----------------------------------------------------------------------------------------------------------------




# server.py (or the file you posted at top)
import datetime
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from checker import AudioLoop
import base64
import asyncio
import uvicorn
from notifications import notifier

app = FastAPI()

@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    session_id = str(uuid.uuid4())
    await websocket.accept()
    
    # Simple notification sender
    notifier.set_websocket(websocket)
    
    # Create AudioLoop and set up notifications
    audio_loop = AudioLoop()
    audio_loop.set_session_id(session_id)
    
    # Send welcome notification (fire-and-forget so it doesn't block)
    asyncio.create_task(notifier.send("Session Started", f"Miasma session {session_id[:8]} started", "success"))
    
    audio_loop.start()
    
    async def receive_from_client():
        try:
            while True:
                data = await websocket.receive_json()
                media_type = data.get("type")
                if media_type == "audio":
                    audio_data = base64.b64decode(data['data'])
                    await audio_loop.media_in_queue.put({"data": audio_data, "mime_type": "audio/pcm"})
                elif media_type == "video":
                    image_data = data['data']
                    await audio_loop.media_in_queue.put({"mime_type": "image/jpeg", "data": base64.b64decode(image_data)})
        except WebSocketDisconnect:
            print("Client disconnected (receive task).")

    async def send_to_client():
        try:
            while True:
                message = await audio_loop.browser_out_queue.get()
                await websocket.send_json(message)
        except WebSocketDisconnect:
            print("Client disconnected (send task).")

    # Run tasks
    receive_task = asyncio.create_task(receive_from_client())
    send_task = asyncio.create_task(send_to_client())

    done, pending = await asyncio.wait(
        [receive_task, send_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
    audio_loop.stop()
    print(f"WebSocket connection for session {session_id} closed.")

if __name__ == "__main__":
    print("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="localhost", port=8080)
