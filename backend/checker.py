# checker.py
import os
import asyncio
import base64
import io
import pyaudio
import traceback
import argparse
import json
from google import genai
from google.genai import types
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import uvicorn
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime
from notifications import notifier
from factchecker import checkfact
# --- Gemini AI and PyAudio setup ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
MODEL = "models/gemini-2.0-flash-live-001"
# Nawaz api key
# Initialize the Google Generative AI client
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key="paste your API key here",
)


# --- Function call handler and tools definition ---
async def handle_function_call_async(function_call):
    """Handles the 'falseInformationDetector' function call from the AI."""
    if function_call.name == "falseInformationDetector":
        args = function_call.args
        claim = args.get("claim", "Unknown claim")

        print("Received a Function Call for falseInformationDetector:")
        print(f"Claim to verify: {claim}")

        # Simulate verification process (replace with actual verification logic)
        verification_result = checkfact(claim)

        # Send notification about function call completion (backgrounded)
        asyncio.create_task(
            notifier.send(
                title=claim + " is " + str(verification_result['is_true']),
                content=str(verification_result['statement']),
                severity="success" if verification_result['is_true'] else "error",
                action=verification_result['confidence_score'],
            )
        )

        return verification_result

    return {"success": False, "message": "Unknown function call"}


# # Keep the sync version for backward compatibility
# def handle_function_call(function_call):
#     """Synchronous wrapper for function call handling"""
#     if function_call.name == "falseInformationDetector":
#         args = function_call.args
#         claim = args.get("claim", "Unknown claim")
#         print("Received a Function Call for falseInformationDetector:")
#         print(f"Claim to verify: {claim}")
#         return {"success": True, "message": "100 Percent true", "confidence": 0.95}
#     return {"success": False, "message": "Unknown function call"}


# Define the tool(s) for the AI model
tools = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="falseInformationDetector",
                description="Detects whether its true or false. we need to pass the information in claim parameter that is users claim as parameter.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    required=["claim"],
                    properties={
                        "claim": types.Schema(
                            type=types.Type.STRING,
                            description="The claim made by the user to be verified",
                        ),
                    },
                ),
            ),
        ]
    ),
]


class AudioLoop:
    """Manages an isolated audio communication session with Gemini."""

    def __init__(self):
        self.media_in_queue = asyncio.Queue(maxsize=10)
        self.browser_out_queue = asyncio.Queue()
        self.session = None
        self.session_task = None
        self.session_id = None

    def set_session_id(self, session_id):
        """Set the session ID for tracking"""
        self.session_id = session_id

    async def send_to_gemini(self):
        """Sends media data from the input queue to the Gemini session."""
        while True:
            msg = await self.media_in_queue.get()
            if self.session:
                await self.session.send(input=msg)

    async def receive_from_gemini(self):
        """Receives audio, text, and tool calls from the Gemini session."""
        while True:
            if not self.session:
                await asyncio.sleep(0.1)
                continue

            turn = self.session.receive()
            try:
                async for response in turn:
                    if data := response.data:
                        encoded_data = base64.b64encode(data).decode("utf-8")
                        await self.browser_out_queue.put(
                            {"type": "audio", "data": encoded_data}
                        )

                    if text := response.text:
                        print("Response from AI: " + text, end="")
                        await self.browser_out_queue.put({"type": "text", "data": text})

                    if function_call := response.tool_call:
                        function_name = function_call.function_calls[0].name
                        function_args = function_call.function_calls[0].args

                        print(f"\n🔧 Function Call Received: {function_name}")
                        print(f"Arguments: {function_args}\n")

                        # Notify frontend about incoming function call (backgrounded)
                        asyncio.create_task(
                            notifier.send(
                                "ADROIT Agent Function Call [Internal Agent884]",
                                f"Claim to be Verified: {function_args['claim']}",
                                "info",
                                "ADROIT_AGENT_FACT_CHECKER_778a",
                            )
                        )

                        # Handle the function call with proper async handling
                        result = await handle_function_call_async(
                            function_call.function_calls[0],
                        )

                        print("Function result: " + str(result))

                        # Notify frontend about function result (backgrounded)
                        # asyncio.create_task(
                        #     notifier.send(
                        #         f"Function {function_name} executed",
                        #         f"Result: {result}",
                        #     )
                        # )

                        function_response = types.FunctionResponse(
                            name=function_call.function_calls[0].name,
                            response={"output": result},  # wrap it
                            id=function_call.function_calls[0].id,
                        )
                        
                        # Send tool response back to the model (await so model receives it)
                        await self.session.send_tool_response(
                            function_responses=[function_response]
                        )


            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in receive_from_gemini: {e}")
                # send notification in background so it doesn't block
                asyncio.create_task(
                    notifier.send(
                        "Session Error",
                        f"Error in Gemini session: {str(e)[:100]}",
                        "error",
                        "Session Error",
                    )
                )
                break

    async def run_session(self, config: types.LiveConnectConfig):
        """Manages the Gemini AI session lifecycle using a provided config."""
        try:
            # notify start (backgrounded)
            asyncio.create_task(
                notifier.send(
                    "Miasma Starting",
                    f"AI Agent session starting (ID: {self.session_id[:8] if self.session_id else 'Unknown'})",
                    "info",
                    "Session Starting",
                )
            )

            async with client.aio.live.connect(model=MODEL, config=config) as session:
                self.session = session

                # notify connected (backgrounded)
                asyncio.create_task(
                    notifier.send(
                        "Adroit's The Miasma Filter Connected",
                        "Successfully connected to server",
                        "success",
                        "Connected",
                    )
                )

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self.send_to_gemini())
                    tg.create_task(self.receive_from_gemini())
        except Exception as e:
            print(f"❌ Session ended with error: {e}")
            asyncio.create_task(
                notifier.send(
                    "Session Failed",
                    f"Gemini session error: {str(e)[:100]}",
                    "error",
                    "Session Error",
                )
            )
        finally:
            self.session = None
            asyncio.create_task(
                notifier.send(
                    "Session Ended",
                    "Miasma AI session has been terminated",
                    "warning",
                    "Session Ended",
                )
            )

    base_prompt = " Whatever factual statements will user will make pass that to the function call to test whether it is true or false . Do this silently dont say anything , just listen and do fucntion call. Dont question Back, just send everything to the funntion call, Just Function call dont say anything. just return the tool call. and You dont wait for the response you pass it directly to the module. you pass the claim to the function and forgot. you are desgined just to make a function call thats it."
    def start(self):
        """Starts the main Gemini session task with a specific configuration."""

        session_config = types.LiveConnectConfig(
            temperature=0.1,
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            speech_config=types.SpeechConfig(
                language_code="en-IN",
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
                ),
            ),
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                    prefix_padding_ms=200,
                    silence_duration_ms=40,
                )
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=25600,
                sliding_window=types.SlidingWindow(target_tokens=12800),
            ),
            tools=tools,
            # safety_settings=[
            #     types.SafetySetting(
            #         category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            #         threshold=types.HarmBlockThreshold.OFF,
            #     ),
            # ],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=self.base_prompt)], role="user"
            ),
        )

        if not self.session_task or self.session_task.done():
            self.session_task = asyncio.create_task(self.run_session(session_config))

    def stop(self):
        """Stops the Gemini session task."""
        if self.session_task and not self.session_task.done():
            self.session_task.cancel()
