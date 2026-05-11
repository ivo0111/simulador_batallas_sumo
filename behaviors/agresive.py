def decide(sensors):
    if sensors["line_left"] and sensors["line_right"]:
        return -2.0, -2.0

    if sensors["line_left"]:
        return 1.5, -1.5           # gira fuerte a la derecha

    if sensors["line_right"]:
        return -1.5, 1.5           # gira fuerte a la izquierda

    if sensors["enemy"]:
        return 5.0, 5.0            # sprint de ataque

    # Avanza lentamente girando para buscar
    return 1.0, 0.3