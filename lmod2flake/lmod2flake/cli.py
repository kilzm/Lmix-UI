import click
import subprocess
import os
from pathlib import Path
from lmod.spider import Spider

def exit_err(msg: str, context):
    click.echo(click.style('error: ', fg='red') + msg, err=True)
    context.exit(1)

LMIX_FLAKE =  "github:kilzm/lmix"
NIX_MODULES_PATH = "/opt/modulefiles/modules_nix/lmix_23.05"

@click.command()
@click.pass_context
@click.argument("directory", required=True)
def modules_to_flake(ctx, directory):
    """Generate a nix flake with a devShell derived from loaded modules"""
    path = Path(directory)
    flake_path = Path(directory) / "flake.nix"
    if not path.exists():
        exit_err("path does not exist", ctx)

    if path.is_file():
        exit_err("path should be a directory (is a file)", ctx)

    if flake_path.exists():
        exit_err("directory is already a flake (remove flake.nix to override)", ctx)

    inputs, native_inputs, stdenv = build_inputs()

    with flake_path.open(mode='w') as flake:
        flake.write(flake_contents(stdenv, '\n'.join(inputs), '\n'.join(native_inputs)))

    nixpkgs_fmt_cmd = ['nix', 'shell', f'{LMIX_FLAKE}#nixpkgs-fmt', '-c', 'nixpkgs-fmt', f'{flake_path}']
    
    try:
        subprocess.run(
            nixpkgs_fmt_cmd,
            encoding='utf-8',
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    except subprocess.CalledProcessError as e:
        exit_err(f"'nix shell' failed with code {e.returncode}: {e.stderr}", ctx)

def build_inputs():
    spider = Spider(NIX_MODULES_PATH)
    modules = [module for module in spider.get_names() if module != 'nix-stdenv']
    inputs = [ ]
    native_inputs = [ ]
    stdenv = "stdenv"
    for module in modules:
        pkg_upper = module.replace('-','_').upper()
        attrname = f"LMIX_{pkg_upper}_ATTRNAME"
        native = f"LMIX_{pkg_upper}_NATIVE"
        ccstdenv = f"LMIX_{pkg_upper}_STDENV"
        if attrname in os.environ:
            if ccstdenv in os.environ:
              stdenv = os.environ[ccstdenv]
              continue

            if os.environ[native] == "1":
                native_inputs.append(os.environ[attrname])
            else:
                inputs.append(os.environ[attrname])

    return inputs, native_inputs, stdenv


def flake_contents(stdenv: str, build_inputs: str, native_build_inputs: str):
    content =  f'''{{
      description = "Autogenerated by lmod2flake";

      inputs.lmix.url = {LMIX_FLAKE};

      outputs = {{ self, lmix }}:
        let
          system = "x86_64-linux";
          pkgs = lmix.legacyPackages.${{system}};
        in
        {{
          devShells.${{system}}.default = pkgs.mkShell'''

    if stdenv != "stdenv":
      content += f".override {{ stdenv = pkgs.{stdenv}; }} rec {{"
    else:
      content += "rec {{" if stdenv != "stdenv" else " rec {"

    if build_inputs != "":
      content += f"buildInputs = with pkgs; [ {build_inputs} ];"

    if native_build_inputs != "":
      content += f"nativeBuildInputs = with pkgs; [ {native_build_inputs} ];"

    content += f'''}};
        }};

      nixConfig = {{
        bash-prompt-prefix = ''\033[0;36m\[(nix develop)\033[0m '';
      }};
    }}'''

    return content