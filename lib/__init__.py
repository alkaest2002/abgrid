import jinja2
import matplotlib

# Customize matplotlib settings
matplotlib.rc("font", **{ "family": "Times New Roman", "size": 8 })
matplotlib.use("Agg")

# Initialize Jinja2 environment with a file system loader for templates
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(["./lib/templates"])
)