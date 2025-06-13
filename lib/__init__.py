import jinja2
import matplotlib

# Customize matplotlib settings
matplotlib.rc("font", **{ "family": "Times New Roman", "size": 8 })
matplotlib.use("Agg")

SYMBOLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
A_COLOR = "#0000FF"
B_COLOR = "#FF0000"
CM_TO_INCHES = 1 / 2.54

# Initialize Jinja2 environment with a file system loader for templates
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(["./lib/templates"])
)