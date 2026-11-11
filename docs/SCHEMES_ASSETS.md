# Схемы подключения Phantom — происхождение и ограничения изображений

Актуально: 12.11.2026. Рабочая страница — `connection-schemes.html`; материалы — `assets/schemes/`.

| Якорь страницы | Локальный файл | Официальный источник МДИС | Размер WebP |
|---|---|---|---|
| `#ip-principle` | `ip-principle.webp` | https://mdis.ru/upload/iblock/915/915427e39cbd70c1a371d10f7932f0d9.jpg | 1884×1134 |
| `#tricom` | `tricom-gip.webp` | https://mdis.ru/upload/iblock/5a1/5a15cd438461e2d75dce96cb3b8b65bb.jpg | 1872×1281 |
| `#minicom` | `minicom-dx500.webp` | https://mdis.ru/upload/iblock/3d7/3d7b42155ad929c99107cd6fc51fccd2.JPG | 2400×1692 |
| `#protocols` | `protocols-sip-h323.webp` | https://mdis.ru/upload/iblock/1ef/1efeaa68c3d7e8f73fb15c9c16bf34fa.jpg | 2232×1182 |

Изображения получены из опубликованных оригиналов; в разовом workflow `build-phantom-schemes.yml` использовались Pillow 11.3.0, увеличение с Lanczos (максимум 3×, длинная сторона до 2400 px), UnsharpMask (radius 1.1, percent 145, threshold 2), WebP quality 91 и method 6. После получения файлов разовый workflow удалён из активной GitHub Actions конфигурации для предотвращения случайного повторного изменения материалов.

**Важно:** увеличение пиксельных размеров и sharpening не восстанавливают детали, которых нет в исходном JPG, и не делают изображение векторным. Убедиться в точности мелких надписей и трассировки линий можно только по оригиналам. Ранее в беседе были созданы отдельные изображения с ИИ-перерисовкой; **они не интегрированы** в техническую страницу из-за риска изменения схемной топологии, маркировок и подключений.

В HTML есть ссылки на официальные JPG и переключение на источник при ошибке загрузки локального WebP. Однако визуально работающий fallback **не подтверждает**, что новый WebP был загружен на AEZA; нужно проверять HTTP 200 и SHA-256 для локальных ресурсов отдельно.

Официальные карточки:
- https://mdis.ru/catalog/product/printsipialnaya-skhema-registratsii-ip-trafika/
- https://mdis.ru/catalog/product/minikom-/ — опытный стенд ТРИКОМ GIP, несмотря на исторический slug URL
- https://mdis.ru/catalog/product/skhemy-podklyucheniya/ — МиниКом DX500
- https://mdis.ru/catalog/product/registratsiya-ip-trafika-s-raznymi-protokolami/
