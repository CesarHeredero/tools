#!/usr/bin/env python3
"""Reconstruct porra/index.html from clean prefix + new JavaScript."""
import os, sys

SRC = '/home/debian/tools/html/porra/index.html'
assert os.path.exists(SRC), f"Not found: {SRC}"

# Read clean prefix: bytes 0-21071 (includes trailing comma after 'RD Congo')
with open(SRC, 'rb') as f:
    prefix = f.read(21071)

tail = prefix[-60:]
print(f"Prefix: {len(prefix)} bytes")
print(f"Tail: {repr(tail)}")
assert b"'DR Congo':'RD Congo'" in prefix, "Unexpected prefix — aborting!"

# Complete suffix: rest of ES + all JavaScript
SUFFIX = """'Uzbekistan':'Uzbekistán','Colombia':'Colombia','England':'Inglaterra','Mexico':'México','Canada':'Canadá','Morocco':'Marruecos','Ecuador':'Ecuador','Iran':'Irán','Uruguay':'Uruguay','Croatia':'Croacia','Australia':'Australia','Qatar':'Catar','Panama':'Panamá','Haiti':'Haití','Paraguay':'Paraguay','Iraq':'Irak','Tunisia':'Túnez','Curaçao':'Curazao'};
const es = t => ES[t] || t || '—';
const ROUNDS = [
  {k:'r32',nstr:'Dieciseisavos',p:3},
  {k:'r16',nstr:'Octavos',p:4},
  {k:'qf',nstr:'Cuartos',p:5},
  {k:'sf',nstr:'Semifinal',p:6},
  {k:'final',nstr:'La final',p:7}
];
const sign = n => n>0?1:n<0?-1:0;
let preds, res;

async function load() {
  try { preds = await (await fetch('./predictions.json')).json(); } catch(e) { preds = PRED_FALLBACK; }
  try { res = await (await fetch('./results.json')).json(); } catch(e) { res = RES_FALLBACK; }
  render();
}

function calcScore(p) {
  let g=0,k=0,ind=0;
  if (res.groups && p.groups) {
    for (const [key,rS] of Object.entries(res.groups)) {
      if (!rS) continue;
      const pS = p.groups[key];
      if (!pS) continue;
      const rO=sign(rS[0]-rS[1]), pO=sign(pS[0]-pS[1]);
      if (rO===pO) g += (pS[0]===rS[0] && pS[1]===rS[1]) ? 3 : 1;
    }
  }
  if (res.reached) {
    for (const rd of ROUNDS) {
      const reached=res.reached[rd.k]||[], predicted=p[rd.k]||[];
      for (const t of predicted) if (reached.includes(t)) k+=rd.p;
    }
  }
  if (res.champion && p.champion===res.champion) ind+=10;
  if (res.individuals) {
    if (res.individuals.scorer && p.scorer===res.individuals.scorer) ind+=5;
    if (res.individuals.mvp && p.mvp===res.individuals.mvp) ind+=5;
    if (res.individuals.young && p.young===res.individuals.young) ind+=5;
  }
  return {total:g+k+ind, g, k, ind};
}

function se(label, val, max) {
  const pct = max>0 ? Math.round(val/max*100) : 0;
  return `<div class="row"><div class="lr"><span>${label}</span><span class="v">${val}</span></div><div class="bar"><span style="width:${pct}%"></span></div></div>`;
}

function render() {
  const data = preds || PRED_FALLBACK;
  const matches = data.matches || [];
  const participants = data.participants || [];
  const ME = participants[0] ? participants[0].name : 'César';
  const me = participants.find(p => p.name === ME) || participants[0];
  const scored = participants.map(p => Object.assign({}, p, {sc: calcScore(p)}));
  scored.sort((a,b) => b.sc.total - a.sc.total);
  const mySc = me ? calcScore(me) : {total:0,g:0,k:0,ind:0};
  const myRank = scored.findIndex(p => p.name === ME) + 1;
  const medals = ['🥇','🥈','🥉'];

  document.getElementById('meTotal').textContent = mySc.total;
  document.getElementById('meG').textContent = mySc.g;
  document.getElementById('meK').textContent = mySc.k;
  document.getElementById('meI').textContent = mySc.ind;
  document.getElementById('sub').textContent = res.updated
    ? 'Actualizado: ' + new Date(res.updated).toLocaleDateString('es')
    : 'Sin resultados aún';
  document.getElementById('rankPill').innerHTML =
    (myRank<=3 ? medals[myRank-1] : '#'+myRank) + ' Posición ' + myRank + '/' + scored.length;

  const anyResult = res.groups && Object.keys(res.groups).length > 0;
  document.getElementById('bannerBox').innerHTML = !anyResult
    ? '<div class="banner">⏳ El torneo aún no ha comenzado. Las puntuaciones son 0.</div>' : '';

  let podHtml = '';
  const podOrder = scored.length>=3 ? [1,0,2] : scored.length===2 ? [0,1] : [0];
  for (const i of podOrder) {
    if (!scored[i]) continue;
    const isMe = scored[i].name === ME;
    podHtml += '<div class="p' + (i===0?' first':'') + '">'
      + '<div class="medal">' + (medals[i]||'#'+(i+1)) + '</div>'
      + '<div class="nm">' + scored[i].name + (isMe?' ★':'') + '</div>'
      + '<div class="pt">' + scored[i].sc.total + '</div></div>';
  }
  document.getElementById('podium').innerHTML = podHtml;

  let lbHtml = '';
  for (let i=0; i<scored.length; i++) {
    const s=scored[i], isMe=s.name===ME;
    lbHtml += '<tr class="' + (isMe?'me':'') + '">'
      + '<td class="pos">' + (i+1) + '</td>'
      + '<td class="nm">' + s.name + '</td>'
      + '<td class="brk">' + s.sc.g + '/' + s.sc.k + '/' + s.sc.ind + '</td>'
      + '<td class="tot">' + s.sc.total + '</td></tr>';
  }
  document.getElementById('lbBody').innerHTML = lbHtml;

  if (me) {
    const gMap = {};
    for (const m of matches) { if (!gMap[m.g]) gMap[m.g]=[]; gMap[m.g].push(m); }
    let brkHtml='', gTot=0;
    for (const grp of Object.keys(gMap).sort()) {
      let pts=0;
      for (const m of gMap[grp]) {
        const r=(res.groups||{})[m.i], p=me.groups && me.groups[m.i];
        if (!r||!p) continue;
        const rO=sign(r[0]-r[1]), pO=sign(p[0]-p[1]);
        if (rO===pO) pts += (p[0]===r[0] && p[1]===r[1]) ? 3 : 1;
      }
      gTot+=pts;
      brkHtml += se('Grupo '+grp, pts, gMap[grp].length*3);
    }
    brkHtml += '<div class="row" style="margin-top:8px"><div class="lr" style="font-size:14px;font-weight:800"><span>Total grupos</span><span class="v">'+gTot+'</span></div></div>';
    document.getElementById('brkBox').innerHTML = brkHtml;

    let koHtml = '';
    for (const rd of ROUNDS) {
      const reached=(res.reached||{})[rd.k]||[], predicted=me[rd.k]||[];
      let hits=0, chips='';
      for (const t of predicted) {
        const hit=reached.includes(t);
        if (hit) hits++;
        const st = reached.length>0 ? (hit?'hit':'miss') : '';
        chips += '<div class="chip ' + st + '">' + (reached.length>0?(hit?'✅':'❌'):'⏳') + ' ' + es(t) + '</div>';
      }
      koHtml += '<div class="card"><div class="round-head"><span class="rt">' + rd.nstr
        + '</span><span class="rp">' + (hits*rd.p) + ' pts · ' + rd.p + 'p/equipo</span></div>'
        + '<div class="chips">' + chips + '</div></div>';
    }
    document.getElementById('koDetail').innerHTML = koHtml;

    const indItems = [
      {role:'Campeón · 10p', pred:me.champion, real:res.champion, pts:10},
      {role:'Goleador · 5p', pred:me.scorer, real:res.individuals&&res.individuals.scorer, pts:5},
      {role:'MVP · 5p', pred:me.mvp, real:res.individuals&&res.individuals.mvp, pts:5},
      {role:'Joven · 5p', pred:me.young, real:res.individuals&&res.individuals.young, pts:5}
    ];
    let indHtml='';
    for (const item of indItems) {
      const hit=item.real && item.pred===item.real, known=!!item.real;
      indHtml += '<div class="ind' + (hit?' hit':'') + '">'
        + '<div class="em">' + (hit?'✅':'⏳') + '</div>'
        + '<div class="info"><div class="role">' + item.role + '</div>'
        + '<div class="who">' + (item.pred||'—') + '</div>'
        + (known&&!hit ? '<div style="font-size:11px;color:var(--red);margin-top:2px">Real: '+item.real+'</div>' : '')
        + '</div><div class="st">' + (hit?item.pts+'pts':'?') + '</div></div>';
    }
    document.getElementById('indBox').innerHTML = indHtml;
  }

  const gMap2 = {};
  for (const m of matches) { if (!gMap2[m.g]) gMap2[m.g]=[]; gMap2[m.g].push(m); }
  let grpHtml = '';
  for (const grp of Object.keys(gMap2).sort()) {
    grpHtml += '<div class="card"><div class="gtag"><i>'+grp+'</i> Grupo '+grp+'</div>';
    for (const m of gMap2[grp]) {
      const r=(res.groups||{})[m.i], p=me&&me.groups&&me.groups[m.i];
      let pts=null, ptsClass='';
      if (r&&p) {
        const rO=sign(r[0]-r[1]), pO=sign(p[0]-p[1]);
        pts = rO===pO ? ((p[0]===r[0]&&p[1]===r[1])?3:1) : 0;
        ptsClass = pts===3?'p3':pts===1?'p1':'p0';
      }
      grpHtml += '<div class="match">'
        + '<div class="tm"><span class="nm">'+es(m.home)+'</span></div>'
        + '<div class="mid">'
        + '<div class="sc">'+(r?'<span class="real">'+r[0]+'–'+r[1]+'</span>':'<span class="none">–</span>')+'</div>'
        + (p?'<div class="pred">'+p[0]+'–'+p[1]+'</div>':'')
        + (pts!==null?'<div class="pts '+ptsClass+'">'+pts+'p</div>':'')
        + '</div>'
        + '<div class="tm away"><span class="nm">'+es(m.away)+'</span></div>'
        + '</div>';
    }
    grpHtml += '</div>';
  }
  document.getElementById('groupsBox').innerHTML = grpHtml;

  let koResHtml = '';
  for (const rd of ROUNDS) {
    const reached=(res.reached||{})[rd.k]||[], predicted=me?(me[rd.k]||[]):[];
    koResHtml += '<div class="round-head"><span class="rt">'+rd.nstr+'</span><span class="rp">'+rd.p+' pts</span></div>'
      + '<div class="chips">';
    if (reached.length>0) {
      for (const t of reached) {
        const hit=predicted.includes(t);
        koResHtml += '<div class="chip'+(hit?' hit':'')+'">'+( hit?'✅':'➖')+' '+es(t)+'</div>';
      }
    } else {
      koResHtml += '<div class="chip">⏳ Sin datos</div>';
    }
    koResHtml += '</div>';
  }
  document.getElementById('koResults').innerHTML = koResHtml;

  document.querySelectorAll('nav.tabs button').forEach(b => {
    b.onclick = () => {
      const t = b.dataset.t;
      document.querySelectorAll('nav.tabs button').forEach(x => x.classList.remove('on'));
      document.querySelectorAll('main section').forEach(s => s.classList.remove('on'));
      b.classList.add('on');
      const sec = document.getElementById(t);
      if (sec) sec.classList.add('on');
    };
  });
}

load();
</script>
</body>
</html>"""

# Combine and write
out = prefix + SUFFIX.encode('utf-8')
with open(SRC, 'wb') as f:
    f.write(out)

print(f"Written: {len(out)} bytes to {SRC}")

# Verify key strings
with open(SRC, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

checks = [
    ('function render()', 'render()'),
    ('function load()', 'load()'),
    ('querySelectorAll', 'tabs navigation'),
    ('classList.remove', 'classList'),
    ('document.getElementById', 'getElementById'),
    ('</script>', 'script close'),
    ('</html>', 'html close'),
]
all_ok = True
for needle, label in checks:
    ok = needle in content
    print(f"  {label}: {'OK' if ok else 'MISSING!'}")
    if not ok: all_ok = False

if all_ok:
    print("All checks passed!")
else:
    print("ERRORS FOUND — fix before deploying")
    sys.exit(1)
