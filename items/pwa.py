from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.cache import never_cache


def manifest(request):
    """Tells the phone the app's name, colours and icons."""
    data = {
        "id": "/",
        "name": "Campus Lost & Found",
        "short_name": "Lost & Found",
        "description": "Post, find and claim lost items on campus.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#EEF2F1",
        "theme_color": "#14213D",
        "icons": [
            {"src": static("items/icons/icon-192.png"), "sizes": "192x192",
             "type": "image/png", "purpose": "any"},
            {"src": static("items/icons/icon-512.png"), "sizes": "512x512",
             "type": "image/png", "purpose": "any"},
            {"src": static("items/icons/icon-maskable-512.png"), "sizes": "512x512",
             "type": "image/png", "purpose": "maskable"},
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json")


SERVICE_WORKER_JS = """
const CACHE = "lostfound-offline-v1";
const OFFLINE_URL = "/offline/";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.add(new Request(OFFLINE_URL, { cache: "reload" })))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Only page loads are handled. If the network is down, show the offline page.
// Nothing else is stored, so private pages never sit in the phone's cache.
self.addEventListener("fetch", (event) => {
  if (event.request.mode !== "navigate") return;
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE_URL)));
});
"""


@never_cache
def service_worker(request):
    """Served from the site root (/sw.js) so it covers every page."""
    response = HttpResponse(SERVICE_WORKER_JS, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def offline(request):
    return render(request, "items/offline.html")