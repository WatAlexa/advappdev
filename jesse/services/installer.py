from jesse.services.env import ENV_VALUES
import jesse.helpers as jh
import platform
import requests
import subprocess
import sys
import click
import os

def _pip_install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def install(is_live_plugin_already_installed: bool, strict: bool):
    if is_live_plugin_already_installed:
        from jesse_live.version import __version__
        click.clear()
        print(f'Version "{__version__}" of the live-trade plugin is already installed.')
        if strict:
            txt = '\nIf you meant to update, first delete the existing version by running "pip uninstall jesse_live -y" and then run "jesse