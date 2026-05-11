async function loadAdminDashboard() {
    requireAuth("admin");
    const data = await api("/simulation/analytics");
    document.querySelector("#metrics").innerHTML = `
        <div class="card metric">Total drones<strong>${data.total_drones}</strong></div>
        <div class="card metric">Active deliveries<strong>${data.active_deliveries}</strong></div>
        <div class="card metric">Failed deliveries<strong>${data.failed_deliveries}</strong></div>
        <div class="card metric">Average battery<strong>${data.average_battery}%</strong></div>
        <div class="card metric">Busiest hub<strong>${data.busiest_hub}</strong></div>
    `;
    drawHubChart(data.hub_stats);
}

function drawHubChart(rows) {
    const canvas = document.querySelector("#hubChart");
    const ctx = canvas.getContext("2d");
    canvas.width = canvas.clientWidth * devicePixelRatio;
    canvas.height = 220 * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio);
    ctx.clearRect(0, 0, canvas.clientWidth, 220);
    const max = Math.max(1, ...rows.map(r => r.order_density));
    rows.forEach((row, i) => {
        const w = (row.order_density / max) * (canvas.clientWidth - 170);
        const y = 22 + i * 30;
        ctx.fillStyle = "#26313a";
        ctx.fillText(row.name.replace(" Hub", ""), 10, y + 12);
        ctx.fillStyle = "#21a67a";
        ctx.fillRect(130, y, w, 16);
        ctx.fillStyle = "#182026";
        ctx.fillText(row.order_density, 138 + w, y + 12);
    });
}

async function loadDrones() {
    requireAuth("admin");
    const drones = await api("/drones");
    const hubs = await api("/darkstores");
    document.querySelector("#hubOptions").innerHTML = hubs.map(h => `<option value="${h.id}">${h.name}</option>`).join("");
    document.querySelector("#dronesBody").innerHTML = drones.map(d => `
        <tr>
            <td>${d.id}</td><td>${d.model}</td><td>${d.status}</td><td>${d.current_battery}%</td>
            <td>${d.max_payload} kg</td><td>${d.latitude.toFixed(4)}, ${d.longitude.toFixed(4)}</td>
            <td><button class="danger" data-delete="${d.id}">Delete</button></td>
        </tr>
    `).join("");
    document.querySelector("#dronesBody").onclick = async event => {
        if (!event.target.dataset.delete) return;
        await api(`/drones/delete/${event.target.dataset.delete}`, { method: "DELETE" });
        loadDrones();
    };
    document.querySelector("#droneForm").onsubmit = async event => {
        event.preventDefault();
        const form = event.target;
        await api("/drones/add", {
            method: "POST",
            body: JSON.stringify({
                model: form.model.value,
                max_payload: Number(form.max_payload.value),
                max_range: Number(form.max_range.value),
                battery_capacity: 100,
                current_battery: Number(form.current_battery.value),
                latitude: Number(form.latitude.value),
                longitude: Number(form.longitude.value),
                dark_store_id: Number(form.dark_store_id.value)
            })
        });
        form.reset();
        loadDrones();
    };
}

async function setupAirspace() {
    requireAuth("admin");
    const map = hyderabadMap("map", 11);
    addMapSearchControl(map, picked => {
        map.setView([picked.lat, picked.lng], 15);
        L.circleMarker([picked.lat, picked.lng], { radius: 6, color: "#2f6fed" }).addTo(map).bindPopup(picked.label).openPopup();
    }, "Search admin map");
    await drawHubs(map);
    const zones = await drawZones(map);
    document.querySelector("#zonesList").innerHTML = zones.map(z => `<div class="card"><strong>${z.name}</strong><p>${z.zone_type}</p><button class="danger" data-zone="${z.id}">Delete</button></div>`).join("");
    let points = [];
    let preview = null;
    map.on("click", e => {
        points.push([e.latlng.lat, e.latlng.lng]);
        if (preview) preview.remove();
        preview = L.polygon(points, { color: "#2f6fed" }).addTo(map);
    });
    document.querySelector("#zoneForm").onsubmit = async event => {
        event.preventDefault();
        if (points.length < 3) return toast("Draw at least three points");
        await api("/zones/create", {
            method: "POST",
            body: JSON.stringify({ name: event.target.name.value, zone_type: event.target.zone_type.value, coordinates: points })
        });
        location.reload();
    };
    document.querySelector("#clearZone").onclick = () => {
        points = [];
        if (preview) preview.remove();
    };
    document.querySelector("#zonesList").onclick = async event => {
        if (!event.target.dataset.zone) return;
        await api(`/zones/${event.target.dataset.zone}`, { method: "DELETE" });
        location.reload();
    };
}

async function setupSimulation() {
    requireAuth("admin");
    const config = await api("/simulation/config");
    const form = document.querySelector("#simForm");
    form.failure_probability.value = config.failure_probability;
    form.telemetry_interval.value = config.telemetry_interval;
    form.max_orders.value = config.max_orders;
    document.querySelector("#simState").textContent = config.running ? "Running" : "Stopped";
    document.querySelector("#startSim").onclick = async () => {
        await api("/simulation/start", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(form))) });
        toast("Simulation started");
        document.querySelector("#simState").textContent = "Running";
    };
    document.querySelector("#stopSim").onclick = async () => {
        await api("/simulation/stop", { method: "POST" });
        toast("Simulation stopped");
        document.querySelector("#simState").textContent = "Stopped";
    };
}

async function setupLiveMap() {
    requireAuth("admin");
    const map = hyderabadMap("map", 11);
    addMapSearchControl(map, picked => {
        map.setView([picked.lat, picked.lng], 15);
        L.circleMarker([picked.lat, picked.lng], { radius: 6, color: "#2f6fed" }).addTo(map).bindPopup(picked.label).openPopup();
    }, "Search Hyderabad operations");
    await drawHubs(map);
    await drawZones(map);
    const orders = await api("/orders/list");
    orders.forEach(o => {
        if (o.route_points && o.route_points.length) L.polyline(o.route_points, { color: o.status === "Delivered" ? "#21a67a" : "#2f6fed", opacity: .65 }).addTo(map);
    });
    const drones = new Map();
    if (window.io) {
        const socket = io(SOCKET_BASE, { path: "/socket.io" });
        socket.on("operations", payload => upsertDrone(map, drones, payload));
    }
}

function upsertDrone(map, drones, payload) {
    let marker = drones.get(payload.drone_id);
    if (!marker) {
        marker = L.marker([payload.latitude, payload.longitude], { icon: droneIcon() }).addTo(map);
        drones.set(payload.drone_id, marker);
    }
    animateMarker(marker, [payload.latitude, payload.longitude]);
    marker.bindPopup(`Drone ${payload.drone_id}<br>${payload.status}<br>Battery ${payload.battery}%`);
}
