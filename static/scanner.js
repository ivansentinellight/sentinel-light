document.addEventListener('DOMContentLoaded', function() {

    const form = document.getElementById('scanner-form');
    const resultsDiv = document.getElementById('scanner-results');
    const emailData = document.getElementById('emailData');
    const websiteData = document.getElementById('websiteData');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(form);

            resultsDiv.classList.remove('hidden');
            emailData.textContent = "Escaneando correo electrónico...";
            websiteData.textContent = "Escaneando sitio web...";

            try {
                const response = await fetch('/scanner', {
                    method: 'POST',
                    body: new URLSearchParams(formData)
                });

                const html = await response.text();

                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;

                const emailResultRaw = tempDiv.querySelector('#emailData')?.textContent || "No se encontró resultado de email.";
                const websiteResultRaw = tempDiv.querySelector('#websiteData')?.textContent || "No se encontró resultado de website.";

                emailData.textContent = emailResultRaw;
                websiteData.textContent = websiteResultRaw;

            } catch (error) {
                console.error("Error durante el escaneo:", error);
                emailData.textContent = "Error en escaneo de email.";
                websiteData.textContent = "Error en escaneo de website.";
            }
        });
    }
});
