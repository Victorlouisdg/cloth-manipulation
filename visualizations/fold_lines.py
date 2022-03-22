import airo_blender_toolkit as abt
import blenderproc as bproc

from cloth_manipulation.folds import SideFold, SleeveFold

bproc.init()

shirt = abt.PolygonalShirt()
keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}

left_sleeve = SleeveFold(keypoints, "left")
right_sleeve = SleeveFold(keypoints, "right")
left_side = SideFold(keypoints, "left")
right_side = SideFold(keypoints, "right")

abt.visualize_line(*left_sleeve.fold_line(), length=0.6)
abt.visualize_line(*right_sleeve.fold_line(), length=0.6)
abt.visualize_line(*left_side.fold_line(), length=1.5)
abt.visualize_line(*right_side.fold_line(), length=1.5)

empty = abt.visualize_transform(left_side.gripper_start_pose(), 0.1)
empty = abt.visualize_transform(right_side.gripper_start_pose(), 0.1)
