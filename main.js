document.addEventListener('DOMContentLoaded', () => {
    // ---------------------------------------------------------
    // 1. Digital Clock
    // ---------------------------------------------------------
    const updateClock = () => {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        const clockEl = document.getElementById('digital-clock');
        if (clockEl) clockEl.textContent = timeString;
    };
    setInterval(updateClock, 1000);
    updateClock();

    // ---------------------------------------------------------
    // 2. View Switching
    // ---------------------------------------------------------
    const navItems = document.querySelectorAll('.nav-item');
    const sections = {
        dashboard: document.getElementById('dashboard-view'),
        cameras: document.getElementById('cameras-view'),
        analyzer: document.getElementById('analyzer-view'),
        analytics: document.getElementById('analytics-view'),
        reports: document.getElementById('reports-view'),
        alerts: document.getElementById('alerts-view'),
        settings: document.getElementById('settings-view')
    };

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const page = item.getAttribute('data-page');
            if (!page || !sections[page]) return;

            e.preventDefault();

            navItems.forEach(ni => ni.classList.remove('active'));
            Object.values(sections).forEach(s => {
                if (s) s.classList.add('hidden');
            });

            item.classList.add('active');
            sections[page].classList.remove('hidden');
        });
    });

    // ---------------------------------------------------------
    // 3. Trend Chart
    // ---------------------------------------------------------
    const chartCanvas = document.getElementById('crowdTrendChart');
    if (chartCanvas) {
        const ctx = chartCanvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(0, 242, 255, 0.4)');
        gradient.addColorStop(1, 'rgba(0, 242, 255, 0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['22:30', '22:35', '22:40', '22:45', '22:50', '22:55', '23:00'],
                datasets: [{
                    label: 'People Count',
                    data: [850, 920, 880, 1050, 1100, 1080, 1092],
                    borderColor: '#00f2ff',
                    borderWidth: 3,
                    pointBackgroundColor: '#00f2ff',
                    pointBorderColor: 'rgba(255,255,255,0.5)',
                    pointHoverRadius: 6,
                    tension: 0.4,
                    fill: true,
                    backgroundColor: gradient
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#a0aec0', font: { family: 'Orbitron', size: 10 } } },
                    x: { grid: { display: false }, ticks: { color: '#a0aec0', font: { family: 'Orbitron', size: 10 } } }
                }
            }
        });
    }

    // ---------------------------------------------------------
    // 4. Simulated Live Dashboard Updates
    // ---------------------------------------------------------
    setInterval(() => {
        const gaugeFill = document.querySelector('.gauge-fill');
        const densityVal = document.querySelector('.risk-item .value');
        if (gaugeFill && densityVal) {
            const newVal = (0.08 + Math.random() * 0.04).toFixed(2);
            densityVal.textContent = newVal;
            gaugeFill.style.width = (100 - (parseFloat(newVal) * 100)) + '%';
        }
    }, 3000);

    // ---------------------------------------------------------
    // 5. AI Analyzer (Backend ML)
    // ---------------------------------------------------------
    const analyzeBtn = document.getElementById('analyze-btn');
    const analysisPanel = document.getElementById('analysis-panel');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const previewImg = document.getElementById('analysis-preview');
    // We don't need detection-canvas anymore since backend sends the annotated image
    const detectionCanvas = document.getElementById('detection-canvas');
    if (detectionCanvas) detectionCanvas.style.display = 'none';

    let currentFile = null;

    const handleFile = (file) => {
        if (!file) return;
        currentFile = file;
        const dropText = dropZone.querySelector('p');
        if (dropText) dropText.textContent = `File selected: ${file.name}`;
        dropZone.style.borderColor = '#37ff8b';

        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                if (previewImg) previewImg.src = e.target.result;
                analysisPanel.classList.add('hidden'); // Reset output on new upload
            };
            reader.readAsDataURL(file);
        } else if (file.type.startsWith('video/')) {
            if (dropText) dropText.textContent = `Video selected: ${file.name}`;
            analysisPanel.classList.add('hidden');
        }
    };

    const performAnalysis = async () => {
        if (!currentFile) {
            alert('Please select an image or video first.');
            return;
        }

        analyzeBtn.textContent = 'Analyzing with Model...';
        analyzeBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', currentFile);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error');
            }

            const result = await response.json();

            // Update UI with results
            updateAnalysisUI(result);

            analysisPanel.classList.remove('hidden');
            analysisPanel.scrollIntoView({ behavior: 'smooth' });
        } catch (err) {
            console.error('Analysis error:', err);
            alert('Error during analysis: ' + err.message);
        } finally {
            analyzeBtn.textContent = 'Analyze Now';
            analyzeBtn.disabled = false;
        }
    };

    const updateAnalysisUI = (result) => {
        const countVal = document.querySelector('.count-val');
        const densityLabel = document.getElementById('density-result');
        const occupancyFill = document.querySelector('.progress-fill.high');
        const occupancyVal = document.querySelector('.meter-val');
        const recText = document.getElementById('rec-text');

        if (countVal) countVal.textContent = result.people_count;

        if (densityLabel) {
            densityLabel.textContent = `${result.density_level} Crowd Density`;
            densityLabel.style.background = result.density_color;
            if (result.density_level === 'LOW') {
                densityLabel.style.color = '#000';
            } else {
                densityLabel.style.color = '#fff';
            }
        }

        if (occupancyFill) {
            occupancyFill.style.width = result.occupancy + '%';
            occupancyFill.style.background = result.density_color;
        }
        if (occupancyVal) occupancyVal.textContent = result.occupancy + '%';

        if (recText) recText.textContent = result.recommendation;

        // Update image with annotated result from backend
        if (previewImg && result.result_image) {
            previewImg.src = 'data:image/jpeg;base64,' + result.result_image;
        }
    };

    // Event Listeners
    if (fileInput) fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
    if (analyzeBtn) analyzeBtn.addEventListener('click', performAnalysis);
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = '#00f2ff'; });
        dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = 'rgba(255, 255, 255, 0.1)'; });
        dropZone.addEventListener('drop', (e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); });
        dropZone.addEventListener('click', () => fileInput.click());
    }

    // ---------------------------------------------------------
    // 6. Analytics View Logic
    // ---------------------------------------------------------
    let analyticsChartObj = null;
    const fetchAnalytics = async () => {
        try {
            const res = await fetch('/api/analytics');
            const data = await res.json();

            // Build Chart
            const ctx = document.getElementById('historicalAnalyticsChart');
            if (ctx) {
                if (analyticsChartObj) analyticsChartObj.destroy();

                const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
                gradient.addColorStop(0, 'rgba(0, 242, 255, 0.4)');
                gradient.addColorStop(1, 'rgba(0, 242, 255, 0)');

                analyticsChartObj = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Total People (Daily)',
                            data: data.datasets.total_people,
                            backgroundColor: gradient,
                            borderColor: '#00f2ff',
                            borderWidth: 1,
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#a0aec0', font: { family: 'Orbitron', size: 10 } } },
                            x: { grid: { display: false }, ticks: { color: '#a0aec0', font: { family: 'Orbitron', size: 10 } } }
                        }
                    }
                });
            }

            // Build Zones Grid
            const zonesGrid = document.getElementById('analytics-zones-grid');
            if (zonesGrid && data.zones) {
                zonesGrid.innerHTML = data.zones.map(z => `
                    <div class="stat-card">
                        <div class="stat-icon" style="background: rgba(0,255,213,0.1); color: var(--accent-teal)"><i class="fas fa-map-marker-alt"></i></div>
                        <div class="stat-info">
                            <h3>${z.name}</h3>
                            <div class="stat-value" style="font-size: 1.5rem">${z.current_count} People</div>
                            <div class="stat-change ${z.status === 'Crowded' ? 'negative' : (z.status === 'Quiet' ? 'positive' : '')}">${z.status} Zone</div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (err) {
            console.error("Failed to load analytics", err);
        }
    };

    // Refresh button
    const refreshBtn = document.getElementById('refresh-analytics');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchAnalytics);
    }

    // Nav listener patch to fetch analytics when tab is clicked
    const analyticsNav = document.querySelector('[data-page="analytics"]');
    if (analyticsNav) {
        analyticsNav.addEventListener('click', () => {
            setTimeout(fetchAnalytics, 100); // slight delay for DOM transition
        });
    }

});

