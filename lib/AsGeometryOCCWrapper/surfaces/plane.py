import numpy as np

from .base_surfaces import BaseElementarySurface

class Plane(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Plane'
    
    def _fixOrientation(self, face_orientation: int):
        if face_orientation == 1:
            old_loc = np.array(self.getLocation())
            old_axis = np.array(self.getZAxis())
            self._shape.Mirror(self._shape.Position().Ax2())
            new_loc = np.array(self.getLocation())
            new_axis = np.array(self.getZAxis())
            
            assert np.all(np.isclose(old_axis, -new_axis)) and \
                   np.all(np.isclose(old_loc, new_loc)), \
                   f'Sanity Check Failed: problem in reversing a {self.getName()}. ' \
                   f'\n\t\t~~~~~ {old_axis} != {-new_axis} or ' \
                   f'{old_loc} != {new_loc} ~~~~~'