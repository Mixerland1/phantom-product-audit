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
