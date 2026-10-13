async function tick(){
  try{
    const s=await(await fetch('/api/status')).json(),on=s.online,run=s.state==='running',w=run&&!on;
    $('st').textContent=s.task?'Wartung':on?'Online':w?'Startet gerade':'Offline';
    $('st').className='badge '+(s.task||w?'wait':on?'on':'off');
    $('motd').textContent=on&&s.motd?s.motd:'Minecraft Server';
    $('note').hidden=!s.task;$('note').textContent=s.task?s.task+' – bitte einen Moment Geduld.':'';
    facts(s);res(s,run);
  }catch(e){}
}
tick();setInterval(tick,4000);