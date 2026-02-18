let sortAscending = true;

// Function for filtering by date
function sortTableByDate() {
  const table = document.getElementById("fileTable");
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const arrow = document.getElementById("sortArrow");

  rows.sort((a, b) => {
    const dateA = new Date(a.children[3].textContent.trim());
    const dateB = new Date(b.children[3].textContent.trim());
    return sortAscending ? dateA - dateB : dateB - dateA;
  });

  rows.forEach(row => tbody.appendChild(row));
  sortAscending = !sortAscending;

  arrow.textContent = sortAscending ? "▲" : "▼";
}


// Functions for filtering by typing
function filterFilename() {
  let input = document.getElementById("searchInput").value.toLowerCase();
  let rows = document.querySelectorAll("#fileTable tbody tr");

  rows.forEach(row => {
    let filename = row.children[1].textContent.toLowerCase(); 
    row.style.display = filename.includes(input) ? "" : "none"; 
  });
  currentPage = 1;
}

function filterEmail() {
  let input = document.getElementById("searchEmail").value.toLowerCase();
  let rows = document.querySelectorAll("#fileTable tbody tr");

  rows.forEach(row => {
    let email = row.children[2].textContent.toLowerCase(); 
    row.style.display = email.includes(input) ? "" : "none"; 
  });
  currentPage = 1;
}

const rowsPerPage = 10;
let currentPage = 1;


// Paginiateing ggggggg
function paginateTable() {
    const rows = document.querySelectorAll("#fileTable tbody tr");
    const totalRows = rows.length;
    const totalPages = Math.ceil(totalRows / rowsPerPage);

    rows.forEach((row, index) => {
        row.style.display = (
            index >= (currentPage - 1) * rowsPerPage && index < currentPage * rowsPerPage
        ) ? "" : "none";
    });

    const pagination = document.getElementById("pagination");
    pagination.innerHTML = "";

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement("button");
        btn.textContent = i;
        btn.className = (i === currentPage) ? "active" : "";
        btn.onclick = function () {
            currentPage = i;
            paginateTable();
        };
        pagination.appendChild(btn);
    }
}
window.onload = paginateTable;


// Modal actions for viewing/downloading files
document.querySelectorAll('.dropdown-toggle').forEach(button => {
    button.addEventListener('click', () => {
        const dropdown = button.nextElementSibling;
        dropdown.style.display = 'flex';
    });
});

window.addEventListener('click', (e) => {
    document.querySelectorAll('.dropdown-menu').forEach(menu =>{
        if (!menu.parentElement.contains(e.target)) {
            menu.style.display = 'none';
        }
    });
});

document.getElementById('modalLeave').addEventListener("click", () => {
    document.getElementById('modalDownload').style.display = 'none';
});
document.getElementById('cancelModal').addEventListener("click", () => {
    document.getElementById('modalPreview').style.display = 'none';
});
function openModal(action, fileId = null) {
    if (action === 'download') {
        currentFileId = fileId
        document.getElementById('modalDownload').style.display = 'flex';
    } else {
        document.getElementById('modalPreview').style.display = 'flex';
        document.getElementById('previewTable').innerHTML = `<p style="display: flex;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 500;";>Loading Preview...</p>`;
        fetch(`/preview/${fileId}`)
            .then(res => res.text())
            .then(html => {document.getElementById('previewTable').innerHTML = html})
            .catch(err => {
                document.getElementById('previewTable').innerHTML = `<p style="display: flex;font-family: 'Inter', 'Segoe UI', sans-serif;font-weight: 500;color:red";>Failed to load preview</p>`
                console.error(err)
            })
    }
}
let currentFileId = null; 
document.getElementById('submitRow').addEventListener("click", () => {
    if (currentFileId !== null) {
        window.location.href = `/download/${currentFileId}`;
        document.getElementById('modalDownload').style.display = 'none';
    }
});


// Modal actions for changing status
function renderBattery(batt) {
    const stage = parseInt(batt.dataset.stage);
    batt.innerHTML = '';

    for (let i = 0; i < 3; i++) {
        const section = document.createElement('div');
        if (i <= stage) section.classList.add(`stage-${i}`);
        batt.appendChild(section);
    }
}
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.battery').forEach(renderBattery);
});

document.getElementById('modalCancel').addEventListener("click", () => {
    document.getElementById('modalStatus').style.display = 'none';
});

function openStatusModal(id, currentStage) {
    const modal = document.getElementById('modalStatus');
    modal.style.display = 'flex';

    document.getElementById('stageSelector').value = currentStage;
    modal.dataset.processId = id;
}

function submitStageChange() {
    const modal = document.getElementById('modalStatus');
    const id = modal.dataset.processId;
    const stage = document.getElementById('stageSelector').value;

    fetch(`/update-stage/${id}`, {
        method: 'POST',
        body: JSON.stringify({ stage }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const battery = document.querySelector(`.battery[data-id='${id}']`);
            battery.dataset.stage = data.status;
            renderBattery(battery);
        }
        modal.style.display = 'none';
    });
}