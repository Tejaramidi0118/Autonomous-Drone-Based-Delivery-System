document.addEventListener("DOMContentLoaded", () => {
    const login = document.querySelector("#loginForm");
    const signup = document.querySelector("#signupForm");

    if (login) {
        login.addEventListener("submit", async event => {
            event.preventDefault();
            try {
                const data = await api("/auth/login", {
                    method: "POST",
                    body: JSON.stringify({
                        email: login.email.value,
                        password: login.password.value
                    })
                });
                saveSession(data);
                location.href = data.user.role === "admin" ? "/pages/admin_dashboard.html" : "/pages/customer_dashboard.html";
            } catch (error) {
                toast(error.message);
            }
        });
    }

    if (signup) {
        signup.addEventListener("submit", async event => {
            event.preventDefault();
            try {
                const data = await api("/auth/signup", {
                    method: "POST",
                    body: JSON.stringify({
                        name: signup.name.value,
                        email: signup.email.value,
                        password: signup.password.value,
                        role: signup.role.value
                    })
                });
                saveSession(data);
                location.href = data.user.role === "admin" ? "/pages/admin_dashboard.html" : "/pages/customer_dashboard.html";
            } catch (error) {
                toast(error.message);
            }
        });
    }
});
