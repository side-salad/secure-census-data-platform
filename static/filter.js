document.addEventListener("DOMContentLoaded", () => {
  const tableSections = document.querySelectorAll(".table-section");

  if (tableSections.length === 0) {
    setupTableSection(document);
  } else {
    tableSections.forEach(setupTableSection);
  }
});


// Sorting functions
function setupTableSection(section) {
  const table = section.querySelector(".data-table")
  const pagination = section.querySelector(".pagination")
  const searchInput = section.querySelector(".searchInput") 
  const searchEmail = section.querySelector(".searchEmail")
  const sortArrow = section.querySelector(".sortArrow")

  let sortAscending = true;
  let currentPage = 1;
  const rowsPerPage = 7;

  function paginateTable() {
    const tbody = table.querySelector("tbody");
    const allRows = Array.from(tbody.querySelectorAll("tr"));
    const addRow = allRows.find(row => row.classList.contains("add-row-trigger"));
    const dataRows = addRow ? allRows.filter(row => row !== addRow) : allRows;

    const totalPages = Math.ceil(dataRows.length / rowsPerPage);

    allRows.forEach(row => row.style.display = "none");

    dataRows.forEach((row, index) => {
      if (index >= (currentPage - 1) * rowsPerPage && index < currentPage * rowsPerPage) {
        row.style.display = "";
      }
    });

    if (addRow) {
      addRow.style.display = "";
      tbody.appendChild(addRow); 
    }

    if (pagination) {
      pagination.innerHTML = "";
      for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement("button");
        btn.textContent = i;
        btn.className = (i === currentPage) ? "active" : "";
        btn.onclick = () => {
          currentPage = i;
          paginateTable();
        };
        pagination.appendChild(btn);
      }
    }
  }

  function filterTable() {
    const unionVal = searchInput?.value.toLowerCase() || "";
    const emailVal = searchEmail?.value.toLowerCase() || "";
    const rows = table.querySelectorAll("tbody tr");

    rows.forEach(row => {
      const union = row.children[1].textContent.toLowerCase();
      const email = row.children[2].textContent.toLowerCase();
      row.style.display = (union.includes(unionVal) && email.includes(emailVal)) ? "" : "none";
    });

    currentPage = 1;
    paginateTable();
  }

  function sortTableByDate() {
    const tbody = table.querySelector("tbody");
    const allRows = Array.from(tbody.querySelectorAll("tr"));
    
    const addRow = allRows.find(row => row.classList.contains("add-row-trigger"));
    
    const dataRows = addRow ? allRows.filter(row => row !== addRow) : allRows;

    dataRows.sort((a, b) => {
      const dateA = new Date(a.children[3].textContent.trim());
      const dateB = new Date(b.children[3].textContent.trim());
      return sortAscending ? dateA - dateB : dateB - dateA;
    });

    dataRows.forEach(row => tbody.appendChild(row));

    if (addRow) tbody.appendChild(addRow);

    sortAscending = !sortAscending;
    if (sortArrow) sortArrow.textContent = sortAscending ? "▲" : "▼";

    paginateTable();
  }

  if (searchInput) searchInput.addEventListener("input", filterTable);
  if (searchEmail) searchEmail.addEventListener("input", filterTable);
  if (sortArrow) sortArrow.parentElement.addEventListener("click", sortTableByDate);

  paginateTable();
}


// Modal functions
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('modalBackdrop');
  const modalFields = document.getElementById('modalFields');
  const modalTitle = document.getElementById('modalTitle');
  const submitButton = document.getElementById('submitRow');
  const cancelButton = document.getElementById('cancelModal');
  const deleteButton = document.getElementById('deleteRow');

  document.querySelectorAll('.add-row-trigger').forEach(row => {
    row.addEventListener('click', () => {
      const tableType = row.dataset.table;
      modal.dataset.table = tableType;
      modal.dataset.mode = "add";
      modal.dataset.rowIndex = "";
      deleteButton.style.display = "none";

      modalFields.innerHTML = getModalFields(tableType);
      modalTitle.textContent = tableType === "admin-members" ? "Add Admin" : "Add Union Member";
      modal.style.display = "flex";
    });
  });

  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('edit-icon')) {
      const row = e.target.closest('tr');
      const section = row.closest('.table-section');
      const tableType = section.querySelector('h3').textContent.includes("Admin") ? "admin-members" : "union-members";

      modal.dataset.table = tableType;
      modal.dataset.mode = "edit";
      modal.dataset.rowIndex = row.rowIndex;
      deleteButton.style.display = "inline-block";

      const cells = row.querySelectorAll('td');
      modalFields.innerHTML = getModalFields(tableType, cells);
      modalTitle.textContent = "Edit Entry";
      modal.style.display = "flex";
    }
  });


  cancelButton.addEventListener("click", () => {
    modal.style.display = 'none';
  });

  deleteButton.addEventListener("click", () => {
    const tableType = modal.dataset.table;
    const email = document.getElementById("original_email")?.value?.trim() || document.getElementById("email")?.value?.trim();

    console.log("Deleting with email:", email);

    fetch(`/delete_${tableType}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_email: email })
    })
      .then(res => res.json())
      .then(data => {
        location.reload(true);
      })
      .catch(err => console.error("Delete failed:", err));
  });


  submitButton.addEventListener("click", () => {
    const tableType = modal.dataset.table;
    const mode = modal.dataset.mode;
    const payload = {};

    modalFields.querySelectorAll(".error-msg").forEach(el => el.remove());

    let hasEmptyField = false;

    modalFields.querySelectorAll("input").forEach(input => {
      const value = input.value.trim();
      payload[input.id] = value;

      if (input.type !== "hidden" && !value) {
        hasEmptyField = true;
        const error = document.createElement("div");
        error.className = "error-msg";
        error.style.color = "red";
        error.style.fontSize = "12px";
        error.style.marginTop = "2px";
        error.textContent = "This field is required.";
        input.insertAdjacentElement("afterend", error);
      }
    });

    if (hasEmptyField) return;

    let endpoint = "";
    if (mode === "edit") {
      payload["original_email"] = document.getElementById("original_email").value.trim();
      endpoint = `/edit_${tableType}`;
    } else if (tableType === "admin-members") {
      endpoint = "/add_admin";
    } else if (tableType === "union-members") {
      endpoint = "/add_union_members";
    } else {
      console.error("Unknown tableType:", tableType);
      return;
    }

    console.log("Submitting to:", endpoint);
    console.log("Payload:", payload);

    fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok || data.success === false) {
          const emailInput = document.getElementById("email");
          const error = document.createElement("div");
          error.className = "error-msg";
          error.style.color = "red";
          error.style.fontSize = "12px";
          error.style.marginTop = "2px";
          error.textContent = data.message || "An error occurred.";
          emailInput.insertAdjacentElement("afterend", error);
        } else {
          location.reload(true);
        }
      })
      .catch(err => console.error("Submit failed:", err));
  });


  function getModalFields(tableType, cells = []) {
    const originalEmail = cells[2]?.textContent.trim() || "";

    let html = `
      <h4 style="margin: 0;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 300;">First Name</h4>
      <input type="text" id="first_name" placeholder="First Name" value="${cells[0]?.textContent.trim() || ""}">
      <h4 style="margin: 0;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 300;">Last Name</h4>
      <input type="text" id="last_name" placeholder="Last Name" value="${cells[1]?.textContent.trim() || ""}">
      <h4 style="margin: 0;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 300;">Email</h4>
      <input type="text" id="email" placeholder="Email" value="${originalEmail}">
      <input type="hidden" id="original_email" value="${originalEmail}">
    `;

    if (tableType === "union-members") {
      html = `
        <h4 style="margin: 0;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 300;">First Name</h4>
        <input type="text" id="first_name" placeholder="First Name" value="${cells[4]?.textContent.trim() || ""}">
        <h4 style="margin: 0;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 300;">Last Name</h4>
        <input type="text" id="last_name" placeholder="Last Name" value="${cells[5]?.textContent.trim() || ""}">
        <h4 style="margin: 0;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 300;">Email</h4>
        <input type="text" id="email" placeholder="Email" value="${originalEmail}">
        <input type="hidden" id="original_email" value="${originalEmail}">
        <h4 style="margin: 0;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 300;">Union</h4>
        <input type="text" id="union" placeholder="Union" value="${cells[1]?.textContent.trim() || ""}">
      `;
    }
    return html;
  }
});