
(function(){
// Only the item's own city button may become the docked page. Any other
// iqm2.com link on the page — the practice-page banner's link to the
// portal front door, an attachment's FileOpen URL — would dock a page
// that is not this item, and the whole walkthrough would compare our
// record against the wrong record (Dan, 2026-08-10).
var CITYA=document.querySelector(".docbtns a.citylink[href*='iqm2.com'],"
    +".docbtns a.citylink[href*='primegov.com/Portal/Meeting']");
if(!CITYA)return;                       // nothing to audit against
var CITY=CITYA.href, SUBMIT="https://audit-intake.municipalrecord.workers.dev";
// The meeting date, as our page believes it, stamped on the city link at
// build time. The dock and the questions repeat it so the auditor never
// has to carry it in their head from the screen before (Quinton,
// 2026-08-13: "I can't see on this screen what meeting we think it was
// for").
var MDATE=CITYA.getAttribute("data-mdate")||"";
// A meeting agenda is a haystack; an item page is not. When the city's
// page is the whole agenda, the auditor hunts for our item on it, so the
// deep link carries our headline's opening words as a text fragment —
// the browser highlights them if they match, and a miss just means no
// highlight (same bargain as OUT below).
var MEETING=CITY.indexOf("Portal/Meeting")>-1||CITY.indexOf("Detail_Meeting")>-1;
var SLUG=(location.pathname.split("/").pop()||"").replace(/\.html$/,"");
// The version of this page the auditor is actually looking at, stamped
// into the page at build time. It travels with the filing so the build
// can tell a current audit from one of a page that has since changed —
// an audit that names no version can never verify anything. A practice
// page is a copy carrying the original's stamp, which is harmless
// because practice files nothing.
var SHAEL=document.getElementById("crsha");
var SHA=SHAEL?(SHAEL.getAttribute("data-sha")||""):"";
// Verified pages stop inviting an audit: the button offers the reader
// what a verified page actually needs, a way to dispute it. The
// walkthrough behind both buttons is the same act — a dispute IS an
// audit that answers "no" somewhere. (.v = council mark, .ok = SC mark.)
var VERIFIED=!!document.querySelector(".audrow .v,.audrow.ok");
// The city's page opens in a small window beside the audit, not a full
// tab: the auditor is mid-walkthrough and the tab bar is where audits go
// to die (Quinton, 2026-08-13). noopener costs us window reuse across
// steps, but the city's portal never gets a handle on the audit page.
function popout(u){
  var w=Math.min(1000,Math.round(screen.width*.55)),
      h=Math.round(screen.height*.85);
  var p=window.open(u,"crcity","popup=yes,noopener,width="+w+",height="+h);
  if(p)p.focus();}
// A practice page is a copy of a real page with a mistake planted in it.
// Its walkthrough teaches every move but files nothing: an audit of a
// page that isn't the record would be a false entry in the ledger, under
// a real screen name, against a docket number that never had that
// mistake (Dan, 2026-08-10).
var PRACTICE=window.CR_PRACTICE||"";
function txt(sel){var e=document.querySelector(sel);
  return e?e.textContent.replace(/\s+/g," ").trim():"";}
// The disposition is the one phrase that appears on both our page and
// theirs — but only after our own furniture comes off. Ours reads
// "Apr 3, 2023 · <check> Order adopted as amended, 5-3 - the Council's
// request went to the City Manager"; theirs says "Order Adopted as
// Amended". So: drop the date before the middot, drop every character
// the city's plain HTML can't contain, and stop at the tally. A
// fragment that doesn't match just means no highlight, never a broken
// link — but a matching one is the whole point of the deep link.
var OUT=(function(){
  var t=txt(".ostmt");if(!t)return "";
  var p=t.split("\u00b7");
  t=p.length>1?p.slice(1).join(" "):t;
  t=t.replace(/[^\x20-\x7E]/g," ");   // emoji, en-dashes, curly quotes
  t=t.split(/[,;(]/)[0];
  return t.replace(/\s+/g," ").trim().slice(0,48);
})();
// The headline's first words, cleaned the same way: whole words only,
// because a text fragment sliced mid-word matches nothing.
var TTL=(function(){
  var t=txt("h1").replace(/[^\x20-\x7E]/g," ").replace(/\s+/g," ").trim();
  return t.split(" ").slice(0,7).join(" ");
})();
var STEPS=[
 {lab:"Headline",sel:"h1",q:(MEETING
      ? "Find this item on the city's agenda"+(MDATE?" for "+MDATE:"")
        +". Does our headline match it?"
      : "Is this headline the same item the city describes?"),
  help:"It doesn't have to match word for word. It has to be the same item, same docket number, saying the same thing.",
  frag:MEETING?TTL:"",anc:"ContentPlaceholder1_pnlMain"},
 {lab:"Outcome & date",sel:".ostmt",q:"Is the outcome and its date right?",
  help:"The official action, the tally, and the meeting date.",
  frag:OUT,anc:"ContentPlaceholder1_divHistory"},
 {lab:"Roll call",sel:".voteblock",q:"Is every name in the right column?",
  help:"A name in the wrong column is the most valuable thing you can find.",
  frag:"YEAS",anc:"ContentPlaceholder1_divHistory"},
 {lab:"City link",sel:".docbtns a.citylink",
  q:"Click the highlighted button. Does it open the city's page for this same item?",
  help:"Just the one button that's lit up, and ignore the others. It opens in a new tab, so your audit stays put. A page that opens isn't necessarily the right page: check the docket number on it.",
  frag:"",anc:""}
].filter(function(s){return document.querySelector(s.sel);});
if(STEPS.length<2)return;               // too thin a page to audit
var i=0,ans=[],spot,panel,city=null,
 // The crop rectangle (CX/CY/CW) is measured against IQM2's layout — it
 // lifts the content column out of that portal's chrome. PrimeGov puts
 // its content somewhere else entirely, so cropping a PrimeGov page by
 // those numbers slices the left edge off mid-sentence, which is exactly
 // what it did (Dan: "i couldn't read the city's page", 2026-08-12).
 // Anything that isn't IQM2 opens whole; the reader can still crop.
 ZOOM=(CITY.indexOf("iqm2.com")>-1?"crop":"full");
function el(t,c,h){var e=document.createElement(t);if(c)e.className=c;
  if(h!=null)e.innerHTML=h;return e;}
function fragUrl(f){return CITY+(f?"#:~:text="+encodeURIComponent(f):"");}
// While auditing, nothing on the page may navigate away: the last check
// asks you to click the city-website button, and following it in the same
// tab destroys the audit in progress (Dan, 2026-08-05).
function navGuard(e){
  var a=e.target&&e.target.closest?e.target.closest("a[href]"):null;
  if(!a)return;
  if(a.closest("#audpanel")||a.closest("#audcity"))return;
  var h=a.getAttribute("href");
  if(!h||h.charAt(0)==="#")return;
  e.preventDefault();e.stopPropagation();window.open(a.href,"_blank","noopener");}
function start(){i=0;ans=[];
  document.addEventListener("click",navGuard,true);
  spot=el("div");spot.id="audspot";document.body.appendChild(spot);
  panel=el("div");panel.id="audpanel";document.body.appendChild(panel);
  btn.style.display="none";render();}
function stop(){document.removeEventListener("click",navGuard,true);
  [spot,panel,city].forEach(function(n){if(n)n.remove();});
  city=null;document.body.classList.remove("audsplit");btn.style.display="";}
function toggleCity(){
  if(city){city.remove();city=null;document.body.classList.remove("audsplit");
    render();return;}
  city=el("div");city.id="audcity";
  // The date leads, in bold: it is the one fact the auditor is checking
  // this whole panel against, and it must not live only on the screen
  // before (Quinton, 2026-08-13).
  var hd=el("div","cityhd","<b>The city's record"+
 (MDATE?" \u00b7 "+MDATE:"")+"</b><span>"+
 (function(){try{return new URL(CITY).hostname;}catch(e){return "";}})()+
 "</span><span class='sp'></span>");
  var open=el("a",null,"Open in its own window \u2197");
  open.href=fragUrl(STEPS[i]&&STEPS[i].frag);
  open.target="_blank";open.rel="noopener";
  open.onclick=function(e){e.preventDefault();popout(this.href);};
  hd.appendChild(open);
  // Text-size buttons: the docked page is the city's 1280px layout
  // squeezed into half a screen, and "painfully tiny" (Quinton,
  // 2026-08-13) is not a reading experience. A\u2212/A+ rescale it.
  var zm=el("button",null,"A\u2212");zm.title="Smaller text";
  zm.onclick=function(){UZ=Math.max(.6,UZ-.15);fit();};hd.appendChild(zm);
  var zp=el("button",null,"A+");zp.title="Bigger text";
  zp.onclick=function(){UZ=Math.min(2,UZ+.15);fit();};hd.appendChild(zp);
  if(CITY.indexOf("iqm2.com")>-1){
    // the crop offsets are IQM2's; a reflowed PrimeGov page has no
    // banner to crop away, so the toggle would only break it
    var zb=el("button",null,"Whole page");zb.id="audzoom";
    zb.onclick=function(){ZOOM=(ZOOM==="crop"?"full":"crop");fit();};
    hd.appendChild(zb);}
  var cl=el("button",null,"Close");cl.onclick=toggleCity;hd.appendChild(cl);
  city.appendChild(hd);
  var wrap=el("div","framewrap");var f=el("iframe");f.id="audframe";
  f.src=cityUrl();wrap.appendChild(f);city.appendChild(wrap);
  document.body.appendChild(city);document.body.classList.add("audsplit");
  fit();render();
  // An ad-blocker that blocks third-party frames blanks this undetectably.
  setTimeout(function(){var n=el("p","apnote",
    "Blank panel? An ad-blocker may be blocking the city's frame. Use "
    + "\u201cOpen in its own window\u201d instead.");
    if(panel&&!panel.querySelector(".apnote"))panel.appendChild(n);},1800);}
function place(sel){var t=document.querySelector(sel);if(!t)return;
  var r=t.getBoundingClientRect(),top=r.top+scrollY-8,left=r.left+scrollX-8;
  spot.style.top=top+"px";spot.style.left=left+"px";
  spot.style.width=(r.width+16)+"px";spot.style.height=(r.height+16)+"px";
  // the panel sits at the bottom, so the safe band stops well above it
  var safeTop=96,safeBot=innerHeight-330;
  if(r.top<safeTop||r.bottom>safeBot){
    var want=Math.max(0,top-safeTop-16);scrollTo(0,want);
    if(Math.abs(scrollY-want)>2&&scrollY<want)
      document.documentElement.scrollTop=want;}}
function cityUrl(){var s=STEPS[i];return CITY+(s&&s.anc?"#"+s.anc:"");}
// Measured against IQM2's LegiFile layout at a 1280px viewport: the real
// content column is 746px wide at (368,195); the rest is banner and nav.
var CX=368,CY=195,CW=746,FRAME_W=1280,UZ=1;
function fit(){var f=document.getElementById("audframe");if(!f)return;
  var dock=document.getElementById("audcity");
  var w=dock.clientWidth,h=dock.clientHeight-42;
  if(ZOOM==="crop"){f.style.width=FRAME_W+"px";
    var k=(w/CW)*UZ;f.style.height=((h/k)+CY)+"px";
    f.style.transform="scale("+k+") translate("+(-CX)+"px,"+(-CY)+"px)";}
  else if(CITY.indexOf("iqm2.com")>-1){
    // IQM2's layout is a fixed 1280px: whole-page means scaling it down
    f.style.width=FRAME_W+"px";
    var k2=Math.min(1,w/FRAME_W)*UZ;f.style.height=(h/k2)+"px";
    f.style.transform="scale("+k2+")";}
  else{
    // PrimeGov's portal is responsive: give it the dock's own width and
    // it reflows to fit, at full-size text. Squeezing its 1280px desktop
    // layout down instead is what made the record "painfully tiny"
    // (Quinton, 2026-08-13). UZ>1 narrows the pretend viewport and
    // scales up, so bigger text still fills the dock edge to edge.
    var vw=Math.max(320,Math.round(w/UZ));f.style.width=vw+"px";
    f.style.height=Math.round(h/UZ)+"px";f.style.transform="scale("+UZ+")";}
  f.parentNode.style.overflowX="hidden";
  var zb=document.getElementById("audzoom");
  if(zb)zb.textContent=ZOOM==="crop"?"Whole page":"Just the record";}
function syncCity(){var f=document.getElementById("audframe");
  if(f&&f.src.split("#")[0]===CITY.split("#")[0])f.src=cityUrl();}
function render(){
  if(i>=STEPS.length)return finish();
  var s=STEPS[i];place(s.sel);syncCity();fit();panel.innerHTML="";
  var head=el("div","apstep","<span>Check "+(i+1)+" of "+STEPS.length+"</span>");
  var x=el("button","apclose","Stop");x.onclick=stop;head.appendChild(x);
  panel.appendChild(head);
  panel.appendChild(el("div","apq",s.q));
  panel.appendChild(el("p","aphelp",s.help));
  var see=el("div","apsee");
  // Dock first and loud: an auditor who never opens the city's record is
  // only checking our page against itself. Narrow screens have no room to
  // dock anything, so there the new tab IS the primary route and must not
  // be worded as the afterthought of a button that isn't there.
  var wide=innerWidth>760;
  if(wide){
    var b=el("button","sbs"+(city?" on":""),
      (city?"\u2716  Hide the city's record":"\u21c6  Show the city's record here"));
    b.onclick=toggleCity;see.appendChild(b);
  }
  var a=el("a",wide?null:"solo",
    wide?"or open it in its own window \u2197":"Open the city's record \u2197");
  a.href=fragUrl(s.frag);a.target="_blank";a.rel="noopener";
  // a small window beside the audit, not a tab behind it — phones get
  // the tab, the only thing a phone can open
  if(wide)a.onclick=function(e){e.preventDefault();popout(this.href);};
  see.appendChild(a);
  panel.appendChild(see);
  var row=el("div","apbtns");
  [["Yes","yes","yes"],["No, something's off","no","no"],["Not sure","apskip","skip"]]
   .forEach(function(bt){var btn2=el("button","apa "+bt[1],bt[0]);
     btn2.onclick=function(){answer(bt[2]);};row.appendChild(btn2);});
  panel.appendChild(row);
  panel.appendChild(el("div","apbar","<div style='width:"+(i/STEPS.length*100)+"%'></div>"));}
function answer(v){
  if(v==="no"){panel.innerHTML="";
    panel.appendChild(el("div","apstep","<span>Check "+(i+1)+" of "+STEPS.length+"</span>"));
    panel.appendChild(el("div","apq","What did you see?"));
    panel.appendChild(el("p","aphelp","Quote the city's page if you can."));
    var ta=el("textarea");ta.placeholder="The city's page says\u2026";
    panel.appendChild(ta);
    var row=el("div","apbtns");var ok=el("button","apa no","Flag it and continue");
    ok.onclick=function(){ans.push({lab:STEPS[i].lab,v:"discrepancy",note:ta.value});
      i++;render();};
    row.appendChild(ok);panel.appendChild(row);ta.focus();return;}
  ans.push({lab:STEPS[i].lab,v:v==="yes"?"confirmed":"not sure",note:""});
  i++;render();}
function tokenOf(){try{return localStorage.getItem("cr-token")||"";}
                   catch(e){return "";}}
function keep(rec){
  try{var all=JSON.parse(localStorage.getItem("mr-audits")||"[]");
    all.push(rec);localStorage.setItem("mr-audits",JSON.stringify(all));}catch(e){}}
function finish(){
  spot.style.opacity="0";panel.innerHTML="";
  panel.appendChild(el("div","apstep","<span>Done: "+STEPS.length+" of "+STEPS.length+"</span>"));
  panel.appendChild(el("div","apq",
    PRACTICE?"That's the walkthrough.":"That's the audit."));
  var ul=el("ul","apsum");
  ans.forEach(function(a){var c=a.v==="confirmed"?"ok":(a.v==="discrepancy"?"bad":"sk");
    ul.appendChild(el("li","","<span>"+a.lab+"</span><span class='"+c+"'>"+a.v+"</span>"));});
  panel.appendChild(ul);
  if(PRACTICE){
    panel.appendChild(el("p","aphelp","Practice files nothing. The "
      +"mistake on this page was planted, so an audit of it would be a "
      +"false entry. See how you did, then go audit a real page."));
    var pr=el("div","apbtns");pr.style.marginTop="12px";
    var pa=el("button","apa yes","Check the answers");
    // location.assign, never an assignment to location's href property:
    // the practice builder rewrites every same-directory link attribute
    // to ../items/, and it cannot tell a link from a line of JavaScript.
    // (Nor can the integrity gate, which reads this file as shipped, so
    // the token must not appear even in a comment.) An absolute path
    // also survives whatever directory a practice page is copied into.
    pa.onclick=function(){location.assign("/auditors/answers.html");};
    pr.appendChild(pa);
    var pd=el("button","apa apskip","Done");pd.onclick=stop;
    pr.appendChild(pd);panel.appendChild(pr);return;}
  panel.appendChild(el("p","aphelp","Pick a screen name. It goes on every page you verify."));
  var nm=el("input");nm.type="text";nm.placeholder="screen name";
  // Prefill from whichever identity exists: the auditor's own past
  // filings, else the name claimed on /work.html — one person, one name.
  try{nm.value=localStorage.getItem("mr-auditor")
      ||localStorage.getItem("cr-name")||"";}catch(e){}
  panel.appendChild(nm);
  var row=el("div","apbtns");row.style.marginTop="12px";
  var s=el("button","apa yes","Submit audit");
  s.onclick=function(){
    // The intake validates page as a bare slug and tracking as the code
    // itself; location.pathname and document.title both fail those
    // checks (slashes, the em-dash suffix), so every filing would have
    // been a 422. The slug is the filename; the code is the title's
    // leading "POR 2023-52". The token is the session minted on
    // /work.html — auditor mode has no claim card of its own, one
    // identity is the point.
    var code=(document.title.match(/^[A-Z]{2,4} \d{4}-\d+/)||[""])[0];
    var rec={page:SLUG,tracking:code||document.title.slice(0,40),
             name:nm.value.trim(),sha:SHA,
             token:tokenOf(),
             answers:ans,at:new Date().toISOString()};
    try{localStorage.setItem("mr-auditor",rec.name);}catch(e){}
    keep(rec);
    // Only a filing the intake accepted may say it was filed. The old
    // panel opened with "Filed. Thank you." on every outcome and put the
    // truth in small print underneath, so a refused audit read as a
    // finished one and the auditor walked away believing the work was in
    // (Quinton did, 2026-08-11). The headline is the outcome now.
    var done=function(filed,msg){
      panel.innerHTML="<div class='apq'>"
        +(filed?"Filed. Thank you.":"Not filed. Kept in this browser.")+"</div>"
        +(filed?"<p class='aphelp'>One audit on this page. A second reader "
                +"agreeing marks it verified.</p>":"")
        +"<p class='apnote'>"+msg+"</p>";
      if(filed){setTimeout(function(){stop();markMine();},3200);return;}
      // Every failure strands the work unless the auditor can carry it out
      // of this browser, so the copy button belongs on all of them, not
      // only on the one that can name its cause. Nor does a panel that
      // says "not filed" dismiss itself after three seconds.
      var r2=el("div","apbtns");
      var cp=el("button","apa yes","Copy my audits");
      cp.onclick=function(){
        var all=localStorage.getItem("mr-audits")||"[]";
        var ok=function(){cp.textContent="Copied. Send it to Dan.";};
        if(navigator.clipboard&&navigator.clipboard.writeText)
          navigator.clipboard.writeText(all).then(ok,function(){
            b.textContent="Copy blocked by the browser";});
        else{var t=el("textarea");t.value=all;panel.appendChild(t);
             t.select();ok();}};
      r2.appendChild(cp);
      var dn=el("button","apa apskip","Done");
      dn.onclick=function(){stop();markMine();};r2.appendChild(dn);
      panel.appendChild(r2);};
    if(!SUBMIT){done(false,"Submissions are not open yet. Copy your audits out "
      +"when you finish the round, or they stay on this machine.");return;}
    fetch(SUBMIT+"/submit",{method:"POST",headers:{"content-type":"application/json"},
      body:JSON.stringify(rec)})
      .then(function(r){
        if(r.ok){done(true,"Sent to the intake.");return;}
        done(false,r.status===401
          ?"The intake wants a claimed screen name. Claim yours once at "
            +"<a href='/work.html'>/work.html</a> and your next audit files "
            +"itself. This one is safe here: copy it out and send it to Dan."
          :"The intake refused it (error "+r.status+"). Nothing is lost: copy "
            +"your audits out, or try again later.");})
      .catch(function(){done(false,"The intake did not answer. Nothing is lost: "
        +"copy your audits out, or try again later.");});};
  row.appendChild(s);
  var c=el("button","apa apskip","Cancel");c.onclick=stop;row.appendChild(c);
  panel.appendChild(row);}
var btn=el("button","audbtn",
  PRACTICE?"Practice this page"
  :VERIFIED?"Report a problem with this page"
  :"Audit this page");
btn.id="audstart";
btn.onclick=start;document.body.appendChild(btn);
// The page remembers the audits filed from this browser. Without this,
// finishing an audit dropped you back on a page still crying "Audit this
// page" as if nothing had happened (Quinton, 2026-08-13) — the rebuilt
// site catches up later, but this browser knows now.
function myAudit(){
  try{var all=JSON.parse(localStorage.getItem("mr-audits")||"[]");
    for(var j=all.length-1;j>=0;j--)
      if(all[j].page===SLUG)return all[j];}catch(e){}
  return null;}
// Taking an audit back (2026-09-06). Before this, an audit could only
// leave the record by a third party ruling it overturned, which also
// costs its author a calibration miss — so an auditor who realised they
// had misread a page had no honest way out. This files a `retract` row
// under the same screen name (the intake checks the token holds it) and
// the next publish drops the audit from the page, the ledger and the
// scores. Nothing is deleted anywhere: the audit file stays, marked.
function retract(m,host){
  var tok="";try{tok=localStorage.getItem("cr-token")||"";}catch(e){}
  var say=function(t){host.textContent=" \u00b7 "+t;host.style.fontWeight="600";};
  if(!SUBMIT){say("Submissions are not open yet, so there is nothing to take back.");return;}
  if(!tok){host.innerHTML=" \u00b7 To take this back, sign in first on "
    +"<a href='/work.html'>the work page</a> (linked from the auditors page), then try again.";return;}
  var why=window.prompt("Take back your audit of this page? You can say why in one line, or leave it blank.","");
  if(why===null)return;
  say("Taking it back\u2026");
  var code=(document.title.match(/^[A-Z]{2,4} \d{4}-\d+/)||[""])[0];
  fetch(SUBMIT+"/submit",{method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({kind:"retract",page:SLUG,
      tracking:m.tracking||code||document.title.slice(0,40),
      name:m.name||"",sha:SHA,token:tok,reason:(why||"").slice(0,2000)})})
    .then(function(r){
      if(r.ok){
        // remember it here so the button does not come back on reload
        try{var all=JSON.parse(localStorage.getItem("mr-audits")||"[]");
          for(var j=0;j<all.length;j++)if(all[j].page===SLUG&&!all[j].retracted)
            all[j].retracted=new Date().toISOString();
          localStorage.setItem("mr-audits",JSON.stringify(all));}catch(e){}
        say("Taken back. It leaves the record on the next publish.");
        if(!VERIFIED)btn.textContent="Audit this page";
        return;}
      say(r.status===401
        ?"The intake did not recognise your sign-in. Sign in again on the work page and try once more."
        :"The intake refused it (error "+r.status+"). Nothing changed; try again later.");})
    .catch(function(){say("The intake did not answer. Nothing changed; try again later.");});}
function markMine(){
  if(PRACTICE)return;
  var m=myAudit();if(!m)return;
  var row=document.querySelector(".audrow");
  if(m.retracted){
    // already taken back from this browser: say so once, offer nothing
    if(row&&!document.getElementById("audmine")){
      var r0=el("span");r0.id="audmine";
      r0.textContent=" \u00b7 You took back your audit of this page. It leaves the record on the next publish.";
      row.appendChild(r0);}
    return;}
  if(row&&!document.getElementById("audmine")){
    var s=el("span");s.id="audmine";
    var d="";try{d=new Date(m.at).toLocaleDateString(undefined,
      {month:"short",day:"numeric",year:"numeric"});}catch(e){}
    s.textContent=" \u00b7 \u2713 You audited this page"
      +(m.name?" as "+m.name:"")+(d?" on "+d:"")+". ";
    s.style.fontWeight="600";row.appendChild(s);
    var tb=el("a");tb.href="#";tb.textContent="Take it back";
    tb.title="File a retraction of your own audit of this page";
    tb.onclick=function(e){e.preventDefault();retract(m,s);};
    s.appendChild(tb);}
  if(!VERIFIED)btn.textContent="\u2713 You audited this page";}
markMine();
// The trust row's own "audit this page" link starts the same walkthrough,
// so the page never offers two different doors to the same act.
Array.prototype.forEach.call(document.querySelectorAll("a[href='#audstart']"),
  function(a){a.addEventListener("click",function(e){e.preventDefault();start();});});
addEventListener("resize",function(){if(spot&&i<STEPS.length){place(STEPS[i].sel);fit();}});
})();
