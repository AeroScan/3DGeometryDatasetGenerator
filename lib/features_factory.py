from .primitives import CurveFactory, SurfaceFactory

class FeaturesFactory:

    @staticmethod
    def removeNoneValuesOfDict(d: dict) -> dict:
        for key in d.keys():
            i = 0
            while i < len(d[key]):
                if d[key][i] is None:
                    d[key].pop(i)
                else:
                    i = i + 1

        return d

    @staticmethod
    def getListOfDictFromPrimitive(primitives: dict) -> dict:
        for i in range(0, len(primitives['curves'])):
            if primitives['curves'][i] is not None:
                primitives['curves'][i] = CurveFactory.getDictFromPrimitive(primitives['curves'][i])
        for i in range(0, len(primitives['surfaces'])):
            if primitives['surfaces'][i] is not None:
                primitives['surfaces'][i] = SurfaceFactory.getDictFromPrimitive(primitives['surfaces'][i])
        
        features = {
            'curves': primitives['curves'],
            'surfaces': primitives['surfaces']
        }

        features = FeaturesFactory.removeNoneValuesOfDict(d=features)

        return features

    @staticmethod
    def updatePrimitiveWithMeshParams(primitive, mesh: dict):
        return primitive.fromMesh(mesh)