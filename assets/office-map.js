/* Карта входа МДИС: плавное масштабирование, открытые тайлы OpenStreetMap. */
(function () {
  'use strict';
  const root = document.querySelector('#office-map .office-local-map');
  if (!root) return;

  const tileLayer = root.querySelector('.office-map-tiles');
  const marker = root.querySelector('.office-map-marker');
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

  // Ориентировочные линии по схемам, предоставленным МДИС:
  // пешком — от выхода метро через подземный переход к входу;
  // авто — со Звенигородского шоссе до въезда на парковку.
  // Это схема подхода, не навигация в реальном времени.
  const routes = {
    walk: [
      { lat: 55.764704, lon: 37.561449 },
      { lat: 55.76459, lon: 37.56133 },
      { lat: 55.76449, lon: 37.56113 },
      { lat: 55.76438, lon: 37.56094 },
      { lat: 55.76428, lon: 37.56072 },
      { lat: 55.76399, lon: 37.56041 },
      { lat: 55.76368, lon: 37.56010 },
      { lat: 55.76349, lon: 37.55986 },
      { lat: 55.76336, lon: 37.55964 },
      { lat: 55.76320, lon: 37.55949 },
      entrance
    ],
    auto: [
      { lat: 55.76391, lon: 37.55775 },
      { lat: 55.76385, lon: 37.55804 },
      { lat: 55.76378, lon: 37.55836 },
      { lat: 55.76367, lon: 37.55853 },
      { lat: 55.76356, lon: 37.55858 },
      { lat: 55.76346, lon: 37.55861 }
    ]
  };

  const routeSvg = root.querySelector('.office-map-route');
  const routeUnder = root.querySelector('.office-map-route-under');
  const routeOver = root.querySelector('.office-map-route-over');
  const routeStart = root.querySelector('.office-map-start');
  const modeButtons = Array.from(root.querySelectorAll('[data-mode]'));
  let routeMode = 'walk';

  function drawRoute() {
    const points = routes[routeMode];
    const width = root.clientWidth, height = root.clientHeight;
    if (!width || !height || !points || points.length < 2) return;
    const screen = points.map(function (point) {
      const p = project(point, zoom);
      return { x: p.x - center.x + width / 2, y: p.y - center.y + height / 2 };
    });
    const d = screen.map(function (p, index) {
      return (index ? 'L' : 'M') + p.x.toFixed(2) + ',' + p.y.toFixed(2);
    }).join(' ');
    routeSvg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
    routeUnder.setAttribute('d', d);
    routeOver.setAttribute('d', d);
    // SVG does not reliably reflect the HTML hidden property: remove the attribute.
    routeSvg.removeAttribute('hidden');
    routeStart.style.left = screen[0].x + 'px';
    routeStart.style.top = screen[0].y + 'px';
    routeStart.hidden = false;
  }

  function fitRoute() {
    const width = root.clientWidth, height = root.clientHeight;
    if (!width || !height) return;
    stopZoomAnimation();
    const points = routes[routeMode].concat([entrance]);
    const reservedWidth = Math.max(80, width - 46);
    const reservedHeight = Math.max(80, height - 86);
    let level = minZoom;
    for (let current = maxZoom; current >= minZoom; current -= 0.1) {
      const coords = points.map(function (point) { return project(point, current); });
      const xx = coords.map(function (point) { return point.x; });
      const yy = coords.map(function (point) { return point.y; });
      if (Math.max(...xx) - Math.min(...xx) <= reservedWidth &&
          Math.max(...yy) - Math.min(...yy) <= reservedHeight) {
        level = current;
        break;
      }
    }
    zoom = Math.max(minZoom, Math.min(maxZoom, level));
    targetZoom = zoom;
    const coords = points.map(function (point) { return project(point, zoom); });
    center = {
      x: (Math.min(...coords.map(function (p) { return p.x; })) +
          Math.max(...coords.map(function (p) { return p.x; }))) / 2,
      y: (Math.min(...coords.map(function (p) { return p.y; })) +
          Math.max(...coords.map(function (p) { return p.y; }))) / 2
    };
  }

  function selectRoute(next) {
    if (next === routeMode) return;
    routeMode = next;
    root.dataset.mode = routeMode;
    modeButtons.forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.mode === routeMode));
    });
    // Keep the same map centre and zoom; only the displayed route changes.
    drawRoute();
  }
  modeButtons.forEach(function (button) {
    button.addEventListener('click', function () { selectRoute(button.dataset.mode); });
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
  }
  root.addEventListener('wheel', function (event) {
    if (!event.deltaY) return;
    event.preventDefault();
    const bounds = root.getBoundingClientRect();
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? bounds.height : 1;
    const delta = Math.max(-0.6, Math.min(0.6, -event.deltaY * unit / 420));
    queueZoom(targetZoom + delta, event.clientX - bounds.left, event.clientY - bounds.top);
  }, { passive: false });

  // На телефоне карта масштабируется двумя пальцами; на компьютере — колесом.
  const pointers = new Map();
  let pinch = null;

  root.addEventListener('pointerdown', function (event) {
    if (event.target.closest('button, a')) return;
    if (event.button !== 0 && event.pointerType === 'mouse') return;
    stopZoomAnimation();
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    try { root.setPointerCapture(event.pointerId); } catch (error) { /* capture unsupported */ }
    if (pointers.size === 1) {
      dragging = { id: event.pointerId, x: event.clientX, y: event.clientY };
      pinch = null;
    } else if (pointers.size === 2) {
      const pair = Array.from(pointers.values());
      dragging = null;
      pinch = {
        distance: Math.max(1, Math.hypot(pair[1].x - pair[0].x, pair[1].y - pair[0].y)),
        zoom: zoom
      };
    }
  });

  root.addEventListener('pointermove', function (event) {
    const old = pointers.get(event.pointerId);
    if (!old) return;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });

    if (pointers.size === 2 && pinch) {
      const pair = Array.from(pointers.values());
      const dist = Math.max(1, Math.hypot(pair[1].x - pair[0].x, pair[1].y - pair[0].y));
      const bounds = root.getBoundingClientRect();
      const x = (pair[0].x + pair[1].x) / 2 - bounds.left;
      const y = (pair[0].y + pair[1].y) / 2 - bounds.top;
      const level = Math.max(minZoom, Math.min(maxZoom, pinch.zoom + Math.log2(dist / pinch.distance)));
      setZoomImmediate(level, x, y);
      targetZoom = zoom;
    } else if (pointers.size === 1 && dragging && dragging.id === event.pointerId) {
      center.x -= event.clientX - old.x;
      center.y -= event.clientY - old.y;
      dragging.x = event.clientX;
      dragging.y = event.clientY;
      draw();
    }
  });

  function releasePointer(event) {
    pointers.delete(event.pointerId);
    pinch = null;
    dragging = null;
    if (pointers.size === 1) {
      const remaining = pointers.entries().next().value;
      dragging = { id: remaining[0], x: remaining[1].x, y: remaining[1].y };
    }
  }
  root.addEventListener('pointerup', releasePointer);
  root.addEventListener('pointercancel', releasePointer);
  root.addEventListener('lostpointercapture', releasePointer);

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
      fitRoute();
      draw();
    }
  });

  if (typeof ResizeObserver === 'function') new ResizeObserver(draw).observe(root);
  else window.addEventListener('resize', draw);
  fitRoute();
  draw();
})();
