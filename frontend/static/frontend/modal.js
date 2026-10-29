// Machine modal: status pills, file upload and file list.

import { api } from "./api.js";
import { escapeAttribute, icons, illustrationMarkup } from "./icons.js";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([hidden]), [tabindex]:not([tabindex="-1"])';

/** Escape text for safe insertion into HTML. */
function escapeHtml(value) {
  return escapeAttribute(value).replaceAll("'", "&#39;");
}

/** Build an element from an HTML string. */
function html(markup) {
  const template = document.createElement("template");
  template.innerHTML = markup.trim();
  return template.content.firstElementChild;
}

/**
 * Open the modal of a machine.
 *
 * @param {object} machine Machine as returned by the API.
 * @param {object} options
 * @param {object|null} [options.initialStatus] Last known status (from the card), if any.
 * @param {(status: object) => void} [options.onStatus] Called whenever a fresh status is loaded.
 * @param {HTMLElement} [options.returnFocusTo] Element to focus again when the modal closes.
 */
export function openMachineModal(machine, { initialStatus = null, onStatus, returnFocusTo } = {}) {
  const hasStatus = machine.capabilities.includes("status");
  const hasFiles = machine.capabilities.includes("files") && machine.files;

  const state = {
    status: initialStatus,
    statusLoaded: !hasStatus || Boolean(initialStatus),
    files: null,
    filesError: "",
    filter: "",
    uploading: false,
  };

  const titleId = `machine-title-${machine.id}`;
  const subtitle = [machine.description, machine.plant].filter(Boolean).join(" · ");

  const overlay = html(`
    <div class="overlay">
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="${titleId}">
        <div class="dialog__header">
          <div class="dialog__thumb">${illustrationMarkup(machine)}</div>
          <div class="dialog__heading">
            <h2 class="dialog__title" id="${titleId}">${escapeHtml(machine.name)}</h2>
            <p class="dialog__subtitle">${escapeHtml(subtitle)}</p>
          </div>
          <button class="icon-button icon-button--lg dialog__close" type="button" aria-label="Chiudi">${icons.close}</button>
        </div>
        <div class="dialog__pills" data-pills></div>
        <div data-body hidden></div>
      </div>
    </div>
  `);

  const dialog = overlay.querySelector(".dialog");
  const pillsEl = overlay.querySelector("[data-pills]");
  const bodyEl = overlay.querySelector("[data-body]");
  const closeButton = overlay.querySelector(".dialog__close");

  // ----- Status pills -------------------------------------------------------

  function isOnline() {
    return hasStatus ? Boolean(state.status?.online) : true;
  }

  function renderPills() {
    const pills = [];
    if (hasStatus) {
      if (!state.statusLoaded) {
        pills.push(`<span class="pill pill--offline">…</span>`);
      } else if (state.status?.online) {
        pills.push(`<span class="pill pill--online"><span class="dot dot--online"></span>Online</span>`);
        if (!state.status.gadget_active) {
          pills.push(`<span class="pill pill--warning">Chiavetta non visibile al banco</span>`);
        }
      } else {
        const detail = escapeAttribute(state.status?.detail || "");
        pills.push(
          `<span class="pill pill--offline" title="${detail}"><span class="dot"></span>Offline</span>`,
        );
      }
    }
    const count = state.status?.files_count ?? (Array.isArray(state.files) ? state.files.length : null);
    if (hasFiles && count !== null && count !== undefined) {
      pills.push(`<span class="pill">${count} file</span>`);
    }
    pillsEl.innerHTML = pills.join("");
    pillsEl.hidden = pills.length === 0;
  }

  // ----- Body: upload + files -----------------------------------------------

  let dropzone;
  let fileInput;
  let dropzoneText;
  let uploadError;
  let filesError;
  let listEl;
  let filesSearchInput;
  let filesSearchToggle;

  function buildBody() {
    const accept = machine.files.accept || [];
    const acceptText = accept.join(", ");
    const inputId = `file-input-${machine.id}`;

    const upload = html(`
      <section class="dialog__section" aria-labelledby="upload-label-${machine.id}">
        <span class="label" id="upload-label-${machine.id}">Carica piano di taglio</span>
        <label class="dropzone" for="${inputId}">
          <span class="dropzone__icon">${icons.upload}</span>
          <p class="dropzone__text" data-dropzone-text>Trascina qui il file oppure</p>
          <span class="button" data-choose>Scegli file</span>
          <p class="dropzone__hint">Solo ${escapeHtml(acceptText)} · massimo ${machine.files.max_mb} MB</p>
          <input class="dropzone__input" id="${inputId}" type="file" accept="${escapeAttribute(accept.join(","))}">
        </label>
        <p class="error" data-upload-error role="alert"></p>
      </section>
    `);

    const files = html(`
      <section class="dialog__section dialog__section--files" aria-labelledby="files-label-${machine.id}">
        <div class="files__head">
          <span class="label" id="files-label-${machine.id}">File sulla chiavetta</span>
          <div class="files__search">
            <input class="text-input" type="search" placeholder="Cerca file" aria-label="Cerca file" autocomplete="off" hidden>
            <button class="icon-button" type="button" aria-label="Cerca file" aria-expanded="false">${icons.search}</button>
          </div>
        </div>
        <p class="error" data-files-error role="alert"></p>
        <ul class="files__list" data-list></ul>
      </section>
    `);

    dropzone = upload.querySelector(".dropzone");
    fileInput = upload.querySelector("input[type=file]");
    dropzoneText = upload.querySelector("[data-dropzone-text]");
    uploadError = upload.querySelector("[data-upload-error]");
    filesError = files.querySelector("[data-files-error]");
    listEl = files.querySelector("[data-list]");
    filesSearchInput = files.querySelector("input[type=search]");
    filesSearchToggle = files.querySelector(".files__search button");

    // The "Scegli file" button is a <span> inside the <label>: a real button would
    // intercept the label activation. Make it keyboard reachable anyway.
    const choose = upload.querySelector("[data-choose]");
    choose.setAttribute("role", "button");
    choose.tabIndex = 0;
    choose.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        fileInput.click();
      }
    });

    fileInput.addEventListener("change", () => {
      const [file] = fileInput.files;
      if (file) upload_(file);
      fileInput.value = "";
    });

    for (const type of ["dragenter", "dragover"]) {
      dropzone.addEventListener(type, (event) => {
        event.preventDefault();
        if (!state.uploading) dropzone.classList.add("is-dragging");
      });
    }
    for (const type of ["dragleave", "drop"]) {
      dropzone.addEventListener(type, (event) => {
        event.preventDefault();
        dropzone.classList.remove("is-dragging");
      });
    }
    dropzone.addEventListener("drop", (event) => {
      const [file] = event.dataTransfer?.files || [];
      if (file && !state.uploading) upload_(file);
    });

    filesSearchToggle.addEventListener("click", () => {
      const open = filesSearchInput.hidden;
      filesSearchInput.hidden = !open;
      filesSearchToggle.setAttribute("aria-expanded", String(open));
      if (open) {
        filesSearchInput.focus();
      } else {
        filesSearchInput.value = "";
        state.filter = "";
        renderList();
      }
    });
    filesSearchInput.addEventListener("input", () => {
      state.filter = filesSearchInput.value.trim().toLowerCase();
      renderList();
    });
    filesSearchInput.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        filesSearchToggle.click();
        filesSearchToggle.focus();
      }
    });

    listEl.addEventListener("click", (event) => {
      const button = event.target.closest("[data-delete]");
      if (button) remove(button.dataset.delete);
    });

    bodyEl.replaceChildren(upload, files);
  }

  function renderList() {
    if (!listEl) return;
    if (state.files === null) {
      listEl.innerHTML = `<li class="files__empty">Caricamento in corso…</li>`;
      return;
    }
    const visible = state.files.filter((name) => name.toLowerCase().includes(state.filter));
    if (visible.length === 0) {
      listEl.innerHTML = `<li class="files__empty">${
        state.files.length === 0 ? "Nessun file sulla chiavetta" : "Nessun file trovato"
      }</li>`;
      return;
    }
    listEl.innerHTML = visible
      .map(
        (name) => `
        <li class="files__row">
          <span class="files__icon">${icons.file}</span>
          <span class="files__name" title="${escapeAttribute(name)}">${escapeHtml(name)}</span>
          <button class="icon-button icon-button--ghost files__delete" type="button"
                  data-delete="${escapeAttribute(name)}" aria-label="Elimina ${escapeAttribute(name)}">${icons.trash}</button>
        </li>`,
      )
      .join("");
  }

  function renderBody() {
    if (!hasFiles) {
      bodyEl.hidden = true;
      return;
    }
    bodyEl.hidden = false;
    if (!state.statusLoaded) {
      bodyEl.innerHTML = `<p class="dialog__notice">Caricamento in corso…</p>`;
      listEl = null;
      return;
    }
    if (!isOnline()) {
      bodyEl.innerHTML = `<p class="dialog__notice">Macchina non raggiungibile. Riprova più tardi.</p>`;
      listEl = null;
      return;
    }
    if (!listEl) buildBody();
    filesError.textContent = state.filesError;
    renderList();
  }

  function render() {
    renderPills();
    renderBody();
  }

  // ----- Data loading -------------------------------------------------------

  async function refreshStatus() {
    if (!hasStatus) return;
    try {
      state.status = await api.getStatus(machine.id);
    } catch (error) {
      state.status = { online: false, gadget_active: false, files_count: 0, detail: error.message };
    }
    state.statusLoaded = true;
    onStatus?.(state.status);
  }

  async function refreshFiles() {
    if (!hasFiles) return;
    try {
      state.files = await api.listFiles(machine.id);
      state.filesError = "";
    } catch (error) {
      state.files = state.files || [];
      state.filesError = error.message;
    }
  }

  async function refreshAll() {
    await Promise.all([refreshStatus(), refreshFiles()]);
    if (overlay.isConnected) render();
  }

  // ----- Actions ------------------------------------------------------------

  function validate(file) {
    const accept = (machine.files.accept || []).map((ext) => ext.toLowerCase());
    const lowerName = file.name.toLowerCase();
    if (accept.length && !accept.some((ext) => lowerName.endsWith(ext))) {
      return `Formato non supportato. Solo ${accept.join(", ")}`;
    }
    const maxBytes = machine.files.max_mb * 1024 * 1024;
    if (maxBytes && file.size > maxBytes) {
      return `File troppo grande. Massimo ${machine.files.max_mb} MB`;
    }
    return "";
  }

  function setUploading(uploading) {
    state.uploading = uploading;
    if (!dropzone) return;
    dropzone.classList.toggle("is-busy", uploading);
    dropzone.setAttribute("aria-disabled", String(uploading));
    fileInput.disabled = uploading;
    dropzoneText.textContent = uploading ? "Caricamento in corso…" : "Trascina qui il file oppure";
  }

  async function upload_(file) {
    uploadError.textContent = "";
    const problem = validate(file);
    if (problem) {
      uploadError.textContent = problem;
      return;
    }
    setUploading(true);
    try {
      await api.uploadFile(machine.id, file);
      await refreshAll();
    } catch (error) {
      if (overlay.isConnected && uploadError.isConnected) uploadError.textContent = error.message;
    } finally {
      setUploading(false);
    }
  }

  async function remove(name) {
    if (!window.confirm(`Eliminare ${name}?`)) return;
    filesError.textContent = "";
    try {
      await api.deleteFile(machine.id, name);
      await refreshAll();
    } catch (error) {
      if (filesError.isConnected) filesError.textContent = error.message;
    }
  }

  // ----- Open / close / focus management ------------------------------------

  function close() {
    document.removeEventListener("keydown", onKeydown, true);
    overlay.remove();
    document.body.classList.remove("is-modal-open");
    returnFocusTo?.focus?.();
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = [...dialog.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null);
    if (focusable.length === 0) {
      event.preventDefault();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  overlay.addEventListener("mousedown", (event) => {
    if (event.target === overlay) close();
  });
  closeButton.addEventListener("click", close);
  document.addEventListener("keydown", onKeydown, true);

  render();
  document.getElementById("modal-root").append(overlay);
  document.body.classList.add("is-modal-open");
  closeButton.focus();

  refreshAll();

  return { close };
}
