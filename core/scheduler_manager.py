import sys
import requests
import subprocess
import os
from datetime import datetime, timedelta

def start_bot_via_api():
    try:
        res = requests.post('http://127.0.0.1:5000/api/bot/start', timeout=10)
        print("Start API Response:", res.json())
    except Exception as e:
        print("Start API Failed:", e)

def stop_bot_via_api():
    try:
        res = requests.post('http://127.0.0.1:5000/api/bot/stop', timeout=10)
        print("Stop API Response:", res.json())
    except Exception as e:
        print("Stop API Failed:", e)

def update_tasks(sessions_ist, system_cfg):
    """
    Creates Windows scheduled tasks based on the earliest start time (-5 mins)
    and the latest end time.
    """
    # Remove existing tasks
    subprocess.run(['schtasks', '/delete', '/tn', 'TradingBot_Start', '/f'], capture_output=True)
    subprocess.run(['schtasks', '/delete', '/tn', 'TradingBot_Stop', '/f'], capture_output=True)
    
    auto_on = system_cfg.get('auto_on_enabled', False)
    auto_off = system_cfg.get('auto_off_enabled', False)
    
    if (not auto_on and not auto_off) or not sessions_ist:
        return
        
    starts = []
    ends = []
    for s in sessions_ist:
        try:
            starts.append(datetime.strptime(s['start'], "%H:%M"))
            ends.append(datetime.strptime(s['end'], "%H:%M"))
        except:
            pass
            
    if not starts: return
    
    earliest_start = min(starts)
    latest_end = max(ends)
    
    start_time = (earliest_start - timedelta(minutes=5)).strftime("%H:%M")
    end_time = latest_end.strftime("%H:%M")
    
    cwd = os.getcwd()
    python_exe = sys.executable
    script_path = os.path.join(cwd, "core", "scheduler_manager.py")
    
    if auto_on:
        # Create start task (runs daily)
        start_cmd = [
            'schtasks', '/create', '/tn', 'TradingBot_Start', '/tr', f'"{python_exe}" "{script_path}" start',
            '/sc', 'daily', '/st', start_time, '/f'
        ]
        res_start = subprocess.run(start_cmd, capture_output=True, text=True)
        # Force task to run on battery power
        subprocess.run(['powershell', '-Command', "Set-ScheduledTask -TaskName 'TradingBot_Start' -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0)"], capture_output=True)
        print("Scheduler Start:", res_start.stdout, res_start.stderr)
        
    if auto_off:
        # Create stop task (runs daily)
        stop_cmd = [
            'schtasks', '/create', '/tn', 'TradingBot_Stop', '/tr', f'"{python_exe}" "{script_path}" stop',
            '/sc', 'daily', '/st', end_time, '/f'
        ]
        res_stop = subprocess.run(stop_cmd, capture_output=True, text=True)
        # Force task to run on battery power
        subprocess.run(['powershell', '-Command', "Set-ScheduledTask -TaskName 'TradingBot_Stop' -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0)"], capture_output=True)
        print("Scheduler Stop:", res_stop.stdout, res_stop.stderr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            start_bot_via_api()
        elif sys.argv[1] == "stop":
            stop_bot_via_api()
