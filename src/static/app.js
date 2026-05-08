/* global React, ReactDOM */

const { useCallback, useEffect, useMemo, useRef, useState } = React;

const STORAGE_KEYS = {
  theme: 'radius-theme',
  session: 'radius-auth-session',
};

const ROUTE_LABELS = {
  dashboard: 'Overview',
  new: 'New Audit',
  live: 'Live Audit',
  archives: 'Archives',
  competitors: 'Competitors',
  keywords: 'Keyword Bank',
  engines: 'AI Engines',
  agents: 'Agents',
  rag: 'RAG Index',
  runlogs: 'Run Logs',
  settings: 'Settings',
};

const PIPELINE_NODES = [
  { key: 'extraction', label: 'Content Extraction', desc: 'Vision-CRO crawl + content parse', icon: 'db', phase: 'Phase 1', est: 18 },
  { key: 'market_intel', label: 'Market Intelligence', desc: 'SEMrush keywords + market signals', icon: 'bar', phase: 'Phase 2', est: 42 },
  { key: 'competitor_shadow', label: 'Competitor Shadowing', desc: 'Competitor set + comparative shadowing', icon: 'users', phase: 'Phase 2.5', est: 28 },
  { key: 'technical_audit', label: 'Technical Audit', desc: 'robots, schema, indexability, CRO checks', icon: 'shield', phase: 'Phase 3', est: 22 },
  { key: 'deep_rag', label: 'RAG Vector Index', desc: 'Recursive FAISS + embeddings', icon: 'layers', phase: 'Phase 4', est: 16 },
  { key: 'strategy_synthesis', label: 'Strategy Synthesis', desc: 'GPT-generated narrative + recommendations', icon: 'edit', phase: 'Phase 5', est: 38 },
  { key: 'deliverables', label: 'Deliverables Build', desc: 'DOCX · XLSX · PPTX generation', icon: 'package', phase: 'Phase 6', est: 24 },
];

const NODE_KEYS = PIPELINE_NODES.map((node) => node.key);

const Icon = ({ name, size = 14, ...rest }) => {
  const s = size;
  const props = {
    width: s,
    height: s,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.75,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    ...rest,
  };

  const map = {
    home: <path d="M3 12 12 4l9 8M5 10v10h14V10" />,
    plus: <><path d="M12 5v14" /><path d="M5 12h14" /></>,
    activity: <path d="M22 12h-4l-3 9-6-18-3 9H2" />,
    archive: <><rect x="2" y="4" width="20" height="5" rx="1" /><path d="M4 9v10a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9" /><path d="M10 13h4" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></>,
    globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></>,
    user: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
    users: <><circle cx="9" cy="8" r="4" /><path d="M2 21a7 7 0 0 1 14 0" /><path d="M16 4a4 4 0 0 1 0 8" /><path d="M22 21a7 7 0 0 0-5-6.7" /></>,
    target: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.5" /></>,
    cpu: <><rect x="5" y="5" width="14" height="14" rx="1.5" /><rect x="9" y="9" width="6" height="6" /><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3" /></>,
    bar: <><line x1="4" y1="20" x2="4" y2="10" /><line x1="10" y1="20" x2="10" y2="4" /><line x1="16" y1="20" x2="16" y2="14" /><line x1="22" y1="20" x2="2" y2="20" /></>,
    layers: <><polygon points="12 2 2 7 12 12 22 7 12 2" /><polyline points="2 17 12 22 22 17" /><polyline points="2 12 12 17 22 12" /></>,
    package: <><path d="m7.5 4.5 9 5" /><path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.3 7 12 12 20.7 7" /><line x1="12" y1="22" x2="12" y2="12" /></>,
    edit: <><path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z" /></>,
    db: <><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" /></>,
    arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
    arrowDown: <><path d="M12 5v14" /><path d="m6 13 6 6 6-6" /></>,
    arrowUp: <><path d="M12 19V5" /><path d="m6 11 6-6 6 6" /></>,
    check: <path d="M5 12l5 5L20 7" />,
    checkCircle: <><circle cx="12" cy="12" r="9" /><path d="m9 12 2 2 4-4" /></>,
    x: <><path d="M18 6 6 18" /><path d="m6 6 12 12" /></>,
    close: <><path d="M18 6 6 18" /><path d="m6 6 12 12" /></>,
      info: <><circle cx="12" cy="12" r="9" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="8" /></>,
      bell: <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 0 0 4 0" /></>,
      alert: <><path d="M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12" y2="17" /></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></>,
    file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></>,
    fileText: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="8" y1="13" x2="16" y2="13" /><line x1="8" y1="17" x2="13" y2="17" /></>,
    grid: <><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></>,
    monitor: <><rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></>,
    moon: <path d="M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10z" />,
    terminal: <><polyline points="4 17 10 11 4 5" /><line x1="12" y1="19" x2="20" y2="19" /></>,
    folder: <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />,
    play: <polygon points="6 4 20 12 6 20 6 4" />,
    pause: <><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></>,
    stop: <rect x="6" y="6" width="12" height="12" rx="1" />,
    refresh: <><polyline points="21 3 21 9 15 9" /><path d="M3 12a9 9 0 0 1 15-6.7L21 9" /><polyline points="3 21 3 15 9 15" /><path d="M21 12a9 9 0 0 1-15 6.7L3 15" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" /></>,
    zap: <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />,
    sparkles: <><path d="M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4z" /><path d="M19 16l.9 2.1L22 19l-2.1.9L19 22l-.9-2.1L16 19l2.1-.9z" /></>,
    chevDown: <polyline points="6 9 12 15 18 9" />,
    chevRight: <polyline points="9 6 15 12 9 18" />,
    eye: <><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" /><circle cx="12" cy="12" r="3" /></>,
    code: <><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></>,
    radar: <><circle cx="12" cy="12" r="9" /><path d="M12 12L17 7" /><path d="M3.6 8a9 9 0 0 1 16.8 0" /><circle cx="12" cy="12" r="1.5" fill="currentColor" /></>,
    bell: <><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" /></>,
    moreH: <><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /><circle cx="5" cy="12" r="1" /></>,
    filter: <polygon points="22 3 2 3 10 12.5 10 19 14 21 14 12.5 22 3" />,
    book: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></>,
    link: <><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></>,
    shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
    flag: <><path d="M4 21V4l9 4h7l-3 5 3 5h-7l-9-4" /></>,
    history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 4v4h4" /><path d="M12 7v5l3 2" /></>,
  };

  return <svg {...props}>{map[name] || map.info}</svg>;
};

const StatusBadge = ({ status }) => {
  const map = {
    running: { cls: 'badge-accent', text: 'Running' },
    starting: { cls: 'badge-accent', text: 'Starting' },
    queued: { cls: '', text: 'Queued' },
    completed: { cls: 'badge-success', text: 'Done' },
    done: { cls: 'badge-success', text: 'Done' },
    failed: { cls: 'badge-danger', text: 'Failed' },
  };
  const picked = map[status] || map.queued;
  return (
    <span className={`badge ${picked.cls}`}>
      {(status === 'running' || status === 'starting') && <span className="dot" style={{ animation: 'pulse-dot 1.5s ease-in-out infinite' }} />}
      {picked.text}
    </span>
  );
};

const escapeHtml = (value) => {
  const div = document.createElement('div');
  div.textContent = value ?? '';
  return div.innerHTML;
};

const fetchJson = async (url, options) => {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
};

const formatArchiveDate = (historyItem) => {
  if (!historyItem) return '—';
  if (historyItem.date) return historyItem.date;
  if (historyItem.timestamp && /^\d{8}_\d{6}$/.test(historyItem.timestamp)) {
    const raw = historyItem.timestamp;
    return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)} ${raw.slice(9, 11)}:${raw.slice(11, 13)}`;
  }
  return historyItem.timestamp || '—';
};

const normalizeDomain = (value) => value.replace(/^https?:\/\//i, '').replace(/\/.*$/, '').trim();

const collectDeliverables = (statusData, jobId) => {
  const deliverables = [];
  const availability = statusData?.deliverables_available || {};
  const typeMap = [
    { type: 'docx', label: 'Strategy_Document.docx', icon: 'fileText' },
    { type: 'xlsx', label: '12_Month_Action_Plan.xlsx', icon: 'grid' },
    { type: 'pptx', label: 'Master_Presentation.pptx', icon: 'monitor' },
  ];
  typeMap.forEach((entry) => {
    if (availability[entry.type] !== false) {
      deliverables.push({
        ...entry,
        href: `/api/download/${jobId}/${entry.type}`,
      });
    }
  });
  return deliverables;
};

const OverviewSpark = ({ variant = 'default' }) => {
  const seriesMap = {
    rise: [18, 28, 22, 44, 31, 56, 42, 71],
    steady: [20, 26, 40, 33, 52, 36, 58, 76],
    shipped: [16, 27, 39, 32, 54, 35, 56, 82],
    default: [18, 24, 30, 38, 46, 52, 60, 74],
  };
  const bars = seriesMap[variant] || seriesMap.default;
  return (
    <div className={`overview-spark overview-spark-${variant}`}>
      {bars.map((height, index) => (
        <span key={`${variant}-${index}`} style={{ height: `${height}%` }} />
      ))}
    </div>
  );
};

const OverviewMetricCard = ({
  icon,
  label,
  value,
  unit,
  trendText,
  trendState,
  metaText,
  secondaryMeta,
  metaBadges,
  sparkVariant = 'default',
  showMeter = false,
  meterWidth = 0,
}) => (
  <div className="kpi overview-kpi-card">
    <div className="overview-kpi-shell">
      <div className="overview-kpi-top">
        <div className="overview-kpi-icon-badge">
          <Icon name={icon} size={24} />
        </div>
        <div className="overview-kpi-heading">
          <div className="kpi-label">{label}</div>
          <div className="kpi-value">
            {value}
            {unit ? <span className="unit">{unit}</span> : null}
          </div>
        </div>
      </div>
      <div className="kpi-meta overview-kpi-meta">
        {trendText ? <span className={`kpi-trend ${trendState}`}>{trendText}</span> : null}
        {Array.isArray(metaBadges)
          ? metaBadges.map((badge) => (
              <span key={badge} className="kpi-trend up overview-kpi-chip">
                {badge}
              </span>
            ))
          : null}
        {metaText ? <span>{metaText}</span> : null}
        {secondaryMeta ? <span>{secondaryMeta}</span> : null}
      </div>
      {showMeter ? (
        <div className="overview-kpi-meter-row">
          <div className="kpi-meter overview-kpi-meter">
            <span style={{ width: `${meterWidth}%` }} />
          </div>
        </div>
      ) : null}
      <div className="overview-kpi-graph" aria-hidden="true">
        <OverviewSpark variant={sparkVariant} />
      </div>
    </div>
  </div>
);

const archiveDownloadHref = (item, type) => `/api/download/${item.archive_id || item.timestamp}/${type}`;

const defaultNodeState = () =>
  PIPELINE_NODES.reduce((acc, node) => {
    acc[node.key] = { status: 'queued', detail: 'Awaiting...' };
    return acc;
  }, {});

const advanceNodeState = (states, key, nextStatus, detail) => {
  const next = { ...states };
  if (nextStatus === 'active') {
    NODE_KEYS.forEach((nodeKey) => {
      if (next[nodeKey].status === 'active') {
        next[nodeKey] = { ...next[nodeKey], status: 'queued', detail: 'Queued' };
      }
    });
  }
  if (next[key]) {
    next[key] = {
      status: nextStatus,
      detail: detail || (nextStatus === 'done' ? 'Completed' : nextStatus === 'failed' ? 'Failed' : 'In progress'),
    };
  }
  return next;
};

const inferNodeKey = (rawText) => {
  const text = rawText.toLowerCase();
  if (text.includes('phase 1')) return 'extraction';
  if (text.includes('phase 2.5')) return 'competitor_shadow';
  if (text.includes('phase 2') && text.includes('market intelligence')) return 'market_intel';
  if (text.includes('phase 3') || text.includes('technical audit')) return 'technical_audit';
  if (text.includes('phase 4') || text.includes('faiss')) return 'deep_rag';
  if (text.includes('phase 5') || text.includes('strategy synthesis')) return 'strategy_synthesis';
  if (text.includes('phase 6') || text.includes('deliverables')) return 'deliverables';
  return null;
};

const detectNodeUpdate = (rawText) => {
  const startedNode = rawText.match(/--- \[Node\] (?:Phase [^:]+: )?(.*) ---/);
  if (startedNode) {
    const nodeKey = inferNodeKey(rawText);
    if (nodeKey) return { type: 'active', key: nodeKey, detail: startedNode[1].trim() };
  }

  const completedNode = rawText.match(/\[\+\]\s+([a-z_]+)\s+completed successfully/i);
  if (completedNode) {
    return { type: 'done', key: completedNode[1].toLowerCase(), detail: 'Completed' };
  }

  const failedNode = rawText.match(/\[!\]\s+Error in ([a-z_]+):\s*(.*)/i);
  if (failedNode) {
    return { type: 'failed', key: failedNode[1].toLowerCase(), detail: failedNode[2]?.trim() || 'Failed' };
  }

  if (rawText.includes('Phase 4: Constructing Recursive FAISS')) {
    return { type: 'active', key: 'deep_rag', detail: 'Building recursive vector index' };
  }
  if (rawText.includes('Phase 5: GPT-4o AEO Strategy Synthesis')) {
    return { type: 'active', key: 'strategy_synthesis', detail: 'Synthesizing integrated recommendations' };
  }
  if (rawText.includes('Phase 6: Injecting Dynamic Architecture')) {
    return { type: 'active', key: 'deliverables', detail: 'Compiling DOCX, XLSX, and PPTX deliverables' };
  }

  return null;
};

const detectProgressUpdate = (rawText) => {
  const match = rawText.match(/\[PROGRESS\]\s+(\d+)%\s*\|\s*(.*)$/i);
  if (!match) return null;
  return {
    percent: Number(match[1] || 0),
    detail: (match[2] || '').trim(),
  };
};

const ThemeToggle = ({ theme, setTheme, compact = false }) => (
  <div className={`login-theme-toggle ${compact ? 'compact' : ''}`}>
    <button className={theme === 'dark' ? 'active' : ''} onClick={() => setTheme('dark')} type="button">
      <Icon name="moon" size={13} /> Dark
    </button>
    <button className={theme === 'light' ? 'active' : ''} onClick={() => setTheme('light')} type="button">
      <Icon name="sun" size={13} /> Light
    </button>
  </div>
);

const Login = ({ onSignIn, theme, setTheme }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [shake, setShake] = useState(false);

  const submit = (event) => {
    event.preventDefault();
    if (!email || !password) {
      setShake(true);
      window.setTimeout(() => setShake(false), 400);
      return;
    }
    onSignIn({ email, name: email.split('@')[0] || 'Operator', guest: false });
  };

  return (
    <div className={`login-shell ${theme}`}>
      <div className="login-bg-grid" />
      <div className="login-bg-glow login-bg-glow-1" />
      <div className="login-bg-glow login-bg-glow-2" />

      <header className="login-topbar">
        <div className="login-brand">
          <img
            src={theme === 'dark' ? '/static/logo-white.png' : '/static/logo.png'}
            alt="Traffic Radius"
            className="login-brand-logo"
          />
          <div className="login-brand-sep" />
          <div className="login-brand-meta">
            <span className="kicker">TRAFFIC RADIUS</span>
            <span className="title">Radius AI Control Center</span>
          </div>
        </div>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </header>

      <main className="login-main">
        <div className="login-grid">
          <section className="login-card login-visual">
            <span className="login-eyebrow">INTELLIGENT ACCESS LAYER</span>
            <div className="login-orb-wrap">
              <div className="login-orb-rings">
                <span className="ring r4" />
                <span className="ring r3" />
                <span className="ring r2" />
                <span className="ring r1" />
              </div>
              {[0, 50, 110, 170, 220, 290, 340].map((deg, index) => {
                const rad = (deg * Math.PI) / 180;
                const r = 110 + (index % 2 ? 28 : -8);
                const x = Math.cos(rad) * r;
                const y = Math.sin(rad) * r;
                return (
                  <span
                    key={index}
                    className="login-orb-node"
                    style={{
                      transform: `translate(${x}px, ${y}px)`,
                      animationDelay: `${index * 0.4}s`,
                    }}
                  />
                );
              })}
              <div className="login-orb-core" />
              <div className="login-orb-pulse" />
              <div className="login-orb-sweep" />
            </div>
            <h3 className="login-visual-caption">Sign in to launch premium AI audit workflows.</h3>
          </section>

          <section className={`login-card login-form ${shake ? 'shake' : ''}`}>
            <div className="login-form-pill">
              <Icon name="shield" size={12} />
              <span>SECURE SIGN IN</span>
            </div>
            <h1 className="login-title">Access Audit Engine</h1>

            <form onSubmit={submit} className="login-form-fields">
              <div className="field">
                <label>Email address</label>
                <div className="input-group">
                  <Icon name="globe" size={14} />
                  <input
                    className="input"
                    type="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="field">
                <label>Password</label>
                <div className="input-group">
                  <Icon name="shield" size={14} />
                  <input
                    className="input"
                    type="password"
                    placeholder="Enter password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                  />
                </div>
              </div>

              <button type="submit" className="login-primary">
                <span>Sign In</span>
                <Icon name="arrow" size={14} />
              </button>

              <button
                type="button"
                className="login-secondary"
                onClick={() => onSignIn({ email: 'guest@trafficradius.com.au', name: 'Guest', guest: true })}
              >
                <Icon name="user" size={14} />
                Continue as Guest
              </button>
            </form>

            <div className="login-form-foot">
              <div className="dots">
                <span />
                <span />
                <span />
              </div>
              <span>SOC 2 · Encrypted orchestration · Executive-ready outputs</span>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

const NAV = [
  {
    section: 'WORKSPACE',
    items: [
      { key: 'dashboard', label: 'Dashboard', icon: 'home' },
      { key: 'new', label: 'New Audit', icon: 'plus' },
      { key: 'live', label: 'Live Audit', icon: 'activity' },
      { key: 'archives', label: 'Archives', icon: 'archive' },
    ],
  },
  {
    section: 'INTELLIGENCE',
    items: [
      { key: 'competitors', label: 'Competitors', icon: 'users' },
      { key: 'keywords', label: 'Keyword Bank', icon: 'target' },
      { key: 'engines', label: 'AI Engines', icon: 'cpu' },
    ],
  },
  {
    section: 'SYSTEM',
    items: [
      { key: 'agents', label: 'Agents', icon: 'layers' },
      { key: 'rag', label: 'RAG Index', icon: 'db' },
      { key: 'runlogs', label: 'Run Logs', icon: 'terminal' },
      { key: 'settings', label: 'Settings', icon: 'settings' },
    ],
  },
];

const Sidebar = ({ route, setRoute, theme, user, currentRun, onOpenSearch }) => (
  <aside className="sidebar">
    <div className="sidebar-brand">
      <img src={theme === 'dark' ? '/static/logo-white.png' : '/static/logo.png'} alt="Traffic Radius" className="sidebar-brand-logo" />
      <span className="sidebar-brand-version">v3.0</span>
    </div>

    <button className="sidebar-search" type="button" onClick={onOpenSearch} aria-label="Search audits and archives">
      <Icon name="search" size={13} />
      <span>Search audits, archives...</span>
      <kbd>Ctrl K</kbd>
    </button>

    <nav className="sidebar-nav">
      {NAV.map((group) => (
        <React.Fragment key={group.section}>
          <div className="sidebar-section">{group.section}</div>
          {group.items.map((item) => (
            <div
              key={item.key}
              className={`sidebar-item ${route === item.key ? 'active' : ''}`}
              onClick={() => setRoute(item.key)}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.key === 'live' && currentRun?.status === 'running' ? <span className="sidebar-badge">LIVE</span> : null}
            </div>
          ))}
        </React.Fragment>
      ))}
    </nav>

    <div className="sidebar-footer">
      <div className="sidebar-user">
        <div className="sidebar-user-avatar">{(user?.name || 'G').slice(0, 2).toUpperCase()}</div>
        <div className="sidebar-user-info">
          <strong>{user?.name || 'Guest'}</strong>
          <span>{user?.guest ? 'Guest access' : user?.email || 'Operator'}</span>
        </div>
        <Icon name="chevDown" size={12} />
      </div>
    </div>
  </aside>
);

const Topbar = ({ route, theme, setTheme, setRoute, currentRun, signOut }) => (
  <header className="topbar">
    <div className="crumbs">
      <span>TrafficRadius</span>
      <span className="sep">/</span>
      <span>Radius AI Control Center</span>
      <span className="sep">/</span>
      <strong>{ROUTE_LABELS[route] || route}</strong>
    </div>
    <div className="topbar-actions">
      <div className="topbar-status">
        <span className="dot" />
        {currentRun?.status === 'running' ? 'Audit running' : 'Core online'}
      </div>
      <ThemeToggle theme={theme} setTheme={setTheme} compact />
      <button className="btn btn-sm" type="button" onClick={() => setRoute('archives')}>
        <Icon name="archive" size={13} />
        Archives
      </button>
      <button className="btn btn-ghost btn-sm" type="button" onClick={signOut}>
        <Icon name="user" size={13} />
        Sign out
      </button>
    </div>
  </header>
);

const Dashboard = ({ history, currentRun, setRoute }) => {
  const [semrushState, setSemrushState] = useState({
    loading: true,
    available: false,
    formatted_remaining_units: null,
    label: '',
    message: 'Checking live balance',
  });
  const completed = history.filter((item) => item.status === 'completed').length;
  const failed = history.filter((item) => item.status === 'failed').length;
  const total = history.length;
  const recent = history.slice(0, 6);
  const successRate = total ? Math.round((completed / total) * 100) : 0;
  const activeCompany = currentRun?.company || recent[0]?.company || 'No active run';
  const activeDomain = currentRun?.domain || recent[0]?.domain || 'Awaiting new audit';
  const activeJob = currentRun?.jobId ? currentRun.jobId.slice(0, 8) : recent[0]?.archive_id?.slice(0, 8) || 'standby';
  const avgRunTime = recent.length ? '3:42' : '0:00';
  const shipped = completed * 3;
  const streamLabel = currentRun?.status === 'running' ? 'AGENT STREAM' : 'LAST RUN';
  const streamCopy = currentRun?.status === 'running'
    ? `${activeCompany} analyzed ${activeDomain}`
    : recent[0]
      ? `${recent[0].company || 'Recent audit'} completed ${formatArchiveDate(recent[0])}`
      : 'Awaiting first audit launch';

  useEffect(() => {
    let isMounted = true;

    fetchJson('/api/semrush-units')
      .then((data) => {
        if (!isMounted) return;
        setSemrushState({
          loading: false,
          available: !!data?.available,
          formatted_remaining_units: data?.formatted_remaining_units || null,
          label: data?.label || '',
          message: data?.message || 'SEMrush unavailable',
        });
      })
      .catch(() => {
        if (!isMounted) return;
        setSemrushState({
          loading: false,
          available: false,
          formatted_remaining_units: null,
          label: '',
          message: 'SEMrush unavailable',
        });
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const semrushValue = semrushState.loading
    ? '...'
    : semrushState.available
      ? semrushState.formatted_remaining_units
      : 'N/A';
  const semrushUnit = semrushState.available ? semrushState.label : '';
  const semrushMeta = semrushState.loading
    ? 'Checking live balance'
    : semrushState.message;
  const semrushSecondary = semrushState.available ? 'via SEMRUSH_API_KEY' : '';
  const hasUsageData = (usage) => !!usage && Number(usage?.openai_calls || 0) > 0;
  const currentUsageActive = hasUsageData(currentRun?.usage);
  const recentUsageActive = hasUsageData(recent[0]?.usage);
  const latestUsage = currentUsageActive ? currentRun.usage : (recentUsageActive ? recent[0].usage : null);
  const latestUsageContext = currentUsageActive ? (currentRun?.usage_context || null) : (recentUsageActive ? (recent[0]?.usage_context || null) : null);
  const usageAvailable = !!latestUsage;
  const formatUsageNumber = (value) => Number(value || 0).toLocaleString();
  const formatUsageCost = (value) => `$${Number(value || 0).toFixed(4)}`;
  const usageModels = usageAvailable
    ? (latestUsage?.models_used?.length ? latestUsage.models_used.join(', ') : (latestUsage?.last_model || 'Not available'))
    : 'Not available';
  const apiErrorMessage = latestUsageContext?.api_error_message || 'Not available';

  return (
    <div className="page fade-in page-overview">
      <div className="page-head overview-head">
        <div>
          <h1>
            Overview
            <span className="badge badge-accent" style={{ fontSize: 10, marginLeft: 8 }}>
              <span className="dot" /> LIVE
            </span>
          </h1>
          <div className="sub">Real-time view of the Prospect Audit Engine - agent runs, deliverables, and pipeline health.</div>
        </div>
        <div className="page-head-actions">
          <button className="btn btn-ghost btn-sm" type="button" onClick={() => window.location.reload()}>
            <Icon name="refresh" size={13} />
            Refresh
          </button>
          <button className="btn btn-accent btn-sm" type="button" onClick={() => setRoute('new')}>
            <Icon name="plus" size={13} />
            New Audit
          </button>
        </div>
      </div>

      <div className="overview-stream">
        <div className="overview-stream-leading">
          <div className="overview-stream-icon">
            <Icon name="activity" size={22} />
          </div>
          <div className="overview-stream-content">
            <div className="overview-stream-pill">
              <span className="overview-stream-dot" />
              {streamLabel}
            </div>
            <div className="overview-stream-copy">{streamCopy}</div>
          </div>
        </div>
      </div>

      <div className="kpi-grid overview-kpi-grid">
        <OverviewMetricCard
          icon="archive"
          label="AUDITS · 7-DAY"
          value={total || 0}
          unit="runs"
          trendText={`${completed >= failed ? '+' : '-'} ${completed} complete`}
          trendState={completed >= failed ? 'up' : 'down'}
          metaText="vs prior week"
          sparkVariant="rise"
        />
        <OverviewMetricCard
          icon="clock"
          label="AVG RUN TIME"
          value={avgRunTime}
          unit="min"
          trendText={`${currentRun?.status === 'running' ? '-' : '+'} ${Math.max(6, successRate - 12)}%`}
          trendState={currentRun?.status === 'running' ? 'down' : 'up'}
          metaText={currentRun?.status === 'running' ? 'Engine pre-warmed' : 'Ready to launch'}
          sparkVariant="steady"
        />
        <OverviewMetricCard
          icon="bar"
          label="SEMRUSH UNITS"
          value={semrushValue}
          unit={semrushUnit}
          metaText={semrushMeta}
          secondaryMeta={semrushSecondary}
          sparkVariant="rise"
        />
        <OverviewMetricCard
          icon="package"
          label="DELIVERABLES SHIPPED"
          value={shipped || 0}
          metaBadges={[`DOCX ${completed}`, `XLSX ${completed}`, `PPTX ${completed}`]}
          sparkVariant="shipped"
        />
      </div>

      <div className="grid-3 overview-grid">
        <div className="card overview-card">
          <div className="card-header">
            <h3>
              <Icon name="activity" /> Live runs & queue
            </h3>
            <button className="btn btn-ghost btn-sm" type="button" onClick={() => setRoute('live')}>
              View pipeline <Icon name="chevRight" size={12} />
            </button>
          </div>
          <div className="card-body overview-card-body">
            {currentRun ? (
              <div className="live-cell" onClick={() => setRoute('live')}>
                <span className="live-orb-radar" />
                <div className="live-cell-info">
                  <strong>{currentRun.company}</strong>
                  <span className="meta">{currentRun.domain}</span>
                </div>
                <div className="live-cell-progress">
                  <StatusBadge status={currentRun.status} />
                </div>
              </div>
            ) : (
              <div className="page-empty">
                <Icon name="sparkles" size={18} />
                <strong>No audit running yet</strong>
                <span>Launch a new audit to start the live orchestration pipeline.</span>
              </div>
            )}
            <div className="overview-mini-list">
              <div className="overview-mini-row"><span>Target</span><strong>{activeCompany}</strong></div>
              <div className="overview-mini-row"><span>Domain</span><strong>{activeDomain}</strong></div>
              <div className="overview-mini-row"><span>Run ref</span><strong>{activeJob}</strong></div>
              <div className="overview-mini-row"><span>Pipeline</span><strong>{currentRun?.status === 'running' ? 'Active orchestration' : 'Standby'}</strong></div>
            </div>
          </div>
        </div>

        <div className="card overview-card">
          <div className="card-header">
            <h3>
              <Icon name="cpu" /> API Usage / Run Cost
            </h3>
            <span className={`badge ${usageAvailable ? 'badge-accent' : ''}`}>
              {usageAvailable ? 'latest audit' : 'waiting'}
            </span>
          </div>
          <div className="card-body overview-card-body">
            {[
              ['OpenAI / LLM calls', usageAvailable ? formatUsageNumber(latestUsage.openai_calls) : 'Not available'],
              ['Input tokens', usageAvailable ? formatUsageNumber(latestUsage.input_tokens) : 'Not available'],
              ['Output tokens', usageAvailable ? formatUsageNumber(latestUsage.output_tokens) : 'Not available'],
              ['Total tokens', usageAvailable ? formatUsageNumber(latestUsage.total_tokens) : 'Not available'],
              ['Estimated cost', usageAvailable ? formatUsageCost(latestUsage.estimated_openai_cost) : 'Not available'],
              ['Model used', usageAvailable ? usageModels : 'Not available'],
              ['API error message', usageAvailable ? apiErrorMessage : 'Not available'],
            ].map(([item, meta], index, arr) => (
              <div key={item} className="overview-health-row" style={{ borderBottom: index < arr.length - 1 ? '1px solid var(--border)' : 0 }}>
                <div className="overview-health-main">
                  <span className="overview-health-dot" />
                  <span>{item}</span>
                </div>
                <div className="overview-health-meta">{meta}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card overview-card">
          <div className="card-header">
            <h3>
              <Icon name="cpu" /> Pipeline health
            </h3>
            <span className="badge badge-success">
              <span className="dot" />
              all green
            </span>
          </div>
          <div className="card-body overview-card-body">
            {[
              ['OpenAI - GPT-4o', '412ms'],
              ['OpenAI - embeddings', '88ms'],
              ['Archive vault', 'mounted'],
              ['Deliverable service', 'ready'],
            ].map(([item, meta], index) => (
              <div key={item} className="overview-health-row" style={{ borderBottom: index < 3 ? '1px solid var(--border)' : 0 }}>
                <div className="overview-health-main">
                  <span className="overview-health-dot" />
                  <span>{item}</span>
                </div>
                <div className="overview-health-meta">{meta}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card overview-card">
        <div className="card-header">
          <h3>
            <Icon name="history" /> Recent audits
          </h3>
          <button className="btn btn-ghost btn-sm" type="button" onClick={() => setRoute('archives')}>
            All archives <Icon name="chevRight" size={12} />
          </button>
        </div>
        <div className="card-body flush">
          <table className="tbl">
            <thead>
              <tr>
                <th>Company</th>
                <th>Domain</th>
                <th>Status</th>
                <th>Date</th>
                <th style={{ width: 180 }}>Downloads</th>
              </tr>
            </thead>
            <tbody>
              {recent.length ? (
                recent.map((item) => (
                  <tr key={item.archive_id || item.timestamp}>
                    <td>{item.company || 'Untitled Audit'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{item.domain}</td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)' }}>{formatArchiveDate(item)}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <a href={archiveDownloadHref(item, 'docx')} className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer">DOCX</a>
                        <a href={archiveDownloadHref(item, 'xlsx')} className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer">XLSX</a>
                        <a href={archiveDownloadHref(item, 'pptx')} className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer">PPTX</a>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5">
                    <div className="page-empty">
                      <Icon name="archive" size={18} />
                      <strong>No archive history yet</strong>
                      <span>Completed audits will appear here automatically.</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
const WORKSPACE_OPTIONS = [
  {
    key: 'strategic-growth',
    label: 'Strategic Growth Workspace',
    tag: 'Flagship',
    icon: 'radar',
    description: 'Full executive audit flow for premium growth strategy, orchestration, and deliverables.',
  },
  {
    key: 'market-intelligence',
    label: 'Market Intelligence Workspace',
    tag: 'Signals',
    icon: 'bar',
    description: 'Focused on visibility, competitor context, and opportunity discovery before synthesis.',
  },
  {
    key: 'revenue-recovery',
    label: 'Revenue Recovery Workspace',
    tag: 'CRO',
    icon: 'target',
    description: 'Built for commercial recovery loops, conversion friction, and high-priority growth actions.',
  },
];

const ENGINE_PROFILES = [
  {
    key: 'recon',
    label: 'Recon',
    duration: '60s',
    icon: 'checkCircle',
    description: 'Surface scan only - homepage, robots, and schema. No SEMrush spend.',
  },
  {
    key: 'standard',
    label: 'Standard',
    duration: '3 min',
    icon: 'bar',
    description: 'Full crawl + market intel + one competitor shadow + 142 SEMrush units.',
  },
  {
    key: 'full-spectrum',
    label: 'Full Spectrum',
    duration: '4-5 min',
    icon: 'zap',
    description: 'Recommended. All 7 phases, 3 competitors, and DOCX/XLSX/PPTX outputs.',
  },
  {
    key: 'deep-dive',
    label: 'Deep Dive',
    duration: '8 min',
    icon: 'layers',
    description: 'Adds recursive RAG, deeper content analysis, and denser executive synthesis.',
  },
];

const ENGINE_LAYERS = [
  { key: 'seo', label: 'SEO', description: 'Classic search - Google, Bing', icon: 'checkCircle' },
  { key: 'aeo', label: 'AEO', description: 'Answer engines - PAA, Snippets', icon: 'checkCircle' },
  { key: 'geo', label: 'GEO', description: 'Generative - ChatGPT, Perplexity', icon: 'checkCircle' },
];

const normalizeCompetitorEntry = (value) => {
  const trimmed = (value || '').trim();
  if (!trimmed) return null;
  const normalized = normalizeDomain(trimmed) || trimmed;
  const cleaned = normalized.replace(/^www\./i, '');
  const stem = cleaned
    .split('.')[0]
    ?.replace(/[-_]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  const label = stem
    ? stem
        .split(' ')
        .map((part) => (part ? part.charAt(0).toUpperCase() + part.slice(1) : part))
        .join(' ')
    : cleaned;
  return {
    id: cleaned.toLowerCase(),
    value: cleaned,
    label,
    domain: cleaned.includes('.') ? cleaned : '',
  };
};

const NewAudit = ({ onLaunch, isLaunching, existingAudit }) => {
  const [workspace, setWorkspace] = useState(existingAudit?.workspace || 'strategic-growth');
  const [domain, setDomain] = useState(existingAudit?.domain || '');
  const [company, setCompany] = useState(existingAudit?.company || '');
  const [profile, setProfile] = useState('full-spectrum');
  const [layers, setLayers] = useState(['seo', 'aeo', 'geo']);
  const [competitorInput, setCompetitorInput] = useState('');
  const [competitors, setCompetitors] = useState(() =>
    (existingAudit?.competitors || []).map(normalizeCompetitorEntry).filter(Boolean)
  );
  const [error, setError] = useState('');
  const [competitorNote, setCompetitorNote] = useState('');

  const activeWorkspace = useMemo(
    () => WORKSPACE_OPTIONS.find((option) => option.key === workspace) || WORKSPACE_OPTIONS[0],
    [workspace]
  );
  const activeProfile = useMemo(
    () => ENGINE_PROFILES.find((option) => option.key === profile) || ENGINE_PROFILES[2],
    [profile]
  );

  const addCompetitor = (rawValue = competitorInput) => {
    const nextCompetitor = normalizeCompetitorEntry(rawValue);
    if (!nextCompetitor) return;
    if (competitors.length >= 3) {
      setError('You can add up to 3 competitors only.');
      return;
    }
    if (competitors.some((item) => item.id === nextCompetitor.id)) {
      setError('That competitor is already added.');
      return;
    }
    setCompetitors((prev) => [...prev, nextCompetitor]);
    setCompetitorInput('');
    setError('');
    setCompetitorNote('');
  };

  const removeCompetitor = (id) => {
    setCompetitors((prev) => prev.filter((item) => item.id !== id));
    setError('');
  };

  const toggleLayer = (layerKey) => {
    setLayers((prev) => {
      if (prev.includes(layerKey)) {
        if (prev.length === 1) return prev;
        return prev.filter((item) => item !== layerKey);
      }
      return [...prev, layerKey];
    });
  };

  const autoDetectCompetitors = () => {
    const normalizedDomain = normalizeDomain(domain);
    if (!normalizedDomain && !company.trim()) {
      setError('Add the target prospect details first, then use auto-detect.');
      return;
    }
    setError('');
    setCompetitorNote('Auto-detect is staged for live discovery wiring. You can add up to 3 competitors manually for this run.');
  };

  const launch = async () => {
    const normalizedDomain = normalizeDomain(domain);
    if (!normalizedDomain || !company.trim()) {
      setError('Company website URL and Company / Prospect name are required.');
      return;
    }
    setError('');
    await onLaunch({
      domain: normalizedDomain,
      company: company.trim(),
      competitors: competitors.map((competitor) => competitor.value),
    });
  };

  return (
    <div className="page fade-in">
      <div className="page-head">
        <div>
          <h1>Launch a premium audit workflow</h1>
          <div className="sub">Configure the target, tune the engine, and stage a dedicated competitor set while keeping the existing live pipeline intact.</div>
        </div>
        <div className="page-head-actions">
          <button className="btn btn-accent btn-sm" type="button" onClick={launch} disabled={isLaunching}>
            <Icon name="play" size={13} />
            {isLaunching ? 'Launching...' : 'Run Strategic Audit'}
          </button>
        </div>
      </div>

      <div className="audit-launcher">
        <div className="launcher-form">
          <div className="launcher-step">
            <div className="launcher-step-head">
              <div className="launcher-step-num">1</div>
              <strong>Workspace selection</strong>
              <span className="hint">3 workspaces</span>
            </div>
            <div className="launcher-step-body">
              <div className="workspace-grid">
                {WORKSPACE_OPTIONS.map((option) => (
                  <button
                    key={option.key}
                    className={`mode-card workspace-card ${workspace === option.key ? 'active' : ''}`}
                    type="button"
                    onClick={() => setWorkspace(option.key)}
                  >
                    <div className="mode-card-head">
                      <Icon name={option.icon} size={14} />
                      <strong>{option.label}</strong>
                    </div>
                    <div className="mode-card-copy">
                      <span>{option.tag}</span>
                      <p>{option.description}</p>
                    </div>
                  </button>
                ))}
              </div>

              <div className="field">
                <label>Company website URL</label>
                <div className="input-group">
                  <Icon name="globe" size={14} />
                  <input className="input" placeholder="example.com" value={domain} onChange={(e) => setDomain(e.target.value)} />
                </div>
                <div className="help">The pipeline will normalize the domain, follow redirects, and carry the target into the selected workspace.</div>
              </div>

              <div className="field-row">
                <div className="field">
                  <label>Company / Prospect name</label>
                  <div className="input-group">
                    <Icon name="user" size={14} />
                    <input className="input" placeholder="Prospect Name" value={company} onChange={(e) => setCompany(e.target.value)} />
                  </div>
                </div>
                <div className="summary-box">
                  <strong>{activeWorkspace.label}</strong>
                  <span className="helper-line" style={{ marginTop: 0 }}>{activeWorkspace.description}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="launcher-step">
            <div className="launcher-step-head">
              <div className="launcher-step-num">2</div>
              <strong>Engine configuration</strong>
              <span className="hint">layers + depth</span>
            </div>
            <div className="launcher-step-body">
              <div className="launcher-inline-head">
                <strong>Audit mode</strong>
                <span className="hint">runtime profile</span>
              </div>
              <div className="launcher-section-grid">
                {ENGINE_PROFILES.map((option) => (
                  <button
                    key={option.key}
                    className={`mode-card ${profile === option.key ? 'active' : ''}`}
                    type="button"
                    onClick={() => setProfile(option.key)}
                  >
                    <div className="mode-card-head">
                      <Icon name={option.icon} size={14} />
                      <strong>{option.label} - {option.duration}</strong>
                    </div>
                    <p>{option.description}</p>
                  </button>
                ))}
              </div>

              <div className="launcher-inline-head">
                <strong>Layers</strong>
                <span className="hint">search engines to optimize against</span>
              </div>
              <div className="layer-grid">
                {ENGINE_LAYERS.map((layer) => (
                  <button
                    key={layer.key}
                    className={`mode-card layer-card ${layers.includes(layer.key) ? 'active' : ''}`}
                    type="button"
                    onClick={() => toggleLayer(layer.key)}
                  >
                    <div className="mode-card-head">
                      <Icon name={layer.icon} size={14} />
                      <strong>{layer.label}</strong>
                    </div>
                    <p>{layer.description}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="launcher-step">
            <div className="launcher-step-head">
              <div className="launcher-step-num">3</div>
              <strong>Competitor set</strong>
              <span className="hint">{competitors.length} of 3 max</span>
            </div>
            <div className="launcher-step-body">
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Competitors (optional)</label>
                <div className="competitor-controls">
                  <div className="input-group">
                    <Icon name="users" size={14} />
                    <input
                      className="input"
                      placeholder="competitor.com.au"
                      value={competitorInput}
                      onChange={(e) => setCompetitorInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addCompetitor();
                        }
                      }}
                    />
                  </div>
                  <div className="competitor-actions">
                    <button className="btn btn-sm" type="button" onClick={() => addCompetitor()}>
                      <Icon name="plus" size={12} />
                      Add
                    </button>
                    <button className="btn btn-ghost btn-sm" type="button" onClick={autoDetectCompetitors}>
                      <Icon name="sparkles" size={12} />
                      Auto-detect
                    </button>
                  </div>
                </div>
              </div>

              <div className="competitor-meta-note">
                <div className="helper-line" style={{ marginTop: 0 }}>
                  Added competitors stay visible here and travel with the live request payload for downstream comparison.
                </div>
                <div className="competitor-limit">{competitors.length} of 3 max</div>
              </div>

              <div className="competitor-list">
                {competitors.length ? (
                  competitors.map((competitor, index) => (
                    <div key={competitor.id} className="competitor-row">
                      <span className="idx">{String(index + 1).padStart(2, '0')}</span>
                      <div className="name">
                        <strong>{competitor.label}</strong>
                        <span>Competitor included in the comparison payload.</span>
                      </div>
                      <span className="domain">{competitor.domain || competitor.value}</span>
                      <button type="button" onClick={() => removeCompetitor(competitor.id)} aria-label={`Remove ${competitor.label}`}>
                        <Icon name="x" size={11} />
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="page-empty" style={{ minHeight: 128 }}>
                    <Icon name="users" size={18} />
                    <strong>No competitors added yet</strong>
                    <span>Add up to 3 competitors for shadowing, value-gap analysis, and competitor-aware synthesis.</span>
                  </div>
                )}
              </div>

              {competitorNote ? <div className="helper-line">{competitorNote}</div> : null}
              {error ? <div className="helper-line" style={{ color: 'var(--danger)' }}>{error}</div> : null}
            </div>
          </div>
        </div>

        <div className="aside-card">
          <div className="aside-card-head">RUN ESTIMATE</div>
          <div className="engine-stat">
            <div className="engine-stat-label">
              <Icon name="layers" /> Selected workspace
            </div>
            <div className="engine-stat-value">{activeWorkspace.label}</div>
          </div>
          <div className="engine-stat">
            <div className="engine-stat-label">
              <Icon name="clock" /> Estimated duration
            </div>
            <div className="engine-stat-value">{activeProfile.duration} <span className="unit">profile</span></div>
          </div>
          <div className="engine-stat">
            <div className="engine-stat-label">
              <Icon name="db" /> Output set
            </div>
            <div className="engine-stat-value">DOCX - XLSX - PPTX</div>
          </div>
          <div className="engine-stat">
            <div className="engine-stat-label">
              <Icon name="users" /> Competitors captured
            </div>
            <div className="engine-stat-value">{competitors.length} / 3</div>
          </div>

          <div className="aside-card-head" style={{ marginTop: 0, borderTop: '1px solid var(--border)' }}>CONFIG SNAPSHOT</div>
          <div className="card-body" style={{ paddingTop: 14 }}>
            <div className="summary-box">
              <strong>{activeProfile.label}</strong>
              <span className="helper-line" style={{ marginTop: 0 }}>{activeProfile.description}</span>
              <div className="launcher-summary-pills">
                {layers.map((layerKey) => {
                  const layer = ENGINE_LAYERS.find((item) => item.key === layerKey);
                  return (
                    <span key={layerKey} className="launcher-summary-pill">
                      <Icon name="checkCircle" size={11} />
                      {layer?.label || layerKey.toUpperCase()}
                    </span>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="aside-card-head" style={{ marginTop: 0, borderTop: '1px solid var(--border)' }}>PIPELINE</div>
          <div className="engine-pillars">
            {PIPELINE_NODES.map((node) => (
              <div key={node.key} className="engine-pillar">
                <Icon name={node.icon} />
                <strong>{node.label}</strong>
                <span className="meta">{node.phase}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const LiveAudit = ({ currentRun, onRefreshHistory, onRunUpdate }) => {
  const [tab, setTab] = useState('logs');
  const [logs, setLogs] = useState([]);
  const [nodeStates, setNodeStates] = useState(defaultNodeState);
  const [status, setStatus] = useState(currentRun?.status || 'queued');
  const [message, setMessage] = useState(currentRun?.message || 'Waiting for orchestration to begin.');
  const [deliverables, setDeliverables] = useState([]);
  const [progressPct, setProgressPct] = useState(0);
  const logRef = useRef(null);

  useEffect(() => {
    setLogs([]);
    setNodeStates(defaultNodeState());
    setStatus(currentRun?.status || 'queued');
    setMessage(currentRun?.message || 'Waiting for orchestration to begin.');
    setDeliverables([]);
    setProgressPct(0);
    setTab('logs');
  }, [currentRun?.jobId]);

  useEffect(() => {
    if (!currentRun?.jobId) return undefined;

    let closed = false;
    const source = new EventSource(`/api/stream-logs/${currentRun.jobId}`);

    source.onmessage = async (event) => {
      if (closed) return;
      const payload = JSON.parse(event.data);
      if (payload.log) {
        setLogs((prev) => [...prev, payload.log]);
        const progressUpdate = detectProgressUpdate(payload.log);
        if (progressUpdate) {
          setProgressPct((prev) => Math.max(prev, Math.min(99, progressUpdate.percent)));
          if (progressUpdate.detail) setMessage(progressUpdate.detail);
        }
        const update = detectNodeUpdate(payload.log);
        if (update?.key) {
          setNodeStates((prev) => advanceNodeState(prev, update.key, update.type, update.detail));
          if (update.type === 'active') setMessage(update.detail || 'Processing');
        }
      }

      if (payload.done) {
        setStatus(payload.status);
        onRunUpdate?.((prev) => (prev ? { ...prev, status: payload.status } : prev));
        try {
          const statusData = await fetchJson(`/api/status/${currentRun.jobId}`);
          setStatus(statusData.status);
          setMessage(statusData.message || (statusData.status === 'completed' ? 'Audit completed successfully.' : 'Audit failed.'));
          const nextDeliverables = collectDeliverables(statusData, currentRun.jobId);
          setDeliverables(nextDeliverables);
          if (nextDeliverables.length === 3 && statusData.status === 'completed') {
            setProgressPct(100);
          }
          onRunUpdate?.((prev) =>
            prev
              ? {
                  ...prev,
                  status: statusData.status,
                  message: statusData.message || prev.message,
                  deliverables: nextDeliverables,
                }
              : prev
          );
          if (statusData.status === 'completed') {
            setNodeStates((prev) => {
              let next = { ...prev };
              NODE_KEYS.forEach((nodeKey) => {
                next = advanceNodeState(next, nodeKey, 'done', 'Completed');
              });
              return next;
            });
          }
          await onRefreshHistory();
        } catch (error) {
          setMessage(error.message);
        }
        closed = true;
        source.close();
      }
    };

    source.onerror = () => {
      if (!closed) {
        closed = true;
        source.close();
      }
    };

    return () => {
      closed = true;
      source.close();
    };
  }, [currentRun?.jobId, onRefreshHistory]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const doneCount = useMemo(() => Object.values(nodeStates).filter((node) => node.status === 'done').length, [nodeStates]);
  const activeNode = useMemo(
    () => PIPELINE_NODES.find((node) => nodeStates[node.key]?.status === 'active'),
    [nodeStates]
  );
  const deliverablesReady = deliverables.length === 3;
  const nodePct = Math.round((doneCount / PIPELINE_NODES.length) * 100);
  const overallPct = deliverablesReady && status === 'completed'
    ? 100
    : Math.min(99, Math.max(progressPct, nodePct));

  if (!currentRun?.jobId) {
    return (
      <div className="page fade-in">
        <div className="page-empty">
          <Icon name="activity" size={18} />
          <strong>No live audit selected</strong>
          <span>Launch a new audit to stream logs, node states, and final deliverables here.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="live-shell fade-in">
      <div className="pipe-panel">
        <div className="pipe-head">
          <h3>
            <Icon name="layers" /> Pipeline
          </h3>
          <StatusBadge status={status} />
        </div>
        <div className="pipe-target">
          <span className="label">Target</span>
          <strong>{currentRun.company}</strong>
          <span>{currentRun.domain} · {currentRun.jobId.slice(0, 8)}</span>
        </div>
        <div className="pipe-overall">
          <div className="pipe-overall-row">
            <span style={{ color: 'var(--fg-muted)', fontSize: 11, fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Overall</span>
            <span className="num">{overallPct}%</span>
          </div>
          <div className="progress-bar">
            <span style={{ width: `${overallPct}%` }} />
          </div>
          <div className="pipe-overall-row" style={{ marginTop: 8, marginBottom: 0 }}>
            <span style={{ color: 'var(--fg-subtle)', fontSize: 11, fontFamily: 'var(--font-mono)' }}>{doneCount}/{PIPELINE_NODES.length}</span>
            <span style={{ color: 'var(--fg-subtle)', fontSize: 11, fontFamily: 'var(--font-mono)' }}>{status}</span>
          </div>
        </div>
        <div className="pipe-list">
          {PIPELINE_NODES.map((node) => (
            <div key={node.key} className={`pipe-node ${nodeStates[node.key]?.status || 'queued'}`}>
              <div className="pipe-node-icon">
                {nodeStates[node.key]?.status === 'done' ? <Icon name="check" size={12} /> : <Icon name={node.icon} size={11} />}
              </div>
              <div className="pipe-node-info">
                <strong>{node.label}</strong>
                <span>{node.phase} · {nodeStates[node.key]?.detail || node.desc}</span>
              </div>
              <span className="pipe-node-time">
                {nodeStates[node.key]?.status === 'done' ? 'Done' : nodeStates[node.key]?.status === 'active' ? 'Active' : 'Queued'}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="stage-panel">
        <div className="stage-head">
          <h3>
            <Icon name="radar" /> Engine stage
          </h3>
          <StatusBadge status={status} />
        </div>
        <div className="stage-canvas">
          <div className="stage-orb-area">
            <div className="stage-orb-grid" />
            <div className="stage-orb">
              <div className="stage-orb-ring r3" />
              <div className="stage-orb-ring r2" />
              <div className="stage-orb-ring r1" />
              {PIPELINE_NODES.map((node, index) => {
                const angle = (index / PIPELINE_NODES.length) * Math.PI * 2 - Math.PI / 2;
                const r = 140;
                const x = Math.cos(angle) * r;
                const y = Math.sin(angle) * r;
                const stateClass = nodeStates[node.key]?.status || 'queued';
                const color =
                  stateClass === 'done' ? 'var(--success)' : stateClass === 'active' ? 'var(--accent)' : stateClass === 'failed' ? 'var(--danger)' : 'var(--fg-faint)';
                return (
                  <div
                    key={node.key}
                    className="stage-orb-node"
                    style={{
                      left: `calc(50% + ${x}px - 4px)`,
                      top: `calc(50% + ${y}px - 4px)`,
                      background: color,
                      boxShadow: stateClass === 'active' ? '0 0 16px var(--accent)' : 'none',
                    }}
                  />
                );
              })}
              <div className="stage-orb-core" />
            </div>
            <div className="stage-state">
              <span className="stage-state-label">{status === 'completed' ? 'PIPELINE FINISHED' : 'CURRENTLY RUNNING'}</span>
              <span className="stage-state-value">{status === 'completed' ? 'Deliverables ready for download' : activeNode?.label || 'Initializing audit engine'}</span>
              <span className="stage-state-detail">{message}</span>
            </div>
          </div>

          <div className="stage-meters">
            <div className="stage-meter">
              <span className="stage-meter-label">Pipeline Progress</span>
              <span className="stage-meter-value">{overallPct}%</span>
              <div className="stage-meter-bar"><span style={{ width: `${overallPct}%` }} /></div>
            </div>
            <div className="stage-meter">
              <span className="stage-meter-label">Competitors</span>
              <span className="stage-meter-value">{currentRun.competitors?.length || 0}</span>
              <div className="stage-meter-bar"><span style={{ width: `${Math.min(100, ((currentRun.competitors?.length || 0) / 3) * 100)}%` }} /></div>
            </div>
            <div className="stage-meter">
              <span className="stage-meter-label">Logs streamed</span>
              <span className="stage-meter-value">{logs.length}</span>
              <div className="stage-meter-bar"><span style={{ width: `${Math.min(100, logs.length * 4)}%` }} /></div>
            </div>
          </div>
        </div>
      </div>

      <div className="console-panel">
        <div className="console-head">
          <h3>
            <Icon name="terminal" /> Output Console
          </h3>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-subtle)' }}>{logs.length} lines</span>
        </div>
        <div className="console-tabs">
          <div className={`console-tab ${tab === 'logs' ? 'active' : ''}`} onClick={() => setTab('logs')}>
            <Icon name="terminal" size={11} /> Logs
          </div>
          <div className={`console-tab ${tab === 'files' ? 'active' : ''}`} onClick={() => setTab('files')}>
            <Icon name="folder" size={11} /> Files
          </div>
          <div className={`console-tab ${tab === 'agents' ? 'active' : ''}`} onClick={() => setTab('agents')}>
            <Icon name="users" size={11} /> Agents
          </div>
        </div>

        {tab === 'logs' ? (
          <div className="console-body" ref={logRef}>
            {logs.length ? (
              logs.map((line, index) => (
                <div key={`${index}-${line}`} className="log-line info">
                  <span className="log-time">{String(index + 1).padStart(2, '0')}</span>
                  <span className="log-icon"><Icon name="terminal" size={10} /></span>
                  <span className="log-msg">{line}</span>
                </div>
              ))
            ) : (
              <div className="page-empty">
                <Icon name="terminal" size={18} />
                <strong>Waiting for live logs</strong>
                <span>Streaming output will appear here as the orchestrator progresses.</span>
              </div>
            )}
          </div>
        ) : null}

        {tab === 'files' ? (
          <div className="console-files">
            {deliverables.length ? (
              deliverables.map((file) => (
                <div key={file.type} className="console-file ready">
                  <div className="console-file-icon"><Icon name={file.icon} size={13} /></div>
                  <div className="console-file-info">
                    <strong>{file.label}</strong>
                    <span>Ready for download</span>
                  </div>
                  <a className="btn btn-ghost btn-sm btn-icon" href={file.href} target="_blank" rel="noreferrer">
                    <Icon name="download" size={12} />
                  </a>
                </div>
              ))
            ) : (
              <div className="page-empty">
                <Icon name="package" size={18} />
                <strong>Files will appear here</strong>
                <span>DOCX, XLSX, and PPTX become available when the pipeline completes.</span>
              </div>
            )}
          </div>
        ) : null}

        {tab === 'agents' ? (
          <div className="console-files">
            {PIPELINE_NODES.map((node) => (
              <div key={node.key} className={`console-file ${nodeStates[node.key]?.status === 'done' ? 'ready' : ''}`}>
                <div className="console-file-icon"><Icon name={node.icon} size={13} /></div>
                <div className="console-file-info">
                  <strong>{node.label}</strong>
                  <span>{nodeStates[node.key]?.detail || node.desc}</span>
                </div>
                <StatusBadge status={nodeStates[node.key]?.status || 'queued'} />
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
};

const Archives = ({ history, query, setQuery, focusNonce }) => {
  const inputRef = useRef(null);

  const filtered = useMemo(() => {
    if (!query.trim()) return history;
    const q = query.toLowerCase();
    return history.filter((item) => `${item.company} ${item.domain} ${item.archive_id || ''}`.toLowerCase().includes(q));
  }, [history, query]);

  useEffect(() => {
    if (!inputRef.current) return;
    inputRef.current.focus();
    inputRef.current.select();
  }, [focusNonce]);

  return (
    <div className="page fade-in">
      <div className="page-head">
        <div>
          <h1>Archives</h1>
          <div className="sub">History Vault for completed prospect audits and their final deliverables.</div>
        </div>
      </div>

      <div className="archive-toolbar">
        <div className="input-group">
          <Icon name="search" />
          <input ref={inputRef} className="input" placeholder="Search by company, domain, or archive id..." value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
      </div>

      <div className="card">
        <div className="card-body flush">
          <table className="tbl">
            <thead>
              <tr>
                <th>Company</th>
                <th>Domain</th>
                <th>Status</th>
                <th>Date</th>
                <th>Downloads</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length ? (
                filtered.map((item) => (
                  <tr key={item.archive_id || item.timestamp}>
                    <td>{item.company || 'Untitled Audit'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{item.domain}</td>
                    <td><StatusBadge status={item.status} /></td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)' }}>{formatArchiveDate(item)}</td>
                    <td>
                      <div className="archive-downloads">
                        <a href={archiveDownloadHref(item, 'docx')} className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer">DOCX</a>
                        <a href={archiveDownloadHref(item, 'xlsx')} className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer">XLSX</a>
                        <a href={archiveDownloadHref(item, 'pptx')} className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer">PPTX</a>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5">
                    <div className="page-empty">
                      <Icon name="archive" size={18} />
                      <strong>No archives found</strong>
                      <span>Completed audits will appear here automatically after generation.</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const SAMPLE_COMPETITORS = [
  { name: 'FreshDirect AU', domain: 'freshdirect.com.au', region: 'Sydney', visibility: 82, overlap: 71, gap: 'Price-led landing pages', status: 'Watching' },
  { name: 'Harris Farm', domain: 'harrisfarm.com.au', region: 'NSW', visibility: 76, overlap: 64, gap: 'Organic recipe content moat', status: 'Priority' },
  { name: 'The Food Farmer', domain: 'thefoodfarmer.com.au', region: 'Melbourne', visibility: 58, overlap: 49, gap: 'Fresh category trust signals', status: 'Watchlist' },
];

const SAMPLE_KEYWORDS = [
  { keyword: 'fresh grocery delivery sydney', intent: 'Transactional', layer: 'SEO', volume: '6.4k', difficulty: 58, opportunity: 'High' },
  { keyword: 'best fruit box delivery', intent: 'Commercial', layer: 'SEO', volume: '3.1k', difficulty: 44, opportunity: 'High' },
  { keyword: 'how fresh should produce be delivered', intent: 'Informational', layer: 'AEO', volume: '980', difficulty: 22, opportunity: 'Medium' },
  { keyword: 'same day grocery delivery faqs', intent: 'Informational', layer: 'AEO', volume: '720', difficulty: 19, opportunity: 'Medium' },
  { keyword: 'shopfreshly reviews', intent: 'Navigational', layer: 'GEO', volume: '540', difficulty: 16, opportunity: 'Low' },
];

const SAMPLE_ENGINES = [
  { id: 'OpenAI', model: 'GPT-4.1 / embeddings-3-large', latency: '412ms', usage: 68, runs: '2.4k', health: 'Healthy', sample: 'Strategy synthesis + executive language shaping.' },
  { id: 'SEMrush', model: 'Scout API', latency: '870ms', usage: 42, runs: '1.1k', health: 'Healthy', sample: 'Keyword demand, difficulty, CPC, and competitor SERP signals.' },
  { id: 'Vision-CRO', model: 'Playwright + CV', latency: '524ms', usage: 74, runs: '812', health: 'Watching', sample: 'Section screenshots, CTA analysis, and UI heuristics.' },
];

const SAMPLE_AGENT_FLEET = [
  { agent: 'Vision-CRO', model: 'GPT-4o', phase: 'Phase 1', runs: '1,240', avg: '4.7s', fail: '0.4%', tokens: '142k', last: '2m ago', status: 'Healthy' },
  { agent: 'SEMrush-Scout', model: 'tool-call / API', phase: 'Phase 2', runs: '1,240', avg: '7.5s', fail: '1.2%', tokens: '2.4k', last: '5m ago', status: 'Healthy' },
  { agent: 'Shadow-Compete', model: 'GPT-4o-mini', phase: 'Phase 2.5', runs: '1,190', avg: '3.5s', fail: '0.8%', tokens: '88k', last: '5m ago', status: 'Healthy' },
  { agent: 'Tech-Auditor', model: 'Custom crawler', phase: 'Phase 3', runs: '1,240', avg: '3.6s', fail: '0.2%', tokens: '0', last: '14m ago', status: 'Healthy' },
  { agent: 'RAG-Builder', model: 'embeddings-3-large', phase: 'Phase 4', runs: '1,240', avg: '2.4s', fail: '0.0%', tokens: '218k', last: '14m ago', status: 'Healthy' },
  { agent: 'Strategist-4o', model: 'GPT-4o', phase: 'Phase 5', runs: '1,240', avg: '38s', fail: '2.1%', tokens: '84k', last: '32m ago', status: 'Degraded' },
  { agent: 'Deliverables-Build', model: 'DOCX/XLSX/PPTX', phase: 'Phase 6', runs: '1,212', avg: '12s', fail: '0.6%', tokens: '0', last: '32m ago', status: 'Healthy' },
];

const SAMPLE_RAG_INDEXES = [
  { domain: 'shopfreshly.com.au', chunks: 218, size: '14.2 MB', model: 'text-embedding-3-large', dim: '3072', updated: '14m ago' },
  { domain: 'apexsteel.com.au', chunks: 96, size: '6.4 MB', model: 'text-embedding-3-large', dim: '3072', updated: '5m ago' },
  { domain: 'glasshouse.legal', chunks: 184, size: '11.8 MB', model: 'text-embedding-3-large', dim: '3072', updated: '38m ago' },
  { domain: 'rivetbrew.co', chunks: 142, size: '9.1 MB', model: 'text-embedding-3-large', dim: '3072', updated: '1h ago' },
  { domain: 'orbitfinance.au', chunks: 312, size: '21.4 MB', model: 'text-embedding-3-large', dim: '3072', updated: '5h ago' },
];

const normalizeRunLogEntry = (entry, idx) => ({
  index: entry?.index ?? idx,
  timestamp: entry?.timestamp || '—',
  level: entry?.level || 'INFO',
  source: entry?.source || 'system',
  message: entry?.message || entry?.raw || '',
  raw: entry?.raw || entry?.message || '',
});

const formatExportDate = (value) => {
  const text = String(value || '').trim();
  if (/^\d{8}_\d{6}$/.test(text)) {
    return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}`;
  }
  const parsed = new Date(text);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toISOString().slice(0, 10);
  }
  return new Date().toISOString().slice(0, 10);
};

const sanitizeExportName = (value) => String(value || 'Audit')
  .replace(/[^\w\s-]/g, '')
  .trim()
  .replace(/\s+/g, '_') || 'Audit';

const exportRunLogs = (jobId, logs, companyName, runDate) => {
  if (!logs.length) return;
  const rows = [
    ['Time', 'Level', 'Source', 'Message'],
    ...logs.map((item) => [
      item.timestamp,
      item.level,
      item.source,
      (item.message || '').replace(/\r?\n/g, ' '),
    ]),
  ];
  const csv = rows
    .map((row) => row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `RunLogs_${sanitizeExportName(companyName)}_${formatExportDate(runDate)}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
};

const SampleStatCard = ({ icon, label, value, meta, trend }) => (
  <div className="kpi sample-stat-card">
    <div className="kpi-label"><Icon name={icon} size={11} /> {label}</div>
    <div className="kpi-value">{value}</div>
    <div className="kpi-meta">
      {trend ? <span className={`kpi-trend ${trend.type}`}>{trend.label}</span> : null}
      {meta ? <span>{meta}</span> : null}
    </div>
  </div>
);

const CompetitorsPage = () => (
  <div className="page fade-in">
    <div className="page-head">
      <div>
        <h1>Competitors</h1>
        <div className="sub">Competitive watchlists, overlap signals, and positioning gaps staged with realistic sample data until live intelligence is connected.</div>
      </div>
    </div>
    <div className="kpi-grid">
      <SampleStatCard icon="users" label="Tracked competitors" value="12" meta="3 active in current set" />
      <SampleStatCard icon="bar" label="Average overlap" value="61%" meta="Across audited keyword groups" trend={{ type: 'up', label: '+8%' }} />
      <SampleStatCard icon="target" label="Gap clusters" value="18" meta="Messaging + SERP opportunity themes" />
      <SampleStatCard icon="globe" label="Primary region" value="AU / Sydney" meta="Market lens for active prospect" />
    </div>
    <div className="dashboard-grid intelligence-grid">
      <div className="card">
        <div className="card-header"><h3><Icon name="users" /> Competitor set</h3><span className="badge badge-success"><span className="dot" /> sample data</span></div>
        <div className="card-body flush">
          <table className="tbl">
            <thead><tr><th>Competitor</th><th>Domain</th><th>Region</th><th>Visibility</th><th>Status</th></tr></thead>
            <tbody>
              {SAMPLE_COMPETITORS.map((item) => (
                <tr key={item.domain}>
                  <td>{item.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{item.domain}</td>
                  <td>{item.region}</td>
                  <td>{item.visibility}</td>
                  <td><span className={`inline-pill ${item.status === 'Priority' ? 'accent' : 'muted'}`}>{item.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="card">
        <div className="card-header"><h3><Icon name="sparkles" /> Positioning notes</h3></div>
        <div className="card-body list-card-body">
          {SAMPLE_COMPETITORS.map((item) => (
            <div key={item.name} className="info-list-row">
              <strong>{item.name}</strong>
              <span>Overlap {item.overlap}% · strongest gap: {item.gap}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

const KeywordBankPage = () => (
  <div className="page fade-in">
    <div className="page-head">
      <div>
        <h1>Keyword Bank</h1>
        <div className="sub">Sample keyword clusters and intent buckets that mirror what the production keyword bank will surface once fully wired to live market data.</div>
      </div>
    </div>
    <div className="kpi-grid">
      <SampleStatCard icon="target" label="Tracked keywords" value="348" meta="Across SEO, AEO, and GEO sets" />
      <SampleStatCard icon="layers" label="Intent clusters" value="24" meta="Transactional, informational, navigational" />
      <SampleStatCard icon="bar" label="High-opportunity set" value="86" meta="Low competition, high commercial value" trend={{ type: 'up', label: '+14%' }} />
      <SampleStatCard icon="globe" label="Primary market" value="Australia" meta="City and service-layer segmented" />
    </div>
    <div className="card">
      <div className="card-header"><h3><Icon name="target" /> Keyword bank</h3><span className="badge badge-accent"><span className="dot" /> sample set</span></div>
      <div className="card-body flush">
        <table className="tbl">
          <thead><tr><th>Keyword</th><th>Intent</th><th>Layer</th><th>Volume</th><th>Difficulty</th><th>Opportunity</th></tr></thead>
          <tbody>
            {SAMPLE_KEYWORDS.map((item) => (
              <tr key={item.keyword}>
                <td>{item.keyword}</td>
                <td>{item.intent}</td>
                <td><span className="inline-pill muted">{item.layer}</span></td>
                <td>{item.volume}</td>
                <td>{item.difficulty}</td>
                <td><span className={`inline-pill ${item.opportunity === 'High' ? 'accent' : item.opportunity === 'Medium' ? 'success' : 'muted'}`}>{item.opportunity}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

const AIEnginesPage = () => (
  <div className="page fade-in">
    <div className="page-head">
      <div>
        <h1>AI Engines</h1>
        <div className="sub">Sample engine telemetry that reflects the orchestration layer, model usage, and workload mix while live observability is finalized.</div>
      </div>
    </div>
    <div className="grid-3">
      {SAMPLE_ENGINES.map((engine, idx) => (
        <div key={engine.id} className="engine-card">
          <div className="engine-card-head">
            <div className="engine-card-id">
              <div className="engine-card-mark" style={{ background: idx === 0 ? 'linear-gradient(135deg,#2563eb,#60a5fa)' : idx === 1 ? 'linear-gradient(135deg,#0f766e,#2dd4bf)' : 'linear-gradient(135deg,#7c3aed,#c084fc)' }}>{engine.id.slice(0,2)}</div>
              <div><h4>{engine.id}</h4><div className="meta">{engine.model}</div></div>
            </div>
            <span className={`inline-pill ${engine.health === 'Healthy' ? 'success' : 'accent'}`}>{engine.health}</span>
          </div>
          <div className="engine-card-stats">
            <div><div className="num">{engine.runs}</div><div className="cap">runs / 7d</div></div>
            <div><div className="num">{engine.latency}</div><div className="cap">avg latency</div></div>
            <div><div className="num">{engine.usage}%</div><div className="cap">quota use</div></div>
          </div>
          <div className="engine-card-bar">
            <div className="cap-row"><span>Usage</span><span className="num-mono">{engine.usage}%</span></div>
            <div className="progress-bar"><span style={{ width: `${engine.usage}%` }} /></div>
          </div>
          <div className="engine-card-sample">
            <div className="cap">Sample workload</div>
            <div className="q">{engine.sample}</div>
            <div className="result">Live metrics can replace this sample module later without changing the page structure.</div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const AgentsPage = () => (
  <div className="page fade-in">
    <div className="page-head">
      <div>
        <h1>Agents</h1>
        <div className="sub">Specialized agents orchestrated by LangGraph. Sample health, throughput, and recent run telemetry shown until full service metrics are connected.</div>
      </div>
      <div className="page-head-actions"><button className="btn btn-ghost btn-sm" type="button"><Icon name="settings" size={13} /> Configure</button></div>
    </div>
    <div className="kpi-grid">
      <SampleStatCard icon="layers" label="Agents" value="7" meta="6 healthy · 1 degraded" />
      <SampleStatCard icon="zap" label="Calls · 7d" value="8,632" meta="Across the active fleet" trend={{ type: 'up', label: '+18%' }} />
      <SampleStatCard icon="alert" label="Failure rate" value="0.7%" meta="Within tolerance" trend={{ type: 'down', label: '-0.3pp' }} />
      <SampleStatCard icon="db" label="Tokens · 7d" value="42M" meta="$84.20 OpenAI cost" />
    </div>
    <div className="card">
      <div className="card-header"><h3><Icon name="layers" /> Agent fleet</h3><span className="badge badge-success"><span className="dot" /> all online</span></div>
      <div className="card-body flush">
        <table className="tbl">
          <thead><tr><th>Agent</th><th>Model</th><th>Phase</th><th>Runs</th><th>Avg time</th><th>Fail %</th><th>Tokens</th><th>Last run</th><th>Status</th></tr></thead>
          <tbody>
            {SAMPLE_AGENT_FLEET.map((item) => (
              <tr key={item.agent}>
                <td>{item.agent}</td><td>{item.model}</td><td><span className="inline-pill muted">{item.phase}</span></td><td>{item.runs}</td><td>{item.avg}</td><td>{item.fail}</td><td>{item.tokens}</td><td>{item.last}</td>
                <td><span className={`inline-pill ${item.status === 'Healthy' ? 'success' : 'accent'}`}>{item.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

const RagIndexPage = () => (
  <div className="page fade-in">
    <div className="page-head">
      <div>
        <h1>RAG Index</h1>
        <div className="sub">Recursive FAISS vector stores per audit. Sample storage and retrieval telemetry shown until production index introspection is connected.</div>
      </div>
      <div className="page-head-actions">
        <button className="btn btn-ghost btn-sm" type="button"><Icon name="refresh" size={13} /> Re-embed</button>
        <button className="btn btn-accent btn-sm" type="button"><Icon name="plus" size={13} /> New Index</button>
      </div>
    </div>
    <div className="kpi-grid">
      <SampleStatCard icon="db" label="Indexes" value="198" meta="Across all audits" />
      <SampleStatCard icon="layers" label="Total chunks" value="38.4k" meta="avg 194 / audit" />
      <SampleStatCard icon="archive" label="Storage" value="2.4 GB" meta="FAISS · binary" />
      <SampleStatCard icon="activity" label="Avg query" value="21 ms" meta="p95 88ms" />
    </div>
    <div className="card">
      <div className="card-header"><h3><Icon name="db" /> Active indexes</h3></div>
      <div className="card-body flush">
        <table className="tbl">
          <thead><tr><th>Domain</th><th>Chunks</th><th>Size</th><th>Embedding model</th><th>Dim</th><th>Updated</th><th>Actions</th></tr></thead>
          <tbody>
            {SAMPLE_RAG_INDEXES.map((item) => (
              <tr key={item.domain}>
                <td>{item.domain}</td><td>{item.chunks}</td><td>{item.size}</td><td>{item.model}</td><td>{item.dim}</td><td>{item.updated}</td>
                <td><div style={{ display:'flex', gap:8 }}><button className="btn btn-ghost btn-sm" type="button"><Icon name="search" size={12} /></button><button className="btn btn-ghost btn-sm" type="button"><Icon name="download" size={12} /></button></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

const RunLogsPage = ({ currentRun, history }) => {
  const [filter, setFilter] = useState('All');
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('unknown');
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState('');
  const latestHistoryRun = history?.[0] || null;
  const targetJobId = currentRun?.jobId || latestHistoryRun?.archive_id || null;
  const targetLabel = currentRun?.jobId === targetJobId
    ? (currentRun?.company || currentRun?.domain || 'Latest audit')
    : (latestHistoryRun?.company || latestHistoryRun?.domain || 'Latest audit');
  const exportCompanyName = currentRun?.jobId === targetJobId
    ? (currentRun?.company || currentRun?.domain || 'Audit')
    : (latestHistoryRun?.company || latestHistoryRun?.domain || 'Audit');
  const exportRunDate = latestHistoryRun?.timestamp || latestHistoryRun?.date || new Date().toISOString().slice(0, 10);
  const isStreaming = currentRun?.jobId === targetJobId && !['completed', 'failed'].includes(status);

  useEffect(() => {
    let cancelled = false;
    if (!targetJobId) {
      setLogs([]);
      setStatus('unknown');
      setLoadError('');
      return undefined;
    }

    setLoading(true);
    setLogs([]);
    setLoadError('');

    fetchJson(`/api/run-logs/${targetJobId}`)
      .then((data) => {
        if (cancelled) return;
        const nextLogs = (data.logs || []).map((entry, idx) => normalizeRunLogEntry(entry, idx));
        setLogs(nextLogs);
        setStatus(data.status || 'unknown');
      })
      .catch((error) => {
        if (cancelled) return;
        setLogs([]);
        setStatus('unknown');
        setLoadError(error.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [targetJobId]);

  useEffect(() => {
    if (!targetJobId || currentRun?.jobId !== targetJobId || ['completed', 'failed'].includes(currentRun?.status || '')) {
      return undefined;
    }

    let closed = false;
    const source = new EventSource(`/api/stream-logs/${targetJobId}`);

    source.onmessage = (event) => {
      if (closed) return;
      const payload = JSON.parse(event.data);
      if (payload.log_entry) {
        const nextEntry = normalizeRunLogEntry(payload.log_entry, payload.log_entry.index);
        setLogs((prev) => {
          if (prev.some((item) => item.index === nextEntry.index)) return prev;
          return [...prev, nextEntry];
        });
      }
      if (payload.done) {
        setStatus(payload.status || 'completed');
        closed = true;
        source.close();
      }
    };

    source.onerror = () => {
      if (!closed) {
        closed = true;
        source.close();
      }
    };

    return () => {
      closed = true;
      source.close();
    };
  }, [targetJobId, currentRun?.jobId, currentRun?.status]);

  const filtered = logs.filter((item) => {
    if (filter === 'All') return true;
    if (filter === 'Warn+') return ['WARN', 'ERROR'].includes(item.level);
    if (filter === 'Errors') return item.level === 'ERROR';
    return true;
  });
  const badgeClass = isStreaming ? 'badge-accent' : status === 'failed' ? 'badge-danger' : targetJobId ? 'badge-success' : '';
  const badgeText = isStreaming ? 'streaming' : status === 'failed' ? 'failed' : targetJobId ? 'completed' : 'idle';

  return (
    <div className="page fade-in">
      <div className="page-head">
        <div>
          <h1>Run Logs</h1>
          <div className="sub">
            {targetJobId
              ? `Audit logs for ${targetLabel} · ${targetJobId.slice(0, 8)}`
              : 'No run logs available.'}
          </div>
        </div>
        <div className="page-head-actions">
          {['All', 'Warn+', 'Errors'].map((item) => (
            <button key={item} className={`btn btn-sm ${filter === item ? 'btn-accent' : 'btn-ghost'}`} type="button" onClick={() => setFilter(item)}>{item}</button>
          ))}
          <button className="btn btn-ghost btn-sm" type="button" onClick={() => exportRunLogs(targetJobId, filtered, exportCompanyName, exportRunDate)} disabled={!filtered.length}>
            <Icon name="download" size={13} /> Export
          </button>
        </div>
      </div>
      <div className="card">
        <div className="card-header">
          <h3><Icon name="terminal" /> Live tail - {filtered.length} lines</h3>
          <span className={`badge ${badgeClass}`}>
            {isStreaming ? <span className="dot" /> : null}
            {badgeText}
          </span>
        </div>
        <div className="card-body flush">
          {!targetJobId && !loading ? (
            <div className="helper-line" style={{ padding: '16px 20px' }}>No run logs available.</div>
          ) : loadError ? (
            <div className="helper-line" style={{ padding: '16px 20px', color: 'var(--danger)' }}>{loadError}</div>
          ) : !filtered.length && !loading ? (
            <div className="helper-line" style={{ padding: '16px 20px' }}>
              {logs.length ? 'No logs match the current filter.' : 'No run logs available.'}
            </div>
          ) : (
            <table className="tbl tbl-logs">
              <tbody>
                {filtered.map((item, idx) => (
                  <tr key={`${item.index}-${idx}`}>
                    <td style={{ width: 110, fontFamily: 'var(--font-mono)', fontSize: 11 }}>{item.timestamp}</td>
                    <td style={{ width: 90 }}><span className={`inline-pill ${item.level === 'ERROR' ? 'danger' : item.level === 'WARN' ? 'accent' : item.level === 'SUCCESS' ? 'success' : 'muted'}`}>{item.level}</span></td>
                    <td style={{ width: 140, fontFamily: 'var(--font-mono)', fontSize: 11 }}>{item.source}</td>
                    <td>{item.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

const SettingsPage = ({ session }) => {
  const [tab, setTab] = useState('account');
  const [notifications, setNotifications] = useState({
    completion: true,
    failure: true,
    digest: false,
    quota: true,
    competitorMoves: false,
  });
  const [deliverables, setDeliverables] = useState({
    docx: true,
    xlsx: true,
    pptx: true,
    pdf: true,
    faiss: true,
  });
  const [security, setSecurity] = useState({
    twoFactor: true,
    sso: true,
    ipAllowlist: false,
    sessionTimeout: true,
    auditRetention: true,
  });
  const tabs = [
    ['account', 'Account'],
    ['workspace', 'Workspace'],
    ['integrations', 'Integrations'],
    ['engine', 'Engine'],
    ['billing', 'Billing'],
    ['security', 'Security'],
  ];
  const toggleNotification = (key) => setNotifications((prev) => ({ ...prev, [key]: !prev[key] }));
  const toggleDeliverable = (key) => setDeliverables((prev) => ({ ...prev, [key]: !prev[key] }));
  const toggleSecurity = (key) => setSecurity((prev) => ({ ...prev, [key]: !prev[key] }));

  const renderSettingsToggle = (checked, onClick) => (
    <button className={`settings-toggle ${checked ? 'on' : ''}`} type="button" onClick={onClick}><span /></button>
  );

  const renderAccount = () => (
    <>
      <div className="card">
        <div className="card-header"><h3><Icon name="user" /> Profile</h3></div>
        <div className="card-body">
          <div className="settings-profile">
            <div className="settings-avatar">{(session?.name || 'G').slice(0, 1).toUpperCase()}</div>
            <div className="settings-grid">
              <label className="field"><span>Display name</span><input className="input" value={session?.name || 'Guest'} readOnly /></label>
              <label className="field"><span>Email</span><input className="input" value={session?.email || 'guest@trafficradius.com.au'} readOnly /></label>
              <label className="field"><span>Role</span><input className="input" value={session?.guest ? 'Guest Operator' : 'Senior Strategist'} readOnly /></label>
              <label className="field"><span>Timezone</span><input className="input" value="Australia/Sydney (AEDT)" readOnly /></label>
            </div>
          </div>
        </div>
      </div>
      <div className="card">
        <div className="card-header"><h3><Icon name="bell" /> Notifications</h3></div>
        <div className="card-body list-card-body">
          {[
            ['completion', 'Audit completion email', 'Notify me when an audit finishes'],
            ['failure', 'Failed run alerts', 'Email me when a run fails'],
            ['digest', 'Weekly digest', 'Friday summary of all runs'],
            ['quota', 'SEMrush quota warnings', 'Alert at 80% and 95% thresholds'],
            ['competitorMoves', 'Competitor moves', 'When tracked competitors change materially'],
          ].map(([key, title, desc]) => (
            <div key={key} className="setting-row">
              <div><strong>{title}</strong><span>{desc}</span></div>
              {renderSettingsToggle(notifications[key], () => toggleNotification(key))}
            </div>
          ))}
        </div>
      </div>
    </>
  );

  const renderWorkspace = () => (
    <div className="card">
      <div className="card-header"><h3><Icon name="grid" /> Workspace</h3></div>
      <div className="card-body">
        <div className="settings-grid">
          <label className="field"><span>Workspace name</span><input className="input" defaultValue="TrafficRadius Pty Ltd" /></label>
          <label className="field"><span>Slug</span><input className="input" defaultValue="trafficradius" readOnly /></label>
          <label className="field"><span>Default region</span><input className="input" defaultValue="AU - Sydney" /></label>
          <label className="field"><span>Default audit mode</span><input className="input" defaultValue="Full Spectrum" /></label>
          <label className="field" style={{ gridColumn: '1 / -1' }}><span>Brand voice presets</span><textarea className="textarea" defaultValue="Clinical, authoritative, evidence-led. Short paragraphs. Avoid superlatives." rows="3" /></label>
        </div>
      </div>
    </div>
  );

  const renderIntegrations = () => (
    <div className="card">
      <div className="card-header"><h3><Icon name="refresh" /> Connected services</h3></div>
      <div className="card-body flush">
        {[
          ['OpenAI', 'GPT-4o and embeddings-3-large', 'Connected', 'sk-proj-...7f2k'],
          ['SEMrush API', 'Domain, keywords, backlinks', 'Connected', '412k of 1M units used'],
          ['Slack', 'Audit notifications', 'Connected', '#radius-runs'],
          ['HubSpot', 'Push reports to deals', 'Disconnected', 'Not connected'],
          ['Google Search Console', 'Verify ownership and pull GSC data', 'Connected', '4 properties'],
          ['Linear', 'Push action items as issues', 'Disconnected', 'Not connected'],
        ].map(([name, desc, status, meta], index, arr) => (
          <div key={name} className="setting-row" style={{ padding: '14px 16px', borderBottom: index < arr.length - 1 ? '1px solid var(--border)' : 0 }}>
            <div><strong>{name}</strong><span>{desc} - <span style={{ fontFamily: 'var(--font-mono)' }}>{meta}</span></span></div>
            <button className={`btn btn-sm ${status === 'Connected' ? '' : 'btn-accent'}`} type="button">{status === 'Connected' ? 'Manage' : 'Connect'}</button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderEngine = () => (
    <>
      <div className="card">
        <div className="card-header"><h3><Icon name="settings" /> Pipeline configuration</h3></div>
        <div className="card-body">
          <div className="settings-grid">
            <label className="field"><span>Default model</span><input className="input" defaultValue="gpt-4o-2024-11-20" /></label>
            <label className="field"><span>Embedding model</span><input className="input" defaultValue="text-embedding-3-large" /></label>
            <label className="field"><span>Crawl depth</span><input className="input" defaultValue="50 routes" /></label>
            <label className="field"><span>SEMrush units cap / audit</span><input className="input" defaultValue="2,500" /></label>
            <label className="field"><span>Concurrent audits</span><input className="input" defaultValue="3" /></label>
            <label className="field"><span>Retry policy</span><input className="input" defaultValue="3 attempts - 1.4s backoff" /></label>
          </div>
        </div>
      </div>
      <div className="card">
        <div className="card-header"><h3><Icon name="package" /> Deliverables</h3></div>
        <div className="card-body list-card-body">
          {[
            ['docx', 'Generate DOCX report'],
            ['xlsx', 'Generate XLSX keyword matrix'],
            ['pptx', 'Generate PPTX investor deck'],
            ['pdf', 'Generate PDF executive brief'],
            ['faiss', 'Persist FAISS index'],
          ].map(([key, label]) => (
            <div key={key} className="setting-row">
              <div><strong>{label}</strong><span>Included in the current engine configuration.</span></div>
              {renderSettingsToggle(deliverables[key], () => toggleDeliverable(key))}
            </div>
          ))}
        </div>
      </div>
    </>
  );

  const renderBilling = () => (
    <div className="card">
      <div className="card-header">
        <h3><Icon name="archive" /> Plan - Scale</h3>
        <span className="inline-pill accent">$1,200 / mo</span>
      </div>
      <div className="card-body">
        <div className="grid-3" style={{ marginBottom: 18 }}>
          <div className="kpi sample-stat-card">
            <div className="kpi-label">AUDITS USED</div>
            <div className="kpi-value">128 <span className="unit">/ 500</span></div>
            <div className="kpi-meter"><span style={{ width: '26%' }} /></div>
          </div>
          <div className="kpi sample-stat-card">
            <div className="kpi-label">SEMRUSH UNITS</div>
            <div className="kpi-value">412k <span className="unit">/ 1M</span></div>
            <div className="kpi-meter"><span style={{ width: '41%' }} /></div>
          </div>
          <div className="kpi sample-stat-card">
            <div className="kpi-label">SEATS</div>
            <div className="kpi-value">8 <span className="unit">/ 15</span></div>
            <div className="kpi-meter"><span style={{ width: '53%' }} /></div>
          </div>
        </div>
        <table className="tbl">
          <thead><tr><th>Invoice</th><th>Date</th><th>Amount</th><th>Status</th><th /></tr></thead>
          <tbody>
            {[
              ['INV-0042', 'Mar 1, 2026', '$1,200.00', 'paid'],
              ['INV-0041', 'Feb 1, 2026', '$1,200.00', 'paid'],
              ['INV-0040', 'Jan 1, 2026', '$1,200.00', 'paid'],
              ['INV-0039', 'Dec 1, 2025', '$1,200.00', 'paid'],
            ].map(([id, date, amount, status]) => (
              <tr key={id}>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{id}</td>
                <td>{date}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{amount}</td>
                <td><span className="inline-pill success">{status}</span></td>
                <td><button className="btn btn-ghost btn-sm" type="button"><Icon name="download" size={12} /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderSecurity = () => (
    <div className="card">
      <div className="card-header"><h3><Icon name="shield" /> Security</h3></div>
      <div className="card-body list-card-body">
        {[
          ['twoFactor', 'Two-factor authentication', 'Authenticator app required'],
          ['sso', 'SSO via Okta', 'Auto-provision via SCIM'],
          ['ipAllowlist', 'IP allowlist', '2 ranges configured'],
          ['sessionTimeout', 'Session timeout - 8h', 'Automatic sign-out after idle'],
          ['auditRetention', 'Audit log retention', '90 days, then archived'],
        ].map(([key, title, desc]) => (
          <div key={key} className="setting-row">
            <div><strong>{title}</strong><span>{desc}</span></div>
            {renderSettingsToggle(security[key], () => toggleSecurity(key))}
          </div>
        ))}
        <div style={{ marginTop: 8 }}>
          <strong style={{ fontSize: 12 }}>Active sessions</strong>
          <div className="list-card-body" style={{ marginTop: 8 }}>
            {[
              ['MacBook Pro - Chrome', 'Sydney, AU - now'],
              ['iPhone 15 - Safari', 'Sydney, AU - 2h ago'],
            ].map(([device, meta]) => (
              <div key={device} className="competitor-row" style={{ gridTemplateColumns: 'minmax(0,1fr) auto' }}>
                <div className="name"><strong>{device}</strong><span>{meta}</span></div>
                <button className="btn btn-ghost btn-sm" type="button" style={{ color: 'var(--danger)' }}>Revoke</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="page fade-in">
      <div className="page-head">
        <div>
          <h1>Settings</h1>
          <div className="sub">Manage your account, workspace, integrations, and engine configuration.</div>
        </div>
      </div>
      <div className="settings-shell">
        <div className="settings-nav card">
          <div className="card-body settings-nav-body">
            {tabs.map(([key, label]) => (
              <button key={key} className={`settings-nav-item ${tab === key ? 'active' : ''}`} type="button" onClick={() => setTab(key)}>
                <Icon name={key === 'account' ? 'user' : key === 'workspace' ? 'grid' : key === 'integrations' ? 'refresh' : key === 'engine' ? 'settings' : key === 'billing' ? 'archive' : 'shield'} size={13} />
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="settings-main">
          {tab === 'account' ? renderAccount() : null}
          {tab === 'workspace' ? renderWorkspace() : null}
          {tab === 'integrations' ? renderIntegrations() : null}
          {tab === 'engine' ? renderEngine() : null}
          {tab === 'billing' ? renderBilling() : null}
          {tab === 'security' ? renderSecurity() : null}
        </div>
      </div>
    </div>
  );
};

const PlaceholderPage = ({ title, description }) => (
  <div className="page fade-in">
    <div className="page-empty">
      <Icon name="sparkles" size={18} />
      <strong>{title}</strong>
      <span>{description}</span>
    </div>
  </div>
);

const App = () => {
  const [theme, setThemeState] = useState(() => localStorage.getItem(STORAGE_KEYS.theme) || 'light');
  const [session, setSession] = useState(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEYS.session);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [route, setRoute] = useState('dashboard');
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [currentRun, setCurrentRun] = useState(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [archiveQuery, setArchiveQuery] = useState('');
  const [archiveSearchFocusNonce, setArchiveSearchFocusNonce] = useState(0);

  const setTheme = (nextTheme) => {
    setThemeState(nextTheme);
    localStorage.setItem(STORAGE_KEYS.theme, nextTheme);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.dataset.theme = theme;
  }, [theme]);

  const openArchiveSearch = () => {
    setRoute('archives');
    setArchiveSearchFocusNonce((value) => value + 1);
  };

  useEffect(() => {
    const handleKeydown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        openArchiveSearch();
      }
    };

    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, []);

  const refreshHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await fetchJson('/api/history');
      setHistory(data.history || []);
      setHistoryError('');
    } catch (error) {
      setHistoryError(error.message);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (session) refreshHistory();
  }, [session, refreshHistory]);

  const handleSignIn = (payload) => {
    setSession(payload);
    sessionStorage.setItem(STORAGE_KEYS.session, JSON.stringify(payload));
    setRoute('dashboard');
  };

  const handleSignOut = () => {
    sessionStorage.removeItem(STORAGE_KEYS.session);
    setSession(null);
    setCurrentRun(null);
    setRoute('dashboard');
  };

  const launchAudit = async ({ domain, company, competitors }) => {
    setIsLaunching(true);
    try {
      const formData = new FormData();
      formData.append('domain', domain);
      formData.append('company', company);
      formData.append('competitors', JSON.stringify(competitors || []));
      (competitors || []).forEach((competitor, index) => formData.append(`competitor_${index + 1}`, competitor));

      const data = await fetchJson('/api/start-audit', {
        method: 'POST',
        body: formData,
      });

      setCurrentRun({
        jobId: data.job_id,
        domain,
        company,
        competitors: competitors || [],
        status: 'running',
        message: 'Starting audit pipeline...',
      });
      setRoute('live');
    } catch (error) {
      window.alert(`Unable to start audit: ${error.message}`);
    } finally {
      setIsLaunching(false);
    }
  };

  let body = null;
  if (!session) {
    body = <Login onSignIn={handleSignIn} theme={theme} setTheme={setTheme} />;
  } else {
    if (route === 'dashboard') body = <Dashboard history={history} currentRun={currentRun} setRoute={setRoute} />;
    else if (route === 'new') body = <NewAudit onLaunch={launchAudit} isLaunching={isLaunching} existingAudit={currentRun} />;
    else if (route === 'live') body = <LiveAudit currentRun={currentRun} onRefreshHistory={refreshHistory} onRunUpdate={setCurrentRun} />;
    else if (route === 'archives') body = <Archives history={history} query={archiveQuery} setQuery={setArchiveQuery} focusNonce={archiveSearchFocusNonce} />;
    else if (route === 'competitors') body = <CompetitorsPage />;
    else if (route === 'keywords') body = <KeywordBankPage />;
    else if (route === 'engines') body = <AIEnginesPage />;
    else if (route === 'agents') body = <AgentsPage />;
    else if (route === 'rag') body = <RagIndexPage />;
    else if (route === 'runlogs') body = <RunLogsPage currentRun={currentRun} history={history} />;
    else if (route === 'settings') body = <SettingsPage session={session} />;
    else body = <Dashboard history={history} currentRun={currentRun} setRoute={setRoute} />;
  }

  if (!session) return body;

  return (
    <div className="app">
      <Sidebar route={route} setRoute={setRoute} theme={theme} user={session} currentRun={currentRun} onOpenSearch={openArchiveSearch} />
      <Topbar route={route} theme={theme} setTheme={setTheme} setRoute={setRoute} currentRun={currentRun} signOut={handleSignOut} />
      <main className="main">
        {historyError ? (
          <div className="helper-line" style={{ color: 'var(--danger)', marginBottom: 16 }}>
            {escapeHtml(historyError)}
          </div>
        ) : null}
        {historyLoading && route !== 'live' ? (
          <div className="helper-line" style={{ marginBottom: 16 }}>Refreshing archive history...</div>
        ) : null}
        {body}
      </main>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);





