# Flip Loop Animation
This addon aims to simplify the creation of walk/run locomotion animations.

- Generates the Second half of the animation with [Paste Flipped](https://docs.blender.org/manual/en/latest/animation/armatures/posing/editing/copy_paste.html)
- Handles looping by duplicating the First frame to Last

## Flip Loop
This is the main operator, it does the following:
1. Deletes the Second half of the animation
2. Copies the First half and Pastes it Flipped into the Second part
3. Duplicates the First frame to Last for loop interpolation

## Auto set Start/End frames
  - Toggle to auto set the scene frames, Start to 0 and End to action.length -1
    - (not setting to the very last because when looping the last frame is a duplicate of first and should be omitted)

## Auto switch to NLA ★ action
  - Toggle to auto set the action by matching the NLA starred (is_solo) track name
    - This assumes that you've renamed the track to the same as the action name

## Notes
### Bake all into first keyframe
You'll need to bake all bones of interest into the first keyframe (frame 0) so that it can be copied over to the last keyframe for loop interpolation to work

### Determining the action length
Flip Loop determines the action length by looking at the last keyframe position, make sure to have any keyframe regardless of value before calling flip loop the first time

### Assign a shortcut
Right click on the button `Apply Flip Loop` to add to favourites, then when the mouse cursor is over the dopesheet viewport press Q and select it.
> My goal is to auto detect when to execute the addon without interfering with other operations, however there are several blockers for that so use a shortcut at the moment.

### Manually fix Rotation jitter
If you're not using Quaternions you could be getting the [Gimbal Lock](https://en.wikipedia.org/wiki/Gimbal_lock).  
you can switch the rotation vectors from the dropdown under `3d Viewport > N Panel > Rotation` to `Quaternion XYZW`.  

If you're still getting weird rotations for example on hands you can use [Flip Quats (Alt-F)](https://docs.blender.org/manual/en/latest/animation/armatures/posing/editing/flip_quats.html).  
> It's important to flip them from where they happen backwards to the first keyframe because the addon regenerates the second half of the animation and the flip will be lost.
