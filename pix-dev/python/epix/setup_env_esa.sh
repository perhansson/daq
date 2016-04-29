setenv MON $PWD
set DAQ="/home/epix/run_software"
if($#argv > 1) then
    set DAQ = $argv[1]
endif
pushd $DAQ
source setup_env_esa.csh
popd

