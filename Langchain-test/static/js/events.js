// Close the dropdown if the user clicks outside of it
window.onclick = function (event) {
    if (!event.target.matches(".user-icon, .user-icon *")) {
        const dropdown = document.getElementById("dropdown");
        if (dropdown.classList.contains("show")) {
            dropdown.classList.remove("show");
        }
    }
};