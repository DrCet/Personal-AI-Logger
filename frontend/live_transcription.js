class TranscriptionHandler {
    constructor() {
        // Initialize buttons
        this.startButton = document.getElementById("startButton");
        this.pauseButton = document.getElementById("pauseButton");
        this.saveButton = document.getElementById("saveButton");
        this.clearButton = document.getElementById("clearButton");
        this.transcriptionDiv = document.getElementById("transcription");
        this.statusDiv = document.getElementById("status");
        this.logsTableContainer = document.getElementById("logsTableContainer");
        this.logsTableBody = document.getElementById("logsTableBody");
        this.showLogsButton = document.getElementById("showLogsButton");
        
        // Initialize state
        this.socket = null;
        this.recorder = null;
        this.stream = null;
        this.audioContext = null;
        this.audioData = [];
        this.fullAudioData = [];
        this.isPaused = false;
        this.fullTranscript = "";

        this.deleteModal = document.getElementById("deleteModal");
        this.confirmDeleteBtn = document.getElementById("confirmDelete");
        this.cancelDeleteBtn = document.getElementById("cancelDelete");
        this.logIdToDelete = null;

        
        // Bind event listeners
        this.startButton.addEventListener("click", () => this.toggleTranscription());
        this.pauseButton.addEventListener("click", () => this.togglePause());
        this.saveButton.addEventListener("click", () => this.saveTranscript());
        this.clearButton.addEventListener("click", () => this.clearTranscript());
        this.showLogsButton.addEventListener("click", () => this.showLogs());
        
        this.showLogs();
        this.updateStatus("Ready");
        this.updateButtonStates(false);
    }

    async showLogs() {
        try {
            this.updateStatus("Fetching logs...");
            const limit = 10;
            const response = await fetch(`/api/logs/data?limit=${limit}`, {
                method: 'GET'
            });
    
            if (!response.ok) {
                throw new Error('Failed to fetch logs');
            }
    
            const logs = await response.json();
            console.log("Fetched logs:", logs);
    
            this.logsTableBody.innerHTML = '';
            if (logs.length === 0) {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="5">No logs found</td>`;
                this.logsTableBody.appendChild(row);
            } else {
                logs.forEach(log => {
                    const filename = log.audio_file;
                    const audioUrl = `/api/audio/${filename}`;
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${log.id}</td>
                        <td>${log.text}</td>
                        <td><audio controls src="${audioUrl}"></audio></td>
                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                        <td></td> <!-- Placeholder for delete button -->
                    `;
                    const deleteButton = document.createElement('button');
                    deleteButton.className = 'delete-button';
                    deleteButton.textContent = 'Delete';
                    deleteButton.addEventListener('click', () => this.showDeleteConfirmation(log.id));
                    row.children[4].appendChild(deleteButton); // Append to the Action column
                    this.logsTableBody.appendChild(row);
                });
            }
    
            this.updateStatus("Logs loaded successfully");
        } catch (error) {
            console.error("Error fetching logs:", error);
            this.updateStatus(`Error fetching logs: ${error.message}`);
            this.logsTableBody.innerHTML = `<tr><td colspan="5">Error loading logs</td></tr>`;
        }
    }

    showDeleteConfirmation(logId) {
        this.logIdToDelete = logId;
        this.deleteModal.style.display = 'flex';
    }

    async confirmDelete() {
        if (this.logIdToDelete) {
            try {
                this.updateStatus("Deleting log...");
                const response = await fetch(`/api/logs/delete/${this.logIdToDelete}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    throw new Error('Failed to delete log');
                }

                this.updateStatus("Log deleted successfully");
                this.deleteModal.style.display = 'none';
                this.showLogs(); // Refresh the logs table
            } catch (error) {
                console.error("Error deleting log:", error);
                this.updateStatus(`Error deleting log: ${error.message}`);
            }
        }
    }

    cancelDelete() {
        this.deleteModal.style.display = 'none';
        this.logIdToDelete = null;
    }


    async toggleTranscription() {
        // Check if we're currently recording (based on recorder state or WebSocket connection)
        if (this.recorder?.state === "recording" || (this.socket && this.socket.readyState === WebSocket.OPEN)) {
            await this.stopTranscription();
        } else {
            await this.startTranscription();
        }
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
                    this.fullAudioData.push(...e.inputBuffer.getChannelData(0));
                    // sendWavChunk when the buffer size is > 24000. With sampling_rate = 16000
                    // this sends audio every 1.5
                    if (this.audioData.length >= 24000) this.sendWavChunk();
                }
            };

            this.updateButtonStates(true);
            
        } catch (error) {
            console.error("Error:", error);
            this.updateStatus(`Error: ${error.message}`);
            // await this.stopTranscription();
        }
    }

    sendWavChunk() {
        if (this.audioData.length < 24000 || this.socket.readyState !== WebSocket.OPEN) return;
        const buffer = new Float32Array(this.audioData.splice(0, 24000));
        this.socket.send(buffer.buffer); // Send ArrayBuffer (raw float32 bytes)
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
            // Create WAV blob from accumulated audio data
            const wavBlob = new Blob([this.encodeWav(new Float32Array(this.fullAudioData), 16000)], 
                { type: 'audio/wav' });
            
            // Create unique filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            // this frontend filename is just a recommended name, and isn't required for the backend to save the file
            const filename = `recording_${timestamp}.wav`;  
    
            // Create FormData with both audio and text
            const formData = new FormData();
            formData.append('file', wavBlob, filename);       //the third argument tis optional
            formData.append('text', this.fullTranscript.trim());
    
            const response = await fetch('/api/logs/audio', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to save transcript and audio');
            }
            
            const result = await response.json();
            // This is new!!
            this.clearTranscript();
            this.showLogs();
            this.updateStatus(`Saved: ${result.file_name} - Transcript cleared`);

        } catch (error) {
            console.error("Error saving:", error);
            this.updateStatus("Error saving transcript and audio");
        }
    }

    clearTranscript() {
        this.fullTranscript = "";
        this.audioData = []
        this.fullAudioData = []
        this.transcriptionDiv.innerText = "Waiting for transcription...";
        this.updateButtonStates(this.recorder?.state === "recording");
    }

    async stopTranscription() {
        try {
            console.log("Stopping transcription, audioContext state:", this.audioContext?.state);
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.close(1000, "Manual stop by client"); // Explicitly close
            }
            if (this.audioContext && this.audioContext.state !== 'closed') {
                await this.audioContext.close();
            }
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }

            // Reset all properties
            this.socket = null;
            this.updateButtonStates(false);
            this.updateStatus("Transcription stopped");
        } catch (error) {
            console.error("Stop error:", error);
            this.updateStatus(`Stop error: ${error.message}`);
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

window.transcriptionHandler = new TranscriptionHandler();

// Add event listeners for modal buttons
document.addEventListener('DOMContentLoaded', () => {
    const transcriptionHandler = window.transcriptionHandler;
    transcriptionHandler.confirmDeleteBtn.addEventListener('click', () => transcriptionHandler.confirmDelete());
    transcriptionHandler.cancelDeleteBtn.addEventListener('click', () => transcriptionHandler.cancelDelete());
});