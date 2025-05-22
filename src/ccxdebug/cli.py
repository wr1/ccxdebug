import argparse
from .material_processor import replace_materials
from .vtu_converter import convert_to_vtu
from .quality_analyzer import analyze_mesh_quality

def main():
    parser = argparse.ArgumentParser(description="CCXDebug: Process CalculiX .inp files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for 'iso' command
    iso_parser = subparsers.add_parser("iso", help="Replace materials with isotropic properties")
    iso_parser.add_argument("input_file", help="Input .inp file")

    # Subparser for 'vtu' command
    vtu_parser = subparsers.add_parser("vtu", help="Convert .inp to VTU format")
    vtu_parser.add_argument("input_file", help="Input .inp file")

    # Subparser for 'quality' command
    quality_parser = subparsers.add_parser("quality", help="Analyze mesh quality")
    quality_parser.add_argument("input_file", help="Input .inp file")

    args = parser.parse_args()

    if args.command == "iso":
        output_file = args.input_file.replace(".inp", "_iso.inp")
        replace_materials(args.input_file, output_file)
        print(f"Isotropic material file saved as {output_file}")
    elif args.command == "vtu":
        output_file = args.input_file.replace(".inp", ".vtu")
        convert_to_vtu(args.input_file, output_file)
        print(f"VTU file saved as {output_file}")
    elif args.command == "quality":
        output_csv = args.input_file.replace(".inp", "_quality.csv")
        output_vtu = args.input_file.replace(".inp", "_quality.vtu")
        analyze_mesh_quality(args.input_file, output_csv, output_vtu)
        print(f"Mesh quality analysis saved as {output_csv} and {output_vtu}")

if __name__ == "__main__":
    main()
