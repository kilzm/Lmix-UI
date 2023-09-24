{ stdenv
, lib
, fetchFromGitHub
, pkg-config
, perl
, bc
, tcl
, lua
, luaPackages
, rsync
, procps
}:

let 
  inherit (luaPackages) luafilesystem luaposix;
in 
stdenv.mkDerivation rec {
  pname = "lmod";
  version = "8.7.32";

  src = fetchFromGitHub {
    owner = "TACC";
    repo = "Lmod";
    rev = "${version}";
    sha256 = "sha256-x9yF7TZRpjCyJHdt3BVky5BH+hKVsa01+xHNKNMjI0E=";
  };

  preBuild = ''
    patchShebangs proj_mgmt
  '';

  buildInputs = [ 
    pkg-config
    bc
    lua
    tcl
    perl
    rsync
    procps
  ];

  propagatedBuildInputs = [ luaposix luafilesystem ];

  meta = with lib; {
    description = "Lua implementation of environment modules";
    homepage = "https://www.tacc.utexas.edu/research/tacc-research/lmod/";
    license = licenses.mit;
    platform = platforms.unix;
  };
}