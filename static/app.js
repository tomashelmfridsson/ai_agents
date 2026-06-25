const form = document.getElementById("qa-form");
const statusNode = document.getElementById("status");
const resultNode = document.getElementById("result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  statusNode.textContent = "Kör orkestrator och specialiserade agenter...";
  resultNode.textContent = "Bearbetar...";

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
      throw new Error(data.error || "Okänt fel");
    }

    statusNode.textContent = `Klar. Iterationer: ${data.iterations}. Coverage: ${data.review.coverage_ratio}`;
    resultNode.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    statusNode.textContent = "Fel vid körning";
    resultNode.textContent = error.message;
  }
});
