import subprocess,sys
checks=[[sys.executable,"-m","compileall","-q","aura_execution"],[sys.executable,"-m","pytest","-q"]]
for c in checks:
    r=subprocess.run(c)
    if r.returncode:sys.exit(r.returncode)
print("release checks passed")
