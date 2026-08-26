(() => {
  "use strict";

  const STOP_WORDS = new Set([
    "a", "an", "and", "are", "for", "from", "how", "i", "in", "into", "is",
    "it", "my", "no", "of", "on", "or", "3rdbrain", "such", "that", "the",
    "this", "to", "under", "with", "without", "item"
  ]);
  const state = {
    records: [], taxonomy: {}, suggestions: [], query: "", suggestionIndex: -1,
    visibleLimit: 20, quickIndex: -1,
    filters: { facets: new Set(), categories: new Set(), page_types: new Set() }
  };
  let assetsPromise;

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);

  const tokens = (value) => (String(value).toLowerCase().match(/[a-z0-9]+(?:[.+#][a-z0-9]+)?/g) || [])
    .filter((token) => !STOP_WORDS.has(token));

  function expandedTerms(query) {
    const normalized = query.trim().toLowerCase();
    const queryTokens = new Set(tokens(query));
    const expanded = new Set(queryTokens);
    const concepts = state.taxonomy.concepts || {};
    const matched = new Set();
    Object.entries(concepts).forEach(([id, concept]) => {
      const labels = [concept.pref_label, ...(concept.alt_labels || []), ...(concept.hidden_labels || [])]
        .filter(Boolean).map((label) => String(label).toLowerCase());
      if (labels.some((label) => normalized.includes(label) || tokens(label).every((token) => queryTokens.has(token)))) {
        matched.add(id);
        (concept.related || []).forEach((related) => matched.add(related));
      }
    });
    matched.forEach((id) => {
      const concept = concepts[id] || {};
      [concept.pref_label, ...(concept.alt_labels || []), ...(concept.hidden_labels || [])]
        .filter(Boolean).forEach((label) => {
          expanded.add(String(label).toLowerCase());
          tokens(label).forEach((token) => expanded.add(token));
        });
    });
    return expanded;
  }

  function passesFilters(record) {
    const checks = {
      facets: new Set(record.facets || []),
      categories: new Set(record.taxonomy_path || []),
      page_types: new Set([record.page_type])
    };
    return Object.entries(state.filters).every(([key, selected]) =>
      [...selected].every((value) => checks[key].has(value))
    );
  }

  function rrf(lists, constant = 60) {
    const scores = new Map();
    lists.forEach((list) => list.forEach((id, index) =>
      scores.set(id, (scores.get(id) || 0) + 1 / (constant + index + 1))
    ));
    return [...scores.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }

  function rank(query, applyFilters = true) {
    const pool = state.records.filter((record) => !applyFilters || passesFilters(record));
    const queryTokens = tokens(query);
    if (!queryTokens.length) return pool.map((record) => ({ ...record, matchReason: "Browse all" }));
    const terms = expandedTerms(query);
    const tokenSets = new Map(pool.map((record) => [record.id, new Set(tokens(record.search_text || ""))]));
    const inverseFrequency = new Map(queryTokens.map((token) => {
      const frequency = [...tokenSets.values()].filter((values) => values.has(token)).length;
      return [token, Math.log((pool.length + 1) / (frequency + 1)) + 1];
    }));
    const ngrams = new Set();
    for (let size = 2; size <= Math.min(4, queryTokens.length); size += 1) {
      for (let start = 0; start <= queryTokens.length - size; start += 1) {
        ngrams.add(queryTokens.slice(start, start + size).join(" "));
      }
    }
    const exactTitles = [];
    const lexical = [];
    const intent = [];
    pool.forEach((record) => {
      const title = record.title.toLowerCase();
      const description = (record.description || "").toLowerCase();
      const searchable = (record.search_text || "").toLowerCase();
      const jobs = (record.jobs || []).join(" ").toLowerCase();
      const aliases = (record.aliases || []).join(" ").toLowerCase();
      const structured = [title, description, jobs, aliases].join(" ");
      let lexicalScore = 0;
      queryTokens.forEach((token) => {
        const weight = inverseFrequency.get(token);
        lexicalScore += (title.split(token).length - 1) * 10 * weight;
        lexicalScore += (aliases.split(token).length - 1) * 8 * weight;
        lexicalScore += (jobs.split(token).length - 1) * 6 * weight;
        lexicalScore += (description.split(token).length - 1) * 4 * weight;
        lexicalScore += Math.min(3, searchable.split(token).length - 1) * .5 * weight;
      });
      ngrams.forEach((phrase) => {
        if (structured.includes(phrase)) lexicalScore += phrase.split(" ").length * 5;
      });
      if (title.trim() === query.trim().toLowerCase()) {
        exactTitles.push([record.id, 2]); lexicalScore += 100;
      } else if (title.startsWith(query.trim().toLowerCase())) {
        exactTitles.push([record.id, 1]); lexicalScore += 30;
      }
      if (searchable.includes(query.toLowerCase())) lexicalScore += 20;
      if (lexicalScore > 0) lexical.push([record.id, lexicalScore]);

      const intentText = [
        ...(record.jobs || []), ...(record.aliases || []), ...(record.facets || []),
        ...(record.taxonomy_path || []), record.description || ""
      ].join(" ").toLowerCase();
      let intentScore = 0;
      terms.forEach((term) => {
        if (term.includes(" ") && intentText.includes(term)) intentScore += 6;
        else intentScore += Math.min(3, intentText.split(term).length - 1);
      });
      const querySet = new Set(queryTokens);
      (record.aliases || []).forEach((alias) => {
        const aliasTokens = new Set(tokens(alias));
        if (aliasTokens.size && [...aliasTokens].every((token) => querySet.has(token))) {
          intentScore += 25 + aliasTokens.size * 3;
        }
      });
      (record.jobs || []).forEach((job) => {
        const jobTokens = new Set(tokens(job));
        const overlap = [...jobTokens].filter((token) => querySet.has(token));
        if (overlap.length) intentScore += overlap.length * 4 + overlap.length / jobTokens.size * 12;
      });
      if (intentScore > 0) intent.push([record.id, intentScore]);
    });
    exactTitles.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    lexical.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    intent.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    const lexicalIds = new Set(lexical.map(([id]) => id));
    const intentIds = new Set(intent.map(([id]) => id));
    const byId = new Map(pool.map((record) => [record.id, record]));
    return rrf([exactTitles.map(([id]) => id), lexical.map(([id]) => id), intent.map(([id]) => id)]).map(([id]) => ({
      ...byId.get(id),
      matchReason: lexicalIds.has(id) && intentIds.has(id) ? "Exact wording + related intent"
        : lexicalIds.has(id) ? "Exact wording" : "Related intent"
    }));
  }

  function logSearch(resultCount) {
    if (!state.query.trim()) return;
    const key = "3rdbrain-search-events";
    const events = JSON.parse(localStorage.getItem(key) || "[]");
    events.push({ query: state.query, resultCount, at: new Date().toISOString() });
    localStorage.setItem(key, JSON.stringify(events.slice(-250)));
  }

  const countBy = (records, getter) => records.reduce((counts, record) => {
    getter(record).forEach((value) => counts.set(value, (counts.get(value) || 0) + 1));
    return counts;
  }, new Map());

  function filterButton(kind, value, count) {
    const pressed = state.filters[kind].has(value);
    return `<button type="button" class="po-filter${pressed ? " is-active" : ""}" ` +
      `data-filter-kind="${kind}" data-filter-value="${escapeHtml(value)}" aria-pressed="${pressed}">` +
      `${escapeHtml(value)} <span>(${count})</span></button>`;
  }

  function renderFilters(baseResults) {
    const target = document.getElementById("po-discovery-filters");
    const compact = window.matchMedia("(max-width: 760px)").matches;
    const facetCounts = countBy(baseResults, (record) => record.facets || []);
    const categoryCounts = countBy(baseResults, (record) => (record.taxonomy_path || []).slice(0, 1));
    const typeCounts = countBy(baseResults, (record) => [record.page_type]);
    const groups = state.taxonomy.facet_groups || {};
    const facetGroups = {};
    [...facetCounts.entries()].forEach(([facet, count]) => {
      const group = groups[facet] || "Capability";
      (facetGroups[group] ||= []).push([facet, count]);
    });
    Object.values(facetGroups).forEach((values) => values.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])));

    const section = (title, body, open = false) =>
      `<details class="po-filter-group"${open ? " open" : ""}><summary>${title}</summary><div>${body}</div></details>`;
    let html = section("Categories", [...categoryCounts.entries()].sort((a, b) => b[1] - a[1])
      .map(([value, count]) => filterButton("categories", value, count)).join(""), !compact);
    Object.entries(facetGroups).forEach(([group, values], index) => {
      if (values.length) html += section(group, values.map(([value, count]) => filterButton("facets", value, count)).join(""), !compact && index === 0);
    });
    html += section("Page type", [...typeCounts.entries()].sort((a, b) => b[1] - a[1])
      .map(([value, count]) => filterButton("page_types", value, count)).join(""));
    target.innerHTML = html;
  }

  function renderActiveFilters() {
    const target = document.getElementById("po-discovery-active");
    const active = Object.entries(state.filters).flatMap(([kind, values]) =>
      [...values].map((value) => ({ kind, value }))
    );
    target.innerHTML = active.map(({ kind, value }) =>
      `<button type="button" data-remove-kind="${kind}" data-remove-value="${escapeHtml(value)}">` +
      `${escapeHtml(value)} <span aria-hidden="true">×</span></button>`
    ).join("");
  }

  function resultCard(record) {
    const chips = (record.facets || []).slice(0, 6).map((facet) => `<span>${escapeHtml(facet)}</span>`).join("");
    const job = (record.jobs || [])[0];
    return `<article class="po-result" data-testid="result-card">` +
      `<div class="po-result__meta"><span>${escapeHtml(record.page_type)}</span>` +
      `<span data-testid="match-reason">${escapeHtml(record.matchReason)}</span></div>` +
      `<h2><a href="${escapeHtml(record.location)}" data-result-id="${escapeHtml(record.id)}">${escapeHtml(record.title)}</a></h2>` +
      `<p class="po-result__breadcrumb">${escapeHtml(record.breadcrumb)}</p>` +
      `<p>${escapeHtml(record.description || job || "Open this page for the full breakdown.")}</p>` +
      (job ? `<p class="po-result__job"><strong>Use it when:</strong> ${escapeHtml(job)}</p>` : "") +
      `<div class="po-result__chips">${chips}</div></article>`;
  }

  function discoveryUrl(query) {
    return `/discover/?q=${encodeURIComponent(query.trim()).replace(/%20/g, "+")}`;
  }

  function quickResult(record) {
    const location = record.location.startsWith("../")
      ? `/${record.location.slice(3)}` : record.location;
    return `<li><a class="po-quick-result" data-testid="quick-result" href="${escapeHtml(location)}">` +
      `<strong>${escapeHtml(record.title)}</strong>` +
      `<span>${escapeHtml(record.breadcrumb)} · ${escapeHtml(record.matchReason)}</span></a></li>`;
  }

  function resetGlobalSearch() {
    const input = document.querySelector(".md-search__input");
    const toggle = document.getElementById("__search");
    const panel = document.querySelector(".po-quick-search");
    if (input) {
      input.value = "";
      input.blur();
    }
    if (toggle) toggle.checked = false;
    if (panel) panel.hidden = true;
    state.quickIndex = -1;
  }

  function wireGlobalSearch() {
    const input = document.querySelector(".md-search__input");
    const inner = document.querySelector(".md-search__inner");
    if (!input || !inner || input.dataset.thirdbrainUnified === "true") return;
    input.dataset.thirdbrainUnified = "true";
    document.body.classList.add("po-unified-search");
    const panel = document.createElement("section");
    panel.className = "po-quick-search";
    panel.setAttribute("aria-label", "3rdBrain quick search results");
    panel.hidden = true;
    inner.appendChild(panel);

    const close = () => {
      panel.hidden = true;
      state.quickIndex = -1;
    };
    const renderQuick = () => {
      const query = input.value.trim();
      if (query.length < 2) return close();
      const results = rank(query, false).slice(0, 6);
      panel.innerHTML = `<p class="po-quick-search__meta">${results.length} best matches · same ranking as Discover</p>` +
        `<ol>${results.map(quickResult).join("")}</ol>` +
        `<a class="po-quick-search__all" href="${escapeHtml(discoveryUrl(query))}">View all in Discover</a>`;
      panel.hidden = false;
      state.quickIndex = -1;
    };
    input.addEventListener("input", renderQuick);
    input.addEventListener("focus", renderQuick);
    input.addEventListener("keydown", (event) => {
      const links = [...panel.querySelectorAll(".po-quick-result")];
      if ((event.key === "ArrowDown" || event.key === "ArrowUp") && links.length) {
        event.preventDefault();
        const offset = event.key === "ArrowDown" ? 1 : -1;
        state.quickIndex = (state.quickIndex + offset + links.length) % links.length;
        links.forEach((link, index) => link.classList.toggle("is-active", index === state.quickIndex));
        links[state.quickIndex].focus();
      } else if (event.key === "Enter" && input.value.trim()) {
        event.preventDefault();
        const target = discoveryUrl(input.value);
        resetGlobalSearch();
        window.location.href = target;
      } else if (event.key === "Escape") close();
    });
    panel.addEventListener("click", (event) => {
      if (event.target.closest(".po-quick-result, .po-quick-search__all")) resetGlobalSearch();
    });
    inner.querySelector("form")?.addEventListener("reset", () => setTimeout(close));
  }

  function render() {
    const base = rank(state.query, false);
    const results = rank(state.query, true);
    renderFilters(base.length ? base : state.records);
    renderActiveFilters();
    const target = document.getElementById("po-discovery-results");
    if (!results.length) {
      target.innerHTML = `<div class="po-discovery__empty"><h2>No exact matches yet</h2>` +
        `<p>Try a broader term, remove a filter, or use one of the suggested jobs above.</p></div>`;
    } else {
      const visible = results.slice(0, state.visibleLimit);
      target.innerHTML = visible.map(resultCard).join("") + (results.length > visible.length
        ? `<button class="po-discovery__more" type="button" data-show-more>` +
          `Show ${Math.min(20, results.length - visible.length)} more</button>`
        : "");
    }
    document.getElementById("po-discovery-status").textContent =
      `${results.length} result${results.length === 1 ? "" : "s"}` +
      (results.length > state.visibleLimit ? ` · showing ${state.visibleLimit}` : "");
    logSearch(results.length);
  }

  function renderSuggestions(value) {
    const list = document.getElementById("po-discovery-suggestions");
    const input = document.getElementById("po-discovery-query");
    const needle = value.trim().toLowerCase();
    const matches = needle.length < 2 ? [] : state.suggestions
      .filter((suggestion) => suggestion.toLowerCase().includes(needle)).slice(0, 7);
    state.suggestionIndex = -1;
    list.innerHTML = matches.map((suggestion, index) =>
      `<li id="po-suggestion-${index}" role="option" aria-selected="false" data-suggestion="${escapeHtml(suggestion)}">${escapeHtml(suggestion)}</li>`
    ).join("");
    list.hidden = !matches.length;
    if (!matches.length) input.removeAttribute("aria-activedescendant");
  }

  function acceptSuggestion(value) {
    const input = document.getElementById("po-discovery-query");
    input.value = value;
    state.query = value;
    state.visibleLimit = 20;
    renderSuggestions("");
    render();
  }

  function wireEvents(root) {
    const input = document.getElementById("po-discovery-query");
    input.addEventListener("input", () => {
      state.query = input.value;
      state.visibleLimit = 20;
      renderSuggestions(input.value);
      render();
    });
    input.addEventListener("keydown", (event) => {
      const options = [...document.querySelectorAll("#po-discovery-suggestions [role='option']")];
      if (event.key === "ArrowDown" && options.length) {
        event.preventDefault();
        state.suggestionIndex = (state.suggestionIndex + 1) % options.length;
      } else if (event.key === "ArrowUp" && options.length) {
        event.preventDefault();
        state.suggestionIndex = (state.suggestionIndex - 1 + options.length) % options.length;
      } else if (event.key === "Enter" && state.suggestionIndex >= 0) {
        event.preventDefault();
        acceptSuggestion(options[state.suggestionIndex].dataset.suggestion);
        return;
      } else if (event.key === "Escape") {
        renderSuggestions("");
        return;
      } else return;
      options.forEach((option, index) => option.setAttribute("aria-selected", String(index === state.suggestionIndex)));
      input.setAttribute("aria-activedescendant", options[state.suggestionIndex].id);
    });
    root.addEventListener("click", (event) => {
      const filter = event.target.closest("[data-filter-kind]");
      const remove = event.target.closest("[data-remove-kind]");
      const suggestion = event.target.closest("[data-suggestion]");
      const example = event.target.closest("[data-query]");
      const result = event.target.closest("[data-result-id]");
      const showMore = event.target.closest("[data-show-more]");
      if (showMore) {
        state.visibleLimit += 20;
        render();
      } else if (filter) {
        renderSuggestions("");
        state.visibleLimit = 20;
        const selected = state.filters[filter.dataset.filterKind];
        selected.has(filter.dataset.filterValue) ? selected.delete(filter.dataset.filterValue) : selected.add(filter.dataset.filterValue);
        render();
      } else if (remove) {
        renderSuggestions("");
        state.visibleLimit = 20;
        state.filters[remove.dataset.removeKind].delete(remove.dataset.removeValue);
        render();
      } else if (suggestion) acceptSuggestion(suggestion.dataset.suggestion);
      else if (example) acceptSuggestion(example.dataset.query);
      else if (result) {
        const events = JSON.parse(localStorage.getItem("3rdbrain-search-clicks") || "[]");
        events.push({ query: state.query, result: result.dataset.resultId, at: new Date().toISOString() });
        localStorage.setItem("3rdbrain-search-clicks", JSON.stringify(events.slice(-250)));
      }
    });
    document.getElementById("po-discovery-clear").addEventListener("click", () => {
      renderSuggestions("");
      state.visibleLimit = 20;
      Object.values(state.filters).forEach((set) => set.clear());
      render();
    });
    document.getElementById("po-discovery-export").addEventListener("click", () => {
      const data = localStorage.getItem("3rdbrain-search-events") || "[]";
      const link = Object.assign(document.createElement("a"), {
        href: URL.createObjectURL(new Blob([data], { type: "application/json" })),
        download: "3rdbrain-search-gaps.json"
      });
      link.click();
      URL.revokeObjectURL(link.href);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "/" && !/input|textarea/i.test(document.activeElement.tagName)) {
        event.preventDefault(); input.focus();
      }
    });
  }

  function loadAssets() {
    if (!assetsPromise) {
      assetsPromise = Promise.all([
        fetch("/assets/discovery/records.json").then((response) => response.json()),
        fetch("/assets/discovery/taxonomy.json").then((response) => response.json()),
        fetch("/assets/discovery/suggestions.json").then((response) => response.json())
      ]).then(([records, taxonomy, suggestions]) => {
        state.records = records;
        state.taxonomy = taxonomy;
        state.suggestions = suggestions;
        const name = taxonomy.project?.name;
        const heading = document.getElementById("po-project-name");
        if (name && heading) heading.textContent = name;
      });
    }
    return assetsPromise;
  }

  async function initialize() {
    const root = document.getElementById("3rdbrain-discovery");
    const progress = document.querySelector(".md-progress[role='progressbar']");
    if (progress && !progress.getAttribute("aria-label")) {
      progress.setAttribute("aria-label", "Page loading progress");
    }
    try {
      await loadAssets();
      wireGlobalSearch();
      // Material swaps article content without reloading the header. Clear any
      // query and quick-results panel left behind by the previous page.
      resetGlobalSearch();
      if (!root || root.dataset.ready === "true") return;
      root.dataset.ready = "true";
      const initialQuery = new URLSearchParams(window.location.search).get("q") || "";
      state.query = initialQuery;
      document.getElementById("po-discovery-query").value = initialQuery;
      root.setAttribute("aria-busy", "false");
      wireEvents(root);
      render();
    } catch (error) {
      if (root) {
        root.setAttribute("aria-busy", "false");
        document.getElementById("po-discovery-status").textContent = "The local search catalog could not be loaded.";
      }
      console.error(error);
    }
  }

  if (window.document$?.subscribe) window.document$.subscribe(initialize);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
})();
