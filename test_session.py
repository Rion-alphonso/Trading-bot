from datetime import datetime, timedelta
import pytz

ist_tz = pytz.timezone('Asia/Kolkata')

def _is_active_session(utc_time):
    if hasattr(utc_time, 'tzinfo') and utc_time.tzinfo is not None:
        naive_time = utc_time.replace(tzinfo=None)
    else:
        naive_time = utc_time
    ist_time = naive_time.replace(tzinfo=pytz.utc).astimezone(ist_tz).time()
    
    if datetime.strptime("10:00", "%H:%M").time() <= ist_time <= datetime.strptime("17:30", "%H:%M").time():
        return True
    if datetime.strptime("20:00", "%H:%M").time() <= ist_time <= datetime.strptime("22:30", "%H:%M").time():
        return True
    return False

base_time = datetime(2025, 5, 30, 0, 0, 0) # Start at midnight UTC
print("UTC Time -> IST Time : isActive")
for i in range(24):
    test_time = base_time + timedelta(hours=i)
    ist_time = test_time.replace(tzinfo=pytz.utc).astimezone(ist_tz).time()
    print(f"{test_time.time()} UTC -> {ist_time} IST : {_is_active_session(test_time)}")
