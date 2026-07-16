const API_BASE = window.location.origin + '/api';

let appState = {
    currentTab: 'chat',
    routePrefs: {
        duration: 4,
        with_kids: false,
        with_elderly: false,
        avoid_slopes: false,
        animal_preference: '',
        start_entrance: 'south'
    },
    mapData: null,
    animals: {},
    venues: {},
    facilities: {},
    currentFilter: 'all',
    isRecording: false,
    recognition: null,
    synth: window.speechSynthesis,
    selectedAnimal: null
};

document.addEventListener('DOMContentLoaded', initApp);

async function initApp() {
    bindEvents();
    initTabs();
    initVoice();
    await Promise.all([loadMapData(), loadAnimals()]);
    renderMap();
    renderAnimals();
    loadWelcome();
}

function bindEvents() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceClose = document.getElementById('voiceClose');
    const planBtn = document.getElementById('planRouteBtn');
    const infoBtn = document.getElementById('infoBtn');
    const closeInfo = document.getElementById('closeInfoModal');
    const closeAnimalModal = document.getElementById('closeAnimalModal');
    const askAnimalBtn = document.getElementById('askAboutAnimal');
    const closeVenueCard = document.getElementById('closeVenueCard');
    const guideVenueBtn = document.getElementById('guideToVenue');

    chatInput.addEventListener('input', e => {
        sendBtn.classList.toggle('active', e.target.value.trim().length > 0);
    });

    chatInput.addEventListener('keypress', e => {
        if (e.key === 'Enter' && e.target.value.trim()) {
            sendMessage(e.target.value);
        }
    });

    sendBtn.addEventListener('click', () => {
        if (chatInput.value.trim()) sendMessage(chatInput.value);
    });

    voiceBtn.addEventListener('click', toggleVoice);
    voiceClose.addEventListener('click', stopVoice);

    document.querySelectorAll('.option-btn[data-duration]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.option-btn[data-duration]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            appState.routePrefs.duration = parseInt(btn.dataset.duration);
        });
    });

    ['with_kids', 'with_elderly', 'avoid_slopes'].forEach(flag => {
        const btn = document.querySelector(`.option-btn[data-flag="${flag}"]`);
        if (btn) {
            btn.addEventListener('click', () => {
                btn.classList.toggle('active');
                appState.routePrefs[flag] = btn.classList.contains('active');
            });
        }
    });

    document.querySelectorAll('.option-btn[data-pref]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.option-btn[data-pref]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            appState.routePrefs.animal_preference = btn.dataset.pref;
        });
    });

    document.querySelectorAll('.option-btn[data-entrance]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.option-btn[data-entrance]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            appState.routePrefs.start_entrance = btn.dataset.entrance;
        });
    });

    planBtn.addEventListener('click', generateRoute);

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            appState.currentFilter = btn.dataset.filter;
            renderAnimals();
        });
    });

    document.querySelectorAll('.facility-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            if (type === 'all') {
                document.querySelectorAll('.facility-toggle').forEach(b => b.classList.add('active'));
            } else {
                document.querySelector('.facility-toggle[data-type="all"]').classList.remove('active');
                btn.classList.toggle('active');
            }
            renderMap();
        });
    });

    infoBtn.addEventListener('click', () => document.getElementById('infoModal').classList.add('show'));
    closeInfo.addEventListener('click', () => document.getElementById('infoModal').classList.remove('show'));
    document.getElementById('infoModal').addEventListener('click', e => {
        if (e.target.id === 'infoModal') document.getElementById('infoModal').classList.remove('show');
    });

    closeAnimalModal.addEventListener('click', () => document.getElementById('animalModal').classList.remove('show'));
    document.getElementById('animalModal').addEventListener('click', e => {
        if (e.target.id === 'animalModal') document.getElementById('animalModal').classList.remove('show');
    });

    askAnimalBtn.addEventListener('click', () => {
        if (appState.selectedAnimal) {
            document.getElementById('animalModal').classList.remove('show');
            switchTab('chat');
            const animal = appState.animals[appState.selectedAnimal];
            sendMessage(`给我讲讲${animal.name}`);
        }
    });

    closeVenueCard.addEventListener('click', () => document.getElementById('venueCard').classList.remove('show'));
    guideVenueBtn.addEventListener('click', () => {
        const title = document.getElementById('venueCardTitle').textContent;
        document.getElementById('venueCard').classList.remove('show');
        switchTab('chat');
        sendMessage(`给我讲讲${title}`);
    });
}

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
}

function switchTab(tabId) {
    appState.currentTab = tabId;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === `tab-${tabId}`));
}

async function loadMapData() {
    try {
        const res = await fetch(`${API_BASE}/map`);
        appState.mapData = await res.json();
        appState.venues = appState.mapData.venues || {};
        appState.facilities = appState.mapData.facilities || {};
    } catch (e) {
        console.error('Failed to load map:', e);
    }
}

async function loadAnimals() {
    try {
        const res = await fetch(`${API_BASE}/animals`);
        const data = await res.json();
        appState.animals = data.animals || {};
    } catch (e) {
        console.error('Failed to load animals:', e);
    }
}

async function loadWelcome() {
    try {
        const res = await fetch(`${API_BASE}/welcome`);
        const data = await res.json();
        document.getElementById('welcomeBubble').innerHTML = formatText(data.message);
        renderQuickQuestions(data.quick_questions || [], true);
    } catch (e) {
        document.getElementById('welcomeBubble').textContent = '你好！我是红山陪逛小助手，有什么可以帮你的吗？';
    }
}

function renderQuickQuestions(questions, isWelcome) {
    const container = document.getElementById('quickQuestions');
    if (isWelcome) container.innerHTML = '';
    questions.forEach(q => {
        const btn = document.createElement('button');
        btn.className = 'quick-q' + (isWelcome ? '' : ' normal-quick-q');
        btn.textContent = q;
        btn.onclick = () => sendMessage(q);
        container.appendChild(btn);
    });
}

async function sendMessage(text) {
    const input = document.getElementById('chatInput');
    input.value = '';
    document.getElementById('sendBtn').classList.remove('active');

    addUserMessage(text);
    showTyping();

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        hideTyping();
        addBotMessage(data.response);

        if (data.route_data) showRouteCard(data.route_data);
        if (data.animal_data) showAnimalCard(data.animal_data);
        if (data.quick_questions) renderQuickQuestions(data.quick_questions, false);

        if (data.speak !== false) speak(data.response);
    } catch (e) {
        hideTyping();
        addBotMessage('抱歉，网络有点问题，请稍后再试。');
    }

    scrollChat();
}

function addUserMessage(text) {
    const container = document.getElementById('chatContainer');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user';
    msgDiv.innerHTML = `
        <div class="avatar">👤</div>
        <div class="msg-content"><div class="msg-bubble">${escapeHtml(text)}</div></div>
    `;
    container.appendChild(msgDiv);
    scrollChat();
}

function addBotMessage(text) {
    const container = document.getElementById('chatContainer');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';
    msgDiv.innerHTML = `
        <div class="avatar">🐾</div>
        <div class="msg-content"><div class="msg-bubble">${formatText(text)}</div></div>
    `;
    container.appendChild(msgDiv);
    scrollChat();
}

function showTyping() {
    const container = document.getElementById('chatContainer');
    const typing = document.createElement('div');
    typing.className = 'message assistant';
    typing.id = 'typingMsg';
    typing.innerHTML = `
        <div class="avatar">🐾</div>
        <div class="msg-content"><div class="msg-bubble typing-bubble"><span></span><span></span><span></span></div></div>
    `;
    container.appendChild(typing);
    scrollChat();
}

function hideTyping() {
    const t = document.getElementById('typingMsg');
    if (t) t.remove();
}

function showRouteCard(route) {
    const container = document.getElementById('chatContainer');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';

    let stopsHtml = '';
    const stopsToShow = route.stops.filter(s => s.id !== 'start' && s.id !== 'end').slice(0, 6);
    stopsToShow.forEach((s, i) => {
        stopsHtml += `<div class="route-mini-stop"><span class="route-mini-dot"></span>${s.emoji} ${s.name}</div>`;
    });

    msgDiv.innerHTML = `
        <div class="avatar">🐾</div>
        <div class="msg-content">
            <div class="route-card-inline">
                <div class="route-header-inline">
                    <strong>🗺️ ${route.name}</strong>
                    <div style="font-size:12px;opacity:0.9;margin-top:4px;">
                        共${route.total_duration}分钟 · ${route.walking_distance}米 · ${route.stops.length}个景点
                    </div>
                </div>
                <div class="route-stops-inline">${stopsHtml}</div>
            </div>
        </div>
    `;
    container.appendChild(msgDiv);
    scrollChat();
}

function showAnimalCard(animal) {
    const container = document.getElementById('chatContainer');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';

    let feedHtml = '';
    if (animal.feeding_times && animal.feeding_times.length) {
        feedHtml = '<div class="feeding-times-inline">';
        animal.feeding_times.forEach(t => feedHtml += `<span class="feeding-time-inline">🍎 ${t}</span>`);
        feedHtml += '</div>';
    }

    msgDiv.innerHTML = `
        <div class="avatar">🐾</div>
        <div class="msg-content">
            <div class="animal-card-inline">
                <div class="animal-inline-header">
                    <span class="animal-inline-emoji">${animal.emoji}</span>
                    <div>
                        <div class="animal-inline-name">${animal.name}</div>
                        <div class="animal-inline-venue">📍 ${animal.venue_name}${animal.names ? ' · ' + animal.names.slice(0,3).join('/') : ''}</div>
                    </div>
                </div>
                ${animal.story ? `<div class="animal-inline-story">${animal.story.substring(0, 120)}...</div>` : ''}
                ${feedHtml}
            </div>
        </div>
    `;
    container.appendChild(msgDiv);
    scrollChat();
}

function formatText(text) {
    return escapeHtml(text)
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

function scrollChat() {
    const c = document.getElementById('chatContainer');
    c.scrollTop = c.scrollHeight;
}

function initVoice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) {
        appState.recognition = new SR();
        appState.recognition.continuous = false;
        appState.recognition.interimResults = false;
        appState.recognition.lang = 'zh-CN';
        appState.recognition.onresult = e => {
            const text = e.results[0][0].transcript;
            document.getElementById('chatInput').value = text;
            document.getElementById('sendBtn').classList.add('active');
            stopVoice();
            sendMessage(text);
        };
        appState.recognition.onend = () => stopVoice();
        appState.recognition.onerror = () => stopVoice();
    }
}

function toggleVoice() {
    if (!appState.recognition) {
        alert('您的浏览器不支持语音识别，请使用Chrome浏览器。');
        return;
    }
    if (appState.isRecording) stopVoice();
    else startVoice();
}

function startVoice() {
    appState.isRecording = true;
    document.getElementById('voiceBtn').classList.add('recording');
    document.getElementById('voiceOverlay').classList.add('show');
    document.getElementById('voiceTip').textContent = '正在听你说话...';
    try { appState.recognition.start(); } catch(e) {}
}

function stopVoice() {
    appState.isRecording = false;
    document.getElementById('voiceBtn').classList.remove('recording');
    document.getElementById('voiceOverlay').classList.remove('show');
    if (appState.recognition) {
        try { appState.recognition.stop(); } catch(e) {}
    }
}

function speak(text) {
    if (!appState.synth) return;
    appState.synth.cancel();
    const clean = text.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|#|\*/gu, '');
    if (clean.trim().length < 5) return;
    const u = new SpeechSynthesisUtterance(clean);
    u.lang = 'zh-CN';
    u.rate = 1;
    appState.synth.speak(u);
}

function renderMap() {
    const svg = document.getElementById('zooMap');
    if (!svg || !appState.mapData) return;

    const g = document.getElementById('mapElements');
    g.innerHTML = '';

    const venues = appState.venues;
    const facilities = appState.facilities;

    Object.entries(venues).forEach(([vid, v]) => {
        const color = v.tier === 'T0' ? '#FF9800' : v.tier === 'T1' ? '#4CAF50' : '#2196F3';
        const gEl = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        gEl.setAttribute('class', 'venue-marker');
        gEl.innerHTML = `
            <circle cx="${v.x}" cy="${v.y}" r="16" fill="${color}" opacity="0.9" filter="url(#shadow)"/>
            <text x="${v.x}" y="${v.y + 5}" text-anchor="middle" font-size="16">${v.emoji}</text>
            <text x="${v.x}" y="${v.y + 28}" text-anchor="middle" font-size="9" fill="#333" font-weight="500">${v.name.length > 6 ? v.name.substring(0,6) : v.name}</text>
        `;
        gEl.onclick = () => showVenueCard(vid);
        g.appendChild(gEl);
    });

    const activeTypes = Array.from(document.querySelectorAll('.facility-toggle.active')).map(b => b.dataset.type);
    const showAll = activeTypes.includes('all');

    Object.entries(facilities).forEach(([ftype, flist]) => {
        if (!showAll && !activeTypes.includes(ftype)) return;
        if (ftype === 'entrance') return;
        flist.forEach(f => {
            const gEl = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            gEl.setAttribute('class', 'facility-marker');
            gEl.innerHTML = `
                <rect x="${f.x - 10}" y="${f.y - 10}" width="20" height="20" rx="4" fill="#9E9E9E" opacity="0.8"/>
                <text x="${f.x}" y="${f.y + 4}" text-anchor="middle" font-size="11">${f.emoji}</text>
            `;
            gEl.onclick = () => showFacilityCard(f);
            g.appendChild(gEl);
        });
    });

    const entrances = facilities.entrance || [];
    entrances.forEach(e => {
        const gEl = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        gEl.innerHTML = `
            <rect x="${e.x - 22}" y="${e.y - 12}" width="44" height="24" rx="12" fill="#E91E63"/>
            <text x="${e.x}" y="${e.y + 4}" text-anchor="middle" font-size="10" fill="white" font-weight="600">${e.name.replace('（', '').substring(0,5)}</text>
        `;
        g.appendChild(gEl);
    });
}

function showVenueCard(vid) {
    const v = appState.venues[vid];
    if (!v) return;
    document.getElementById('venueCardTitle').innerHTML = `${v.emoji} ${v.name}`;
    const animalsHere = Object.values(appState.animals).filter(a => a.venue_id === vid || a.venue === vid);
    let desc = v.description || '';
    if (animalsHere.length) {
        desc += `<br><br><strong>明星动物：</strong>${animalsHere.map(a => a.emoji + a.name).join('、')}`;
    }
    if (v.tips) desc += `<br><br>💡 ${v.tips}`;
    document.getElementById('venueCardDesc').innerHTML = desc;
    document.getElementById('venueCard').classList.add('show');
}

function showFacilityCard(f) {
    document.getElementById('venueCardTitle').innerHTML = `${f.emoji} ${f.name}`;
    document.getElementById('venueCardDesc').textContent = f.note || `${f.type === 'restroom' ? '公共卫生间' : f.type === 'restaurant' ? '餐饮点' : f.type === 'rest_area' ? '休息区' : '直饮水点'}`;
    document.getElementById('venueCard').classList.add('show');
}

async function generateRoute() {
    const btn = document.getElementById('planRouteBtn');
    btn.disabled = true;
    btn.textContent = '规划中...';

    try {
        const res = await fetch(`${API_BASE}/route/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(appState.routePrefs)
        });
        const route = await res.json();
        displayRouteResult(route);
    } catch (e) {
        alert('规划失败，请重试');
    }

    btn.disabled = false;
    btn.textContent = '✨ 生成我的专属路线';
}

function displayRouteResult(route) {
    const result = document.getElementById('routeResult');
    result.style.display = 'block';

    const textDiv = document.getElementById('routeText');
    textDiv.innerHTML = '';

    const stops = route.stops.filter(s => s.id !== 'start' && s.id !== 'end');
    stops.forEach((s, i) => {
        const div = document.createElement('div');
        div.className = 'route-stop';
        div.innerHTML = `
            <span class="route-stop-num">${i + 1}</span>
            <div class="route-stop-content">
                <div class="route-stop-name">${s.emoji} ${s.name}</div>
                ${s.reason ? `<div class="route-stop-tip">💡 ${s.reason}</div>` : ''}
                <div class="route-stop-tip">⏱️ 建议游览${s.suggested_duration}分钟</div>
            </div>
        `;
        textDiv.appendChild(div);
    });

    const stats = document.getElementById('routeStats');
    stats.innerHTML = `
        <div class="stat-item">
            <div class="stat-value">${Math.round(route.total_duration / 60 * 10) / 10}h</div>
            <div class="stat-label">总时长</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${Math.round(route.walking_distance / 10) / 100}km</div>
            <div class="stat-label">步行距离</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${stops.length}</div>
            <div class="stat-label">景点数</div>
        </div>
    `;

    result.scrollIntoView({ behavior: 'smooth' });
}

function renderAnimals() {
    const grid = document.getElementById('animalsGrid');
    grid.innerHTML = '';

    const filter = appState.currentFilter;
    const animals = Object.entries(appState.animals).filter(([_, a]) => {
        if (filter === 'all') return true;
        return a.category === filter || (filter === 'star' && a.tier === 'T0');
    });

    const tierLabels = { T0: '⭐ 明星', T1: '🔥 人气', T2: '💫 特色' };

    animals.forEach(([key, a]) => {
        const card = document.createElement('div');
        card.className = 'animal-card';
        card.onclick = () => showAnimalDetail(key);
        card.innerHTML = `
            <div class="animal-card-img">${a.emoji}</div>
            <div class="animal-card-info">
                <div class="animal-card-name">${a.name}</div>
                <div class="animal-card-venue">${a.venue_name}</div>
                <span class="tier-badge tier-${a.tier}">${tierLabels[a.tier] || '特色'}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function showAnimalDetail(animalKey) {
    const a = appState.animals[animalKey];
    if (!a) return;
    appState.selectedAnimal = animalKey;

    document.getElementById('animalEmoji').textContent = a.emoji;
    document.getElementById('animalName').textContent = a.name;
    document.getElementById('animalNames').textContent = a.names && a.names.length ? a.names.slice(0,4).join(' / ') : '';

    const body = document.querySelector('.animal-detail-body');
    let feedText = a.feeding_times && a.feeding_times.length ? a.feeding_times.join('、') : '全天可观赏';

    body.innerHTML = `
        <div class="animal-info-row">
            <span class="info-label">📍 所在展区</span>
            <span>${a.venue_name}</span>
        </div>
        <div class="animal-info-row">
            <span class="info-label">⏰ 活跃时间</span>
            <span style="font-size:12px">${feedText}</span>
        </div>
        <div class="animal-info-row">
            <span class="info-label">⭐ 热度等级</span>
            <span>${a.tier}</span>
        </div>
        <div class="animal-story">
            <h4>它们的故事</h4>
            <p>${a.description || ''}</p>
            ${a.story ? `<p style="margin-top:8px">${a.story}</p>` : ''}
        </div>
    `;

    document.getElementById('animalModal').classList.add('show');
}
