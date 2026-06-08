const cartKey = "cart";
const addressKey = "saved_addresses";

function getCart() {
    return JSON.parse(localStorage.getItem(cartKey) || "[]");
}

function setCart(cart) {
    localStorage.setItem(cartKey, JSON.stringify(cart));
}

function getSavedAddresses() {
    return JSON.parse(localStorage.getItem(addressKey) || "[]");
}

function setSavedAddresses(addresses) {
    localStorage.setItem(addressKey, JSON.stringify(addresses.slice(0, 8)));
}

function saveAddress(label, point) {
    if (!label || !point) return;
    const cleanLabel = label.split(",").slice(0, 3).join(", ");
    const addresses = getSavedAddresses().filter(a => a.label !== cleanLabel);
    addresses.unshift({ label: cleanLabel, lat: point[0], lng: point[1] });
    setSavedAddresses(addresses);
    toast("Address saved");
}

function renderSavedAddresses(containerId, onPick) {
    const root = document.querySelector(containerId);
    if (!root) return;
    const addresses = getSavedAddresses();
    root.innerHTML = addresses.length
        ? addresses.map((a, i) => `<button class="address-chip" type="button" data-address="${i}">${a.label}</button>`).join("")
        : `<p class="muted">No saved addresses yet.</p>`;
    root.onclick = event => {
        const index = event.target.dataset.address;
        if (index === undefined) return;
        const address = getSavedAddresses()[Number(index)];
        onPick(address);
    };
}

async function setupCustomerDashboard() {
    requireAuth("customer");
    const [hubs, orders] = await Promise.all([
        api("/darkstores"),
        api("/orders/list").catch(() => [])
    ]);
    document.querySelector("#hubCount").textContent = `${hubs.length} hubs`;
    const active = orders.filter(o => ["Assigned", "Taking Off", "In Flight", "Delivering", "Reassigned"].includes(o.status));
    document.querySelector("#activeOrders").textContent = `${active.length} active orders`;
    const recentRoot = document.querySelector("#recentOrders");
    recentRoot.innerHTML = orders.length
        ? orders.slice(0, 4).map(order => `
            <a class="order-card" href="/pages/tracking.html?order=${order.id}">
                <span class="badge">${order.status}</span>
                <strong>${order.order_type === "grocery" ? "Grocery order" : "Package delivery"} #${order.id}</strong>
                <p>${order.distance_km} km route | ${order.eta_minutes} min ETA</p>
            </a>
        `).join("")
        : `<div class="empty-state">No orders yet. Start with groceries or send your first package.</div>`;
    document.querySelector("#hubStrip").innerHTML = hubs.map(hub => `
        <article class="hub-card">
            <strong>${hub.name.replace(" Hub", "")}</strong>
            <span>${hub.drone_count} drones</span>
            <span>${hub.active_deliveries} active</span>
            <div class="stock-bar"><i style="width:${Math.min(100, (hub.available_stock / hub.inventory_capacity) * 100)}%"></i></div>
        </article>
    `).join("");
}

async function loadProducts() {
    requireAuth("customer");
    const products = await api("/products");
    const unique = [];
    const seen = new Set();
    products.forEach(p => {
        if (!seen.has(p.name)) {
            seen.add(p.name);
            unique.push(p);
        }
    });
    const root = document.querySelector("#products");
    const search = document.querySelector("#productSearch");
    const tabs = document.querySelector("#categoryTabs");
    let activeCategory = "All";
    const categories = ["All", ...Array.from(new Set(unique.map(p => p.category))).sort()];

    function renderTabs() {
        tabs.innerHTML = categories.map(category => `<button class="category-tab ${category === activeCategory ? "active" : ""}" data-category="${category}">${category}</button>`).join("");
    }

    function renderProducts() {
        const term = (search?.value || "").trim().toLowerCase();
        const filtered = unique.filter(p => {
            const categoryMatch = activeCategory === "All" || p.category === activeCategory;
            const searchMatch = !term || p.name.toLowerCase().includes(term) || p.category.toLowerCase().includes(term);
            return categoryMatch && searchMatch;
        });
        root.innerHTML = filtered.map(p => `
            <article class="card product">
                <div class="product-visual">${p.name.split(" ").map(part => part[0]).join("").slice(0, 2)}</div>
                <span class="badge">${p.category}</span>
                <h3>${p.name}</h3>
                <p class="muted">${p.weight_kg} kg pack | In stock</p>
                <div class="row product-action"><strong>Rs. ${p.price}</strong><button data-add="${p.id}">Add</button></div>
            </article>
        `).join("") || `<div class="empty-state">No products match your search.</div>`;
    }

    renderTabs();
    renderProducts();
    tabs.addEventListener("click", event => {
        const category = event.target.dataset.category;
        if (!category) return;
        activeCategory = category;
        renderTabs();
        renderProducts();
    });
    search?.addEventListener("input", renderProducts);
    root.addEventListener("click", event => {
        const id = Number(event.target.dataset.add);
        if (!id) return;
        const product = unique.find(p => p.id === id);
        const cart = getCart();
        const existing = cart.find(item => item.id === id);
        if (existing) existing.quantity += 1;
        else cart.push({ ...product, quantity: 1 });
        setCart(cart);
        toast("Added to cart");
    });
}

function renderCart() {
    requireAuth("customer");
    const cart = getCart();
    const root = document.querySelector("#cartItems");
    if (!cart.length) {
        root.innerHTML = `<div class="card">Your cart is empty.</div>`;
        return;
    }
    root.innerHTML = cart.map(item => `
        <div class="card row">
            <div style="flex:1"><strong>${item.name}</strong><p class="muted">Rs. ${item.price} x ${item.quantity}</p></div>
            <button class="secondary" data-dec="${item.id}">-</button>
            <span>${item.quantity}</span>
            <button class="secondary" data-inc="${item.id}">+</button>
            <button class="danger" data-remove="${item.id}">Remove</button>
        </div>
    `).join("");
    document.querySelector("#total").textContent = `Rs. ${cart.reduce((s, i) => s + i.price * i.quantity, 0).toFixed(0)}`;
    root.addEventListener("click", event => {
        const cart = getCart();
        const id = Number(event.target.dataset.inc || event.target.dataset.dec || event.target.dataset.remove);
        if (!id) return;
        const item = cart.find(i => i.id === id);
        if (event.target.dataset.inc) item.quantity += 1;
        if (event.target.dataset.dec) item.quantity -= 1;
        const next = event.target.dataset.remove ? cart.filter(i => i.id !== id) : cart.filter(i => i.quantity > 0);
        setCart(next);
        location.reload();
    });
}

async function setupCheckout() {
    requireAuth("customer");
    const map = hyderabadMap("map", 12);
    const hubs = await drawHubs(map);
    await drawZones(map);
    let drop = [17.4065, 78.4772];
    let dropLabel = "Manual pin";
    const marker = L.marker(drop).addTo(map).bindPopup("Delivery location");
    const distanceEl = document.querySelector("#distanceEstimate");

    function updateDrop(point, label = "Manual pin") {
        drop = point;
        dropLabel = label;
        marker.setLatLng(drop).bindPopup(label).openPopup();
        const nearest = hubs.reduce((best, hub) => {
            const distance = haversineKm([hub.latitude, hub.longitude], drop);
            return !best || distance < best.distance ? { hub, distance } : best;
        }, null);
        distanceEl.textContent = nearest ? `${nearest.distance.toFixed(2)} km from ${nearest.hub.name}` : "Select an address";
    }

    addMapSearchControl(map, picked => updateDrop([picked.lat, picked.lng], picked.label));
    renderSavedAddresses("#savedAddresses", address => {
        map.setView([address.lat, address.lng], 15);
        updateDrop([address.lat, address.lng], address.label);
    });
    map.on("click", e => updateDrop([e.latlng.lat, e.latlng.lng]));
    updateDrop(drop, dropLabel);
    document.querySelector("#saveAddress").onclick = () => {
        saveAddress(dropLabel, drop);
        renderSavedAddresses("#savedAddresses", address => {
            map.setView([address.lat, address.lng], 15);
            updateDrop([address.lat, address.lng], address.label);
        });
    };

    document.querySelector("#checkoutForm").addEventListener("submit", async event => {
        event.preventDefault();
        const cart = getCart();
        const weight = cart.reduce((sum, item) => sum + item.weight_kg * item.quantity, 0) || 1;
        try {
            const order = await api("/orders/create", {
                method: "POST",
                body: JSON.stringify({
                    order_type: "grocery",
                    payload_weight: weight,
                    priority: event.target.priority.checked,
                    dropoff_lat: drop[0],
                    dropoff_lng: drop[1],
                    items: cart.map(i => ({ product_id: i.id, name: i.name, quantity: i.quantity }))
                })
            });
            setCart([]);
            location.href = `/pages/tracking.html?order=${order.id}`;
        } catch (error) { toast(error.message); }
    });
}

async function setupPackage() {
    requireAuth("customer");
    const map = hyderabadMap("map", 12);
    await drawHubs(map);
    await drawZones(map);
    let pickup = null;
    let dropoff = null;
    let pickupLabel = "Pickup";
    let dropoffLabel = "Delivery";
    let mode = "pickup";
    let routeLine = null;
    const markers = {};
    const distanceEl = document.querySelector("#packageDistance");

    function setMode(next) {
        mode = next;
        document.querySelectorAll("[data-mode]").forEach(btn => btn.classList.toggle("selected", btn.dataset.mode === mode));
    }

    function setPoint(kind, point, label) {
        if (kind === "pickup") {
            pickup = point;
            pickupLabel = label || "Pickup";
        } else {
            dropoff = point;
            dropoffLabel = label || "Delivery";
        }
        if (!markers[kind]) markers[kind] = L.marker(point).addTo(map);
        markers[kind].setLatLng(point).bindPopup(label || kind).openPopup();
        if (pickup && dropoff) {
            if (routeLine) routeLine.remove();
            routeLine = L.polyline([pickup, dropoff], { color: "#2f6fed", dashArray: "6 6" }).addTo(map);
            distanceEl.textContent = `${haversineKm(pickup, dropoff).toFixed(2)} km direct estimate`;
        }
    }

    setMode("pickup");
    document.querySelectorAll("[data-mode]").forEach(btn => btn.onclick = () => setMode(btn.dataset.mode));
    addMapSearchControl(map, picked => setPoint(mode, [picked.lat, picked.lng], picked.label), "Search pickup or delivery");
    renderSavedAddresses("#savedAddresses", address => {
        map.setView([address.lat, address.lng], 15);
        setPoint(mode, [address.lat, address.lng], address.label);
    });
    map.on("click", e => setPoint(mode, [e.latlng.lat, e.latlng.lng], mode === "pickup" ? "Pickup pin" : "Delivery pin"));
    const rerenderPackageAddresses = () => renderSavedAddresses("#savedAddresses", address => {
        map.setView([address.lat, address.lng], 15);
        setPoint(mode, [address.lat, address.lng], address.label);
    });
    document.querySelector("#savePickup").onclick = () => {
        if (pickup) {
            saveAddress(pickupLabel, pickup);
            rerenderPackageAddresses();
        }
    };
    document.querySelector("#saveDropoff").onclick = () => {
        if (dropoff) {
            saveAddress(dropoffLabel, dropoff);
            rerenderPackageAddresses();
        }
    };

    document.querySelector("#packageForm").addEventListener("submit", async event => {
        event.preventDefault();
        if (!pickup || !dropoff) return toast("Select pickup and delivery points");
        try {
            const order = await api("/orders/create", {
                method: "POST",
                body: JSON.stringify({
                    order_type: "package",
                    pickup_lat: pickup[0],
                    pickup_lng: pickup[1],
                    dropoff_lat: dropoff[0],
                    dropoff_lng: dropoff[1],
                    payload_weight: Number(event.target.weight.value),
                    priority: event.target.priority.checked,
                    fragile: event.target.fragile.checked,
                    items: [{ type: event.target.package_type.value }]
                })
            });
            location.href = `/pages/tracking.html?order=${order.id}`;
        } catch (error) { toast(error.message); }
    });
}

async function setupTracking() {
    requireAuth();
    const id = new URLSearchParams(location.search).get("order");
    const order = await api(`/orders/status/${id}`);
    const map = hyderabadMap("map", 13);
    await drawHubs(map);
    await drawZones(map);

    // Draw planned route
    if (order.route_points && order.route_points.length > 1) {
        L.polyline(order.route_points, { color: "#2f6fed", weight: 3, opacity: 0.6 }).addTo(map);
    }

    // Dropoff marker
    L.marker([order.dropoff_lat, order.dropoff_lng], {
        icon: L.divIcon({ className: "", html: `<div style="background:#e84040;color:#fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:bold;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)">D</div>`, iconSize:[22,22], iconAnchor:[11,11] })
    }).addTo(map).bindPopup("Delivery point");

    // Drone marker — start at pickup or first known position
    const startPos = [order.pickup_lat, order.pickup_lng];
    const marker = L.marker(startPos, { icon: droneIcon(0) }).addTo(map).bindPopup(`Drone ${order.drone_id}`);
    if (order.route_points && order.route_points.length > 1) {
        map.fitBounds(order.route_points, { padding: [40, 40] });
    }
    updateTracking(order);

    // Travelled path line — grows as drone moves
    const travelPath = L.polyline([], { color: "#0f6e56", weight: 2.5, opacity: 0.9 }).addTo(map);
    const visitedCoords = [];

    // Local ETA countdown ticker — decrements every second between WebSocket ticks
    let localEta = parseFloat(order.eta_minutes) || 0;
    let lastEtaUpdate = Date.now();
    const etaEl = document.querySelector("#eta");
    const etaTicker = setInterval(() => {
        const elapsed = (Date.now() - lastEtaUpdate) / 60000; // minutes elapsed
        localEta = Math.max(0, localEta - elapsed);
        lastEtaUpdate = Date.now();
        if (etaEl && localEta > 0) {
            etaEl.textContent = `${localEta.toFixed(1)} min`;
        }
    }, 1000);

    function handleTelemetry(payload) {
        if (String(payload.order_id) !== String(id)) return;

        // Physics-speed animation — uses real speed from engine
        const speedKmh = payload.speed_kmh || payload.speed || 38;
        const heading = payload.latitude && marker.getLatLng()
            ? Math.atan2(
                payload.longitude - marker.getLatLng().lng,
                payload.latitude  - marker.getLatLng().lat)
            : 0;
        animateMarker(marker, [payload.latitude, payload.longitude], speedKmh, heading);

        // Grow travelled path
        visitedCoords.push([payload.latitude, payload.longitude]);
        travelPath.setLatLngs(visitedCoords);

        // Reset local ETA countdown to server value
        if (payload.eta_minutes !== undefined) {
            localEta = parseFloat(payload.eta_minutes);
            lastEtaUpdate = Date.now();
        }

        updateTracking(payload);

        // Stop ticker on completion
        if (payload.status === "Delivered" || payload.status === "Failed") {
            clearInterval(etaTicker);
        }
    }

    if (window.io) {
        const socket = io(SOCKET_BASE, { path: "/socket.io" });
        socket.emit("subscribe", { order_id: id });
        socket.on("telemetry", handleTelemetry);
    } else {
        const ws = new WebSocket(`${WS_BASE}/ws/telemetry/${id}`);
        ws.onmessage = event => handleTelemetry(JSON.parse(event.data));
    }
}

function updateTracking(data) {
    const status = document.querySelector("#status");
    if (status) status.textContent = data.status || "—";

    const battery = document.querySelector("#battery");
    if (battery) {
        const pct = data.battery ?? data.predicted_battery_usage ?? 0;
        const color = pct > 50 ? "#2e7d32" : pct > 25 ? "#e65100" : "#c62828";
        battery.innerHTML = `<span style="color:${color}">${parseFloat(pct).toFixed(1)}%</span>`;
    }

    // ETA: only update the DOM here on initial load; live countdown is handled by ticker
    const etaEl = document.querySelector("#eta");
    if (etaEl && data.eta_minutes !== undefined && !window._etaTickerRunning) {
        etaEl.textContent = `${parseFloat(data.eta_minutes).toFixed(1)} min`;
    }

    const drone = document.querySelector("#drone");
    if (drone) drone.textContent = data.drone_id || "Pending";

    const distance = document.querySelector("#distance");
    if (distance && data.distance_km !== undefined) {
        distance.textContent = `${parseFloat(data.distance_km).toFixed(2)} km`;
    }

    // Show speed if element exists (optional enhancement)
    const speed = document.querySelector("#speed");
    if (speed && (data.speed_kmh || data.speed)) {
        speed.textContent = `${parseFloat(data.speed_kmh || data.speed).toFixed(0)} km/h`;
    }
}

async function setupOrders() {
    requireAuth("customer");
    const orders = await api("/orders/list").catch(() => []);
    
    const activeOrders = orders.filter(o => ["Assigned", "Taking Off", "In Flight", "Delivering", "Reassigned"].includes(o.status));
    const pastOrders = orders.filter(o => ["Delivered", "Failed", "Cancelled"].includes(o.status) || o.status === "Pending");
    
    const activeRoot = document.querySelector("#activeOrdersList");
    const pastRoot = document.querySelector("#pastOrdersList");
    
    activeRoot.innerHTML = activeOrders.length
        ? activeOrders.map(order => `
            <div class="order-card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <span class="badge" style="margin-bottom: 8px;">${order.status}</span>
                    <strong>${order.order_type === "grocery" ? "Grocery order" : "Package delivery"} #${order.id}</strong>
                    <p>${order.distance_km} km route | ${order.eta_minutes} min ETA</p>
                </div>
                <a href="/pages/tracking.html?order=${order.id}" class="nav-link active" style="margin-top: 16px; text-align: center; justify-content: center;">Track Order</a>
            </div>
        `).join("")
        : `<div class="empty-state">You have no active orders.</div>`;
        
    pastRoot.innerHTML = pastOrders.length
        ? pastOrders.map(order => `
            <div class="order-card">
                <span class="badge ${order.status === 'Failed' ? 'status-danger' : ''}" style="margin-bottom: 8px;">${order.status}</span>
                <strong>${order.order_type === "grocery" ? "Grocery order" : "Package delivery"} #${order.id}</strong>
                <p>${new Date(order.created_at).toLocaleDateString()}</p>
                <p>${order.distance_km} km route</p>
            </div>
        `).join("")
        : `<div class="empty-state">You have no past orders.</div>`;
}