document.addEventListener("DOMContentLoaded", () => {
    // Alternância de tema claro/escuro com base na preferência do usuário
    const themeSwitch = document.getElementById("themeSwitch");
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");

    // Configuração inicial do tema de acordo com a preferência do sistema
    if (prefersDarkScheme.matches) {
        document.body.classList.add("dark-mode");
        themeSwitch.checked = true;
    } else {
        document.body.classList.add("light-mode");
        themeSwitch.checked = false;
    }

    // Evento para alternar o tema quando o usuário interage com o switch
    themeSwitch.addEventListener("change", () => {
        document.body.classList.toggle("dark-mode", themeSwitch.checked);
        document.body.classList.toggle("light-mode", !themeSwitch.checked);
    });
});

function toggleDropdown() {
    const dropdown = document.getElementById("dropdown");
    dropdown.classList.toggle("show");
}

function redirectToMacros() {
    window.location.href = "/macros";
}

function redirectToEditor() {
    window.location.href = "/editor";
}

document.getElementById("menu-toggle").addEventListener("click", function () {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("open");
});

function loadContent(page) {
    const iframe = document.getElementById("contentFrame");
    iframe.src = page;
}
