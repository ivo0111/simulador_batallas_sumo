def decide(sensors):
    if sensors["line_left"] or sensors["line_right"]:
        return -1.5, -1.5

    return 2.0, -2.0               # giro continuo