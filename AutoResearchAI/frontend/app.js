/**
 * AutoResearch AI - Frontend Application
 * Deep Thinker Automotive Intelligence Engine
 * Universal Car Search, Report Dossier Generation & Interactive Voice Assistant.
 */

// Application State
const AppState = {
  currentQuery: "",
  activeSection: "home",
  isResearching: false,
  isListening: false,
  isSpeaking: false,
  recognition: null,
  currentReportData: null,
  pipelineTimerInterval: null,
  pipelineStartTime: null
};

// DOM Elements Cache
const DOM = {
  // Navigation
  navLinks: document.querySelectorAll('.nav-link, .mobile-nav-link'),
  sections: document.querySelectorAll('.view-section'),
  mobileToggle: document.getElementById('mobileMenuToggle'),
  mobileDrawer: document.getElementById('mobileDrawer'),
  systemStatusPill: document.getElementById('systemStatusPill'),

  // Search & Hero
  heroSearchForm: document.getElementById('heroSearchForm'),
  mainSearchInput: document.getElementById('mainSearchInput'),
  voiceSearchBtn: document.getElementById('voiceSearchBtn'),
  voiceBanner: document.getElementById('voiceListeningBanner'),
  cancelVoiceBtn: document.getElementById('cancelVoiceBtn'),
  examplePills: document.querySelectorAll('.query-pill'),

  // Research UI
  displayActiveQuery: document.getElementById('displayActiveQuery'),
  resultQueryType: document.getElementById('resultQueryType'),
  pipelineTimer: document.getElementById('pipelineTimer'),
  pipelineTracker: document.getElementById('pipelineTracker'),
  researchLoadingState: document.getElementById('researchLoadingState'),
  loadingStatusMessage: document.getElementById('loadingStatusMessage'),
  researchNoteBanner: document.getElementById('researchNoteBanner'),
  resultsCardsFlow: document.getElementById('resultsCardsFlow'),
  researchEmptyState: document.getElementById('researchEmptyState'),
  generateReportFromQueryBtn: document.getElementById('generateReportFromQueryBtn'),
  speakSummaryBtn: document.getElementById('speakSummaryBtn'),
  speakSummaryCardBtn: document.getElementById('speakSummaryCardBtn'),

  // Cards
  cardSummary: document.getElementById('cardSummary'),
  summaryTextContent: document.getElementById('summaryTextContent'),
  answerMarkdownContent: document.getElementById('answerMarkdownContent'),
  copyAnswerBtn: document.getElementById('copyAnswerBtn'),

  cardDeepThinker: document.getElementById('cardDeepThinker'),
  deepThinkerContent: document.getElementById('deepThinkerContent'),

  cardSpecifications: document.getElementById('cardSpecifications'),
  specsGridContainer: document.getElementById('specsGridContainer'),
  specsCountBadge: document.getElementById('specsCountBadge'),

  cardComparison: document.getElementById('cardComparison'),
  comparisonTableHead: document.getElementById('comparisonTableHead'),
  comparisonTableBody: document.getElementById('comparisonTableBody'),
  conflictAlertPill: document.getElementById('conflictAlertPill'),
  conflictDetailsContainer: document.getElementById('conflictDetailsContainer'),

  cardKeyFindings: document.getElementById('cardKeyFindings'),
  findingsListContainer: document.getElementById('findingsListContainer'),

  cardSources: document.getElementById('cardSources'),
  sourcesGridContainer: document.getElementById('sourcesGridContainer'),
  sourcesCountBadge: document.getElementById('sourcesCountBadge'),

  // Report Generator Section
  reportGenerateForm: document.getElementById('reportGenerateForm'),
  reportVehicleInput: document.getElementById('reportVehicleInput'),
  generateReportBtn: document.getElementById('generateReportBtn'),
  reportLoadingIndicator: document.getElementById('reportLoadingIndicator'),
  dossierReportContainer: document.getElementById('dossierReportContainer'),
  dossierVehicleName: document.getElementById('dossierVehicleName'),
  dossierTagline: document.getElementById('dossierTagline'),
  dossierDate: document.getElementById('dossierDate'),
  dossierOverview: document.getElementById('dossierOverview'),
  dossierSpecsGrid: document.getElementById('dossierSpecsGrid'),
  dossierProsList: document.getElementById('dossierProsList'),
  dossierConsList: document.getElementById('dossierConsList'),
  dossierPowertrain: document.getElementById('dossierPowertrain'),
  dossierSafety: document.getElementById('dossierSafety'),
  dossierOwnership: document.getElementById('dossierOwnership'),
  dossierVerdict: document.getElementById('dossierVerdict'),
  printReportBtn: document.getElementById('printReportBtn'),
  reportPresets: document.querySelectorAll('.report-preset'),

  // Compare Tool
  directCompareForm: document.getElementById('directCompareForm'),
  compCar1: document.getElementById('compCar1'),
  compCar2: document.getElementById('compCar2'),
  compCar3: document.getElementById('compCar3'),
  presetTags: document.querySelectorAll('.preset-tag:not(.report-preset)'),

  // History
  historyListContainer: document.getElementById('historyListContainer'),
  refreshHistoryBtn: document.getElementById('refreshHistoryBtn'),

  // Toast
  toastContainer: document.getElementById('toastContainer')
};

// =====================================================================
// Initialization
// =====================================================================
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initSearch();
  initVoiceAssistant();
  initReportGenerator();
  initCompareTool();
  initHistory();
  checkSystemHealth();
});

// =====================================================================
// System Health Check
// =====================================================================
async function checkSystemHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error('Health check failed');
    const data = await res.json();

    const statusDot = DOM.systemStatusPill.querySelector('.status-indicator');
    const statusLabel = DOM.systemStatusPill.querySelector('.status-label');

    if (data.status === 'healthy') {
      statusDot.style.backgroundColor = 'var(--status-success)';
      const groqText = data.groq_configured ? "Groq Online" : "Groq Ready";
      statusLabel.textContent = `${groqText} • Crawl4AI`;
    } else {
      statusDot.style.backgroundColor = 'var(--status-warning)';
      statusLabel.textContent = 'System degraded';
    }
  } catch (err) {
    console.warn("Backend health check:", err);
  }
}

// =====================================================================
// Navigation & Router
// =====================================================================
function initNavigation() {
  DOM.navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      const targetSection = link.getAttribute('data-section');
      if (targetSection) {
        e.preventDefault();
        switchSection(targetSection);
        if (DOM.mobileDrawer.classList.contains('open')) {
          DOM.mobileDrawer.classList.remove('open');
        }
      }
    });
  });

  if (DOM.mobileToggle) {
    DOM.mobileToggle.addEventListener('click', () => {
      DOM.mobileDrawer.classList.toggle('open');
    });
  }

  // Direct hash navigation
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#', '') || 'home';
    switchSection(hash);
  });
}

function switchSection(sectionId) {
  AppState.activeSection = sectionId;

  // Update Nav Active State
  DOM.navLinks.forEach(link => {
    if (link.getAttribute('data-section') === sectionId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Switch View Section Visibility
  DOM.sections.forEach(sec => {
    if (sec.id === `${sectionId}-section` || (sectionId === 'features' && sec.id === 'home-section')) {
      sec.classList.add('active');
      if (sectionId === 'features') {
        const featEl = document.getElementById('features');
        if (featEl) featEl.scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      sec.classList.remove('active');
    }
  });

  if (sectionId === 'history') {
    loadHistory();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =====================================================================
// Search & Research Pipeline Execution
// =====================================================================
function initSearch() {
  DOM.heroSearchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = DOM.mainSearchInput.value.trim();
    if (!query) {
      showToast('Please enter any car model or automotive question.', 'error');
      DOM.mainSearchInput.focus();
      return;
    }
    executeResearchPipeline(query);
  });

  DOM.examplePills.forEach(pill => {
    pill.addEventListener('click', () => {
      const q = pill.getAttribute('data-query');
      if (q) {
        DOM.mainSearchInput.value = q;
        executeResearchPipeline(q);
      }
    });
  });

  if (DOM.copyAnswerBtn) {
    DOM.copyAnswerBtn.addEventListener('click', () => {
      const text = DOM.summaryTextContent.textContent + "\n\n" + DOM.answerMarkdownContent.innerText;
      navigator.clipboard.writeText(text).then(() => {
        showToast('Answer copied to clipboard!', 'success');
      });
    });
  }

  if (DOM.generateReportFromQueryBtn) {
    DOM.generateReportFromQueryBtn.addEventListener('click', () => {
      const vehicle = AppState.currentQuery.replace(/give specifications of|compare|specs of|price of/gi, '').trim();
      DOM.reportVehicleInput.value = vehicle || "Porsche 911 GT3";
      switchSection('reports');
      generateVehicleReport(DOM.reportVehicleInput.value);
    });
  }
}

async function executeResearchPipeline(query) {
  if (AppState.isResearching) return;
  AppState.isResearching = true;
  AppState.currentQuery = query;

  stopSpeaking();
  switchSection('research');

  DOM.displayActiveQuery.textContent = query;
  DOM.resultQueryType.textContent = "Analyzing Intent...";
  DOM.researchEmptyState.classList.add('hidden');
  DOM.resultsCardsFlow.classList.add('hidden');
  DOM.researchNoteBanner.classList.add('hidden');
  DOM.researchLoadingState.classList.remove('hidden');

  startPipelineTimer();
  updatePipelineStage('understand');

  try {
    setTimeout(() => {
      if (AppState.isResearching) {
        updatePipelineStage('discover');
        DOM.loadingStatusMessage.textContent = "Deep Thinker discovering authoritative vehicle specifications & portals...";
      }
    }, 700);

    setTimeout(() => {
      if (AppState.isResearching) {
        updatePipelineStage('crawl');
        DOM.loadingStatusMessage.textContent = "Crawl4AI extracting clean webpage evidence & manufacturer data...";
      }
    }, 1600);

    setTimeout(() => {
      if (AppState.isResearching) {
        updatePipelineStage('synthesize');
        DOM.loadingStatusMessage.textContent = "Deep Thinker synthesizing mechanical, electrical & thermal engineering data...";
      }
    }, 2500);

    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'AI service temporarily unavailable.');
    }

    const data = await response.json();
    renderResearchResults(data);

  } catch (err) {
    console.error("Research failed:", err);
    showToast(err.message || 'AI service temporarily unavailable.', 'error');
    DOM.loadingStatusMessage.textContent = "AI service temporarily unavailable.";
    DOM.summaryTextContent.textContent = "AI service temporarily unavailable.";
    DOM.answerMarkdownContent.innerHTML = `<p style="color: #F87171;">${escapeHtml(err.message || 'AI service temporarily unavailable.')}</p>`;
    DOM.resultsCardsFlow.classList.remove('hidden');
  } finally {
    stopPipelineTimer();
    DOM.researchLoadingState.classList.add('hidden');
    AppState.isResearching = false;
  }
}

// =====================================================================
// Results Renderer (Deep Thinker, Summary, Specs, Comparison, Findings, Sources)
// =====================================================================
function renderResearchResults(data) {
  DOM.resultQueryType.textContent = data.query_type || "General Automotive";
  if (data.execution_time_seconds) {
    DOM.pipelineTimer.textContent = `${data.execution_time_seconds}s`;
  }

  completePipelineStages();

  if (data.note) {
    DOM.researchNoteBanner.textContent = data.note;
    DOM.researchNoteBanner.classList.remove('hidden');
  } else {
    DOM.researchNoteBanner.classList.add('hidden');
  }

  // 1. Executive Summary
  DOM.summaryTextContent.textContent = data.summary || "No summary available.";
  DOM.answerMarkdownContent.innerHTML = formatMarkdown(data.answer || "");

  // 2. DEEP THINKER CARD
  if (data.deep_thinking_analysis) {
    DOM.deepThinkerContent.innerHTML = formatMarkdown(data.deep_thinking_analysis);
    DOM.cardDeepThinker.classList.remove('hidden');
  } else {
    DOM.cardDeepThinker.classList.add('hidden');
  }

  // 3. Specifications Card
  const specs = data.specifications || [];
  DOM.specsCountBadge.textContent = `${specs.length} Verified`;
  if (specs.length > 0) {
    DOM.specsGridContainer.innerHTML = specs.map(item => `
      <div class="spec-chip">
        <div class="spec-category">${escapeHtml(item.category || 'Specification')}</div>
        <div class="spec-name">${escapeHtml(item.property)}</div>
        <div class="spec-value">${escapeHtml(item.value)} ${item.unit ? `<small style="font-size: 0.8rem; font-weight: normal;">${escapeHtml(item.unit)}</small>` : ''}</div>
        ${item.source ? `<div class="spec-source">Source: ${escapeHtml(item.source)}</div>` : ''}
      </div>
    `).join('');
    DOM.cardSpecifications.classList.remove('hidden');
  } else {
    DOM.cardSpecifications.classList.add('hidden');
  }

  // 4. Comparison Table
  const comparison = data.comparison;
  if (comparison && comparison.rows && comparison.rows.length > 0) {
    const vehicles = comparison.vehicles || [];

    DOM.comparisonTableHead.innerHTML = `
      <tr>
        <th class="feature-col">Feature / Attribute</th>
        ${vehicles.map(v => `<th>${escapeHtml(v)}</th>`).join('')}
      </tr>
    `;

    DOM.comparisonTableBody.innerHTML = comparison.rows.map(row => {
      const rowConflictClass = row.has_conflict ? 'conflict-row' : '';
      const conflictTag = row.has_conflict ? `<span class="conflict-tag">Conflict</span>` : '';
      const valuesHtml = vehicles.map(v => {
        const val = row.values ? row.values[v] : null;
        return `<td>${escapeHtml(val || 'N/A')}</td>`;
      }).join('');

      return `
        <tr class="${rowConflictClass}">
          <td class="feature-col">
            ${escapeHtml(row.feature)}
            ${conflictTag}
          </td>
          ${valuesHtml}
        </tr>
      `;
    }).join('');

    if (comparison.conflicts_detected) {
      DOM.conflictAlertPill.classList.remove('hidden');
      const conflictNotes = comparison.rows
        .filter(r => r.has_conflict && r.conflict_notes)
        .map(r => `<strong>${escapeHtml(r.feature)}:</strong> ${escapeHtml(r.conflict_notes)}`)
        .join('<br>');

      if (conflictNotes) {
        DOM.conflictDetailsContainer.innerHTML = `<div>⚠️ <strong>Conflicting Information Identified:</strong><br>${conflictNotes}</div>`;
        DOM.conflictDetailsContainer.classList.remove('hidden');
      } else {
        DOM.conflictDetailsContainer.classList.add('hidden');
      }
    } else {
      DOM.conflictAlertPill.classList.add('hidden');
      DOM.conflictDetailsContainer.classList.add('hidden');
    }

    DOM.cardComparison.classList.remove('hidden');
  } else {
    DOM.cardComparison.classList.add('hidden');
  }

  // 5. Key Findings
  const findings = data.key_findings || [];
  if (findings.length > 0) {
    DOM.findingsListContainer.innerHTML = findings.map(f => `
      <li class="finding-item">
        <span class="finding-bullet">▪</span>
        <span>${escapeHtml(f)}</span>
      </li>
    `).join('');
    DOM.cardKeyFindings.classList.remove('hidden');
  } else {
    DOM.cardKeyFindings.classList.add('hidden');
  }

  // 6. Sources
  const sources = data.sources || [];
  DOM.sourcesCountBadge.textContent = `${sources.length} Sources`;
  if (sources.length > 0) {
    DOM.sourcesGridContainer.innerHTML = sources.map(src => {
      const isOfficial = src.is_official || src.relevance === 'Official';
      return `
        <div class="source-item-card">
          <div>
            <div class="source-top">
              <span class="source-domain">${escapeHtml(src.domain || 'Source')}</span>
              <span class="source-relevance-tag ${isOfficial ? 'official' : ''}">
                ${isOfficial ? '🛡️ Official OEM / Authority' : escapeHtml(src.relevance || 'Verified')}
              </span>
            </div>
            <a href="${escapeHtml(src.url)}" target="_blank" rel="noopener noreferrer" class="source-title-link">
              ${escapeHtml(src.title || src.domain)} ↗
            </a>
          </div>
          ${src.evidence ? `
            <div class="source-evidence">
              "${escapeHtml(src.evidence)}"
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
    DOM.cardSources.classList.remove('hidden');
  } else {
    DOM.cardSources.classList.add('hidden');
  }

  DOM.resultsCardsFlow.classList.remove('hidden');
}

// =====================================================================
// Vehicle Research Dossier / Report Generator
// =====================================================================
function initReportGenerator() {
  if (!DOM.reportGenerateForm) return;

  DOM.reportGenerateForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const vehicle = DOM.reportVehicleInput.value.trim();
    if (!vehicle) {
      showToast('Please enter a vehicle model for the report.', 'error');
      return;
    }
    generateVehicleReport(vehicle);
  });

  DOM.reportPresets.forEach(btn => {
    btn.addEventListener('click', () => {
      const car = btn.getAttribute('data-car');
      if (car) {
        DOM.reportVehicleInput.value = car;
        generateVehicleReport(car);
      }
    });
  });

  if (DOM.printReportBtn) {
    DOM.printReportBtn.addEventListener('click', () => {
      window.print();
    });
  }
}

async function generateVehicleReport(vehicleName) {
  DOM.reportLoadingIndicator.classList.remove('hidden');
  DOM.dossierReportContainer.classList.add('hidden');

  try {
    const res = await fetch('/api/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vehicle_name: vehicleName })
    });

    if (!res.ok) {
      throw new Error('Failed to generate vehicle dossier report.');
    }

    const data = await res.json();
    AppState.currentReportData = data;

    // Populate Dossier Elements
    DOM.dossierVehicleName.textContent = data.vehicle_name;
    DOM.dossierTagline.textContent = data.tagline;
    DOM.dossierDate.textContent = `Generated: ${data.generated_at}`;
    DOM.dossierOverview.textContent = data.overview;

    // Specs
    DOM.dossierSpecsGrid.innerHTML = (data.specifications || []).map(s => `
      <div class="spec-chip">
        <div class="spec-category">${escapeHtml(s.category)}</div>
        <div class="spec-name">${escapeHtml(s.property)}</div>
        <div class="spec-value">${escapeHtml(s.value)} ${s.unit ? `<small>${escapeHtml(s.unit)}</small>` : ''}</div>
      </div>
    `).join('');

    // Pros & Cons
    DOM.dossierProsList.innerHTML = (data.pros || []).map(p => `<li>${escapeHtml(p)}</li>`).join('');
    DOM.dossierConsList.innerHTML = (data.cons || []).map(c => `<li>${escapeHtml(c)}</li>`).join('');

    // Deep Analysis Sections
    DOM.dossierPowertrain.textContent = data.powertrain_analysis;
    DOM.dossierSafety.textContent = data.safety_and_chassis;
    DOM.dossierOwnership.textContent = data.ownership_and_maintenance;
    DOM.dossierVerdict.textContent = data.deep_engineering_verdict;

    DOM.dossierReportContainer.classList.remove('hidden');
    DOM.dossierReportContainer.scrollIntoView({ behavior: 'smooth' });
    showToast(`Dossier Report ready for ${data.vehicle_name}!`, 'success');

  } catch (err) {
    console.error("Report generation failed:", err);
    showToast(err.message, 'error');
  } finally {
    DOM.reportLoadingIndicator.classList.add('hidden');
  }
}

// =====================================================================
// Interactive Voice Assistant (Speech Recognition + TTS)
// =====================================================================
function initVoiceAssistant() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    AppState.recognition = new SpeechRecognition();
    AppState.recognition.continuous = false;
    AppState.recognition.interimResults = false;
    AppState.recognition.lang = 'en-US';

    DOM.voiceSearchBtn.addEventListener('click', () => {
      if (AppState.isListening) {
        stopListening();
      } else {
        startListening();
      }
    });

    DOM.cancelVoiceBtn.addEventListener('click', stopListening);

    AppState.recognition.onstart = () => {
      AppState.isListening = true;
      DOM.voiceSearchBtn.classList.add('listening');
      DOM.voiceBanner.classList.remove('hidden');
      stopSpeaking();
    };

    AppState.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      DOM.mainSearchInput.value = transcript;
      stopListening();
      showToast(`Voice captured: "${transcript}"`, 'info');
      executeResearchPipeline(transcript);
    };

    AppState.recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopListening();
      if (event.error === 'not-allowed') {
        showToast('Microphone access was denied. Please allow microphone permission in your browser.', 'error');
      } else {
        showToast(`Voice error: ${event.error}`, 'error');
      }
    };

    AppState.recognition.onend = () => {
      stopListening();
    };
  } else {
    DOM.voiceSearchBtn.title = "Voice recognition is not supported in this browser. Please use Chrome, Edge, or Safari.";
  }

  // Text-To-Speech (TTS) Voice Speaker
  const speakHandler = () => {
    const textToSpeak = DOM.summaryTextContent.textContent;
    if (!textToSpeak) return;

    if (AppState.isSpeaking) {
      stopSpeaking();
    } else {
      speakText(textToSpeak);
    }
  };

  if (DOM.speakSummaryBtn) DOM.speakSummaryBtn.addEventListener('click', speakHandler);
  if (DOM.speakSummaryCardBtn) DOM.speakSummaryCardBtn.addEventListener('click', speakHandler);
}

function startListening() {
  if (AppState.recognition && !AppState.isListening) {
    try {
      AppState.recognition.start();
    } catch (e) {
      console.warn("Recognition start error:", e);
    }
  }
}

function stopListening() {
  AppState.isListening = false;
  DOM.voiceSearchBtn.classList.remove('listening');
  DOM.voiceBanner.classList.add('hidden');
  if (AppState.recognition) {
    try {
      AppState.recognition.stop();
    } catch (e) {}
  }
}

function speakText(text) {
  if (!('speechSynthesis' in window)) {
    showToast('Text-to-speech is not supported on this device.', 'error');
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    AppState.isSpeaking = true;
    if (DOM.speakSummaryBtn) DOM.speakSummaryBtn.textContent = '⏹️ Stop Speaking';
    if (DOM.speakSummaryCardBtn) DOM.speakSummaryCardBtn.textContent = '⏹️ Stop';
  };

  utterance.onend = () => {
    stopSpeaking();
  };

  utterance.onerror = () => {
    stopSpeaking();
  };

  window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
  AppState.isSpeaking = false;
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  if (DOM.speakSummaryBtn) DOM.speakSummaryBtn.textContent = '🔊 Speak Answer';
  if (DOM.speakSummaryCardBtn) DOM.speakSummaryCardBtn.textContent = '🔊 Speak';
}

// =====================================================================
// Compare Tool
// =====================================================================
function initCompareTool() {
  if (!DOM.directCompareForm) return;

  DOM.directCompareForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const c1 = DOM.compCar1.value.trim();
    const c2 = DOM.compCar2.value.trim();
    const c3 = DOM.compCar3.value.trim();

    if (!c1 || !c2) {
      showToast('Please enter at least two vehicles to compare.', 'error');
      return;
    }

    const vehicles = [c1, c2];
    if (c3) vehicles.push(c3);

    const compQuery = `Compare ${vehicles.join(' and ')}`;
    DOM.mainSearchInput.value = compQuery;
    executeResearchPipeline(compQuery);
  });

  DOM.presetTags.forEach(tag => {
    tag.addEventListener('click', () => {
      const c1 = tag.getAttribute('data-c1');
      const c2 = tag.getAttribute('data-c2');
      if (c1 && c2) {
        DOM.compCar1.value = c1;
        DOM.compCar2.value = c2;
        DOM.compCar3.value = '';
        const compQuery = `Compare ${c1} and ${c2}`;
        DOM.mainSearchInput.value = compQuery;
        executeResearchPipeline(compQuery);
      }
    });
  });
}

// =====================================================================
// Research History Loader
// =====================================================================
function initHistory() {
  if (DOM.refreshHistoryBtn) {
    DOM.refreshHistoryBtn.addEventListener('click', loadHistory);
  }
}

async function loadHistory() {
  DOM.historyListContainer.innerHTML = '<div class="loading-spinner-sm">Fetching history...</div>';
  try {
    const res = await fetch('/api/history?limit=25');
    const data = await res.json();

    if (!data.success || !data.history || data.history.length === 0) {
      DOM.historyListContainer.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 2rem;">
          No research sessions recorded yet. Run your first vehicle query above!
        </div>
      `;
      return;
    }

    DOM.historyListContainer.innerHTML = data.history.map(item => `
      <div class="history-card-item">
        <div class="history-main-info">
          <div class="history-query-text">${escapeHtml(item.query)}</div>
          <div class="history-summary-text">${escapeHtml(item.summary)}</div>
          <div class="history-meta-row">
            <span>🏷️ ${escapeHtml(item.query_type)}</span>
            <span>⏱️ ${new Date(item.created_at).toLocaleString()}</span>
          </div>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="rerunHistoricalQuery('${escapeHtml(item.query)}')">
          Re-Analyze
        </button>
      </div>
    `).join('');

  } catch (err) {
    console.error("Failed to load history:", err);
    DOM.historyListContainer.innerHTML = `<div style="color: #F87171;">Failed to load history from database.</div>`;
  }
}

window.rerunHistoricalQuery = function(query) {
  DOM.mainSearchInput.value = query;
  executeResearchPipeline(query);
};

// =====================================================================
// Pipeline Animation & Timer
// =====================================================================
function startPipelineTimer() {
  AppState.pipelineStartTime = Date.now();
  DOM.pipelineTimer.textContent = "0.0s";
  if (AppState.pipelineTimerInterval) clearInterval(AppState.pipelineTimerInterval);
  AppState.pipelineTimerInterval = setInterval(() => {
    const elapsed = ((Date.now() - AppState.pipelineStartTime) / 1000).toFixed(1);
    DOM.pipelineTimer.textContent = `${elapsed}s`;
  }, 100);
}

function stopPipelineTimer() {
  if (AppState.pipelineTimerInterval) {
    clearInterval(AppState.pipelineTimerInterval);
    AppState.pipelineTimerInterval = null;
  }
}

function updatePipelineStage(stage) {
  const steps = ['understand', 'discover', 'crawl', 'synthesize'];
  const curIdx = steps.indexOf(stage);

  steps.forEach((s, idx) => {
    const el = document.getElementById(`step-${s}`);
    if (!el) return;
    el.classList.remove('active', 'completed');
    if (idx < curIdx) {
      el.classList.add('completed');
    } else if (idx === curIdx) {
      el.classList.add('active');
    }
  });
}

function completePipelineStages() {
  const steps = ['understand', 'discover', 'crawl', 'synthesize'];
  steps.forEach(s => {
    const el = document.getElementById(`step-${s}`);
    if (el) {
      el.classList.remove('active');
      el.classList.add('completed');
    }
  });
}

// =====================================================================
// Toast Utilities
// =====================================================================

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✓' : (type === 'error' ? '⚠️' : 'ℹ️');
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  DOM.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);
  html = html.replace(/^### (.*$)/gim, '<h4>$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gms, '<ul>$1</ul>');
  html = html.replace(/\n\n/g, '</p><p>');
  return `<p>${html}</p>`;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
