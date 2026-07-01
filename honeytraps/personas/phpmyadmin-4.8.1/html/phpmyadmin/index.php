<!DOCTYPE html>
<html>
<head>
<title>phpMyAdmin</title>
<meta charset="utf-8">
<meta name="generator" content="phpMyAdmin 4.8.1" />
</head>
<body>
<div id="login_form">
    <form method="post" action="index.php" name="login_form">
        <fieldset>
            <legend>Log in</legend>

            <div class="item">
                <label for="input_username">Username:</label>
                <input type="text" name="pma_username" id="input_username" value="" size="24" class="textfield" />
            </div>

            <div class="item">
                <label for="input_password">Password:</label>
                <input type="password" name="pma_password" id="input_password" value="" size="24" class="textfield" autocomplete="off" />
            </div>

            <!-- AllowArbitraryServer is enabled on this instance -->
            <div class="item">
                <label for="input_serverchoice">Server Choice:</label>
                <input type="text" name="pma_serverchoice" id="input_serverchoice" value="1" size="24" class="textfield" />
            </div>
        </fieldset>

        <input type="hidden" name="server" value="1" />
        <input type="hidden" name="target" value="index.php" />
        <input type="hidden" name="token" value="a1b2c3d4e5f6" />

        <input value="Go" type="submit" id="input_go" />
    </form>
</div>

<div id="footer_versions">
    <span class="version">
        phpMyAdmin 4.8.1
    </span>
</div>
</body>
</html>
