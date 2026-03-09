document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scan-btn');
    const loader = document.getElementById('loader');
    const errorContainer = document.getElementById('error-msg');
    const errorText = document.getElementById('error-text');
    const resultsContainer = document.getElementById('results-container');
    const tableBody = document.getElementById('table-body');
    const scanStats = document.getElementById('scan-stats');

    scanBtn.addEventListener('click', async () => {
        // UI Reset
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<span class="btn-text">Scanning...</span>';
        loader.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
        tableBody.innerHTML = '';

        try {
            // Initiate backend scan
            const response = await fetch('/api/scan');
            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;

                if (data.length === 0) {
                    throw new Error("No coins matched the R < 2.0 criteria.");
                }

                // Populate Table
                scanStats.innerText = `Found ${data.length} coins`;

                data.forEach(coin => {
                    const row = document.createElement('tr');

                    // Format Numbers
                    const lastCloseStr = `$${parseFloat(coin['Last Close']).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
                    const highStr = `$${parseFloat(coin['60D High']).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
                    const drawdownStr = parseFloat(coin['Drawdown (%)']).toFixed(2) + '%';
                    const rStr = parseFloat(coin['Relative_Strength_R']).toFixed(2);

                    row.innerHTML = `
                        <td class="symbol-cell">
                            <img src="https://ui-avatars.com/api/?name=${coin.Symbol}&background=random&color=fff&rounded=true&size=32" alt="${coin.Symbol}" width="28" height="28" style="border-radius:50%">
                            ${coin.Symbol}
                        </td>
                        <td style="color: var(--text-muted)">${coin.Ticker}</td>
                        <td class="number-cell">${lastCloseStr}</td>
                        <td class="number-cell">${highStr}</td>
                        <td class="number-cell value-bad">-${drawdownStr}</td>
                        <td class="number-cell r-value">${rStr}x</td>
                    `;
                    tableBody.appendChild(row);
                });

                // Show Results
                resultsContainer.classList.remove('hidden');
            } else {
                throw new Error(result.message || "Failed to parse API data.");
            }

        } catch (error) {
            console.error(error);
            errorText.innerText = "Error: " + error.message;
            errorContainer.classList.remove('hidden');
        } finally {
            // Restore button state
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<span class="btn-text">Start Market Scan</span><span class="btn-icon">➔</span>';
            loader.classList.add('hidden');

            // Auto scroll to results
            if (!resultsContainer.classList.contains('hidden')) {
                resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    });
});
