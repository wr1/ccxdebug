import numpy as np
import pyvista as pv
import csv

def compute_warping(points):
    """Compute warping factor for a quad element (max distance from plane)."""
    if len(points) < 4:
        return 0.0
    p0, p1, p2 = points[:3]
    v1 = p1 - p0
    v2 = p2 - p0
    normal = np.cross(v1, v2)
    if np.linalg.norm(normal) == 0:
        return float('inf')
    normal = normal / np.linalg.norm(normal)
    d = np.abs(np.dot(points - p0, normal))
    return np.max(d)

def is_butterfly(points):
    """Check if a quad element is a butterfly (opposing edges cross)."""
    if len(points) != 4:
        return False
    def triangle_area(p1, p2, p3):
        v1 = p2 - p1
        v2 = p3 - p1
        return 0.5 * np.linalg.norm(np.cross(v1, v2))
    area1 = triangle_area(points[0], points[1], points[2])
    area2 = triangle_area(points[2], points[3], points[0])
    total_area = area1 + area2
    return total_area < 0 or np.isclose(total_area, 0, atol=1e-10)

def compute_3d_jacobian(points):
    """Compute min Jacobian determinant for an 8-node hex element."""
    if len(points) != 8:
        return float('nan')
    # Hexahedron node order: bottom (0,1,2,3), top (4,5,6,7)
    centroid = np.mean(points, axis=0)
    min_det = float('inf')
    # Define tetrahedra using corner nodes and centroid
    for tet_indices in [
        [0, 1, 3],  # Bottom face
        [1, 2, 3],
        [4, 5, 7],  # Top face
        [5, 6, 7]
    ]:
        p0 = points[tet_indices[0]]
        p1 = points[tet_indices[1]]
        p2 = points[tet_indices[2]]
        p3 = centroid
        v1 = p1 - p0
        v2 = p2 - p0
        v3 = p3 - p0
        det = np.dot(v1, np.cross(v2, v3))
        min_det = min(min_det, det)
    return min_det

def analyze_mesh_quality(input_path, output_csv, output_vtu):
    """Analyze mesh quality of a CalculiX .inp file, save metrics to CSV and VTU."""
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
            if 'TYPE=' in line.upper():
                try:
                    current_element_type = line.upper().split('TYPE=')[1].split(',')[0].strip()
                except IndexError:
                    raise ValueError("Invalid *ELEMENT format: TYPE= specifier malformed")
            else:
                current_element_type = 'C3D8'
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
                    continue

        if in_element and current_element_type:
            parts = line.split(',')
            try:
                elem_id = int(parts[0].strip())
                elem_nodes = [int(n.strip()) for n in parts[1:] if n.strip() and n.strip().isdigit()]
                if elem_nodes:
                    elem_indices = [node_ids[n] for n in elem_nodes]
                    elements.append((elem_id, elem_indices))
                    element_types.append(current_element_type)
            except (ValueError, KeyError):
                continue

    if not nodes or not elements:
        raise ValueError("No valid nodes or elements found in .inp file")

    points = np.array(nodes, dtype=np.float64)
    vtk_cell_types = []
    cells = []
    valid_elements = []
    valid_element_types = []
    for elem_type, (elem_id, elem_nodes) in zip(element_types, elements):
        if elem_type.upper() == 'C3D8' and len(elem_nodes) == 8:
            vtk_cell_types.append(pv.CellType.HEXAHEDRON)
            cells.append(8)
            cells.extend(elem_nodes)
            valid_elements.append((elem_id, elem_nodes))
            valid_element_types.append(elem_type)
        elif elem_type.upper() == 'S8R' and len(elem_nodes) >= 4:
            vtk_cell_types.append(pv.CellType.QUAD)
            cells.append(4)
            cells.extend(elem_nodes[:4])
            valid_elements.append((elem_id, elem_nodes))
            valid_element_types.append(elem_type)
        else:
            continue

    if not cells:
        raise ValueError("No valid elements converted to VTK types")

    cells = np.array(cells, dtype=np.int64)
    cell_types = np.array(vtk_cell_types, dtype=np.uint8)
    grid = pv.UnstructuredGrid(cells, cell_types, points)

    # Compute quality metrics
    quality = grid.compute_cell_quality(quality_measure='scaled_jacobian')
    aspect_ratio = grid.compute_cell_quality(quality_measure='aspect_ratio')['CellQuality']
    skew = grid.compute_cell_quality(quality_measure='skew')['CellQuality']
    jacobian = quality['CellQuality']
    grid = grid.compute_cell_sizes()
    areas_volumes = grid.cell_data['Area'] if 'Area' in grid.cell_data else grid.cell_data['Volume']

    # Custom metrics
    warping = []
    butterflies = []
    jacobian_3d = []
    for cell_id, (elem_id, elem_nodes) in enumerate(valid_elements):
        cell_points = points[elem_nodes[:4] if valid_element_types[cell_id] == 'S8R' else elem_nodes]
        warp = compute_warping(cell_points)
        warping.append(warp)
        butterfly = is_butterfly(cell_points) if valid_element_types[cell_id] == 'S8R' else False
        butterflies.append(butterfly)
        j3d = compute_3d_jacobian(points[elem_nodes]) if len(elem_nodes) == 8 else float('nan')
        jacobian_3d.append(j3d)

    # Flag problematic elements
    problematic_elements = []
    for i, (elem_id, _) in enumerate(valid_elements):
        issues = []
        if aspect_ratio[i] > 20:
            issues.append(f"High aspect ratio: {aspect_ratio[i]:.4f}")
        if areas_volumes[i] < 1e-6:
            issues.append(f"Near-zero area/volume: {areas_volumes[i]:.4e}")
        if jacobian[i] <= 0:
            issues.append(f"Nonpositive Jacobian: {jacobian[i]:.4f}")
        if valid_element_types[i] == 'S8R' and not np.isnan(jacobian_3d[i]) and jacobian_3d[i] <= 0:
            issues.append(f"Nonpositive 3D Jacobian: {jacobian_3d[i]:.4f}")
        if issues:
            problematic_elements.append((elem_id, valid_element_types[i], issues))

    # Assign metrics to cell data
    grid.cell_data['Element_ID'] = [e[0] for e in valid_elements]
    grid.cell_data['Element_Type'] = [1 if t.upper() == 'C3D8' else 0 for t in valid_element_types]
    grid.cell_data['Aspect_Ratio'] = aspect_ratio
    grid.cell_data['Skew'] = skew
    grid.cell_data['Jacobian'] = jacobian
    grid.cell_data['Jacobian_3D'] = jacobian_3d
    grid.cell_data['Warping'] = warping
    grid.cell_data['Area_Volume'] = areas_volumes
    grid.cell_data['Butterfly'] = [1 if b else 0 for b in butterflies]

    # Save VTU
    grid.save(output_vtu, binary=True)

    # Save results to CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Element_ID', 'Type', 'Aspect_Ratio', 'Skew', 'Jacobian', 'Jacobian_3D', 'Warping', 'Area_Volume', 'Butterfly'])
        for i, (elem_id, _) in enumerate(valid_elements):
            writer.writerow([
                elem_id,
                valid_element_types[i],
                aspect_ratio[i],
                skew[i],
                jacobian[i],
                jacobian_3d[i],
                warping[i],
                areas_volumes[i],
                butterflies[i]
            ])

    # Print summary
    print("Mesh Quality Summary:")
    if problematic_elements:
        print("Problematic Elements Detected:")
        for elem_id, elem_type, issues in problematic_elements:
            print(f"Element {elem_id} ({elem_type}):")
            for issue in issues:
                print(f"  {issue}")
    else:
        print("No problematic elements detected.")

    # Specific summary for elements 825, 885, 945
    print("\nDetailed Summary for Elements 825, 885, 945:")
    for elem_id in [825, 885, 945]:
        for i, (e_id, _) in enumerate(valid_elements):
            if e_id == elem_id:
                print(f"Element {elem_id} ({valid_element_types[i]}):")
                print(f"  Aspect Ratio: {aspect_ratio[i]:.4f}")
                print(f"  Skew: {skew[i]:.4f}")
                print(f"  Jacobian: {jacobian[i]:.4f}")
                print(f"  Jacobian 3D: {jacobian_3d[i]:.4f}")
                print(f"  Warping: {warping[i]:.4f}")
                print(f"  Area/Volume: {areas_volumes[i]:.4e}")
                print(f"  Butterfly: {butterflies[i]}")
                break
        else:
            print(f"Element {elem_id} not found in mesh")

    # Recommendations
    if problematic_elements:
        print("\nRecommendations:")
        print("- High aspect ratios: Remesh elements with ratios > 20 to reduce elongation.")
        print("- Near-zero area/volume: Check for collapsed nodes and merge duplicates.")
        print("- Nonpositive 3D Jacobian (S8R): Verify element type (S8R vs. C3D8) in solver; remesh if treated as solid.")
        print("- Use a meshing tool (e.g., Gmsh, ANSYS) to smooth or regenerate problematic regions.")
        print("- Visualize metrics in ParaView using the VTU file to identify problematic elements.")
