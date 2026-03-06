{
  description = "apple-tools";

  inputs = {
    nixpkgs.url = "https://channels.nixos.org/nixpkgs-unstable/nixexprs.tar.xz";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        libs = with pkgs; [];
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [uv lit filecheck] ++ libs;

          shellHook = ''
            export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath libs}
            source .venv/bin/activate
          '';
        };
      }
    );
}
