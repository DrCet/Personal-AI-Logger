import os
import argparse

def print_project_structure(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Ignore .venv, vosk_model, .git, and __pycache__ directories
        dirnames[:] = [d for d in dirnames if d not in ['.venv', 'vosk_model', '.git', '__pycache__']]
        
        level = dirpath.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f'{indent}{os.path.basename(dirpath)}/')
        
        subindent = ' ' * 4 * (level + 1)
        for f in filenames:
            print(f'{subindent}{f}')

def main():
    parser = argparse.ArgumentParser(description='Print the project structure.')
    parser.add_argument('--print_structure', action='store_true', help='Print the project structure of the current directory')
    args = parser.parse_args()
    
    if args.print_structure:
        print_project_structure(os.getcwd())

if __name__ == "__main__":
    main()
