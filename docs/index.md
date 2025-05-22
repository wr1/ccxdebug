 # CCXDebug Documentation
 
 Welcome to the documentation for CCXDebug, a CLI tool for processing CalculiX .inp files.
 
 ## Features
 
 - `ccxdebug iso <file>`: Replace all material definitions with isotropic materials (E=210000, ν=0.3).
 - `ccxdebug vtu <file>`: Convert .inp file to VTU format for visualization.
 - `ccxdebug quality <file>`: Analyze mesh quality, including aspect ratio, skew, warping, and checks for zero-area or butterfly elements. Outputs CSV and VTU files for analysis and visualization in ParaView.
 
 ## Getting Started
 
 Install using Poetry:
 
 ```bash
 poetry install
 ```
