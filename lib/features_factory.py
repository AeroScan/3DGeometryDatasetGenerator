
class FeaturesFactory:
    @staticmethod
    def getPrimitiveObject(type, shape=None, mesh=None):
        type = type.lower()
        if type in CurveFactory.CURVE_TYPES.keys():
            return CurveFactory.getPrimitiveObject(type, shape, mesh)
        elif type in SurfaceFactory.SURFACE_TYPES.keys():
            return SurfaceFactory.getPrimitiveObject(type, shape, mesh)
        else:
            return None

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

    @staticmethod
    def normalizeShape(features, R, t, s):
        for key in features:
            for i in range(len(features[key])):
                if features[key][i] is not None:
                    features[key][i].normalize(R=R, t=t, s=s)
