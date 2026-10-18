// 作品のページ（/fm7/<作品>/）に埋め込んだ設定（<script id="work">）を読み、そのページの隣の disk.d77 を
// WebM7 と互換 ROM で起動するだけのプレイヤー。ほかのディスクは読まない。
import { FM7Browser } from './webm7/core/fm7_browser.js';

const ROMDIR = new URL('webm7/assets/altroms/', import.meta.url);

// 互換 ROM の組み合わせ（ref/WebM7/index.html の builtinRomEntries と同じ。AV40 と AV だけ）
function romEntries(machine) {
    return [
        ['7tbasic3.rom', (fm7, d) => fm7.loadFBasicROM(d)],
        ['boot_bas.rom', (fm7, d) => fm7.loadBootBasROM(d)],
        ['boot_dos.rom', (fm7, d) => fm7.loadBootROM(d)],
        ['subsys_c.rom', (fm7, d) => fm7.loadSubROM(d)],
        [machine === 'fm77av' ? 'initav1.rom' : 'initiate.rom', (fm7, d) => fm7.loadInitiateROM(d)],
        ['subsys_a.rom', (fm7, d) => fm7.loadSubROM_A(d)],
        ['subsys_b.rom', (fm7, d) => fm7.loadSubROM_B(d)],
        ['subsyscg.rom', (fm7, d) => fm7.loadCGROM(d)],
        ['kanji.rom',    (fm7, d) => fm7.loadKanjiROM(d)],
    ];
}

const canvas = document.getElementById('screen');
const startBtn = document.getElementById('start');
const message = document.getElementById('message');

async function fetchOk(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
    return res.arrayBuffer();
}

// 押す・離すを、キーボードのイベントと同じ形でコアに渡す
function fakeKey(code, key) {
    return { code, key, shiftKey: false, ctrlKey: false, altKey: false, metaKey: false,
             repeat: false, preventDefault() {} };
}

function bindTouch(fm7, btn) {
    const ev = fakeKey(btn.dataset.code, btn.dataset.key);
    const down = (e) => {
        e.preventDefault();
        btn.setPointerCapture?.(e.pointerId);
        btn.classList.add('on');
        fm7.keyboard.keyDown(ev);
    };
    const up = (e) => {
        e.preventDefault();
        if (!btn.classList.contains('on')) return;
        btn.classList.remove('on');
        fm7.keyboard.keyUp(ev);
    };
    btn.addEventListener('pointerdown', down);
    btn.addEventListener('pointerup', up);
    btn.addEventListener('pointercancel', up);
    btn.addEventListener('lostpointercapture', up);
    btn.addEventListener('contextmenu', (e) => e.preventDefault());
}

function setupTouch(fm7, touch) {
    // 指で触れる端末だけ（ヘッドレスの Chrome の端末模擬は pointer: coarse にならないので maxTouchPoints も見る）
    if (!touch || !(matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0)) return;
    const box = document.getElementById('touch');
    document.getElementById('dpad').hidden = !touch.dpad;
    const buttons = document.getElementById('buttons');
    for (const b of touch.buttons || []) {
        const el = document.createElement('button');
        el.type = 'button';
        el.textContent = b.label;
        el.dataset.code = b.code;
        el.dataset.key = b.key || b.label;
        buttons.append(el);
    }
    for (const el of box.querySelectorAll('button')) bindTouch(fm7, el);
    box.hidden = false;
}

// ドライブのランプ。コアはディスクの命令を受けるたびに fdc.accessLatch を立てるので、毎フレーム読んで消し、
// そのとき選ばれているドライブのランプを少しの間点ける（WebM7 の index.html と同じ読み方）
const LAMP_HOLD_MS = 60;

function watchDrives(fm7) {
    const lamps = [...document.querySelectorAll('.lamp[data-drive]')];
    const until = [0, 0, 0, 0];
    const tick = (now) => {
        const fdc = fm7.fdc;
        if (fdc.accessLatch) {
            fdc.accessLatch = false;
            until[fdc.currentDrive & 3] = now + LAMP_HOLD_MS;
        }
        for (const l of lamps) l.classList.toggle('lit', now < until[l.dataset.drive]);
        requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
}

async function main() {
    const game = JSON.parse(document.getElementById('work').textContent);
    const machine = game.machine === 'fm77av' ? 'fm77av' : 'fm77av40';

    const entries = romEntries(machine);
    const [disk, ...roms] = await Promise.all([
        fetchOk('disk.d77'),
        ...entries.map(([file]) => fetchOk(new URL(file, ROMDIR))),
    ]);

    const fm7 = new FM7Browser();
    entries.forEach(([, load], i) => load(fm7, new Uint8Array(roms[i])));
    fm7.setMachineType(machine);
    if (!fm7.loadDisk(0, disk)) throw new Error('ディスクを読み込めません');
    // FM77AV はディスクがあると DOS モードを選ぶので、起動モードを決めておく（tools/webm7run.mjs と同じ）
    fm7._bootModeOverride = game.boot === 'dos' ? 'dos' : 'basic';
    fm7._bootModeExplicit = true;
    setupTouch(fm7, game.touch);

    // 音はユーザーの操作の中でしか始められないので、押されてから電源を入れる
    // クリックと Enter・スペースの両方から呼ばれるので、2 回目は何もしない
    let powered = false;
    const power = () => {
        if (powered) return;
        powered = true;
        startBtn.hidden = true;
        document.body.classList.add('powered');
        fm7.reset();
        fm7.start(canvas);
        watchDrives(fm7);
        startBtn.blur();
    };
    message.textContent = '';
    if (new URLSearchParams(location.search).has('autostart')) {
        power();  // 確かめる用（音は出ない）
    } else {
        startBtn.hidden = false;
        startBtn.addEventListener('click', power, { once: true });
        // フォーカスは当てずに（枠が出るので）、Enter・スペースでも起動できるようにする
        const onKey = (e) => {
            if (!['Enter', 'NumpadEnter', 'Space'].includes(e.code) || startBtn.hidden) return;
            e.preventDefault();
            document.removeEventListener('keydown', onKey);
            startBtn.click();
        };
        document.addEventListener('keydown', onKey);
    }
    window.fm7 = fm7;
    if (new URLSearchParams(location.search).has('debug')) showDebug(fm7);
}

// &debug: 届いたキーと、コアのキーボードの状態を出す（キーが効かないときに調べる用）
function showDebug(fm7) {
    const box = document.createElement('pre');
    box.style.cssText = 'position:fixed;left:8px;top:8px;margin:0;padding:8px;z-index:9;'
        + 'background:rgba(0,0,0,.8);color:#0f0;font:12px/1.4 monospace;pointer-events:none';
    document.body.append(box);
    let downs = 0, last = '-';
    const log = (e) => {
        if (e.type === 'keydown') downs++;
        last = `${e.type} code=${e.code} key=${e.key} keyCode=${e.keyCode} composing=${e.isComposing}`
             + ` target=${e.target.tagName}${e.target.id ? '#' + e.target.id : ''}`;
    };
    // コアより先に見る（capture）。コアが受け取ったかは pushes で見る
    document.addEventListener('keydown', log, true);
    document.addEventListener('keyup', log, true);
    const kb = fm7.keyboard;
    let pushes = 0;
    const orig = kb._pushKey.bind(kb);
    kb._pushKey = (c) => { pushes++; return orig(c); };
    setInterval(() => {
        const a = document.activeElement;
        box.textContent = [
            `running=${fm7._running} fps=${fm7._currentFPS} hasFocus=${document.hasFocus()}`
                + ` active=${a ? a.tagName + (a.id ? '#' + a.id : '') : '-'}`,
            `keydown=${downs} pushes=${pushes} scan=${kb._useScanCodes} irqMask=${kb._irqMask}`
                + ` buf=${kb._buffer.length} avail=${kb._keyAvailable}`
                + ` held=${[...kb._heldKeys].join(',')}`,
            `last: ${last}`,
        ].join('\n');
    }, 100);
}

main().catch((e) => {
    console.error(e);
    message.textContent = e.message;
});
