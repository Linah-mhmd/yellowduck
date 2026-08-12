// Toggle dropdown visibility with smooth animation
function toggleDropdown() {
    const menu = document.getElementById("dropdownMenu");

    // Hide all other dropdowns if multiple exist
    document.querySelectorAll('.dropdown-menu').forEach(el => {
        if (el !== menu) {
            el.style.opacity = 0;
            setTimeout(() => el.style.display = 'none', 200);
        }
    });

    // Toggle current dropdown
    if (menu.style.display === "block") {
        menu.style.opacity = 0;
        setTimeout(() => {
            menu.style.display = "none";
        }, 200);
    } else {
        menu.style.display = "block";
        setTimeout(() => {
            menu.style.opacity = 1;
        }, 10);
    }
}

// Close dropdown if clicked outside
window.addEventListener('click', function (e) {
    const dropdown = document.querySelector('.account-dropdown');
    const menu = document.getElementById("dropdownMenu");

    if (dropdown && !dropdown.contains(e.target)) {
        if (menu && menu.style.display === 'block') {
            menu.style.opacity = 0;
            setTimeout(() => menu.style.display = "none", 200);
        }
    }
});

//  Close dropdown via close button
function closeDropdown() {
    const menu = document.getElementById("dropdownMenu");
    if (menu) {
        menu.style.opacity = 0;
        setTimeout(() => {
            menu.style.display = "none";
        }, 200);
    }
}
/// Dashboard
 function toggleDashboardMenu(event) {
    event.preventDefault();
    const menu = document.getElementById('dashboardMenu');
    menu.classList.toggle('show');
}

document.addEventListener('click', function (e) {
    const dropdown = document.querySelector('.dashboard-dropdown');
    if (!dropdown.contains(e.target)) {
        document.getElementById('dashboardMenu').classList.remove('show');
    }
});