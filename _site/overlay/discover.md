---
description: Search 3rdBrain by task, category, capability, access and platform — with visible match explanations
search:
  exclude: true
---

# Discover <span id="po-project-name">your knowledge base</span> { .po-discovery-title }

Find material the way you remember it: describe the job, then narrow by capability,
category, access or platform. Exact names and natural-language meaning are ranked together
inside your browser, with zero LLM calls.
{ .po-discovery-intro }

<div id="3rdbrain-discovery" class="po-discovery" aria-busy="true">
  <div class="po-discovery__search-shell">
    <label class="po-discovery__label" for="po-discovery-query">What are you trying to do?</label>
    <div class="po-discovery__input-wrap">
      <input
        id="po-discovery-query"
        class="po-discovery__input"
        type="search"
        role="searchbox"
        aria-label="Search this knowledge base"
        aria-autocomplete="list"
        aria-controls="po-discovery-suggestions"
        autocomplete="off"
        placeholder="e.g. prepare email replies without auto-sending"
      >
      <kbd>/</kbd>
    </div>
    <ul id="po-discovery-suggestions" class="po-discovery__suggestions" role="listbox" hidden></ul>
    <div class="po-discovery__examples" aria-label="Example searches">
      <button type="button" data-query="turn incoming email into tasks">Email → tasks</button>
      <button type="button" data-query="cheap local worker under a hosted agent">Local AI worker</button>
      <button type="button" data-query="make a video ad for a local business">Video ads</button>
    </div>
  </div>

  <div class="po-discovery__toolbar">
    <p id="po-discovery-status" class="po-discovery__status" role="status" aria-live="polite">Loading the catalog…</p>
    <div class="po-discovery__actions">
      <button id="po-discovery-clear" type="button">Clear all filters</button>
      <button id="po-discovery-export" type="button">Export search gaps</button>
    </div>
  </div>

  <div class="po-discovery__layout">
    <aside id="po-discovery-filters" class="po-discovery__filters" aria-label="Refine results"></aside>
    <section aria-label="Search results">
      <div id="po-discovery-active" class="po-discovery__active" role="group" aria-label="Active filters"></div>
      <div id="po-discovery-results" class="po-discovery__results"></div>
    </section>
  </div>
</div>

<noscript>This discovery page needs JavaScript. The normal sidebar and built-in search remain available.</noscript>
