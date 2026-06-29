const form = document.getElementById("qa-form");
const statusNode = document.getElementById("status");
const resultNode = document.getElementById("result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  statusNode.textContent = "Running the deterministic workflow...";
  resultNode.className = "empty-state";
  resultNode.textContent = "Processing...";

  const formData = new FormData(form);
  const payload = {
    title: formData.get("title"),
    requirements: formData.get("requirements"),
  };

  try {
    const response = await fetch("/api/process", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Unknown error");
    }

    statusNode.textContent = `Completed after ${data.iterations} iteration(s). Coverage ratio: ${data.review.coverage_ratio}.`;
    resultNode.className = "";
    resultNode.innerHTML = buildWorkflowReport(data);
  } catch (error) {
    statusNode.textContent = "Run failed";
    resultNode.className = "empty-state";
    resultNode.textContent = error.message;
  }
});

function buildWorkflowReport(payload) {
  const summary = [
    ["Scenario", payload.title],
    ["Iterations", String(payload.iterations)],
    ["Requirements", String(payload.requirements.length)],
    ["Designs", String(payload.test_designs.length)],
    ["Artifacts", String(payload.generated_artifacts.length)],
    ["Coverage", String(payload.review.coverage_ratio)],
  ];

  const summaryHtml = summary
    .map(
      ([label, value]) => `
        <div class="metric-card">
          <div class="metric-label">${escapeHtml(label)}</div>
          <div class="metric-value">${escapeHtml(value)}</div>
        </div>
      `,
    )
    .join("");

  const stages = (payload.stage_traces || [])
    .map((trace, index) =>
      buildStageCard(
        index + 1,
        trace.agent_name,
        trace.status,
        trace.input_summary || [],
        trace.reasoning_trace || [],
        trace.output_summary || [],
        trace.reasoning_source || "structured_trace",
      ),
    )
    .join("");

  return `
    <div class="report-shell">
      <div class="summary-grid">${summaryHtml}</div>
      <section class="diagram-card">
        <h3>Pipeline visualization</h3>
        <div class="diagram-flow">
          <div class="diagram-node"><strong>Input</strong><span>Scenario title and raw requirement statements.</span></div>
          <div class="diagram-node"><strong>Requirements analyst</strong><span>Requirement IDs, priority tags, assumptions, acceptance criteria.</span></div>
          <div class="diagram-node"><strong>Test designer</strong><span>Test type selection, steps, oracle, expected results.</span></div>
          <div class="diagram-node"><strong>Artifact generator</strong><span>Selectors, test data, pseudocode, target mapping.</span></div>
          <div class="diagram-node"><strong>Reviewer</strong><span>Coverage ratio, findings, improvement actions, approval signal.</span></div>
        </div>
      </section>
      <div class="stage-grid">${stages}</div>
    </div>
  `;
}

function buildStageCard(index, role, status, inputSummary, reasoningTrace, outputSummary, reasoningSource) {
  const inputLead = inputSummary[0] || "No input recorded.";
  const inputItems = inputSummary.slice(1).map((log) => `<li>${escapeHtml(log)}</li>`).join("");
  const reasoningLead = reasoningTrace[0] || "No reasoning trace recorded.";
  const reasoningItems = reasoningTrace.slice(1).map((log) => `<li>${escapeHtml(log)}</li>`).join("");
  const outputLead = outputSummary[0] || "No output recorded.";
  const outputItems = outputSummary.slice(1).map((log) => `<li>${escapeHtml(log)}</li>`).join("");

  return `
    <section class="stage-card">
      <div class="stage-head">
        <div>
          <div class="stage-index">Stage ${index}</div>
          <div class="stage-role">${escapeHtml(role)}</div>
        </div>
        <div class="stage-meta"><strong>Status:</strong> ${escapeHtml(status)}</div>
        <div class="stage-meta"><strong>Trace source:</strong> ${escapeHtml(reasoningSource)}</div>
      </div>
      <div class="stage-body">
        <div class="log-title">Input</div>
        <p class="io-summary">${escapeHtml(inputLead)}</p>
        ${inputItems ? `<ul class="log-list">${inputItems}</ul>` : ""}
        <div class="log-title">Reasoning trace</div>
        <p class="io-summary">${escapeHtml(reasoningLead)}</p>
        ${reasoningItems ? `<ul class="log-list">${reasoningItems}</ul>` : ""}
        <div class="log-title">Output</div>
        <p class="io-summary">${escapeHtml(outputLead)}</p>
        ${outputItems ? `<ul class="log-list">${outputItems}</ul>` : ""}
      </div>
    </section>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
