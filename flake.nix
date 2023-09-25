{
  description = "UI for Lmix modules";

  inputs.nixpkgs.url = github:NixOS/nixpkgs?ref=23.05;
  inputs.lmix_23_05.url = "github:kilzm/Lmix";
  # inputs.lmix_23_11.url = "github:/kilzm/Lmix?ref=...";

  outputs = inputs@{ self, nixpkgs, ... }: 
  let
    inherit (nixpkgs.lib) 
      foldr filterAttrs replaceStrings attrNames attrValues 
      hasPrefix removePrefix makeSearchPath;
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };

    lmix = let 
      filtered = filterAttrs (n: _: hasPrefix "lmix" n) inputs;
      flakes = attrValues filtered;
      parse-version = name: replaceStrings ["_"] ["."] (removePrefix "lmix_" name);
      versions = map parse-version (attrNames filtered);
    in { inherit flakes versions; };

    modules = let 
      getMods = pkgs: attrValues (filterAttrs (name: _: hasPrefix "_modules" name) pkgs);
    in foldr (_lmix: mods: mods ++ getMods _lmix.packages.${system}) [ ] lmix.flakes;

  in {
    packages.${system} = {
      lmod = pkgs.callPackage ./lmod { };
      lmod2flake = pkgs.callPackage ./lmod2flake { };
      all-modules = pkgs.symlinkJoin { name = "modulefiles"; paths = modules; };
    };

    devShells.${system}.default = let
      inherit (self.packages.${system}) lmod lmod2flake all-modules;
      MODULEPATH = makeSearchPath "" (map (ver: "${all-modules}/lmix_${ver}") lmix.versions);
    in pkgs.mkShell rec {
      packages = [ lmod lmod2flake all-modules ];
      shellHook = "source ${lmod}/lmod/${lmod.version}/init/bash";
      inherit MODULEPATH;
    };

    apps.${system} = rec {
      default = lmod2flake;
      lmod2flake = {
        type = "app";
        program = let 
          inherit (self.packages.${system}) lmod2flake; 
        in "${lmod2flake}/bin/lmod2flake";
      };
    };
  };
}