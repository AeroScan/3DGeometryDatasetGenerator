
class BaseCurveFeature:

    def __init__(self):
        self.sharp = None
        self.vert_indices = None
        self.vert_parameters = None

    def fromMesh(self, mesh: dict) -> None:
        self.sharp = mesh['sharp'] if 'sharp' in mesh.keys() else 'true'
        self.vert_indices = mesh['vert_indices'] if 'vert_indices' in mesh.keys() else []
        self.vert_parameters = mesh['vert_parameters'] if 'vert_parameters' in mesh.keys() else []

    def toDict(self) -> dict:
        features = {}
        features['sharp'] = self.sharp
        features['vert_indices'] = self.vert_indices
        features['vert_parameters'] = self.vert_parameters

        return features