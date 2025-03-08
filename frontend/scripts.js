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
                    this.stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            sampleRate: 16000,
                            channelCount: 1 // Ensure mono audio
                        }
                    });
                    
                    this.recorder = new MediaRecorder(this.stream, {
                        mimeType: 'audio/wav',
                    });
                    
                    this.setupEventListeners();
                    this.recorder.start(1000); // Send chunks every second
                    console.log("Recording started with settings:", this.recorder.state);
                    
                    this.button.innerText = "Stop Transcription";
                } catch (err) {
                    console.error("Microphone error:", err);
                    this.transcriptionDiv.innerText = "Microphone access denied";
                    this.stopTranscription();
                }
            };

            this.socket.onmessage = (event) => {
                try {
                    const response = JSON.parse(event.data);
                    if (response.status === "success") {
                        if (response.transcription.trim()) {
                            this.transcriptionDiv.innerText = response.transcription;
                        }
                    } else {
                        console.error("Transcription error:", response.message);
                    }
                } catch (e) {
                    console.error("Failed to parse server response:", e);
                }
            };

            // ...existing error handlers...
        } catch (error) {
            console.error("Connection error:", error);
            this.transcriptionDiv.innerText = "Failed to connect";
            this.stopTranscription();
        }
    }

    async stopTranscription() {
        if (this.recorder) {
            this.recorder.stop();
            this.recorder = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.button.innerText = "Start Transcription";
        console.log("Transcription stopped");
    }

    setupEventListeners() {
        this.recorder.ondataavailable = (event) => {
            if (this.socket?.readyState === WebSocket.OPEN && event.data.size > 0) {
                this.socket.send(event.data);
                console.log(`Audio chunk sent: ${event.data.size} bytes`);
            }
        };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("Page loaded, initializing TranscriptionHandler");
    new TranscriptionHandler();
});