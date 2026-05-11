const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api`;
const WS_BASE = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.hostname}:8000`;
const SOCKET_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;

function getToken() {
    return localStorage.getItem("token");
}

function getUser() {
    try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; }
}

function saveSession(data) {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    location.href = "/pages/login.html";
}

async function api(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
}

function requireAuth(role) {
    const user = getUser();
    if (!user || !getToken()) location.href = "/pages/login.html";
    if (role && user.role !== role) location.href = "/pages/customer_dashboard.html";
    const el = document.querySelector("[data-user]");
    if (el && user) el.textContent = `${user.name} (${user.role})`;
}

function toast(message) {
    let node = document.querySelector(".toast");
    if (!node) {
        node = document.createElement("div");
        node.className = "toast";
        document.body.appendChild(node);
    }
    node.textContent = message;
    node.classList.add("show");
    setTimeout(() => node.classList.remove("show"), 2600);
}

function hyderabadMap(id, zoom = 11) {
    const map = L.map(id).setView([17.4065, 78.4772], zoom);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
    }).addTo(map);
    map.setMaxBounds([[17.20, 78.20], [17.62, 78.68]]);
    return map;
}

function isHyderabadPoint(lat, lng) {
    return lat >= 17.20 && lat <= 17.62 && lng >= 78.20 && lng <= 78.68;
}

function haversineKm(a, b) {
    const radius = 6371;
    const toRad = value => value * Math.PI / 180;
    const dLat = toRad(b[0] - a[0]);
    const dLng = toRad(b[1] - a[1]);
    const lat1 = toRad(a[0]);
    const lat2 = toRad(b[0]);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
    return 2 * radius * Math.asin(Math.sqrt(h));
}

function routeDistanceKm(points) {
    return points.slice(1).reduce((sum, point, index) => sum + haversineKm(points[index], point), 0);
}

async function geocodeHyderabad(query) {
    const url = new URL("https://nominatim.openstreetmap.org/search");
    url.searchParams.set("format", "json");
    url.searchParams.set("limit", "5");
    url.searchParams.set("addressdetails", "1");
    url.searchParams.set("bounded", "1");
    url.searchParams.set("viewbox", "78.20,17.62,78.68,17.20");
    url.searchParams.set("q", `${query}, Hyderabad, Telangana, India`);
    const response = await fetch(url);
    if (!response.ok) throw new Error("Address search failed");
    return (await response.json())
        .map(item => ({ label: item.display_name, lat: Number(item.lat), lng: Number(item.lon) }))
        .filter(item => isHyderabadPoint(item.lat, item.lng));
}

function addMapSearchControl(map, onPick, placeholder = "Search Hyderabad address") {
    const control = L.control({ position: "topleft" });
    control.onAdd = () => {
        const wrap = L.DomUtil.create("div", "map-search");
        wrap.innerHTML = `
            <input type="search" placeholder="${placeholder}">
            <button type="button">Search</button>
            <div class="map-results"></div>
        `;
        L.DomEvent.disableClickPropagation(wrap);
        const input = wrap.querySelector("input");
        const button = wrap.querySelector("button");
        const results = wrap.querySelector(".map-results");
        async function runSearch() {
            if (!input.value.trim()) return;
            results.innerHTML = `<div class="map-result">Searching...</div>`;
            try {
                const matches = await geocodeHyderabad(input.value.trim());
                results.innerHTML = matches.length ? matches.map((m, i) => `<button type="button" class="map-result" data-i="${i}">${m.label}</button>`).join("") : `<div class="map-result">No Hyderabad matches found</div>`;
                results.querySelectorAll("[data-i]").forEach(node => {
                    node.onclick = () => {
                        const picked = matches[Number(node.dataset.i)];
                        map.setView([picked.lat, picked.lng], 15);
                        results.innerHTML = "";
                        input.value = picked.label.split(",").slice(0, 2).join(", ");
                        onPick(picked);
                    };
                });
            } catch (error) {
                results.innerHTML = `<div class="map-result">${error.message}</div>`;
            }
        }
        button.onclick = runSearch;
        input.onkeydown = event => {
            if (event.key === "Enter") {
                event.preventDefault();
                runSearch();
            }
        };
        return wrap;
    };
    control.addTo(map);
    return control;
}

function droneIcon() {
    return L.divIcon({ className: "drone-icon", html: "&#9650;", iconSize: [22, 22] });
}

function hubIcon() {
    return L.divIcon({ className: "hub-icon", html: "&#9632;", iconSize: [18, 18] });
}

function animateMarker(marker, target, ms = 900) {
    const start = marker.getLatLng();
    const started = performance.now();
    function step(now) {
        const t = Math.min(1, (now - started) / ms);
        const lat = start.lat + (target[0] - start.lat) * t;
        const lng = start.lng + (target[1] - start.lng) * t;
        marker.setLatLng([lat, lng]);
        if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

async function drawHubs(map) {
    const hubs = await api("/darkstores");
    hubs.forEach(h => {
        L.marker([h.latitude, h.longitude], { icon: hubIcon() }).addTo(map)
            .bindPopup(`<b>${h.name}</b><br>Drones: ${h.drone_count}<br>Active: ${h.active_deliveries}<br>Inventory: ${h.available_stock}`);
    });
    return hubs;
}

async function drawZones(map) {
    const zones = await api("/zones/list");
    zones.forEach(z => {
        L.polygon(z.coordinates, { color: "#d94f4f", fillOpacity: .22 }).addTo(map)
            .bindPopup(`${z.name}<br>${z.zone_type}`);
    });
    return zones;
}
