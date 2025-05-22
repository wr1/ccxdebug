import numpy as np
import pyvista as pv

def convert_to_vtu(input_path, output_path):
    """Convert a CalculiX .inp file to VTU format using PyVista."""
    nodes = []
    node_ids = {}
    elements = []
    element_types = []
    in_node = False
    in_element = False
    current_element_type = None

    with open(input_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('**'):
            continue

        if line.upper().startswith('*NODE'):
            in_node = True
            in_element = False
            continue

        if line.upper().startswith('*ELEMENT'):
            in_node = False
            in_element = True
            # Extract element type (e.g., TYPE=S8R)
            if 'TYPE=' in line.upper():
                try:
                    current_element_type = line.upper().split('TYPE=')[1].split(',')[0].strip()
                except IndexError:
                    raise ValueError("Invalid *ELEMENT format: TYPE= specifier malformed")
            else:
                current_element_type = 'C3D8'  # Default to C3D8 if TYPE= is missing
            continue

        if line.upper().startswith('*'):
            in_node = False
            in_element = False
            current_element_type = None
            continue

        if in_node:
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    node_id = int(parts[0].strip())
                    coords = [float(parts[i].strip()) for i in range(1, 4)]
                    nodes.append(coords)
                    node_ids[node_id] = len(nodes) - 1
                except (ValueError, IndexError):
                    continue  # Skip malformed node lines

        if in_element and current_element_type:
            parts = line.split(',')
            try:
                # First part is element ID, rest are node IDs
                elem_nodes = [int(n.strip()) for n in parts[1:] if n.strip() and n.strip().isdigit()]
                if elem_nodes:
                    # Map node IDs to 0-based indices
                    elem_indices = [node_ids[n] for n in elem_nodes]
                    elements.append(elem_indices)
                    element_types.append(current_element_type)
            except (ValueError, KeyError):
                continue  # Skip malformed element lines or undefined nodes

    if not nodes or not elements:
        raise ValueError("No valid nodes or elements found in .inp file")

    # Convert nodes to NumPy array
    points = np.array(nodes, dtype=np.float64)

    # Map CalculiX element types to VTK types
    vtk_cell_types = []
    cells = []
    for elem_type, elem_nodes in zip(element_types, elements):
        if elem_type.upper() == 'C3D8':
            # VTK_HEXAHEDRON (8 nodes)
            if len(elem_nodes) != 8:
                continue  # Skip if incorrect number of nodes
            vtk_cell_types.append(pv.CellType.HEXAHEDRON)
            cells.append(8)
            cells.extend(elem_nodes)
        elif elem_type.upper() == 'S8R':
            # Approximate S8R (8-node shell) as VTK_QUAD (4 nodes) or skip
            # Note: S8R is a shell element, so we use first 4 nodes as a quad
            if len(elem_nodes) >= 4:
                vtk_cell_types.append(pv.CellType.QUAD)
                cells.append(4)
                cells.extend(elem_nodes[:4])  # Use first 4 nodes
            else:
                continue  # Skip if insufficient nodes
        else:
            raise ValueError(f"Unsupported element type: {elem_type}")

    if not cells:
        raise ValueError("No valid elements converted to VTK types")

    # Create PyVista UnstructuredGrid
    cells = np.array(cells, dtype=np.int64)
    cell_types = np.array(vtk_cell_types, dtype=np.uint8)
    grid = pv.UnstructuredGrid(cells, cell_types, points)

    # Save to VTU
    grid.save(output_path, binary=True)
