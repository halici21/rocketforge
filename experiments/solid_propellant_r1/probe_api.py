"""What the existing thermochemistry public API actually exposes."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import rocketforge.physics.thermochemistry as T
print("public names:", sorted(n for n in dir(T) if not n.startswith("_")))
