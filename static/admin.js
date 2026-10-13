const api=async(p,b)=>{try{const r=await fetch('/api/admin/'+p,b===undefined?{}:{method:'POST',headers:{'X-Req':'1','Content-Type':'application/json'},body:JSON.stringify(b)});if(r.status===401){location='/login';return{}}return await r.json()}catch(e){return{error:'Keine Verbindung zum Panel.'}}};
let S={},cur='overview',tick=0;
const NAMEOK=/^[.A-Za-z0-9_]{1,16}$/;
const mk=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!==undefined)e.textContent=x;return e};
function rows(ul,items,empty,build){ul.innerHTML='';if(!items.length){ul.append(mk('li','empty',empty));return}items.forEach(i=>ul.append(build(i)))}
function item(txt,btns){const li=mk('li');li.append(mk('span','',txt));const d=mk('span','acts');btns.forEach(b=>d.append(b));li.append(d);return li}
function btn(t,k,v,c){const b=mk('button',c||'sm',t);b.dataset[k]=v;return b}
const done=r=>toast(r.error||r.message||r.out||'Erledigt.',!!r.error);

/* ---------- Status & Steuerung ---------- */
async function state(){
  let s;try{s=await(await fetch('/api/status')).json()}catch(e){return}
  S=s;
  const on=s.online,run=s.state==='running',miss=s.state==='missing',w=run&&!on,t=s.task;
  $('st').textContent=t?t:on?'Online':w?'Startet gerade …':miss?'Container nicht gefunden':'Offline';
  $('dot').className='dot '+(t||w?'wait':on?'on':'off');
  $('stsub').textContent=t?'Bitte warten, das kann ein bis zwei Minuten dauern. Du musst nichts weiter tun.'
    :on?s.players+' von '+s.max+' Spielern online.'
    :w?'Der Server fährt hoch. Das dauert meist 1 bis 2 Minuten.'
    :miss?'Der Minecraft-Container existiert nicht (mehr).'
    :'Der Server ist aus. Klicke auf „Server starten“.';
  $('b_start').hidden=run||miss;$('b_restart').hidden=!run;$('b_stop').hidden=!run;
  document.querySelectorAll('[data-p]').forEach(b=>b.disabled=!!t);
  $('err').hidden=!s.err;$('err').textContent=s.err||'';
  facts(s);res(s,run);
}
document.addEventListener('click',async e=>{
  const b=e.target.closest('[data-p]');if(!b)return;
  const a=b.dataset.p,n=S.players||0,txt=a==='stop'?'stoppen':'neu starten';
  if(a!=='start'&&!await uiConfirm(n?'Es sind noch '+n+' Spieler online. Sie werden getrennt. Server wirklich '+txt+'?':'Server wirklich '+txt+'?'))return;
  done(await api('power',{action:a}));state();
});

/* ---------- Konsole ---------- */
async function log(){const r=await api('console'),l=$('log'),b=l.scrollTop+l.clientHeight>l.scrollHeight-40;l.textContent=r.log||'';if(b)l.scrollTop=l.scrollHeight}
async function runCmd(c){c=c.trim().replace(/^\/+/,'');if(!c)return;done(await api('cmd',{cmd:c}));log()}
$('cf').onsubmit=e=>{e.preventDefault();const c=$('cmd').value;$('cmd').value='';runCmd(c)};

document.addEventListener('click', async e => {const b = e.target.closest('[data-q]');if (!b) return;
    if (b.dataset.q === 'say') {
  const m = await uiPrompt('Nachricht an alle Spieler:','','Nachricht senden?');
    if (m !== null && m.trim()) {runCmd('say ' + m);}
  } else {runCmd(b.dataset.q);}});

/* ---------- Spieler ---------- */
const act=(t,a,n,c)=>{const b=mk('button',c||'sm',t);b.dataset.a=a;b.dataset.n=n;return b};
async function players(){
  const r=await api('players');if(r.error)return;
  rows($('l_on'),S.names||[],'Gerade ist niemand online.',n=>item(n,[act('Kicken','kick',n),act('Bannen','ban',n,'sm danger')]));
  rows($('l_wl'),r.whitelist,'Die Whitelist ist leer.',n=>item(n,[act('Entfernen','whitelist_remove',n)]));
  rows($('l_op'),r.ops,'Es gibt keine Operatoren.',n=>item(n,[act('OP entziehen','deop',n)]));
  rows($('l_ban'),r.banned,'Niemand ist gebannt.',n=>item(n,[act('Entbannen','pardon',n)]));
}
document.addEventListener('click',async e=>{
  const b=e.target.closest('[data-a]');if(!b)return;
  const a=b.dataset.a,n=(b.dataset.n!==undefined?b.dataset.n:$('pn').value).trim();
  if(!NAMEOK.test(n))return toast('Bitte einen gültigen Spielernamen eingeben (1 bis 16 Zeichen: Buchstaben, Zahlen, _).',true);
  if(a==='ban'&&!await uiConfirm('„'+n+'“ wirklich bannen?'))return;
  done(await api('player',{action:a,name:n}));players();
});

/* ---------- Plugins ---------- */
async function plugins(){
  const r=await api('plugins');
  if(r.error){rows($('l_pl'),[],r.error,()=>null);return}
  rows($('l_pl'),r.files,'Noch keine Plugins installiert.',f=>item(f.name+'  ('+f.mb+' MB)',[btn('Löschen','pd',f.name,'sm danger')]));
}
const up=f=>new Promise(res=>{
  const x=new XMLHttpRequest(),fd=new FormData();fd.append('file',f);
  x.open('POST','/api/admin/plugins/upload');x.setRequestHeader('X-Req','1');
  x.upload.onprogress=e=>{if(e.lengthComputable)$('upb').style.width=(e.loaded/e.total*100)+'%'};
  x.onload=()=>{if(x.status===401){location='/login';return}let r;try{r=JSON.parse(x.responseText)}catch(e){r={error:'Upload fehlgeschlagen (Status '+x.status+').'}}res(r)};
  x.onerror=()=>res({error:'Upload fehlgeschlagen, die Verbindung wurde unterbrochen.'});
  x.send(fd);
});
async function upAll(files){
  for(const f of files){
    if(!/\.jar$/i.test(f.name)){toast('„'+f.name+'“ ist keine .jar-Datei.',true);continue}
    $('upw').hidden=false;$('upb').style.width='0';$('upn').textContent=f.name;
    done(await up(f));
  }
  $('upw').hidden=true;plugins();
}
const dz=$('drop');
['dragenter','dragover'].forEach(v=>dz.addEventListener(v,e=>{e.preventDefault();dz.classList.add('hot')}));
['dragleave','drop'].forEach(v=>dz.addEventListener(v,e=>{e.preventDefault();dz.classList.remove('hot')}));
dz.addEventListener('drop',e=>upAll(e.dataTransfer.files));
$('pf').onchange=e=>{upAll([...e.target.files]);e.target.value=''};
document.addEventListener('click',async e=>{
  const b=e.target.closest('[data-pd]');if(!b)return;
  if(!await uiConfirm('Plugin „'+b.dataset.pd+'“ löschen? Seine Einstellungen im Ordner plugins/ bleiben erhalten.'))return;
  done(await api('plugins/delete',{name:b.dataset.pd}));plugins();
});

/* ---------- Einstellungen ---------- */
const SET=[
 ['motd','text','Servername (MOTD)','Dieser Text steht in der Serverliste von Minecraft.'],
 ['gamemode','sel','Spielmodus','Gilt für Spieler, die neu beitreten.',{survival:'Überleben',creative:'Kreativ',adventure:'Abenteuer',spectator:'Zuschauer'}],
 ['difficulty','sel','Schwierigkeit','',{peaceful:'Friedlich',easy:'Leicht',normal:'Normal',hard:'Schwer'}],
 ['max-players','num','Maximale Spielerzahl','',1,500],
 ['view-distance','num','Sichtweite (Chunks)','Kleiner = weniger CPU und RAM. 8 bis 10 ist ein guter Wert.',3,32],
 ['simulation-distance','num','Simulationsweite (Chunks)','Wie weit um die Spieler herum die Welt „lebt“. Kleiner = schneller.',3,32],
 ['pvp','bool','Spieler können sich gegenseitig schaden (PvP)'],
 ['white-list','bool','Whitelist aktiv','Nur eingetragene Spieler dürfen beitreten.'],
 ['online-mode','bool','Nur echte Minecraft-Accounts (Online-Modus)','Nur ausschalten, wenn du genau weißt, warum. Sonst kann sich jeder als jemand anderes ausgeben.'],
 ['allow-flight','bool','Fliegen erlauben','Manche Plugins brauchen das, sonst werden fliegende Spieler gekickt.'],
 ['enable-command-block','bool','Befehlsblöcke erlauben'],
 ['allow-nether','bool','Nether aktiv'],
 ['spawn-monsters','bool','Monster spawnen'],
 ['spawn-animals','bool','Tiere spawnen'],
];
(function(){const f=$('setf');SET.forEach(d=>{
  const row=mk('div','set'),L=mk('div');L.append(mk('b','',d[2]));if(d[3])L.append(mk('small','',d[3]));row.append(L);
  let el;
  if(d[1]==='bool'){el=mk('input');el.type='checkbox'}
  else if(d[1]==='sel'){el=mk('select');Object.entries(d[4]).forEach(([v,x])=>{const o=mk('option','',x);o.value=v;el.append(o)})}
  else if(d[1]==='num'){el=mk('input');el.type='number';el.min=d[4];el.max=d[5]}
  else{el=mk('input');el.maxLength=100}
  el.id='s_'+d[0];row.append(el);f.append(row)})})();
async function settings(){
  const r=await api('settings');if(r.error){toast(r.error,true);return}
  SET.forEach(d=>{const e=$('s_'+d[0]),v=r.values[d[0]];if(d[1]==='bool')e.checked=v==='true';else e.value=v});
  const p=await api('props');$('props').value=p.text||'';
}
async function saveSet(){
  const v={};SET.forEach(d=>{const e=$('s_'+d[0]);v[d[0]]=d[1]==='bool'?e.checked:d[1]==='num'?Math.min(d[5],Math.max(d[4],parseInt(e.value,10)||d[4])):e.value});
  const r=await api('settings',{values:v});done(r);return !r.error;
}
$('set_save').onclick=saveSet;
$('set_rs').onclick=async()=>{if(await saveSet()&&await uiConfirm('Server jetzt neu starten? Spieler werden getrennt.'))done(await api('power',{action:'restart'}))};
$('pr_save').onclick=async()=>{const r=await api('props',{text:$('props').value});toast(r.error||'Gespeichert. Gilt nach dem nächsten Neustart.',!!r.error)};

/* ---------- Version & RAM ---------- */
async function software(){
  const r=await api('software');if(r.error){toast(r.error,true);return}
  const sel=$('ver_sel'),vs=r.versions||[];sel.innerHTML='';
  vs.forEach(v=>{const o=mk('option','',v+(v===r.version?' (aktuell)':''));o.value=v;sel.append(o)});
  if(r.version&&vs.includes(r.version))sel.value=r.version;
  $('ver_cur').textContent=r.version||'unbekannt (Server aus?)';
  $('ver_btn').disabled=!vs.length||!r.managed;
  $('ver_hint').textContent=!r.managed?'Dieser Server wurde nicht mit dem Image itzg/minecraft-server erstellt, hier kann die Version nicht gewechselt werden.':!vs.length?'Die Versionsliste konnte nicht geladen werden (keine Verbindung zu papermc.io?). Versuche es später erneut.':'';
  const rr=$('ram_r');rr.min=1;rr.max=r.max_gb;rr.value=Math.min(r.ram_gb,r.max_gb);rr.disabled=!r.managed||r.max_gb<2;
  $('ram_btn').disabled=!r.managed;$('ram_v').textContent=rr.value+' GB';
  $('ram_i').textContent='Dein Rechner hat '+r.total_gb+' GB RAM. Mehr als '+r.max_gb+' GB sind gesperrt, damit das System nicht abstürzt.'+(r.managed?'':' Dieser Server wurde nicht mit itzg/minecraft-server erstellt, der RAM kann hier nicht geändert werden.');
}
$('ram_r').oninput=()=>$('ram_v').textContent=$('ram_r').value+' GB';
$('ver_btn').onclick = async () => {
  const v = $('ver_sel').value;
  if (!v) return;
  
  // Wir prüfen, ob es sich um ein Downgrade handelt (aktuell vs. gewählt)
  const cur = $('ver_cur').textContent;
  // Hilfsfunktion zum Vergleichen von Versionsnummern (z.B. "1.20.4" vs "1.19.2")
  const isDowngrade = cur && vkey(v) < vkey(cur);

  let resetWorld = false;

  if (isDowngrade) {
    // Wenn es ein Downgrade ist, fragen wir, ob eine neue Welt erstellt werden soll
    resetWorld = await uiConfirm(
      'ACHTUNG: Du versuchst ein Downgrade von ' + cur + ' auf ' + v + '.\n' +
      'Das kann die alte Welt beschädigen. Soll dabei eine komplett NEUE Welt erstellt werden?\n\n' +
      'Klicke auf "OK" für Ja (neue Welt erstellen) oder "Abbrechen" zum Abbrechen.'
    );
    if (!resetWorld) return; // Wenn abgebrochen wird, stoppen wir hier
  } else {
    // Normaler Versionswechsel / Upgrade
    if (!await uiConfirm('Auf Version ' + v + ' wechseln? Vorher wird automatisch ein Backup erstellt.')) return;
  }

  // Wir schicken den Parameter "reset_world" an den API-Endpunkt
  done(await api('version', { version: v, reset_world: resetWorld }));
  state();
};

// Hilfsfunktion zum Vergleichen von Versionen (muss im JS vorhanden sein)
function vkey(v) {
  return v.split('.').map(x => parseInt(x, 10));
}
$('ram_btn').onclick=async()=>{const g=$('ram_r').value;
  if(!await uiConfirm('Dem Server '+g+' GB RAM geben? Er wird dafür neu gestartet.'))return;
  done(await api('ram',{gb:+g}));state();};

/* ---------- Welt ---------- */

$('w_btn').onclick = async () => {
    const confirmation = await uiPrompt(
        'ACHTUNG: Die aktuelle Welt wird gelöscht (vorher gibt es ein Backup).\nTippe zur Bestätigung: NEUE WELT',
        '',
        'Welt zurücksetzen?');
    if (confirmation !== 'NEUE WELT') return;
    done(await api('reset_world', { seed: $('seed').value }));
    state();};


/* ---------- Backups ---------- */
async function backups(){
  const r=await api('backups');if(r.error)return;
  $('bk').disabled=r.busy;$('bk').textContent=r.busy?'Backup läuft …':'💾 Jetzt Backup erstellen';
  rows($('bl'),r.files,'Noch keine Backups vorhanden.',f=>{
    const m=f.name.match(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/),t=m?m[3]+'.'+m[2]+'.'+m[1]+' um '+m[4]+':'+m[5]+' Uhr':f.name;
    const a=mk('a','sm btn','Download');a.href='/admin/backup/'+f.name;
    return item(t+'  ('+f.mb+' MB)',[a,btn('Wiederherstellen','br',f.name),btn('Löschen','bd',f.name,'sm danger')]);
  });
}
$('bk').onclick=async()=>{done(await api('backup',{}));backups()};
document.addEventListener('click',async e=>{
  const r=e.target.closest('[data-br]'),d=e.target.closest('[data-bd]');
  if(r){if(!await uiConfirm('Dieses Backup wiederherstellen? Die aktuelle Welt wird ersetzt (vorher wird sie automatisch gesichert) und der Server startet neu.'))return;done(await api('restore',{name:r.dataset.br}));state()}
  if(d){if(!await uiConfirm('Backup endgültig löschen?'))return;done(await api('backup/delete',{name:d.dataset.bd}));backups()}
});

/* ---------- Server-Icon ---------- */
let selectedServerIcon = null;

async function loadServerIcon() {
  const r = await api('server-icon');
  if (r.error) {
    $('server_icon_status').textContent = r.error;
    return;
  }

  $('server_icon_preview').src = r.data;
  $('server_icon_status').textContent = r.custom
    ? 'Eigenes Server-Icon aktiv.'
    : 'Standard-Icon aktiv.';
}

$('server_icon_file').onchange = e => {
  const file = e.target.files[0];
  selectedServerIcon = file || null;
  $('server_icon_upload').disabled = !file;

  if (!file) return;

  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
    toast('Bitte wähle eine PNG-, JPG- oder WebP-Datei.', true);
    selectedServerIcon = null;
    $('server_icon_upload').disabled = true;
    e.target.value = '';
    return;
  }

  const url = URL.createObjectURL(file);
  $('server_icon_preview').src = url;
  $('server_icon_status').textContent =
    file.name + ' – bereit zum Hochladen';
};

$('icon_drop').addEventListener('dragover', e => {
  e.preventDefault();
  $('icon_drop').classList.add('hot');
});

$('icon_drop').addEventListener('dragleave', () => {
  $('icon_drop').classList.remove('hot');
});

$('icon_drop').addEventListener('drop', e => {
  e.preventDefault();
  $('icon_drop').classList.remove('hot');

  const file = e.dataTransfer.files[0];
  if (!file) return;

  const input = $('server_icon_file');
  const transfer = new DataTransfer();
  transfer.items.add(file);
  input.files = transfer.files;
  input.dispatchEvent(new Event('change'));
});

$('server_icon_upload').onclick = async () => {
  if (!selectedServerIcon) return;

  const fd = new FormData();
  fd.append('file', selectedServerIcon);

  const button = $('server_icon_upload');
  button.disabled = true;
  button.textContent = 'Wird hochgeladen …';

  try {
    const r = await fetch('/api/admin/server-icon/upload', {
      method: 'POST',
      headers: { 'X-Req': '1' },
      body: fd
    });

    if (r.status === 401) {
      location = '/login';
      return;
    }

    const result = await r.json();
    done(result);

    if (!result.error) {
      selectedServerIcon = null;
      $('server_icon_file').value = '';
      await loadServerIcon();
    }
  } catch (e) {
    toast('Das Icon konnte nicht hochgeladen werden.', true);
  } finally {
    button.textContent = 'Icon hochladen';
    button.disabled = !selectedServerIcon;
  }
};

$('server_icon_reset').onclick = async () => {
  if (!await uiConfirm('Das Standard-Server-Icon wiederherstellen?')) return;

  const r = await api('server-icon/reset', {});
  done(r);

  if (!r.error) {
    selectedServerIcon = null;
    $('server_icon_file').value = '';
    $('server_icon_upload').disabled = true;
    await loadServerIcon();
  }
};


/* ---------- Tabs & Start ---------- */
const tabs = [...document.querySelectorAll('[data-t]')],
  LOAD = {
    console: log,
    players,
    plugins,
    settings: async () => {
      await settings();
      await loadServerIcon();
    },
    software,
    backups
  };
function show(){
  let h=(location.hash||'#overview').slice(1);if(!tabs.some(a=>a.dataset.t===h))h='overview';cur=h;
  tabs.forEach(a=>a.classList.toggle('act',a.dataset.t===h));
  document.querySelectorAll('.pg').forEach(p=>p.hidden=p.id!=='p-'+h);
  if(LOAD[h])LOAD[h]();
}
addEventListener('hashchange',show);
setInterval(()=>{tick++;state();if(cur==='console')log();if(cur==='backups')backups();if(cur==='players'&&tick%2===0)players()},3000);
state().then(show);