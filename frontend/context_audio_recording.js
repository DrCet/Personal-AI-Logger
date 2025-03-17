document.addEventListener('DOMContentLoaded', () => {
    const generateSentenceBtn = document.getElementById('generateSentence');
    const startRecordingBtn = document.getElementById('startRecording');
    const stopRecordingBtn = document.getElementById('stopRecording');
    const saveRecordingBtn = document.getElementById('saveRecording');
    const showLogsBtn = document.getElementById('showLogsButton');
    const sentenceDiv = document.getElementById('sentence');
    const recordingStatus = document.getElementById('recordingStatus');
    const logsTableBody = document.getElementById('logsTableBody');
    const deleteModal = document.getElementById('deleteModal');
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    const cancelDeleteBtn = document.getElementById('cancelDelete');

    let mediaRecorder;
    let audioChunks = [];
    let currentSentence = '';

    // Generate a random sentence
    const sentences = [
        "The spaceship hovered silently above the alien planet.",
        "A mysterious signal came from the edge of the galaxy.",
        "The robot repaired the damaged starship in record time.",
        "Green lights flickered in the distant nebula.",
        "The captain ordered a course change to avoid the asteroid field."
    ];

    generateSentenceBtn.addEventListener('click', () => {
        currentSentence = sentences[Math.floor(Math.random() * sentences.length)];
        sentenceDiv.textContent = currentSentence;
        startRecordingBtn.disabled = false;
        recordingStatus.textContent = 'Ready to record.';
    });

    // Request microphone access and start recording
    startRecordingBtn.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const audioUrl = URL.createObjectURL(audioBlob);
                saveRecordingBtn.disabled = false;
                saveRecordingBtn.dataset.audioBlob = audioBlob; // Store blob for saving
                recordingStatus.textContent = 'Recording stopped. Click "Save" to store.';
            };

            mediaRecorder.start();
            startRecordingBtn.disabled = true;
            stopRecordingBtn.disabled = false;
            recordingStatus.textContent = 'Recording...';
        } catch (error) {
            recordingStatus.textContent = `Error accessing microphone: ${error.message}`;
        }
    });

    // Stop recording
    stopRecordingBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            stopRecordingBtn.disabled = true;
        }
    });

    // Save recording to server
    saveRecordingBtn.addEventListener('click', async () => {
        const audioBlob = saveRecordingBtn.dataset.audioBlob;
        if (!audioBlob || !currentSentence) {
            recordingStatus.textContent = 'No recording or sentence to save.';
            return;
        }

        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('sentence', currentSentence);
        formData.append('timestamp', new Date().toISOString());

        try {
            const response = await fetch('/context-audio-recording/save', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                recordingStatus.textContent = 'Recording saved successfully!';
                loadLogs();
                startRecordingBtn.disabled = false;
                saveRecordingBtn.disabled = true;
                delete saveRecordingBtn.dataset.audioBlob;
            } else {
                recordingStatus.textContent = `Error: ${data.detail}`;
            }
        } catch (error) {
            recordingStatus.textContent = `Error saving recording: ${error.message}`;
        }
    });

    // Show logs
    showLogsBtn.addEventListener('click', () => {
        loadLogs();
    });

    // Load logs from server
    async function loadLogs() {
        try {
            const response = await fetch('/context-audio-recording/logs');
            const logs = await response.json();
            logsTableBody.innerHTML = '';
            logs.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${log.id}</td>
                    <td>${log.sentence}</td>
                    <td><audio controls src="/audio/${log.filename}"></audio></td>
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td><button class="delete-button" data-id="${log.id}">Delete</button></td>
                `;
                logsTableBody.appendChild(row);
            });

            // Add delete event listeners
            document.querySelectorAll('.delete-button').forEach(button => {
                button.addEventListener('click', () => {
                    const logId = button.dataset.id;
                    deleteModal.style.display = 'flex';
                    confirmDeleteBtn.onclick = () => deleteLog(logId);
                    cancelDeleteBtn.onclick = () => (deleteModal.style.display = 'none');
                });
            });
        } catch (error) {
            console.error('Error loading logs:', error);
        }
    }

    // Delete log
    async function deleteLog(logId) {
        try {
            const response = await fetch(`/context-audio-recording/delete/${logId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                deleteModal.style.display = 'none';
                loadLogs();
            }
        } catch (error) {
            console.error('Error deleting log:', error);
        }
    }

    // Initial load
    loadLogs();
});