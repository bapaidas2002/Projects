// Model parameters calculated from the linear regression dataset
const SLOPE = 1.0012;
const INTERCEPT = -0.0966;

document.getElementById('predictionForm').addEventListener('submit', function (event) {
    event.preventDefault();

    // Get input x value
    const xInput = parseFloat(document.getElementById('xValue').value);

    if (isNaN(xInput)) {
        alert('Please enter a valid number.');
        return;
    }

    // Linear Regression Formula: y = m * x + b
    const yPredicted = (SLOPE * xInput) + INTERCEPT;

    // Output formatted to 4 decimal places
    document.getElementById('yOutput').textContent = yPredicted.toFixed(4);

    // Unhide the result box
    document.getElementById('resultBox').classList.remove('hidden');
});