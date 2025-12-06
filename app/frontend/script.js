// app/frontend/script.js

const form = document.getElementById("musicForm");
const resultCard = document.getElementById("result");
const userIdInput = document.getElementById("user_id");
const loadingBar = document.getElementById("loading-bar");
const submitBtn = document.querySelector(".primary-btn");

const genresSelect = document.getElementById("genres");
const moodSelect = document.getElementById("mood");
const historyBanner = document.getElementById("history-banner");
const useHistoryBtn = document.getElementById("use-history-btn");

// --- Simple login-style behavior & past-preferences prompt ---
document.addEventListener("DOMContentLoaded", () => {
  const savedId = localStorage.getItem("neonvinyl_user_id");
  if (savedId && !userIdInput.value) {
    userIdInput.value = savedId;
  }

  const lastPrefsRaw = localStorage.getItem("neonvinyl_last_prefs");
  if (lastPrefsRaw) {
    historyBanner.classList.remove("hidden");

    useHistoryBtn.addEventListener("click", () => {
      try {
        const prefs = JSON.parse(lastPrefsRaw);
        applyPreferencesToForm(prefs);
        historyBanner.classList.add("hidden");
        // auto-run playlist for that profile
        form.requestSubmit();
      } catch (e) {
        console.error("Failed to parse saved preferences", e);
      }
    });
  }
});

function showLoading() {
  if (loadingBar) loadingBar.classList.remove("hidden");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Curating…";
  }
}

function hideLoading() {
  if (loadingBar) loadingBar.classList.add("hidden");
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.textContent = "Build / Update Playlist";
  }
}

// Collect current form preferences into a structured object
function getCurrentPreferences() {
  const artistsRaw = document.getElementById("artists").value;
  const genres = Array.from(genresSelect.selectedOptions).map(
    (opt) => opt.value
  );
  const mood = moodSelect.value || null;

  return {
    artists: artistsRaw.split(",").map((a) => a.trim()).filter(Boolean),
    genres,
    mood,
  };
}

// Apply a saved preferences object back into the form
function applyPreferencesToForm(prefs) {
  const artistsInput = document.getElementById("artists");

  if (Array.isArray(prefs.artists)) {
    artistsInput.value = prefs.artists.join(", ");
  }

  // genres: clear all, then re-select
  Array.from(genresSelect.options).forEach((opt) => {
    opt.selected = false;
  });
  if (Array.isArray(prefs.genres)) {
    const lower = prefs.genres.map((g) => g.toLowerCase());
    Array.from(genresSelect.options).forEach((opt) => {
      if (lower.includes(opt.value.toLowerCase())) {
        opt.selected = true;
      }
    });
  }

  // mood
  moodSelect.value = prefs.mood || "";
}

// Persist preferences in browser for future sessions
function saveLastPreferences(prefs) {
  try {
    localStorage.setItem("neonvinyl_last_prefs", JSON.stringify(prefs));
  } catch (e) {
    console.warn("Could not store preferences", e);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const userId = userIdInput.value.trim();
  if (userId) {
    localStorage.setItem("neonvinyl_user_id", userId);
  }

  const preferences = getCurrentPreferences();
  const payload = { user_id: userId, preferences };

  showLoading();

  try {
    const resp = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      alert("Backend error. Check server logs.");
      return;
    }

    const data = await resp.json();
    renderResult(data);
    saveLastPreferences(preferences);
  } catch (err) {
    console.error(err);
    alert("Network error. Is the backend running?");
  } finally {
    hideLoading();
  }
});

function renderResult(data) {
  // Playlist meta
  document.getElementById("version").textContent = data.playlist_version;
  document.getElementById("sessions").textContent = data.sessions_count;
  document.getElementById("explanation").textContent = data.explanation;

  // Now playing = first track in playlist, if any
  const first = data.playlist[0];
  const npTitle = document.getElementById("np-title");
  const npArtist = document.getElementById("np-artist");

  if (first) {
    npTitle.textContent = first.title || "Unknown track";
    npArtist.textContent = first.artist || "Unknown artist";
  } else {
    npTitle.textContent = "No tracks generated";
    npArtist.textContent = "Try adding some favorite artists or genres.";
  }

  // Render lists
  renderTrackList("all-tracks", data.playlist);
  renderTrackList("new-tracks", data.new_tracks);
  renderTrackList("kept-tracks", data.kept_tracks);
  renderTrackList("removed-tracks", data.removed_tracks);

  resultCard.classList.remove("hidden");
}

function renderTrackList(elementId, tracks) {
  const ul = document.getElementById(elementId);
  ul.innerHTML = "";

  if (!tracks || tracks.length === 0) {
    const li = document.createElement("li");
    li.textContent = "None";
    ul.appendChild(li);
    return;
  }

  tracks.forEach((t) => {
    const li = document.createElement("li");

    const left = document.createElement("div");
    left.className = "track-main";

    const title = document.createElement("span");
    title.className = "track-title";
    title.textContent = t.title || "Unknown title";

    const artist = document.createElement("span");
    artist.className = "track-artist";
    artist.textContent = t.artist || "Unknown artist";

    left.appendChild(title);
    left.appendChild(artist);

    const right = document.createElement("div");
    right.className = "track-meta";
    const parts = [];
    if (t.release_date) parts.push(t.release_date);
    if (t.source) parts.push(t.source.replace("musicbrainz_", "MB "));
    right.textContent = parts.join(" • ");

    li.appendChild(left);
    li.appendChild(right);
    ul.appendChild(li);
  });
}
