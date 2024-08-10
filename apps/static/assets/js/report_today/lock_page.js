function handleSubmit(event) {
    event.preventDefault();
    const form = event.target;
    showOverlay();
    form.submit();
}

function showOverlay() {
    const overlay = document.getElementById("overlay");
    overlay.classList.remove("d-none");
    console.log("Overlay should be visible now."); // Agrega este log para verificar
}

document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("search-form");
    form.addEventListener("submit", handleSubmit);

    // Verifica que noResultsMessage esté definido antes de usarlo
    const noResultsMessage = document.getElementById('no-results-message');
    if (noResultsMessage) {
        noResultsMessage.style.display = 'none';
        console.log("No results message hidden."); // Agrega este log para verificar
    } else {
        console.log("No results message element not found."); // Agrega este log para verificar
    }
    console.log("Event listeners have been set up."); // Agrega este log para verificar
});
