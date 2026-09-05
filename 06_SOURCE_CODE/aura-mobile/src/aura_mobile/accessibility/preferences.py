from dataclasses import dataclass


@dataclass
class MobileAccessibility: screen_reader:bool=False; reduced_motion:bool=False; text_scale:float=1.0
