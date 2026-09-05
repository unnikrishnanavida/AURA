from dataclasses import dataclass


@dataclass
class Preferences: font_scale:float=1.0; reduced_motion:bool=False; high_contrast:bool=False
