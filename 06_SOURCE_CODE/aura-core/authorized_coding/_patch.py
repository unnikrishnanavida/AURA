import re
p = r"E:\AURA\06_SOURCE_CODE\aura-core\authorized_coding\models.py"
s = open(p).read()
s = s.replace("    for name, spec_field in spec.fields:\n        if name not in inputs:", "    for spec_field in spec.fields:\n        name = spec_field.name\n        if name not in inputs:")
s = s.replace("@dataclass(frozen=True)\nclass Approval:", "@dataclass\nclass Approval:")
open(p, "w").write(s)
print("done")
PY