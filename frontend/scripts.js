class TranscriptionHandler {
    constructor() {
        // Initialize buttons
        this.startButton = document.getElementById("startButton");
        this.pauseButton = document.getElementById("pauseButton");
        this.saveButton = document.getElementById("saveButton");
        this.clearButton = document.getElementById("clearButton");
        this.transcriptionDiv = document.getElementById("transcription");
        this.statusDiv = document.getElementById("status");
        
        // Initialize state
        this.socket = null;
        this.recorder = null;
        this.stream = null;
        this.audioContext = null;
        this.audioData = [];
        this.isPaused = false;
        this.fullTranscript = "";
        
        // Bind event listeners
        this.startButton.addEventListener("click", () => this.toggleTranscription());
        this.pauseButton.addEventListener("click", () => this.togglePause());
        this.saveButton.addEventListener("click", () => this.saveTranscript());
        this.clearButton.addEventListener("click", () => this.clearTranscript());
        
        this.updateStatus("Ready");
        this.updateButtonStates(false);
    }

    async toggleTranscription() {
        this.socket ? await this.stopTranscription() : await this.startTranscription();
    }

    async startTranscription() {
        try {
            if (!navigator.mediaDevices) throw new Error("MediaDevices API not available");
            const constraints = { 
                audio: { 
                    sampleRate: 16000, 
                    channelCount: 1, 
                    echoCancellation: true, 
                    noiseSuppression: true 
                } 
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.updateStatus("Microphone access granted");

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            const source = this.audioContext.createMediaStreamSource(this.stream);
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            source.connect(processor);
            processor.connect(this.audioContext.destination);

            const wsUrl = `ws://${window.location.hostname}:8000/api/transcribe`;
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                this.initializeRecorder();
                this.updateStatus("Connected to server");
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.transcription) {
                    this.fullTranscript += " " + data.transcription;
                    this.transcriptionDiv.innerText = this.fullTranscript;
                    this.updateButtonStates(true);
                } else if (data.error) {
                    this.updateStatus(`Error: ${data.error}`);
                }
            };
            
            this.socket.onerror = () => {
                this.updateStatus("WebSocket connection failed");
                this.stopTranscription();
            };
            
            this.socket.onclose = () => {
                console.log("WebSocket closed");
                this.updateStatus("Disconnected from server");
                this.stopTranscription();
            };

            processor.onaudioprocess = (e) => {
                if (!this.isPaused) {
                    this.audioData.push(...e.inputBuffer.getChannelData(0));
                    if (this.audioData.length >= 16000) this.sendWavChunk();
                }
            };

            this.updateButtonStates(true);
            
        } catch (error) {
            console.error("Error:", error);
            this.updateStatus(`Error: ${error.message}`);
            await this.stopTranscription();
        }
    }

    sendWavChunk() {
        if (!this.audioContext || this.audioData.length === 0 || 
            this.socket?.readyState !== WebSocket.OPEN || this.isPaused) return;
        
        const buffer = new Float32Array(this.audioData.splice(0, 16000));
        this.socket.send(this.encodeWav(buffer, 16000));
    }

    encodeWav(samples, sampleRate) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);

        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) 
                view.setUint8(offset + i, string.charCodeAt(i));
        };

        writeString(0, 'RIFF');
        view.setUint32(4, 36 + samples.length * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, samples.length * 2, true);

        for (let i = 0; i < samples.length; i++) {
            const s = Math.max(-1, Math.min(1, samples[i]));
            view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
        return buffer;
    }

    initializeRecorder() {
        try {
            if (!this.stream || !this.stream.active) 
                throw new Error("Audio stream inactive");
            
            this.recorder = new MediaRecorder(this.stream);
            
            this.recorder.ondataavailable = (event) => {
                if (this.socket?.readyState === WebSocket.OPEN && 
                    event.data.size > 0 && !this.isPaused) {
                    this.socket.send(event.data);
                }
            };
            
            this.recorder.start(1000);
            this.startButton.innerText = "Stop Transcription";
            this.updateStatus("Recording started");
            
        } catch (error) {
            console.error("Recorder error:", error);
            this.updateStatus(`Recorder error: ${error.message}`);
            this.stopTranscription();
        }
    }

    async togglePause() {
        if (!this.recorder) return;
        
        this.isPaused = !this.isPaused;
        
        if (this.isPaused) {
            this.recorder.pause();
            this.pauseButton.textContent = "Resume";
            this.updateStatus("Paused");
        } else {
            this.recorder.resume();
            this.pauseButton.textContent = "Pause";
            this.updateStatus("Recording");
        }
    }

    async saveTranscript() {
        try {
            const response = await fetch('/api/log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text: this.fullTranscript.trim() 
                })
            });
            
            if (!response.ok) throw new Error('Failed to save transcript');
            
            this.updateStatus("Transcript saved successfully");
        } catch (error) {
            console.error("Error saving transcript:", error);
            this.updateStatus("Error saving transcript");
        }
    }

    clearTranscript() {
        this.fullTranscript = "";
        this.transcriptionDiv.innerText = "Waiting for transcription...";
        this.updateStatus("Transcript cleared");
        this.updateButtonStates(this.recorder?.state === "recording");
    }

    async stopTranscription() {
        try {
            // Stop recorder first
            if (this.recorder && this.recorder.state === "recording") {
                this.recorder.stop();
            }
            
            // Stop audio tracks
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
            
            // Close audio context
            if (this.audioContext?.state !== 'closed') {
                await this.audioContext.close();
            }
            
            // Close WebSocket last
            if (this.socket?.readyState === WebSocket.OPEN) {
                this.socket.close();
            }

            // Reset all properties
            this.recorder = null;
            this.stream = null;
            this.audioContext = null;
            this.socket = null;
            this.audioData = [];
            this.isPaused = false;
            
            this.startButton.innerText = "Start Transcription";
            this.updateButtonStates(false);
            this.updateStatus("Stopped");
            
        } catch (error) {
            console.error("Error stopping transcription:", error);
            this.updateStatus("Error stopping transcription");
        }
    }

    updateButtonStates(isRecording) {
        this.pauseButton.disabled = !isRecording;
        this.saveButton.disabled = !this.fullTranscript;
        this.clearButton.disabled = !this.fullTranscript;
        this.startButton.textContent = isRecording ? "Stop Transcription" : "Start Transcription";
    }

    updateStatus(message) {
        this.statusDiv.textContent = message;
        console.log("Status:", message);
    }
}

document.addEventListener('DOMContentLoaded', () => new TranscriptionHandler());