import subprocess
import time
import sys

# Define the microservices to start
processes = [
    ("Auth Microservice", "run_auth.py"),
    ("Meals Microservice", "run_meals.py"),
    ("Analytics Microservice", "run_analytics.py"),
    ("Notifications Microservice", "run_notifications.py"),
    ("API Gateway", "api_gateway.py")
]

active_processes = []

try:
    print("====================================")
    print("STARTING MICROSERVICES CLUSTER")
    print("====================================")
    
    # Start each microservice using python interpreter
    for name, script in processes:
        print(f"Starting {name}...")
        p = subprocess.Popen([sys.executable, script])
        active_processes.append((name, p))
        time.sleep(1) # Small delay to avoid racing output logs
        
    print("====================================")
    print("All Microservices Running. (Press CTRL+C to stop all)")
    print("====================================")
    
    # Wait for the user to terminate the orchestrator
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down microservices cluster...")
    for name, p in active_processes:
        print(f"Terminating {name}...")
        p.terminate()
        p.wait()
    print("Shutdown complete.")
