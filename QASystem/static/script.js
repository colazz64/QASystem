document.addEventListener("DOMContentLoaded", () => {
    const uploadButton = document.getElementById("uploadButton");
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".pdf,.doc,.docx,.txt";

    // Trigger file input when the upload button is clicked
    uploadButton?.addEventListener("click", () => {
        console.log("Upload button clicked."); // Debugging log
        fileInput.click();
    });

    // Handle file selection and upload
    fileInput.addEventListener("change", () => {
        console.log("File selected."); // Debugging log
        const file = fileInput.files[0];
        if (!file) {
            console.error("No file selected."); // Debugging log
            alert("No file selected.");
            return;
        }

        const loadingSpinner = document.getElementById("loadingSpinner");
        loadingSpinner.style.display = "block";

        const formData = new FormData();
        formData.append("document", file);

        console.log("Sending POST request to /upload."); // Debugging log

        fetch("/upload", {
            method: "POST",
            body: formData,
        })
            .then((response) => {
                console.log("Server response received."); // Debugging log
                if (!response.ok) {
                    throw new Error("Upload failed. Please try again.");
                }
                return response.json();
            })
            .then((data) => {
                loadingSpinner.style.display = "none";
                console.log("Upload successful, response:", data); // Debugging log
                if (data.error) {
                    alert(data.error);
                    return;
                }

                // Redirect to the afterupload page
                const queryParams = new URLSearchParams({
                    pdf_url: data.pdf_url,
                    summary: data.summary,
                    questions: data.suggested_questions.join("|"),
                });
                window.location.href = `/afterupload?${queryParams.toString()}`;
            })
            .catch((error) => {
                loadingSpinner.style.display = "none";
                console.error("Upload Error:", error); // Debugging log
                alert("An error occurred. Please try again.");
            });
    });
});
