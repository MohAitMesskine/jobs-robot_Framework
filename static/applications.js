const workspace = document.querySelector("#applications-workspace");
const applicationsList = document.querySelector("#application-list");
const applicationsCount = document.querySelector("#applications-count");
const refreshButton = document.querySelector("#refresh-applications");
const logoutButton = document.querySelector("#logout-button");
const isStaff = workspace.dataset.isStaff === "true";

function createApplicationCard(application) {
  const card = document.createElement("article");
  card.className = "application-card";

  const heading = document.createElement("div");
  heading.className = "application-card-heading";
  const jobTitle = document.createElement("h2");
  jobTitle.textContent = application.job_title;
  const applicationId = document.createElement("span");
  applicationId.className = "application-id";
  applicationId.textContent = `Candidature #${application.id}`;
  heading.append(jobTitle, applicationId);
  card.append(heading);

  if (isStaff) {
    const candidate = document.createElement("p");
    candidate.className = "application-candidate";
    candidate.textContent = `${application.name} · ${application.email}`;
    card.append(candidate);
  }

  const message = document.createElement("p");
  message.className = "application-message";
  message.textContent = application.message;
  card.append(message);
  return card;
}

async function loadApplications() {
  applicationsCount.textContent = "Chargement des candidatures…";
  applicationsList.replaceChildren();

  try {
    const response = await fetch(workspace.dataset.applicationsEndpoint);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Impossible de charger les candidatures.");
    }

    applicationsCount.textContent =
      `${data.applications.length} candidature${data.applications.length === 1 ? "" : "s"}`;
    if (data.applications.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = isStaff
        ? "Aucune candidature reçue pour le moment."
        : "Vous n’avez pas encore envoyé de candidature.";
      applicationsList.append(empty);
      return;
    }

    data.applications.forEach((application) => {
      applicationsList.append(createApplicationCard(application));
    });
  } catch (error) {
    applicationsCount.textContent = error.message;
  }
}

refreshButton.addEventListener("click", loadApplications);
logoutButton.addEventListener("click", async () => {
  logoutButton.disabled = true;
  try {
    const response = await fetch("/api/auth/logout", { method: "POST" });
    if (!response.ok) throw new Error("La déconnexion a échoué.");
    window.location.assign("/");
  } catch (error) {
    logoutButton.disabled = false;
    applicationsCount.textContent = error.message;
  }
});

loadApplications();
