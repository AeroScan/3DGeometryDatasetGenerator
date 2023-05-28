from OCC.Core.Geom import Geom_Plane

import numpy as np

from .base_surfaces import BaseElementarySurface

class Plane(BaseElementarySurface):

    @staticmethod
    def getType():
        return 'Plane'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_Plane(adaptor.Plane())
    
    def _fixOrientation(self):
        if self._orientation == 1:
            old_loc = np.array(self.getLocation())
            old_axis = np.array(self.getZAxis())
            self._geom.Mirror(self._geom.Position().Ax2())
            new_loc = np.array(self.getLocation())
            new_axis = np.array(self.getZAxis())
            
            assert np.all(np.isclose(old_axis, -new_axis)) and \
                   np.all(np.isclose(old_loc, new_loc)), \
                   f'Sanity Check Failed: problem in reversing a {self.getType()}. ' \
                   f'\n\t\t~~~~~ {old_axis} != {-new_axis} or ' \
                   f'{old_loc} != {new_loc} ~~~~~'
            
            # orientation = 0
