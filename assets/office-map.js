/* Карта входа МДИС: плавное масштабирование, открытые тайлы OpenStreetMap. */
(function () {
  'use strict';
  const root = document.querySelector('#office-map .office-local-map');
  if (!root) return;

  const tileLayer = root.querySelector('.office-map-tiles');
  const marker = root.querySelector('.office-map-marker');
  const zoomIn = root.querySelector('.office-map-zoom-in');
  const zoomOut = root.querySelector('.office-map-zoom-out');
  const unavailable = root.querySelector('.office-map-unavailable');
  const entrance = { lat: 55.763107, lon: 37.559358 };
  const minZoom = 15;
  const maxZoom = 19;
  const tileSize = 256;
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let zoom = 17;
  let targetZoom = zoom;
  let center = project(entrance, zoom);
  let dragging = null;
  let animationId = 0;
  let lastFrameTime = 0;
  let anchorX = 0;
  let anchorY = 0;
  const tiles = new Map();

  // Координаты метро и парковки — ориентиры; вход МДИС подтверждён владельцем сайта.
  const routeEnds = {
    walk: {from:{lat:55.764704,lon:37.561449},to:entrance},
    zven: {from:{lat:55.76388,lon:37.55688},to:{lat:55.76337,lon:37.55947}},
    street: {from:{lat:55.76215,lon:37.56073},to:{lat:55.76337,lon:37.55947}}
  };
  const routeSvg=root.querySelector('.office-map-route');
  const routeUnder=root.querySelector('.office-map-route-under');
  const routeOver=root.querySelector('.office-map-route-over');
  const routeStart=root.querySelector('.office-map-start');
  const routeInfo=root.querySelector('.office-map-route-info');
  const originsBox=root.querySelector('.office-map-origins');
  const modes=Array.from(root.querySelectorAll('[data-mode]'));
  const origins=Array.from(root.querySelectorAll('[data-drive]'));
  const routeCache=new Map();
  let routeMode='',driveFrom='zven',routePts=null,requestId=0;

  function routeHref(pair,mode){
    return 'https://yandex.ru/maps/?rtext='+pair.from.lat+'%2C'+pair.from.lon+'~'+
      pair.to.lat+'%2C'+pair.to.lon+'&rtt='+(mode==='walk'?'pd':'auto');
  }
  function routeMessage(message,href){
    routeInfo.textContent=message;
    if(href){
      const link=document.createElement('a');
      link.href=href;link.target='_blank';link.rel='noopener noreferrer';
      link.textContent=' Открыть маршрут в Яндекс Картах';
      routeInfo.appendChild(link);
    }
    routeInfo.hidden=false;
  }
  function drawRoute(){
    if(!routePts){routeSvg.hidden=true;routeStart.hidden=true;return;}
    const width=root.clientWidth,height=root.clientHeight;
    const projected=routePts.map(function(p){
      const q=project(p,zoom);
      return {x:q.x-center.x+width/2,y:q.y-center.y+height/2};
    });
    const d=projected.map(function(p,i){return (i?'L':'M')+p.x.toFixed(2)+','+p.y.toFixed(2);}).join(' ');
    routeSvg.setAttribute('viewBox','0 0 '+width+' '+height);
    routeUnder.setAttribute('d',d);routeOver.setAttribute('d',d);
    routeSvg.hidden=false;
    routeStart.style.left=projected[0].x+'px';
    routeStart.style.top=projected[0].y+'px';
    routeStart.hidden=false;
  }
  function fitRoute(points){
    if(!root.clientWidth||!root.clientHeight)return;
    stopZoomAnimation();
    const width=root.clientWidth,height=root.clientHeight;
    let level=minZoom;
    for(let z=maxZoom;z>=minZoom;z-=.2){
      const p=points.map(function(a){return project(a,z);});
      const xs=p.map(function(a){return a.x;}),ys=p.map(function(a){return a.y;});
      if(Math.max(...xs)-Math.min(...xs)<=Math.max(40,width-94)&&
         Math.max(...ys)-Math.min(...ys)<=Math.max(40,height-168)){level=z;break;}
    }
    zoom=Math.min(maxZoom,Math.max(minZoom,level));targetZoom=zoom;
    const pts=points.map(function(a){return project(a,zoom);});
    center={x:(Math.min(...pts.map(p=>p.x))+Math.max(...pts.map(p=>p.x)))/2,
            y:(Math.min(...pts.map(p=>p.y))+Math.max(...pts.map(p=>p.y)))/2-20};
  }
  function parseGeometry(json){
    const route=json.routes&&json.routes[0];
    const g=route&&route.geometry;
    if(!g||g.type!=='LineString'||!Array.isArray(g.coordinates))throw Error('No route shape');
    const points=g.coordinates.map(function(c){return {lon:c[0],lat:c[1]};}).filter(function(p){
      return Number.isFinite(p.lat)&&Number.isFinite(p.lon);
    });
    if(points.length<2)throw Error('Empty route');
    return {points:points,distance:route.distance};
  }
  async function loadRoute(){
    const current=++requestId;
    routePts=null;drawRoute();
    const pair=routeEnds[routeMode==='walk'?'walk':driveFrom];
    const href=routeHref(pair,routeMode);
    routeMessage('Построение маршрута…',null);
    const key=routeMode==='walk'?'walk':driveFrom;
    try{
      let data=routeCache.get(key);
      if(!data){
        const query={locations:[pair.from,pair.to],
          costing:routeMode==='walk'?'pedestrian':'auto',format:'osrm',shape_format:'geojson',
          units:'kilometers'};
        const abort=new AbortController();
        const timer=setTimeout(function(){abort.abort();},10000);
        try{
          const response=await fetch('https://valhalla1.openstreetmap.de/route?json='+
            encodeURIComponent(JSON.stringify(query)),{signal:abort.signal,credentials:'omit'});
          if(!response.ok)throw Error('Routing unavailable');
          data=parseGeometry(await response.json());
          routeCache.set(key,data);
        }finally{clearTimeout(timer);}
      }
      if(current!==requestId)return;
      routePts=data.points;fitRoute(routePts);draw();
      const d=Number(data.distance);
      const distance=Number.isFinite(d)?(d<1?Math.round(d*1000)+' м':d.toFixed(1).replace('.',',')+' км'):'';
      const label=routeMode==='walk'?'Пешком от метро, выход № 1 (ориентир). ':
        'Подъезд к парковке у Звенигородского шоссе (ориентир). ';
      routeMessage(label+distance+'. Уточните доступность парковки.',href);
    }catch(e){
      if(current!==requestId)return;
      routePts=null;drawRoute();
      routeMessage('Маршрут внутри карты временно недоступен.',href);
    }
  }
  modes.forEach(function(btn){
    btn.addEventListener('click',function(){
      const next=btn.dataset.mode;
      if(next===routeMode){
        requestId++;routeMode='';root.dataset.mode='';routePts=null;
        routeSvg.hidden=true;routeStart.hidden=true;routeInfo.hidden=true;originsBox.hidden=true;
        modes.forEach(function(b){b.setAttribute('aria-pressed','false');});
        stopZoomAnimation();zoom=17;targetZoom=17;center=project(entrance,17);draw();return;
      }
      routeMode=next;root.dataset.mode=next;originsBox.hidden=next!=='auto';
      modes.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.mode===next));});
      loadRoute();
    });
  });
  origins.forEach(function(btn){
    btn.addEventListener('click',function(){
      if(routeMode!=='auto')return;
      driveFrom=btn.dataset.drive;
      origins.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.drive===driveFrom));});
      loadRoute();
    });
  });


  function project(point, level) {
    const size = tileSize * Math.pow(2, level);
    const sin = Math.sin(point.lat * Math.PI / 180);
    return {
      x: (point.lon + 180) / 360 * size,
      y: (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * size
    };
  }

  function unproject(point, level) {
    const size = tileSize * Math.pow(2, level);
    const a = Math.PI * (1 - 2 * point.y / size);
    return {
      lon: point.x / size * 360 - 180,
      lat: (2 * Math.atan(Math.exp(a)) - Math.PI / 2) * 180 / Math.PI
    };
  }

  function showTileErrorIfNeeded() {
    const current = Array.from(tiles.values());
    if (current.some(function (img) { return img.complete && img.naturalWidth > 0; })) {
      unavailable.hidden = true;
      return;
    }
    if (current.length && current.every(function (img) { return img.dataset.failed === '1'; })) {
      unavailable.hidden = false;
    }
  }

  function draw() {
    const width = root.clientWidth;
    const height = root.clientHeight;
    if (!width || !height) return;
    const visible = new Set();

    // Два соседних уровня: старые тайлы остаются под новыми при смене масштаба.
    // Дробный zoom масштабирует их непрерывно, без скачка на целую ступень.
    const lowLevel = Math.floor(zoom);
    const highLevel = Math.min(lowLevel + 1, maxZoom);
    const levels = lowLevel === highLevel ? [lowLevel] : [lowLevel, highLevel];

    levels.forEach(function (level) {
      const scale = Math.pow(2, zoom - level);
      const left = center.x / scale - width / (2 * scale);
      const top = center.y / scale - height / (2 * scale);
      const minX = Math.floor(left / tileSize);
      const maxX = Math.floor((left + width / scale) / tileSize);
      const minY = Math.floor(top / tileSize);
      const maxY = Math.floor((top + height / scale) / tileSize);
      const extent = Math.pow(2, level);
      const renderedSize = tileSize * scale;

      for (let y = minY; y <= maxY; y++) {
        if (y < 0 || y >= extent) continue;
        for (let x = minX; x <= maxX; x++) {
          const wrapped = ((x % extent) + extent) % extent;
          const key = level + '/' + wrapped + '/' + y;
          visible.add(key);
          let img = tiles.get(key);
          if (!img) {
            img = document.createElement('img');
            img.className = 'office-map-tile';
            img.alt = '';
            img.draggable = false;
            img.decoding = 'async';
            img.referrerPolicy = 'strict-origin-when-cross-origin';
            img.addEventListener('load', function () {
              unavailable.hidden = true;
            });
            img.addEventListener('error', function () {
              img.dataset.failed = '1';
              showTileErrorIfNeeded();
            });
            tiles.set(key, img);
            tileLayer.appendChild(img);
            img.src = 'https://tile.openstreetmap.org/' + level + '/' + wrapped + '/' + y + '.png';
          }
          img.style.left = ((x * tileSize - left) * scale) + 'px';
          img.style.top = ((y * tileSize - top) * scale) + 'px';
          img.style.width = renderedSize + 'px';
          img.style.height = renderedSize + 'px';
          img.style.zIndex = String(level);
          // Разрешение и размер подписей сменяются постепенно, без щелчка.
          if (level === lowLevel) {
            img.style.opacity = '1';
          } else {
            const blend = Math.max(0, Math.min(1, (zoom - lowLevel - 0.35) / 0.6));
            img.style.opacity = String(blend);
          }
        }
      }
    });

    tiles.forEach(function (img, key) {
      if (!visible.has(key)) {
        img.remove();
        tiles.delete(key);
      }
    });

    const pin = project(entrance, zoom);
    marker.style.left = (pin.x - center.x + width / 2) + 'px';
    marker.style.top = (pin.y - center.y + height / 2) + 'px';
    zoomIn.disabled = targetZoom >= maxZoom;
    zoomOut.disabled = targetZoom <= minZoom;
    drawRoute();
  }

  function setZoomImmediate(level, x, y) {
    if (level === zoom) return;
    const width = root.clientWidth;
    const height = root.clientHeight;
    const geoAnchor = unproject({
      x: center.x + x - width / 2,
      y: center.y + y - height / 2
    }, zoom);
    zoom = level;
    const next = project(geoAnchor, zoom);
    center = {
      x: next.x - x + width / 2,
      y: next.y - y + height / 2
    };
    draw();
  }

  function stopZoomAnimation() {
    if (animationId) window.cancelAnimationFrame(animationId);
    animationId = 0;
    lastFrameTime = 0;
    targetZoom = zoom;
  }

  function animateZoom(timestamp) {
    animationId = 0;
    const elapsed = lastFrameTime ? Math.min(timestamp - lastFrameTime, 64) : 16;
    lastFrameTime = timestamp;
    const difference = targetZoom - zoom;
    if (Math.abs(difference) < 0.002) {
      setZoomImmediate(targetZoom, anchorX, anchorY);
      lastFrameTime = 0;
      return;
    }
    // Плавное приближение с быстрым, но мягким затуханием (~200–300 мс).
    const factor = 1 - Math.exp(-elapsed / 75);
    setZoomImmediate(zoom + difference * factor, anchorX, anchorY);
    animationId = window.requestAnimationFrame(animateZoom);
  }

  function queueZoom(level, x, y) {
    targetZoom = Math.max(minZoom, Math.min(maxZoom, level));
    anchorX = x;
    anchorY = y;
    if (reduceMotion) {
      if (animationId) window.cancelAnimationFrame(animationId);
      animationId = 0;
      lastFrameTime = 0;
      setZoomImmediate(targetZoom, anchorX, anchorY);
    } else if (!animationId && Math.abs(targetZoom - zoom) > 0.002) {
      lastFrameTime = 0;
      animationId = window.requestAnimationFrame(animateZoom);
    }
    zoomIn.disabled = targetZoom >= maxZoom;
    zoomOut.disabled = targetZoom <= minZoom;
  }

  zoomIn.addEventListener('click', function () {
    queueZoom(targetZoom + 1, root.clientWidth / 2, root.clientHeight / 2);
  });
  zoomOut.addEventListener('click', function () {
    queueZoom(targetZoom - 1, root.clientWidth / 2, root.clientHeight / 2);
  });
  root.addEventListener('wheel', function (event) {
    if (!event.deltaY) return;
    event.preventDefault();
    const bounds = root.getBoundingClientRect();
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? bounds.height : 1;
    const delta = Math.max(-0.6, Math.min(0.6, -event.deltaY * unit / 420));
    queueZoom(targetZoom + delta, event.clientX - bounds.left, event.clientY - bounds.top);
  }, { passive: false });

  root.addEventListener('pointerdown', function (event) {
    if (event.target.closest('button, a')) return;
    if (event.button !== 0 && event.pointerType === 'mouse') return;
    stopZoomAnimation();
    dragging = { id: event.pointerId, x: event.clientX, y: event.clientY };
    root.setPointerCapture(event.pointerId);
  });
  root.addEventListener('pointermove', function (event) {
    if (!dragging || dragging.id !== event.pointerId) return;
    center.x -= event.clientX - dragging.x;
    center.y -= event.clientY - dragging.y;
    dragging.x = event.clientX;
    dragging.y = event.clientY;
    draw();
  });
  function stopDrag(event) {
    if (dragging && event.pointerId === dragging.id) dragging = null;
  }
  root.addEventListener('pointerup', stopDrag);
  root.addEventListener('pointercancel', stopDrag);
  root.addEventListener('lostpointercapture', function () { dragging = null; });

  root.addEventListener('keydown', function (event) {
    if (event.target.closest('button, a')) return;
    const moves = { ArrowUp: [0, -80], ArrowDown: [0, 80], ArrowLeft: [-80, 0], ArrowRight: [80, 0] };
    if (moves[event.key]) {
      event.preventDefault();
      stopZoomAnimation();
      center.x += moves[event.key][0];
      center.y += moves[event.key][1];
      draw();
    } else if (event.key === '+' || event.key === '=') {
      event.preventDefault();
      queueZoom(targetZoom + 1, root.clientWidth / 2, root.clientHeight / 2);
    } else if (event.key === '-') {
      event.preventDefault();
      queueZoom(targetZoom - 1, root.clientWidth / 2, root.clientHeight / 2);
    } else if (event.key === 'Home') {
      event.preventDefault();
      stopZoomAnimation();
      zoom = 17;
      targetZoom = zoom;
      center = project(entrance, zoom);
      draw();
    }
  });

  if (typeof ResizeObserver === 'function') new ResizeObserver(draw).observe(root);
  else window.addEventListener('resize', draw);
  draw();
})();
