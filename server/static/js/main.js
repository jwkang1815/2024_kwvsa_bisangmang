const videoFeed = document.getElementById('video-feed');
const annotationsDiv = document.getElementById('annotations');

// Use a ReadableStream to process the multipart response
fetch('/stream')
  .then(response => response.body)
  .then(body => {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    function readStream() {
      reader.read().then(({ done, value }) => {
        if (done) {
          console.log('Stream ended.');
          return;
        }

        buffer += decoder.decode(value, { stream: true });
        // Process the buffer for complete multipart boundaries
        processBuffer();
        // Continue reading from the stream
        readStream();
      });
    }

    function processBuffer() {
      const boundary = '--frame';
      let boundaryIndex = buffer.indexOf(boundary);

      while (boundaryIndex !== -1) {
        const dataPart = buffer.substring(0, boundaryIndex);
        buffer = buffer.substring(boundaryIndex + boundary.length);

        // Process only if dataPart is not empty
        if (dataPart.trim()) {
          handleDataPart(dataPart);
        }

        boundaryIndex = buffer.indexOf(boundary);
      }
    }

    function handleDataPart(dataPart) {
      const headerSeparator = '\r\n\r\n';
      const headerSeparatorIndex = dataPart.indexOf(headerSeparator);

      if (headerSeparatorIndex !== -1) {
        const header = dataPart.substring(0, headerSeparatorIndex);
        const body = dataPart.substring(headerSeparatorIndex + headerSeparator.length);
        const contentTypeLine = header.split('\r\n').find(line => line.startsWith('Content-Type:'));

        if (contentTypeLine) {
          const contentType = contentTypeLine.split(':')[1].trim();

          if (contentType === 'text/plain') {
            // Extract image filename from path
            const imageFilename = body.substring(body.lastIndexOf('/') + 1);
            // Update image source directly
            videoFeed.src = `images/incomming/${imageFilename}`;
          } else if (contentType === 'application/json') {
            try {
              const annotations = JSON.parse(body);
              annotationsDiv.innerHTML = `
                <p>Prediction: ${annotations.Prediction}</p>
                <p>Bird: ${annotations.Bird}</p>
                <p>Drone: ${annotations.Drone}</p>
                <p>None: ${annotations.None}</p>
              `;
            } catch (error) {
              console.error("Error parsing JSON:", error);
            }
          }
        }
      }
    }

    readStream();
  });