document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scan-btn');
    const loader = document.getElementById('loader');
    const errorContainer = document.getElementById('error-msg');
    const errorText = document.getElementById('error-text');
    const resultsContainer = document.getElementById('results-container');
    const tableBody = document.getElementById('table-body');
    const scanStats = document.getElementById('scan-stats');

    const wyckoffBtn = document.getElementById('wyckoff-btn');
    const wyckoffLoader = document.getElementById('wyckoff-loader');
    const wyckoffError = document.getElementById('wyckoff-error');
    const wyckoffErrorText = document.getElementById('wyckoff-error-text');
    const wyckoffResults = document.getElementById('wyckoff-results');
    const wyckoffTableBody = document.getElementById('wyckoff-table-body');
    const wyckoffStats = document.getElementById('wyckoff-stats');

    const step1 = document.getElementById('step-1-indicator');
    const step2 = document.getElementById('step-2-indicator');

    // PDF elements
    const pdfBtn = document.getElementById('pdf-btn');

    // Store screener data for passing to Wyckoff
    let screenerData = [];
    let wyckoffPassedData = []; // Store passed data for PDF

    // ============================
    // Step 1: Market Screener
    // ============================
    scanBtn.addEventListener('click', async () => {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<span class="btn-text">Scanning...</span>';
        loader.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
        wyckoffResults.classList.add('hidden');
        wyckoffError.classList.add('hidden');
        tableBody.innerHTML = '';
        wyckoffTableBody.innerHTML = '';
        screenerData = [];

        // Reset pipeline indicators
        step1.classList.add('active');
        step1.classList.remove('completed');
        step2.classList.remove('active', 'completed');

        try {
            const response = await fetch('/api/scan');
            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                if (data.length === 0) {
                    throw new Error("No coins matched the R < 2.0 criteria.");
                }

                screenerData = data;
                scanStats.innerText = `Found ${data.length} coins`;

                data.forEach(coin => {
                    const row = document.createElement('tr');
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

                // Mark Step 1 as completed
                step1.classList.remove('active');
                step1.classList.add('completed');

                resultsContainer.classList.remove('hidden');
            } else {
                throw new Error(result.message || "Failed to parse API data.");
            }
        } catch (error) {
            console.error(error);
            errorText.innerText = "Error: " + error.message;
            errorContainer.classList.remove('hidden');
        } finally {
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<span class="btn-text">Start Market Scan</span><span class="btn-icon">➔</span>';
            loader.classList.add('hidden');

            if (!resultsContainer.classList.contains('hidden')) {
                resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    });

    // ============================
    // Step 2: Wyckoff Analysis
    // ============================
    wyckoffBtn.addEventListener('click', async () => {
        if (screenerData.length === 0) return;

        // Collect Tickers from Screener results
        const symbols = screenerData.map(coin => coin.Ticker);

        wyckoffBtn.disabled = true;
        wyckoffBtn.innerHTML = '<span class="btn-text">Analyzing...</span>';
        wyckoffLoader.classList.remove('hidden');
        wyckoffResults.classList.add('hidden');
        wyckoffError.classList.add('hidden');
        wyckoffTableBody.innerHTML = '';
        pdfBtn.classList.add('hidden'); // Hide PDF button during analysis
        wyckoffPassedData = [];

        // Activate Step 2 indicator
        step2.classList.add('active');
        step2.classList.remove('completed');

        try {
            const response = await fetch('/api/wyckoff', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbols: symbols })
            });
            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                wyckoffStats.innerText = `${data.length} coins passed validation`;

                if (data.length === 0) {
                    wyckoffStats.innerText = 'No coins passed VCP validation';
                } else {
                    wyckoffPassedData = data; // Cache for PDF
                    pdfBtn.classList.remove('hidden'); // Show PDF button
                }

                data.forEach(coin => {
                    const row = document.createElement('tr');
                    const volDryUp = parseFloat(coin['Volume Dry-Up (%)']).toFixed(2);
                    const atrShrink = parseFloat(coin['ATR Shrinkage (%)']).toFixed(2);
                    const priceRange = parseFloat(coin['Price Range (%)']).toFixed(2);

                    // Format Timeframe Start - End
                    const timeframe = `${coin['Start Date']} - ${coin['End Date']}`;

                    row.innerHTML = `
                        <td class="symbol-cell">
                            <img src="https://ui-avatars.com/api/?name=${coin.Symbol.replace('/USDT', '')}&background=10b981&color=fff&rounded=true&size=32" alt="${coin.Symbol}" width="28" height="28" style="border-radius:50%">
                            ${coin.Symbol}
                        </td>
                        <td class="number-cell" style="font-size: 0.85rem;">${timeframe}</td>
                        <td class="number-cell value-compression">${volDryUp}%</td>
                        <td class="number-cell value-compression">${atrShrink}%</td>
                        <td class="number-cell value-compression">${priceRange}%</td>
                        <td class="number-cell">${coin['VPA Signal']}</td>
                        <td><span class="status-badge status-passed">✓ Passed</span></td>
                    `;
                    wyckoffTableBody.appendChild(row);
                });

                // Mark Step 2 as completed
                step2.classList.remove('active');
                step2.classList.add('completed');

                wyckoffResults.classList.remove('hidden');
            } else {
                throw new Error(result.message || "VCP analysis failed.");
            }
        } catch (error) {
            console.error(error);
            wyckoffErrorText.innerText = "Error: " + error.message;
            wyckoffError.classList.remove('hidden');
        } finally {
            wyckoffBtn.disabled = false;
            wyckoffBtn.innerHTML = '<span class="btn-text">Run VCP Analysis</span><span class="btn-icon">⚡</span>';
            wyckoffLoader.classList.add('hidden');

            if (!wyckoffResults.classList.contains('hidden')) {
                wyckoffResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    });

    // ============================
    // PDF Generation Logic
    // ============================
    pdfBtn.addEventListener('click', () => {
        if (wyckoffPassedData.length === 0) return;

        const doc = new window.jspdf.jsPDF();

        // Header
        doc.setFont("helvetica", "bold");
        doc.setFontSize(18);
        doc.text("NODE 1: VCP INSTITUTIONAL REPORT", 14, 22);

        // Sub-header (Date)
        const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        doc.setFontSize(11);
        doc.setFont("helvetica", "normal");
        doc.text(`Printed on: ${today}`, 14, 30);

        // Context Info
        const firstCoin = wyckoffPassedData[0];
        doc.text(`Analysis Timeframe: ${firstCoin['Start Date']} to ${firstCoin['End Date']} (500 Candle 4H)`, 14, 38);

        // Prepare data for table
        const tableColumn = ["Symbol", "Timeframe", "Vol Dry-Up (%)", "ATR Shrink (%)", "Price Range (%)", "VPA Signal", "Status"];
        const tableRows = [];

        wyckoffPassedData.forEach(coin => {
            const coinData = [
                coin.Symbol,
                `${coin['Start Date']} to ${coin['End Date']}`,
                `${parseFloat(coin['Volume Dry-Up (%)']).toFixed(2)}%`,
                `${parseFloat(coin['ATR Shrinkage (%)']).toFixed(2)}%`,
                `${parseFloat(coin['Price Range (%)']).toFixed(2)}%`,
                coin['VPA Signal'],
                "Passed"
            ];
            tableRows.push(coinData);
        });

        // Generate AutoTable
        doc.autoTable({
            head: [tableColumn],
            body: tableRows,
            startY: 45,
            styles: { fontSize: 10, cellPadding: 3 },
            headStyles: { fillColor: [99, 102, 241], textColor: [255, 255, 255] },
            alternateRowStyles: { fillColor: [240, 240, 245] },
            margin: { top: 45 }
        });

        // Save PDF
        doc.save("Node1_VCP_Report.pdf");
    });
});
