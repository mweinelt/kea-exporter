{
  description = "Kea Exporter";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.pre-commit-hooks.url = "github:cachix/pre-commit-hooks.nix";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, pre-commit-hooks, flake-utils }:
    flake-utils.lib.eachSystem [ "aarch64-linux" "x86_64-linux" ] (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
    in
      {
        checks = {
          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              isort.enable = true;
              ruff.enable = true;
              ruff-format = {
                enable = true;
                entry = "${pkgs.ruff}/bin/ruff format";
                pass_filenames = false;
              };
              rstcheck = {
                enable = true;
                entry = "${pkgs.rstcheck}/bin/rstcheck";
                pass_filenames = true;
                files = "\\.rst$";
              };
            };
          };
        };
        devShells.default = with pkgs; mkShell {
          inherit (self.checks.${system}.pre-commit-check) shellHook;

          buildInputs = [
            isort
            pdm
            ruff
          ] ++ (with python3.pkgs; [
            typing-extensions
          ]);
        };
      }
    );
}
