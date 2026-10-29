// Entry point: renders the machine grid, header search and opens the machine modal.

import { api } from "./api.js";
import { escapeAttribute, icons, illustrationMarkup } from "./icons.js";
import { openMachineModal } from "./modal.js";

const grid = document.getElementById("machines");
const header = document.querySelector(".header");
const searchToggle = document.getElementById("machine-search-toggle");
const searchInput = document.getElementById("machine-search-input");

/** @type {Map<number, object>} Latest known status per machine id. */
const statuses = new Map();
/** @type {Map<number, HTMLElement>} Card element per machine id. */
const cards = new Map();
let machines = [];

/** Escape text for safe insertion into HTML. */
function escapeHtml(value) {
  return escapeAttribute(value).replaceAll("'", "&#39;");
}

// ----- Cards ----------------------------------------------------------------

/** Build the card of a machine. */
function createCard(machine) {
  const hasStatus = machine.capabilities.includes("status");
  const card = document.createElement("button");
  card.type = "button";
  card.className = "card";
  card.dataset.id = machine.id;
  card.setAttribute("aria-haspopup", "dialog");
  card.innerHTML = `
    <div class="card__illustration">${illustrationMarkup(machine)}</div>
    <div class="card__body">
      <div>
        <h2 class="card__name">${escapeHtml(machine.name)}</h2>
        ${machine.description ? `<p class="card__description">${escapeHtml(machine.description)}</p>` : ""}
      </div>
      <dl class="card__meta">
        <div class="card__field">
          <dt class="label">Stabilimento</dt>
          <dd class="card__value" title="${escapeAttribute(machine.plant || "")}">${escapeHtml(machine.plant || "—")}</dd>
        </div>
        <div class="card__field">
          <dt class="label">Stato</dt>
          <dd class="card__value" data-status>${hasStatus ? "…" : "—"}</dd>
        </div>
      </dl>
    </div>
  `;
  card.addEventListener("click", () => {
    openMachineModal(machine, {
      initialStatus: statuses.get(machine.id) ?? null,
      onStatus: (status) => setCardStatus(machine.id, status),
      returnFocusTo: card,
    });
  });
  return card;
}

/** Update the "Stato" field of a card. */
function setCardStatus(machineId, status) {
  statuses.set(machineId, status);
  const card = cards.get(machineId);
  if (!card) return;
  const value = card.querySelector("[data-status]");
  const online = Boolean(status?.online);
  value.className = `card__value ${online ? "card__value--online" : "card__value--offline"}`;
  value.innerHTML = `<span class="dot ${online ? "dot--online" : ""}"></span>${online ? "Online" : "Offline"}`;
  value.title = online ? "" : status?.detail || "";
}

/** Load the status of every machine supporting it, all in parallel. */
function loadStatuses() {
  const jobs = machines
    .filter((machine) => machine.capabilities.includes("status"))
    .map(async (machine) => {
      try {
        setCardStatus(machine.id, await api.getStatus(machine.id));
      } catch (error) {
        setCardStatus(machine.id, { online: false, detail: error.message });
      }
    });
  return Promise.allSettled(jobs);
}

/** Render the grid: cards, empty state or error state. */
function renderGrid() {
  cards.clear();
  grid.replaceChildren();
  if (machines.length === 0) {
    grid.innerHTML = `<p class="grid__message">Nessun macchinario disponibile</p>`;
    return;
  }
  for (const machine of machines) {
    const card = createCard(machine);
    cards.set(machine.id, card);
    grid.append(card);
  }
  applyFilter();
}

function renderError() {
  grid.innerHTML = `
    <p class="grid__message">
      <span>Impossibile caricare i macchinari</span>
      <button class="button button--outline" type="button" data-retry>Riprova</button>
    </p>`;
  grid.querySelector("[data-retry]").addEventListener("click", load);
}

async function load() {
  grid.setAttribute("aria-busy", "true");
  try {
    machines = await api.listMachines();
  } catch {
    grid.setAttribute("aria-busy", "false");
    renderError();
    return;
  }
  renderGrid();
  grid.setAttribute("aria-busy", "false");
  await loadStatuses();
}

// ----- Header search ----------------------------------------------------------

function applyFilter() {
  const query = searchInput.value.trim().toLowerCase();
  for (const machine of machines) {
    const card = cards.get(machine.id);
    if (!card) continue;
    const haystack = `${machine.name} ${machine.description || ""}`.toLowerCase();
    card.hidden = query !== "" && !haystack.includes(query);
  }
  const anyVisible = machines.some((machine) => !cards.get(machine.id)?.hidden);
  let empty = grid.querySelector("[data-no-match]");
  if (!anyVisible && machines.length > 0) {
    if (!empty) {
      empty = document.createElement("p");
      empty.className = "grid__message";
      empty.dataset.noMatch = "";
      empty.textContent = "Nessun macchinario trovato";
      grid.append(empty);
    }
  } else {
    empty?.remove();
  }
}

function openSearch() {
  searchInput.hidden = false;
  searchToggle.setAttribute("aria-expanded", "true");
  header.classList.add("is-search-open");
  searchInput.focus();
}

function closeSearch({ refocus = true } = {}) {
  searchInput.value = "";
  searchInput.hidden = true;
  searchToggle.setAttribute("aria-expanded", "false");
  header.classList.remove("is-search-open");
  applyFilter();
  if (refocus) searchToggle.focus();
}

searchToggle.innerHTML = icons.search;
searchToggle.addEventListener("click", () => {
  if (searchInput.hidden) {
    openSearch();
  } else {
    closeSearch();
  }
});
searchInput.addEventListener("input", applyFilter);
searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    closeSearch();
  }
});
searchInput.addEventListener("blur", () => {
  if (searchInput.value.trim() === "") closeSearch({ refocus: false });
});

load();
