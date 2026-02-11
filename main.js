document.addEventListener('DOMContentLoaded', () => {
    const popup = document.getElementById('naver-map-popup');
    const closeButton = document.getElementById('close-popup');
    const POPUP_LAST_SHOWN_KEY = 'popupLastShownDate';

    // Function to set the current date in local storage
    const setLastShownDate = () => {
        const today = new Date().toDateString();
        localStorage.setItem(POPUP_LAST_SHOWN_KEY, today);
    };

    // Function to check if the popup was shown today
    const wasShownToday = () => {
        const lastShownDate = localStorage.getItem(POPUP_LAST_SHOWN_KEY);
        const today = new Date().toDateString();
        return lastShownDate === today;
    };

    if (popup && closeButton) {
        if (!wasShownToday()) {
            // Show the popup if it hasn't been shown today
            popup.classList.remove('hidden');
            popup.classList.add('show');
            document.body.style.overflow = 'hidden'; // Prevent scrolling when popup is open

            setLastShownDate(); // Mark as shown today
        } else {
            // Ensure popup is hidden if it was already shown today
            popup.classList.add('hidden');
        }

        // Close the popup when the close button is clicked
        closeButton.addEventListener('click', () => {
            popup.classList.remove('show');
            popup.classList.add('hidden');
            document.body.style.overflow = 'auto'; // Re-enable scrolling
        });

        // Close the popup when clicking outside the content
        popup.addEventListener('click', (event) => {
            if (event.target === popup) {
                popup.classList.remove('show');
                popup.classList.add('hidden');
                document.body.style.overflow = 'auto'; // Re-enable scrolling
            }
        });
    }
});