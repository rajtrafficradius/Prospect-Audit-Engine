document.addEventListener('DOMContentLoaded', () => {
    const state = {
        theme: 'light',
        mode: 'audit',
        competitors: []
    };

    const form = document.getElementById('auditForm');
    const domainInput = document.getElementById('domain');
    const companyInput = document.getElementById('company');
    const competitorInput = document.getElementById('competitorInput');
    const addCompetitorBtn = document.getElementById('addCompetitorBtn');
    const competitorList = document.getElementById('competitorList');
    const competitorCount = document.getElementById('competitorCount');
    const competitorSummary = document.getElementById('competitorSummary');
    const competitorHelper = document.getElementById('competitorHelper');
    const submitBtn = document.getElementById('submitBtn');
    const submitLabel = submitBtn.querySelector('.submit-label');
    const btnIcon = submitBtn.querySelector('[data-submit-icon]');
    const btnSpinner = document.getElementById('btnSpinner');
    const themeDarkBtn = document.getElementById('themeDarkBtn');
    const themeLightBtn = document.getElementById('themeLightBtn');
    const authThemeDarkBtn = document.getElementById('authThemeDarkBtn');
    const authThemeLightBtn = document.getElementById('authThemeLightBtn');
    const modeButtons = document.querySelectorAll('.mode-chip');
    const auditPanel = document.getElementById('auditPanel');
    const competitorsPanel = document.getElementById('competitorsPanel');
    const authShell = document.getElementById('authShell');
    const appRoot = document.getElementById('appRoot');
    const loginForm = document.getElementById('loginForm');
    const authEmail = document.getElementById('authEmail');
    const authPassword = document.getElementById('authPassword');
    const guestLoginBtn = document.getElementById('guestLoginBtn');
    const authNotice = document.getElementById('authNotice');

    const heroSection = document.getElementById('heroSection');
    const workspace = document.getElementById('workspace');
    const currentFocusText = document.getElementById('currentFocusText');
    const activeTargetDomain = document.getElementById('activeTargetDomain');
    const targetBadge = document.querySelector('.target-badge');
    const agentLiveStatus = document.getElementById('agentLiveStatus');
    const centralOrb = document.getElementById('centralOrb');
    const agentMainState = document.getElementById('agentMainState');
    const agentSubState = document.getElementById('agentSubState');
    const artifactVault = document.getElementById('artifactVault');
    const logList = document.getElementById('logList');
    const terminalWindow = document.getElementById('terminalWindow');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const stdoutStatusPill = document.getElementById('stdoutStatusPill');
    const stdoutCurrentStage = document.getElementById('stdoutCurrentStage');
    const stdoutCurrentMessage = document.getElementById('stdoutCurrentMessage');
    const stdoutMiniProgressFill = document.getElementById('stdoutMiniProgressFill');
    const stdoutStepMeta = document.getElementById('stdoutStepMeta');
    const stdoutFileMeta = document.getElementById('stdoutFileMeta');
    const stdoutFileList = document.getElementById('stdoutFileList');

    const agentNodes = {
        extraction: document.getElementById('node-extraction'),
        vision: document.getElementById('node-vision'),
        market: document.getElementById('node-market'),
        rag: document.getElementById('node-rag'),
        synthesis: document.getElementById('node-synthesis')
    };

    const historyModal = document.getElementById('historyModal');
    const openHistoryBtn = document.getElementById('openHistoryBtn');
    const closeHistoryBtn = document.getElementById('closeHistoryBtn');
    const historyList = document.getElementById('historyList');

    const previewModal = document.getElementById('previewModal');
    const closePreviewBtn = document.getElementById('closePreviewBtn');
    const previewContent = document.getElementById('previewContent');
    const commandOrbit = document.querySelector('.side-orbit');
    const authCubeScene = document.querySelector('.auth-cube-scene');

    let eventSource = null;
    let currentJobId = null;
    const AUTH_SESSION_KEY = 'radius-auth-session';

    function renderIcons() {
        feather.replace();
    }

    function initPremiumMotion() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        let rafId = null;
        let targetX = window.innerWidth * 0.5;
        let targetY = window.innerHeight * 0.24;

        const updatePointerGlow = () => {
            document.documentElement.style.setProperty('--pointer-x', `${targetX}px`);
            document.documentElement.style.setProperty('--pointer-y', `${targetY}px`);
            rafId = null;
        };

        const queuePointerGlow = (x, y) => {
            targetX = x;
            targetY = y;
            if (rafId) return;
            rafId = window.requestAnimationFrame(updatePointerGlow);
        };

        window.addEventListener('mousemove', (event) => {
            queuePointerGlow(event.clientX, event.clientY);
        }, { passive: true });

        window.addEventListener('mouseleave', () => {
            queuePointerGlow(window.innerWidth * 0.5, window.innerHeight * 0.24);
        });
    }

    function initCommandCenterMotion() {
        if (!commandOrbit || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        if (!commandOrbit.querySelector('.orbit-particle')) {
            const particleConfigs = [
                { left: '24%', top: '32%', duration: '7.2s', delay: '-0.8s' },
                { left: '68%', top: '26%', duration: '8.8s', delay: '-2.1s' },
                { left: '58%', top: '62%', duration: '9.6s', delay: '-1.2s' },
                { left: '34%', top: '70%', duration: '7.9s', delay: '-3.6s' },
                { left: '76%', top: '48%', duration: '8.4s', delay: '-4.3s' },
                { left: '18%', top: '52%', duration: '10.2s', delay: '-2.8s' }
            ];

            particleConfigs.forEach((config) => {
                const particle = document.createElement('span');
                particle.className = 'orbit-particle';
                particle.style.left = config.left;
                particle.style.top = config.top;
                particle.style.setProperty('--particle-duration', config.duration);
                particle.style.setProperty('--particle-delay', config.delay);
                commandOrbit.appendChild(particle);
            });
        }

        const setOrbitShift = (x, y, glowScale = 1) => {
            commandOrbit.style.setProperty('--orbit-shift-x', `${x}px`);
            commandOrbit.style.setProperty('--orbit-shift-y', `${y}px`);
            commandOrbit.style.setProperty('--orbit-glow-scale', String(glowScale));
        };

        commandOrbit.addEventListener('mousemove', (event) => {
            const bounds = commandOrbit.getBoundingClientRect();
            const relativeX = ((event.clientX - bounds.left) / bounds.width - 0.5) * 14;
            const relativeY = ((event.clientY - bounds.top) / bounds.height - 0.5) * 14;
            setOrbitShift(relativeX, relativeY, 1.08);
        }, { passive: true });

        commandOrbit.addEventListener('mouseleave', () => {
            setOrbitShift(0, 0, 1);
        });
    }

    function initAuthVisualMotion() {
        if (!authCubeScene || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        const setAuthShift = (x, y, glowScale = 1) => {
            authCubeScene.style.setProperty('--auth-shift-x', `${x}px`);
            authCubeScene.style.setProperty('--auth-shift-y', `${y}px`);
            authCubeScene.style.setProperty('--auth-glow-scale', String(glowScale));
        };

        authCubeScene.addEventListener('mousemove', (event) => {
            const bounds = authCubeScene.getBoundingClientRect();
            const relativeX = ((event.clientX - bounds.left) / bounds.width - 0.5) * 16;
            const relativeY = ((event.clientY - bounds.top) / bounds.height - 0.5) * 16;
            setAuthShift(relativeX, relativeY, 1.04);
        }, { passive: true });

        authCubeScene.addEventListener('mouseleave', () => {
            setAuthShift(0, 0, 1);
        });
    }

    function setTheme(theme) {
        state.theme = theme;
        document.body.dataset.theme = theme;
        themeDarkBtn?.classList.toggle('active', theme === 'dark');
        themeLightBtn?.classList.toggle('active', theme === 'light');
        authThemeDarkBtn?.classList.toggle('active', theme === 'dark');
        authThemeLightBtn?.classList.toggle('active', theme === 'light');
        renderIcons();
    }

    function setAuthNotice(message, variant = 'info') {
        if (!authNotice) return;
        const iconMap = {
            info: 'info',
            success: 'check-circle',
            error: 'alert-triangle'
        };
        authNotice.className = `auth-notice is-${variant}`;
        authNotice.innerHTML = `
            <i data-feather="${iconMap[variant] || 'info'}"></i>
            <span>${escapeHtml(message)}</span>
        `;
        renderIcons();
    }

    function showDashboard() {
        authShell?.classList.add('hidden');
        appRoot?.classList.remove('hidden');
    }

    function showAuth() {
        authShell?.classList.remove('hidden');
        appRoot?.classList.add('hidden');
    }

    function persistSession(payload) {
        try {
            sessionStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(payload));
        } catch (error) {
            console.warn('Unable to persist auth session', error);
        }
    }

    function readSession() {
        try {
            const raw = sessionStorage.getItem(AUTH_SESSION_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (error) {
            console.warn('Unable to read auth session', error);
            return null;
        }
    }

    function completeAuthSession(payload) {
        persistSession({
            ...payload,
            theme: state.theme,
            timestamp: Date.now()
        });
        showDashboard();
    }

    function loginAsGuest() {
        setAuthNotice('Guest access enabled. You can launch audits immediately while credential-based sign-in is prepared for future integration.', 'success');
        completeAuthSession({
            role: 'guest',
            access: 'guest',
            label: 'Guest Session'
        });
    }

    function setStdoutStatus(status, label, message) {
        if (!stdoutStatusPill) return;
        stdoutStatusPill.className = `stdout-status-pill ${status}`;
        stdoutStatusPill.innerHTML = `<i data-feather="${status === 'success' ? 'check-circle' : status === 'error' ? 'alert-triangle' : status === 'processing' ? 'loader' : 'activity'}"></i><span>${escapeHtml(label)}</span>`;
        stdoutCurrentStage.textContent = label;
        stdoutCurrentMessage.textContent = message;
        renderIcons();
    }

    function setStdoutProgress(percent, description) {
        const normalized = Math.max(0, Math.min(100, percent));
        stdoutMiniProgressFill.style.width = `${normalized}%`;
        stdoutStepMeta.textContent = `${normalized}%`;
        if (description) stdoutCurrentMessage.textContent = description;
    }

    function renderStdoutEmptyFiles() {
        stdoutFileList.innerHTML = `
            <div class="stdout-empty">
                <i data-feather="folder"></i>
                <div>
                    <strong>No files yet</strong>
                    <span>Completed deliverables will appear here as they are compiled.</span>
                </div>
            </div>
        `;
        stdoutFileMeta.textContent = 'Waiting';
        renderIcons();
    }

    function appendStdoutStep({ status = 'pending', icon = 'activity', title, detail }) {
        const currentActive = logList.querySelector('.active');
        if (currentActive) currentActive.classList.remove('active');

        const item = document.createElement('li');
        item.className = `log-item ${status === 'processing' ? 'active node-marker' : status === 'success' ? 'success-marker' : status === 'error' ? 'error-marker' : ''}`.trim();
        item.innerHTML = `
            <div class="stdout-step-icon"><i data-feather="${icon}"></i></div>
            <div class="stdout-step-content">
                <div class="stdout-step-title">${escapeHtml(title)}</div>
                <div class="stdout-step-detail">${escapeHtml(detail)}</div>
            </div>
        `;
        logList.appendChild(item);
        terminalWindow.scrollTop = terminalWindow.scrollHeight;
        renderIcons();
    }

    function addStdoutFile(name, note, icon = 'file-text') {
        const safeId = `file-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
        if (stdoutFileList.querySelector(`[data-file-id="${safeId}"]`)) return;
        if (stdoutFileList.querySelector('.stdout-empty')) stdoutFileList.innerHTML = '';

        const item = document.createElement('div');
        item.className = 'stdout-file-entry';
        item.dataset.fileId = safeId;
        item.innerHTML = `
            <i data-feather="${icon}"></i>
            <div class="stdout-file-copy">
                <div class="stdout-file-name">${escapeHtml(name)}</div>
                <div class="stdout-file-note">${escapeHtml(note)}</div>
            </div>
        `;
        stdoutFileList.appendChild(item);
        stdoutFileMeta.textContent = `${stdoutFileList.querySelectorAll('.stdout-file-entry').length} saved`;
        renderIcons();
    }

    function setMode(mode) {
        state.mode = mode;
        modeButtons.forEach((button) => {
            const active = button.dataset.mode === mode;
            button.classList.toggle('active', active);
            button.setAttribute('aria-selected', String(active));
        });

        const auditActive = mode === 'audit';
        auditPanel.classList.toggle('active', auditActive);
        competitorsPanel.classList.toggle('active', !auditActive);
        auditPanel.setAttribute('aria-hidden', String(!auditActive));
        competitorsPanel.setAttribute('aria-hidden', String(auditActive));
        auditPanel.hidden = !auditActive;
        competitorsPanel.hidden = auditActive;
    }

    function renderCompetitors() {
        competitorCount.textContent = String(state.competitors.length);

        if (state.competitors.length === 0) {
            competitorList.innerHTML = `
                <div class="competitor-empty">
                    <i data-feather="users"></i>
                    <div>
                        <strong>No competitors added</strong>
                        <span>Add up to three competitors to enrich the comparison context.</span>
                    </div>
                </div>
            `;
            competitorSummary.textContent = 'No competitors added yet.';
        } else {
            competitorList.innerHTML = state.competitors
                .map((competitor, index) => `
                    <article class="competitor-pill">
                        <div class="competitor-pill-copy">
                            <span class="pill-index">Competitor ${index + 1}</span>
                            <strong>${escapeHtml(competitor)}</strong>
                        </div>
                        <button type="button" class="pill-remove" data-index="${index}" aria-label="Remove ${escapeHtml(competitor)}">
                            <i data-feather="x"></i>
                        </button>
                    </article>
                `)
                .join('');
            competitorSummary.innerHTML = state.competitors
                .map((competitor) => `<span class="summary-pill">${escapeHtml(competitor)}</span>`)
                .join('');
        }

        const limitReached = state.competitors.length >= 3;
        addCompetitorBtn.disabled = limitReached;
        competitorInput.disabled = limitReached;
        competitorHelper.textContent = limitReached
            ? 'Competitor limit reached. Remove one to add another.'
            : 'Competitors will be included in the request payload for downstream processing.';

        renderIcons();
    }

    function addCompetitor() {
        const value = competitorInput.value.trim();
        if (!value) {
            competitorHelper.textContent = 'Enter a competitor name before adding it.';
            return;
        }

        if (state.competitors.some((name) => name.toLowerCase() === value.toLowerCase())) {
            competitorHelper.textContent = 'That competitor is already listed.';
            return;
        }

        if (state.competitors.length >= 3) {
            competitorHelper.textContent = 'You can add up to 3 competitors only.';
            return;
        }

        state.competitors.push(value);
        competitorInput.value = '';
        competitorHelper.textContent = 'Competitor added successfully.';
        renderCompetitors();
    }

    competitorList.addEventListener('click', (event) => {
        const button = event.target.closest('.pill-remove');
        if (!button) return;
        const index = Number(button.dataset.index);
        state.competitors.splice(index, 1);
        competitorHelper.textContent = 'Competitor removed.';
        renderCompetitors();
    });

    addCompetitorBtn.addEventListener('click', addCompetitor);
    competitorInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            addCompetitor();
        }
    });

    modeButtons.forEach((button) => {
        button.addEventListener('click', () => setMode(button.dataset.mode));
    });

    themeDarkBtn?.addEventListener('click', () => setTheme('dark'));
    themeLightBtn?.addEventListener('click', () => setTheme('light'));
    authThemeDarkBtn?.addEventListener('click', () => setTheme('dark'));
    authThemeLightBtn?.addEventListener('click', () => setTheme('light'));

    loginForm?.addEventListener('submit', (event) => {
        event.preventDefault();
        const email = authEmail?.value.trim() || '';
        const password = authPassword?.value.trim() || '';

        if (!email || !password) {
            setAuthNotice('Use Continue as Guest now, or enter both email and password to preview the future credential-based sign-in flow.', 'error');
            if (!email) authEmail?.focus();
            else authPassword?.focus();
            return;
        }

        setAuthNotice('Credential sign-in is running in preview mode. Real authentication can be connected here later without changing the dashboard flow.', 'success');
        completeAuthSession({
            role: 'user',
            access: 'scoped',
            label: email,
            email
        });
    });

    guestLoginBtn?.addEventListener('click', loginAsGuest);

    openHistoryBtn.addEventListener('click', async () => {
        historyModal.classList.remove('hidden');
        historyList.innerHTML = '<div class="spinner" style="margin: 40px auto;"></div>';

        try {
            const res = await fetch('/api/history');
            const data = await res.json();

            if (!data.history || data.history.length === 0) {
                historyList.innerHTML = '<p class="modal-empty">No archives found. Your past audits will appear here.</p>';
                return;
            }

            let html = '<div class="history-grid">';
            data.history.forEach((item) => {
                html += `
                    <div class="history-card">
                        <div class="hc-header">
                            <div class="hc-domain">${escapeHtml(item.domain || 'Unknown domain')}</div>
                            <div class="hc-company">${escapeHtml(item.company || 'Unknown company')}</div>
                            <div class="hc-date">${escapeHtml(item.date || 'Unknown date')} • Vault: ${(item.archive_id || 'Legacy').slice(0, 8)}</div>
                        </div>
                        <div class="hc-actions">
                            <a href="/api/download/${item.archive_id}/docx" class="btn-dl docx" target="_blank"><i data-feather="file-text"></i> DOCX</a>
                            <a href="/api/download/${item.archive_id}/xlsx" class="btn-dl xlsx" target="_blank"><i data-feather="grid"></i> XLSX</a>
                            <a href="/api/download/${item.archive_id}/pptx" class="btn-dl pptx" target="_blank"><i data-feather="monitor"></i> PPTX</a>
                            <button type="button" class="btn-dl preview-btn" onclick="openLivePreview('${item.archive_id}')"><i data-feather="eye"></i> Preview</button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            historyList.innerHTML = html;
            renderIcons();
        } catch (error) {
            historyList.innerHTML = '<p class="modal-error">Error securely connecting to Archive Vault.</p>';
        }
    });

    closeHistoryBtn.addEventListener('click', () => historyModal.classList.add('hidden'));
    closePreviewBtn.addEventListener('click', () => previewModal.classList.add('hidden'));
    historyModal.addEventListener('click', (event) => {
        if (event.target === historyModal) historyModal.classList.add('hidden');
    });
    previewModal.addEventListener('click', (event) => {
        if (event.target === previewModal) previewModal.classList.add('hidden');
    });

    window.openLivePreview = async (archiveId) => {
        previewModal.classList.remove('hidden');
        previewContent.innerHTML = '<div class="spinner" style="margin: 40px auto;"></div><p class="modal-loading">Decrypting Vault Artifacts...</p>';

        try {
            const res = await fetch(`/output/archives/${archiveId}/strategy_narrative.json`);
            if (!res.ok) throw new Error('Preview format not supported on older legacy archives.');

            const data = await res.json();
            let html = '<div class="report-reader">';
            html += `<h1>Executive Summary</h1><p>${escapeHtml(data.executive_summary || 'N/A')}</p>`;
            html += `<h2>Competitive Landscape</h2><p>${escapeHtml(data.competitive_landscape_analysis || 'N/A')}</p>`;

            if (data.integrated_strategy_technical) {
                html += `<h2>Technical & AI Readiness (Pillar 1)</h2><p>${escapeHtml(data.integrated_strategy_technical.overview || 'N/A')}</p>`;
                if (data.integrated_strategy_technical.key_initiatives) {
                    html += `<ul>${data.integrated_strategy_technical.key_initiatives.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
                }
            }

            if (data.content_strategy_roadmap && data.content_strategy_roadmap.length > 0) {
                html += '<h2>Key Content Opportunities</h2>';
                data.content_strategy_roadmap.forEach((pillar) => {
                    html += `<h3>${escapeHtml(pillar.topic)}</h3><p>${escapeHtml(pillar.rationale)}</p>`;
                    if (pillar.sub_topics) {
                        html += `<ul>${pillar.sub_topics.map((topic) => `<li>${escapeHtml(topic)}</li>`).join('')}</ul>`;
                    }
                });
            }

            html += '</div>';
            previewContent.innerHTML = html;
        } catch (error) {
            previewContent.innerHTML = `<p class="modal-error"><i data-feather="alert-triangle"></i> ${escapeHtml(error.message)}</p>`;
            renderIcons();
        }
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const domain = domainInput.value.trim();
        const company = companyInput.value.trim();

        if (!domain || !company) {
            competitorHelper.textContent = 'Please enter both company website URL and company name before launching the audit.';
            setMode('audit');
            if (!domain) domainInput.focus();
            else companyInput.focus();
            return;
        }

        btnIcon?.classList.add('hidden');
        btnSpinner.classList.remove('hidden');
        submitBtn.disabled = true;
        submitLabel.textContent = 'Launching audit';

        const formData = new FormData();
        formData.append('domain', domain);
        formData.append('company', company);
        formData.append('mode', state.mode);
        formData.append('competitors', JSON.stringify(state.competitors));
        state.competitors.forEach((competitor, index) => {
            formData.append(`competitor_${index + 1}`, competitor);
        });

        try {
            const response = await fetch('/api/start-audit', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            currentJobId = data.job_id;

            setTimeout(() => {
                heroSection.classList.add('hidden');
                workspace.classList.remove('hidden');
                activeTargetDomain.innerText = `${company} • ${domain}`;
                targetBadge.classList.add('active');
                resetWorkspaceState();
                startLogStream(currentJobId);
            }, 450);
        } catch (error) {
            console.error(error);
            submitBtn.disabled = false;
            btnIcon?.classList.remove('hidden');
            btnSpinner.classList.add('hidden');
            submitLabel.textContent = 'Run Strategic Audit';
            window.alert('Connection error deploying agent swarm.');
        }
    });

    function resetWorkspaceState() {
        if (eventSource) eventSource.close();
        logList.innerHTML = '';
        artifactVault.classList.add('hidden');
        agentLiveStatus.classList.remove('hidden');
        progressContainer.classList.add('hidden');
        progressFill.style.width = '0%';
        progressText.innerText = '0% | Initializing...';
        centralOrb.className = 'giant-orb booting';
        agentMainState.innerText = 'Agent Deployed';
        agentSubState.innerText = 'Connecting to LangGraph network...';
        currentFocusText.innerText = 'Initializing Swarm...';
        setStdoutStatus('pending', 'Awaiting launch', 'Generation steps, live status, and saved files will appear here once the audit starts.');
        setStdoutProgress(0, 'Generation steps, live status, and saved files will appear here once the audit starts.');
        renderStdoutEmptyFiles();

        Object.values(agentNodes).forEach((node) => {
            node.className = 'node-item pending';
            node.querySelector('.node-status').innerText = 'Awaiting...';
        });
    }

    function startLogStream(jobId) {
        eventSource = new EventSource(`/api/stream-logs/${jobId}`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.done) {
                eventSource.close();
                if (data.status === 'completed') {
                    finishPipeline(jobId);
                } else {
                    handleError(data.message || 'Pipeline failed.');
                }
                return;
            }
            if (data.log) parseAndRenderLog(data.log);
        };

        eventSource.onerror = () => {
            eventSource.close();
        };
    }

    function parseAndRenderLog(rawText) {
        if (rawText.includes(': keep-alive ping')) return;

        if (rawText.includes('[PROGRESS]')) {
            const match = rawText.match(/\[PROGRESS\]\s*([^|]+)\|\s*(.*)/);
            if (match) {
                const percentInt = parseInt(match[1].trim(), 10);
                const desc = match[2].trim();
                progressContainer.classList.remove('hidden');
                const currentWidth = parseFloat(progressFill.style.width) || 0;
                if (percentInt > currentWidth) progressFill.style.width = `${percentInt}%`;
                progressText.innerText = `${percentInt}% | ${desc}`;
                setStdoutStatus('processing', 'Generating deliverables', desc);
                setStdoutProgress(percentInt, desc);
                return;
            }
        }

        if (rawText.includes('Phase 1, 1.5 & 2')) {
            setNodeActive('extraction');
            setNodeActive('vision');
            setNodeActive('market');
            centralOrb.className = 'giant-orb extracting';
            agentMainState.innerText = 'Extracting Intelligence';
            agentSubState.innerText = 'Scraping UI, SEO seeds, and market KPIs in parallel.';
            currentFocusText.innerText = 'Parallel Data Extraction';
            setStdoutStatus('processing', 'Parallel Data Extraction', 'Scraping UI, SEO seeds, and market KPIs in parallel.');
            appendStdoutStep({
                status: 'processing',
                icon: 'database',
                title: 'Parallel Data Extraction',
                detail: 'UI, CRO, and market intelligence collection has started across the active agent nodes.'
            });
            return;
        } else if (rawText.includes('Phase 4: Constructing Recursive FAISS')) {
            setNodeDone('extraction');
            setNodeDone('vision');
            setNodeDone('market');
            setNodeActive('rag');
            centralOrb.className = 'giant-orb extracting';
            agentMainState.innerText = 'Vectorizing Context';
            agentSubState.innerText = 'Building local RAG database for rapid retrieval.';
            currentFocusText.innerText = 'RAG Vector Indexing';
            setStdoutStatus('processing', 'RAG Vector Indexing', 'Building the retrieval layer for contextual strategy synthesis.');
            appendStdoutStep({
                status: 'processing',
                icon: 'layers',
                title: 'RAG Vector Indexing',
                detail: 'Recursive FAISS construction is in progress for local retrieval and synthesis support.'
            });
            return;
        } else if (rawText.includes('Phase 5: GPT-4o AEO Strategy Synthesis')) {
            setNodeDone('rag');
            setNodeActive('synthesis');
            centralOrb.className = 'giant-orb synthesizing';
            agentMainState.innerText = 'Synthesizing Strategy';
            agentSubState.innerText = 'GPT-4o is writing the integrated narrative parameters.';
            currentFocusText.innerText = 'LLM Narrative Generation';
            setStdoutStatus('processing', 'LLM Narrative Generation', 'The strategy narrative and recommendations are being assembled.');
            appendStdoutStep({
                status: 'processing',
                icon: 'edit-3',
                title: 'LLM Narrative Generation',
                detail: 'The model is synthesizing strategic findings into executive-ready guidance.'
            });
            return;
        } else if (rawText.includes('Phase 6: Injecting Dynamic Architecture')) {
            setNodeDone('synthesis');
            centralOrb.className = 'giant-orb booting';
            agentMainState.innerText = 'Compiling Deliverables';
            agentSubState.innerText = 'Generating dynamic charts, Excel models, and native DOCX.';
            currentFocusText.innerText = 'File Compilation';
            setStdoutStatus('processing', 'File Compilation', 'Preparing final deliverables and packaging outputs.');
            appendStdoutStep({
                status: 'processing',
                icon: 'package',
                title: 'File Compilation',
                detail: 'Generating dynamic charts, spreadsheet models, presentation, and document outputs.'
            });
            return;
        } else if (rawText.includes('✅')) {
            setStdoutStatus('success', 'Step completed', rawText.replace('✅', '').trim() || 'Completed successfully.');
            appendStdoutStep({
                status: 'success',
                icon: 'check-circle',
                title: 'Completed',
                detail: rawText.replace('✅', '').trim() || 'Completed successfully.'
            });
            return;
        } else if (rawText.includes('[!]')) {
            setStdoutStatus('error', 'Pipeline issue detected', rawText.replace('[!]', '').trim() || 'An issue occurred during generation.');
            appendStdoutStep({
                status: 'error',
                icon: 'alert-triangle',
                title: 'Attention required',
                detail: rawText.replace('[!]', '').trim() || 'An issue occurred during generation.'
            });
            return;
        }

        appendStdoutStep({
            status: 'pending',
            icon: 'activity',
            title: 'System event',
            detail: rawText
        });
    }

    function setNodeActive(key) {
        if (!agentNodes[key]) return;
        agentNodes[key].className = 'node-item active';
        agentNodes[key].querySelector('.node-status').innerText = 'Processing...';
    }

    function setNodeDone(key) {
        if (!agentNodes[key]) return;
        agentNodes[key].className = 'node-item done';
        agentNodes[key].querySelector('.node-status').innerText = 'Complete';
    }

    async function finishPipeline(jobId) {
        const currentActive = logList.querySelector('.active');
        if (currentActive) currentActive.classList.remove('active');

        currentFocusText.innerText = 'Audit Successfully Compiled.';
        agentLiveStatus.classList.add('hidden');
        setStdoutStatus('success', 'Audit complete', 'Deliverables compiled successfully and ready to download.');
        setStdoutProgress(100, 'Deliverables compiled successfully and ready to download.');

        try {
            const statusRes = await fetch(`/api/status/${jobId}`);
            const jobStatus = await statusRes.json();
            const docxLink = document.getElementById('docxLink');
            const xlsxLink = document.getElementById('xlsxLink');
            const pptxLink = document.getElementById('pptxLink');
            const availability = jobStatus.deliverables_available || {};

            bindDeliverable(docxLink, 'docx', availability.docx !== false, jobId);
            bindDeliverable(xlsxLink, 'xlsx', availability.xlsx !== false, jobId);
            bindDeliverable(pptxLink, 'pptx', availability.pptx !== false, jobId);

            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.history && data.history.length > 0) {
                const latest = data.history[0];
                const previewBtn = document.getElementById('livePreviewBtn');
                if (previewBtn) {
                    previewBtn.classList.remove('hidden');
                    previewBtn.onclick = () => window.openLivePreview(latest.archive_id);
                }
            }
        } catch (error) {
            console.error('Failed to fetch latest archive for preview binding', error);
        }

        setTimeout(() => {
            artifactVault.classList.remove('hidden');
            renderIcons();
        }, 300);
    }

    function bindDeliverable(element, fileType, available, jobId) {
        if (!element) return;
        if (available) {
            element.href = `/api/download/${jobId}/${fileType}`;
            element.style.opacity = '1';
            element.style.pointerEvents = 'auto';
            element.removeAttribute('title');
            const labels = {
                docx: ['Strategy_Document.docx', 'Executive document compiled and saved.', 'file-text'],
                xlsx: ['12_Month_Action_Plan.xlsx', 'Action plan spreadsheet generated.', 'grid'],
                pptx: ['Master_Presentation.pptx', 'Presentation deck prepared and saved.', 'monitor']
            };
            const [name, note, icon] = labels[fileType] || [`${fileType.toUpperCase()} Output`, 'Deliverable saved successfully.', 'file'];
            addStdoutFile(name, note, icon);
        } else {
            element.href = '#';
            element.style.opacity = '0.5';
            element.style.pointerEvents = 'none';
            element.title = 'File not generated in this run';
        }
    }

    function handleError(message) {
        centralOrb.style.background = 'radial-gradient(circle, #fff 5%, #ef4444 40%, transparent 70%)';
        centralOrb.style.animation = 'none';
        agentMainState.innerText = 'Critical Failure';
        agentSubState.innerText = message;
        setStdoutStatus('error', 'Critical failure', message);
        appendStdoutStep({
            status: 'error',
            icon: 'alert-octagon',
            title: 'System failure',
            detail: message
        });
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    const existingSession = readSession();
    setTheme(state.theme);
    setMode('audit');
    renderCompetitors();
    renderIcons();
    initPremiumMotion();
    initCommandCenterMotion();
    initAuthVisualMotion();

    if (existingSession) {
        showDashboard();
    } else {
        showAuth();
        setAuthNotice('Guest access is the recommended path right now. Credentials are reserved for future connected authentication.', 'info');
    }
});
