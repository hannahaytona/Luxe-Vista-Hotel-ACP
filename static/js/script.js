// Close modals when clicking outside
window.onclick = function(event) {
    let modals = document.getElementsByClassName('modal');
    for (let i = 0; i < modals.length; i++) {
        if (event.target == modals[i]) {
            modals[i].classList.remove('active');
        }
    }
}

// Fade out flash messages after 5 seconds
document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        let flashMessages = document.querySelector('.flash-messages');
        if (flashMessages) {
            flashMessages.style.opacity = '0';
            setTimeout(function() {
                flashMessages.style.display = 'none';
            }, 500);
        }
    }, 5000);
});
