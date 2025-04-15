// Initialize PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf.worker.min.js';

document.getElementById('extractBtn').addEventListener('click', extractText);
document.getElementById('copyBtn').addEventListener('click', copyText);

let startTime;

async function extractText() {
    const fileInput = document.getElementById('pdfFile');
    const extractedTextArea = document.getElementById('extractedText');
    const timeInfo = document.getElementById('timeInfo');
    
    if (!fileInput.files.length) {
        alert('Please select a PDF file first');
        return;
    }
    
    const file = fileInput.files[0];
    const fileReader = new FileReader();
    
    fileReader.onload = async function() {
        try {
            startTime = performance.now();
            const typedArray = new Uint8Array(this.result);
            
            // Load the PDF document
            const pdf = await pdfjsLib.getDocument(typedArray).promise;
            
            let fullText = '';
            
            // Extract text from each page
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                const textItems = textContent.items.map(item => item.str);
                fullText += textItems.join(' ') + '\n\n';
            }
            
            const endTime = performance.now();
            const executionTime = (endTime - startTime) / 1000; // Convert to seconds
            
            extractedTextArea.value = fullText;
            timeInfo.innerHTML = `<p>Execution Time: <strong>${executionTime.toFixed(4)} seconds</strong></p>`;
        } catch (error) {
            console.error('Error extracting text:', error);
            extractedTextArea.value = `Error extracting text: ${error.message}`;
            timeInfo.innerHTML = `<p style="color: red;">Extraction failed</p>`;
        }
    };
    
    fileReader.readAsArrayBuffer(file);
}

function copyText() {
    const extractedTextArea = document.getElementById('extractedText');
    const copyStatus = document.getElementById('copyStatus');
    
    extractedTextArea.select();
    document.execCommand('copy');
    
    copyStatus.textContent = 'Copied!';
    setTimeout(() => {
        copyStatus.textContent = '';
    }, 2000);
}