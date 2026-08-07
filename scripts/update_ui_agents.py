"""
Atualiza o index.html com animações de agentes na esteira da pipeline.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FILE = 'static/index.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# === 1. ADD AGENT ANIMATION CSS ===
old_css = '.pipeline-history .history-topic{font-weight:600;flex:1}\n.pipeline-history .history-time{color:#5c6370;font-size:11px}\n</style>'

new_css = """.pipeline-history .history-topic{font-weight:600;flex:1}
.pipeline-history .history-time{color:#5c6370;font-size:11px}

/* ===== AGENT ANIMATIONS ===== */
@keyframes agentTyping{0%,100%{transform:translateY(0)}25%{transform:translateY(-2px)}50%{transform:translateY(0)}75%{transform:translateY(1px)}}
@keyframes agentReading{0%,100%{transform:rotate(0deg)}25%{transform:rotate(-3deg)}75%{transform:rotate(3deg)}}
@keyframes agentThinking{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
@keyframes agentWalking{0%{transform:translateX(-5px)}50%{transform:translateX(5px)}100%{transform:translateX(-5px)}}
@keyframes agentSleeping{0%,100%{opacity:0.5;transform:translateY(0)}50%{opacity:0.3;transform:translateY(1px)}}
@keyframes agentSparkle{0%,100%{opacity:0;transform:scale(0)}50%{opacity:1;transform:scale(1)}}
@keyframes gearSpin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
@keyframes conveyorBeltMove{0%{background-position:0 0}100%{background-position:40px 0}}
.cs-agent-avatar{font-size:42px;display:block;margin-bottom:4px;transition:all .3s ease;position:relative}
.cs-agent-avatar .sparkle{position:absolute;font-size:12px;animation:agentSparkle 1.5s ease-in-out infinite;pointer-events:none}
.cs-agent-avatar .sparkle:nth-child(1){top:-5px;left:-5px;animation-delay:0s}
.cs-agent-avatar .sparkle:nth-child(2){top:-8px;right:-3px;animation-delay:0.5s}
.cs-agent-avatar .sparkle:nth-child(3){bottom:-2px;left:2px;animation-delay:1s}
.conveyor-stage.active .cs-agent-avatar{animation:agentTyping .8s ease-in-out infinite}
.conveyor-stage.completed .cs-agent-avatar{animation:none}
.conveyor-stage.idle .cs-agent-avatar{animation:agentSleeping 2s ease-in-out infinite;opacity:.6}
.conveyor-stage-wrapper:hover .idle .cs-agent-avatar{animation:agentWalking .6s ease-in-out infinite;opacity:.8}
.conveyor-stage .cs-agent-name{font-size:11px;font-weight:700;color:#e8edf2;margin-bottom:1px}
.conveyor-stage .cs-agent-action{font-size:9px;color:#5c6370;min-height:14px}
.conveyor-stage.active .cs-agent-action{color:#fbbf24}
.conveyor-stage.completed .cs-agent-action{color:#4ade80}
.conveyor-stage .cs-agent-gear{display:inline-block;font-size:10px;margin-left:3px;opacity:.4}
.conveyor-stage.active .cs-agent-gear{animation:gearSpin 2s linear infinite;opacity:1}
.conveyor-stage.completed .cs-agent-gear{animation:none;opacity:.6}
.cs-action-badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:8px;font-size:9px;font-weight:600;margin-top:4px;transition:all .3s}
.cs-action-badge.working{background:rgba(245,158,11,.15);color:#fbbf24}
.cs-action-badge.done{background:rgba(34,197,94,.15);color:#4ade80}
.cs-action-badge.waiting{background:rgba(100,116,139,.15);color:#94a3b8}
.conveyor-stage .agent-tooltip{position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);background:#1a1c2a;border:1px solid #2a2d3e;border-radius:8px;padding:8px 12px;font-size:11px;color:#e8edf2;white-space:nowrap;opacity:0;pointer-events:none;transition:all .2s;z-index:10}
.conveyor-stage .agent-tooltip::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);border:6px solid transparent;border-top-color:#2a2d3e}
.conveyor-stage:hover .agent-tooltip{opacity:1;transform:translateX(-50%) translateY(-4px)}
.conveyor-belt::before{background:repeating-linear-gradient(90deg,#1e2030 0,#1e2030 12px,transparent 12px,transparent 16px);background-size:40px 6px;animation:conveyorBeltMove 3s linear infinite;opacity:.3;transition:opacity .5s}
.conveyor-belt.running::before{opacity:.8;animation-duration:1.5s}
</style>"""

content = content.replace(old_css, new_css)

# === 2. UPDATE STAGES WITH AGENT DATA ===
old_stages = """const STAGES=[
  {id:"fundacao",name:"Fundacao",icon:"\U0001f3d7\ufe0f",agent:"Seu Hermes + Dona Celia"},
  {id:"arquitetura",name:"Arquitetura",icon:"\U0001f4cb",agent:"Joaquim"},
  {id:"producao",name:"Producao",icon:"\U0001f4dd",agent:"Carlao + Dona Rosa"},
  {id:"refino",name:"Refino",icon:"\U0001f3a8",agent:"Tatiana + Seu Ze"},
  {id:"entrega",name:"Entrega",icon:"\u2705",agent:"Seu Francisco"}
];"""

new_stages = """const STAGES=[
  {id:"fundacao",name:"Fundacao",icon:"\U0001f3d7\ufe0f",agent:"Seu Hermes + Dona Celia",
    agents:[{name:"Seu Hermes",emoji:"\U0001f474",role:"Orquestrador",action:"Coordenando equipes"},{name:"Dona Celia",emoji:"\U0001f469\u200d\U0001f3a8",role:"Designer",action:"Criando identidade"}]},
  {id:"arquitetura",name:"Arquitetura",icon:"\U0001f4cb",agent:"Joaquim",
    agents:[{name:"Joaquim",emoji:"\U0001f50d",role:"Pesquisador",action:"Pesquisando keywords"}]},
  {id:"producao",name:"Producao",icon:"\U0001f4dd",agent:"Carlao + Dona Rosa",
    agents:[{name:"Carlao",emoji:"\u270d\ufe0f",role:"Redator",action:"Escrevendo artigos"},{name:"Dona Rosa",emoji:"\U0001f50e",role:"Revisora",action:"Verificando similaridade"}]},
  {id:"refino",name:"Refino",icon:"\U0001f3a8",agent:"Tatiana + Seu Ze",
    agents:[{name:"Tatiana",emoji:"\U0001f4f8",role:"Fotografa",action:"Buscando imagens"},{name:"Seu Ze",emoji:"\U0001f4c5",role:"Agendador",action:"Programando publicacao"}]},
  {id:"entrega",name:"Entrega",icon:"\u2705",agent:"Seu Francisco",
    agents:[{name:"Seu Francisco",emoji:"\U0001f474",role:"Supervisor",action:"Conferindo producao"}]}
];"""

content = content.replace(old_stages, new_stages)

# === 3. UPDATE renderPipeline ===
old_render = """function renderPipeline(){
  var t=$("macroPipelineTrack");if(!t)return;
  t.innerHTML=STAGES.map(function(s,i){
    var c='';
    if(i<STAGES.length-1)c='<div class="conveyor-connector"><div class="cc-base"></div><div class="cc-glow" id="cg_'+s.id+'"></div><div class="cc-dot" id="cd_'+s.id+'"></div></div>';
    return '<div class="conveyor-stage-wrapper"><div class="conveyor-stage idle" id="st_'+s.id+'"><div class="cs-border" style="display:none"></div><div class="cs-check" style="display:none">✓</div><span class="cs-icon">'+s.icon+'</span><div class="cs-name">'+s.name+'</div><div class="cs-agent">'+s.agent+'</div><div class="cs-status idle" id="cs_'+s.id+'">⏳</div><div class="cs-progress"><div class="cs-progress-bar" id="cp_'+s.id+'"></div></div><div class="cs-message" id="cm_'+s.id+'"></div></div>'+c+'</div>';
  }).join("");
}"""

new_render = """function renderPipeline(){
  var t=$("macroPipelineTrack");if(!t)return;
  t.innerHTML=STAGES.map(function(s,i){
    var c='';if(i<STAGES.length-1)c='<div class="conveyor-connector"><div class="cc-base"></div><div class="cc-glow" id="cg_'+s.id+'"></div><div class="cc-dot" id="cd_'+s.id+'"></div></div>';
    var av=s.agents? s.agents.map(function(a){return '<span title="'+a.name+': '+a.action+'" style="display:inline-block;margin:0 1px">'+a.emoji+'</span>';}).join(''):s.icon;
    var tp='<div class="agent-tooltip">'+(s.agents? s.agents.map(function(a){return a.name+' • '+a.role;}).join('<br>'):s.agent)+'</div>';
    return '<div class="conveyor-stage-wrapper"><div class="conveyor-stage idle" id="st_'+s.id+'"><div class="cs-border" style="display:none"></div><div class="cs-check" style="display:none">✓</div>'+
      '<div class="cs-agent-avatar">'+av+'<span class="sparkle">✦</span><span class="sparkle">✦</span><span class="sparkle">✦</span></div>'+
      '<div class="cs-name">'+s.name+'</div>'+
      '<div class="cs-agent-action" id="ac_'+s.id+'">⏳ <span id="al_'+s.id+'">Aguardando</span> <span class="cs-agent-gear">⚙</span></div>'+
      '<div class="cs-progress"><div class="cs-progress-bar" id="cp_'+s.id+'"></div></div>'+
      '<div class="cs-status idle" id="cs_'+s.id+'">⏳</div>'+
      '<div class="cs-message" id="cm_'+s.id+'"></div>'+tp+'</div>'+c+'</div>';
  }).join("");
}"""

content = content.replace(old_render, new_render)

# === 4. UPDATE updateStage ===
old_upd = """function updateStage(sid,status,prog,msg,data){
  var el=$("st_"+sid),st=$("cs_"+sid),pr=$("cp_"+sid),ms=$("cm_"+sid);
  if(!el)return;
  el.className="conveyor-stage "+status;
  if(st){st.className="cs-status "+status;var lb={idle:"⏳",active:"🔄",completed:"✅",failed:"❌"};st.textContent=lb[status]||status}
  var ck=el.querySelector(".cs-check");
  if(ck){ck.style.display=status==="completed"?"flex":"none";if(status==="completed")ck.style.animation="checkPop .4s cubic-bezier(.34,1.56,.64,1)"}
  if(pr){pr.className="cs-progress-bar "+status;if(status==="active"&&prog>0)pr.style.width=prog+"%"}
  if(ms)ms.textContent=msg||"";
  if(status==="active"||status==="completed"){
    ["fundacao","arquitetura","producao","refino"].forEach(function(id){
      var g=$("cg_"+id);if(g)g.classList.add("lit");
      var d=$("cd_"+id);if(d)d.classList.add("lit");
    });
  }
  if(data){
    if(data.current_article!==undefined){ms.cur=data.current_article;$("macroCurrentBadge").textContent="📝 Artigo "+data.current_article+"/"+ms.target;updateBar()}
    if(data.article_topic){$("macroCurrentTitle").textContent=data.article_topic;ms.topic=data.article_topic}
    if(data.phase_detail){$("macroCurrentPhase").textContent="🔄 "+data.phase_detail}
  }
}"""

new_upd = """function updateStage(sid,status,prog,msg,data){
  var el=$("st_"+sid),st=$("cs_"+sid),pr=$("cp_"+sid),ms=$("cm_"+sid),al=$("al_"+sid),ac=$("ac_"+sid);
  if(!el)return;
  el.className="conveyor-stage "+status;
  if(st){st.className="cs-status "+status;var lb={idle:"⏳",active:"🔄",completed:"✅",failed:"❌"};st.textContent=lb[status]||status}
  var ck=el.querySelector(".cs-check");
  if(ck){ck.style.display=status==="completed"?"flex":"none";if(status==="completed")ck.style.animation="checkPop .4s cubic-bezier(.34,1.56,.64,1)"}
  if(pr){pr.className="cs-progress-bar "+status;if(status==="active"&&prog>0)pr.style.width=prog+"%"}
  if(ms)ms.textContent=msg||"";
  // Update agent action label
  if(al){
    var actions={idle:"Aguardando",active:"Trabalhando...",completed:"Concluido!",failed:"Erro"};
    al.textContent=actions[status]||status;
  }
  if(ac)ac.innerHTML=(status==="active"?"🔄 ":"⏳ ")+'<span id="al_'+sid+'">'+(al?al.textContent:"")+'</span> <span class="cs-agent-gear">⚙</span>';
  // Belt animation
  var belt=document.querySelector(".conveyor-belt");
  if(belt)belt.classList.toggle("running",status==="active");
  // Connector glow
  if(status==="active"||status==="completed"){
    ["fundacao","arquitetura","producao","refino"].forEach(function(id){
      var g=$("cg_"+id);if(g)g.classList.add("lit");
      var d=$("cd_"+id);if(d)d.classList.add("lit");
    });
  }
  if(data){
    if(data.current_article!==undefined){ms.cur=data.current_article;$("macroCurrentBadge").textContent="📝 Artigo "+data.current_article+"/"+ms.target;updateBar()}
    if(data.article_topic){$("macroCurrentTitle").textContent=data.article_topic;ms.topic=data.article_topic}
    if(data.phase_detail){$("macroCurrentPhase").textContent="🔄 "+data.phase_detail}
  }
}"""

content = content.replace(old_upd, new_upd)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: UI atualizada com agentes animados!")
