FROM python:3.11-slim

WORKDIR /app

# INSTALL THE CLOUD WEAPONS: curl and awscli
RUN apt-get update && apt-get install -y curl awscli && rm -rf /var/lib/apt/lists/*

# Install the required library directly
RUN pip install requests

COPY shodan_evasion.py .

# The -u flag prevents silent logs!
CMD ["python", "-u", "shodan_evasion.py"]