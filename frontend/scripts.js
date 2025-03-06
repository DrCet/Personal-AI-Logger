class TranscriptionHandler {
    constructor() {
        this.button = document.getElementById("startButton");
        this.transcriptionDiv = document.getElementById("transcription");
        this.socket = null;
        this.recorder = null;
        this.stream = null;
        
        console.log("TranscriptionHandler initialized");
        this.button.addEventListener("click", () => {
            console.log("Button clicked");
            this.handleTranscription();
        });
    }

    async handleTranscription() {
        console.log("Starting transcription...");
        if (this.socket) {
            console.log("Socket exists, stopping transcription");
            await this.stopTranscription();
            return;
        }
        await this.startTranscription();
    }

    async startTranscription() {
        try {
            console.log("Connecting to WebSocket...");
            this.socket = new WebSocket("ws://127.0.0.1:8000/api/transcribe");
            
            this.socket.onopen = async () => {
                console.log("WebSocket connected successfully");
                try {
                    console.log("Requesting microphone access...");
                    this.stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            sampleRate: 16000
                        }
                    });
                    console.log("Microphone access granted");
                    
                    this.recorder = new MediaRecorder(this.stream);
                    this.setupEventListeners();
                    this.recorder.start(1000);
                    console.log("Recording started");
                    
                    this.button.innerText = "Stop Transcription";
                } catch (err) {
                    console.error("Microphone error:", err);
                    this.transcriptionDiv.innerText = "Microphone access denied";
                }
            };

            this.socket.onerror = (error) => {
                console.error("WebSocket error:", error);
                this.transcriptionDiv.innerText = "Connection failed";
            };

            this.socket.onclose = (event) => {
                console.log("WebSocket closed:", event.code, event.reason);
            };

        } catch (error) {
            console.error("Connection error:", error);
            this.transcriptionDiv.innerText = "Failed to connect";
        }
    }

    setupEventListeners() {
        this.recorder.ondataavailable = (event) => {
            console.log("Audio data available");
            if (this.socket?.readyState === WebSocket.OPEN) {
                this.socket.send(event.data);
                console.log("Audio data sent");
            }
        };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("Page loaded, initializing TranscriptionHandler");
    new TranscriptionHandler();
});