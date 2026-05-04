import typer
import json
import os
import subprocess
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
from architect.engine import BlueprintEngine

app = typer.Typer(help="Architect: Codebase Blueprint Generator - Founder's Edition")
console = Console()

def resolve_default(default_val):
    if default_val == "dynamic_cores":
        return os.cpu_count() or 4
    return default_val

def get_user_inputs(blueprint_name: str, arch_data: dict) -> dict:
    variables = arch_data.get("variables", {})
    context = {}
    
    console.print(f"\n[bold blue]--- Configuring {blueprint_name} ---[/]")
    
    # Founder's Trade-off Interview
    tradeoff = typer.prompt("Philosophy: [Performance] or [Speed]?", default="Performance")
    context["philosophy"] = tradeoff.lower()
    
    if context["philosophy"] == "speed":
        console.print("[bold yellow]Adding weight... hope your server has the RAM for this![/]")
    else:
        console.print("[bold green]Zero-dependency mindset engaged. Keeping it lean.[/]")

    if variables:
        for var_key, config in variables.items():
            if isinstance(config, dict):
                prompt_text = config.get("prompt", var_key)
                var_type = config.get("type", "string")
                default_val = config.get("default", "")
                
                resolved_default = resolve_default(default_val)
                
                while True:
                    prompt_str = f"{prompt_text} [Default: {resolved_default}]"
                    user_input = typer.prompt(prompt_str, default=str(resolved_default))
                    
                    if var_type == "int":
                        try:
                            context[var_key] = int(user_input)
                            break
                        except ValueError:
                            console.print("[bold red]Error: Please enter a valid integer.[/]")
                    else:
                        context[var_key] = user_input
                        break
            else:
                context[var_key] = typer.prompt(config)
    console.print("[bold blue]-------------------------------[/]\n")
    return context

def print_rich_tree(output_dir: str, folders: list, files: list, descriptions: dict):
    out_path = Path(output_dir).resolve()
    tree = Tree(f"📁 [bold cyan]{out_path}/[/]")
    
    all_items = []
    for f in folders:
        all_items.append({"path": f, "is_dir": True})
    for f in files:
        all_items.append({"path": f, "is_dir": False})
        
    all_items.sort(key=lambda x: x["path"])
    
    for item in all_items:
        icon = "📁" if item["is_dir"] else "📝"
        name = item["path"]
        desc = descriptions.get(name, "")
        
        if desc:
            if "START HERE" in desc:
                desc = desc.replace("START HERE", "[bold yellow]START HERE[/]")
            label = f"{icon} {name}  [dim]<-- {desc}[/]"
        else:
            label = f"{icon} {name}"
            
        tree.add(label)
        
    console.print(tree)

def print_data_flow(blueprint_name: str):
    console.print("\n[bold blue]Data Flow Architecture:[/]")
    if blueprint_name == "minimal_web":
        console.print("[bold cyan]User[/] -> [bold green]Request[/] -> [bold yellow]Route Handler[/] -> [bold magenta]Domain Logic[/] -> [bold red]Database[/]")
    elif blueprint_name == "concurrent_tasks":
        console.print("[bold cyan]Producer (Main)[/] -> [bold yellow]ThreadSafeQueue[/] -> [bold green]Worker Threads (Consumer)[/]")
    elif blueprint_name == "ml_pipeline":
        console.print("[bold cyan]Synthetic Data Gen[/] -> [bold yellow]Preprocessing[/] -> [bold green]Gradient Forest Training[/] -> [bold red]Model Evaluation[/]")
    else:
        console.print("[dim]No standard data flow diagram for this blueprint.[/]")

@app.command(name="generate")
def generate_project(
    archetype: str = typer.Argument(..., help="The name of the archetype to use"),
    output: str = typer.Option(".", "--output", "-o", help="The output directory path"),
    serve: bool = typer.Option(False, "--serve", help="Automatically serve and open a generated web app")
):
    try:
        out_dir = Path(output)
        if out_dir.exists() and any(out_dir.iterdir()):
            confirm = typer.confirm(f"This folder isn't empty. Overwrite/Inject here?", default=False)
            if not confirm:
                raise typer.Abort()

        engine = BlueprintEngine()
        
        try:
            arch_data = engine.load_archetype(archetype)
        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise typer.Exit(1)
            
        context = get_user_inputs(archetype, arch_data)

        folders = arch_data.get("folders", [])
        files = list(arch_data.get("files", {}).keys())
        descriptions = arch_data.get("descriptions", {})

        engine.generate(archetype, output, **context)
        
        console.print("\n[bold green]Architecture initialized successfully.[/]")
        print_rich_tree(output, folders, files, descriptions)
        print_data_flow(archetype)
        
        console.print(f"\n[bold yellow]Next Step:[/] Open GUIDE.md to begin implementation.")
        if archetype != "minimal_web" and not serve:
            # Special message for C++
            if archetype == "concurrent_tasks":
                console.print(f"Run `cd {out_dir} && make run` to see the thread pool in action.")
            else:
                console.print(f"Run `cd {out_dir} && make build` (or equivalent) to verify the skeleton.")

        if serve and archetype == "minimal_web":
            console.print("\n[bold green]Starting Live Serve...[/]")
            port = 8000
            url = f"http://localhost:{port}"
            proc = subprocess.Popen(["python", "-m", "http.server", str(port)], cwd=str(out_dir.resolve()), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print(f"Server running at [bold cyan]{url}[/]")
            webbrowser.open(url)
            console.print("[dim]Press Ctrl+C to stop the server.[/]")
            try:
                proc.wait()
            except KeyboardInterrupt:
                proc.terminate()
                console.print("\nServer stopped.")

    except typer.Abort:
        console.print("\n[bold red]Aborted.[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")

@app.command(name="sketch")
def sketch_idea(
    idea_name: str = typer.Argument(..., help="The name of your idea")
):
    """
    Generate a SKETCH.md for a 3:00 AM brainstorm session.
    """
    engine = BlueprintEngine()
    path = engine.generate_sketch(idea_name)
    if path:
        console.print(Panel.fit(
            f"[bold green]Sketch created![/]\nPath: {path}\nOpen it up and start brainstorming.",
            title="Inspiration -> Implementation"
        ))
    else:
        console.print("[bold red]Failed to create sketch.[/]")

@app.command(name="stats")
def show_stats():
    """
    Show personal Vault dashboard.
    """
    engine = BlueprintEngine()
    data = engine.get_vault_data()
    
    if not data:
        console.print("[bold yellow]Vault is empty. Go build something![/]")
        return
        
    sketches = [d for d in data if d.get("type") == "Sketch"][-5:]
    blueprints = [d for d in data if d.get("type") == "Blueprint"][-5:]
    
    table_b = Table(title="Last 5 Blueprints Built", show_header=True, header_style="bold magenta")
    table_b.add_column("Date")
    table_b.add_column("Archetype")
    
    for b in reversed(blueprints):
        date_str = b["timestamp"].split("T")[0]
        table_b.add_row(date_str, b["name"])
        
    table_s = Table(title="Last 5 Ideas Sketched", show_header=True, header_style="bold cyan")
    table_s.add_column("Date")
    table_s.add_column("Idea")
    
    for s in reversed(sketches):
        date_str = s["timestamp"].split("T")[0]
        table_s.add_row(date_str, s["name"])

    console.print("\n[bold green]--- Founder's Vault ---[/]\n")
    console.print(table_b)
    console.print("")
    console.print(table_s)

    # Self-Update Reminder
    if blueprints or sketches:
        last_entry = data[-1]
        last_date = datetime.fromisoformat(last_entry["timestamp"])
        if datetime.now() - last_date > timedelta(days=30):
            console.print("\n[bold yellow]Motivational Insight:[/]")
            console.print("[italic]\"Great things are not done by impulse, but by a series of small things brought together.\"[/]")
            console.print("[dim]It's been over 30 days. Time to build something new today?[/]")

@app.command(name="gallery")
def show_gallery():
    """
    The Founder's Gallery: A beautiful showcase of all available blueprints.
    """
    engine = BlueprintEngine()
    archetypes = engine.get_available_archetypes()
    
    table = Table(title="[bold blue]The Founder's Gallery[/]", show_header=True, header_style="bold green")
    table.add_column("Blueprint")
    table.add_column("Language")
    table.add_column("Philosophy")
    table.add_column("When to use")
    
    for arch_name in archetypes:
        try:
            data = engine.load_archetype(arch_name)
            table.add_row(
                f"[bold cyan]{arch_name}[/]",
                data.get("language", "N/A"),
                data.get("philosophy", "N/A"),
                data.get("usage", "N/A")
            )
        except:
            continue
            
    console.print(table)

@app.command(name="list")
def list_archetypes():
    engine = BlueprintEngine()
    archetypes = engine.get_available_archetypes()
    if not archetypes:
        console.print("No archetypes found.")
    else:
        console.print("[bold blue]Available Archetypes:[/]")
        for arch in archetypes:
            console.print(f"  - {arch}")

@app.command(name="check")
def check_project(
    project_dir: str = typer.Argument(".", help="The project directory to check")
):
    dir_path = Path(project_dir)
    config_path = dir_path / ".architect.json"
    
    if not config_path.exists():
        console.print("[bold red]Error:[/] .architect.json not found.", err=True)
        raise typer.Exit(1)
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    archetype_name = config.get("archetype", "Unknown")
    expected_files = config.get("files", [])
    
    console.print(f"Checking project based on '[bold cyan]{archetype_name}[/]' blueprint...")
    
    missing_files = []
    for file_str in expected_files:
        if not (dir_path / file_str).exists():
            missing_files.append(file_str)
            
    if missing_files:
        console.print("[bold red]Status: INCOMPLETE[/]")
        console.print("The following essential files are missing:")
        for f in missing_files:
            console.print(f"  - [MISSING] {f}")
    else:
        console.print("[bold green]Status: Ready to Build 🚀[/]")

def main():
    app()

if __name__ == "__main__":
    main()
