
(function(){
var D=window.DX||{},rows=D.rows||[],cols=D.cols||[];
var q=document.getElementById("dxq"),tb=document.getElementById("dxb"),
    cnt=document.getElementById("dxn"),more=document.getElementById("dxm"),
    head=document.getElementById("dxh");
var sortCol=-1,sortDir=1,shown=0,view=rows,PAGE=200;
var COLL=(window.Intl&&Intl.Collator)
  ?new Intl.Collator(undefined,{numeric:true,sensitivity:"base"}):null;
function CMP(x,y){return COLL?COLL.compare(x,y):(x<y?-1:x>y?1:0);}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c];});}
// Columns holding an identifier or a short verdict, by header name.
var NARROW={"date":1,"item":1,"term":1,"role":1,"from":1,"to":1,
            "tally":1,"minutes":1,"source":1,"attribution":1,
            "items":1,"no.":1};
var WIDE={"voted yes":1,"voted no":1,"absent":1,"voted present":1,
          "sponsors":1,"why not":1,"how we know":1,"title":1};
var CLS=cols.map(function(c){var k=String(c).toLowerCase();
  return NARROW[k]?" class='nw'":WIDE[k]?" class='wide'":"";});
// Columns whose values are categories: clicking one filters the table to
// it, which is how a reader moves from "every body" to "this body"
// without learning a query language (Dan, 2026-09-10).
var FILTER={"body":1,"committee":1,"source":1,"attribution":1,"role":1,
            "minutes":1,"term":1,"section":1,"sponsors":1,"note":1};
var FILTERCOL=cols.map(function(c){return FILTER[String(c).toLowerCase()]?1:0;});
function draw(reset){
  if(reset){tb.innerHTML="";shown=0;}
  var frag=document.createDocumentFragment();
  var end=Math.min(shown+PAGE,view.length);
  for(var i=shown;i<end;i++){
    var tr=document.createElement("tr");
    tr.innerHTML=view[i].map(function(c,j){
      var inner;
      // A cell carrying {f:[...]} holds several categories at once — the
      // councillors who filed one order. Each name filters on its own;
      // filtering on the joined string would match only that exact
      // combination of sponsors (Dan, 2026-09-10).
      if(c&&typeof c==="object"&&!Array.isArray(c)&&c.f){
        inner=c.f.map(function(v){
          return "<a href='#' class='fx' data-v='"+esc(v)+"'>"+esc(v)+
                 "</a>";}).join("<span class='sep'>·</span>");
      }else{
        var t=Array.isArray(c)?c[0]:c, h=Array.isArray(c)?c[1]:'';
        inner=h?("<a href='"+esc(h)+"'>"+esc(t)+"</a>")
          :(FILTERCOL[j]&&t?("<a href='#' class='fx' data-v='"
                             +esc(t)+"'>"+esc(t)+"</a>"):esc(t));
      }
      return "<td"+(CLS[j]||"")+">"+inner+"</td>";}).join("");
    frag.appendChild(tr);
  }
  tb.appendChild(frag);shown=end;
  cnt.textContent=view.length.toLocaleString()+" of "+
    rows.length.toLocaleString()+" rows"+
    (shown<view.length?", showing "+shown.toLocaleString():"");
  more.style.display=shown<view.length?"":"none";
  if(!view.length&&!tb.querySelector(".dx-empty"))
    tb.innerHTML='<tr><td class="dx-empty" colspan="'+cols.length+
      '">Nothing matches that.</td></tr>';
}
function apply(){
  var t=(q.value||"").toLowerCase().trim();
  function txt(c){
    if(c&&typeof c==="object"&&!Array.isArray(c))
      return c.f?c.f.join(" "):(c[0]||"");
    return Array.isArray(c)?c[0]:c;}
  view=t?rows.filter(function(r){
    return r.map(txt).join(" ").toLowerCase().indexOf(t)>-1;}):rows.slice();
  // numeric:true so "#26" sorts before "#260" instead of between it and
  // "#259" — a column of docket numbers in text order reads as a
  // scrambled record (Dan, 2026-09-09)
  if(sortCol>-1)view.sort(function(a,b){
    return CMP(txt(a[sortCol])||"",txt(b[sortCol])||"")*sortDir;});
  draw(true);
}
head.querySelectorAll("th").forEach(function(th,i){
  th.onclick=function(){
    sortDir=(sortCol===i)?-sortDir:1;sortCol=i;
    head.querySelectorAll("th .ar").forEach(function(a){a.textContent="";});
    th.querySelector(".ar").textContent=sortDir>0?"\u2191":"\u2193";
    apply();};
});
q.oninput=apply;
tb.addEventListener("click",function(e){
  var a=e.target.closest&&e.target.closest("a.fx");
  if(!a)return;
  e.preventDefault();q.value=a.getAttribute("data-v")||"";apply();
  window.scrollTo({top:0,behavior:"smooth"});});
more.querySelector("button").onclick=function(){draw(false);};
apply();
})();
