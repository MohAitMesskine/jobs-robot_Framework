const searchForm = document.querySelector("#search-form");
const jobList = document.querySelector("#job-list");
const resultsCount = document.querySelector("#results-count");
const applicationPanel = document.querySelector("#candidature");
const applicationForm = document.querySelector("#application-form");
const feedback = document.querySelector("#form-feedback");
const authPanel = document.querySelector("#auth-panel");
const authFeedback = document.querySelector("#auth-feedback");
const authToggle = document.querySelector("#auth-toggle");
const logoutButton = document.querySelector("#logout-button");
let currentUser = null;
let selectedJob = null;

function createJobCard(job) {
  const card = document.createElement("article");
  card.className = "job-card";

  const top = document.createElement("div");
  top.className = "job-card-top";

  const companyMark = document.createElement("span");
  companyMark.className = "company-mark";
  companyMark.textContent = job.company.charAt(0);
  companyMark.setAttribute("aria-hidden", "true");

  const details = document.createElement("div");
  details.className = "job-details";
  const title = document.createElement("h3");
  title.textContent = job.title;
  const company = document.createElement("p");
  company.textContent = job.company;
  details.append(title, company);

  const contract = document.createElement("span");
  contract.className = "contract-badge";
  contract.textContent = job.contract;
  top.append(companyMark, details, contract);

  const description = document.createElement("p");
  description.className = "job-description";
  description.textContent = job.description;

  const bottom = document.createElement("div");
  bottom.className = "job-card-bottom";
  const metadata = document.createElement("div");
  metadata.className = "job-metadata";
  const location = document.createElement("span");
  location.textContent = `⌖  ${job.location}`;
  const salary = document.createElement("span");
  salary.textContent = `↗  ${job.salary}`;
  metadata.append(location, salary);

  const apply = document.createElement("button");
  apply.className = "apply-button";
  apply.type = "button";
  apply.textContent = "Postuler";
  apply.setAttribute("aria-label", `Postuler : ${job.title}`);
  apply.addEventListener("click", () => selectJob(job));
  bottom.append(metadata, apply);
  card.append(top, description, bottom);
  return card;
}

function selectJob(job) {
  selectedJob = job;
  document.querySelector("#application-job-id").value = job.id;
  document.querySelector("#selected-job").textContent =
    `Candidature pour « ${job.title} » chez ${job.company}.`;
  feedback.textContent = "";
  if (!currentUser) {
    authPanel.hidden = false;
    authFeedback.textContent = "Connectez-vous ou créez un compte pour postuler.";
    authPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    document.querySelector("#login-email").focus({ preventScroll: true });
    return;
  }
  applicationPanel.hidden = false;
  applicationPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  document.querySelector("#applicant-message").focus({ preventScroll: true });
}

function updateAuthControls() {
  const userStatus = document.querySelector("#user-status");
  userStatus.hidden = !currentUser;
  userStatus.textContent = currentUser ? `Bonjour, ${currentUser.name}` : "";
  authToggle.hidden = Boolean(currentUser);
  logoutButton.hidden = !currentUser;
}

async function submitAuthForm(event, endpoint) {
  event.preventDefault();
  authFeedback.textContent = "Vérification en cours…";
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Authentification impossible.");
    currentUser = result.user;
    updateAuthControls();
    authFeedback.textContent = "Vous êtes connecté·e.";
    document.querySelector("#login-form").reset();
    document.querySelector("#register-form").reset();
    authPanel.hidden = true;
    if (selectedJob) selectJob(selectedJob);
  } catch (error) {
    authFeedback.textContent = error.message;
  }
}

async function loadJobs(event) {
  if (event) event.preventDefault();
  const params = new URLSearchParams(new FormData(searchForm));
  const query = params.toString();
  resultsCount.textContent = "Recherche en cours…";
  jobList.replaceChildren();

  try {
    const response = await fetch(`/api/jobs${query ? `?${query}` : ""}`);
    if (!response.ok) throw new Error("Impossible de charger les offres.");
    const data = await response.json();
    resultsCount.textContent = `${data.jobs.length} offre${data.jobs.length > 1 ? "s" : ""} trouvée${data.jobs.length > 1 ? "s" : ""}`;
    if (data.jobs.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Aucune offre ne correspond à votre recherche. Essayez d’autres critères.";
      jobList.append(empty);
      return;
    }
    data.jobs.forEach((job) => jobList.append(createJobCard(job)));
  } catch (error) {
    resultsCount.textContent = error.message;
  }
}

searchForm.addEventListener("submit", loadJobs);
document.querySelector("#clear-filters").addEventListener("click", () => {
  searchForm.reset();
  loadJobs();
});

authToggle.addEventListener("click", () => {
  authPanel.hidden = !authPanel.hidden;
  if (!authPanel.hidden) {
    authPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    document.querySelector("#login-email").focus({ preventScroll: true });
  }
});
document.querySelector("#login-form").addEventListener("submit", (event) => {
  submitAuthForm(event, "/api/auth/login");
});
document.querySelector("#register-form").addEventListener("submit", (event) => {
  submitAuthForm(event, "/api/auth/register");
});
logoutButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/auth/logout", { method: "POST" });
    if (!response.ok) throw new Error("La déconnexion a échoué.");
    currentUser = null;
    selectedJob = null;
    applicationPanel.hidden = true;
    updateAuthControls();
  } catch (error) {
    authFeedback.textContent = error.message;
  }
});

applicationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  feedback.textContent = "Envoi en cours…";
  const formData = new FormData(applicationForm);
  const payload = Object.fromEntries(formData.entries());
  payload.job_id = Number(payload.job_id);

  try {
    const response = await fetch("/api/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "L’envoi a échoué.");
    feedback.textContent = "Merci ! Votre candidature a bien été envoyée.";
    applicationForm.reset();
  } catch (error) {
    feedback.textContent = error.message;
  }
});

async function loadCurrentUser() {
  try {
    const response = await fetch("/api/auth/me");
    if (response.status === 401) {
      currentUser = null;
      updateAuthControls();
      return;
    }
    if (!response.ok) throw new Error("Impossible de vérifier la connexion.");
    const data = await response.json();
    currentUser = data.user;
    updateAuthControls();
  } catch (error) {
    currentUser = null;
    authFeedback.textContent = error.message;
    updateAuthControls();
  }
}

loadCurrentUser();

loadJobs();
