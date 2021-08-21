#!/usr/bin/env python3

counter = 3 - 1 if 3 > 1 else 3

s = '#!/usr/bin/env python3\n\ncounter = %d - 1 if %d > 1 else 3\n\ns = %s\nprint(s %% (counter, counter, repr(s)))'
print(s % (counter, counter, repr(s)))
