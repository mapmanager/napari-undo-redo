# ABOUT

Shapes layer supports 5 types of shapes:

- ellipse: data = np.array(
        [corner, corner + size_v, corner + size_h + size_v, corner + size_h])
- rectangle: data = np.array(
        [corner, corner + size_v, corner + size_h + size_v, corner + size_h])
- polygon:
- line: data = np.array([corner, corner + full_size])
- path:

Except ellipse, all have vertex add and vertex delete properties.

## Need to add commands for

1. Add
1. Delete
1. Move
1. Face Color Change
1. Edge Color Change
1. Edge width change
1. blending
1. opacity