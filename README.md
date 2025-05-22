 # CCXDebug
 
 A CLI tool for processing CalculiX (.inp) files with three commands:
 - `ccxdebug iso <file>`: Replace material definitions with isotropic materials.
 - `ccxdebug vtu <file>`: Convert .inp file to VTU format using PyVista.
 - `ccxdebug quality <file>`: Analyze mesh quality (aspect ratio, skew, warping, etc.), saving results to CSV and VTU for visualization in ParaView.
 
 ## Installation
 
 ```bash
 poetry install
 ```
 
 ## Usage
 
 ```bash
 # Replace materials with isotropic (E=210000, ν=0.3)
 ccxdebug iso input.inp
 # Convert .inp to VTU
 ccxdebug vtu input.inp
 # Analyze mesh quality
 ccxdebug quality input.inp
 ```
 
 The `quality` command generates:
 - `input_quality.csv`: Detailed metrics for each element.
 - `input_quality.vtu`: Mesh with quality metrics as cell data, viewable in ParaView.
