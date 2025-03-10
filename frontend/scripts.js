class TranscriptionHandler {
    constructor() {
        this.button = document.getElementById("startButton");
        this.transcriptionDiv = document.getElementById("transcription");
        // this.debugDiv = document.getElementById("debug") || document.createElement("div");
        document.body.appendChild(this.debugDiv);
        this.socket = null;
        this.recorder = null;
        this.stream = null;
        this.audioContext = null; // New AudioContext for WAV encoding
        this.audioData = []; // Buffer for audio samples
        console.log("TranscriptionHandler initialized");
        this.button.addEventListener("click", () => this.handleTranscription());
    }

    async handleTranscription() {
        console.log("Button clicked");
        if (this.socket) {
            await this.stopTranscription();
            return;
        }
        await this.startTranscription();
    }

    async startTranscription() {
        try {
            if (!navigator.mediaDevices) throw new Error("MediaDevices API not available");
            this.log("Starting transcription...");
            const constraints = {
                audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
            };
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.log("Microphone stream active:", this.stream.active);

            // Initialize AudioContext
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            const source = this.audioContext.createMediaStreamSource(this.stream);
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1); // Buffer size for processing
            source.connect(processor);
            processor.connect(this.audioContext.destination);

            const wsUrl = "ws://localhost:8000/api/transcribe";
            this.socket = new WebSocket(wsUrl);
            this.socket.onopen = () => {
                this.log("WebSocket connected");
                this.initializeRecorder();
            };
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.transcriptionDiv.innerText = data.transcription || `Error: ${data.error}`;
                // this.log("Received:", data);
            };
            this.socket.onerror = (error) => {
                this.log("WebSocket error:", error);
                this.transcriptionDiv.innerText = "WebSocket connection failed";
            };
            this.socket.onclose = () => this.log("WebSocket closed");

            // Audio processing for WAV
            processor.onaudioprocess = (e) => {
                const inputData = e.inputBuffer.getChannelData(0);
                this.audioData.push(...inputData);
                if (this.audioData.length >= 16000) { // Send 1 second of audio (16000 samples at 16kHz)
                    this.sendWavChunk();
                }
            };
        } catch (error) {
            this.log("Error:", error.name, error.message);
            this.transcriptionDiv.innerText = `Error: ${error.name} - ${error.message}`;
            await this.stopTranscription();
        }
    }

    sendWavChunk() {
        if (!this.audioContext || this.audioData.length === 0) return;

        const sampleRate = 16000;
        const numSamples = this.audioData.length;
        const buffer = new Float32Array(this.audioData.splice(0, 16000)); // Take 1 second
        const wavData = this.encodeWav(buffer, sampleRate);
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(wavData);
            // this.log("WAV chunk sent:", wavData.byteLength, "bytes");
        }
    }

    // WAV encoding function (simplified)
    encodeWav(samples, sampleRate) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);

        // Write WAV header
        this.writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + samples.length * 2, true); // File length minus 8
        this.writeString(view, 8, 'WAVE');
        this.writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true); // Size of fmt chunk
        view.setUint16(20, 1, true); // Audio format (1 = PCM)
        view.setUint16(22, 1, true); // Number of channels
        view.setUint32(24, sampleRate, true); // Sample rate
        view.setUint32(28, sampleRate * 2, true); // Byte rate
        view.setUint16(32, 2, true); // Block align
        view.setUint16(34, 16, true); // Bits per sample
        this.writeString(view, 36, 'data');
        view.setUint32(40, samples.length * 2, true); // Data chunk size

        // Write audio data (convert Float32 to Int16)
        for (let i = 0; i < samples.length; i++) {
            const s = Math.max(-1, Math.min(1, samples[i]));
            view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }

        return buffer;
    }

    writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    initializeRecorder() {
        try {
            if (!this.stream || !this.stream.active) throw new Error("Audio stream inactive");
            // this.log("Initializing MediaRecorder with stream:", this.stream);
            this.recorder = new MediaRecorder(this.stream, { mimeType: 'audio/webm;codecs=opus' });
            this.setupEventListeners();
            this.recorder.start(1000); // 1s chunks for consistency with WAV
            // this.log("Recording started, state:", this.recorder.state);
            this.button.innerText = "Stop Transcription";
        } catch (error) {
            this.log("Recorder error:", error.message);
            this.transcriptionDiv.innerText = `Recorder error: ${error.message}`;
            this.stopTranscription();
        }
    }

    // Create logs for debug. Uncomment this and the debug div in index.html file
    // log(...args) {
    //     const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ');
    //     console.log(message);
    //     try {
    //         if (this.debugDiv) {
    //             this.debugDiv.innerHTML += `<div>${new Date().toISOString()} - ${message}</div>`;
    //         }
    //     } catch (e) {
    //         console.error("Debug div update failed:", e);
    //     }
    // }

    setupEventListeners() {
        if (!this.recorder) return;
        this.recorder.ondataavailable = (event) => {
            // this.log("Data available, size:", event.data.size);
            if (this.socket?.readyState === WebSocket.OPEN && event.data.size > 0) {
                this.socket.send(event.data); // Fallback to WebM if WAV fails
                // this.log("Audio chunk sent:", event.data.size, "bytes");
            }
        };
        this.recorder.onerror = (error) => {
            this.log("Recorder error:", error);
            this.transcriptionDiv.innerText = "Recording error occurred";
            this.stopTranscription();
        };
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
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.button.innerText = "Start Transcription";
        this.log("Transcription stopped");
        this.audioData = []; // Clear audio data buffer
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TranscriptionHandler();
});