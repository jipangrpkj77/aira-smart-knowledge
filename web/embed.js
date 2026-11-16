(function(){
  if(document.getElementById('aira-root'))return;
  const base=(document.currentScript && new URL(document.currentScript.src).origin)||'http://127.0.0.1:8765';
  let css=document.createElement('link');css.rel='stylesheet';css.href=base+'/widget.css';document.head.appendChild(css);
  const root=document.createElement('div');root.id='aira-root';
  root.innerHTML=`<section id="aira-panel" role="dialog" aria-label="Chat bersama AIRA"><div id="aira-header"><img alt="AIRA" src="${base}/assets/aira_idle.png"><div id="aira-h-title">AIRA <small>AI Assistant • SIGNTECH SOLUTION</small></div><button id="aira-minimize" type="button" aria-label="Minimize chat" title="Minimize">−</button><button id="aira-close" type="button" aria-label="Tutup chatbot" title="Tutup">×</button></div><div id="aira-messages" aria-live="polite"><div class="aira-msg aira-ai">Assalamualaikum! 🌸 Saya AIRA, pembantu AI SIGNTECH SOLUTION. Ada apa yang boleh saya bantu?</div></div><div id="aira-typing" role="status" aria-live="polite" hidden><span class="aira-typing-dots" aria-hidden="true"><i></i><i></i><i></i></span><span id="aira-typing-text">AIRA sedang menyediakan jawapan...</span></div><div id="aira-quick"><button class="aira-chip" data-question="Apakah kursus Python yang ditawarkan SIGNTECH?">Kursus Python</button><button class="aira-chip" data-question="Apakah perkhidmatan SIGNTECH SOLUTION?">Perkhidmatan</button><button class="aira-chip" data-question="Bagaimanakah cara mendapatkan maklumat HRD Corp?">HRD Corp</button></div><form id="aira-form"><input id="aira-input" type="text" maxlength="2000" placeholder="Taip pertanyaan anda..." aria-label="Soalan kepada AIRA"><button id="aira-send" aria-label="Hantar mesej" type="submit">➤</button></form><div id="aira-footer">AIRA boleh tersilap. Sahkan maklumat penting dengan SIGNTECH.</div></section><div id="aira-launch"><button id="aira-bubble" type="button">Chat dengan AIRA 💙</button><button id="aira-avatar" type="button" aria-label="Buka chatbot AIRA" aria-expanded="false"><img id="aira-face" src="${base}/assets/aira_welcome_animated.webp" alt="AIRA, pembantu maya Muslimah"></button></div>`;
  document.body.appendChild(root);
  const $=id=>root.querySelector('#'+id),face=$('aira-face'); let history=[],busy=false,open=false;
  const headFace=$('aira-header').querySelector('img');
  let faceTimer=null;
  const picture=name=>base+'/assets/aira_'+name+'.png';
  function state(name,duration=0){
    clearTimeout(faceTimer);
    const avatar=$('aira-avatar');
    avatar.classList.toggle('aira-breath', name==='idle');
    avatar.classList.toggle('aira-thinking', name==='thinking');
    // Keep facial identity and prevent the ghosted pose crossfade.
    face.src=name==='idle'?base+'/assets/aira_idle_animated.webp':
        name==='welcome'?base+'/assets/aira_v2_welcome.webp':picture(name);
    headFace.src=face.src;
    if(duration)faceTimer=setTimeout(()=>state('idle'),duration);
  }
  function toggle(force){open=(typeof force==='boolean'?force:!open);root.classList.toggle('aira-open',open);$('aira-avatar').setAttribute('aria-expanded',String(open));$('aira-bubble').hidden=open;state(open?'welcome':'idle',open?2500:0);if(open)$('aira-input').focus()}
  $('aira-avatar').onclick=()=>toggle();$('aira-bubble').onclick=()=>toggle(true);$('aira-close').onclick=()=>toggle(false);$('aira-minimize').onclick=()=>toggle(false);
  function add(role,text){let node=document.createElement('div');node.className='aira-msg '+(role==='user'?'aira-user':'aira-ai');node.textContent=text;$('aira-messages').appendChild(node);node.scrollIntoView({block:'end'});return node}
  function pick(text){let s=text.toLowerCase();if(/terima kasih|thank(s| you)/.test(s))return 'thankyou';if(/maaf|sorry/.test(s))return 'apologize';if(/bye|selamat tinggal|jumpa lagi/.test(s))return 'goodbye';if(/tahniah|syabas|berjaya/.test(s))return 'success';if(/pautan|link|daftar|klik/.test(s))return 'pointing';if(/tidak faham|keliru/.test(s))return 'confused';return 'answering'}
  // Prefer the language of the newest question. AIRA may switch each turn.
  function detectLanguage(value, fallback='ms') {
    const s=(value||'').toLowerCase().trim();
    if(!s) return fallback;
    const ms=/\b(apakah|bagaimana|kenapa|mengapa|boleh|saya|anda|awak|nak|mahu|kursus|latihan|syarikat|perkhidmatan|tolong|terima kasih|jawapan|harga|yuran|tarikh|daftar|tidak|yang|untuk|dengan|dalam|daripada|sedang|menyediakan|maklumat|mengenai|bahasa|inggeris)\b/g;
    const en=/\b(what|how|why|when|where|which|who|can|could|would|should|please|help|tell|explain|about|course|training|company|services|price|fees|date|register|thank you|thanks|your|you|the|is|are|do|does|have|provide|available|english|response|answer|learning|beginner)\b/g;
    const m=(s.match(ms)||[]).length, e=(s.match(en)||[]).length;
    if(e>m) return 'en';
    if(m>e) return 'ms';
    return fallback;
  }
  const copy={
    ms:{waiting:'AIRA sedang menyediakan jawapan...',error:'Maaf, AIRA belum dapat menghubungi AI sekarang. Sila pastikan Ollama berjalan pada komputer pelayan.',placeholder:'Taip pertanyaan anda...',bubble:'Chat dengan AIRA 💙',footer:'AIRA boleh tersilap. Sahkan maklumat penting dengan SIGNTECH.',welcome:'Assalamualaikum! 🌸 Saya AIRA, pembantu AI SIGNTECH SOLUTION. Ada apa yang boleh saya bantu?'},
    en:{waiting:'AIRA is preparing a response...',error:'Sorry, AIRA cannot connect to the AI right now. Please make sure Ollama is running on the server.',placeholder:'Type your question...',bubble:'Chat with AIRA 💙',footer:'AIRA can make mistakes. Please verify important information with SIGNTECH.',welcome:'Hello! 🌸 I’m AIRA, SIGNTECH SOLUTION’s AI assistant. How can I help you?'}
  };
  let currentLanguage='ms';
  function setLanguage(lang){
    currentLanguage=lang==='en'?'en':'ms';
    const t=copy[currentLanguage];
    $('aira-input').placeholder=t.placeholder;
    $('aira-bubble').textContent=t.bubble;
    $('aira-footer').textContent=t.footer;
    const greeting=$('aira-messages').firstElementChild;
    if(greeting && greeting.dataset.initialGreeting==='true') greeting.textContent=t.welcome;
    $('aira-typing-text').textContent=t.waiting;
    $('aira-minimize').setAttribute('aria-label',currentLanguage==='en'?'Minimize chat':'Minimumkan chat');
    $('aira-close').setAttribute('aria-label',currentLanguage==='en'?'Close chat':'Tutup chatbot');
  }
  $('aira-messages').firstElementChild.dataset.initialGreeting='true';
  async function ask(q){
    if(busy||!q.trim()) return;
    busy=true;
    const prev=history.slice();
    const lang=detectLanguage(q,currentLanguage);
    setLanguage(lang);
    add('user',q);
    $('aira-input').value='';
    state('listening',500);
    $('aira-typing-text').textContent=copy[lang].waiting;
    $('aira-typing').hidden=false;
    $('aira-messages').scrollTop=$('aira-messages').scrollHeight;
    state('thinking');
    $('aira-send').disabled=true;
    try{
      const res=await fetch(base+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:q,history:prev,language:lang})});
      const data=await res.json();
      if(!res.ok) throw Error(data.error||'AI service unavailable');
      const replyLanguage=detectLanguage(data.answer,lang);
      setLanguage(replyLanguage);
      $('aira-typing').hidden=true;
      add('assistant',data.answer);
      if (Array.isArray(data.sources) && data.sources.length) {
        const el=document.createElement('div'); el.className='aira-sources';
        el.textContent=(lang==='en'?'Sources: ':'Sumber: ')+data.sources.map(x=>x.title).slice(0,3).join(' • ');
        $('aira-messages').appendChild(el);
      }
      history.push({role:'user',content:q},{role:'assistant',content:data.answer});
      state(pick(q+' '+data.answer),2700);
    }catch(e){
      $('aira-typing').hidden=true;
      add('assistant',copy[lang].error);
      state('apologize',2600);
      console.error('[AIRA]',e);
    }finally{$('aira-typing').hidden=true;busy=false;$('aira-send').disabled=false;$('aira-input').focus()}
  }
  $('aira-form').addEventListener('submit',e=>{e.preventDefault();ask($('aira-input').value)});
  root.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>ask(b.dataset.question)));
  // Expose preview-only animation controls; no page-source editing required.
  window.AIRA_V2_DEMO={state,openChat:()=>toggle(true)};
  state('welcome',1450);
})();
