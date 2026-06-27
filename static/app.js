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

  const stages = [
    buildStageCard(
      1,
      "Requirements analysis",
      `${payload.requirements.length} requirement item(s) extracted`,
      "Structured requirements",
      payload.requirements.map(
        (item) =>
          `${item.requirement_id}: priority ${item.priority}, ${item.acceptance_criteria.length} acceptance criteria, ${item.assumptions.length} assumption(s).`,
      ),
    ),
    buildStageCard(
      2,
      "Test design",
      `${payload.test_designs.length} design(s) created`,
      "Traceable test cases",
      payload.test_designs.map(
        (item) =>
          `${item.test_case_id}: ${item.test_type} with ${item.steps.length} step(s) and ${item.expected_results.length} expected result(s).`,
      ),
    ),
    buildStageCard(
      3,
      "Artifact generation",
      `${payload.generated_artifacts.length} artifact(s) generated`,
      "Selectors, test data, pseudocode",
      payload.generated_artifacts.map(
        (item) =>
          `${item.artifact_id}: target ${item.target}, test name ${item.test_name}, ${item.selectors.length} selector suggestion(s).`,
      ),
    ),
    buildStageCard(
      4,
      "Review",
      "Coverage and assumptions reviewed",
      "Review findings",
      payload.review.findings.length ? payload.review.findings : ["No critical issues were identified."],
    ),
    buildStageCard(
      5,
      "Orchestration summary",
      "Workflow pass completed",
      "Iteration outcome",
      [
        `The workflow ended after ${payload.iterations} iteration(s).`,
        `Coverage ratio: ${payload.review.coverage_ratio}.`,
        `Approved: ${payload.review.approved ? "yes" : "no"}.`,
        ...payload.review.improvement_actions,
      ],
    ),
  ].join("");

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

function buildStageCard(index, role, status, outputType, logs) {
  const items = (logs.length ? logs : ["No output produced."])
    .map((log) => `<li>${escapeHtml(log)}</li>`)
    .join("");

  return `
    <section class="stage-card">
      <div class="stage-head">
        <div>
          <div class="stage-index">Stage ${index}</div>
          <div class="stage-role">${escapeHtml(role)}</div>
        </div>
        <div class="stage-meta"><strong>Status:</strong> ${escapeHtml(status)}</div>
        <div class="stage-meta"><strong>Output:</strong> ${escapeHtml(outputType)}</div>
      </div>
      <div class="stage-body">
        <div class="log-title">Execution log</div>
        <ul class="log-list">${items}</ul>
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
