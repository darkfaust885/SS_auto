async function auth(username, password) {
    const model = {
        "name": username,
        "password": password
    }
    const request = new Request('/api/auth', { method: 'POST', body: JSON.stringify(model) });
    return fetch(request)
        .then(response => {
            if (response.status === 200) {
                return response.json()
            } else {
                return undefined
            }
        })
}

function set_cookie(name, value) {
    let date = new Date(Date.now() + 86400e3);
    date = date.toUTCString();
    document.cookie = name + '=' + value + "; expires=" + date;
}

function delete_cookie(name) {
    document.cookie = name + '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

function is_auth() {
    return document.cookie.includes("token")
}

function get_cookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function get_token() {
    return get_cookie('token')
}

function logout() {
    delete_cookie('token')
    window.location.reload()
}

async function test_check_auth(name) {
    const request = new Request('/hello-auth/' + name, { headers: { 'Authorization': 'Bearer ' + get_token() } });
    return fetch(request)
        .then(response => {
            if (response.status === 200) {
                return response.json()
            } else {
                return undefined
            }
        })
}

function is_auth_visible(id) {
    if (is_auth()) {
        document.getElementById(id).style.display = 'block';
    } else {
        document.getElementById(id).style.display = 'none';
    }
}

function is_non_auth_visible(id) {
    if (is_auth()) {
        document.getElementById(id).style.display = 'none';
    } else {
        document.getElementById(id).style.display = 'block';
    }
}