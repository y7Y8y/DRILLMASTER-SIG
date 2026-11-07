"""scene3d — modèle de scène partagé coupe/3D (numpy, sans QGIS)."""
from .model import HoleTable, IntervalTable, SceneModel
from .geometry import (build_trajectories, positions, interval_segments,
                       build_spatial_index, lod_selection, expand_tubes)
