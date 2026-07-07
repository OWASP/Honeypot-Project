<!DOCTYPE html>
<html>
<head>
<meta name="generator" content="WordPress 5.0.3" />
<title>Log In &lsaquo; Honeypot Site &mdash; WordPress</title>
<link rel="stylesheet" href="/wp-includes/css/buttons.min.css" type="text/css" />
</head>
<body class="login login-action-login wp-core-ui">
<div id="login">
    <h1><a href="https://wordpress.org/">WordPress</a></h1>
    <form name="loginform" id="loginform" action="/wp-login.php" method="post">
        <p>
            <label for="user_login">Username or Email Address</label>
            <input type="text" name="log" id="user_login" class="input" value="" size="20" autocapitalize="off" />
        </p>
        <p>
            <label for="user_pass">Password</label>
            <input type="password" name="pwd" id="user_pass" class="input" value="" size="20" />
        </p>
        <p class="forgetmenot"><input name="rememberme" type="checkbox" id="rememberme" value="forever" /> <label for="rememberme">Remember Me</label></p>
        <p class="submit">
            <input type="submit" name="wp-submit" id="wp-submit" class="button button-primary button-large" value="Log In" />
            <input type="hidden" name="redirect_to" value="/wp-admin/" />
            <input type="hidden" name="testcookie" value="1" />
        </p>
    </form>
    <p id="nav">
        <a href="/wp-login.php?action=lostpassword">Lost your password?</a>
    </p>
</div>
</body>
</html>
