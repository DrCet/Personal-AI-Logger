class RecordingHandler {
    constructor() {
        // Initialize DOM elements
        this.generateSentenceBtn = document.getElementById("generateSentence");
        this.startRecordingBtn = document.getElementById("startRecording");
        this.stopRecordingBtn = document.getElementById("stopRecording");
        this.saveRecordingBtn = document.getElementById("saveRecording");
        this.clearSentenceBtn = document.getElementById("clearSentence");
        this.showLogsBtn = document.getElementById("showLogsButton");
        this.sentenceDiv = document.getElementById("sentence");
        this.recordingStatus = document.getElementById("recordingStatus");
        this.logsTableBody = document.getElementById("logsTableBody");
        this.deleteModal = document.getElementById("deleteModal");
        this.confirmDeleteBtn = document.getElementById("confirmDelete");
        this.cancelDeleteBtn = document.getElementById("cancelDelete");

        // Initialize state
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.currentSentence = "";
        this.logIdToDelete = null;

        // Bind event listeners
        this.generateSentenceBtn.addEventListener("click", () => this.generateSentence());
        this.startRecordingBtn.addEventListener("click", () => this.startRecording());
        this.stopRecordingBtn.addEventListener("click", () => this.stopRecording());
        this.saveRecordingBtn.addEventListener("click", () => this.saveRecording());
        this.showLogsBtn.addEventListener("click", () => this.showLogs());
        this.clearSentenceBtn.addEventListener("click", () => this.clearCurrentSentence());

        // Initial setup
        this.showLogs();
        this.updateStatus("Click 'Generate Sentence' to start.");
        this.updateButtonStates(false);

        this.SENTENCE_CORPUS = [
            "The spaceship hovered silently above the alien planet.",
            "A mysterious signal came from the edge of the galaxy.",
            "The robot repaired the damaged starship in record time.",
            "Green lights flickered in the distant nebula.",
            "The captain ordered a course change to avoid the asteroid field.",
            "A lone astronaut drifted through the void of space.",
            "The AI system detected an anomaly in the star charts.",
            "Purple storms raged on the surface of the gas giant.",
            "The crew discovered ancient ruins on the moon's surface.",
            "A black hole loomed ominously at the galaxy's core.",
            "The interstellar probe sent back images of a frozen world.",
            "A comet streaked across the sky, leaving a trail of ice.",
            "The station orbited a planet with rings of shimmering dust.",
            "An alien artifact emitted a strange, pulsating glow.",
            "The engineer calibrated the warp drive for a long journey.",
            "A supernova illuminated the night sky with brilliant light.",
            "The colonists built a dome to survive the harsh atmosphere.",
            "A fleet of drones scanned the asteroid belt for resources.",
            "The scientist analyzed data from a distant exoplanet.",
            "The space elevator connected the planet to its orbiting station."
        ];
    }

    // Update status message
    updateStatus(message) {
        this.recordingStatus.textContent = message;
        console.log("Status:", message);
    }

    updateButtonStates(isRecording) {
        this.startRecordingBtn.disabled = isRecording || !this.currentSentence;
        this.stopRecordingBtn.disabled = !isRecording;
        this.saveRecordingBtn.disabled = !this.audioChunks.length || !this.currentSentence;
        this.clearSentenceBtn.disabled = !this.currentSentence; // Disable if no sentence to clear
    }

    // Generate a sentence by fetching from the backend
    generateSentence() {
        try {
            this.updateStatus("Generating sentence...");
            this.currentSentence = this.SENTENCE_CORPUS[Math.floor(Math.random() * this.SENTENCE_CORPUS.length)];
            this.sentenceDiv.textContent = this.currentSentence;
            this.updateStatus("Sentence generated. Ready to record.");
            this.updateButtonStates(false);
        } catch (error) {
            console.error("Error generating sentence:", error);
            this.updateStatus(`Error generating sentence: ${error.message}`);
        }
    }

    // Start recording audio
    async startRecording() {
        try {
            if (!navigator.mediaDevices) throw new Error("MediaDevices API not available");

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                this.updateStatus("Recording stopped. Click 'Save' to store.");
                this.updateButtonStates(false);
            };

            this.mediaRecorder.start();
            this.updateStatus("Recording...");
            this.updateButtonStates(true);
        } catch (error) {
            console.error("Error starting recording:", error);
            this.updateStatus(`Error accessing microphone: ${error.message}`);
        }
    }

    // Stop recording audio
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === "recording") {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            this.mediaRecorder = null;
        }
    }

    // Save the recording to the server
    async saveRecording() {
        if (!this.audioChunks.length || !this.currentSentence) {
            this.updateStatus("No recording or sentence to save.");
            return;
        }

        try {
            this.updateStatus("Saving recording...");
            const wavBlob = new Blob(this.audioChunks, { type: "audio/wav" });
            // Create unique filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            // this frontend filename is just a recommended name, and isn't required for the backend to save the file
            const filename = `recording_${timestamp}.wav`;  
            const formData = new FormData();
            formData.append("audio", wavBlob, filename);
            formData.append("text", this.currentSentence);


            const response = await fetch('/api/logs/audio', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error("Failed to save recording");
            }

            const result = await response.json();
            this.updateStatus(`Saved: ${result.file_name} - Transcript cleared`);
            this.clearCurrentSentence();
            this.showLogs();
            this.updateButtonStates(false);
        } catch (error) {
            console.error("Error saving recording:", error);
            this.updateStatus(`Error saving recording: ${error.message}`);
        }
    }

    // Clear the current display sentence
    clearCurrentSentence() {
        this.currentSentence = "";
        this.audioChunks = [];
        this.sentenceDiv.textContent = "Click 'Generate Sentence' to start.";
        this.updateStatus("Sentence cleared.");
        this.updateButtonStates(false);
    }

    // Fetch and display logs
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

    // Show delete confirmation modal
    showDeleteConfirmation(logId) {
        this.logIdToDelete = logId;
        this.deleteModal.style.display = "flex";
    }

    // Confirm deletion of a log
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
}

// Instantiate the handler
window.recordingHandler = new RecordingHandler();

// Add event listeners for modal buttons
document.addEventListener("DOMContentLoaded", () => {
    const recordingHandler = window.recordingHandler;
    recordingHandler.confirmDeleteBtn.addEventListener("click", () => recordingHandler.confirmDelete());
    recordingHandler.cancelDeleteBtn.addEventListener("click", () => recordingHandler.cancelDelete());
});