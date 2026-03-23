import numpy as np
from stl import mesh

# Vértices exactos del IndexedFaceSet de tu proto
vertices = np.array([
    [-0.1, -0.1,  0.05],  # 0
    [ 0.1, -0.1,  0.05],  # 1
    [ 0.1, -0.18,-0.048], # 2
    [-0.1, -0.18,-0.048], # 3
    [-0.1, -0.1, -0.05],  # 4
    [ 0.1, -0.1, -0.05],  # 5
    [ 0.1, -0.18,-0.05],  # 6
    [-0.1, -0.18,-0.05],  # 7
])

# Caras del coordIndex (trianguladas)
faces = np.array([
    [1,0,3],[1,3,2],  # top slope
    [0,1,5],[0,5,4],  # back
    [4,5,6],[4,6,7],  # bottom
    [4,7,3],[4,3,0],  # right
    [2,6,5],[2,5,1],  # left
    [2,3,7],[2,7,6],  # front
])

rampa = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        rampa.vectors[i][j] = vertices[f[j]]

rampa.save("rampa.stl")
print("rampa.stl generada")