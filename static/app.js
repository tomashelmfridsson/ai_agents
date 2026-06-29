const form = document.getElementById("qa-form");
const statusNode = document.getElementById("status");
const resultNode = document.getElementById("result");
const scenarioPresetNode = document.getElementById("scenario-preset");
const titleNode = document.getElementById("title");
const requirementsNode = document.getElementById("requirements");

const SAMPLE_SCENARIOS = {
  "Scenario 1": {
    title: "Demo: web application for login and registration",
    requirements: `The user must be able to sign in with email and password.
The system shall display a clear error message when credentials are invalid.
An administrator shall be able to view an overview of registered users.
The user shall be able to register a new account through a form.`,
  },
  "Scenario 2": {
    title: "E-commerce checkout and order confirmation",
    requirements: `The customer must be able to add a product to the shopping cart.
The system shall calculate the total price including tax before checkout.
The customer must be able to complete payment with a valid card.
The system shall display an order confirmation after a successful purchase.`,
  },
  "Scenario 3": {
    title: "Password reset and account recovery",
    requirements: `The user shall be able to request a password reset using an email address.
The system must send a reset link only to registered email addresses.
The user must be able to set a new password through the reset form.
The system shall show a clear error message when the reset token is invalid or expired.`,
  },
  "Scenario 4": {
    title: "Support ticket creation and status tracking",
    requirements: `The customer shall be able to create a support ticket from a form.
The system shall validate that subject and description are provided before submission.
The support agent must be able to update the ticket status.
The customer shall be able to view the current ticket status in the portal.`,
  },
  "Scenario 5": {
    title: "Inventory management for warehouse staff",
    requirements: `A warehouse operator must be able to register incoming stock.
The system shall prevent negative inventory values.
A manager shall be able to view a list of products below the reorder threshold.
The system shall log every stock adjustment with timestamp and user identity.`,
  },
  "Scenario 6": {
    title: "Course enrollment in a student portal",
    requirements: `A student must be able to browse available courses for the current term.
The student shall be able to enroll in a course with available seats.
The system must block enrollment when prerequisites are not fulfilled.
The system shall display a confirmation when enrollment succeeds.`,
  },
};

scenarioPresetNode?.addEventListener("change", () => {
  const scenario = SAMPLE_SCENARIOS[scenarioPresetNode.value];
  if (!scenario) {
    return;
  }
  titleNode.value = scenario.title;
  requirementsNode.value = scenario.requirements;
});

titleNode?.addEventListener("input", () => {
  if (scenarioPresetNode) {
    scenarioPresetNode.value = "custom";
  }
});

requirementsNode?.addEventListener("input", () => {
  if (scenarioPresetNode) {
    scenarioPresetNode.value = "custom";
  }
});

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
          <div class="diagram-node"><strong>Orchestrator Agent</strong><span>Controls routing, collects results, and decides whether another pass is needed.</span></div>
          <div class="diagram-node"><strong>Requirements Analyst Agent</strong><span>Requirement IDs, priority tags, assumptions, acceptance criteria.</span></div>
          <div class="diagram-node"><strong>Test Design Agent</strong><span>Test type selection, steps, oracle, expected results.</span></div>
          <div class="diagram-node"><strong>Review Agent</strong><span>Coverage ratio, findings, improvement actions, approval signal.</span></div>
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
      <details class="stage-toggle">
        <summary>
          <div class="stage-head">
            <div>
              <div class="stage-index">Stage ${index}</div>
              <div class="stage-role">${escapeHtml(role)}</div>
            </div>
            <div class="stage-meta"><strong>Status:</strong> ${escapeHtml(status)}</div>
            <div class="stage-meta"><strong>Trace source:</strong> ${escapeHtml(reasoningSource)}</div>
            <div class="stage-chevron"></div>
          </div>
        </summary>
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
      </details>
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
