"""Seiten-Bausteine für «Das ändert sich», Wochenrückblicke und HR-Rechner. Wird von build.py importiert."""
from datetime import date, datetime, timedelta

RECHNER = [
    ("kuendigung", "Kündigungsfrist & Sperrfrist", "Wann endet das Arbeitsverhältnis? Mit Probezeit, Dienstjahren und Verlängerung durch Krankheit oder Unfall (Art. 335b, 335c, 336c OR).", "arbeitsrecht"),
    ("lohnfortzahlung", "Lohnfortzahlung bei Krankheit", "Wie lange muss der Lohn weiterbezahlt werden? Nach Berner, Zürcher oder Basler Skala (Art. 324a OR).", "lohn"),
    ("ferien", "Ferienanspruch pro rata", "Ferientage bei Ein- oder Austritt unter dem Jahr und bei Teilzeit (Art. 329a OR).", "gesundheit"),
    ("bvg", "BVG-Check", "Ist der Lohn BVG-pflichtig, wie hoch ist der koordinierte Lohn und die minimale Altersgutschrift? Werte 2026 und 2027.", "praxis"),
]


def iso_week(iso):
    y, w, _ = datetime.strptime(iso, "%Y-%m-%d").isocalendar()
    return f"{y}-{w:02d}"


def week_range(wid):
    y, w = (int(x) for x in wid.split("-"))
    mon = date.fromisocalendar(y, w, 1)
    return mon, mon + timedelta(days=6)


# ---------------- Rechner: gemeinsame JS-Helfer ----------------
JS_HELPERS = r"""
function $(id){return document.getElementById(id);}
function parseD(v){if(!v)return null;var p=v.split('-');return new Date(Date.UTC(+p[0],+p[1]-1,+p[2]));}
function fmt(d){return ('0'+d.getUTCDate()).slice(-2)+'.'+('0'+(d.getUTCMonth()+1)).slice(-2)+'.'+d.getUTCFullYear();}
function addDays(d,n){return new Date(d.getTime()+n*86400000);}
function diffDays(a,b){return Math.round((b.getTime()-a.getTime())/86400000);}
function addMonths(d,n){var y=d.getUTCFullYear(),m=d.getUTCMonth()+n,day=d.getUTCDate();var t=new Date(Date.UTC(y,m+1,0));return new Date(Date.UTC(t.getUTCFullYear(),t.getUTCMonth(),Math.min(day,t.getUTCDate())));}
function endOfMonth(d){return new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0));}
function dienstjahr(start,d){var n=0;while(addMonths(start,12*(n+1))<=d)n++;return n+1;}
function anniversary(start,n){return addMonths(start,12*n);}
function out(id,html){var el=$(id);el.innerHTML=html;el.hidden=false;}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function chf(n){return 'CHF '+Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,"'");}
"""

KUENDIGUNG_FORM = """
<form class="calc" id="f" novalidate>
  <div class="calc-grid">
    <div class="field"><label for="start">Eintrittsdatum</label><input type="date" id="start" required></div>
    <div class="field"><label for="notice">Kündigung zugegangen am</label><input type="date" id="notice" required><small>Massgebend ist der Zugang beim Empfänger, nicht das Versanddatum.</small></div>
    <div class="field"><label for="probe">Probezeit</label><select id="probe"><option value="0">keine</option><option value="1" selected>1 Monat (gesetzlich)</option><option value="2">2 Monate</option><option value="3">3 Monate</option></select></div>
    <div class="field"><label for="who">Wer kündigt?</label><select id="who"><option value="ag">Arbeitgeber</option><option value="an">Arbeitnehmer/in</option></select></div>
    <div class="field"><label for="frist">Kündigungsfrist</label><select id="frist"><option value="0" selected>gesetzlich (Art. 335c OR)</option><option value="1">1 Monat (vertraglich)</option><option value="2">2 Monate (vertraglich)</option><option value="3">3 Monate (vertraglich)</option><option value="4">4 Monate (vertraglich)</option><option value="6">6 Monate (vertraglich)</option></select></div>
    <div class="field"><label for="termin">Kündigungstermin</label><select id="termin"><option value="me" selected>auf Ende eines Monats</option><option value="any">auf jeden Tag (nur wenn vereinbart)</option></select></div>
  </div>
  <fieldset class="calc-opt"><legend>Krankheit oder Unfall der Arbeitnehmerin/des Arbeitnehmers (optional)</legend>
    <p class="hint">Nur relevant, wenn der Arbeitgeber kündigt. Eine Arbeitsunfähigkeit eingeben; Schwangerschaft und Militärdienst sind nicht abgebildet.</p>
    <div class="calc-grid">
      <div class="field"><label for="au1">arbeitsunfähig ab</label><input type="date" id="au1"></div>
      <div class="field"><label for="au2">bis und mit</label><input type="date" id="au2"></div>
    </div>
  </fieldset>
  <button class="btn red" type="submit">Berechnen</button>
</form>
<div class="calc-result" id="res" hidden aria-live="polite"></div>
"""

KUENDIGUNG_JS = r"""
$('f').addEventListener('submit',function(ev){ev.preventDefault();
  var start=parseD($('start').value),notice=parseD($('notice').value);
  if(!start||!notice){out('res','<p class="warn">Bitte Eintrittsdatum und Zugang der Kündigung eingeben.</p>');return;}
  if(notice<start){out('res','<p class="warn">Die Kündigung ging vor Stellenantritt zu. Ob die Frist ab Zugang oder ab Stellenantritt läuft, wird von den Kantonen unterschiedlich gehandhabt. Dieser Fall wird hier nicht berechnet.</p>');return;}
  var probe=+$('probe').value,who=$('who').value,fv=+$('frist').value,me=$('termin').value==='me'||fv===0;
  var steps=[];var probeEnd=probe?addDays(addMonths(start,probe),-1):null;
  if(probe&&notice<=probeEnd){
    var end=addDays(notice,7);
    steps.push('Die Kündigung ging am '+fmt(notice)+' und damit in der Probezeit zu (Probezeit bis '+fmt(probeEnd)+').');
    steps.push('In der Probezeit gilt eine Frist von 7 Tagen auf jeden beliebigen Tag (Art. 335b Abs. 1 OR), sofern nichts anderes vereinbart ist.');
    steps.push('Sperrfristen nach Art. 336c OR gelten in der Probezeit nicht.');
    out('res','<p class="big">Letzter Arbeitstag: <b>'+fmt(end)+'</b></p><ol>'+steps.map(function(s){return '<li>'+s+'</li>';}).join('')+'</ol><p class="hint">Hinweis: War die Person während der Probezeit krank, verlängert sich die Probezeit entsprechend (Art. 335b Abs. 3 OR). Das ist hier nicht berücksichtigt.</p>');return;}
  var dj=dienstjahr(start,notice);var months=fv||(dj===1?1:(dj<=9?2:3));
  steps.push('Zugang der Kündigung im '+dj+'. Dienstjahr (massgebend ist der Zugang).');
  steps.push(fv?('Vertragliche Frist: '+months+(months===1?' Monat':' Monate')+'.'):('Gesetzliche Frist im '+dj+'. Dienstjahr: '+months+(months===1?' Monat':' Monate')+' auf Ende eines Monats (Art. 335c Abs. 1 OR).'));
  var raw=addMonths(notice,months);var end=me?endOfMonth(raw):raw;
  var fStart=me?addDays(addMonths(end,-months),1):addDays(notice,1);
  if(me&&fStart<=notice){fStart=addDays(notice,1);}
  steps.push('Ordentliches Ende: '+fmt(end)+' (Kündigungsfrist vom '+fmt(fStart)+' bis '+fmt(end)+').');
  var au1=parseD($('au1').value),au2=parseD($('au2').value),extra='';
  if(who==='ag'&&au1){
    if(!au2||au2<au1){out('res','<p class="warn">Bitte bei der Arbeitsunfähigkeit ein gültiges Enddatum eingeben.</p>');return;}
    var djAu=dienstjahr(start,au1);var dur=djAu===1?30:(djAu<=5?90:180);
    var sEnd=addDays(au1,dur-1);if(au2<sEnd)sEnd=au2;
    var inProbe=probe&&au1<=probeEnd;
    if(inProbe){steps.push('Die Arbeitsunfähigkeit beginnt in der Probezeit; dort gelten keine Sperrfristen.');}
    else if(notice>=au1&&notice<=sEnd){
      out('res','<p class="big danger">Die Kündigung ist <b>nichtig</b>.</p><ol>'+steps.concat(['Die Kündigung ging während der Sperrfrist zu ('+fmt(au1)+' bis '+fmt(sEnd)+', '+dur+' Tage im '+djAu+'. Dienstjahr). Eine Kündigung zur Unzeit ist nichtig (Art. 336c Abs. 2 OR).','Sie muss nach Ablauf der Sperrfrist neu ausgesprochen werden.']).map(function(s){return '<li>'+s+'</li>';}).join('')+'</ol>');return;}
    else if(au1<=end&&sEnd>=fStart&&au1>notice){
      var from=au1>fStart?au1:fStart;var remaining=diffDays(from,end)+1;var newEnd=addDays(sEnd,remaining);var finalEnd=me?endOfMonth(newEnd):newEnd;
      steps.push('Sperrfrist im '+djAu+'. Dienstjahr: höchstens '+dur+' Tage (Art. 336c Abs. 1 lit. b OR). Sie dauert hier vom '+fmt(au1)+' bis '+fmt(sEnd)+'.');
      steps.push('Bei Beginn der Sperrfrist waren noch '+remaining+' Tage der Kündigungsfrist offen. Sie laufen ab dem '+fmt(addDays(sEnd,1))+' weiter und enden am '+fmt(newEnd)+'.');
      if(me&&+finalEnd!==+newEnd)steps.push('Weil das neue Ende nicht auf ein Monatsende fällt, verlängert sich das Arbeitsverhältnis bis zum nächsten Monatsende (Art. 336c Abs. 3 OR).');
      end=finalEnd;extra='<p class="hint">Eine zweite Arbeitsunfähigkeit mit anderer Ursache kann eine weitere Sperrfrist auslösen. Rückfälle derselben Krankheit lösen keine neue Sperrfrist aus.</p>';
    } else { steps.push('Die Arbeitsunfähigkeit fällt nicht in die Kündigungsfrist und verlängert sie deshalb nicht.'); }
  } else if(who==='an'&&au1){ steps.push('Die Sperrfristen schützen nur vor Kündigungen durch den Arbeitgeber. Bei einer Kündigung durch die Arbeitnehmerin/den Arbeitnehmer verlängert eine Krankheit die Frist nicht.'); }
  out('res','<p class="big">Letzter Arbeitstag: <b>'+fmt(end)+'</b></p><ol>'+steps.map(function(s){return '<li>'+s+'</li>';}).join('')+'</ol>'+extra);
});
"""

LOHNF_FORM = """
<form class="calc" id="f" novalidate>
  <div class="calc-grid">
    <div class="field"><label for="start">Eintrittsdatum</label><input type="date" id="start" required></div>
    <div class="field"><label for="au">Beginn der Arbeitsunfähigkeit</label><input type="date" id="au" required></div>
    <div class="field"><label for="skala">Skala</label><select id="skala"><option value="bern">Berner Skala (die meisten Kantone)</option><option value="zuerich">Zürcher Skala (u.a. ZH, SH, TG)</option><option value="basel">Basler Skala (BS, BL)</option></select><small>Welche Skala gilt, richtet sich nach der Praxis der Gerichte am Arbeitsort bzw. Gerichtsstand.</small></div>
  </div>
  <button class="btn red" type="submit">Berechnen</button>
</form>
<div class="calc-result" id="res" hidden aria-live="polite"></div>
"""

LOHNF_JS = r"""
var ZH=function(n){return n===1?'3 Wochen':(n+6)+' Wochen';};
var BE=[0,'3 Wochen','1 Monat','2 Monate','2 Monate','3 Monate','3 Monate','3 Monate','3 Monate','3 Monate','4 Monate','4 Monate','4 Monate','4 Monate','4 Monate','5 Monate','5 Monate','5 Monate','5 Monate','5 Monate','6 Monate','6 Monate','6 Monate','6 Monate','6 Monate','6 Monate'];
var BS=[0,'3 Wochen','2 Monate','2 Monate','3 Monate','3 Monate','3 Monate','3 Monate','3 Monate','4 Monate','4 Monate','4 Monate','4 Monate','4 Monate','5 Monate','5 Monate','5 Monate','5 Monate','5 Monate','6 Monate','6 Monate','6 Monate','6 Monate','6 Monate','6 Monate','6 Monate'];
$('f').addEventListener('submit',function(ev){ev.preventDefault();
  var start=parseD($('start').value),au=parseD($('au').value),sk=$('skala').value;
  if(!start||!au||au<start){out('res','<p class="warn">Bitte ein gültiges Eintrittsdatum und einen Beginn der Arbeitsunfähigkeit nach dem Eintritt eingeben.</p>');return;}
  var n=dienstjahr(start,au),capped=Math.min(n,25);
  var val=sk==='zuerich'?ZH(capped):(sk==='bern'?BE[capped]:BS[capped]);
  var name={bern:'Berner',zuerich:'Zürcher',basel:'Basler'}[sk];
  var djEnd=addDays(anniversary(start,n),-1);
  var notes=['Die Dauer gilt <b>pro Dienstjahr</b>: Alle Absenzen wegen Krankheit, Unfall usw. im selben Dienstjahr werden zusammengezählt. Mit dem neuen Dienstjahr ab '+fmt(addDays(djEnd,1))+' entsteht der Anspruch neu.'];
  var threeM=addMonths(start,3);
  if(n===1&&au<threeM)notes.unshift('<b>Achtung:</b> Die Arbeitsunfähigkeit beginnt in den ersten drei Monaten. Ein Anspruch besteht nur, wenn das Arbeitsverhältnis für mehr als drei Monate eingegangen wurde (Art. 324a Abs. 1 OR); bei unbefristeten Verträgen ist das umstritten.');
  if(n>25)notes.push('Die Gerichtstabelle reicht bis zum 25. Dienstjahr. Für längere Dienstdauer bitte im Einzelfall prüfen.');
  notes.push('Besteht eine Krankentaggeldversicherung, die mindestens gleichwertig ist (z.B. 80 % Lohn während 720 Tagen, Prämie mindestens hälftig vom Arbeitgeber), ersetzt sie diese Skala, wenn das schriftlich vereinbart ist (Art. 324a Abs. 4 OR).');
  out('res','<p class="big">Anspruch im '+n+'. Dienstjahr: <b>'+val+'</b> Lohnfortzahlung</p><p>Nach '+name+' Skala. Das laufende Dienstjahr dauert bis '+fmt(djEnd)+'.</p><ul>'+notes.map(function(s){return '<li>'+s+'</li>';}).join('')+'</ul>');
});
"""

FERIEN_FORM = """
<form class="calc" id="f" novalidate>
  <div class="calc-grid">
    <div class="field"><label for="wochen">Ferienanspruch pro Jahr (Wochen)</label><select id="wochen"><option value="4">4 Wochen (gesetzliches Minimum)</option><option value="5">5 Wochen (bis 20. Altersjahr gesetzlich)</option><option value="6">6 Wochen</option><option value="4.4">22 Tage (4,4 Wochen)</option><option value="5.2">26 Tage (5,2 Wochen)</option></select></div>
    <div class="field"><label for="pensum">Pensum in %</label><input type="number" id="pensum" min="1" max="100" step="1" value="100"></div>
    <div class="field"><label for="von">Beschäftigt ab</label><input type="date" id="von" required></div>
    <div class="field"><label for="bis">bis und mit</label><input type="date" id="bis" required><small>Beide Daten im selben Kalenderjahr bzw. Ferienjahr.</small></div>
  </div>
  <button class="btn red" type="submit">Berechnen</button>
</form>
<div class="calc-result" id="res" hidden aria-live="polite"></div>
"""

FERIEN_JS = r"""
$('f').addEventListener('submit',function(ev){ev.preventDefault();
  var w=+$('wochen').value,p=+$('pensum').value,von=parseD($('von').value),bis=parseD($('bis').value);
  if(!von||!bis||bis<von||!(p>0&&p<=100)){out('res','<p class="warn">Bitte einen gültigen Zeitraum und ein Pensum zwischen 1 und 100 % eingeben.</p>');return;}
  if(von.getUTCFullYear()!==bis.getUTCFullYear()){out('res','<p class="warn">Bitte einen Zeitraum innerhalb desselben Jahres eingeben.</p>');return;}
  var y=von.getUTCFullYear(),daysYear=diffDays(new Date(Date.UTC(y,0,1)),new Date(Date.UTC(y+1,0,1))),days=diffDays(von,bis)+1;
  var full=w*5,pr=full*days/daysYear,tage=pr*p/100,rounded=Math.round(tage*2)/2;
  out('res','<p class="big">Ferienanspruch: <b>'+rounded.toString().replace('.',',')+' Arbeitstage</b></p><ul><li>Voller Jahresanspruch: '+full.toString().replace('.',',')+' Arbeitstage bei 100 %.</li><li>Pro rata für '+days+' von '+daysYear+' Tagen: '+pr.toFixed(2).replace('.',',')+' Tage bei 100 %.</li><li>Bei '+p+' % Pensum: '+tage.toFixed(2).replace('.',',')+' Tage, gerundet auf halbe Tage.</li><li>Bei Teilzeit kann der Anspruch auch in Wochen ausgedrückt werden: '+(w*days/daysYear).toFixed(2).replace('.',',')+' Wochen, jeweils zu den üblichen Arbeitstagen.</li></ul><p class="hint">Nicht berücksichtigt: Kürzungen wegen längerer Absenzen (Art. 329b OR) und abweichende Regelungen in Vertrag, Reglement oder GAV.</p>');
});
"""

BVG_FORM = """
<form class="calc" id="f" novalidate>
  <div class="calc-grid">
    <div class="field"><label for="lohn">AHV-pflichtiger Jahreslohn (CHF)</label><input type="number" id="lohn" min="0" step="100" value="60000"></div>
    <div class="field"><label for="jahr">Jahr</label><select id="jahr"><option value="2027" selected>2027</option><option value="2026">2026</option></select></div>
    <div class="field"><label for="alter">Alter im betreffenden Jahr (optional)</label><input type="number" id="alter" min="15" max="70" step="1" placeholder="z.B. 42"><small>Massgebend ist das Alter, das im Kalenderjahr erreicht wird.</small></div>
  </div>
  <button class="btn red" type="submit">Berechnen</button>
</form>
<div class="calc-result" id="res" hidden aria-live="polite"></div>
"""

BVG_JS = r"""
var V={2026:{e:22680,k:26460,o:90720,m:3780},2027:{e:23040,k:26880,o:92160,m:3840}};
$('f').addEventListener('submit',function(ev){ev.preventDefault();
  var l=+$('lohn').value,j=$('jahr').value,v=V[j],a=$('alter').value?+$('alter').value:null;
  if(!(l>=0)){out('res','<p class="warn">Bitte einen gültigen Jahreslohn eingeben.</p>');return;}
  var items=['Eintrittsschwelle '+j+': '+chf(v.e)+', Koordinationsabzug: '+chf(v.k)+', oberer Grenzbetrag: '+chf(v.o)+'.'];
  if(l<=v.e){out('res','<p class="big">Nicht BVG-pflichtig</p><p>Der Jahreslohn liegt nicht über der Eintrittsschwelle von '+chf(v.e)+'. Eine obligatorische Versicherung besteht nicht, die Pensionskasse kann aber eine tiefere Schwelle vorsehen.</p><ul><li>'+items.join('</li><li>')+'</li></ul>');return;}
  var k=Math.min(l,v.o)-v.k;if(k<v.m)k=v.m;
  var res='<p class="big">BVG-pflichtig, koordinierter Lohn: <b>'+chf(k)+'</b></p>';
  if(a!==null){
    if(a<18){res+='<p>Unter 18 Jahren besteht noch keine BVG-Pflicht. Versichert wird ab dem 1. Januar nach dem 17. Geburtstag.</p>';}
    else if(a<25){res+='<p>Im Alter von '+a+' Jahren ist nur das Risiko Tod und Invalidität versichert. Altersgutschriften beginnen am 1. Januar nach dem 24. Geburtstag.</p>';}
    else{var r=a<=34?7:(a<=44?10:(a<=54?15:18));res+='<p>Minimale Altersgutschrift bei '+a+' Jahren: <b>'+r+' %</b> des koordinierten Lohnes, also <b>'+chf(k*r/100)+'</b> pro Jahr (gesetzliches Minimum, Art. 16 BVG).</p>';}
  }
  items.push('Koordinierter Lohn = AHV-Lohn (höchstens '+chf(v.o)+') minus Koordinationsabzug, mindestens '+chf(v.m)+'.');
  items.push('Viele Pensionskassen versichern mehr als das Minimum oder passen den Koordinationsabzug bei Teilzeit an. Massgebend ist das Reglement.');
  out('res',res+'<ul><li>'+items.join('</li><li>')+'</li></ul>');
});
"""

CALCS = {
    "kuendigung": (KUENDIGUNG_FORM, KUENDIGUNG_JS, ["Art. 335b OR", "Art. 335c OR", "Art. 336c OR", "BGE 134 III 354"]),
    "lohnfortzahlung": (LOHNF_FORM, LOHNF_JS, ["Art. 324a OR", "Art. 324b OR"]),
    "ferien": (FERIEN_FORM, FERIEN_JS, ["Art. 329a OR", "Art. 329b OR"]),
    "bvg": (BVG_FORM, BVG_JS, ["Art. 2 BVG", "Art. 7–8 BVG", "Art. 16 BVG"]),
}
