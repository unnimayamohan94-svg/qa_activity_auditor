let auditData = [];

let selectedSummaryFilter = "";


/* =========================================================
   CONSTANTS
========================================================= */

const SECTION_ORDER = [
    "QA Activities – Last Week",
    "Ongoing tasks in QA bucket",
    "Overall UAT Items",
    "QA Backlog",
    "Overall Adhoc task",
    "Overall active"
];


/* =========================================================
   LOAD AUDIT DATA
========================================================= */

async function loadAudit(showLoader = false) {

    const extractionDateElement =
        document.getElementById("extractionDate");

    const extractionDate =
        extractionDateElement.value;


    if (!extractionDate) {

        alert("Please select an Extraction Date.");

        return;
    }


    if (showLoader) {
        setLoading(true);
    }


    try {

        const response = await fetch(
            `/azure-devops/audit?extraction_date=${encodeURIComponent(extractionDate)}`
        );


        if (!response.ok) {

            throw new Error(
                `Failed to load audit data (${response.status})`
            );

        }


        const data =
            await response.json();


        auditData =
            Array.isArray(data.audits)
                ? data.audits
                : [];


        selectedSummaryFilter = "";

        updateSummary();

        populateSectionFilter();

        populateActivityFilter();

        renderSections();

        showEmptyDetails();


    } catch (error) {

        console.error(
            "Error loading audit:",
            error
        );


        auditData = [];

        updateSummary();

        renderSections();


        const detailsContent =
            document.getElementById(
                "detailsContent"
            );


        if (detailsContent) {

            detailsContent.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">!</div>
                    <h3>Failed to load audit data</h3>
                    <p>${escapeHtml(error.message)}</p>
                </div>
            `;

        }

    } finally {

        if (showLoader) {
            setLoading(false);
        }

    }

}


/* =========================================================
   LOADING / PRELOADER
========================================================= */

function setLoading(isLoading) {

    const overlay =
        document.getElementById(
            "loadingOverlay"
        );


    const button =
        document.getElementById(
            "runAuditButton"
        );


    if (isLoading) {

        overlay.classList.remove(
            "hidden"
        );


        button.disabled = true;

        button.classList.add(
            "is-loading"
        );

    } else {

        overlay.classList.add(
            "hidden"
        );


        button.disabled = false;

        button.classList.remove(
            "is-loading"
        );

    }

}


/* =========================================================
   SUMMARY
========================================================= */

function updateSummary() {

    const total =
        auditData.length;


    let passed = 0;

    let failed = 0;


    auditData.forEach(audit => {

        const hasFailure =
            audit.results?.some(
                result =>
                    result.status === "FAIL"
            );


        if (hasFailure) {

            failed++;

        } else {

            passed++;

        }

    });


    document.getElementById(
        "totalTasks"
    ).textContent = total;


    document.getElementById(
        "passedTasks"
    ).textContent = passed;


    document.getElementById(
        "failedTasks"
    ).textContent = failed;


    updateSummaryCardState();

}


/* =========================================================
   SUMMARY CARD FILTER
========================================================= */

function applySummaryFilter(filter) {

    selectedSummaryFilter = filter;


    const statusFilter =
        document.getElementById(
            "statusFilter"
        );


    if (filter === "PASS") {

        statusFilter.value = "PASS";

    } else if (filter === "FAIL") {

        statusFilter.value = "FAIL";

    } else {

        statusFilter.value = "";

    }


    updateSummaryCardState();

    renderSections();

    scrollToResults();

}


/* =========================================================
   SUMMARY CARD ACTIVE STATE
========================================================= */

function updateSummaryCardState() {

    const cards = [
        document.getElementById("totalCard"),
        document.getElementById("passedCard"),
        document.getElementById("failedCard")
    ];


    cards.forEach(card => {

        if (card) {
            card.classList.remove(
                "summary-card-active"
            );
        }

    });


    if (selectedSummaryFilter === "PASS") {

        document
            .getElementById("passedCard")
            ?.classList.add(
                "summary-card-active"
            );

    } else if (
        selectedSummaryFilter === "FAIL"
    ) {

        document
            .getElementById("failedCard")
            ?.classList.add(
                "summary-card-active"
            );

    } else {

        document
            .getElementById("totalCard")
            ?.classList.add(
                "summary-card-active"
            );

    }

}


/* =========================================================
   SECTION FILTER
========================================================= */

function populateSectionFilter() {

    const select =
        document.getElementById(
            "sectionFilter"
        );


    const sections = [
        ...new Set(
            auditData
                .map(
                    audit => audit.section
                )
                .filter(Boolean)
        )
    ];


    const orderedSections =
        SECTION_ORDER.filter(
            section =>
                sections.includes(section)
        );


    sections.forEach(section => {

        if (
            !orderedSections.includes(section)
        ) {

            orderedSections.push(section);

        }

    });


    select.innerHTML =
        `<option value="">All Sections</option>`;


    orderedSections.forEach(section => {

        const option =
            document.createElement(
                "option"
            );


        option.value = section;

        option.textContent = section;


        select.appendChild(option);

    });

}


/* =========================================================
   ACTIVITY FILTER
========================================================= */

function populateActivityFilter() {

    const select =
        document.getElementById(
            "activityFilter"
        );


    const activities = [
        ...new Set(
            auditData
                .map(
                    audit =>
                        audit.activity_type
                )
                .filter(Boolean)
        )
    ].sort();


    select.innerHTML =
        `<option value="">All Activities</option>`;


    activities.forEach(activity => {

        const option =
            document.createElement(
                "option"
            );


        option.value = activity;

        option.textContent = activity;


        select.appendChild(option);

    });

}


/* =========================================================
   FILTERED DATA
========================================================= */

function getFilteredAudits() {

    const search =
        document
            .getElementById("search")
            .value
            .trim()
            .toLowerCase();


    const section =
        document
            .getElementById(
                "sectionFilter"
            )
            .value;


    const activity =
        document
            .getElementById(
                "activityFilter"
            )
            .value;


    const status =
        document
            .getElementById(
                "statusFilter"
            )
            .value;


    const ongoing =
        document
            .getElementById(
                "ongoingFilter"
            )
            .value;


    return auditData.filter(audit => {

        const titleMatch =
            !search ||
            (audit.title || "")
                .toLowerCase()
                .includes(search);


        const sectionMatch =
            !section ||
            audit.section === section;


        const activityMatch =
            !activity ||
            audit.activity_type === activity;


        const ongoingMatch =
            ongoing === "" ||
            String(
                Boolean(audit.ongoing)
            ) === ongoing;


        let auditStatus =
            "PASS";


        if (
            audit.results?.some(
                result =>
                    result.status === "FAIL"
            )
        ) {

            auditStatus = "FAIL";

        }


        const statusMatch =
            !status ||
            auditStatus === status;


        return (
            titleMatch &&
            sectionMatch &&
            activityMatch &&
            ongoingMatch &&
            statusMatch
        );

    });

}


/* =========================================================
   SECTION STATISTICS
========================================================= */

function getAuditStatus(audit) {

    return audit.results?.some(
        result =>
            result.status === "FAIL"
    )
        ? "FAIL"
        : "PASS";

}


function getSectionStats(audits) {

    let passed = 0;

    let failed = 0;


    audits.forEach(audit => {

        if (
            getAuditStatus(audit) === "FAIL"
        ) {

            failed++;

        } else {

            passed++;

        }

    });


    return {
        total: audits.length,
        passed,
        failed
    };

}


/* =========================================================
   RENDER ALL SECTIONS
========================================================= */

function renderSections() {

    const container =
        document.getElementById(
            "sectionsContainer"
        );


    const filtered =
        getFilteredAudits();


    container.innerHTML = "";


    const sectionNames =
        getSectionNames();


    if (sectionNames.length === 0) {

        container.innerHTML = `
            <div class="no-results-card">
                <div class="no-results-icon">⌕</div>
                <h3>No audit results found</h3>
                <p>
                    Run the audit or adjust your filters.
                </p>
            </div>
        `;

        return;
    }


    sectionNames.forEach(
        (sectionName, index) => {

            const sectionAudits =
                filtered.filter(
                    audit =>
                        audit.section ===
                        sectionName
                );


            const stats =
                getSectionStats(
                    sectionAudits
                );


            const card =
                createSectionCard(
                    sectionName,
                    sectionAudits,
                    stats,
                    index === 0
                );


            container.appendChild(card);

        }
    );


    /*
     * If a selected section has no matching
     * records after filtering, tell the user.
     */

    const visibleCards =
        container.querySelectorAll(
            ".section-card"
        );


    visibleCards.forEach(card => {

        const table =
            card.querySelector(
                ".section-table-body"
            );


        if (
            table &&
            table.children.length === 0
        ) {

            const emptyRow =
                document.createElement(
                    "tr"
                );


            emptyRow.innerHTML = `
                <td colspan="9"
                    class="section-empty">
                    No tasks match the current filters.
                </td>
            `;


            table.appendChild(
                emptyRow
            );

        }

    });

}


/* =========================================================
   SECTION NAMES
========================================================= */

function getSectionNames() {

    const existingSections = [
        ...new Set(
            auditData
                .map(
                    audit => audit.section
                )
                .filter(Boolean)
        )
    ];


    const selectedSection =
        document
            .getElementById(
                "sectionFilter"
            )
            .value;


    if (selectedSection) {

        return [selectedSection];

    }


    const ordered =
        SECTION_ORDER.filter(
            section =>
                existingSections.includes(
                    section
                )
        );


    existingSections.forEach(section => {

        if (
            !ordered.includes(section)
        ) {

            ordered.push(section);

        }

    });


    return ordered;

}


/* =========================================================
   CREATE SECTION CARD
========================================================= */

function createSectionCard(
    sectionName,
    audits,
    stats,
    openByDefault
) {

    const card =
        document.createElement(
            "section"
        );


    card.className =
        "section-card";


    const sectionId =
        `section-${slugify(sectionName)}`;


    const header =
        document.createElement(
            "div"
        );


    header.className =
        "section-header";


    header.innerHTML = `
        <div class="section-title-area">

            <button
                type="button"
                class="section-toggle"
                aria-expanded="${openByDefault}"
                aria-controls="${sectionId}"
            >
                <span class="section-chevron">
                    ${openByDefault ? "▼" : "▶"}
                </span>
            </button>

            <div>
                <h2>
                    ${escapeHtml(sectionName)}
                </h2>

                <p>
                    ${stats.total}
                    ${stats.total === 1 ? "task" : "tasks"}
                </p>
            </div>

        </div>


        <div class="section-metrics">

            <span class="metric-chip metric-total">
                <strong>${stats.total}</strong>
                Total
            </span>

            <span class="metric-chip metric-pass">
                <strong>${stats.passed}</strong>
                Passed
            </span>

            <span class="metric-chip metric-fail">
                <strong>${stats.failed}</strong>
                Failed
            </span>

        </div>
    `;


    const body =
        document.createElement(
            "div"
        );


    body.id = sectionId;

    body.className =
        "section-body";


    if (!openByDefault) {

        body.classList.add(
            "collapsed"
        );

    }


    body.innerHTML =
        createSectionTable(
            audits
        );


    card.appendChild(header);

    card.appendChild(body);


    const toggle =
        header.querySelector(
            ".section-toggle"
        );


    toggle.addEventListener(
        "click",
        function () {

            const isCollapsed =
                body.classList.toggle(
                    "collapsed"
                );


            const expanded =
                !isCollapsed;


            toggle.setAttribute(
                "aria-expanded",
                String(expanded)
            );


            toggle.querySelector(
                ".section-chevron"
            ).textContent =
                expanded
                    ? "▼"
                    : "▶";

        }
    );


    /*
     * Clicking the section header itself
     * also opens/closes it.
     */

    header.addEventListener(
        "click",
        function(event) {

            if (
                event.target.closest(
                    ".section-toggle"
                )
            ) {
                return;
            }


            toggle.click();

        }
    );


    return card;

}


/* =========================================================
   SECTION TABLE
========================================================= */

function createSectionTable(
    audits
) {

    if (!audits.length) {

        return `
            <div class="section-no-data">
                <div class="section-no-data-icon">⌕</div>
                <p>
                    No tasks match the current filters.
                </p>
            </div>
        `;

    }


    let rows = "";


    audits.forEach(audit => {

        const status =
            getAuditStatus(audit);


        rows += `

            <tr>

                <td class="id-cell">
                    ${escapeHtml(
                        String(
                            audit.work_item_id ?? "-"
                        )
                    )}
                </td>


                <td>
                    <span class="activity-badge">
                        ${escapeHtml(
                            audit.activity_type ||
                            "Unclassified"
                        )}
                    </span>
                </td>


                <td class="title-cell">
                    ${escapeHtml(
                        audit.title || "-"
                    )}
                </td>


                <td>
                    ${escapeHtml(
                        audit.assignee || "-"
                    )}
                </td>


                <td>
                    <span class="state-badge">
                        ${escapeHtml(
                            audit.state || "-"
                        )}
                    </span>
                </td>


                <td class="completion-cell">

                    ${
                        audit.completion_percentage !==
                        null &&
                        audit.completion_percentage !==
                        undefined
                            ? `${escapeHtml(
                                String(
                                    audit.completion_percentage
                                )
                              )}%`
                            : "-"
                    }

                </td>


                <td>

                    <span class="
                        status-badge
                        ${
                            status === "PASS"
                                ? "status-pass"
                                : "status-fail"
                        }
                    ">

                        <span class="status-dot"></span>

                        ${status}

                    </span>

                </td>


                <td>

                    ${
                        audit.ongoing
                            ? `
                                <span class="ongoing-badge">
                                    Ongoing
                                </span>
                              `
                            : ""
                    }

                </td>


                <td>

                    <button
                        type="button"
                        class="view-button"
                        data-work-item-id="${
                            audit.work_item_id
                        }"
                    >
                        View
                    </button>

                </td>

            </tr>

        `;

    });


    return `

        <div class="table-wrapper">

            <table class="section-table">

                <thead>

                    <tr>
                        <th>ID</th>
                        <th>ACTIVITY</th>
                        <th>TITLE</th>
                        <th>ASSIGNEE</th>
                        <th>STATE</th>
                        <th>COMPLETION</th>
                        <th>STATUS</th>
                        <th>TYPE</th>
                        <th>DETAILS</th>
                    </tr>

                </thead>


                <tbody class="section-table-body">

                    ${rows}

                </tbody>

            </table>

        </div>

    `;

}


/* =========================================================
   SHOW DETAILS
========================================================= */

function showDetails(workItemId) {

    const audit =
        auditData.find(
            item =>
                String(
                    item.work_item_id
                ) ===
                String(workItemId)
        );


    if (!audit) {
        return;
    }

    // Show Audit Details only after a task is selected.
    const detailsPanel =
        document.getElementById("detailsPanel");

    if (detailsPanel) {
        detailsPanel.style.display = "block";
    }


    const container =
        document.getElementById(
            "detailsContent"
        );


    const status =
        getAuditStatus(audit);


    let html = `

        <div class="details-header">

            <div>

                <span class="details-eyebrow">
                    Audit Details
                </span>

                <h2>
                    ${escapeHtml(
                        audit.title || "-"
                    )}
                </h2>

            </div>


            <span class="
                status-badge
                ${
                    status === "PASS"
                        ? "status-pass"
                        : "status-fail"
                }
            ">
                <span class="status-dot"></span>
                ${status}
            </span>

        </div>


        <div class="details-meta">

            <div>
                <span>Work Item</span>
                <strong>
                    ${escapeHtml(
                        String(
                            audit.work_item_id ??
                            "-"
                        )
                    )}
                </strong>
            </div>


            <div>
                <span>Section</span>
                <strong>
                    ${escapeHtml(
                        audit.section || "-"
                    )}
                </strong>
            </div>


            <div>
                <span>Activity</span>
                <strong>
                    ${escapeHtml(
                        audit.activity_type ||
                        "Unclassified"
                    )}
                </strong>
            </div>


            <div>
                <span>Assignee</span>
                <strong>
                    ${escapeHtml(
                        audit.assignee || "-"
                    )}
                </strong>
            </div>


            <div>
                <span>State</span>
                <strong>
                    ${escapeHtml(
                        audit.state || "-"
                    )}
                </strong>
            </div>

        </div>

    `;


    if (
        !audit.results ||
        audit.results.length === 0
    ) {

        html += `
            <div class="no-validation-results">
                No validation results.
            </div>
        `;

    } else {

        html += `

            <div class="results-heading">
                Validation Results
            </div>


            <div class="details-table-wrapper">

                <table class="details-table">

                    <thead>

                        <tr>
                            <th>RULE</th>
                            <th>FIELD</th>
                            <th>STATUS</th>
                            <th>SEVERITY</th>
                            <th>MESSAGE</th>
                        </tr>

                    </thead>


                    <tbody>
        `;


        audit.results.forEach(result => {

            html += `

                <tr>

                    <td class="rule-cell">
                        ${escapeHtml(
                            result.rule_id || "-"
                        )}
                    </td>


                    <td>
                        ${escapeHtml(
                            result.field_name || "-"
                        )}
                    </td>


                    <td>

                        <span class="
                            result-status
                            ${
                                result.status === "PASS"
                                    ? "result-pass"
                                    : "result-fail"
                            }
                        ">
                            ${escapeHtml(
                                result.status || "-"
                            )}
                        </span>

                    </td>


                    <td>

                        <span class="
                            severity-badge
                            severity-${String(
                                result.severity ||
                                ""
                            ).toLowerCase()}
                        ">
                            ${escapeHtml(
                                result.severity || "-"
                            )}
                        </span>

                    </td>


                    <td>
                        ${escapeHtml(
                            result.message || "-"
                        )}
                    </td>

                </tr>

            `;

        });


        html += `

                    </tbody>

                </table>

            </div>

        `;

    }


    /* =====================================================
       DEVOPS UPDATE DRAFT
       PAT/write-back is intentionally not connected yet.
    ====================================================== */

    html += `

        <div class="devops-update-card">

            <div class="devops-update-header">
                <div>
                    <span class="details-eyebrow">Azure DevOps</span>
                    <h3>Update Work Item</h3>
                    <p>Prepare a field update. Nothing is written to DevOps yet.</p>
                </div>
                <span class="devops-status-badge">Write-back not connected</span>
            </div>

            <div class="devops-update-grid">

                <div class="devops-field">
                    <label for="devopsWorkItem">Work Item</label>
                    <select id="devopsWorkItem">
                        <option value="${escapeHtml(String(audit.work_item_id ?? ""))}">
                            ${escapeHtml(String(audit.work_item_id ?? "-"))} – ${escapeHtml(audit.title || "Untitled")}
                        </option>
                    </select>
                </div>

                <div class="devops-field">
                    <label for="devopsField">Field to Update</label>
                    <select id="devopsField">
                        ${getDevopsFieldOptions(audit)}
                    </select>
                </div>

                <div class="devops-field devops-mode-field">
                    <label for="devopsUpdateMode">Update Mode</label>
                    <select id="devopsUpdateMode">
                        <option value="append">Append to existing content</option>
                        <option value="replace">Replace existing content</option>
                    </select>
                </div>

                <div class="devops-field devops-content-field">
                    <label for="devopsUpdateContent">Comment / Update Content</label>
                    <textarea
                        id="devopsUpdateContent"
                        rows="5"
                        placeholder="Enter the QA information you want to add or use to replace the selected field..."
                    ></textarea>
                </div>

            </div>

            <div class="devops-update-actions">
                <button type="button" class="btn btn-secondary" id="previewDevopsUpdate">
                    Preview Changes
                </button>
                <button type="button" class="btn btn-primary" id="updateDevopsButton" disabled title="PAT/write-back integration will be enabled later">
                    Update DevOps
                </button>
            </div>

            <div id="devopsPreview" class="devops-preview hidden"></div>

        </div>

    `;


    container.innerHTML =
        html;


    const previewButton =
        document.getElementById("previewDevopsUpdate");

    if (previewButton) {
        previewButton.addEventListener("click", previewDevopsUpdate);
    }


    document
        .getElementById(
            "detailsPanel"
        )
        .scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

}


/* =========================================================
   DEVOPS UPDATE FIELDS

   Keep this list aligned with the fields exposed by the
   validation results. The preferred order matches the
   QA fields used by the auditor. Any additional field name
   returned by validation results is added automatically.
========================================================= */

function getDevopsFieldOptions(audit) {

    const preferredFields = [
        "Channel Name",
        "State",
        "Target Start Date",
        "Target End Date",
        "Actual Start Date",
        "Actual End Date",
        "Detailed Description",
        "Completion Percentage",
        "UAT Start Date",
        "UAT End Date",
        "UAT Completion Percentage",
        "Overall UAT Bugs",
        "Tags"
    ];


    const validatedFields = (audit?.results || [])
        .map(result => result?.field_name)
        .filter(Boolean);


    const fields = [];


    [...preferredFields, ...validatedFields].forEach(field => {

        if (!fields.includes(field)) {
            fields.push(field);
        }

    });


    return fields.map(field => `
        <option value="${escapeHtml(field)}">
            ${escapeHtml(field)}
        </option>
    `).join("");

}


/* =========================================================
   DEVOPS UPDATE PREVIEW
========================================================= */

function previewDevopsUpdate() {

    const workItem =
        document.getElementById("devopsWorkItem");

    const field =
        document.getElementById("devopsField");

    const mode =
        document.getElementById("devopsUpdateMode");

    const content =
        document.getElementById("devopsUpdateContent");

    const preview =
        document.getElementById("devopsPreview");


    if (!workItem || !field || !mode || !content || !preview) {
        return;
    }


    const value = content.value.trim();

    if (!value) {
        preview.classList.remove("hidden");
        preview.innerHTML = `
            <div class="devops-preview-error">
                Please enter content before previewing the update.
            </div>
        `;
        return;
    }


    const fieldName =
        field.options[field.selectedIndex]?.text || field.value;

    const modeName =
        mode.value === "append"
            ? "Append to existing content"
            : "Replace existing content";


    preview.classList.remove("hidden");

    preview.innerHTML = `
        <div class="devops-preview-header">
            <strong>Proposed Update</strong>
            <span>${escapeHtml(modeName)}</span>
        </div>

        <div class="devops-preview-meta">
            <div><span>Work Item</span><strong>${escapeHtml(workItem.value)}</strong></div>
            <div><span>Field</span><strong>${escapeHtml(fieldName)}</strong></div>
        </div>

        <div class="devops-preview-content">
            ${escapeHtml(value).replaceAll("\n", "<br>")}
        </div>

        <div class="devops-preview-note">
            Preview only. No Azure DevOps Work Item has been changed.
        </div>
    `;

}


/* =========================================================
   EMPTY DETAILS
========================================================= */

function showEmptyDetails() {

    const container =
        document.getElementById(
            "detailsContent"
        );


    container.innerHTML = "";


    const panel =
        document.getElementById(
            "detailsPanel"
        );


    if (!panel) {
        return;
    }

    // Keep Audit Details hidden until a task is selected.
    panel.style.display = "none";

    const emptyState =
        panel.querySelector(
            ".details-empty"
        );

    if (emptyState) {
        emptyState.style.display = "flex";
    }

}


function hideEmptyDetails() {

    const panel =
        document.getElementById(
            "detailsPanel"
        );

    if (!panel) {
        return;
    }

    panel.style.display = "block";

    const emptyState =
        panel.querySelector(
            ".details-empty"
        );

    if (emptyState) {
        emptyState.style.display = "none";
    }

}


/* =========================================================
   CLEAR FILTERS
========================================================= */

function clearFilters() {

    document.getElementById(
        "search"
    ).value = "";


    document.getElementById(
        "sectionFilter"
    ).value = "";


    document.getElementById(
        "activityFilter"
    ).value = "";


    document.getElementById(
        "statusFilter"
    ).value = "";


    document.getElementById(
        "ongoingFilter"
    ).value = "";


    selectedSummaryFilter = "";


    updateSummaryCardState();

    renderSections();

}


/* =========================================================
   SCROLL TO RESULTS
========================================================= */

function scrollToResults() {

    const sections =
        document.getElementById(
            "sectionsContainer"
        );


    if (!sections) {
        return;
    }


    sections.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* =========================================================
   HELPERS
========================================================= */

function slugify(value) {

    return String(value)
        .toLowerCase()
        .replace(
            /[^a-z0-9]+/g,
            "-"
        )
        .replace(
            /^-+|-+$/g,
            "");

}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


/* =========================================================
   EVENT HANDLERS
========================================================= */

function setupEventHandlers() {

    /*
     * Run Audit
     */

    document
        .getElementById(
            "runAuditButton"
        )
        .addEventListener(
            "click",
            function() {

                loadAudit(true);

            }
        );


    /*
     * Refresh
     */

    document
        .getElementById(
            "refreshButton"
        )
        .addEventListener(
            "click",
            function() {

                loadAudit(true);

            }
        );


    /*
     * Swagger
     */

    document
        .getElementById(
            "swaggerButton"
        )
        .addEventListener(
            "click",
            function() {

                window.open(
                    "/docs",
                    "_blank"
                );

            }
        );


    /*
     * Summary cards
     */

    document
        .getElementById(
            "totalCard"
        )
        .addEventListener(
            "click",
            function() {

                applySummaryFilter("");

            }
        );


    document
        .getElementById(
            "passedCard"
        )
        .addEventListener(
            "click",
            function() {

                applySummaryFilter("PASS");

            }
        );


    document
        .getElementById(
            "failedCard"
        )
        .addEventListener(
            "click",
            function() {

                applySummaryFilter("FAIL");

            }
        );


    /*
     * Filters
     */

    [
        "search",
        "sectionFilter",
        "activityFilter",
        "statusFilter",
        "ongoingFilter"
    ].forEach(id => {

        const element =
            document.getElementById(id);


        if (!element) {
            return;
        }


        element.addEventListener(
            "input",
            function() {

                if (
                    id !== "statusFilter"
                ) {

                    selectedSummaryFilter =
                        "";

                    updateSummaryCardState();

                }


                renderSections();

            }
        );


        element.addEventListener(
            "change",
            function() {

                if (
                    id !== "statusFilter"
                ) {

                    selectedSummaryFilter =
                        "";

                    updateSummaryCardState();

                }


                renderSections();

            }
        );

    });


    /*
     * Clear filters
     */

    document
        .getElementById(
            "clearFilters"
        )
        .addEventListener(
            "click",
            clearFilters
        );


    /*
     * View buttons.
     * Event delegation is used because the
     * section tables are generated dynamically.
     */

    document
        .getElementById(
            "sectionsContainer"
        )
        .addEventListener(
            "click",
            function(event) {

                const button =
                    event.target.closest(
                        ".view-button"
                    );


                if (!button) {
                    return;
                }


                hideEmptyDetails();


                showDetails(
                    button.dataset.workItemId
                );

            }
        );

}


/* =========================================================
   INITIAL LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        setupEventHandlers();


        const dateInput =
            document.getElementById(
                "extractionDate"
            );


        /*
         * Use local browser date rather than
         * toISOString(), which can shift the
         * date because of timezone conversion.
         */

        const now =
            new Date();


        const year =
            now.getFullYear();


        const month =
            String(
                now.getMonth() + 1
            ).padStart(
                2,
                "0"
            );


        const day =
            String(
                now.getDate()
            ).padStart(
                2,
                "0"
            );


        dateInput.value =
            `${year}-${month}-${day}`;


        updateSummary();

        renderSections();

        showEmptyDetails();

        loadAudit(false);

    }
);
