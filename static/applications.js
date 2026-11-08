const workspace = document.querySelector("#applications-workspace");
const applicationsList = document.querySelector("#application-list");
const applicationsCount = document.querySelector("#applications-count");
const statAppsCount = document.querySelector("#stat-apps-count");
const refreshButton = document.querySelector("#refresh-applications");
const logoutButton = document.querySelector("#logout-button");
const isStaff = workspace.dataset.isStaff === "true";
const userRole = workspace.dataset.userRole;

function createApplicationCard(application) {
  const card = document.createElement("article");
  card.className = "application-card";

  const heading = document.createElement("div");
  heading.className = "application-card-heading";
  const jobTitle = document.createElement("h2");
  jobTitle.textContent = application.job_title;

  const metaRight = document.createElement("div");
  metaRight.style.display = "flex";
  metaRight.style.alignItems = "center";
  metaRight.style.gap = "8px";

  const statusBadge = document.createElement("span");
  statusBadge.className = "status-badge";
  statusBadge.textContent = "Transmise";

  const applicationId = document.createElement("span");
  applicationId.className = "application-id";
  applicationId.textContent = `Candidature #${application.id}`;

  metaRight.append(statusBadge, applicationId);
  heading.append(jobTitle, metaRight);
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

  // Action buttons (Withdraw / Delete)
  const cardFooter = document.createElement("div");
  cardFooter.className = "application-card-footer";

  const deleteBtn = document.createElement("button");
  deleteBtn.className = "card-action-btn danger-btn";
  deleteBtn.type = "button";
  deleteBtn.textContent = isStaff ? "Supprimer la candidature" : "Retirer ma candidature";
  deleteBtn.addEventListener("click", async () => {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cette candidature ?")) return;
    try {
      const res = await fetch(`/api/applications/${application.id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Erreur lors de la suppression.");
      loadApplications();
    } catch (err) {
      alert(err.message);
    }
  });

  cardFooter.append(deleteBtn);
  card.append(cardFooter);

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

    const count = data.applications.length;
    if (statAppsCount) statAppsCount.textContent = count;
    applicationsCount.textContent = `${count} candidature${count === 1 ? "" : "s"}`;

    if (count === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.innerHTML = `
        <p>${isStaff ? "Aucune candidature reçue pour le moment." : "Vous n’avez pas encore envoyé de candidature."}</p>
        ${!isStaff ? '<a class="apply-button primary-btn" style="display:inline-block;margin-top:10px" href="/#offres">Voir toutes les offres disponibles →</a>' : ""}
      `;
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

// Staff & Employee workspace features (publish jobs, manage listings, Elasticsearch status)
if (isStaff || userRole === "admin" || userRole === "employee" || userRole === "recruiter") {
  const tabApps = document.querySelector("#tab-applications");
  const tabPublish = document.querySelector("#tab-publish-job");
  const tabManage = document.querySelector("#tab-manage-jobs");

  const panelApps = document.querySelector("#panel-applications");
  const panelPublish = document.querySelector("#panel-publish-job");
  const panelManage = document.querySelector("#panel-manage-jobs");

  const esIndicator = document.querySelector("#es-status-indicator");
  const reindexBtn = document.querySelector("#reindex-btn");

  const createJobForm = document.querySelector("#create-job-form");
  const publishFeedback = document.querySelector("#publish-feedback");
  const adminJobsList = document.querySelector("#admin-jobs-list");

  function switchTab(activeTab, activePanel) {
    [tabApps, tabPublish, tabManage].forEach((t) => t && t.classList.remove("active"));
    [panelApps, panelPublish, panelManage].forEach((p) => p && (p.hidden = true));
    activeTab.classList.add("active");
    activePanel.hidden = false;
  }

  if (tabApps) tabApps.addEventListener("click", () => switchTab(tabApps, panelApps));
  if (tabPublish) tabPublish.addEventListener("click", () => switchTab(tabPublish, panelPublish));
  if (tabManage) {
    tabManage.addEventListener("click", () => {
      switchTab(tabManage, panelManage);
      loadAdminJobs();
    });
  }

  // Check ES status
  async function checkESStatus() {
    if (!esIndicator) return;
    try {
      const res = await fetch("/api/es/status");
      const data = await res.json();
      if (data.status === "online") {
        esIndicator.textContent = "En ligne (9200)";
        esIndicator.className = "stat-value text-green";
      } else {
        esIndicator.textContent = "Hors ligne (Fallback local)";
        esIndicator.className = "stat-value text-orange";
      }
    } catch {
      esIndicator.textContent = "Indisponible";
      esIndicator.className = "stat-value text-orange";
    }
  }

  if (reindexBtn) {
    reindexBtn.addEventListener("click", async () => {
      reindexBtn.disabled = true;
      reindexBtn.textContent = "En cours...";
      try {
        const res = await fetch("/api/admin/reindex", { method: "POST" });
        const data = await res.json();
        alert(data.message || "Réindexation terminée.");
      } catch (err) {
        alert("Erreur de réindexation: " + err.message);
      } finally {
        reindexBtn.disabled = false;
        reindexBtn.textContent = "Réindexer ES";
        checkESStatus();
      }
    });
  }

  // Submit job form
  if (createJobForm) {
    createJobForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      publishFeedback.textContent = "Publication en cours...";
      publishFeedback.className = "form-feedback";

      const formData = new FormData(createJobForm);
      const payload = {
        title: formData.get("title"),
        company: formData.get("company"),
        location: formData.get("location"),
        contract: formData.get("contract"),
        salary: formData.get("salary"),
        description: formData.get("description"),
        tags: formData.get("tags"),
      };

      try {
        const res = await fetch("/api/jobs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Impossible de publier l'offre.");

        publishFeedback.textContent = `✓ Offre « ${data.job.title} » publiée avec succès !`;
        publishFeedback.className = "form-feedback text-green";
        createJobForm.reset();
      } catch (err) {
        publishFeedback.textContent = err.message;
        publishFeedback.className = "form-feedback text-danger";
      }
    });
  }

  // Load existing jobs for admin
  async function loadAdminJobs() {
    if (!adminJobsList) return;
    adminJobsList.replaceChildren();
    adminJobsList.textContent = "Chargement des offres...";

    try {
      const res = await fetch("/api/jobs");
      const data = await res.json();
      adminJobsList.replaceChildren();

      if (!data.jobs || data.jobs.length === 0) {
        adminJobsList.textContent = "Aucune offre enregistrée.";
        return;
      }

      data.jobs.forEach((job) => {
        const item = document.createElement("div");
        item.className = "admin-job-row";

        const info = document.createElement("div");
        info.innerHTML = `<strong>#${job.id} ${job.title}</strong> — <span>${job.company} (${job.location})</span> <span class="contract-badge">${job.contract}</span>`;

        const delBtn = document.createElement("button");
        delBtn.className = "card-action-btn danger-btn";
        delBtn.textContent = "Supprimer";
        delBtn.addEventListener("click", async () => {
          if (!confirm(`Supprimer définitivement l'offre "${job.title}" ?`)) return;
          try {
            const delRes = await fetch(`/api/jobs/${job.id}`, { method: "DELETE" });
            if (!delRes.ok) throw new Error("Erreur de suppression.");
            loadAdminJobs();
          } catch (err) {
            alert(err.message);
          }
        });

        item.append(info, delBtn);
        adminJobsList.append(item);
      });
    } catch (err) {
      adminJobsList.textContent = err.message;
    }
  }

  checkESStatus();
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
