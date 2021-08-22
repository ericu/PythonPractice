#!/usr/bin/env python3


def power_set(input_set):
    def helper(element, rest):
        if not rest:
            tail = frozenset([frozenset([element]), frozenset()])
        else:
            tail = helper(rest[0], rest[1:])
        local = frozenset({tail_set | {element} for tail_set in tail})
        return local | tail

    as_list = list(input_set)
    if not as_list:
        return frozenset()
    return helper(as_list[0], as_list[1:])


def display_set(set_of_sets):
    as_list = sorted([list(inner_set) for inner_set in set_of_sets])
    for row in as_list:
        print(row)


if __name__ == "__main__":
    display_set(power_set({3, 4, 5, 6, 7}))
