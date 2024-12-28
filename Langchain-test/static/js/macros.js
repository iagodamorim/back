let macros = [];

function loadMacros(data) {
    macros = data;
    const macroList = document.getElementById("macro-list");
    if (!macroList) {
        return;
    }
    macroList.innerHTML = ""; // Clear existing macros

    macros.forEach((macro, index) => {
        const macroDiv = document.createElement("div");
        macroDiv.classList.add("macro-item");

        const macroName = document.createElement("input");
        macroName.type = "text";
        macroName.value = macro.name;
        macroName.classList.add("macro-name");
        macroName.oninput = e => (macros[index].name = e.target.value);

        const macroSnippet = document.createElement("textarea");
        macroSnippet.value = macro.snippet;
        macroSnippet.classList.add("macro-snippet");
        macroSnippet.oninput = e => (macros[index].snippet = e.target.value);

        const deleteBtn = document.createElement("button");
        deleteBtn.innerText = "Delete";
        deleteBtn.classList.add("delete-macro-btn");
        deleteBtn.onclick = () => deleteMacro(index);

        macroDiv.appendChild(macroName);
        macroDiv.appendChild(macroSnippet);
        macroDiv.appendChild(deleteBtn);
        macroList.appendChild(macroDiv);
    });
}

function addMacro() {
    macros.push({
        name: "New Macro",
        snippet: "",
    });
    loadMacros(macros);
}

function deleteMacro(index) {
    macros.splice(index, 1);
    loadMacros(macros);
}

function saveMacros() {
    const dataStr = JSON.stringify(macros, null, 2);

    // Sending data to Flask backend
    fetch("/save_macros", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: dataStr,
    })
        .then(response => response.json())
        .then(data => {
            showConfirmationMessage("Macros saved successfully!");
        })
        .catch(error => {
            console.error("Error:", error);
        });
}

function goToHome() {
    window.location.href = "/";
}

function showConfirmationMessage(message) {
    const messageElement = document.getElementById("confirmation-message");
    messageElement.textContent = message;
    messageElement.classList.add("show");

    // Hide the message after 3 seconds
    setTimeout(() => {
        messageElement.classList.remove("show");
    }, 3000);
}

// Load macros from a JSON file on page load
fetch("/static/data/macros.json")
    .then(response => response.json())
    .then(data => loadMacros(data))
    .catch(error => console.error("Error loading JSON:", error));