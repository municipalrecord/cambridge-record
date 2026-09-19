
(function(){
var form=document.getElementById("giveform");
if(!form)return;
// Real Stripe checkout-session creation is server-side and has to live
// behind a Worker, the same way audit intake does (audit.js's SUBMIT) —
// there is no payments backend in this repo yet. This endpoint is the
// contract that Worker needs to satisfy: POST {amount_cents, interval},
// respond 200 {url: "<stripe checkout session url>"} on success.
var INTAKE="https://pay-intake.municipalrecord.workers.dev";
var amtGroup=form.querySelectorAll("input[name=amt]"),
    freqGroup=form.querySelectorAll("input[name=freq]"),
    customWrap=document.getElementById("customwrap"),
    customInput=document.getElementById("customamt"),
    summary=document.getElementById("paysummary"),
    btn=document.getElementById("paybtn"),
    err=document.getElementById("payerr");

function onGroup(inputs,fn){
  for(var i=0;i<inputs.length;i++)inputs[i].addEventListener("change",fn);}
// :has() covers the highlight in every current browser; the class keeps
// the same look on anything older without it (belt and suspenders, not
// a fallback we're relying on to fire alone).
function paintOn(inputs){
  for(var i=0;i<inputs.length;i++)
    inputs[i].closest("label").classList.toggle("on",inputs[i].checked);}

function amount(){
  var picked=form.querySelector("input[name=amt]:checked");
  if(!picked)return 0;
  if(picked.value!=="other")return parseInt(picked.value,10);
  var n=parseFloat(customInput.value);
  return (n>0&&isFinite(n))?Math.round(n):0;}

function frequency(){
  var picked=form.querySelector("input[name=freq]:checked");
  return picked?picked.value:"once";}

function fmt(n){return "$"+n.toLocaleString("en-US");}

function refresh(){
  paintOn(amtGroup);paintOn(freqGroup);
  var other=form.querySelector("input[name=amt]:checked").value==="other";
  customWrap.hidden=!other;
  var amt=amount(),freq=frequency();
  summary.innerHTML=amt>0
    ?(freq==="monthly"
      ?"You're giving <b>"+fmt(amt)+"</b> a month. Cancel any time."
      :"You're giving <b>"+fmt(amt)+"</b> once.")
    :"Pick an amount to continue.";
  btn.disabled=!(amt>0);}

// Only the amount group's own change should ever move focus — toggling
// one-time/monthly must never yank focus off whatever the reader just
// clicked, even while "Other" is the standing amount pick.
onGroup(amtGroup,function(){
  refresh();
  if(this.value==="other")customInput.focus();});
onGroup(freqGroup,refresh);
customInput.addEventListener("input",refresh);
refresh();

form.addEventListener("submit",function(e){
  e.preventDefault();
  var amt=amount();
  if(!(amt>0))return;
  err.hidden=true;
  btn.disabled=true;btn.textContent="Redirecting to checkout…";
  fetch(INTAKE+"/create-checkout-session",{method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify({amount_cents:amt*100,interval:frequency()})})
    .then(function(r){
      if(!r.ok)throw new Error("status "+r.status);
      return r.json();})
    .then(function(data){
      if(!data||!data.url)throw new Error("no checkout url");
      location.href=data.url;})
    .catch(function(){
      btn.disabled=false;btn.textContent="Continue to secure checkout →";
      err.hidden=false;
      err.innerHTML="Checkout isn't reachable right now. Nothing was "
        +"charged. Try again in a moment, or "
        +"<a href='mailto:corrections@municipalrecord.org?subject=Supporting%20the%20Record'>"
        +"email us</a> and we'll sort it out directly.";});
});
})();
