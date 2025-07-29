# 📁 Heimnetz Project Repository (Module 1–24 vollständig)

## 📦 File Structure

📄 `.htaccess`
📄 `admin.html`
📄 `admin_api.php`
📄 `api.php`
📄 `config.php`
📁 **css**
  📄 `styles.css`
📁 **dashboard**
  📄 `feed.json`
📁 **demo**
  📄 `devices.json`
📄 `index.html`
📁 **js**
  📄 `admin.js`
  📄 `app.js`
📁 **plugins**
  📄 `nextcloud_setup.ps1`
📁 **setup**
  📄 `setup.ps1`
📁 **sql**
  📄 `heimnetz.sql`
📁 **tools**
  📄 `healthcheck.ps1`
  📄 `heimnetz_gui.ps1`
  📄 `import.ps1`
  📄 `plugin_loader.ps1`
  📄 `qrcode.ps1`
  📄 `reset.ps1`
  📄 `ssl_installer.ps1`
  📄 `version_checker.ps1`

## 📝 File Contents

<details>
<summary>.htaccess</summary>

```htaccess
AuthType Basic
AuthName "Restricted Area"
AuthUserFile "C:/xampp/htdocs/heimnetz/.htpasswd"
Require valid-user
```
</details>

<details>
<summary>admin.html</summary>

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Panel - Heimnetz</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body class="theme-dark">
    <header>
        <h1>Admin Panel</h1>
        <nav>
            <a href="index.html">Dashboard</a>
        </nav>
    </header>
    <main>
        <section>
            <h2>Manage Devices</h2>
            <form id="addDeviceForm">
                <input type="text" name="hostname" placeholder="Hostname" required>
                <input type="text" name="ip_address" placeholder="IP Address" required>
                <input type="text" name="mac_address" placeholder="MAC Address" required>
                <button type="submit">Add Device</button>
            </form>
        </section>
    </main>
    <script src="js/admin.js"></script>
</body>
</html>
```
</details>

<details>
<summary>admin_api.php</summary>

```php
<?php
$mysqli = new mysqli("localhost", "root", "", "heimnetz");

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $hostname = $_POST['hostname'] ?? '';
    $ip = $_POST['ip_address'] ?? '';
    $mac = $_POST['mac_address'] ?? '';

    $stmt = $mysqli->prepare("INSERT INTO devices (hostname, ip_address, mac_address, status, last_seen) VALUES (?, ?, ?, 'offline', NOW())");
    $stmt->bind_param("sss", $hostname, $ip, $mac);
    $stmt->execute();

    echo json_encode(["status" => "Device added"]);
}
?>
```
</details>

<details>
<summary>api.php</summary>

```php
<?php
header('Content-Type: application/json');

$mysqli = new mysqli("localhost", "root", "", "heimnetz");

if ($mysqli->connect_error) {
    http_response_code(500);
    echo json_encode(["error" => "Database connection failed"]);
    exit;
}

$result = $mysqli->query("SELECT * FROM devices");
$devices = [];

while ($row = $result->fetch_assoc()) {
    $devices[] = $row;
}

echo json_encode($devices);
$mysqli->close();
?>
```
</details>

<details>
<summary>config.php</summary>

```php
<?php
define("DB_HOST", "localhost");
define("DB_USER", "root");
define("DB_PASS", "");
define("DB_NAME", "heimnetz");

$mysqli = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
if ($mysqli->connect_error) {
    die("Connection failed: " . $mysqli->connect_error);
}
?>
```
</details>

<details>
<summary>css/styles.css</summary>

```css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    background-color: #121212;
    color: #eee;
}
header, footer {
    background-color: #1e1e1e;
    padding: 1em;
    text-align: center;
}
nav a {
    color: #90caf9;
    margin: 0 1em;
}
.theme-light {
    background-color: #f5f5f5;
    color: #333;
}
```
</details>

<details>
<summary>dashboard/feed.json</summary>

```json
{
  "generated": "2025-07-13T13:00:00",
  "devices": [
    {
      "hostname": "Router",
      "status": "online",
      "last_seen": "2025-07-13T12:59:00"
    },
    {
      "hostname": "NAS",
      "status": "offline",
      "last_seen": "2025-07-12T22:45:00"
    }
  ]
}
```
</details>

<details>
<summary>demo/devices.json</summary>

```json
[
  {
    "hostname": "Router",
    "ip_address": "192.168.1.1",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "status": "online",
    "last_seen": "2025-07-13T10:00:00"
  },
  {
    "hostname": "NAS",
    "ip_address": "192.168.1.10",
    "mac_address": "11:22:33:44:55:66",
    "status": "offline",
    "last_seen": "2025-07-12T22:45:00"
  }
]
```
</details>

<details>
<summary>index.html</summary>

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Heimnetz Dashboard</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body class="theme-dark">
    <header>
        <h1>Heimnetz Dashboard</h1>
        <nav>
            <a href="admin.html">Admin Panel</a>
        </nav>
    </header>
    <main>
        <section id="device-list">
            <h2>Network Devices</h2>
            <div id="devices"></div>
        </section>
    </main>
    <footer>
        <p>&copy; 2025 Heimnetz</p>
    </footer>
    <script src="js/app.js"></script>
</body>
</html>
```
</details>

<details>
<summary>js/admin.js</summary>

```js
document.getElementById('addDeviceForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const response = await fetch('admin_api.php', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    alert(result.status);
    e.target.reset();
});
```
</details>

<details>
<summary>js/app.js</summary>

```js
fetch('api.php')
    .then(res => res.json())
    .then(devices => {
        const container = document.getElementById('devices');
        container.innerHTML = devices.map(d => \`
            <div class="device">
                <strong>\${d.hostname}</strong> — \${d.ip_address} — \${d.status}
            </div>\`
        ).join('');
    });
```
</details>

<details>
<summary>plugins/nextcloud_setup.ps1</summary>

```ps1
# nextcloud_setup.ps1 – Beispiel-Plugin zur automatisierten Nextcloud-Einrichtung
Write-Host "🔧 Starte Nextcloud-Setup..."

$zipUrl = 'https://download.nextcloud.com/server/releases/latest.zip'
$targetPath = 'C:/xampp/htdocs/nextcloud'

if (!(Test-Path $targetPath)) {
    Invoke-WebRequest -Uri $zipUrl -OutFile './nextcloud.zip'
    Expand-Archive './nextcloud.zip' -DestinationPath 'C:/xampp/htdocs'
    Remove-Item './nextcloud.zip'
    Write-Host "✅ Nextcloud wurde entpackt!"
} else {
    Write-Host "📁 Nextcloud-Verzeichnis existiert bereits."
}
```
</details>

<details>
<summary>setup/setup.ps1</summary>

```ps1
Write-Host "🔧 Running Heimnetz Setup..."

# Create database and tables in MariaDB
$connectionString = "server=localhost;uid=root;pwd=;database=heimnetz"
$query = @"
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(64),
    ip_address VARCHAR(45),
    mac_address VARCHAR(17),
    status VARCHAR(10),
    last_seen DATETIME
);
"@

$mysqlExe = "C:\xampp\mysql\bin\mysql.exe"
& $mysqlExe -e $query
Write-Host "✅ Database initialized."
```
</details>

<details>
<summary>sql/heimnetz.sql</summary>

```sql
-- heimnetz.sql – Vollständiger SQL-Dump
DROP DATABASE IF EXISTS heimnetz;
CREATE DATABASE heimnetz;
USE heimnetz;

CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(100),
    ip_address VARCHAR(45),
    mac_address VARCHAR(45),
    status VARCHAR(10) DEFAULT 'offline',
    last_seen DATETIME
);
```
</details>

<details>
<summary>tools/healthcheck.ps1</summary>

```ps1
# healthcheck.ps1 – Geräteverfügbarkeit prüfen
$mysqlPath = "C:\xampp\mysql\bin\mysql.exe"
$pingResults = @()

$devices = & $mysqlPath -u root -N -e "SELECT id, ip_address FROM devices;" heimnetz
foreach ($line in $devices) {
    $parts = $line -split "	"
    $id = $parts[0]
    $ip = $parts[1]

    $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue
    $status = if ($ping) { 'online' } else { 'offline' }
    $query = "UPDATE devices SET status='$status', last_seen=NOW() WHERE id=$id;"
    & $mysqlPath -u root -e "$query" heimnetz
    $pingResults += "$ip is $status"
}

$pingResults | ForEach-Object { Write-Host $_ }
```
</details>

<details>
<summary>tools/heimnetz_gui.ps1</summary>

```ps1
# heimnetz_gui.ps1 – Simples GUI-Frontend (WPF) für Windows
Add-Type -AssemblyName PresentationFramework

[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="Heimnetz Panel" Height="250" Width="400">
    <StackPanel Margin="10">
        <Label Content="Willkommen im Heimnetz!" FontSize="16" FontWeight="Bold" Margin="0,0,0,10"/>
        <Button Content="Healthcheck ausführen" Name="btnHealth" Margin="0,0,0,5"/>
        <Button Content="Geräte importieren" Name="btnImport"/>
    </StackPanel>
</Window>
"@

$reader = (New-Object System.Xml.XmlNodeReader $xaml)
$window = [Windows.Markup.XamlReader]::Load($reader)

$btnHealth = $window.FindName("btnHealth")
$btnHealth.Add_Click({ Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File ./tools/healthcheck.ps1" })

$btnImport = $window.FindName("btnImport")
$btnImport.Add_Click({ Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File ./tools/import.ps1" })

$window.ShowDialog()
```
</details>

<details>
<summary>tools/import.ps1</summary>

```ps1
# import.ps1 – Geräte aus devices.csv importieren
$csvPath = ".\devices.csv"
$mysqlPath = "C:\xampp\mysql\bin\mysql.exe"

if (!(Test-Path $csvPath)) {
    Write-Host "❌ Datei $csvPath nicht gefunden!" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Importiere Geräte aus $csvPath ..." -ForegroundColor Cyan
$csv = Import-Csv $csvPath
foreach ($entry in $csv) {
    $query = "INSERT INTO devices (hostname, ip_address, mac_address, status, last_seen) VALUES ('$($entry.hostname)', '$($entry.ip_address)', '$($entry.mac_address)', 'offline', NOW());"
    & $mysqlPath -u root -e "$query" heimnetz
}

Write-Host "✅ Import abgeschlossen!" -ForegroundColor Green
```
</details>

<details>
<summary>tools/plugin_loader.ps1</summary>

```ps1
# plugin_loader.ps1 – Lädt Plugins aus dem plugins/ Verzeichnis
$pluginPath = "./plugins"
if (!(Test-Path $pluginPath)) {
    Write-Host "📁 plugins/ Verzeichnis nicht gefunden, wird erstellt..."
    New-Item -ItemType Directory -Path $pluginPath
}

$plugins = Get-ChildItem $pluginPath -Filter "*.ps1"
foreach ($plugin in $plugins) {
    Write-Host "🔌 Lade Plugin: $($plugin.Name)"
    . "$($plugin.FullName)"
}
```
</details>

<details>
<summary>tools/qrcode.ps1</summary>

```ps1
# qrcode.ps1 – Erstellt QR-Codes für Geräte
$ErrorActionPreference = 'Stop'
Import-Module -Name 'QR-CodeGenerator' -ErrorAction SilentlyContinue

$devices = @(
    @{hostname='Router'; ip='192.168.1.1'; mac='AA:BB:CC:DD:EE:FF'},
    @{hostname='NAS'; ip='192.168.1.10'; mac='11:22:33:44:55:66'}
)

foreach ($device in $devices) {
    $data = "Hostname: $($device.hostname)`nIP: $($device.ip)`nMAC: $($device.mac)"
    $file = "$($device.hostname)_QR.png"
    New-QRCode -Content $data -FilePath "./$file" -QuietZone 2 -PixelsPerModule 6
    Write-Host "✅ QR-Code erstellt: $file"
}
```
</details>

<details>
<summary>tools/reset.ps1</summary>

```ps1
# reset.ps1 – Heimnetz-Projekt zurücksetzen
Write-Host "⚠️ Heimnetz-Datenbank wird zurückgesetzt..." -ForegroundColor Yellow

$mysqlPath = "C:\xampp\mysql\bin\mysql.exe"
$sqlReset = @"
DROP TABLE IF EXISTS devices;
CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(100),
    ip_address VARCHAR(45),
    mac_address VARCHAR(45),
    status VARCHAR(10) DEFAULT 'offline',
    last_seen DATETIME
);
"@

& $mysqlPath -u root -e "$sqlReset" heimnetz
Write-Host "✅ Datenbank wurde zurückgesetzt!" -ForegroundColor Green
```
</details>

<details>
<summary>tools/ssl_installer.ps1</summary>

```ps1
# ssl_installer.ps1 – Lokales SSL mit mkcert installieren
$ErrorActionPreference = 'Stop'
$mkcertUrl = "https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-windows-amd64.exe"
$mkcertExe = "C:\tools\mkcert.exe"

if (!(Test-Path $mkcertExe)) {
    Write-Host "⬇️ mkcert wird heruntergeladen..."
    Invoke-WebRequest -Uri $mkcertUrl -OutFile $mkcertExe
}

Write-Host "🔒 Zertifikatserstellung für localhost..."
& $mkcertExe -install
& $mkcertExe localhost 127.0.0.1 ::1

Move-Item ".\localhost+2.pem" "C:\xampp\apache\conf\ssl.crt\localhost.pem" -Force
Move-Item ".\localhost+2-key.pem" "C:\xampp\apache\conf\ssl.key\localhost.key" -Force

Write-Host "✅ SSL-Zertifikate wurden installiert!" -ForegroundColor Green
```
</details>

<details>
<summary>tools/version_checker.ps1</summary>

```ps1
# version_checker.ps1 – Prüft, ob eine neue Version vorliegt
$currentVersion = '1.0.0'
$versionFile = './version.json'

if (!(Test-Path $versionFile)) {
    Write-Host "⚠️ Version-Datei nicht gefunden, wird erstellt..."
    @{version = $currentVersion} | ConvertTo-Json | Out-File $versionFile -Encoding UTF8
}

$remote = Invoke-RestMethod -Uri 'https://example.com/heimnetz/version.json' -ErrorAction SilentlyContinue
if ($remote.version -ne $null -and $remote.version -ne $currentVersion) {
    Write-Host "⬆️ Neue Version verfügbar: $($remote.version) – Aktuell: $currentVersion"
} else {
    Write-Host "✅ Heimnetz ist aktuell: $currentVersion"
}
```
</details>

# 📁 Heimnetz Project Repository (Module 1–16 vollständig)

## 📦 File Structure (Module 13–16)

```
heimnetz/
├── admin/
│   ├── login.php
│   └── admin_panel.php
├── dashboard/
│   ├── css/
│   │   └── theme.css
│   ├── theme_toggle.js
│   └── ws_status.js
├── tools/
│   ├── ws_server.py
│   └── export_import.ps1
```

---

## 📝 File Contents

### `dashboard/css/theme.css`

```css
/* theme.css – Light/Dark Theme Support */
:root {
  --bg-color: #f9f9f9;
  --text-color: #222;
}
body.dark {
  --bg-color: #1e1e1e;
  --text-color: #ddd;
}
body {
  background-color: var(--bg-color);
  color: var(--text-color);
  transition: background-color 0.3s, color 0.3s;
}
```

---

### `dashboard/theme_toggle.js`

```js
// theme_toggle.js – Theme Toggle Button
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("themeToggle");
  toggle.addEventListener("click", () => {
    document.body.classList.toggle("dark");
    localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
  });

  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark");
  }
});
```

---

### `admin/login.php`

```php
<?php
session_start();
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $user = $_POST['username'] ?? '';
  $pass = $_POST['password'] ?? '';
  if ($user === 'admin' && $pass === 'geheim') {
    $_SESSION['loggedin'] = true;
    header('Location: admin_panel.php');
    exit;
  }
  $error = "Login fehlgeschlagen.";
}
?><!DOCTYPE html>
<html><head><title>Login</title></head>
<body>
  <form method="POST">
    <label>Benutzer: <input name="username"></label><br>
    <label>Passwort: <input name="password" type="password"></label><br>
    <button type="submit">Login</button>
    <?php if (!empty($error)) echo "<p style='color:red;'>$error</p>"; ?>
  </form>
</body></html>
```

---

### `admin/admin_panel.php`

```php
<?php
session_start();
if (!($_SESSION['loggedin'] ?? false)) {
  header('Location: admin/login.php');
  exit;
}
?><!DOCTYPE html>
<html><head><title>Admin</title></head>
<body><h1>Willkommen, Admin!</h1></body></html>
```

---

### `dashboard/ws_status.js`

```js
// ws_status.js – WebSocket-Verbindung zur Live-Statusanzeige
const socket = new WebSocket('ws://localhost:8765');
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Beispiel: Online-Status von Geräten aktualisieren
  console.log('Live-Update:', data);
};
```

---

### `tools/ws_server.py`

```python
# ws_server.py – Simple WebSocket-Server in Python
import asyncio, websockets, json

async def notify(websocket, path):
    while True:
        data = json.dumps({
            "hostname": "Router",
            "status": "online",
            "time": "2025-07-13T13:45:00"
        })
        await websocket.send(data)
        await asyncio.sleep(5)

start_server = websockets.serve(notify, "0.0.0.0", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
```

---

### `tools/export_import.ps1`

```powershell
# export_import.ps1 – Export/Import ganzer Gerätesätze
param([string]$mode = "export")

if ($mode -eq "export") {
  Copy-Item "../db/devices.sqlite" "./backup/devices_backup_$(Get-Date -Format yyyyMMdd_HHmm).sqlite"
  Write-Host "✅ Geräte-Datenbank exportiert."
}
elseif ($mode -eq "import") {
  $latest = Get-ChildItem ./backup -Filter *.sqlite | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  Copy-Item $latest.FullName "../db/devices.sqlite" -Force
  Write-Host "📥 Letzter Export importiert: $($latest.Name)"
}

# 📦 Heimnetz – Module 17–20

## 📁 File Structure (Module 17–20)

```
heimnetz/
├── backup/
│   ├── backup.sh
│   └── restore.sh
├── dashboard/
│   └── qr/
│       ├── qrcode.js
│       └── view.html
├── users/
│   ├── users.json
│   ├── login.php
│   └── auth.php
├── plugins/
│   ├── catalog.json
│   └── install.php
```

---

## 📝 File Contents

### `backup/backup.sh`

```bash
#!/bin/bash
# Backup-Script für Heimnetz (Modul 17)

DATE=$(date +"%Y%m%d_%H%M")
BACKUP_NAME="heimnetz_backup_$DATE.zip"

zip -r "./$BACKUP_NAME" ../dashboard ../db ../admin ../config
echo "✅ Backup erstellt: $BACKUP_NAME"
```

---

### `backup/restore.sh`

```bash
#!/bin/bash
# Restore-Script für Heimnetz (Modul 17)

LATEST=$(ls -t heimnetz_backup_*.zip | head -n 1)

if [ -z "$LATEST" ]; then
  echo "⚠️ Kein Backup gefunden."
else
  unzip "$LATEST" -d ../
  echo "📦 Wiederhergestellt: $LATEST"
fi
```

---

### `dashboard/qr/qrcode.js`

```html
<!-- Modul 18: QR-Code-Ansicht mit Smartphone-Scan -->

<!DOCTYPE html>
<html>
<head>
  <title>Gerätezugang – QR</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/qrious/4.0.2/qrious.min.js"></script>
</head>
<body>
  <h2>📱 QR-Code zum Heimnetz-Dashboard</h2>
  <canvas id="qr"></canvas>

  <script>
    const qr = new QRious({
      element: document.getElementById('qr'),
      value: 'http://10.0.1.100/dashboard/index.html',
      size: 250
    });
  </script>
</body>
</html>
```

---

### `users/users.json`

```json
[
  {
    "username": "admin",
    "password": "admin123",
    "role": "admin"
  },
  {
    "username": "gast",
    "password": "gast123",
    "role": "viewer"
  }
]
```

---

### `users/login.php`

```php
<?php
session_start();
$users = json_decode(file_get_contents("users.json"), true);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  foreach ($users as $user) {
    if ($_POST['username'] === $user['username'] && $_POST['password'] === $user['password']) {
      $_SESSION['user'] = $user;
      header("Location: ../dashboard/index.html");
      exit;
    }
  }
  $error = "Login fehlgeschlagen.";
}
?><!DOCTYPE html>
<html><body>
<form method="post">
  <input name="username" placeholder="Benutzer">
  <input type="password" name="password" placeholder="Passwort">
  <button type="submit">Login</button>
  <?= isset($error) ? "<p style='color:red;'>$error</p>" : "" ?>
</form>
</body></html>
```

---

### `users/auth.php`

```php
<?php
session_start();
if (!isset($_SESSION['user'])) {
  header("Location: login.php");
  exit;
}
```

---

### `plugins/catalog.json`

```json
[
  {
    "name": "Nextcloud Setup",
    "description": "Installiert und konfiguriert Nextcloud",
    "url": "https://yourserver.local/plugins/nextcloud.zip"
  },
  {
    "name": "Pi-hole Integration",
    "description": "Bindet Pi-hole ins Dashboard ein",
    "url": "https://yourserver.local/plugins/pihole.zip"
  }
]
```

---

### `plugins/install.php`

```php
<?php
$catalog = json_decode(file_get_contents("catalog.json"), true);

foreach ($catalog as $plugin) {
  echo "<div>";
  echo "<h3>{$plugin['name']}</h3>";
  echo "<p>{$plugin['description']}</p>";
  echo "<a href='{$plugin['url']}'>🔽 Download Plugin</a>";
  echo "</div><hr>";
}
```

---

## ✅ Zusammenfassung Module 17–20

| Modul | Funktion                                      | Technologie            |
| ----- | --------------------------------------------- | ---------------------- |
| 17    | Backup & Restore über Shellskripte            | `bash`, `zip`, `unzip` |
| 18    | QR-Code für mobile Geräteansicht              | HTML5, `qrious.js`     |
| 19    | Mehrbenutzersystem mit JSON-Auth              | PHP, JSON, Sessions    |
| 20    | Plugin-Marktplatz mit Installationsverlinkung | PHP, JSON              |


# 📦 Heimnetz – Module 21–24

## 📁 File Structure (Module 21–24)

```
heimnetz/
├── notify/
│   └── mailer.php
├── dashboard/
│   └── icons/
│       ├── tv.png
│       ├── nas.png
│       └── iot.png
├── dashboard/
│   └── performance/
│       └── metrics.js
├── updater/
│   ├── version.json
│   └── selfupdate.php
```

---

## 📝 File Contents

### `notify/mailer.php` (Modul 21: E-Mail-Benachrichtigungen)

```php
<?php
// Heimnetz Mailer – sendet bei Fehlern oder Logins eine E-Mail

function sendNotification($subject, $message) {
    $to = "admin@heimnetz.local";
    $headers = "From: notifier@heimnetz.local\r\n";
    mail($to, $subject, $message, $headers);
}

// Beispiel: Loginbenachrichtigung
if ($_GET['event'] === 'login') {
    $user = $_GET['user'] ?? 'Unbekannt';
    sendNotification("🔐 Login erkannt", "Benutzer '$user' hat sich angemeldet.");
}
?>
```

---

### `dashboard/icons/` (Modul 22: Geräte-Icons & Kategorien)

* Beispielbilder – in deinem echten Projekt kommen hier PNG-Dateien rein:

  * `tv.png` → Icon für Smart TVs
  * `nas.png` → Icon für NAS-Geräte
  * `iot.png` → Icon für IoT/Smart Devices

```html
<!-- Beispielhafte Verwendung im Dashboard -->
<img src="icons/tv.png" alt="Smart TV" width="32">
<span>Samsung SmartTV</span>
```

---

### `dashboard/performance/metrics.js` (Modul 23: Performance-Monitoring)

```javascript
// Modul 23: Performance-Metriken anzeigen

window.addEventListener("load", () => {
    const t0 = performance.timing.navigationStart;
    const t1 = performance.timing.domContentLoadedEventEnd;
    const loadTime = (t1 - t0) / 1000;

    document.getElementById("perf-stats").innerText =
        `⚡ Ladezeit: ${loadTime.toFixed(2)}s`;
});
```

🔧 In der `index.html` musst du nur ein `<div id="perf-stats"></div>` einbauen.

---

### `updater/version.json` (Modul 24: Versionierung)

```json
{
  "version": "1.0.5",
  "date": "2025-07-13",
  "changelog": [
    "Modul 21: E-Mail-Benachrichtigungen",
    "Modul 22: Gerätekategorien mit Icons",
    "Modul 23: Performance-Monitor",
    "Modul 24: Auto-Updater Framework"
  ]
}
```

---

### `updater/selfupdate.php` (Modul 24: Auto-Updater)

```php
<?php
$current = json_decode(file_get_contents("version.json"), true);
$latest = json_decode(file_get_contents("https://yourdomain.com/heimnetz/version.json"), true);

if (version_compare($latest['version'], $current['version'], '>')) {
    echo "<h3>🚀 Neue Version verfügbar: " . $latest['version'] . "</h3>";
    echo "<p>Changelog:</p><ul>";
    foreach ($latest['changelog'] as $change) {
        echo "<li>$change</li>";
    }
    echo "</ul><a href='https://yourdomain.com/heimnetz/update.zip'>🔽 Jetzt aktualisieren</a>";
} else {
    echo "✅ Heimnetz ist aktuell.";
}
?>
```

---

## ✅ Zusammenfassung Module 21–24

| Modul | Funktion                         | Technologie             |
| ----- | -------------------------------- | ----------------------- |
| 21    | E-Mail-Alerting bei Events       | PHP `mail()`            |
| 22    | Gerätekategorien & Icons         | HTML/CSS + Bilder       |
| 23    | Performance-Messung im Dashboard | JS `performance.timing` |
| 24    | Versionierung & Updateprüfung    | PHP + JSON              |

---

## 📦 Statusbericht: Heimnetz Dashboard

Du hast jetzt ein Dashboard mit:

* Authentifizierung & Mehrbenutzerlogik ✅
* Backup & Restore ✅
* Mobile QR-Zugriff ✅
* Plugin-System ✅
* Monitoring & Performance-Metrik ✅
* Automatischer Updater mit Changelog ✅

---

## 🔜 Bereit für Module 25–28?

Hier ein Ausblick für die Zukunft:

* **25:** WebSocket-Benachrichtigungen (live Events)
* **26:** Offline-Funktionalität mit Service Worker
* **27:** Export/Import ganzer Gerätekonfiguration
* **28:** Dark Mode Switcher mit persistenter Einstellung
