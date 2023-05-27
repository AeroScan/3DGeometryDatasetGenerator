from .base_curves import BaseLineCurve

class Line(BaseLineCurve):
    
    @staticmethod
    def getType():
        return 'Line'