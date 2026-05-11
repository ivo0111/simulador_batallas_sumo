def decide(sensors):
    # Prioridad 1: no caerse
    if sensors["line_left"] and sensors["line_right"]:
        return -2.0, -2.0          # retrocede recto

    if sensors["line_left"]:
        return -1.0, 1.0           # gira a la derecha

    if sensors["line_right"]:
        return 1.0, -1.0           # gira a la izquierda

    # Prioridad 2: si ve al enemigo, esquiva girando
    if sensors["enemy"]:
        return -2.0, 2.0

    # Si no pasa nada, gira buscando al enemigo
    return 0.5, -0.5