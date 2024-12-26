document.addEventListener("DOMContentLoaded", function () {
    console.log("Script çalışıyor");

    const connectionTypeRadios = document.querySelectorAll("input[name='connection_type']");
    const sshForm = document.getElementById("ssh_form");
    const consoleForm = document.getElementById("console_form");


    function toggleForms() {
        const isConsoleSelected = Array.from(connectionTypeRadios).some(radio => radio.checked && radio.value === "Console");
        sshForm.style.display = isConsoleSelected ? "none" : "block";
        consoleForm.style.display = isConsoleSelected ? "block" : "none";
    }

    toggleForms();
    connectionTypeRadios.forEach(radio => {
        radio.addEventListener("change", toggleForms);
    });
});