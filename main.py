import subprocess

# Run stoch.py in a separate process
subprocess.Popen(['python', 'stoch.py'])

# Run ema.py in a separate process
subprocess.Popen(['python', 'ema.py'])