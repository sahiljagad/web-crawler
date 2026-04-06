// TODO: Replace these with your Supabase project values
const SUPABASE_URL = "https://gsolgdkybvufrjdnkris.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_BHlZERAwyN7-Dc5VubeyBA_zX1S5FjW";
const NTFY_TOPIC = "bayarea-events";

const eventsContainer = document.getElementById("events");
const filterDate = document.getElementById("filter-date");
const filterPrice = document.getElementById("filter-price");
const filterLocation = document.getElementById("filter-location");
const subscribeLink = document.getElementById("subscribe-link");

let allEvents = [];

subscribeLink.href = `https://ntfy.sh/${NTFY_TOPIC}`;

async function fetchEvents() {
  try {
    const url = `${SUPABASE_URL}/rest/v1/events?select=*&order=event_date.asc`;
    const response = await fetch(url, {
      headers: {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`
      }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    allEvents = await response.json();
    applyFilters();
  } catch (err) {
    eventsContainer.innerHTML = `<div class="empty-state">Failed to load events. Try again later.</div>`;
    console.error("Fetch error:", err);
  }
}

function applyFilters() {
  let filtered = allEvents;

  const dateVal = filterDate.value;
  if (dateVal) {
    filtered = filtered.filter(e => e.event_date === dateVal);
  }

  const priceVal = filterPrice.value;
  if (priceVal) {
    filtered = filtered.filter(e =>
      e.price && e.price.toLowerCase().includes(priceVal.toLowerCase())
    );
  }

  const locVal = filterLocation.value.toLowerCase().trim();
  if (locVal) {
    filtered = filtered.filter(e =>
      e.location && e.location.toLowerCase().includes(locVal)
    );
  }

  renderEvents(filtered);
}

function formatDate(dateStr) {
  if (!dateStr) return "TBD";
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric"
  });
}

function renderEvents(events) {
  if (events.length === 0) {
    eventsContainer.innerHTML = `<div class="empty-state">No events found</div>`;
    return;
  }

  eventsContainer.innerHTML = events.map(event => `
    <div class="event-card">
      <div class="event-name">${escapeHtml(event.name)}</div>
      <div class="event-details">
        <div class="event-row">${formatDate(event.event_date)}</div>
        <div class="event-row">${escapeHtml(event.start_time || "")}</div>
        <div class="event-row">${escapeHtml(event.location || "Location TBD")}</div>
      </div>
      ${event.price ? `<span class="price-badge">${escapeHtml(event.price)}</span>` : ""}
      ${event.website ? `<a class="event-link" href="${escapeHtml(event.website)}" target="_blank" rel="noopener">Get Tickets</a>` : ""}
    </div>
  `).join("");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Filter listeners
filterDate.addEventListener("change", applyFilters);
filterPrice.addEventListener("change", applyFilters);

let locationTimeout;
filterLocation.addEventListener("input", () => {
  clearTimeout(locationTimeout);
  locationTimeout = setTimeout(applyFilters, 300);
});

// Init
fetchEvents();
