import typer

from techui_builder import __version__

app = typer.Typer()


@app.callback(help="Output the version of techui-builder", invoke_without_command=True)
def version():
    print(f"techui-builder version: {__version__}")
    raise typer.Exit()
