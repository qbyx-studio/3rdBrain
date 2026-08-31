import { create, insertMultiple, search } from "@orama/orama";

const MODEL = "Xenova/all-MiniLM-L6-v2";
const TRANSFORMERS_MODULE = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.2.0/dist/transformers.min.js";
const RECALL_FILLERS = new Set([
  "a", "about", "an", "could", "find", "for", "from", "i", "in", "it", "like",
  "loads", "looking", "my", "of", "on", "remember", "remembered", "something",
  "stuff", "that", "the", "thing", "this", "to", "tool", "want", "was", "what",
  "where", "with",
]);

let records = [];
let enginePromise;

function recallQuery(query) {
  const meaningful = (String(query).toLowerCase().match(/[a-z0-9]+/g) || [])
    .filter((token) => !RECALL_FILLERS.has(token))
    .map((token) => token.length > 4 && token.endsWith("s") && !/(ss|us|is)$/.test(token)
      ? token.slice(0, -1) : token);
  return meaningful.join(" ") || query;
}

function retrievalText(record) {
  return [
    record.title,
    record.description,
    ...(record.jobs || []),
    ...(record.aliases || []),
    ...(record.facets || []),
    ...(record.taxonomy_path || []),
  ].filter(Boolean).join(". ");
}

async function embed(extractor, text) {
  const output = await extractor(text, { pooling: "mean", normalize: true });
  return Array.from(output.data);
}

async function buildEngine() {
  self.postMessage({ type: "status", status: "loading-model" });
  const { env, pipeline } = await import(TRANSFORMERS_MODULE);
  env.allowLocalModels = false;
  env.useBrowserCache = true;
  const extractor = await pipeline("feature-extraction", MODEL, { dtype: "q8" });
  const database = create({
    schema: {
      id: "string",
      title: "string",
      description: "string",
      jobs: "string",
      aliases: "string",
      taxonomy: "string",
      body: "string",
      embedding: "vector[384]",
    },
  });
  const documents = [];
  self.postMessage({ type: "status", status: "indexing", total: records.length });
  for (let index = 0; index < records.length; index += 1) {
    const record = records[index];
    documents.push({
      id: record.id,
      title: record.title || "",
      description: record.description || "",
      jobs: (record.jobs || []).join(" "),
      aliases: (record.aliases || []).join(" "),
      taxonomy: [...(record.taxonomy_path || []), ...(record.facets || [])].join(" "),
      body: record.search_text || "",
      embedding: await embed(extractor, retrievalText(record)),
    });
    if ((index + 1) % 50 === 0) {
      self.postMessage({ type: "status", status: "indexing", completed: index + 1, total: records.length });
    }
  }
  await insertMultiple(database, documents);
  self.postMessage({ type: "status", status: "ready" });
  return { database, extractor };
}

self.addEventListener("message", async (event) => {
  const message = event.data || {};
  if (message.type === "initialize") {
    records = message.records || [];
    return;
  }
  if (message.type !== "search" || !message.query || !records.length) return;
  try {
    enginePromise ||= buildEngine();
    const { database, extractor } = await enginePromise;
    const term = recallQuery(message.query);
    const meaningfulCount = term.split(/\s+/).filter(Boolean).length;
    const result = await search(database, {
      mode: "hybrid",
      term,
      properties: ["title", "description", "jobs", "aliases", "taxonomy", "body"],
      boost: { title: 9, aliases: 7, jobs: 6, description: 5, taxonomy: 3, body: 1 },
      tolerance: 1,
      vector: { value: await embed(extractor, message.query), property: "embedding" },
      similarity: 0.2,
      hybridWeights: meaningfulCount >= 8
        ? { text: 0.36, vector: 0.64 }
        : { text: 0.2, vector: 0.8 },
      limit: 40,
    });
    self.postMessage({
      type: "results",
      requestId: message.requestId,
      query: message.query,
      ids: result.hits.map((hit) => hit.document.id),
    });
  } catch (error) {
    enginePromise = undefined;
    self.postMessage({
      type: "error",
      requestId: message.requestId,
      message: error instanceof Error ? error.message : String(error),
    });
  }
});
