from datetime import datetime

now = datetime.now()
current_day = now.weekday()  # Monday=0, ..., Friday=4
current_time = now.time()

# Python weekday() mapping:
# Monday    = 0
# Tuesday   = 1
# Wednesday = 2
# Thursday  = 3
# Friday    = 4
# Saturday  = 5
# Sunday    = 6


if current_day == 4 or (current_day == 0 and current_time < datetime.strptime("14:00", "%H:%M").time()):
    print("Condition met.") # latest first expiry
else:
    print("Condition not met.") # sencond expiry
