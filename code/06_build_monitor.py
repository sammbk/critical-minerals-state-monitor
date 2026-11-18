"""Build the Critical Minerals State Monitor page from data/clean/minerals_*.

Writes dashboard/monitor/index.html (one self-contained page: national overview and
state profiles) and copies the clean CSVs to dashboard/monitor/data/ for download. The
dashboard/monitor/ folder is the published site.

    python code/06_build_monitor.py
"""

import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "dashboard" / "monitor"

NAMES = {"AK": "Alaska", "AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona", "CA": "California",
         "CO": "Colorado", "CT": "Connecticut", "DC": "District of Columbia", "DE": "Delaware",
         "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "IA": "Iowa", "ID": "Idaho",
         "IL": "Illinois", "IN": "Indiana", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
         "MA": "Massachusetts", "MD": "Maryland", "ME": "Maine", "MI": "Michigan",
         "MN": "Minnesota", "MO": "Missouri", "MS": "Mississippi", "MT": "Montana",
         "NC": "North Carolina", "ND": "North Dakota", "NE": "Nebraska", "NH": "New Hampshire",
         "NJ": "New Jersey", "NM": "New Mexico", "NV": "Nevada", "NY": "New York", "OH": "Ohio",
         "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
         "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
         "UT": "Utah", "VA": "Virginia", "VT": "Vermont", "WA": "Washington", "WI": "Wisconsin",
         "WV": "West Virginia", "WY": "Wyoming"}


def payload() -> dict:
    d = pd.read_csv(CLEAN / "minerals_state.csv")
    meta = json.loads((CLEAN / "minerals_meta.json").read_text(encoding="utf-8"))
    ind = pd.read_csv(CLEAN / "minerals_state_industry.csv")
    states = {}
    for s, g in d.groupby("state"):
        top = (ind[ind["state"] == s].groupby("industry")["user_usd"].sum()
               .sort_values(ascending=False).head(5))
        states[s] = {
            "name": NAMES[s], "gdp": float(g["gdp_usd"].iloc[0]),
            "m": {r.mineral: [round(float(r.producer_usd)), round(float(r.user_usd)),
                              r.producer_status] for r in g.itertuples()},
            "ind": [[k, round(float(v))] for k, v in top.items()],
        }
    return {"meta": meta, "states": states}


def build() -> None:
    (OUT / "data").mkdir(parents=True, exist_ok=True)
    for f in ["minerals_state.csv", "minerals_state_industry.csv", "minerals_meta.json"]:
        shutil.copy(CLEAN / f, OUT / "data" / f)
    html = TEMPLATE.replace("/*DATA*/null", json.dumps(payload(), separators=(",", ":")))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote {OUT / 'index.html'} ({len(html) / 1024:.0f} KB)")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Critical Minerals State Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>
:root{--ink:#111418;--text:#2B3138;--muted:#5B6470;--rule:#D0D4DA;--light:#E6E8EB;--navy:#12355B;--band:#0E2A47;--pad:clamp(28px,10vw,184px)}
*{box-sizing:border-box}
body{margin:0;background:#FFFFFF;color:var(--ink);font:15px/1.5 'IBM Plex Sans',Arial,sans-serif}
a{color:var(--navy)}a:hover{color:var(--ink)}
:focus-visible{outline:2px solid var(--navy);outline-offset:2px}
.wrap{max-width:1440px;margin:0 auto;padding:0 var(--pad)}
.serif{font-family:'Source Serif 4',Georgia,serif}
header.band{background:var(--band);color:#FFFFFF}
header.band .wrap{padding-top:30px;padding-bottom:28px;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:24px}
.wm{color:#FFFFFF;text-decoration:none}
.wm small{display:block;font-size:12px;font-weight:600;letter-spacing:.24em;text-transform:uppercase;color:#A9C1DE}
.wm span{display:block;font-family:'Source Serif 4',Georgia,serif;font-weight:600;font-size:40px;line-height:1;letter-spacing:-.015em;margin-top:8px}
.tag{text-align:right}.tag i{font-family:'Source Serif 4',Georgia,serif;font-size:16px;color:#DCE6F2}
.tag div{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:18px;font-size:13px;color:#C3CFDD;margin-top:8px}.tag a{color:#FFFFFF}
nav.tabs{border-bottom:1px solid var(--rule)}nav.tabs .wrap{display:flex;flex-wrap:wrap;font-size:14px;font-weight:500}
nav.tabs a{padding:12px 16px 10px 0;margin-right:16px;color:var(--text);text-decoration:none;border-bottom:3px solid transparent}
nav.tabs a[aria-current=page]{color:var(--ink);border-bottom-color:var(--navy)}
main.wrap{padding-top:36px;padding-bottom:72px;display:flex;flex-direction:column;gap:40px}
h1{font-family:'Source Serif 4',Georgia,serif;font-weight:600;font-size:34px;line-height:1.15;margin:0 0 10px}
h2{font-family:'Source Serif 4',Georgia,serif;font-weight:600;font-size:22px;margin:2px 0 4px}
.lede{margin:0;font-size:16px;line-height:1.6;color:var(--text);max-width:760px}
.top{display:flex;flex-wrap:wrap;gap:32px;justify-content:space-between}
dl.meta{flex:0 1 300px;margin:0;font-size:13px;display:grid;grid-template-columns:1fr 1fr;row-gap:8px;column-gap:16px;align-content:start;border-top:1px solid var(--rule);padding-top:10px}
dl.meta dt{color:var(--muted)}dl.meta dd{margin:0}
.controls{display:flex;flex-wrap:wrap;gap:24px;align-items:flex-end;padding:16px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.lab{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:6px}
select{min-height:40px;min-width:220px;padding:6px 10px;border:1px solid #8A929C;border-radius:0;font:500 14px 'IBM Plex Sans',Arial,sans-serif;color:var(--ink);background:#FFFFFF}
.seg{display:flex}.seg button{min-height:40px;padding:6px 16px;margin-left:-1px;border:1px solid #8A929C;border-radius:0;background:#FFFFFF;color:var(--ink);font:500 14px 'IBM Plex Sans',Arial,sans-serif;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--navy);color:#FFFFFF}
.ex{border-top:2px solid var(--ink);padding-top:12px;min-width:0}
.exn{font-size:13px;font-weight:600;color:var(--navy)}.sub{font-size:14px;color:var(--muted);margin-bottom:16px}
.cap{margin-top:14px;padding-top:8px;border-top:1px solid var(--light);font-size:12px;line-height:1.5;color:var(--muted)}
.fig1{display:grid;grid-template-columns:minmax(0,1.9fr) minmax(260px,1fr);gap:40px;align-items:start}
.two{display:grid;grid-template-columns:minmax(0,1.9fr) minmax(260px,1fr);gap:40px;align-items:start}
@media (max-width:820px){.fig1,.two{grid-template-columns:minmax(0,1fr)}}
.map{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));grid-template-rows:repeat(8,minmax(0,1fr));gap:2px;aspect-ratio:12/8.6}
.map a{display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:13px;font-weight:600;line-height:1.15;text-decoration:none}
.map a span{font-size:10.5px;font-weight:400}
.legend{display:flex;flex-wrap:wrap;align-items:center;margin-top:14px;font-size:12px;color:var(--text)}.legend i{display:inline-block;width:44px;height:10px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;font-weight:600;font-size:12px;color:var(--muted);padding:6px 0}
thead tr{border-bottom:1px solid var(--ink)}tbody tr{border-bottom:1px solid var(--light)}
td{padding:9px 0}.num{text-align:right;font-variant-numeric:tabular-nums}
.kf{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));border-top:2px solid var(--ink);border-bottom:1px solid var(--rule)}
.kf>div{padding:14px 16px 16px;border-right:1px solid var(--rule)}.kf>div:first-child{padding-left:0}.kf>div:last-child{border-right:0}
.kf .l{font-size:12px;color:var(--muted)}.kf .v{font-family:'Source Serif 4',Georgia,serif;font-size:30px;font-weight:600;font-variant-numeric:tabular-nums}
.pending{border:1px solid var(--rule);padding:20px;font-size:14px;color:var(--text);line-height:1.6}
footer{border-top:1px solid var(--rule);padding-top:16px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;font-size:12px;color:var(--muted)}
[hidden]{display:none!important}
</style>
</head>
<body>
<header class="band"><div class="wrap">
<a class="wm" href="#overview"><small>Critical Minerals</small><span>State Monitor</span></a>
<div class="tag"><i>Price risk and price policy across the 50 states and the District of Columbia</i>
<div><span>Release 1.0</span><span id="thru"></span><a href="#methods">Methods</a><a href="data/minerals_state.csv">Data</a></div></div>
</div></header>
<nav class="tabs" aria-label="Primary"><div class="wrap">
<a href="#overview" data-v="overview">National overview</a><a href="#state" data-v="state">States</a>
<a href="#overview-pass" data-v="overview">Pass-through</a><a href="#overview-policy" data-v="overview">Policy scenarios</a>
<a href="#methods" data-v="overview">Methods and data</a></div></nav>

<main class="wrap" id="v-overview">
<section class="top"><div style="flex:1 1 620px;min-width:0"><h1>National overview</h1>
<p class="lede">Each state's exposure to world prices for six critical metals, measured on two sides: as a producer, from the value of its mine output, and as a user, from the metal content of its industries. Release 1.0 covers aluminum, copper, lead, nickel, tin and zinc.</p></div>
<dl class="meta"><dt>Prices through</dt><dd id="m-thru"></dd><dt>State GDP year</dt><dd id="m-gdp"></dd><dt>Coverage</dt><dd>51 jurisdictions, 6 metals</dd><dt>Frequency</dt><dd>Monthly prices</dd></dl></section>

<section class="controls" aria-label="Selections">
<div><label class="lab" for="mineral">Mineral</label><br><select id="mineral"></select></div>
<div><div class="lab" id="measure-l">Measure</div><div class="seg" role="group" aria-labelledby="measure-l" id="measure"></div></div>
</section>

<section class="fig1">
<figure class="ex" style="margin:0"><div class="exn">Figure 1</div><h2 id="f1t"></h2><div class="sub" id="f1s"></div>
<div class="map" id="map" role="img"></div><div class="legend" id="legend"></div>
<figcaption class="cap" id="f1c"></figcaption></figure>
<div class="ex"><div class="exn">Table 1</div><h2>Largest exposures</h2>
<table><thead><tr><th style="width:28px">#</th><th>State</th><th class="num" id="t1h"></th></tr></thead><tbody id="t1"></tbody></table>
<div class="kf" style="margin-top:20px;border-top:1px solid var(--rule)"><div><div class="l">World price, 12-month average change</div><div class="v" id="k1"></div><div class="l" id="k1s"></div></div>
<div><div class="l">States with a net gain</div><div class="v" id="k2"></div><div class="l">from a 10% price rise</div></div></div>
</div></section>

<section class="ex"><div class="exn">Table 2</div><h2>The six metals at a glance</h2><div class="sub">United States; values at the latest 12-month average world price</div>
<div style="overflow-x:auto"><table><thead><tr><th>Metal</th><th class="num">Price, $/t</th><th class="num">Change from prior 12 months</th><th class="num">U.S. use, $ billion</th><th class="num">State-reported mine output, $ billion</th><th style="padding-left:16px">Producer data</th></tr></thead><tbody id="t2"></tbody></table></div>
<div class="cap">Source: World Bank monthly prices; U.S. Geological Survey, Minerals Yearbook and Mineral Commodity Summaries 2026; author's calculations.</div></section>

<section class="ex" id="overview-pass"><div class="exn">Figure 2</div><h2>Pass-through of a mineral price surprise</h2>
<div class="pending">Estimates of how mineral price surprises move U.S. producer prices, industrial production, state employment and personal income will appear here with the first working paper. They are not shown until they are estimated.</div></section>

<section class="ex" id="overview-policy"><h2>Policy scenarios</h2>
<div class="pending">A tool for price floors and stockpile purchases and releases, with each state's gain and cost, is in development for release 1.1.</div></section>

<section class="ex" id="methods"><h2>Methods and data</h2><div class="two"><div>
<p style="margin:0 0 10px;font-size:14px;line-height:1.6;color:var(--text)"><b>Producer exposure</b> is the value of mine output at the latest 12-month average world price. Copper is summed by state from the leading mines in the USGS Minerals Yearbook 2022 (table 2); zinc is Alaska's output (table 2); nickel is Michigan's Eagle mine, the only U.S. nickel mine (2024). Where USGS withholds a producing state's figure (copper in Montana and Missouri; zinc in Idaho, Missouri, New York and Tennessee; lead in Missouri, Alaska and Idaho) it is excluded, never imputed. Primary aluminum output by state is not compiled in this release; the United States has no tin mine.</p>
<p style="margin:0 0 10px;font-size:14px;line-height:1.6;color:var(--text)"><b>User exposure</b> sets each metal's national total at 2024 U.S. apparent consumption (USGS) times the current price, and allocates it across states by each state's real industry output times the 2017 BEA input-output purchases of that metal per dollar of output, excluding the mining, smelting and mill industries themselves. Nickel, lead, zinc and tin share one input-output category and so share one state allocation in this release.</p>
<p style="margin:0;font-size:14px;line-height:1.6;color:var(--text)"><b>Net effect</b> of a 10% world price rise is one tenth of producer minus user value, as a percent of state GDP. It is a first-round accounting measure, not an estimate of final outcomes.</p></div>
<div><div class="lab">Downloads</div><ul style="margin:0;padding:0;list-style:none;font-size:14px;line-height:2">
<li><a href="data/minerals_state.csv">State exposure by metal (CSV)</a></li><li><a href="data/minerals_state_industry.csv">State user exposure by industry (CSV)</a></li><li><a href="data/minerals_meta.json">Prices and build metadata (JSON)</a></li><li><a href="https://github.com/sammbk/critical-minerals-state-monitor">Source code and release history</a></li></ul></div></div></section>
<footer><div>Critical Minerals State Monitor, by Samson M'boueke. Built from public data. Not an official statistic. <a href="https://github.com/sammbk/critical-minerals-state-monitor">Source code</a></div><div>Release 1.0, November 18, 2026</div></footer>
</main>

<main class="wrap" id="v-state" hidden>
<div class="top" style="align-items:flex-end"><div style="flex:1 1 600px;min-width:0"><div style="font-size:13px;color:var(--muted)"><a href="#overview">National overview</a> / States</div><h1 id="s-name" style="margin-top:6px"></h1><p class="lede" id="s-lede"></p></div>
<div><label class="lab" for="state-pick">State</label><br><select id="state-pick"></select></div></div>
<section class="kf" aria-label="Key figures"><div><div class="l">Exposure as a producer</div><div class="v" id="s-k1" style="color:#1A4378"></div><div class="l" id="s-k1s"></div></div>
<div><div class="l">Exposure as a user</div><div class="v" id="s-k2" style="color:#7A3E0E"></div><div class="l" id="s-k2s"></div></div>
<div><div class="l">Net effect of a 10% price rise</div><div class="v" id="s-k3"></div><div class="l" id="s-k3s"></div></div></section>
<section class="two"><div class="ex"><div class="exn">Table 3</div><h2>Exposure by metal</h2><div class="sub">Percent of state GDP exposed, and net effect of a 10% rise in each metal's world price</div>
<div style="overflow-x:auto"><table><thead><tr><th>Metal</th><th class="num" style="color:#7A3E0E;padding-right:8px">As a user</th><th style="color:#1A4378;padding-left:8px">As a producer</th><th class="num">Net</th></tr></thead><tbody id="s-t"></tbody></table></div>
<div class="cap" id="s-cap"></div></div>
<div class="ex"><div class="exn">Table 4</div><h2>Most exposed industries</h2>
<table><thead><tr><th>Industry</th><th class="num">Metal use, $ million</th></tr></thead><tbody id="s-ind"></tbody></table>
<div class="cap">All six metals; value at the latest 12-month average price.</div></div></section>
<footer><div>Critical Minerals State Monitor, by Samson M'boueke. Built from public data. Not an official statistic. <a href="https://github.com/sammbk/critical-minerals-state-monitor">Source code</a></div><div>Release 1.0, November 18, 2026</div></footer>
</main>

<script>
const D=/*DATA*/null;
const MIN=['all','aluminum','copper','lead','nickel','tin','zinc'];
const LBL={all:'All six metals',aluminum:'Aluminum',copper:'Copper',lead:'Lead',nickel:'Nickel',tin:'Tin',zinc:'Zinc'};
const TILES=[['AK',1,1],['ME',12,1],['VT',11,2],['NH',12,2],['WA',2,3],['ID',3,3],['MT',4,3],['ND',5,3],['MN',6,3],['IL',7,3],['WI',8,3],['MI',9,3],['NY',10,3],['RI',11,3],['MA',12,3],['OR',2,4],['NV',3,4],['WY',4,4],['SD',5,4],['IA',6,4],['IN',7,4],['OH',8,4],['PA',9,4],['NJ',10,4],['CT',11,4],['CA',2,5],['UT',3,5],['CO',4,5],['NE',5,5],['MO',6,5],['KY',7,5],['WV',8,5],['VA',9,5],['MD',10,5],['DE',11,5],['AZ',3,6],['NM',4,6],['KS',5,6],['AR',6,6],['TN',7,6],['NC',8,6],['SC',9,6],['DC',10,6],['OK',5,7],['LA',6,7],['MS',7,7],['AL',8,7],['GA',9,7],['HI',1,8],['TX',5,8],['FL',10,8]];
const BLUE=['#DCE6F2','#A9C1DE','#6F95C4','#3A69A6','#1A4378'],ORNG=['#F6E3D3','#EDBE96','#DE8F57','#A85A1C','#7A3E0E'];
const S={mineral:'all',measure:'net'};
const $=id=>document.getElementById(id);
function vals(s,m){const x=D.states[s];let p=0,u=0,w=false;const ms=m==='all'?MIN.slice(1):[m];
 for(const k of ms){const r=x.m[k];p+=r[0];u+=r[1];if(r[2]==='withheld')w=true}return{p,u,g:x.gdp,w}}
function measure(s){const v=vals(s,S.mineral);return S.measure==='producer'?100*v.p/v.g:S.measure==='user'?100*v.u/v.g:10*(v.p-v.u)/v.g}
const minus=t=>t.replace('-','−');
function fmt(v,dp){const t=Math.abs(v).toFixed(dp);if(Number(t)===0)return t;return(S.measure==='net'&&v>0?'+':'')+minus((v<0?'-':'')+t)}
function bin(r){return r<.08?0:r<.2?1:r<.4?2:r<.65?3:4}
function overview(){
 const rows=TILES.map(t=>({c:t[0],v:measure(t[0]),w:vals(t[0],S.mineral).w}));const mx=Math.max(...rows.map(r=>Math.abs(r.v)))||1;
 const dp=mx<0.1?3:2;
 $('map').innerHTML=TILES.map((t,i)=>{const r=rows[i],q=Math.abs(r.v)/mx;let f;
  if(S.measure==='producer')f=r.v===0?'#F1F2F4':BLUE[bin(q)];else if(S.measure==='user')f=ORNG[bin(q)];else f=q<.05?'#ECEEF1':(r.v>=0?BLUE[bin(q)]:ORNG[bin(q)]);
  const ink=[BLUE[3],BLUE[4],ORNG[3],ORNG[4]].includes(f)?'#FFFFFF':'#111418';
  return `<a href="#state-${t[0]}" style="grid-column:${t[1]};grid-row:${t[2]};background:${f};color:${ink}" aria-label="${D.states[t[0]].name}: ${fmt(r.v,dp)} percent">${t[0]}${r.w&&S.measure!=='user'?'*':''}<span>${fmt(r.v,dp)}</span></a>`}).join('');
 const T={net:'Net effect of a 10% price rise',producer:'Exposure as a producer',user:'Exposure as a user'}[S.measure];
 $('f1t').textContent=T+', '+LBL[S.mineral].toLowerCase();$('f1s').textContent='Percent of state GDP';
 $('map').setAttribute('aria-label','Tile map of the 50 states and DC: '+T.toLowerCase());
 const lg=S.measure==='producer'?BLUE:S.measure==='user'?ORNG:[ORNG[4],ORNG[2],'#ECEEF1',BLUE[2],BLUE[4]];
 $('legend').innerHTML=`<span style="margin-right:10px">${S.measure==='net'?'Net loss':'Lower'}</span>`+lg.map(c=>`<i style="background:${c}"></i>`).join('')+`<span style="margin-left:10px">${S.measure==='net'?'Net gain':'Higher'}</span>`;
 const note={net:'Net effect: one tenth of producer value minus user value.',producer:'Producer exposure: value of mine output.',user:'User exposure: metal content of industries outside the mining and smelting chain.'}[S.measure];
 $('f1c').textContent='Note: tile map; each state is drawn at the same size. '+note+' * Producing state whose value USGS withholds; excluded. Source: author’s calculations from U.S. Geological Survey, Bureau of Economic Analysis and World Bank data.';
 $('t1h').textContent='% of GDP';
 $('t1').innerHTML=rows.filter(r=>Number(Math.abs(r.v).toFixed(dp))>0).sort((a,b)=>Math.abs(b.v)-Math.abs(a.v)).slice(0,8).map((r,i)=>`<tr><td style="color:var(--muted)">${i+1}</td><td><a href="#state-${r.c}" style="color:#111418">${D.states[r.c].name}</a></td><td class="num">${fmt(r.v,dp)}</td></tr>`).join('');
 const pc=D.meta.price_change_12m_pct,wu=D.meta.national_user_usd;const tw=MIN.slice(1).reduce((a,m)=>a+wu[m],0);const k=S.mineral==='all'?MIN.slice(1).reduce((a,m)=>a+pc[m]*wu[m],0)/tw:pc[S.mineral];
 $('k1').textContent=minus((k>0?'+':'')+k.toFixed(1)+'%');
 $('k1s').textContent=S.mineral==='all'?'Six metals, weighted by U.S. use':LBL[S.mineral]+', World Bank monthly';
 const gain=TILES.filter(t=>{const v=vals(t[0],S.mineral);return v.p-v.u>0}).length;$('k2').textContent=gain+' of 51';
 document.querySelectorAll('#measure button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.k===S.measure))}
function table2(){const m=D.meta,u=m.national_user_usd,p=m.national_producer_reported_usd;
 const note={aluminum:'By state not compiled',copper:'Leading mines, 2022; MT, MO withheld',lead:'Withheld by state',nickel:'Michigan, 2024',tin:'No U.S. mine',zinc:'Alaska only, 2022'};
 $('t2').innerHTML=MIN.slice(1).map(k=>`<tr><td>${LBL[k]}</td><td class="num">${Math.round(m.price_now_12m_avg[k]).toLocaleString('en-US')}</td><td class="num">${minus((m.price_change_12m_pct[k]>0?'+':'')+m.price_change_12m_pct[k].toFixed(1)+'%')}</td><td class="num">${(u[k]/1e9).toFixed(2)}</td><td class="num">${(p[k]/1e9).toFixed(2)}</td><td style="padding-left:16px;color:var(--muted)">${note[k]}</td></tr>`).join('')}
function rank(s,f){const arr=Object.keys(D.states).map(c=>[c,f(c)]).sort((a,b)=>b[1]-a[1]);return arr.findIndex(a=>a[0]===s)+1}
function state(s){const x=D.states[s];$('state-pick').value=s;$('s-name').textContent=x.name;
 const v=vals(s,'all'),pp=100*v.p/v.g,uu=100*v.u/v.g,nn=10*(v.p-v.u)/v.g;
 const big=Object.entries(x.m).sort((a,b)=>b[1][1]-a[1][1])[0][0];
 $('s-lede').textContent=(v.p>0?'A mineral producer and a mineral user. ':'A mineral user with no reported mine output in these metals. ')+'Its largest exposure as a user is '+LBL[big].toLowerCase()+'.';
 $('s-k1').textContent=pp.toFixed(3)+'%';$('s-k1s').textContent='of state GDP; rank '+rank(s,c=>{const q=vals(c,'all');return q.p/q.g})+' of 51';
 $('s-k2').textContent=uu.toFixed(3)+'%';$('s-k2s').textContent='of state GDP; rank '+rank(s,c=>{const q=vals(c,'all');return q.u/q.g})+' of 51';
 $('s-k3').textContent=minus((nn>0?'+':'')+nn.toFixed(3)+'%');$('s-k3s').textContent='of state GDP; about '+minus((nn<0?'-':'+')+'$'+Math.abs(Math.round(0.1*(v.p-v.u)/1e6)).toLocaleString('en-US'))+' million';
 const mx=Math.max(...MIN.slice(1).map(k=>Math.max(x.m[k][0],x.m[k][1])))||1;
 $('s-t').innerHTML=MIN.slice(1).map(k=>{const r=x.m[k],n=10*(r[0]-r[1])/x.gdp;const st=r[2]==='withheld'?' (producer value withheld)':r[2]==='not compiled'?'':'';
  return `<tr><th scope="row" style="font-weight:500;font-size:14px;color:#111418;padding:10px 0">${LBL[k]}<span style="color:var(--muted);font-weight:400">${st}</span></th><td style="border-right:1px solid #111418"><div style="display:flex;justify-content:flex-end"><div style="height:12px;width:${(100*r[1]/mx).toFixed(1)}%;background:#A85A1C"></div></div></td><td><div style="height:12px;width:${(100*r[0]/mx).toFixed(1)}%;background:#3A69A6"></div></td><td class="num">${minus((n>0?'+':'')+n.toFixed(4))}</td></tr>`}).join('');
 $('s-cap').textContent='Note: bars share one scale. Aluminum producer output by state is not compiled in this release. Source: author’s calculations from U.S. Geological Survey, Bureau of Economic Analysis and World Bank data.';
 $('s-ind').innerHTML=x.ind.map(i=>`<tr><td>${i[0]}</td><td class="num">${Math.round(i[1]/1e6).toLocaleString('en-US')}</td></tr>`).join('')}
function route(){const h=location.hash.slice(1);const st=h.startsWith('state');$('v-overview').hidden=st;$('v-state').hidden=!st;
 document.querySelectorAll('nav.tabs a').forEach(a=>a.removeAttribute('aria-current'));document.querySelector(`nav.tabs a[data-v=${st?'state':'overview'}]`).setAttribute('aria-current','page');
 if(st){const c=h.split('-')[1]||'MI';state(D.states[c]?c:'MI');window.scrollTo(0,0)}}
function init(){$('thru').textContent='Prices through '+D.meta.prices_through;$('m-thru').textContent=D.meta.prices_through;$('m-gdp').textContent=D.meta.gdp_year;
 $('mineral').innerHTML=MIN.map(k=>`<option value="${k}">${LBL[k]}</option>`).join('');$('mineral').onchange=e=>{S.mineral=e.target.value;overview()};
 $('measure').innerHTML=[['net','Net'],['producer','As a producer'],['user','As a user']].map(x=>`<button type="button" data-k="${x[0]}">${x[1]}</button>`).join('');
 document.querySelectorAll('#measure button').forEach(b=>b.onclick=()=>{S.measure=b.dataset.k;overview()});
 $('state-pick').innerHTML=Object.keys(D.states).sort((a,b)=>D.states[a].name.localeCompare(D.states[b].name)).map(c=>`<option value="${c}">${D.states[c].name}</option>`).join('');
 $('state-pick').onchange=e=>{location.hash='state-'+e.target.value};
 overview();table2();window.onhashchange=route;route()}
init();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
