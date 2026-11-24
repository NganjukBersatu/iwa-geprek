BEHAVIOR = "behavior"
WORK = "work"

ON_TIME = "on_time"
ATTENDANCE = "attendance"
GIVEN_TASKS_DONE = "given_tasks_done"
GIVEN_TASKS_IN_TIME = "given_tasks_in_time"
OWN_TASKS_DONE = "own_tasks_done"
OWN_TASKS_IN_TIME = "own_tasks_in_time"

# Owner policy: relative weight of each group; a group without data is left out and the rest share the score.
WEIGHTS = {BEHAVIOR: 50, WORK: 50}

# Owner policy: attendance days (present, late, absent) needed before the attendance components count.
MIN_COUNTED_DAYS = 1

MAX_STARS = 5
STAR_STEP = 0.5
