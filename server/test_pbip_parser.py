import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from server.pbip_parser import PBIPParser
from server.metadata_tools import MetadataTools


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    parser = PBIPParser(project_root)
    tools = MetadataTools(project_root)

    print("PBIP Project Root:", project_root)
    print("Report folder:", parser.report_folder)
    print("Semantic model folder:", parser.semantic_model_folder)

    print("\n=== Pages ===")
    for page in parser.get_pages():
        print(page)

    print("\n=== All Visuals ===")
    for visual in parser.get_all_visuals():
        print(visual)

    print("\n=== Tables ===")
    for table in parser.get_tables():
        print(table)

    print("\n=== Measures ===")
    for measure in parser.get_measures():
        print(measure)

    print("\n=== Metadata Tools Summary ===")
    print(tools.list_pages())
    print(tools.list_visuals())
    print(tools.list_tables())
    print(tools.list_measures())


if __name__ == "__main__":
    main()
