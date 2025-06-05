{ pkgs ? import <nixpkgs> { } }:

let
  pythonEnv = pkgs.python3.withPackages(ps: with ps; [ 
    black  
    build 
    click 
    colorama 
    isort 
    lexid 
    looseversion 
    mypy-extensions 
    packaging 
    pathspec 
    pip-tools 
    platformdirs 
    pyproject-hooks 
    toml 
    tomli 
    typing-extensions 
    wheel
  ]);

in
pkgs.mkShell {
  packages = [
    pythonEnv
  ];
}
