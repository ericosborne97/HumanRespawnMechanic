'''
Lets create a relatively simple simulation

We will create three threads. Alpha, Bravo and Charlie.

All will be born at the same time.

From the moment they are born they will start a timer to record how long
they have been alive.
They will also store a string which represents their name.

Alpha will live for 5 periods, Bravo for 10, and Charlie will live forever.

Every time a thread dies the program creates a new randomly named thread
which will live and die.

Alpha and Bravo die relatively quickly as their life is short.

Afterwards a number of threads are born and die, only Charlie is immortal.

After a very long time "Alpha" or "Bravo" will respawn.

To them no time has passed since they "died".

But for the immortal Charlie many periods have passed.

Ctrl-C ends the world.
'''
import itertools
import random
import threading
import time

# --- the physics of this little universe -------------------------------------

PERIOD = 0.5                # seconds in one "period"
IMMORTAL = float('inf')     # a lifespan Charlie alone is given
RESPAWN_CHANCE = 0.15       # odds that a newborn is a returning old name
AGE_OF_RETURN = 20          # periods that must pass before the old names return
LIFESPANS = {"Alpha": 5, "Bravo": 10, "Charlie": IMMORTAL}

WORLD_BORN = time.monotonic()
_ids = itertools.count(4000)      # ID numbers for everyone born after the first three
_stop = threading.Event()         # set on Ctrl-C: the end of the world
_lock = threading.Lock()          # keeps the printing (and the tally) honest
_deaths = 0


def world_age():
    """How many periods the universe has existed."""
    return (time.monotonic() - WORLD_BORN) / PERIOD


def announce(message):
    with _lock:
        print(f"[period {world_age():7.1f}]  {message}")


NAME_PARTS = (
    ("Del", "Fox", "Kil", "Nov", "Qua", "Rho", "Sig", "Tan", "Ves", "Wren", "Yar", "Zed"),
    ("ta", "mo", "ri", "ka", "vex", "lun", "dar", "sel", "pha", "nix"),
)


def random_name():
    return random.choice(NAME_PARTS[0]) + random.choice(NAME_PARTS[1])


# --- Create three threads (Alpha, Bravo, Charlie) ----------------------------

class thread(threading.Thread):
    def __init__(self, thread_name, thread_ID, lifespan):
        threading.Thread.__init__(self, daemon=True)
        self.thread_name = thread_name
        self.thread_ID = thread_ID
        self.lifespan = lifespan        # in periods
        self.born = None                # the timer starts the moment it runs

    @property
    def age(self):
        """How many periods this thread has been alive, from its own point of view."""
        if self.born is None:
            return 0.0
        return (time.monotonic() - self.born) / PERIOD

    # helper function to execute the threads
    def run(self):
        self.born = time.monotonic()
        if self.lifespan is IMMORTAL:
            announce(f"{self.thread_name} {self.thread_ID} opens its eyes, and will never close them.")
            self.live_forever()
        else:
            announce(f"{self.thread_name} {self.thread_ID} is born, with {self.lifespan} periods to spend.")
            self.live_and_die()

    def live_forever(self):
        next_report = 10.0
        while not _stop.wait(PERIOD):       # wait() returns True only when the world ends
            if self.age >= next_report:
                announce(f"{self.thread_name} is still here. {self.age:.0f} periods, "
                         f"{_deaths} funerals.")
                next_report += 10

    def live_and_die(self):
        if _stop.wait(self.lifespan * PERIOD):
            return                          # the world ended before its time was up
        self.die()

    def die(self):
        global _deaths
        with _lock:
            _deaths += 1
        announce(f"{self.thread_name} {self.thread_ID} dies at the age of {self.age:.1f}.")
        successor().start()                 # every death makes room for a birth


def successor():
    """Whoever is born next. Rarely, it is an old name coming back around."""
    if world_age() > AGE_OF_RETURN and random.random() < RESPAWN_CHANCE:
        name = random.choice(("Alpha", "Bravo"))
        returning = thread(name, next(_ids), LIFESPANS[name])
        announce(f"...something stirs. {name} is coming back.")
        announce(f"   To {name}, not one instant has passed. "
                 f"To Charlie, {charlie.age:.0f} periods have.")
        return returning
    return thread(random_name(), next(_ids), random.randint(2, 8))


alpha = thread("Alpha", 1000, LIFESPANS["Alpha"])
bravo = thread("Bravo", 2000, LIFESPANS["Bravo"])
charlie = thread("Charlie", 3000, LIFESPANS["Charlie"])

alpha.start()
bravo.start()
charlie.start()

# Begin the endless cycle
forever = True
try:
    while forever:
        time.sleep(PERIOD)
except KeyboardInterrupt:
    _stop.set()
    announce("The world ends. Charlie finally gets to rest, "
             f"at the age of {charlie.age:.0f}.")
