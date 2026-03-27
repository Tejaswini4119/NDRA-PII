{
  description = "NDRA-PII Dev Environment (Final Stable Fix)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python312;

        pythonEnv = python.withPackages (ps: with ps; [
          pip
          setuptools
          wheel

          fastapi
          uvicorn
          python-multipart
          pydantic
          pydantic-settings

          spacy
          regex

          requests
          pyyaml
          pandas

          pypdf
          python-docx
          python-pptx
          openpyxl

          beautifulsoup4
          pillow
          reportlab
        ]);

      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv

            pkgs.git
            pkgs.gcc
            pkgs.pkg-config
            pkgs.zlib
            pkgs.openssl
            pkgs.libffi
          ];

          shellHook = ''
            echo "🚀 NDRA-PII DEV ENV READY (FINAL)"

            export PYTHONPATH=$PWD

            # pip isolation
            export PIP_PREFIX=$PWD/.pip
            export PYTHONUSERBASE=$PIP_PREFIX
            export PATH=$PIP_PREFIX/bin:$PATH

            export PYTHONNOUSERSITE=1

            # 🔥 ONLY THIS LINE MATTERS FOR PRESIDIO
            export PYTHONPATH=$PWD/.pip/lib/python3.12/site-packages:$PYTHONPATH

            echo "✔ Nix core + pip extensions ready"
          '';
        };
      });
}
