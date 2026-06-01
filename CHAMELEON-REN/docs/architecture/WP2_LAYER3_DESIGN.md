# Work Package 2: Layer 3 Persona Architecture & State Persistence

## 1. The Persona Seeding Process
To create highly realistic honeypot personas that mimic live university infrastructure, a temporary manual seeding process was utilized during development. 
* Port bindings (e.g., `8081:80`) were temporarily exposed to the local host.
* The native web installers for WordPress, Moodle, Odoo, and Gibbon were accessed manually.
* Fictitious administrative accounts, student records, and university portal data were populated to generate organic database structures.
* Once the organic state was achieved, the databases were dumped, and the temporary port bindings were permanently removed to force all traffic through the Layer 1 Nginx WAF.

## 2. The Stateless Trap (State Persistence)
Honeypots are inherently vulnerable to ransomware and data corruption. To counter this, CHAMELEON-REN implements a "Stateless Trap" architecture:
* All database personas are ephemeral.
* The seeded organic state was exported to `.sql` dump files (e.g., `gibbon_init.sql`).
* These files are mapped directly into the MariaDB/PostgreSQL `docker-entrypoint-initdb.d/` directories.
* **Self-Restoration:** If an attacker drops all tables or encrypts the database, the Docker container simply needs to be restarted. Upon boot, the database engine automatically reads the `.sql` dumps and restores the honeypot to its exact pristine state in seconds.
* Configuration amnesia (e.g., Gibbon's `config.php`) was solved by securely extracting the generated configuration file via `docker cp` and hard-mounting it as a read-only (`:ro`) volume in the `docker-compose.yml`.

## 3. Security Constraints & Isolation
Per the project's strict security requirements, the Layer 3 personas must never be utilized as pivot points to attack external networks.
* **Network Isolation:** All personas reside strictly on the `chameleon_internal` Docker bridge network. They have no outbound internet access and cannot resolve external DNS.
* **Resource Quotas:** To prevent Denial of Service (DoS) conditions from exhausting the host's resources, strict hardware limits were enforced via Docker Compose `deploy` constraints. Each persona is strictly limited to `0.50` CPUs and `512M` of memory.

## 4. Dependency Troubleshooting & Compilation
Several target applications required custom Dockerfiles to compile properly in an isolated environment, most notably the Gibbon SIS:
* The base `php:8.2-apache` image lacked required extensions for educational software.
* Custom build steps were engineered to install `libicu-dev`, `libzip-dev`, and `gettext`.
* PHP extensions `intl`, `pdo_mysql`, and `zip` were manually configured and enabled.
* Composer was injected into the build pipeline to handle specific vendor dependencies before runtime.