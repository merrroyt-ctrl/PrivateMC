const $=i=>document.getElementById(i);
let tt;
function toast(t,bad){const e=$('toast');e.textContent=t||'Fertig.';e.className=bad?'bad':'';e.hidden=false;clearTimeout(tt);tt=setTimeout(()=>e.hidden=true,6000)}
async function copy(t){try{await navigator.clipboard.writeText(t)}catch(e){const x=document.createElement('textarea');x.value=t;document.body.append(x);x.select();document.execCommand('copy');x.remove()}}
const gb=b=>(b/1073741824).toFixed(1).replace('.',',')+' GB';
const lvl=p=>p>=90?'bad':p>=70?'warn':'';
const ago=s=>{const m=Math.max(0,(Date.now()-new Date(s))/6e4|0),d=m/1440|0,h=(m%1440)/60|0;return d?d+' Tg '+h+' Std':h?h+' Std '+(m%60)+' Min':m+' Min'};
function spark(a){if(!a||a.length<2)return'';const n=a.length,p=a.map((v,i)=>(i/(n-1)*100).toFixed(1)+','+(29-Math.min(100,v)/100*27).toFixed(1)).join(' ');return'<svg viewBox="0 0 100 30" preserveAspectRatio="none"><polyline points="'+p+'" fill="none" stroke="currentColor" stroke-width="1.5" vector-effect="non-scaling-stroke"/></svg>'}
function res(s,run){
  const ok=run&&s.cpu!=null,cp=ok?Math.min(100,s.cpu):0,rp=ok&&s.ram_max?Math.min(100,s.ram/s.ram_max*100):0;
  $('cpu_t').textContent=ok?Math.round(cp)+' %':'–';
  $('cpu_b').style.width=cp+'%';$('cpu_b').className=lvl(cp);
  $('cpu_h').textContent=ok?'von allen '+s.cores+' Prozessorkernen':'Wird angezeigt, sobald der Server läuft.';
  $('ram_t').textContent=ok?gb(s.ram)+(s.ram_max?' von '+gb(s.ram_max):''):'–';
  $('ram_b').style.width=rp+'%';$('ram_b').className=lvl(rp);
  $('ram_h').textContent=ok?Math.round(rp)+' % des zugewiesenen Speichers belegt':'';
  $('cpu_s').innerHTML=ok?spark(s.hc):'';$('ram_s').innerHTML=ok?spark(s.hr):'';
}
function facts(s){
  const on=s.online;
  $('pl').textContent=on?s.players+' von '+s.max:'–';
  $('ver').textContent=on?s.version:'–';
  $('ping').textContent=on?s.ping+' ms':'–';
  $('up').textContent=on?ago(s.since):'–';
  const ul=$('names');ul.innerHTML='';
  const n=on?(s.names||[]):[];
  (n.length?n:[on?(s.players?s.players+' Spieler online':'Gerade ist niemand online.'):'Der Server ist gerade nicht erreichbar.']).forEach(x=>{const li=document.createElement('li');li.textContent=x;ul.append(li)});
}
$('cp')&&($('cp').onclick=async()=>{await copy($('addr').textContent);$('cp').textContent='Kopiert ✓';setTimeout(()=>$('cp').textContent='Adresse kopieren',2000)});

// ========================================
// PRIVATEMC CUSTOM DIALOGS
// ========================================

function customDialog({
    title = 'PrivateMC',
    message = '',
    icon = '✦',
    type = 'alert',
    placeholder = '',
    defaultValue = '',
    confirmText = 'Bestätigen',
    cancelText = 'Abbrechen',
    danger = false
} = {}) {
    return new Promise(resolve => {
        const overlay = $('dialog_overlay');
        const form = $('dialog_form');
        const input = $('dialog_input');
        const ok = $('dialog_ok');
        const cancel = $('dialog_cancel');

        $('dialog_title').textContent = title;
        $('dialog_message').textContent = message;
        $('dialog_icon').textContent = icon;

        input.hidden = type !== 'prompt';
        input.placeholder = placeholder;
        input.value = defaultValue;
        input.required = false;

        ok.textContent = confirmText;
        ok.className = danger ? 'danger' : 'ok';
        cancel.textContent = cancelText;
        cancel.hidden = type === 'alert';

        overlay.hidden = false;

        const finish = value => {
            overlay.hidden = true;
            form.removeEventListener('submit', submit);
            cancel.removeEventListener('click', cancelDialog);
            overlay.removeEventListener('click', outside);
            document.removeEventListener('keydown', escape);
            resolve(value);
        };

        const submit = event => {
            event.preventDefault();

            if (type === 'prompt') {
                finish(input.value);
            } else {
                finish(true);
            }
        };

        const cancelDialog = () => finish(
            type === 'prompt' ? null : false
        );

        const outside = event => {
            if (event.target === overlay) cancelDialog();
        };

        const escape = event => {
            if (event.key === 'Escape') cancelDialog();
        };

        form.addEventListener('submit', submit);
        cancel.addEventListener('click', cancelDialog);
        overlay.addEventListener('click', outside);
        document.addEventListener('keydown', escape);

        if (type === 'prompt') {
            input.focus();
            input.select();
        } else {
            ok.focus();
        }
    });
}

function uiAlert(message, title = 'Hinweis') {
    return customDialog({
        title,
        message,
        icon: 'ℹ',
        type: 'alert',
        confirmText: 'Alles klar'
    });
}

function uiConfirm(message, title = 'Bist du sicher?', danger = false) {
    return customDialog({
        title,
        message,
        icon: danger ? '⚠' : '?',
        type: 'confirm',
        confirmText: danger ? 'Ja, fortfahren' : 'Bestätigen',
        danger
    });
}

function uiPrompt(message, defaultValue = '', title = 'Eingabe') {
    return customDialog({
        title,
        message,
        icon: '✎',
        type: 'prompt',
        placeholder: 'Hier eingeben …',
        defaultValue,
        confirmText: 'Speichern'
    });
}