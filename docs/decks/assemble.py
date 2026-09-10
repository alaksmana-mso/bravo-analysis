import sys, pathlib
D = pathlib.Path(__file__).parent
CSS = (D/'_deck.css').read_text()
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Archivo:wght@500;600;700;800&'
         'family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&'
         'family=IBM+Plex+Mono:wght@400;500;600&display=swap">')
NAV = """
<div class="rail" id="rail" role="tablist" aria-label="Slides"></div>
<div class="hud" id="hud" aria-live="off"><b>01</b> / 01</div>
<script>
(function(){
  var deck=document.getElementById('deck');
  var slides=[].slice.call(deck.querySelectorAll('.slide'));
  var rail=document.getElementById('rail'), hud=document.getElementById('hud');
  var pad=function(n){return String(n).padStart(2,'0')};
  slides.forEach(function(s,i){
    s.id='s'+(i+1);
    var b=document.createElement('button');
    b.type='button';
    b.setAttribute('aria-label','Slide '+(i+1)+(s.dataset.nav?': '+s.dataset.nav:''));
    b.addEventListener('click',function(){go(i)});
    rail.appendChild(b);
  });
  var dots=[].slice.call(rail.children), cur=0;
  function paint(i){
    cur=i;
    dots.forEach(function(d,j){d.setAttribute('aria-current',j===i?'true':'false')});
    hud.innerHTML='<b>'+pad(i+1)+'</b> / '+pad(slides.length);
  }
  function go(i){
    i=Math.max(0,Math.min(slides.length-1,i));
    slides[i].scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth',block:'start'});
    paint(i);
  }
  paint(0);
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting) paint(slides.indexOf(e.target)); });
    },{root:deck,threshold:0.55});
    slides.forEach(function(s){io.observe(s)});
  }
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey) return;
    var k=e.key;
    if(k==='ArrowDown'||k==='ArrowRight'||k==='PageDown'||k===' '){e.preventDefault();go(cur+1)}
    else if(k==='ArrowUp'||k==='ArrowLeft'||k==='PageUp'){e.preventDefault();go(cur-1)}
    else if(k==='Home'){e.preventDefault();go(0)}
    else if(k==='End'){e.preventDefault();go(slides.length-1)}
  });
})();
</script>
"""
def build(slug, title, accent_light, accent_dark, body):
    ov = (":root{--ac:%s;--acBg:%s1f;--acBg2:%s0f}\n"
          "@media (prefers-color-scheme:dark){:root:not([data-theme=\"light\"]){"
          "--ac:%s;--acBg:%s24;--acBg2:%s12}}\n"
          ":root[data-theme=\"dark\"]{--ac:%s;--acBg:%s24;--acBg2:%s12}\n") % (
          accent_light,accent_light,accent_light, accent_dark,accent_dark,accent_dark,
          accent_dark,accent_dark,accent_dark)
    out = "<title>%s</title>\n%s\n<style>\n%s\n%s</style>\n<main class=\"deck\" id=\"deck\">\n%s\n</main>\n%s" % (
          title, FONTS, CSS, ov, body, NAV)
    (D/(slug+'.html')).write_text(out)
    n = out.count('class="slide')
    print("%-28s %6d bytes  %2d slides" % (slug+'.html', len(out), n))
