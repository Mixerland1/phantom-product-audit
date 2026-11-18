/* Карта входа МДИС. Тайлы OpenStreetMap; без внешнего JS и рекламного iframe. */
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
  let zoom = 17;
  let center = project(entrance, zoom);
  let dragging = null;
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

  function draw() {
    const width = root.clientWidth;
    const height = root.clientHeight;
    if (!width || !height) return;
    const left = center.x - width / 2;
    const top = center.y - height / 2;
    const minX = Math.floor(left / tileSize);
    const maxX = Math.floor((left + width) / tileSize);
    const minY = Math.floor(top / tileSize);
    const maxY = Math.floor((top + height) / tileSize);
    const extent = Math.pow(2, zoom);
    const visible = new Set();

    for (let y = minY; y <= maxY; y++) {
      if (y < 0 || y >= extent) continue;
      for (let x = minX; x <= maxX; x++) {
        const wrapped = ((x % extent) + extent) % extent;
        const key = zoom + '/' + wrapped + '/' + y;
        visible.add(key);
        let image = tiles.get(key);
        if (!image) {
          image = document.createElement('img');
          image.className = 'office-map-tile';
          image.alt = '';
          image.draggable = false;
          image.decoding = 'async';
          image.referrerPolicy = 'strict-origin-when-cross-origin';
          image.addEventListener('load', function () {
            unavailable.hidden = true;
          });
          image.addEventListener('error', function () {
            image.dataset.failed = '1';
            const current = Array.from(tiles.values());
            if (current.length && current.every(function (item) { return item.dataset.failed === '1'; })) {
              unavailable.hidden = false;
            }
          });
          tiles.set(key, image);
          tileLayer.appendChild(image);
          image.src = 'https://tile.openstreetmap.org/' + zoom + '/' + wrapped + '/' + y + '.png';
        }
        image.style.left = (x * tileSize - left) + 'px';
        image.style.top = (y * tileSize - top) + 'px';
      }
    }
    tiles.forEach(function (image, key) {
      if (!visible.has(key)) {
        image.remove();
        tiles.delete(key);
      }
    });

    const pin = project(entrance, zoom);
    marker.style.left = (pin.x - left) + 'px';
    marker.style.top = (pin.y - top) + 'px';
    zoomIn.disabled = zoom >= maxZoom;
    zoomOut.disabled = zoom <= minZoom;
  }

  function setZoom(level, anchorX, anchorY) {
    level = Math.max(minZoom, Math.min(maxZoom, level));
    if (level === zoom) return;
    const width = root.clientWidth;
    const height = root.clientHeight;
    const point = unproject({
      x: center.x + anchorX - width / 2,
      y: center.y + anchorY - height / 2
    }, zoom);
    zoom = level;
    const next = project(point, zoom);
    center = {
      x: next.x - anchorX + width / 2,
      y: next.y - anchorY + height / 2
    };
    unavailable.hidden = true;
    draw();
  }

  zoomIn.addEventListener('click', function () {
    setZoom(zoom + 1, root.clientWidth / 2, root.clientHeight / 2);
  });
  zoomOut.addEventListener('click', function () {
    setZoom(zoom - 1, root.clientWidth / 2, root.clientHeight / 2);
  });
  root.addEventListener('wheel', function (event) {
    if (!event.deltaY) return;
    event.preventDefault();
    const bounds = root.getBoundingClientRect();
    setZoom(zoom + (event.deltaY < 0 ? 1 : -1), event.clientX - bounds.left, event.clientY - bounds.top);
  }, { passive: false });

  root.addEventListener('pointerdown', function (event) {
    if (event.target.closest('button, a')) return;
    if (event.button !== 0 && event.pointerType === 'mouse') return;
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
      center.x += moves[event.key][0];
      center.y += moves[event.key][1];
      draw();
    } else if (event.key === '+' || event.key === '=') {
      event.preventDefault();
      setZoom(zoom + 1, root.clientWidth / 2, root.clientHeight / 2);
    } else if (event.key === '-') {
      event.preventDefault();
      setZoom(zoom - 1, root.clientWidth / 2, root.clientHeight / 2);
    } else if (event.key === 'Home') {
      event.preventDefault();
      zoom = 17;
      center = project(entrance, zoom);
      draw();
    }
  });

  if (typeof ResizeObserver === 'function') new ResizeObserver(draw).observe(root);
  else window.addEventListener('resize', draw);
  draw();
})();
