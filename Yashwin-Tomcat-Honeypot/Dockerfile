# Use Tomcat 9.0.98, the exact version affected by CVE-2025-24813
FROM tomcat:9.0.98

# Add metadata labels for the honeypot orchestration
LABEL maintainer="Yashwin"
LABEL persona="apache-tomcat-9.0.98-cve-2025-24813"
LABEL description="Discrete Tomcat persona mimicking CVE-2025-24813 (Partial PUT RCE)"

# MAKE IT VULNERABLE (The Lure)
# CVE-2025-24813 requires the DefaultServlet to have 'readonly' set to false.
# We inject this misconfiguration to ensure automated scanners fall for the trap.
RUN sed -i '/<servlet-name>default<\/servlet-name>/a \        <init-param>\n            <param-name>readonly<\/param-name>\n            <param-value>false<\/param-value>\n        <\/init-param>' /usr/local/tomcat/conf/web.xml

# Expose the standard HTTP port
EXPOSE 8080

# Start the Tomcat server
CMD ["catalina.sh", "run"]