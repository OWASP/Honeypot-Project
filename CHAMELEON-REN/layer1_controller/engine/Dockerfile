FROM python:3.11-slim

WORKDIR /app

# Install the required Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our routing script into the container
COPY stimulus_engine.py .

EXPOSE 5000

# Start the Stimulus Engine
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "stimulus_engine:app"]