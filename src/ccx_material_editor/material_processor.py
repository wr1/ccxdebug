import numpy as np

def replace_materials(input_path, output_path):
    """Read a CalculiX .inp file, replace all material elastic definitions with isotropic ones, and write to output."""
    with open(input_path, 'r') as f:
        lines = f.readlines()

    output_lines = []
    in_material = False
    in_elastic = False
    material_name = None

    for line in lines:
        line = line.strip()

        # Detect material definition
        if line.upper().startswith('*MATERIAL'):
            in_material = True
            material_name = line.split('NAME=')[1].strip() if 'NAME=' in line else 'Unnamed'
            output_lines.append(line)
            continue

        # Detect elastic definition within material
        if in_material and line.upper().startswith('*ELASTIC'):
            in_elastic = True
            output_lines.append('*ELASTIC')
            output_lines.append('210000, 0.3')
            continue

        # Skip data lines after *ELASTIC
        if in_elastic and not line.upper().startswith('*'):
            continue

        # Reset flags when encountering a new keyword
        if line.upper().startswith('*'):
            in_material = False
            in_elastic = False
            material_name = None

        # Append all other lines
        output_lines.append(line)

    with open(output_path, 'w') as f:
        for line in output_lines:
            f.write(line + '\n')
