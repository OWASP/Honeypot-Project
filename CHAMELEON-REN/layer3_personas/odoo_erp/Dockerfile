# Odoo ERP Container
FROM odoo:17.0

# Switch to root to modify filesystem permissions and patch the core
USER root

# Prep directories for auth_oauth and mail modules to capture specific probes
RUN mkdir -p /mnt/extra-addons/auth_oauth \
    && mkdir -p /mnt/extra-addons/mail \
    && chown -R odoo:odoo /mnt/extra-addons

# ==========================================
# Server Spoofing Fix (Nginx/1.24.0)
# ==========================================
# Surgically patch Werkzeug to broadcast Nginx headers instead of Python/Werkzeug
RUN find /usr/ -type f -name "serving.py" -path "*/werkzeug/*" -exec sed -i 's/Werkzeug\//Nginx\/1.24.0/g' {} + \
    && find /usr/ -type f -name "serving.py" -path "*/werkzeug/*" -exec sed -i 's/Python\// /g' {} +

# Switch back to the safe odoo user
USER odoo
