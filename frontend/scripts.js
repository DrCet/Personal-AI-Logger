const socket = new WebSocket("ws://127.0.0.1:8000/ws/transcribe");

navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    const recorder = new MediaRecorder(stream);
    recorder.start(1000); // Send audio every second

    recorder.ondataavailable = event => {
        socket.send(event.data);
    };

    socket.onmessage = event => {
        console.log("Transcription:", JSON.parse(event.data).transcription);
    };
});
