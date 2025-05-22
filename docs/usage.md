 # Usage
 
 Run commands from the terminal:
 
 ```bash
 # Replace materials with isotropic properties
 ccxdebug iso input.inp
 # Output: input_iso.inp
 
 # Convert .inp to VTU format
 ccxdebug vtu input.inp
 # Output: input.vtu
 
 # Analyze mesh quality
 ccxdebug quality input.inp
 # Output: input_quality.csv, input_quality.vtu
 ```
 
 The `quality` command produces:
 - A CSV file with metrics for each element.
 - A VTU file with quality metrics as cell data, which can be visualized in ParaView to plot metrics like aspect ratio or Jacobian.
