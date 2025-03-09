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
                    // Request microphone access with specific settings
                    this.stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            sampleRate: 16000,  // Match backend sample rate
                            channelCount: 1,    // Mono audio
                            sampleSize: 16      // 16-bit audio
                        }
                    });
                    
                    // Use WAV format
                    this.recorder = new MediaRecorder(this.stream, {
                        mimeType: 'audio/wav',
                        audioBitsPerSecond: 256000
                    });
                    
                    this.setupEventListeners();
                    this.recorder.start(1000); // 1-second chunks
                    console.log("Recording started:", this.recorder.state);
                    
                    this.button.innerText = "Stop Transcription";
                    this.transcriptionDiv.innerText = "Listening...";
                } catch (err) {
                    console.error("Microphone error:", err);
                    this.transcriptionDiv.innerText = "Microphone access denied";
                    await this.stopTranscription();
                }
            };

            // Handle incoming transcriptions
            this.socket.onmessage = (event) => {
                try {
                    const response = JSON.parse(event.data);
                    if (response.status === "success" && response.transcription?.trim()) {
                        // Append new transcription
                        const currentText = this.transcriptionDiv.innerText;
                        this.transcriptionDiv.innerText = currentText === "Listening..." ? 
                            response.transcription : 
                            `${currentText} ${response.transcription}`;
                    } else if (response.status === "error") {
                        console.error("Transcription error:", response.message);
                    }
                } catch (e) {
                    console.error("Failed to parse server response:", e);
                }
            };

            // Handle WebSocket errors
            this.socket.onerror = (error) => {
                console.error("WebSocket error:", error);
                this.transcriptionDiv.innerText = "Connection error";
                this.stopTranscription();
            };

        } catch (error) {
            console.error("Connection error:", error);
            this.transcriptionDiv.innerText = "Failed to connect";
            await this.stopTranscription();
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