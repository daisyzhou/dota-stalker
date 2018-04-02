import queue

# Queue of (player, match)
matches_to_notify = queue.Queue(maxsize=200)
