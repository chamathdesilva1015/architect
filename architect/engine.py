import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class BlueprintEngine:
    def __init__(self, templates_dir="templates", archetypes_dir="archetypes"):
        self.templates_dir = Path(templates_dir)
        self.archetypes_dir = Path(archetypes_dir)
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.vault_path = Path.home() / ".architect_vault.json"

    def get_available_archetypes(self):
        if not self.archetypes_dir.exists():
            return []
        return [f.stem for f in self.archetypes_dir.glob("*.json")]

    def load_archetype(self, archetype_name):
        archetype_path = self.archetypes_dir / f"{archetype_name}.json"
        if not archetype_path.exists():
            raise FileNotFoundError(f"Archetype '{archetype_name}' not found at {archetype_path}")
        
        with open(archetype_path, 'r') as f:
            return json.load(f)

    def log_to_vault(self, entry_type, name):
        """Log an action to the personal vault."""
        vault_data = []
        if self.vault_path.exists():
            try:
                with open(self.vault_path, 'r') as f:
                    vault_data = json.load(f)
            except Exception:
                vault_data = []
                
        vault_data.append({
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            "name": name
        })
        
        try:
            with open(self.vault_path, 'w') as f:
                json.dump(vault_data, f, indent=2)
        except Exception as e:
            print(f"Failed to log to vault: {e}")

    def get_vault_data(self):
        if not self.vault_path.exists():
            return []
        try:
            with open(self.vault_path, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def generate(self, archetype_name, output_path, **context):
        archetype = self.load_archetype(archetype_name)
        out_dir = Path(output_path)
        
        if out_dir.exists():
            print(f"Warning: Output path '{out_dir}' already exists. Files may be overwritten.")
        else:
            out_dir.mkdir(parents=True)

        # Create folders
        folders = archetype.get("folders", [])
        for folder in folders:
            folder_path = out_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)

        # Process files
        files = archetype.get("files", {})
        generated_files = []
        
        for dest_path_str, template_name in files.items():
            dest_path = out_dir / dest_path_str
            
            # Ensure parent directories exist for the file
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                template = self.jinja_env.get_template(template_name)
                # Render with the provided dynamic context
                final_context = {"project_name": out_dir.name}
                final_context.update(context)
                rendered_content = template.render(**final_context)
                
                with open(dest_path, 'w') as f:
                    f.write(rendered_content)
                generated_files.append(dest_path_str)
            except Exception as e:
                print(f"Error generating {dest_path} from {template_name}: {e}")
                
        # Write the Health Check config
        config_path = out_dir / ".architect.json"
        config_data = {
            "archetype": archetype_name,
            "files": generated_files
        }
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        # Log to vault
        self.log_to_vault("Blueprint", archetype_name)

    def generate_sketch(self, idea_name, output_dir="."):
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = out_dir / "SKETCH.md"
        try:
            template = self.jinja_env.get_template("SKETCH.md.j2")
            rendered_content = template.render(idea_name=idea_name)
            with open(dest_path, 'w') as f:
                f.write(rendered_content)
            
            self.log_to_vault("Sketch", idea_name)
            return str(dest_path)
        except Exception as e:
            print(f"Error generating sketch: {e}")
            return None
