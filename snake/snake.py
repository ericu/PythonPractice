#!/usr/bin/env python3

import curses

def main(stdscr):
    (y_min, x_min) = stdscr.getbegyx()
    (height, width) = stdscr.getmaxyx()
    if width < 20 or height < 15:
        raise RuntimeError(f'Sorry, your screen of {width} by {height} is too small')

    stdscr.clear()
    stdscr.border()
    stdscr.hline(2, 1, curses.ACS_HLINE, width - 2)
    stdscr.addch(2, 0, curses.ACS_LTEE)
    stdscr.addch(2, width - 1, curses.ACS_RTEE)

    status_bar = curses.newwin(1, width - 2, 1, 1)

    stdscr.refresh()
    # It appears that we can't write to the last character of the window using
    # addnstr, as it then pushes the cursor off the edge and returns an error.
    # From the documentation: "Attempting to write to the lower right corner of
    # a window, subwindow, or pad will cause an exception to be raised after the
    # character is printed".  So we'll leave a padding space at the beginning
    # and end of the status bar; it'll look better anyway.
    status_bar.addnstr(0, 1, 'This_is_in_the_status_bar._This_is_in_the_status_bar._This_is_in_the_status_bar._This_is_in_the_status_bar._This_is_in_the_status_bar.', width - 4, curses.A_REVERSE)
    status_bar.refresh()
    stdscr.getkey()

if __name__ == "__main__":
    curses.wrapper(main)

