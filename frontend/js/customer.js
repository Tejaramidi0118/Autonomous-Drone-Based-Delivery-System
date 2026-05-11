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
    root.innerHTML = unique.map(p => `
        <article class="card product">
            <span class="badge">${p.category}</span>
            <h3>${p.name}</h3>
            <p class="muted">${p.weight_kg} kg pack</p>
            <div class="row"><strong>Rs. ${p.price}</strong><button data-add="${p.id}">Add</button></div>
        </article>
    `).join("");
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
    L.polyline(order.route_points, { color: "#2f6fed", weight: 4 }).addTo(map);
    L.marker([order.dropoff_lat, order.dropoff_lng]).addTo(map).bindPopup("Delivery");
    const marker = L.marker([order.pickup_lat, order.pickup_lng], { icon: droneIcon() }).addTo(map).bindPopup("Drone");
    map.fitBounds(order.route_points);
    updateTracking(order);

    if (window.io) {
        const socket = io(SOCKET_BASE, { path: "/socket.io" });
        socket.emit("subscribe", { order_id: id });
        socket.on("telemetry", payload => {
            if (String(payload.order_id) !== String(id)) return;
            animateMarker(marker, [payload.latitude, payload.longitude]);
            updateTracking(payload);
        });
    } else {
        const ws = new WebSocket(`${WS_BASE}/ws/telemetry/${id}`);
        ws.onmessage = event => {
            const payload = JSON.parse(event.data);
            animateMarker(marker, [payload.latitude, payload.longitude]);
            updateTracking(payload);
        };
    }
}

function updateTracking(data) {
    document.querySelector("#status").textContent = data.status;
    document.querySelector("#battery").textContent = `${data.battery ?? data.predicted_battery_usage}%`;
    document.querySelector("#eta").textContent = `${data.eta_minutes} min`;
    document.querySelector("#drone").textContent = data.drone_id || "Pending assignment";
    const distance = document.querySelector("#distance");
    if (distance && data.distance_km !== undefined) distance.textContent = `${data.distance_km} km`;
}
