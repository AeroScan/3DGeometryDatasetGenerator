import numpy as np

EPS = np.finfo(np.float32).eps

def rotation_matrix_a_to_b(A, B):
    """
    Finds rotation matrix from vector A in 3d to vector B
    in 3d.
    B = R @ A
    """
    cos = np.dot(A, B)
    sin = np.linalg.norm(np.cross(B, A))
    u = A
    v = B - np.dot(A, B) * A
    v = v / (np.linalg.norm(v) + EPS)
    w = np.cross(B, A)
    w = w / (np.linalg.norm(w) + EPS)
    F = np.stack([u, v, w], 1)
    G = np.array([[cos, -sin, 0],
                [sin, cos, 0],
                [0, 0, 1]])
    # B = R @ A
    try:
        R = F @ G @ np.linalg.inv(F)
    except:
        R = np.eye(3, dtype=np.float32)
    return R

def pca_numpy(array):
    S, U = np.linalg.eig(array.T @ array)
    return S, U

def add_noise(array, limit = 0.01):
    points = array[:, :3]
    normals = array[:, 3:]
    noise = normals * np.random.uniform(-limit, limit, (points.shape[0],1))
    points = points + noise.astype(np.float32)
    #not adding noise on normals yet
    noise_array = np.concatenate((points, normals), axis=1)
    return noise_array

def align_canonical(array):
    points = array[:, :3]
    normals = array[:, 3:]
    S, U = pca_numpy(points)
    smallest_ev = U[:, np.argmin(S)]
    R = rotation_matrix_a_to_b(smallest_ev, np.array([1, 0, 0]))
    # rotate input points such that the minor principal
    # axis aligns with x axis.
    points = (R @ points.T).T
    normals= (R @ normals.T).T
    aligned_array = np.concatenate((points, normals), axis=1)
    return aligned_array

def centralize(array):
    points = array[:, :3]
    mean = np.mean(points, 0)
    centralized_points = points - mean
    array[:, :3] = centralized_points
    return array

def rescale(array, factor = 1000):
    points = array[:, :3]
    scaled_points = points / (factor + EPS)
    array[:, :3] = scaled_points
    return array

def cube_rescale(array, factor = 1):
    points = array[:, :3]
    std = np.max(points, 0) - np.min(points, 0)
    scaled_points = (points / (np.max(std) + EPS))*factor
    array[:, :3] = scaled_points
    return array