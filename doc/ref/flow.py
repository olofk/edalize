import os

# Import the Icestorm backend
from edalize.flows.icestorm import Icestorm

# Find out which flow options that are available
available_flow_options = Icestorm.get_flow_options()
print(available_flow_options)

# In this case we are happy with the default flow options
flow_options = {}

# Get the tool-specific options for all tool in the flow
tool_options = Icestorm.get_tool_options(flow_options)
print(tool_options)

# Create an EDAM description with our preferred tool settings

edam = {
    "name": "my_design",
    "files": [{"name": "myfile.v", "file_type": "verilogSource"}],
    "flow_options": {
        "nextpnr_options": ["--lp8k", "--package", "cm81", "--freq", "'32'"]
    },
}

# Instatiate the flow
work_root = "out"
os.makedirs(work_root, exist_ok=True)
icestorm = Icestorm(edam, work_root)

# Create all files needed to run the flow
icestorm.configure()

# Build the design
icestorm.build()
