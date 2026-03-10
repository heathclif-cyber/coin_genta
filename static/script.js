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
    const step3 = document.getElementById('step-3-indicator');
    const step4 = document.getElementById('step-4-indicator');

    // PDF elements
    const pdfBtn = document.getElementById('pdf-btn');
    const pdfSentimentBtn = document.getElementById('pdf-sentiment-btn');

    // Store screener data for passing to Wyckoff
    let screenerData = [];
    let wyckoffPassedData = []; // Store passed data for PDF
    let onchainPassedData = []; // Store passed data for next step
    let sentimentPassedData = []; // Store passed data for Final PDF

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
                    const cleanSymbol = coin.Symbol.includes('/') ? coin.Symbol.split('/')[0] : coin.Symbol;
                    const lastCloseStr = `$${parseFloat(coin['Last Close']).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
                    const highStr = `$${parseFloat(coin['60D High']).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
                    const drawdownStr = parseFloat(coin['Drawdown (%)']).toFixed(2) + '%';
                    const rStr = parseFloat(coin['Relative_Strength_R']).toFixed(2);

                    row.innerHTML = `
                        <td class="symbol-cell">
                            <img src="https://assets.coincap.io/assets/icons/${cleanSymbol.toLowerCase()}@2x.png" onerror="this.src='https://ui-avatars.com/api/?name=${cleanSymbol}&background=random&color=fff&rounded=true'" alt="${cleanSymbol}" width="28" height="28" style="borderRadius:50%">
                            ${cleanSymbol}
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
                    const cleanSymbol = coin.Symbol.includes('/') ? coin.Symbol.split('/')[0] : coin.Symbol;
                    const volDryUp = parseFloat(coin['Volume Dry-Up (%)']).toFixed(2);
                    const atrShrink = parseFloat(coin['ATR Shrinkage (%)']).toFixed(2);
                    const priceRange = parseFloat(coin['Price Range (%)']).toFixed(2);

                    // Format Timeframe Start - End
                    const timeframe = `${coin['Start Date']} - ${coin['End Date']}`;

                    row.innerHTML = `
                        <td class="symbol-cell">
                            <img src="https://assets.coincap.io/assets/icons/${cleanSymbol.toLowerCase()}@2x.png" onerror="this.src='https://ui-avatars.com/api/?name=${cleanSymbol}&background=random&color=fff&rounded=true'" alt="${cleanSymbol}" width="28" height="28" style="borderRadius:50%">
                            ${cleanSymbol}
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
    // Step 3: On-Chain Analysis
    // ============================
    const onchainBtn = document.getElementById('onchain-btn');
    const onchainLoader = document.getElementById('onchain-loader');
    const onchainResults = document.getElementById('onchain-results');
    const onchainError = document.getElementById('onchain-error');
    const onchainErrorText = document.getElementById('onchain-error-text');
    const onchainTableBody = document.getElementById('onchain-table-body');
    const onchainStats = document.getElementById('onchain-stats');

    if (onchainBtn) {
        onchainBtn.addEventListener('click', async () => {
            if (wyckoffPassedData.length === 0) return;

            onchainBtn.disabled = true;
            onchainBtn.innerHTML = '<span class="btn-text">Analyzing...</span>';
            onchainLoader.classList.remove('hidden');
            onchainResults.classList.add('hidden');
            onchainError.classList.add('hidden');
            onchainTableBody.innerHTML = '';

            // Activate Step 3 indicator
            if (step3) {
                step3.classList.add('active');
                step3.classList.remove('completed');
            }

            try {
                const response = await fetch('/api/onchain', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ coins: wyckoffPassedData })
                });
                const result = await response.json();

                if (result.status === 'success') {
                    const data = result.data;
                    onchainStats.innerText = `${data.length} coins passed validation`;

                    if (data.length === 0) {
                        onchainStats.innerText = 'No coins passed On-Chain validation';
                    } else {
                        onchainPassedData = data;
                    }

                    data.forEach(coin => {
                        const row = document.createElement('tr');
                        const cleanSymbol = coin.Symbol.includes('/') ? coin.Symbol.split('/')[0] : coin.Symbol;

                        row.innerHTML = `
                            <td class="symbol-cell">
                                <img src="https://assets.coincap.io/assets/icons/${cleanSymbol.toLowerCase()}@2x.png" onerror="this.src='https://ui-avatars.com/api/?name=${cleanSymbol}&background=random&color=fff&rounded=true'" alt="${cleanSymbol}" width="28" height="28" style="borderRadius:50%">
                                ${cleanSymbol}
                            </td>
                            <td class="number-cell">${coin['Netflow Status']}</td>
                            <td class="number-cell">${coin['Wallet Age Ratio']}</td>
                            <td class="number-cell">${coin['SSR Status']}</td>
                            <td><span class="status-badge status-passed">💎 Passed</span></td>
                        `;
                        onchainTableBody.appendChild(row);
                    });

                    // Mark Step 3 as completed
                    if (step3) {
                        step3.classList.remove('active');
                        step3.classList.add('completed');
                    }

                    onchainResults.classList.remove('hidden');
                } else {
                    throw new Error(result.message || "On-Chain analysis failed.");
                }
            } catch (error) {
                console.error(error);
                onchainErrorText.innerText = "Error: " + error.message;
                onchainError.classList.remove('hidden');
            } finally {
                onchainBtn.disabled = false;
                onchainBtn.innerHTML = '<span class="btn-text">Run On-Chain Verification</span><span class="btn-icon">🔗</span>';
                onchainLoader.classList.add('hidden');

                if (!onchainResults.classList.contains('hidden')) {
                    onchainResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    }

    // ============================
    // Step 4: Sentiment Analysis
    // ============================
    const sentimentBtn = document.getElementById('sentiment-btn');
    const sentimentLoader = document.getElementById('sentiment-loader');
    const sentimentResults = document.getElementById('sentiment-results');
    const sentimentError = document.getElementById('sentiment-error');
    const sentimentErrorText = document.getElementById('sentiment-error-text');
    const sentimentTableBody = document.getElementById('sentiment-table-body');
    const sentimentStats = document.getElementById('sentiment-stats');

    if (sentimentBtn) {
        sentimentBtn.addEventListener('click', async () => {
            if (onchainPassedData.length === 0) return;

            sentimentBtn.disabled = true;
            sentimentBtn.innerHTML = '<span class="btn-text">Analyzing...</span>';
            sentimentLoader.classList.remove('hidden');
            sentimentResults.classList.add('hidden');
            sentimentError.classList.add('hidden');
            sentimentTableBody.innerHTML = '';
            if (pdfSentimentBtn) pdfSentimentBtn.classList.add('hidden');
            sentimentPassedData = [];

            // Activate Step 4 indicator
            if (step4) {
                step4.classList.add('active');
                step4.classList.remove('completed');
            }

            try {
                const response = await fetch('/api/sentiment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ coins: onchainPassedData })
                });
                const result = await response.json();

                if (result.status === 'success') {
                    const data = result.data;
                    sentimentStats.innerText = `${data.length} coins passed validation`;

                    if (data.length === 0) {
                        sentimentStats.innerText = 'No coins passed Sentiment validation (Market not in Extreme Fear)';
                    } else {
                        sentimentPassedData = data;
                        if (pdfSentimentBtn) pdfSentimentBtn.classList.remove('hidden');
                    }

                    data.forEach(coin => {
                        const row = document.createElement('tr');
                        const cleanSymbol = coin.Symbol.includes('/') ? coin.Symbol.split('/')[0] : coin.Symbol;

                        row.innerHTML = `
                            <td class="symbol-cell">
                                <img src="https://assets.coincap.io/assets/icons/${cleanSymbol.toLowerCase()}@2x.png" onerror="this.src='https://ui-avatars.com/api/?name=${cleanSymbol}&background=random&color=fff&rounded=true'" alt="${cleanSymbol}" width="28" height="28" style="borderRadius:50%">
                                ${cleanSymbol}
                            </td>
                            <td class="number-cell">${coin['Overall On-Chain Validation']}</td>
                            <td class="number-cell" style="font-weight: 700; color: #ef4444;">${coin['Sentiment Score']}</td>
                            <td class="number-cell">${coin['Sentiment Status']}</td>
                            <td><span class="status-badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3);">🏆 Ultimate Final</span></td>
                        `;
                        sentimentTableBody.appendChild(row);
                    });

                    // Mark Step 4 as completed
                    if (step4) {
                        step4.classList.remove('active');
                        step4.classList.add('completed');
                    }

                    sentimentResults.classList.remove('hidden');
                } else {
                    throw new Error(result.message || "Sentiment analysis failed.");
                }
            } catch (error) {
                console.error(error);
                sentimentErrorText.innerText = "Error: " + error.message;
                sentimentError.classList.remove('hidden');
            } finally {
                sentimentBtn.disabled = false;
                sentimentBtn.innerHTML = '<span class="btn-text">Run Sentiment & Divergence Audit</span><span class="btn-icon">👁️</span>';
                sentimentLoader.classList.add('hidden');

                if (!sentimentResults.classList.contains('hidden')) {
                    sentimentResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    }


    // ============================
    // PDF Generation Logic (Node 3 Final Report)
    // ============================
    if (pdfSentimentBtn) {
        pdfSentimentBtn.addEventListener('click', () => {
            if (sentimentPassedData.length === 0) return;

            const doc = new window.jspdf.jsPDF();

            // Header
            doc.setFont("helvetica", "bold");
            doc.setFontSize(18);
            doc.text("GENUINE ALPHA INSTITUTIONAL REPORT", 14, 22);

            // Sub-header (Date)
            const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
            doc.setFontSize(11);
            doc.setFont("helvetica", "normal");
            doc.text(`Printed on: ${today}`, 14, 30);

            // Context Info - Extract Global Sentiment from the first passed coin
            const firstCoin = sentimentPassedData[0];
            const globalSentimentScore = firstCoin['Sentiment Score'];
            const globalSentimentStatus = firstCoin['Sentiment Status'];

            doc.setFont("helvetica", "bold");
            doc.text(`GLOBAL MARKET SENTIMENT: ${globalSentimentScore}/100 [ ${globalSentimentStatus} ]`, 14, 38);

            doc.setFont("helvetica", "normal");
            doc.text(`VCP Timeframe: ${firstCoin['Start Date']} to ${firstCoin['End Date']}`, 14, 46);

            // Prepare data for table
            const tableColumn = ["Symbol", "VPA Signal", "Netflow Status", "Wallet Age", "SSR Index", "Sentiment", "Final Valid"];
            const tableRows = [];

            sentimentPassedData.forEach(coin => {
                const coinData = [
                    coin.Symbol,
                    coin['VPA Signal'] || '-',
                    coin['Netflow Status'] || '-',
                    coin['Wallet Age Ratio'] || '-',
                    coin['SSR Status'] || '-',
                    coin['Sentiment Status'] || '-',
                    "💎 PASSED"
                ];
                tableRows.push(coinData);
            });

            // Generate AutoTable
            doc.autoTable({
                head: [tableColumn],
                body: tableRows,
                startY: 55,
                styles: { fontSize: 8, cellPadding: 3 },
                headStyles: { fillColor: [245, 158, 11], textColor: [255, 255, 255] }, // Amber/Orange institutional theme
                alternateRowStyles: { fillColor: [250, 245, 235] },
                margin: { top: 55 }
            });

            // Save PDF
            doc.save("Genuine_Alpha_Ultimate_Report.pdf");
        });
    }
});
