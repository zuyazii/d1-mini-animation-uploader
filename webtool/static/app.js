/* eslint-disable no-console */
const state = {
  frames: [],
  isBuilding: false,
};

const elements = {
  uploadForm: document.querySelector("#upload-form"),
  framesGrid: document.querySelector("#frames-grid"),
  buildBtn: document.querySelector("#build-btn"),
  buildLog: document.querySelector("#build-log"),
  alert: document.querySelector("#alert"),
  frameCount: document.querySelector("#frame-count"),
  refreshBtn: document.querySelector("#refresh-btn"),
  clearAllBtn: document.querySelector("#clear-all-btn"),
  unifiedDelay: document.querySelector("#unified-delay"),
  applyUnifiedDelayBtn: document.querySelector("#apply-unified-delay"),
};

const DEFAULT_DELAY = window.APP_CONFIG?.defaultDelay ?? 1000;
let alertTimer = null;

function showAlert(message, type = "info", duration = 4000) {
  const el = elements.alert;
  if (!el) return;
  el.textContent = message;
  el.className = "";
  el.classList.add("show");
  if (type !== "info") {
    el.classList.add(type);
  }
  clearTimeout(alertTimer);
  alertTimer = setTimeout(() => {
    el.className = "";
  }, duration);
}

async function request(url, options = {}) {
  const opts = { ...options };
  opts.headers = new Headers(options.headers || {});
  if (!(opts.body instanceof FormData)) {
    if (opts.body && !opts.headers.has("Content-Type")) {
      opts.headers.set("Content-Type", "application/json");
    }
  }
  if (!opts.headers.has("Accept")) {
    opts.headers.set("Accept", "application/json");
  }

  const response = await fetch(url, opts);
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (error) {
      console.error("Failed to parse response JSON", error);
    }
  }

  if (!response.ok) {
    const detail = (data?.detail ?? text) || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function renderFrames() {
  const grid = elements.framesGrid;
  if (!grid) return;
  
  grid.innerHTML = "";

  if (!state.frames.length) {
    const emptyMsg = document.createElement("div");
    emptyMsg.className = "empty-message";
    emptyMsg.textContent = "No frames have been uploaded yet.";
    grid.appendChild(emptyMsg);
    elements.frameCount.textContent = "0 frames";
    if (elements.clearAllBtn) {
      elements.clearAllBtn.style.display = "none";
    }
    return;
  }

  const sorted = [...state.frames].sort((a, b) => a.order - b.order);
  
  if (elements.clearAllBtn) {
    elements.clearAllBtn.style.display = "block";
  }

  sorted.forEach((frame, index) => {
    const card = document.createElement("div");
    card.className = "frame-item";
    card.dataset.frameId = frame.id;
    card.draggable = true;

    // Frame preview
    const preview = document.createElement("div");
    preview.className = "frame-preview";
    
    const asciiLabel = document.createElement("div");
    asciiLabel.className = "ascii-label";
    asciiLabel.textContent = "ASCII";
    preview.appendChild(asciiLabel);
    
    const pre = document.createElement("pre");
    pre.textContent = (frame.ascii_preview || []).join("\n") || "[preview unavailable]";
    preview.appendChild(pre);
    
    const frameNumber = document.createElement("div");
    frameNumber.className = "frame-number";
    frameNumber.textContent = `#${index + 1}`;
    preview.appendChild(frameNumber);
    
    card.appendChild(preview);

    // Frame name
    const name = document.createElement("div");
    name.className = "frame-name";
    name.textContent = frame.name;
    card.appendChild(name);

    // Delay input
    const delayWrapper = document.createElement("div");
    delayWrapper.style.display = "flex";
    delayWrapper.style.gap = "0.5rem";
    delayWrapper.style.alignItems = "center";
    delayWrapper.style.marginTop = "0.5rem";
    
    const delayLabel = document.createElement("label");
    delayLabel.style.fontSize = "0.75rem";
    delayLabel.style.color = "var(--muted)";
    delayLabel.textContent = "Delay (ms):";
    
    const delayInput = document.createElement("input");
    delayInput.type = "number";
    delayInput.min = "1";
    delayInput.max = "60000";
    delayInput.value = String(frame.delay_ms);
    delayInput.dataset.field = "delay";
    delayInput.dataset.id = frame.id;
    delayInput.style.flex = "1";
    delayInput.style.padding = "0.35rem";
    delayInput.style.background = "#0f172a";
    delayInput.style.border = "1px solid var(--border)";
    delayInput.style.borderRadius = "0.35rem";
    delayInput.style.color = "var(--text)";
    delayInput.draggable = false;
    
    delayWrapper.appendChild(delayLabel);
    delayWrapper.appendChild(delayInput);
    card.appendChild(delayWrapper);

    // Actions
    const actions = document.createElement("div");
    actions.className = "frame-actions";
    actions.appendChild(makeActionButton("↑", "up", frame.id, index === 0));
    actions.appendChild(makeActionButton("↓", "down", frame.id, index === sorted.length - 1));
    actions.appendChild(makeActionButton("Delete", "delete", frame.id, false, "danger"));
    card.appendChild(actions);

    grid.appendChild(card);
  });

  elements.frameCount.textContent = `${state.frames.length} frame${state.frames.length === 1 ? "" : "s"}`;
  
  // Setup drag and drop handlers
  setupDragAndDrop();
}

function makeActionButton(label, action, frameId, disabled = false, extraClass = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.dataset.action = action;
  button.dataset.id = frameId;
  button.draggable = false;
  if (extraClass) {
    button.classList.add(extraClass);
  }
  button.disabled = disabled;
  return button;
}

async function fetchFrames(showToast = false) {
  try {
    const frames = await request("/frames");
    state.frames = frames;
    renderFrames();
    if (showToast) {
      showAlert("Frame list refreshed.", "success");
    }
  } catch (error) {
    console.error(error);
    showAlert(`Failed to load frames: ${error.message}`, "error");
  }
}

async function handleUpload(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;

  const formData = new FormData(form);
  const fileInput = form.querySelector('input[name="files"]');
  const files = fileInput.files;
  
  if (!files || files.length === 0) {
    showAlert("Please choose a PNG or ZIP file to upload.", "error");
    submitButton.disabled = false;
    return;
  }

  // Remove the file input from FormData and add all files with the correct field name
  formData.delete("files");
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  try {
    await request("/upload", {
      method: "POST",
      body: formData,
    });
    showAlert("Upload complete.", "success");
    form.reset();
    form.querySelector('input[name="delay_ms"]').value = DEFAULT_DELAY;
    await fetchFrames();
  } catch (error) {
    console.error(error);
    showAlert(`Upload failed: ${error.message}`, "error");
  } finally {
    submitButton.disabled = false;
  }
}

async function updateDelay(frameId, delayValue) {
  try {
    const updated = await request(`/frames/${frameId}`, {
      method: "PATCH",
      body: JSON.stringify({ delay_ms: delayValue }),
    });
    state.frames = state.frames.map((frame) => (frame.id === frameId ? updated : frame));
    renderFrames();
    showAlert("Delay updated.", "success", 2500);
  } catch (error) {
    console.error(error);
    showAlert(`Failed to update delay: ${error.message}`, "error");
  }
}

async function reorderFrame(frameId, direction) {
  const sorted = [...state.frames].sort((a, b) => a.order - b.order);
  const index = sorted.findIndex((frame) => frame.id === frameId);
  const targetIndex = direction === "up" ? index - 1 : index + 1;
  if (targetIndex < 0 || targetIndex >= sorted.length) {
    return;
  }
  const [moved] = sorted.splice(index, 1);
  sorted.splice(targetIndex, 0, moved);
  const newOrder = sorted.map((frame) => frame.id);

  try {
    const frames = await request("/frames/reorder", {
      method: "POST",
      body: JSON.stringify({ order: newOrder }),
    });
    state.frames = frames;
    renderFrames();
    showAlert("Frame order updated.", "success", 2500);
  } catch (error) {
    console.error(error);
    showAlert(`Failed to reorder frames: ${error.message}`, "error");
  }
}

async function deleteFrame(frameId) {
  if (!window.confirm("Delete this frame?")) {
    return;
  }
  try {
    await request(`/frames/${frameId}`, { method: "DELETE" });
    state.frames = state.frames.filter((frame) => frame.id !== frameId);
    renderFrames();
    showAlert("Frame deleted.", "success", 2500);
  } catch (error) {
    console.error(error);
    showAlert(`Failed to delete frame: ${error.message}`, "error");
  }
}

function setBuilding(isBuilding) {
  state.isBuilding = isBuilding;
  elements.buildBtn.disabled = isBuilding;
  elements.buildBtn.textContent = isBuilding ? "Building..." : "Build & Upload via PlatformIO";
}

function formatLog(result) {
  const lines = [];
  if (result.header) {
    lines.push(`Generated header: ${result.header}`);
  }
  lines.push("=== STDOUT ===");
  lines.push(result.stdout?.trim() || "<empty>");
  lines.push("\n=== STDERR ===");
  lines.push(result.stderr?.trim() || "<empty>");
  lines.push(`\nExit code: ${result.returncode}`);
  return lines.join("\n");
}

async function triggerBuild() {
  if (!state.frames.length) {
    showAlert("Add at least one frame before building.", "error");
    return;
  }
  setBuilding(true);
  elements.buildLog.value = "Running PlatformIO build...";
  try {
    const result = await request("/build", { method: "POST" });
    elements.buildLog.value = formatLog(result);
    const type = result.returncode === 0 ? "success" : "error";
    showAlert(
      result.returncode === 0 ? "Build and upload finished successfully." : "Build completed with errors.",
      type,
      6000,
    );
  } catch (error) {
    elements.buildLog.value = `Build failed: ${error.message}`;
    showAlert(`Build failed: ${error.message}`, "error", 6000);
  } finally {
    setBuilding(false);
  }
}

let draggedElement = null;
let draggedOverElement = null;

function setupDragAndDrop() {
  const grid = elements.framesGrid;
  if (!grid) return;

  const frameItems = grid.querySelectorAll(".frame-item");
  
  frameItems.forEach((item) => {
    // Prevent dragging on buttons and inputs
    item.addEventListener("dragstart", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") {
        e.preventDefault();
        return;
      }
      draggedElement = item;
      item.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/html", item.innerHTML);
    });

    item.addEventListener("dragend", (e) => {
      item.classList.remove("dragging");
      if (draggedOverElement) {
        draggedOverElement.classList.remove("drag-over");
        draggedOverElement = null;
      }
      draggedElement = null;
    });

    item.addEventListener("dragover", (e) => {
      if (draggedElement === item) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      
      if (draggedOverElement && draggedOverElement !== item) {
        draggedOverElement.classList.remove("drag-over");
      }
      item.classList.add("drag-over");
      draggedOverElement = item;
    });

    item.addEventListener("dragleave", (e) => {
      // Only remove drag-over if we're actually leaving the item
      if (!item.contains(e.relatedTarget)) {
        item.classList.remove("drag-over");
        if (draggedOverElement === item) {
          draggedOverElement = null;
        }
      }
    });

    item.addEventListener("drop", async (e) => {
      e.preventDefault();
      item.classList.remove("drag-over");
      
      if (!draggedElement || draggedElement === item) {
        return;
      }

      const sorted = [...state.frames].sort((a, b) => a.order - b.order);
      const draggedId = draggedElement.dataset.frameId;
      const targetId = item.dataset.frameId;
      
      const draggedIndex = sorted.findIndex((f) => f.id === draggedId);
      const targetIndex = sorted.findIndex((f) => f.id === targetId);
      
      if (draggedIndex === -1 || targetIndex === -1) return;
      
      // Reorder
      const [moved] = sorted.splice(draggedIndex, 1);
      sorted.splice(targetIndex, 0, moved);
      const newOrder = sorted.map((frame) => frame.id);

      try {
        const frames = await request("/frames/reorder", {
          method: "POST",
          body: JSON.stringify({ order: newOrder }),
        });
        state.frames = frames;
        renderFrames();
        showAlert("Frame order updated.", "success", 2500);
      } catch (error) {
        console.error(error);
        showAlert(`Failed to reorder frames: ${error.message}`, "error");
      }
    });
  });
}

function handleGridClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const { action, id } = button.dataset;
  if (action === "delete") {
    deleteFrame(id);
  } else if (action === "up" || action === "down") {
    reorderFrame(id, action);
  }
}

function handleDelayChange(event) {
  if (event.target.dataset.field !== "delay") return;
  const value = Number.parseInt(event.target.value, 10);
  if (!Number.isFinite(value) || value <= 0) {
    showAlert("Delay must be a positive number.", "error");
    return;
  }
  updateDelay(event.target.dataset.id, value);
}

async function applyUnifiedDelay() {
  const delayValue = Number.parseInt(elements.unifiedDelay?.value || "0", 10);
  if (!Number.isFinite(delayValue) || delayValue <= 0) {
    showAlert("Delay must be a positive number.", "error");
    return;
  }

  try {
    const updates = state.frames.map((frame) =>
      request(`/frames/${frame.id}`, {
        method: "PATCH",
        body: JSON.stringify({ delay_ms: delayValue }),
      })
    );
    await Promise.all(updates);
    await fetchFrames();
    showAlert(`All frames updated to ${delayValue}ms delay.`, "success");
  } catch (error) {
    console.error(error);
    showAlert(`Failed to update delays: ${error.message}`, "error");
  }
}

async function clearAllFrames() {
  if (!window.confirm("Delete all frames? This cannot be undone.")) {
    return;
  }
  
  try {
    const deletePromises = state.frames.map((frame) =>
      request(`/frames/${frame.id}`, { method: "DELETE" })
    );
    await Promise.all(deletePromises);
    state.frames = [];
    renderFrames();
    showAlert("All frames deleted.", "success");
  } catch (error) {
    console.error(error);
    showAlert(`Failed to delete frames: ${error.message}`, "error");
  }
}

function init() {
  if (!elements.uploadForm || !elements.framesGrid || !elements.buildBtn) {
    console.error("Required elements not found");
    return;
  }

  elements.uploadForm.addEventListener("submit", handleUpload);
  elements.framesGrid.addEventListener("click", handleGridClick);
  elements.framesGrid.addEventListener("change", handleDelayChange);
  elements.buildBtn.addEventListener("click", triggerBuild);
  
  if (elements.refreshBtn) {
    elements.refreshBtn.addEventListener("click", (event) => {
      event.preventDefault();
      fetchFrames(true);
    });
  }
  
  if (elements.applyUnifiedDelayBtn) {
    elements.applyUnifiedDelayBtn.addEventListener("click", applyUnifiedDelay);
  }
  
  if (elements.clearAllBtn) {
    elements.clearAllBtn.addEventListener("click", clearAllFrames);
  }
  
  fetchFrames();
}

document.addEventListener("DOMContentLoaded", init);
