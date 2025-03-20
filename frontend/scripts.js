const logsTableContainer = document.getElementById("logsTableContainer");
const logsTableBody = document.getElementById("logsTableBody");
const deleteModal = document.getElementById("deleteModal");
const confirmDeleteBtn = document.getElementById("confirmDelete");
const cancelDeleteBtn = document.getElementById("cancelDelete");
let logIdToDelete = null;

// Show logs on the root page
document.getElementById("showLogsButton").addEventListener("click", async () => {
    try {
        logsTableContainer.style.display = "block"; // Show the table
        logsTableBody.innerHTML = ''; // Clear previous logs

        const limit = 10; // Match the limit used in context-audio-recording
        const response = await fetch(`/api/logs/data?limit=${limit}`, {
            method: 'GET'
        });

        if (!response.ok) {
            throw new Error('Failed to fetch logs');
        }

        const logs = await response.json();
        console.log("Fetched logs:", logs);

        if (logs.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="5">No logs found</td>`;
            logsTableBody.appendChild(row);
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
                deleteButton.addEventListener('click', () => showDeleteConfirmation(log.id));
                row.children[4].appendChild(deleteButton);
                logsTableBody.appendChild(row);
            });
        }
    } catch (error) {
        console.error("Error fetching logs:", error);
        logsTableBody.innerHTML = `<tr><td colspan="5">Error loading logs: ${error.message}</td></tr>`;
    }
});

// Download logs as JSON
document.getElementById("downloadLogsButton").addEventListener("click", async () => {
    try {
        const response = await fetch('/api/logs/download');
        console.log("Download response status:", response.status);
        if (!response.ok) {
            const errorText = await response.text();
            console.error("Download error:", errorText);
            throw new Error(`Failed to download logs: ${response.status} - ${errorText}`);
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'logs.json'; // Filename for download
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Error downloading logs:", error);
        alert("Error downloading logs: " + error.message);
    }
});

// Show delete confirmation modal
function showDeleteConfirmation(logId) {
    logIdToDelete = logId;
    deleteModal.style.display = "flex";
}

// Confirm deletion of a log
confirmDeleteBtn.addEventListener("click", async () => {
    if (logIdToDelete) {
        try {
            const response = await fetch(`/api/logs/delete/${logIdToDelete}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete log');
            }

            deleteModal.style.display = 'none';
            logIdToDelete = null;
            // Refresh logs after deletion
            document.getElementById("showLogsButton").click();
        } catch (error) {
            console.error("Error deleting log:", error);
            alert(`Error deleting log: ${error.message}`);
        }
    }
});

// Cancel deletion
cancelDeleteBtn.addEventListener("click", () => {
    deleteModal.style.display = 'none';
    logIdToDelete = null;
});