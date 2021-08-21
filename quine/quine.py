#!/usr/bin/env python3

s = '#!/usr/bin/env python3\n\ns = %s\nprint(s %% repr(s))'
print(s % repr(s))
