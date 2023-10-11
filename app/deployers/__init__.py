"""Define all deployment step.

Each step should be in a dedicated deployers to make the code easier to maintain.
"""
from app.deployers.config import ConfigDeployer
from app.deployers.grains import GrainsDeployer
from app.deployers.minion import MinionDeployer
from app.deployers.python_build import PythonBuildDeployer
from app.deployers.systemd import SystemdDeployer
