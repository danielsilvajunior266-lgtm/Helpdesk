/**
 * AutoFlow VIP Audio & Real-Time Tracking Engine
 * Gerencia efeitos sonoros procedurais (Buzina Esportiva / VRUMMM Alta Velocidade)
 * e monitoramento em tempo real de status de ordens de serviço.
 */

class AutoFlowAudioEngine {
    constructor() {
        this.ctx = null;
        this.hasUnlocked = false;
        this._initListeners();
    }

    _initListeners() {
        const unlock = () => {
            if (!this.hasUnlocked) {
                this.getContext();
                this.hasUnlocked = true;
            }
        };
        window.addEventListener('click', unlock, { once: true });
        window.addEventListener('touchstart', unlock, { once: true });
        window.addEventListener('keydown', unlock, { once: true });
    }

    getContext() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.ctx = new AudioCtx();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
        return this.ctx;
    }

    /**
     * Toca buzina esportiva dupla (Fom-Fom!) de supercarro
     */
    playSportHorn() {
        try {
            // Tenta primeiro via Audio tag do asset estático
            const audioEl = new Audio('/static/audio/horn.wav?v=' + Date.now());
            audioEl.volume = 0.85;
            audioEl.play().catch(() => {
                // Fallback procedural sintetizado via Web Audio API
                this._synthesizeSportHorn();
            });
        } catch (_) {
            this._synthesizeSportHorn();
        }
    }

    _synthesizeSportHorn() {
        const ctx = this.getContext();
        if (!ctx) return;

        const now = ctx.currentTime;
        const freqs = [370, 466, 740, 932]; // Dual-tone esportivo italiano (F#4 + Bb4)

        const playBeep = (startTime, duration) => {
            const masterGain = ctx.createGain();
            masterGain.gain.setValueAtTime(0, startTime);
            masterGain.gain.linearRampToValueAtTime(0.25, startTime + 0.02);
            masterGain.gain.setValueAtTime(0.25, startTime + duration - 0.03);
            masterGain.gain.linearRampToValueAtTime(0, startTime + duration);
            masterGain.connect(ctx.destination);

            freqs.forEach((f, idx) => {
                const osc = ctx.createOscillator();
                osc.type = idx < 2 ? 'sawtooth' : 'sine';
                osc.frequency.setValueAtTime(f, startTime);

                const gain = ctx.createGain();
                gain.gain.setValueAtTime(idx < 2 ? 0.3 : 0.1, startTime);
                osc.connect(gain);
                gain.connect(masterGain);

                osc.start(startTime);
                osc.stop(startTime + duration);
            });
        };

        // Beep 1: Fom!
        playBeep(now, 0.14);
        // Beep 2: Fom!
        playBeep(now + 0.20, 0.22);
    }

    /**
     * Toca o som de carro esportivo passando em alta velocidade (VRUMMM! com Doppler sweep e turbo)
     */
    playSpeedEnginePass() {
        try {
            const audioEl = new Audio('/static/audio/vrumm.wav?v=' + Date.now());
            audioEl.volume = 0.95;
            audioEl.play().catch(() => {
                this._synthesizeSpeedPass();
            });
        } catch (_) {
            this._synthesizeSpeedPass();
        }
    }

    _synthesizeSpeedPass() {
        const ctx = this.getContext();
        if (!ctx) return;

        const now = ctx.currentTime;
        const duration = 1.4;
        const passTime = now + 0.55;

        // Master Gain com Envelope de Distância
        const masterGain = ctx.createGain();
        masterGain.gain.setValueAtTime(0.01, now);
        masterGain.gain.exponentialRampToValueAtTime(0.45, passTime);
        masterGain.gain.exponentialRampToValueAtTime(0.001, now + duration);
        masterGain.connect(ctx.destination);

        // Filtro Lowpass Dinâmico (simula o efeito do ar e escapamento)
        const filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(3500, now);
        filter.frequency.linearRampToValueAtTime(800, now + duration);
        filter.connect(masterGain);

        // Osciladores do Motor (V8 Flat-Plane Roar)
        [1, 1.5, 2, 3, 4].forEach((mult, idx) => {
            const osc = ctx.createOscillator();
            osc.type = 'sawtooth';

            // Curva Doppler de Frequência
            osc.frequency.setValueAtTime(520 * mult, now);
            osc.frequency.exponentialRampToValueAtTime(360 * mult, passTime);
            osc.frequency.exponentialRampToValueAtTime(130 * mult, now + duration);

            const oscGain = ctx.createGain();
            oscGain.gain.setValueAtTime(0.25 / (idx + 1), now);
            osc.connect(oscGain);
            oscGain.connect(filter);

            osc.start(now);
            osc.stop(now + duration);
        });

        // Ruído de ar do escapamento (White noise)
        const bufferSize = ctx.sampleRate * duration;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        const noise = ctx.createBufferSource();
        noise.buffer = buffer;
        const noiseFilter = ctx.createBiquadFilter();
        noiseFilter.type = 'bandpass';
        noiseFilter.frequency.setValueAtTime(1200, now);
        noiseFilter.frequency.exponentialRampToValueAtTime(400, now + duration);
        
        const noiseGain = ctx.createGain();
        noiseGain.gain.setValueAtTime(0.05, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.2, passTime);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, now + duration);

        noise.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(masterGain);

        noise.start(now);
        noise.stop(now + duration);
    }
}

// Instância global de Áudio
window.AutoFlowAudio = new AutoFlowAudioEngine();

/**
 * Gerenciador de Monitoramento em Tempo Real
 */
class AutoFlowLiveTrackerManager {
    constructor() {
        this.knownOrders = new Map(); // id -> status
        this.isPolling = false;
        this.timer = null;
        this.pollInterval = 3500; // 3.5s
    }

    start() {
        if (this.isPolling) return;
        this.isPolling = true;
        this.poll();
        this.timer = setInterval(() => this.poll(), this.pollInterval);
    }

    stop() {
        if (this.timer) clearInterval(this.timer);
        this.isPolling = false;
    }

    async poll() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const companyId = urlParams.get('company_id') || '';
            const fetchUrl = `/portal/live-status/${companyId ? `?company_id=${companyId}` : ''}`;

            const response = await fetch(fetchUrl, {
                headers: { 'Accept': 'application/json' },
                cache: 'no-store'
            });

            if (!response.ok) return;
            const data = await response.json();
            if (!data || !data.orders) return;

            this._processOrdersUpdate(data.orders);
        } catch (_) {}
    }

    _processOrdersUpdate(orders) {
        let hasChanges = false;

        orders.forEach(order => {
            const orderId = order.id;
            const currentStatus = order.status;
            const prevStatus = this.knownOrders.get(orderId);

            if (prevStatus !== undefined && prevStatus !== currentStatus) {
                hasChanges = true;
                this._handleStatusTransition(order, prevStatus, currentStatus);
            }

            this.knownOrders.set(orderId, currentStatus);
        });

        // Se houve alteração ou status inicial carregado, sincroniza cards
        if (hasChanges) {
            this._refreshOrdersDOM(orders);
        }
    }

    _handleStatusTransition(order, fromStatus, toStatus) {
        console.log(`[AutoFlow Live] Ordem #${order.id} mudou de ${fromStatus} para ${toStatus}`);

        if (toStatus === 'in_progress' || toStatus === 'washing') {
            // Notificação com buzina de carro esportivo
            window.AutoFlowAudio.playSportHorn();
            this.showNotification({
                title: '🏎️💨 Carro em Atendimento!',
                message: `O seu veículo ${order.vehicle_plate} (${order.vehicle_name}) entrou EM ATENDIMENTO na unidade ${order.company_name}!`,
                type: 'in_progress',
                soundBadge: 'Buzina Esportiva (Fom-Fom!)'
            });
        } else if (toStatus === 'completed') {
            // Notificação com barulho de carro em alta velocidade (VRUMMM!)
            window.AutoFlowAudio.playSpeedEnginePass();
            this.showNotification({
                title: '🏁✨ Pronto para Retirada!',
                message: `VRUMMM! O seu veículo ${order.vehicle_plate} (${order.vehicle_name}) está 100% PRONTO na unidade ${order.company_name}! Venha retirar.`,
                type: 'completed',
                soundBadge: 'Motor Supercar (VRUMMM!)'
            });
        } else if (toStatus === 'delivered') {
            this.showNotification({
                title: '🚗 Entregue com Sucesso!',
                message: `Veículo ${order.vehicle_plate} entregue. Obrigado pela preferência na Rede AutoFlow!`,
                type: 'delivered',
                soundBadge: 'Serviço Finalizado'
            });
        }
    }

    showNotification({ title, message, type, soundBadge }) {
        let container = document.getElementById('autoflow-live-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'autoflow-live-toast-container';
            container.className = 'fixed top-5 right-5 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none px-4';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `pointer-events-auto transform transition-all duration-300 ease-out translate-y-[-20px] opacity-0 p-4 rounded-3xl carbon-card border shadow-2xl backdrop-blur-xl ${
            type === 'completed' 
                ? 'border-emerald-500/50 bg-slate-900/95 shadow-emerald-500/20' 
                : 'border-[#1EA8D7]/50 bg-slate-900/95 shadow-[#1EA8D7]/20'
        }`;

        toast.innerHTML = `
            <div class="flex items-start space-x-3.5">
                <div class="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 ${
                    type === 'completed' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-[#1EA8D7]/20 text-[#38C5EE]'
                }">
                    <i data-lucide="${type === 'completed' ? 'sparkles' : 'spray-can'}" class="w-5 h-5"></i>
                </div>
                <div class="flex-1 space-y-1">
                    <div class="flex items-center justify-between">
                        <h4 class="font-extrabold text-sm text-white">${title}</h4>
                        <span class="text-[9px] font-extrabold uppercase px-2 py-0.5 rounded-full ${
                            type === 'completed' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-[#1EA8D7]/20 text-[#38C5EE]'
                        }">${soundBadge || 'VIP'}</span>
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">${message}</p>
                </div>
                <button onclick="this.closest('#autoflow-live-toast-container > div').remove()" class="text-slate-500 hover:text-white p-1">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
        `;

        container.appendChild(toast);
        if (window.lucide) window.lucide.createIcons();

        // Animação de entrada
        setTimeout(() => {
            toast.classList.remove('translate-y-[-20px]', 'opacity-0');
            toast.classList.add('translate-y-0', 'opacity-100');
        }, 30);

        // Auto dismiss após 8s
        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-y-[-20px]');
            setTimeout(() => toast.remove(), 400);
        }, 8000);
    }

    _refreshOrdersDOM(orders) {
        // Atualiza contadores e badges dinamicamente
        const activeCount = orders.filter(o => o.status !== 'delivered' && o.status !== 'cancelled').length;
        const patioBadge = document.querySelector('.gold-card .text-[#1EA8D7], .carbon-card .text-[#1EA8D7]');
        if (patioBadge && patioBadge.innerText !== undefined) {
            // se é o contador de No Pátio
            const parent = patioBadge.closest('.carbon-card, .gold-card');
            if (parent && parent.innerText.includes('No Pátio')) {
                patioBadge.innerText = activeCount;
            }
        }
    }
}

// Inicia monitoramento ao carregar o DOM
document.addEventListener('DOMContentLoaded', () => {
    window.AutoFlowLiveTracker = new AutoFlowLiveTrackerManager();
    window.AutoFlowLiveTracker.start();
});
